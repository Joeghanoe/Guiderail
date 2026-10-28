"""drawio_kit core: scene primitives, draw.io + SVG backends, image/icon helpers. Stdlib only."""
import base64, glob, json, math, os, re, struct, subprocess, sys, tempfile
from xml.sax.saxutils import quoteattr, escape

AZ = "img/lib/azure2/"
ICONS = {  # builtin draw.io icons used for chips / rows
    "logicapp": AZ + "integration/Logic_Apps.svg",
    "apim": AZ + "integration/API_Management_Services.svg",
    "eg": AZ + "integration/Event_Grid_Domains.svg",
    "xslt": AZ + "iot/Function_Apps.svg",
    "fn": AZ + "iot/Function_Apps.svg",
    "sb": AZ + "integration/Service_Bus.svg",
    "dwh": AZ + "analytics/Azure_Synapse_Analytics.svg",
}
ICON_FALLBACK = {"logicapp": "#0a7abf", "apim": "#6f3fb0", "eg": "#2a9d8f", "xslt": "#f2a900", "fn": "#f2a900",
                 "sb": "#1f6fd1", "dwh": "#0a7abf"}
CHIP_COLS = [("apim", "APIM"), ("eg", "Event Grid"), ("xslt", "XSLT"), ("fn", "Func")]


# ---------------------------------------------------------------- scene + backends
class Scene:
    def __init__(self):
        self.items = []

    def add(self, kind, **kw):
        self.items.append((kind, kw))

    def rect(self, x, y, w, h, fill="#ffffff", stroke="#bdbdbd", sw=1, dash=False, rx=0, opacity=1, tip=None):
        self.add("rect", x=x, y=y, w=w, h=h, fill=fill, stroke=stroke, sw=sw, dash=dash, rx=rx, opacity=opacity, tip=tip)

    def text(self, x, y, w, h, txt, size=11, bold=False, color="#000000", align="left", opacity=1, valign="top", italic=False):
        self.add("text", x=x, y=y, w=w, h=h, txt=txt, size=size, bold=bold, color=color, align=align,
                 opacity=opacity, valign=valign, italic=italic)

    def image(self, x, y, w, h, src, opacity=1, label=""):
        self.add("image", x=x, y=y, w=w, h=h, src=src, opacity=opacity, label=label)

    def badge(self, x, y, txt, color="#333333", d=22):
        self.add("badge", x=x, y=y, txt=str(txt), color=color, d=d)

    def line(self, pts, color, sw=1.6, dash=False, start="none", end="none", opacity=1):
        self.add("line", pts=pts, color=color, sw=sw, dash=dash, start=start, end=end, opacity=opacity)


def wrap(txt, width, size):
    cpl = max(4, int(width / (size * 0.53)))
    out = []
    for para in str(txt).split("\n"):
        line = ""
        for word in para.split():
            if len(line) + len(word) + (1 if line else 0) > cpl:
                out.append(line); line = word
            else:
                line = (line + " " + word).strip()
        out.append(line)
    return out


class DrawioOut:
    def __init__(self, W, H, name):
        self.cells, self.n, self.W, self.H, self.name = [], 1, W, H, name

    def _id(self):
        self.n += 1
        return f"c{self.n}"

    def _cell(self, value, style, x, y, w, h, tip=None):
        cid = self._id()
        geo = f'<mxGeometry x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" as="geometry"/>'
        if tip:
            self.cells.append(f'<object label={quoteattr(value)} tooltip={quoteattr(tip)} id="{cid}"><mxCell style={quoteattr(style)} vertex="1" parent="1">{geo}</mxCell></object>')
        else:
            self.cells.append(f'<mxCell id="{cid}" value={quoteattr(value)} style={quoteattr(style)} vertex="1" parent="1">{geo}</mxCell>')

    def render(self, sc):
        for kind, k in sc.items:
            op = f"opacity={int(k.get('opacity', 1) * 100)};" if k.get("opacity", 1) < 1 else ""
            if kind == "rect":
                st = (f"rounded={1 if k['rx'] else 0};arcSize={min(50, k['rx'] * 2) if k['rx'] else 0};html=1;fillColor={k['fill']};"
                      f"strokeColor={k['stroke']};strokeWidth={k['sw']};" + ("dashed=1;dashPattern=6 3;" if k["dash"] else "") + op)
                self._cell("", st, k["x"], k["y"], k["w"], k["h"], k["tip"])
            elif kind == "text":
                st = (f"text;html=0;whiteSpace=wrap;overflow=hidden;align={k['align']};verticalAlign={k['valign']};fontSize={k['size']};"
                      f"fontColor={k['color']};spacing=0;spacingLeft=0;spacingTop=0;" + ("fontStyle=1;" if k["bold"] else "")
                      + ("fontStyle=2;" if k["italic"] and not k["bold"] else "") + (f"textOpacity={int(k['opacity'] * 100)};" if k["opacity"] < 1 else ""))
                self._cell(k["txt"], st, k["x"], k["y"], k["w"], k["h"])
            elif kind == "image":
                s = k["src"]
                if s[0] == "azure":
                    st = f"shape=image;html=1;image={s[1]};aspect=fixed;imageAspect=0;" + op
                elif s[0] == "img":
                    st = f"shape=image;html=1;image=data:{s[1]},{s[2]};aspect=fixed;imageAspect=0;" + op
                else:  # stencil
                    st = f"html=1;shape={s[1]};strokeColor=none;" + op
                self._cell("", st, k["x"], k["y"], k["w"], k["h"])
            elif kind == "badge":
                st = (f"ellipse;html=1;fillColor={k['color']};strokeColor=#ffffff;strokeWidth=2;fontColor=#ffffff;fontStyle=1;"
                      f"fontSize=10;align=center;verticalAlign=middle;spacing=0;")
                self._cell(k["txt"], st, k["x"], k["y"], k["d"], k["d"])
            elif kind == "line":
                st = (f"html=1;endArrow={'classic' if k['end']=='arrow' else 'oval' if k['end']=='dot' else 'none'};endFill=1;endSize=4;"
                      f"startArrow={'classic' if k['start']=='arrow' else 'oval' if k['start']=='dot' else 'none'};startFill=1;startSize=4;"
                      f"strokeColor={k['color']};strokeWidth={k['sw']};" + ("dashed=1;dashPattern=7 4;" if k["dash"] else "") + op)
                pts = k["pts"]
                mid = "".join(f'<mxPoint x="{x:.1f}" y="{y:.1f}"/>' for x, y in pts[1:-1])
                cid = self._id()
                self.cells.append(
                    f'<mxCell id="{cid}" style={quoteattr(st)} edge="1" parent="1"><mxGeometry relative="1" as="geometry">'
                    f'<mxPoint x="{pts[0][0]:.1f}" y="{pts[0][1]:.1f}" as="sourcePoint"/>'
                    f'<mxPoint x="{pts[-1][0]:.1f}" y="{pts[-1][1]:.1f}" as="targetPoint"/>'
                    + (f'<Array as="points">{mid}</Array>' if mid else "") + '</mxGeometry></mxCell>')
        return ('<mxfile host="TeamValue lld_diagram" pages="1"><diagram name=' + quoteattr(self.name) + ' id="lld1">'
                f'<mxGraphModel dx="1600" dy="1000" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" '
                f'page="1" pageScale="1" pageWidth="{int(self.W)}" pageHeight="{int(self.H)}" math="0" shadow="0"><root>'
                '<mxCell id="0"/><mxCell id="1" parent="0"/>' + "".join(self.cells) + '</root></mxGraphModel></diagram></mxfile>')


class SvgOut:
    def __init__(self, W, H, lib=None):
        self.W, self.H, self.o, self.lib, self._ic = W, H, [], lib, {}

    def azure_icon(self, path):
        if not self.lib: return None
        if path not in self._ic:
            f = os.path.join(self.lib, path)
            self._ic[path] = base64.b64encode(open(f, "rb").read()).decode() if os.path.exists(f) else None
        return self._ic[path]

    def render(self, sc):
        o = self.o
        o.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.W}" height="{self.H}" viewBox="0 0 {self.W} {self.H}" '
                 'font-family="Helvetica, Arial, sans-serif"><rect width="100%" height="100%" fill="#ffffff"/>'
                 '<defs>' + "".join(
                     f'<marker id="{n}" markerWidth="8" markerHeight="8" refX="{rx}" refY="4" orient="{ori}" markerUnits="userSpaceOnUse">{shape}</marker>'
                     for n, rx, ori, shape in [
                         ("ae", 8, "auto", '<path d="M0,0 L8,4 L0,8 z" fill="context-stroke"/>'),
                         ("as", 8, "auto-start-reverse", '<path d="M0,0 L8,4 L0,8 z" fill="context-stroke"/>'),
                         ("de", 4, "auto", '<circle cx="4" cy="4" r="3" fill="context-stroke"/>'),
                         ("ds", 4, "auto", '<circle cx="4" cy="4" r="3" fill="context-stroke"/>')]) + '</defs>')
        for kind, k in sc.items:
            op = f' opacity="{k.get("opacity", 1)}"' if k.get("opacity", 1) < 1 else ""
            if kind == "rect":
                o.append(f'<rect x="{k["x"]}" y="{k["y"]}" width="{k["w"]}" height="{k["h"]}" rx="{k["rx"]}" fill="{k["fill"]}" '
                         f'stroke="{k["stroke"]}" stroke-width="{k["sw"]}"' + (' stroke-dasharray="6 3"' if k["dash"] else "") + op + '/>')
            elif kind == "text":
                lines = wrap(k["txt"], k["w"], k["size"])
                ax = {"left": k["x"], "center": k["x"] + k["w"] / 2, "right": k["x"] + k["w"]}[k["align"]]
                anchor = {"left": "start", "center": "middle", "right": "end"}[k["align"]]
                lh = k["size"] * 1.2
                y0 = k["y"] + k["size"] + (max(0, (k["h"] - lh * len(lines)) / 2) if k["valign"] == "middle" else 0)
                for i, ln in enumerate(lines):
                    o.append(f'<text x="{ax}" y="{y0 + i * lh:.1f}" font-size="{k["size"]}" fill="{k["color"]}" text-anchor="{anchor}"'
                             + (' font-weight="bold"' if k["bold"] else "") + (' font-style="italic"' if k["italic"] else "") + op
                             + f'>{escape(ln)}</text>')
            elif kind == "image":
                s = k["src"]
                icon = self.azure_icon(s[1]) if s[0] == "azure" else None
                if icon:
                    o.append(f'<image x="{k["x"]}" y="{k["y"]}" width="{k["w"]}" height="{k["h"]}" href="data:image/svg+xml;base64,{icon}"{op}/>')
                elif s[0] == "img":
                    o.append(f'<image x="{k["x"]}" y="{k["y"]}" width="{k["w"]}" height="{k["h"]}" href="data:{s[1]};base64,{s[2]}" '
                             f'preserveAspectRatio="xMidYMid meet"{op}/>')
                else:
                    name = s[1].split("/")[-1].replace(".svg", "")[:2] if s[0] == "azure" else "OD"
                    col = ICON_FALLBACK.get(k.get("label") or "", "#0a7abf")
                    o.append(f'<rect x="{k["x"]}" y="{k["y"]}" width="{k["w"]}" height="{k["h"]}" rx="3" fill="{col}"{op}/>'
                             f'<text x="{k["x"] + k["w"] / 2}" y="{k["y"] + k["h"] / 2 + 3}" font-size="8" fill="#fff" text-anchor="middle"{op}>{escape(name)}</text>')
            elif kind == "badge":
                d = k["d"]
                o.append(f'<circle cx="{k["x"] + d / 2}" cy="{k["y"] + d / 2}" r="{d / 2}" fill="{k["color"]}" stroke="#fff" stroke-width="2"/>'
                         f'<text x="{k["x"] + d / 2}" y="{k["y"] + d / 2 + 3.5}" font-size="10" font-weight="bold" fill="#fff" text-anchor="middle">{escape(k["txt"])}</text>')
            elif kind == "line":
                p = " ".join(f"{x:.1f},{y:.1f}" for x, y in k["pts"])
                m = ""
                if k["end"] != "none": m += f' marker-end="url(#{"ae" if k["end"] == "arrow" else "de"})"'
                if k["start"] != "none": m += f' marker-start="url(#{"as" if k["start"] == "arrow" else "ds"})"'
                o.append(f'<polyline points="{p}" fill="none" stroke="{k["color"]}" stroke-width="{k["sw"]}"'
                         + (' stroke-dasharray="7 4"' if k["dash"] else "") + m + op + '/>')
        o.append("</svg>")
        return "\n".join(o)


# ---------------------------------------------------------------- helpers
def load_image(path):
    """-> (mime, base64, w, h). png and svg are used as is; other formats (jpg, webp, avif, ico, ...)
    and very large pngs are converted/downscaled to png with macOS sips."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".svg":
        txt = open(path, encoding="utf-8", errors="ignore").read()
        m = re.search(r'viewBox="[\d.\-]+[ ,]+[\d.\-]+[ ,]+([\d.]+)[ ,]+([\d.]+)"', txt)
        if m: w, h = float(m.group(1)), float(m.group(2))
        else:
            mw, mh = re.search(r'width="([\d.]+)', txt), re.search(r'height="([\d.]+)', txt)
            w, h = (float(mw.group(1)), float(mh.group(1))) if mw and mh else (4.0, 3.0)
        return "image/svg+xml", base64.b64encode(txt.encode("utf-8")).decode(), w, h
    raw = open(path, "rb").read()
    big = ext == ".png" and struct.unpack(">I", raw[16:20])[0] > 600
    if ext != ".png" or big:
        tmp = os.path.join(tempfile.mkdtemp(), "logo.png")
        r = subprocess.run(["sips", "-Z", "400", "-s", "format", "png", path, "--out", tmp], capture_output=True)
        if r.returncode != 0 or not os.path.exists(tmp):
            raise SystemExit(f"cannot convert logo {path} (needs macOS sips, or provide a png/svg)")
        raw = open(tmp, "rb").read()
    w, h = struct.unpack(">II", raw[16:24])
    return "image/png", base64.b64encode(raw).decode(), w, h


def find_drawio_lib():
    """Folder that contains img/lib/azure2 (draw.io webapp), used only to embed real icons in the SVG preview."""
    cands = [os.environ.get("DRAWIO_LIB", "")] + sorted(glob.glob(os.path.expanduser(
        "~/.vscode/extensions/hediet.vscode-drawio-*/drawio/src/main/webapp")), reverse=True)
    return next((c for c in cands if c and os.path.isdir(os.path.join(c, "img", "lib", "azure2"))), None)


def fmt(n):
    return f"{n:,}" if isinstance(n, int) else (n or "–")




def icon(k):
    """Icon alias (ICONS), a path under img/lib/azure2/ (e.g. 'integration/Logic_Apps.svg') or a full img/lib path."""
    if k in ICONS:
        return ICONS[k]
    return k if k.startswith("img/") else AZ + k


def search_icons(term, lib=None):
    """Find real draw.io icon paths whose file name contains term (case-insensitive)."""
    lib = lib or find_drawio_lib()
    if not lib:
        return []
    root = os.path.join(lib, "img", "lib")
    t = term.lower().replace(" ", "_")
    return sorted(os.path.relpath(os.path.join(d, f), lib) for d, _, fs in os.walk(root)
                  for f in fs if f.endswith(".svg") and t in f.lower())


def check_icons(sc, lib=None):
    """Return builtin icons used in the scene that do not exist in the local draw.io library."""
    lib = lib or find_drawio_lib()
    if not lib:
        return []
    used = {k["src"][1] for kind, k in sc.items if kind == "image" and k["src"][0] == "azure"}
    return sorted(u for u in used if not os.path.exists(os.path.join(lib, u)))


def render_png(svg_path, png_path, w, h):
    """Render the SVG preview to PNG with headless Edge/Chrome (macOS). False when no browser is found."""
    for b in ("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
              "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"):
        if os.path.exists(b):
            html = os.path.join(tempfile.mkdtemp(), "v.html")
            open(html, "w").write(f'<html><body style="margin:0"><img src="file://{os.path.abspath(svg_path)}" style="display:block"></body></html>')
            subprocess.run([b, "--headless", "--disable-gpu", "--hide-scrollbars", f"--window-size={int(w)},{int(h)}",
                            f"--screenshot={os.path.abspath(png_path)}", "file://" + html], capture_output=True)
            return os.path.exists(png_path)
    return False
