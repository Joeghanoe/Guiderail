"""Look up and download software logos. Stdlib only.

Sources, tried in this order (or one chosen with source=):
  simpleicons  exact product name match in Simple Icons (CC0 files, brand colour, glyph or wordmark)
  commons      Wikimedia Commons file whose title contains "logo" and every word of the name (strict; the search is noisy)
  favicon      site icon for an explicit domain only (low quality, last resort)

Only the product name or domain is sent out. Downloaded files are data (SEC.1): size-capped, type-checked, SVG with
scripts rejected. Each download is recorded in <dir>/SOURCES.json. Logos are trademarks: check the licence and
look at the file before it goes into a customer document.
"""
import datetime, json, os, re, urllib.parse, urllib.request

UA = "TeamValue-harness-diagrams/1.0 (logo lookup)"
SI = "https://cdn.jsdelivr.net/npm/simple-icons@13"
MAX_BYTES = 2_000_000


def _get(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError(f"download over {MAX_BYTES} bytes: {url}")
    return data


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _ext_ok(data):
    """Return the file extension when data looks like a safe svg or png, else None."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    head = data[:4000].lower()
    if b"<svg" in head and b"<script" not in data.lower() and b"onload" not in data.lower():
        return ".svg"
    return None


def _simpleicons(name, dry):
    data = json.loads(_get(SI + "/_data/simple-icons.json"))
    icons = data["icons"] if isinstance(data, dict) else data
    want = norm(name)
    hit = next((i for i in icons if norm(i["title"]) == want or norm(i.get("slug", "")) == want), None)
    if not hit:
        return None
    slug = hit.get("slug") or re.sub(r"[^a-z0-9]", "", hit["title"].lower().replace("+", "plus").replace(".", "dot").replace("&", "and"))
    url = f"{SI}/icons/{slug}.svg"
    res = dict(source="simpleicons", url=url, title=hit["title"],
               note="Simple Icons (CC0 file), brand colour; trademark belongs to the owner")
    if dry:
        return res
    svg = _get(url).decode("utf-8", "ignore")
    svg = svg.replace("<svg ", f'<svg fill="#{hit["hex"]}" ', 1)
    res["data"] = svg.encode("utf-8")
    return res


def _commons(name, dry):
    q = urllib.parse.urlencode({"action": "query", "generator": "search", "gsrsearch": f"{name} logo", "gsrnamespace": 6,
                                "gsrlimit": 8, "prop": "imageinfo", "iiprop": "url|mime", "iiurlwidth": 400, "format": "json"})
    pages = json.loads(_get("https://commons.wikimedia.org/w/api.php?" + q)).get("query", {}).get("pages", {})
    words = [w for w in re.split(r"\W+", name.lower()) if len(w) > 1]
    for p in sorted(pages.values(), key=lambda p: p.get("index", 99)):
        title = p["title"].lower()
        info = (p.get("imageinfo") or [{}])[0]
        if "logo" in title and all(w in title for w in words) and info.get("mime", "").startswith("image/"):
            url = info.get("thumburl") or info.get("url")
            res = dict(source="commons", url=url, title=p["title"],
                       note=f"Wikimedia Commons {p['title']} ({info.get('descriptionurl', '')}); check licence and trademark")
            if not dry:
                res["data"] = _get(url)
            return res
    return None


def _favicon(domain, dry):
    url = "https://www.google.com/s2/favicons?" + urllib.parse.urlencode({"domain": domain, "sz": 128})
    res = dict(source="favicon", url=url, title=domain, note="site favicon, low quality; replace with a proper logo")
    if not dry:
        res["data"] = _get(url)
    return res


def fetch(name, dest_dir, file_id=None, domain=None, source=None, dry=False, force=False):
    """Download a logo for `name` into dest_dir/<file_id>.<ext>. Returns a result dict, or None when nothing matched.
    dry=True only reports the candidate. favicon is only used when domain is given."""
    order = [source] if source else ["simpleicons", "commons"] + (["favicon"] if domain else [])
    for src in order:
        try:
            if src == "favicon":
                res = _favicon(domain, dry)
            elif src in ("simpleicons", "commons"):
                res = (_simpleicons if src == "simpleicons" else _commons)(name, dry)
            else:
                raise SystemExit(f"unknown source '{src}' (simpleicons, commons, favicon)")
        except SystemExit:
            raise
        except Exception as e:  # network, parse: try the next source
            print(f"  {src}: {e}")
            continue
        if not res:
            continue
        if dry:
            return res
        ext = _ext_ok(res["data"])
        if not ext:
            print(f"  {src}: rejected (not a plain png/svg)")
            continue
        fid = file_id or norm(name)
        os.makedirs(dest_dir, exist_ok=True)
        path = os.path.join(dest_dir, fid + ext)
        if os.path.exists(path) and not force:
            raise SystemExit(f"{path} exists; use force to overwrite")
        open(path, "wb").write(res.pop("data"))
        res["path"] = path
        reg = os.path.join(dest_dir, "SOURCES.json")
        log = json.load(open(reg)) if os.path.exists(reg) else {}
        log[os.path.basename(path)] = dict(name=name, source=res["source"], url=res["url"], note=res["note"],
                                           fetched=datetime.date.today().isoformat())
        json.dump(log, open(reg, "w"), indent=2)
        return res
    return None
