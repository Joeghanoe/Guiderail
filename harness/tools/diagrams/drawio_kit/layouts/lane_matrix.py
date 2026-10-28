"""Layout: lane matrix. Rows (e.g. logic apps) grouped per flow on the left, vertical lanes (APIM slices / direct
paths) on the right headed by the system logo; each row draws a horizontal line in the system colour."""
import os, sys
from ..core import *
from .. import core


class Builder:
    def __init__(self, spec, base):
        self.spec, self.base, self.sc = spec, base, Scene()
        self.cfg = dict(group_x=40, group_w=190, icon_x=244, name_x=274, name_w=410, runs_x=690, runs_w=66,
                        chip_x0=764, chip_step=34, chip=22, lane0=1010, lane_step=88, band_pad=44, band_gap=24,
                        head_y=262, rows_top=312, leg_w=580)
        self.cfg.update(spec.get("layout", {}))
        self.logos = {}
        self.notes = []     # (num, title, body)
        self.stats = {}

    # --- logos
    def logo(self, sid):
        if sid in self.logos:
            return self.logos[sid]
        s = self.spec["systems"][sid]
        if s.get("logo"):
            cands = [s["logo"]]
        else:  # logos/<id>.<ext> next to the spec or one folder up
            cands = [os.path.join(d, f"{sid}{e}") for d in ("logos", os.path.join("..", "logos"))
                     for e in (".png", ".svg", ".jpg", ".jpeg", ".webp", ".avif", ".ico", ".gif")]
        full = next((os.path.join(self.base, c) for c in cands if os.path.exists(os.path.join(self.base, c))), None)
        r = None
        if full:
            mime, b64, w, h = load_image(full)
            r = ("img", mime, b64, w, h)
        elif s.get("stencil"):
            r = ("stencil", s["stencil"], 4, 3)
        self.logos[sid] = r
        return r

    def draw_logo(self, sid, cx, y, boxw, boxh, opacity=1):
        s = self.spec["systems"][sid]
        r = self.logo(sid)
        if r is None:  # square tile with the name
            side = min(boxw, boxh)
            self.sc.rect(cx - side / 2, y + (boxh - side) / 2, side, side, fill=s["color"], stroke=s["color"], rx=6, opacity=opacity)
            self.sc.text(cx - side / 2 + 2, y + (boxh - side) / 2, side - 4, side, s.get("tile", s["name"]), size=8, bold=True,
                         color="#ffffff", align="center", valign="middle", opacity=opacity)
            return
        if r[0] == "img":
            _, mime, data, iw, ih = r
            src = ("img", mime, data)
        else:
            _, data, iw, ih = r
            src = ("stencil", data)
        sc = min(boxw / iw, boxh / ih)
        w, h = iw * sc, ih * sc
        self.sc.image(cx - w / 2, y + (boxh - h) / 2, w, h, src, opacity=opacity)

    # --- numbering
    def note(self, title, body):
        n = len(self.notes) + 1
        self.notes.append((n, title, body))
        return n

    def build(self):
        sp, c, sc = self.spec, self.cfg, self.sc
        ICONS.update(sp.get("icons", {}))
        self.chips = [tuple(x) for x in sp.get("chips", CHIP_COLS)]
        # lanes
        lane_x, lane_info, bands = {}, {}, []
        x = c["lane0"] - c["band_pad"]
        for b in sp["bands"]:
            b0 = x
            for i, ln in enumerate(b["lanes"]):
                lane_x[ln["id"]] = b0 + c["band_pad"] + i * c["lane_step"]
                lane_info[ln["id"]] = (b.get("direct", b["id"] == "direct"), ln)  # (bypasses the gateway, lane)
            x = lane_x[b["lanes"][-1]["id"]] + c["band_pad"]
            bands.append((b, b0, x))
            x += c["band_gap"]
        right = x - c["band_gap"]
        # flow notes first so numbering matches the table
        for s in sp["sections"]:
            for f in s["flows"]:
                f["_n"] = self.note(f"{f['id']} · {f['title']}", f.get("note", ""))
        for b, b0, b1 in bands:
            if b.get("note"):
                b["_n"] = self.note(b["note"]["title"], b["note"]["body"])
            for ln in b["lanes"]:
                if ln.get("note"):
                    ln["_n"] = self.note(ln["note"]["title"], ln["note"]["body"])
        for en in sp.get("extra_notes", []):
            self.note(en["title"], en["body"])

        # ---- rows layout (first pass: y positions)
        y = c["rows_top"]
        layout = []
        for s in sp["sections"]:
            sy = y
            y += 30
            fl = []
            for f in s["flows"]:
                fy = y
                rows = []
                for r in f["rows"]:
                    n = len(r.get("l", []))
                    rh = max(38, 10 * n + 14)
                    rows.append((r, y, rh))
                    y += rh
                f["_rows"], f["_y0"], f["_y1"] = rows, fy, y
                fl.append((f, fy, y))
                y += 10
            layout.append((s, sy, y))
            y += 14
        bottom = y
        self.stats["height"] = bottom

        # ---- backgrounds
        sc.rect(30, 110, right - 20 + 0, bottom - 110 + 150, fill="#ffffff", stroke="#e0e0e0", rx=4)
        for s, sy, ey in layout:
            sc.rect(30, sy, right - 20, ey - sy - 8, fill=s.get("fill", "#f7f7f7"), stroke=s.get("stroke", "#cfcfcf"), rx=4)
            cnt = sum(1 for f in s["flows"] for r in f["rows"] if r.get("kind", "logicapp") == "logicapp")
            if "expect" in s and cnt != s["expect"]:
                print(f"WARNING: section '{s['title']}' has {cnt} logic apps, spec expects {s['expect']}", file=sys.stderr)
            self.stats[s["id"]] = cnt
            sc.text(44, sy + 6, 900, 18, s["title"] + (f"  ({cnt} logic apps)" if cnt else ""), size=12, bold=True)
            if s.get("subtitle"):
                sc.text(420, sy + 8, 520, 16, s["subtitle"], size=9, color="#666666", align="right")
        # bands (lane areas)
        for b, b0, b1 in bands:
            sc.rect(b0, 116, b1 - b0, bottom - 116 + 140, fill=b.get("fill", "#f3f3f3"), stroke=b.get("stroke", "#aaaaaa"), dash=True, rx=6)
            bicon = b.get("icon")
            if bicon:
                sc.image(b0 + 8, 122, 22, 22, ("azure", icon(bicon)), label=bicon)
            sc.text(b0 + (36 if bicon else 10), 123, b1 - b0 - 60, 34, b["title"], size=10, bold=True)
            if b.get("_n"):
                sc.badge(b1 - 28, 122, b["_n"], b.get("badge", "#333333"), 20)

        # column header
        hy = c["head_y"]
        sc.text(c["name_x"], hy + 14, 300, 14, "Logic app  ·  trigger → published event", size=9, bold=True, color="#555555")
        sc.text(c["runs_x"], hy + 8, c["runs_w"], 24, "Aug 2026\nruns / calls", size=8, color="#555555", align="center")
        for i, (k, lbl) in enumerate(self.chips):
            cx = c["chip_x0"] + i * c["chip_step"]
            sc.image(cx, hy + 2, c["chip"], c["chip"], ("azure", icon(k)), label=k)
            sc.text(cx - 6, hy + 25, c["chip"] + 12, 11, lbl, size=7, color="#555555", align="center")

        # ---- lane bars + headers (top and bottom)
        lane_top, lane_bot = 270, bottom - 6
        for b, b0, b1 in bands:
            for ln in b["lanes"]:
                lx, col = lane_x[ln["id"]], sp["systems"][ln["system"]]["color"]
                sc.rect(lx - 3, lane_top, 6, lane_bot - lane_top, fill=col, stroke=col, sw=0, opacity=0.35)
                for yy, flip in ((168, False), (lane_bot + 8, True)):
                    self.draw_logo(ln["system"], lx, yy, 74, 46)
                    sc.text(lx - 44, yy + 52, 88, 14, sp["systems"][ln["system"]]["name"], size=9, bold=True, align="center")
                    sc.text(lx - 44, yy + 66, 88, 24, ln.get("label", ""), size=7.5, color="#666666", align="center")
                    if ln.get("_n") and not flip:
                        sc.badge(lx + 20, yy - 6, ln["_n"], col, 18)

        # ---- flows and rows
        x0_line = c["chip_x0"] + 4 * c["chip_step"] + 8
        for s, sy, ey in layout:
            for f in s["flows"]:
                fy, fe = f["_y0"], f["_y1"]
                sc.rect(c["group_x"], fy, c["group_w"], fe - fy - 4, fill="#ffffff", stroke="#bdbdbd", rx=4)
                sc.badge(c["group_x"] - 8, fy + 4, f["_n"], "#333333", 22)
                sc.text(c["group_x"] + 18, fy + 6, c["group_w"] - 24, 14, f["id"], size=11, bold=True)
                sc.text(c["group_x"] + 18, fy + 22, c["group_w"] - 24, fe - fy - 28, f["title"], size=9.5, color="#333333")
                for r, ry, rh in f["_rows"]:
                    self.row(r, ry, rh, lane_x, lane_info, x0_line)

        # ---- legend (right)
        leg_x = right + 40
        real, self.sc = self.sc, Scene()
        ly = self.legend(leg_x, 40)          # dry run to measure the panel
        self.sc = real
        sc.rect(leg_x, 40, c["leg_w"], ly - 40, fill="#ffffff", stroke="#bdbdbd", rx=4)
        self.legend(leg_x, 40)
        W = leg_x + c["leg_w"] + 40
        H = max(bottom + 260, ly + 40)
        # title
        sc.text(40, 20, 1800, 36, sp["meta"]["title"], size=26, bold=True)
        total = sum(v for k, v in self.stats.items() if k != "height")
        sub = sp["meta"].get("subtitle", "").replace("{total}", str(total))
        sc.text(40, 62, 1800, 20, sub, size=12, color="#555555")
        self.W, self.H = W, H

    def row(self, r, y, rh, lane_x, lane_info, x0_line):
        c, sc, sp = self.cfg, self.sc, self.spec
        st = r.get("st", "enabled")
        op = 0.5 if st == "disabled" else 1
        cy = y + rh / 2 - 2
        tip = r.get("tip")
        sc.rect(c["icon_x"] - 4, y, x0_line - c["icon_x"] - 4, rh - 4, fill="#ffffff",
                stroke="#9e9e9e" if st != "idle" else "#c62828", dash=st in ("idle", "disabled"), rx=4, opacity=op, tip=tip)
        kind = r.get("kind", "logicapp")
        sc.image(c["icon_x"], cy - 9, 18, 18, ("azure", icon(r.get("icon", "logicapp"))), opacity=op, label=r.get("icon", "logicapp"))
        sub = r.get("s", "")
        if st == "disabled": sub = (sub + "  ·  DISABLED").strip(" ·")
        if st == "idle": sub = (sub + "  ·  no traffic Aug 2026").strip(" ·")
        sc.text(c["name_x"], cy - 15, c["name_w"], 14, r["n"], size=10, bold=True, opacity=op)
        sc.text(c["name_x"], cy - 1, c["name_w"], 12, sub, size=8, color="#666666", opacity=op)
        sc.text(c["runs_x"], cy - 7, c["runs_w"], 14, fmt(r.get("r")), size=9, align="center", color="#333333", opacity=op)
        used = set(x for x in r.get("u", "").split(",") if x)
        unk = set(x for x in r.get("q", "").split(",") if x)
        links = [self.parse_link(l) for l in r.get("l", [])]
        if any(not lane_info[l[0]][0] for l in links) or r.get("apim"):
            used.add("apim")
        for i, (k, _) in enumerate(self.chips):
            cx = c["chip_x0"] + i * c["chip_step"]
            if k in used:
                sc.image(cx, cy - 11, c["chip"], c["chip"], ("azure", icon(k)), opacity=op, label=k)
            elif k in unk:
                sc.rect(cx, cy - 11, c["chip"], c["chip"], fill="#ffffff", stroke="#9e9e9e", dash=True, rx=4)
                sc.text(cx, cy - 11, c["chip"], c["chip"], "?", size=11, bold=True, color="#757575", align="center", valign="middle")
            else:
                sc.image(cx, cy - 11, c["chip"], c["chip"], ("azure", icon(k)), opacity=0.12, label=k)
        n = len(links)
        for i, (lane, d, lbl) in enumerate(links):
            ly = cy + (i - (n - 1) / 2) * 9
            col = sp["systems"][lane_info[lane][1]["system"]]["color"]
            direct = lane_info[lane][0]
            sc.line([(x0_line, ly), (lane_x[lane], ly)], col, sw=2 if direct else 1.6, dash=direct,
                    start="arrow" if "r" in d else "none", end="arrow" if "w" in d else "dot", opacity=op)

    def parse_link(self, s):
        p = s.split(":")
        if p[0] not in self.spec_lanes():
            raise SystemExit(f"unknown lane '{p[0]}' in link '{s}'")
        if len(p) < 2 or not set(p[1]) <= set("rw"):
            raise SystemExit(f"bad direction in link '{s}' (use r, w or rw)")
        return p[0], p[1], (p[2] if len(p) > 2 else "")

    def spec_lanes(self):
        return {ln["id"] for b in self.spec["bands"] for ln in b["lanes"]}

    def legend(self, x, y):
        sc, sp, c = self.sc, self.spec, self.cfg
        w = c["leg_w"]
        y0 = y
        y += 12
        sc.text(x + 16, y, w - 32, 22, "Legend", size=16, bold=True)
        y += 32
        sc.text(x + 16, y, w - 32, 14, "Line colour = system the logic app talks to", size=10, bold=True)
        y += 20
        for sid, s in sp["systems"].items():
            sc.line([(x + 16, y + 12), (x + 70, y + 12)], s["color"], sw=3)
            self.draw_logo(sid, x + 110, y - 2, 56, 26)
            sc.text(x + 150, y + 5, w - 170, 14, s["name"] + (f" — {s['legend']}" if s.get("legend") else ""), size=9)
            y += 30
        y += 6
        for txt, kw in [("Through APIM (AIP): solid. Arrow at the system = write", dict(start="none", end="arrow", dash=False)),
                        ("Read: arrow at the logic app, dot at the system", dict(start="arrow", end="dot", dash=False)),
                        ("Direct, not via APIM: dashed", dict(start="none", end="arrow", dash=True))]:
            sc.line([(x + 16, y + 8), (x + 90, y + 8)], "#555555", sw=2 if kw["dash"] else 1.6, **kw)
            sc.text(x + 104, y + 2, w - 120, 14, txt, size=9)
            y += 20
        y += 6
        sc.text(x + 16, y, w - 32, 14, "AIP components used by the logic app (faint = not used, ? = not itemised in the source)", size=9, bold=True)
        y += 18
        for k, lbl in sp.get("chip_legend", [["apim", "APIM: calls a slice on the API gateway"], ["eg", "Event Grid: subscribes to or publishes an event"],
                                             ["xslt", "XSLT translator function (shared Translate)"], ["fn", "Helper function app (dedicated workaround)"]]):
            sc.image(x + 20, y - 2, 18, 18, ("azure", icon(k)), label=k)
            sc.text(x + 48, y + 1, w - 64, 14, lbl, size=9)
            y += 22
        y += 4
        sc.rect(x + 16, y, 40, 16, fill="#ffffff", stroke="#9e9e9e", dash=True, rx=3, opacity=0.5)
        sc.text(x + 64, y + 2, w - 80, 14, "Faded dashed frame = disabled in production", size=9); y += 22
        sc.rect(x + 16, y, 40, 16, fill="#ffffff", stroke="#c62828", dash=True, rx=3)
        sc.text(x + 64, y + 2, w - 80, 14, "Red dashed frame = enabled, no traffic in Aug 2026", size=9); y += 28
        sc.rect(x + 16, y, w - 32, 1, fill="#e0e0e0", stroke="#e0e0e0", sw=0); y += 10
        for n, title, body in self.notes:
            lines = wrap(body, w - 80, 9)
            h = 14 + 11.5 * len(lines) + 8
            sc.badge(x + 16, y, n, "#333333", 22)
            sc.text(x + 48, y + 1, w - 64, 14, title, size=10, bold=True)
            sc.text(x + 48, y + 16, w - 64, 11.5 * len(lines) + 2, body, size=9, color="#333333")
            y += max(h, 30)
        y += 8
        tb = sp["meta"].get("titleblock", [])
        if tb:
            sc.rect(x + 16, y, w - 32, 18 * len(tb) + 8, fill="#ffffff", stroke="#333333", sw=1)
            for i, (k, v) in enumerate(tb):
                sc.text(x + 24, y + 5 + i * 18, 100, 14, k, size=9, bold=True)
                sc.text(x + 128, y + 5 + i * 18, w - 160, 14, v, size=9)
            y += 18 * len(tb) + 16
        if sp["meta"].get("source"):
            lines = wrap(sp["meta"]["source"], w - 32, 8)
            sc.text(x + 16, y, w - 32, 10 * len(lines) + 4, sp["meta"]["source"], size=8, color="#666666")
            y += 10 * len(lines) + 8
        return y


