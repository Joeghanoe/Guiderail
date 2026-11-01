---
type: Playbook
title: Draw an integration diagram
description: Turn an integration analysis into a one-page draw.io diagram (which component talks to which system, through what) by writing a spec for the diagram generator, never new drawing code.
tags: [diagrams, drawio, integration, lld]
status: stable
verified: { by: human:joeghanoe, at: 2026-11-01T20:11:03Z }
---

# Steps

1. **Fix the question** in one sentence: which components, which systems, which view (for example "every logic app, and the SaaS system and path it uses"). One page, one diagram; do not split it over sheets unless the user asks.
2. **Read the generator README** `~/.golden-path-harness/harness/tools/diagrams/README.md` and the example `examples/minimal.json`. Do not write a new script. If no layout fits the picture, add a layout file next to `lane_matrix.py` and register it, then continue with a spec (see the README).
3. **Take the facts from the source document**, not from memory: names, triggers, counts, which system each component calls and whether it goes through the gateway or directly. Mark what the source does not say (`q`, a grey lane) instead of guessing. Set `expect` on each section to the count the source states.
4. **Write the spec** next to the customer's analysis files. Systems carry a colour; a logo is optional. Without a logo the tool draws a square tile with the name, so a missing logo never blocks the diagram. Logos go in `logos/` next to the spec (png, svg, jpg, webp, avif, ico). Let the tool look them up: set `"fetch": false` on internal systems and run the build with `--fetch-logos` (or `dk logo "<name>"` for one). **Open each downloaded logo** and keep it only if it is the right product; delete it otherwise and leave the tile. Add `"domain"` only for a site you know belongs to the product.
5. **Find icons with the tool**: `~/.golden-path-harness/harness/tools/diagrams/dk icons "<term>"`. Do not guess paths; the build warns about a path that is not in the draw.io library.
6. **Build and look at it**: `~/.golden-path-harness/harness/tools/diagrams/dk build spec.json -o "<name>.drawio" --png "<name>.preview.png"`. Read the PNG before you say it is done, check the `counts per section` line against the source, and report that the `.drawio` itself was not opened in draw.io if you did not.
7. **Hand over** the `.drawio`, the preview and the spec. Say what is assumed or not itemised in the source, and which logos are still name tiles.

# Notes

- Customer content (specs, logos, outputs) stays in the customer's folder, not in the harness (examples are project-agnostic).
- The generator is data-driven so the next diagram costs a spec, not a script (H.2).
