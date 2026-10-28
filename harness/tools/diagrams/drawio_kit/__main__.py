"""CLI.

    python3 -m drawio_kit build spec.json -o out.drawio [--svg out.svg] [--png out.png]
    python3 -m drawio_kit icons <term>        # find real draw.io icon paths, e.g. "logic apps"
"""
import argparse, json, os, sys

from . import core, logos
from .layouts import lane_matrix

LAYOUTS = {"lane_matrix": lane_matrix}


def fetch_missing_logos(spec, base, builder):
    """Download a logo for every system that has none. Spec per system: fetch=false skips, search= product name, domain= favicon fallback."""
    for sid, s in spec["systems"].items():
        if s.get("fetch", True) is False or s.get("stencil") or builder.logo(sid) is not None:
            continue
        res = logos.fetch(s.get("search", s["name"]), os.path.join(base, "logos"), file_id=sid, domain=s.get("domain"))
        print(f"logo {sid}: " + (f"{res['source']} {res['title']} -> {res['path']}" if res else "not found, using name tile"))
        builder.logos.pop(sid, None)


def build(a):
    spec = json.load(open(a.spec, encoding="utf-8"))
    layout = LAYOUTS.get(spec.get("layout_type", "lane_matrix"))
    if layout is None:
        raise SystemExit(f"unknown layout_type; available: {', '.join(LAYOUTS)}")
    base = os.path.dirname(os.path.abspath(a.spec))
    b = layout.Builder(spec, base)
    if a.fetch_logos:
        fetch_missing_logos(spec, base, b)
    b.build()
    open(a.out, "w", encoding="utf-8").write(core.DrawioOut(b.W, b.H, spec["meta"].get("pagename", "Diagram")).render(b.sc))
    missing = core.check_icons(b.sc)
    for m in missing:
        print(f"WARNING: icon not in the draw.io library: {m} (find one with: icons <term>)", file=sys.stderr)
    svg = a.svg or (os.path.splitext(a.png)[0] + ".svg" if a.png else None)
    if svg:
        open(svg, "w", encoding="utf-8").write(core.SvgOut(b.W, b.H, core.find_drawio_lib()).render(b.sc))
    if a.png and not core.render_png(svg, a.png, b.W, b.H):
        print("WARNING: no Edge/Chrome found, PNG not rendered", file=sys.stderr)
    stats = ", ".join(f"{k}={v}" for k, v in b.stats.items() if k != "height")
    print(f"written {a.out} ({int(b.W)}x{int(b.H)}); counts per section: {stats}")
    tiles = [f"{s['name']} (logos/{sid}.png)" for sid, s in spec["systems"].items() if b.logo(sid) is None and not s.get("stencil")]
    if tiles:
        print("NOTE: no logo found, drawn as a square with the name: " + ", ".join(tiles)
              + ". Tell the user; drop the file into logos/ to replace it" + ("" if a.fetch_logos else ", or rerun with --fetch-logos") + ".")


def logo(a):
    res = logos.fetch(a.name, a.dir, file_id=a.id, domain=a.domain, source=a.source, dry=a.candidates, force=a.force)
    if not res:
        raise SystemExit(f"no logo found for '{a.name}'. Try --domain, --source, or leave it as a name tile.")
    if a.candidates:
        print(f"{res['source']}: {res['title']}\n  {res['url']}\n  {res['note']}")
    else:
        print(f"saved {res['path']} from {res['source']} ({res['title']}); open it to confirm it is the right logo")


def main():
    ap = argparse.ArgumentParser(prog="drawio_kit")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("build")
    p.add_argument("spec")
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--svg")
    p.add_argument("--png")
    p.add_argument("--fetch-logos", action="store_true", help="download logos for systems that have none (needs network)")
    p.set_defaults(fn=build)
    lg = sub.add_parser("logo", help="look up and download one logo")
    lg.add_argument("name")
    lg.add_argument("-d", "--dir", default="logos")
    lg.add_argument("--id", help="file name without extension (default: the name, lowercase)")
    lg.add_argument("--domain", help="enables the favicon fallback, e.g. afas.nl")
    lg.add_argument("--source", choices=["simpleicons", "commons", "favicon"])
    lg.add_argument("--candidates", action="store_true", help="show what would be downloaded, download nothing")
    lg.add_argument("--force", action="store_true", help="overwrite an existing file")
    lg.set_defaults(fn=logo)
    q = sub.add_parser("icons")
    q.add_argument("term")
    q.set_defaults(fn=lambda a: print("\n".join(core.search_icons(a.term)) or "no match (or draw.io library not found; set DRAWIO_LIB)"))
    a = ap.parse_args()
    a.fn(a)


main()
