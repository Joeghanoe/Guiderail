# Diagrams (draw.io generator)

Generate draw.io diagrams from a small JSON spec instead of writing a new script each time. Stdlib Python 3 only. An agent should write **only the spec**, never new drawing code. Playbook: draw-integration-diagram.

    ~/.golden-path-harness/harness/tools/diagrams/dk build spec.json -o "Name.drawio" --png "Name.preview.png"   # also writes Name.preview.svg
    ~/.golden-path-harness/harness/tools/diagrams/dk icons "logic apps"                                          # real draw.io icon paths, do not guess

    ~/.golden-path-harness/harness/tools/diagrams/dk logo "Salesforce" -d logos            # look up and download one logo (--candidates: dry run)
    ~/.golden-path-harness/harness/tools/diagrams/dk build spec.json -o X.drawio --fetch-logos   # download a logo for every system that has none

## Logo lookup

`drawio_kit/logos.py` looks a product up by name: Simple Icons (exact name, CC0 files in brand colour), then Wikimedia Commons (strict: file title must contain "logo" and every word of the name), then a site favicon, only when you give a `--domain` (or `"domain"` in the spec). It saves `logos/<id>.<svg|png>` and records source and URL in `logos/SOURCES.json`.

- Per system in the spec: `"search": "AFAS Software"` (product name to look up), `"domain": "afas.nl"` (favicon fallback), `"fetch": false` (internal systems; never look up, keep the name tile).
- Not found = the name tile stays, and the build ends with a `NOTE: no logo found, drawn as a square with the name: ...` line. Pass that on to the user in your summary; they can drop a file into `logos/` to replace the tile. Do not guess a domain or loosen the match.
- **Look at every downloaded logo** before using it (open the PNG preview): lookups can return the wrong or an old logo, and a favicon is low quality. Logos are trademarks; the licence note is in `SOURCES.json`.
- Only the product name or domain leaves the machine. Downloads are size-capped, must be a plain png or svg, and an svg with scripts is rejected (SEC.1). Existing files in `logos/` are never overwritten without `--force`.

## What is reusable and what is per diagram

| Part | Where | Per diagram? |
| --- | --- | --- |
| Scene primitives, draw.io + SVG backends, PNG preview | `drawio_kit/core.py` | no |
| Logo loading (png, svg, jpg, webp, avif, ico), square name tile when no logo | `core.py` | no |
| Icon lookup against the local draw.io library, missing-icon warning | `core.py`, `./dk icons` | no |
| Layout recipe | `drawio_kit/layouts/<name>.py` | only when no layout fits |
| Legend, numbered notes, title block | layout | no |
| **Spec (data)** | `spec.json` | **yes, this is all the agent writes** |

Layouts available: `lane_matrix` (default). Select with `"layout_type"` in the spec.

- `lane_matrix`: rows (apps, functions, jobs) grouped per flow on the left, vertical lanes (gateway slices, direct paths) on the right headed by the system logo. A row draws one horizontal line per system it talks to, coloured by system. Use for "which component talks to which system, and through what".

A new picture type (for example the DNK zones-and-icons as-is/to-be) is a new file in `layouts/` that reuses `core`, registered in `LAYOUTS` in `__main__.py`. Build it once, then it is data-only too.

## Spec (lane_matrix)

See `examples/minimal.json`. Shape:

    meta        title, subtitle, pagename, source, titleblock [[key, value], ...]
    systems     id -> {name, color, logo?, tile?, legend}      logo: path relative to the spec, else logos/<id>.<ext>
    bands       [{id, title, icon?, direct?, note?, lanes: [{id, system, label, note?}]}]   direct: true = bypasses the gateway (dashed)
    sections    [{id, title, fill, expect?, flows: [{id, title, note, rows: [row]}]}]
    row         n name, s sub-line, r runs, st disabled|idle, u "eg,xslt,fn", q "xslt" (not itemised, shows ?),
                l ["lane:r|w|rw", ...], tip tooltip, kind logicapp|consumer, icon alias, apim true
    optional    chips, chip_legend, icons (alias -> path), extra_notes, layout (spacing overrides)

Notes are numbered automatically: flows first, then bands and lanes, then `extra_notes`. `expect` on a section prints a warning when the row count differs from the source document, so check it.

## Conventions

- No logo available: leave `logo` out. The kit draws a square tile with the name; drop `logos/<id>.png` in later to replace it.
- Icons: use an alias from `ICONS` in `core.py`, a path under `azure2/` (e.g. `integration/Logic_Apps.svg`) or a full `img/lib/...` path. `./dk build` warns about paths missing from the library.
- The `.drawio` references draw.io's built-in icons (same as the DNK files); the SVG/PNG preview embeds them from the local library (VS Code draw.io extension, or set `DRAWIO_LIB` to the draw.io `webapp` folder).
- Check the PNG preview before saying it is done; it is the only visual check available without opening draw.io.
