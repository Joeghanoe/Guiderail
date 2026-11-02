#!/usr/bin/env python3
"""Rank candidates for compressing harness prose. A candidate finder, never an authority.

Harness prose is agent-consumed context: every byte of an always-loaded file is paid on every task,
and every byte `bundle.py select` returns is paid on every change it matches. This script measures what
can be measured about that cost - bytes, duplication across files, filler phrasing, prose that reads as
narrative rather than instruction, section cost against how often a file is loaded, frontmatter against
body - and ranks the result as suggestions.

It cannot tell whether a sentence carries value. No signal here reads meaning, so a passage can look
padded by every signal and still be the one sentence that stops a reviewer over-applying a rule. Only
`tools/review/eval.py` can show that behaviour survived a cut, and only for behaviour the examples cover.
Decide with the evals; use this to decide where to look first. See /playbooks/compress-harness-prose.md.

Commands:
  report        bytes, frontmatter ratio, load weight and signal counts per file and per folder
  duplicates    passages repeated across files, with the definition site where there is one
  candidates    ranked suggestions: bytes identified per unit of risk, cheapest and safest first

The bundle root is the directory above this script's directory, or --root <dir>.

Example:
  python3 -I harness/tools/harness/density.py candidates --top 15
"""

import argparse
import bisect
import collections
import importlib.util
import json
import pathlib
import re
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bundle  # noqa: E402

# Folders whose Markdown an agent loads as instructions. Everything else under the bundle is machine input.
PROSE_DIRS = ("rules", "playbooks", "gates", "principles", "examples")
# Loaded before an agent opens anything, so their bytes are paid on every task (see bundle.py budget).
ALWAYS_LOADED = ("/AGENTS.base.md", "/index.md")
SHINGLE = 8                 # words; shorter than this matches ordinary English, longer misses restatements
SCHEMA_HOLDERS = 3          # at or above this, repeats inside one folder are that folder's template
MIN_WEIGHT = 0.1            # a rule no sample path matches is still loaded sometimes; never weight it zero
MIN_CANDIDATE_BYTES = 120   # below this a cut is not worth an eval run
MAX_RISK = 5
RISK = {"duplicate": 1,     # the same instruction twice: the definition site keeps it, the copy goes
        "padding": 2,       # a sentence whose phrasing marks it as filler
        "narrative": 3}     # reads as narrative rather than instruction: the weakest signal here
RISK_UNCOVERED = 2          # no gating eval scenario exercises this file
RISK_BLOCKER = 1            # the rule is a blocker: a reviewer that stops applying it fails loudly late
RISK_NO_DEFINITION = 1      # copies with no definition site: someone must choose the one home first

REFUSALS = (
    ("examples/", "an example is the eval instrument; compressing one moves the measurement, not the cost"),
    ("principles/", "a principle is a pointer to its external authority, not harness prose"),
)
GENERATED_REFUSAL = "written by `bundle.py index` from the frontmatter it lists; it shrinks when they do"
CAUTIONS = {"/AGENTS.base.md": "always loaded, so the highest reach in the bundle, and its restatements of "
                               "the rules are deliberate: cut padding only, never a restated rule ID",
            "/index.md": "always loaded, and `bundle.py check` requires a link to every top-level folder"}

# Masked before any prose signal runs: machine-read or protected text that compression must not touch.
FRONTMATTER = re.compile(r"\A---\n.*?\n---\n", re.S)
FENCE = re.compile(r"^(```|~~~)[^\n]*\n.*?^\1[^\n]*$", re.S | re.M)
TABLE = re.compile(r"^[ \t]*\|.*$", re.M)
HEADING = re.compile(r"^(#{1,6})[ \t]+(.*)$", re.M)
INLINE_CODE = re.compile(r"`[^`\n]*`")
LINK_TARGET = re.compile(r"\]\([^)\n]*\)")            # the text stays prose, the target is machine input
# A section whose reasoning is the thing being preserved: it stops a reviewer over-applying the rule,
# or it is the example an eval scores against.
PROTECTED_HEADING = re.compile(r"^#{1,6}\s+(Boundar|Variant|Good example|Bad example|Situation)", re.I)
RULE_ID = re.compile(r"\b[A-Z]{1,5}\.\d+\b")
PRINCIPLE_ID = re.compile(r"\bP\d{1,2}\b")
WORD = re.compile(r"[a-z0-9]+")
SENTENCE = re.compile(r"\S[^.!?]*[.!?]", re.S)
# Phrasings that correlate with filler: a sentence that announces something instead of instructing it,
# or that explains what a capable model already knows. A weak proxy for padding, never proof of it.
PADDING = re.compile(r"\b(it is important to|it should be noted|note that|please note|remember that|"
                     r"keep in mind|bear in mind|in other words|that is to say|as a best practice|"
                     r"best practice is|in general|generally speaking|of course|obviously|simply put|"
                     r"basically|needless to say|it goes without saying|as mentioned( above)?|"
                     r"in today's|at the end of the day)\b", re.I)
# Instructive: the sentence cites something checkable, forbids something, or tells the agent to act.
# A list item counts: in this bundle a bullet is how an instruction is written, not how prose is padded.
ANCHOR_CITE = re.compile(r"`|\]\(|/\w|\d")
ANCHOR_VERB = re.compile(r"\b(must|never|always|only|no|not|nor|neither|none|cannot|can't|don't|doesn't|"
                         r"do|does|may|run|runs|use|uses|write|writes|keep|keeps|stop|stops|ask|asks|"
                         r"report|reports|check|checks|open|opens|cite|cites|refuse|refuses|block|blocks|"
                         r"propose|proposes|state|states|say|says|count|name|names|follow|follows)\b", re.I)
LIST_ITEM = re.compile(r"^[ \t]*(?:[-*+]|\d+\.)[ \t]")

Token = collections.namedtuple("Token", "text start end line block")
LIMITS = (
    "This is a candidate finder. It ranks where to look; it never decides that a cut is safe.",
    "No signal here measures meaning. A passage can be padded by every signal and still be the sentence "
    "that keeps a reviewer from over-applying a rule.",
    "Only tools/review/eval.py can show that reviewer behaviour survived a cut, and only for the "
    "behaviour the examples cover. A flat pass rate licenses a cut; it does not prove the cut was free.",
    "Text no example exercises is the most dangerous text to compress, not the safest: nothing reports its "
    "loss. Candidates in an uncovered file carry a risk penalty for that reason.",
    "A duplicate is the exception: de-duplicating keeps the instruction at its definition site, so its "
    "safety does not rest on eval coverage.",
    "The narrative signal cannot tell a terse instruction from a restatement, so it is the weakest of "
    "the three and always ranks last. Read every narrative candidate before touching it.",
    "Copies of one passage are listed per file. Keeping one of N copies saves N-1 of the byte estimates, "
    "not all of them.",
    "load weight is measured against the path corpus given (--paths, else git ls-files of the repo). A "
    "corpus is a sample: a rule this corpus never matches is still loaded on some change.",
)


def blank(match):
    """Replace a region with spaces, so every later offset and line number still points at the source."""
    return re.sub(r"\S", " ", match.group(0))


def prose_text(raw):
    """The raw file with machine-read and quoted regions blanked out: what is left is prose."""
    for pattern in (FRONTMATTER, FENCE, TABLE, HEADING, INLINE_CODE, LINK_TARGET):
        raw = pattern.sub(blank, raw)
    return raw


def headings(raw):
    """[(line, "# Heading")] in source order, for naming the section a candidate sits in."""
    return [(raw.count("\n", 0, m.start()) + 1, m.group(0).strip()) for m in HEADING.finditer(raw)]


def heading_at(marks, line):
    name = "(top)"
    for at, text in marks:
        if at <= line:
            name = text
        else:
            break
    return name


def protected_spans(raw):
    """Character ranges compression must leave alone: frontmatter, code, tables and protected sections.

    A line that merely cites a rule ID is not protected; the citation is what a shortened passage keeps.
    """
    spans = [(m.start(), m.end()) for pattern in (FRONTMATTER, FENCE, TABLE)
             for m in pattern.finditer(raw)]
    marks = [m for m in HEADING.finditer(raw) if PROTECTED_HEADING.match(m.group(0))]
    for mark in marks:
        level = len(mark.group(1))
        end = len(raw)
        for other in HEADING.finditer(raw, mark.end()):
            if len(other.group(1)) <= level:
                end = other.start()
                break
        spans.append((mark.start(), end))
    return spans


def masked_content(document, start, end):
    """The characters inside a span that the prose mask blanked: inline code, a link target, a table cell.

    Two passages with the same words but different masked content are one sentence around two different
    parameters: a template to factor, not a copy to delete.
    """
    return " ".join("".join(raw for raw, shown in zip(document.raw[start:end], document.prose[start:end])
                            if raw != shown).split())


def overlaps(span, spans):
    return any(start < span[1] and span[0] < end for start, end in spans)


BLANK_LINE = re.compile(r"\n[ \t]*\n")


def blocks(prose):
    """Prose split on blank lines: one paragraph, list or bullet run each.

    Masked regions become whitespace, so a heading, code block or table ends the block before it. Nothing
    measured here crosses one, which keeps a passage from spanning the code or table that sits between
    two sentences.
    """
    spans, at = [], 0
    for gap in BLANK_LINE.finditer(prose):
        if prose[at:gap.start()].strip():
            spans.append((at, gap.start()))
        at = gap.end()
    if prose[at:].strip():
        spans.append((at, len(prose)))
    return spans


def tokens_of(prose):
    """Lowercase words with their offsets, line numbers and block, in source order."""
    line_starts = [0] + [m.end() for m in re.finditer(r"\n", prose)]
    lowered = prose.lower()
    tokens = []
    for index, (start, end) in enumerate(blocks(prose)):
        for match in WORD.finditer(lowered, start, end):
            line = bisect.bisect_right(line_starts, match.start())
            tokens.append(Token(match.group(0), match.start(), match.end(), line, index))
    return tokens


class Document:
    """One agent-consumed Markdown file with everything the signals need, measured once."""

    def __init__(self, root, path):
        self.path = path
        self.key = "/" + path.relative_to(root).as_posix() if path.is_relative_to(root) else "/" + path.name
        self.raw = path.read_text(encoding="utf-8")
        self.bytes = len(self.raw.encode("utf-8"))
        self.meta, body = bundle.parse(path)
        self.meta = self.meta or {}
        self.frontmatter_bytes = self.bytes - len(body.encode("utf-8"))
        self.prose = prose_text(self.raw)
        self.tokens = tokens_of(self.prose)
        self.headings = headings(self.raw)
        self.protected = protected_spans(self.raw)
        self.folder = self.key.rsplit("/", 1)[0] or "/"
        self.kind = bundle.unquote(self.meta.get("type", "")) or "Text"
        # Every index.md but the bundle's own is written by `bundle.py index` from the frontmatter it lists.
        self.generated = self.key.endswith("/" + bundle.INDEX) and self.key != "/" + bundle.INDEX
        self.rule_id = bundle.unquote(self.meta.get("rule_id", ""))
        self.severity = bundle.unquote(self.meta.get("severity", ""))

    def refusal(self):
        """Why compression should not start here at all, or None."""
        if self.generated:
            return GENERATED_REFUSAL
        for marker, reason in REFUSALS:
            if marker in self.key:
                return reason
        return None

    def sentences(self):
        """(span, raw text, signal) per prose sentence, inside one block and outside every protected span.

        signal is "padding", "narrative" or None. A sentence on a list line is instruction by convention.
        """
        for start, end in blocks(self.prose):
            for match in SENTENCE.finditer(self.prose, start, end):
                span = (match.start(), match.end())
                if overlaps(span, self.protected) or len(match.group(0).split()) < 4:
                    continue
                text = self.raw[match.start():match.end()]
                line_start = self.raw.rfind("\n", 0, match.start()) + 1
                listed = bool(LIST_ITEM.match(self.raw, line_start))
                if PADDING.search(text):
                    yield span, text, "padding"
                elif not (listed or ANCHOR_CITE.search(text) or ANCHOR_VERB.search(text)):
                    yield span, text, "narrative"
                else:
                    yield span, text, None

    def frontmatter_ratio(self):
        return round(self.frontmatter_bytes / self.bytes, 2) if self.bytes else 0.0


def load_corpus(root, paths_file):
    """Sample of the paths a change touches, for how often select() would return a rule."""
    if paths_file:
        text = pathlib.Path(paths_file).read_text(encoding="utf-8")
        return [line.strip() for line in text.splitlines() if line.strip()]
    listed = subprocess.run(["git", "-C", str(root.parent), "ls-files"],
                            capture_output=True, text=True, check=False)
    return [line for line in listed.stdout.splitlines() if line]


def load_weight(document, corpus):
    """How often this file's bytes are paid: 1.0 always loaded, less for a rule select() rarely returns.

    Floored at MIN_WEIGHT: a corpus is a sample, and a playbook is loaded by name, not by applies_to.
    """
    if document.key in ALWAYS_LOADED:
        return 1.0
    globs = []
    if document.kind == "Rule":
        try:
            globs = [bundle.glob_to_regex(g) for g in json.loads(document.meta.get("applies_to", "[]"))]
        except ValueError:
            globs = []
    if not globs or not corpus:
        return MIN_WEIGHT
    matched = sum(1 for path in corpus if any(g.match(path) for g in globs))
    return round(MIN_WEIGHT + (1 - MIN_WEIGHT) * matched / len(corpus), 3)


def eval_coverage(root):
    """Gating eval scenarios per rule file, taken from eval.py so this cannot drift from the instrument.

    Returns {rule file key: gating scenario count}, or None when the evaluator cannot be read.
    """
    source = root / "tools" / "review" / "eval.py"
    if not source.is_file():
        return None
    try:
        spec = importlib.util.spec_from_file_location("harness_eval_for_density", source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        by_rule_id = {}
        for path, meta, _ in bundle.concepts(root):
            if meta and bundle.unquote(meta.get("type", "")) == "Rule":
                by_rule_id[bundle.unquote(meta.get("rule_id", ""))] = "/" + path.relative_to(root).as_posix()
        counts = collections.Counter()
        for _, scenario, *_ in module.from_cases(root):
            if scenario.get("advisory"):
                continue
            expect = scenario.get("expect", {})
            ids = [want["rule_id"] for want in expect.get("must_find", [])] + expect.get("must_not_find", [])
            for rule_id in {i for i in ids if i in by_rule_id}:
                counts[by_rule_id[rule_id]] += 1
        return dict(counts)
    except Exception as error:                                  # a bundle that cannot be evaluated
        print(f"density: eval coverage unavailable ({type(error).__name__}: {error})", file=sys.stderr)
        return None


def documents(root):
    paths = []
    base = root.parent / "AGENTS.base.md"
    if base.is_file():
        paths.append(base)
    if (root / bundle.INDEX).is_file():
        paths.append(root / bundle.INDEX)
    for name in PROSE_DIRS:
        if (root / name).is_dir():
            paths += sorted(p for p in (root / name).rglob("*.md"))
    return {d.key: d for d in (Document(root, p) for p in paths)}


def merge_runs(indexes, width):
    """Merge overlapping shingle positions into one passage span of word indexes."""
    spans = []
    for index in sorted(indexes):
        if spans and index <= spans[-1][1]:
            spans[-1][1] = max(spans[-1][1], index + width - 1)
        else:
            spans.append([index, index + width - 1])
    return spans


def duplicate_passages(docs, width=SHINGLE):
    """Passages that appear in more than one file, as {(holder set, words): [passage, ...]}.

    One bucket per distinct repeated passage: two unrelated passages shared by the same pair of files
    are two findings, not one.
    """
    holders = collections.defaultdict(set)
    grams = {}
    # A generated index repeats the descriptions it lists by construction: that is not duplicated prose.
    docs = {key: document for key, document in docs.items() if not document.generated}
    for key, document in docs.items():
        tokens = document.tokens
        grams[key] = [(i, tuple(t.text for t in tokens[i:i + width]))
                      for i in range(len(tokens) - width + 1)
                      if tokens[i].block == tokens[i + width - 1].block]
        for _, gram in grams[key]:
            holders[gram].add(key)
    buckets = collections.defaultdict(list)
    for key, document in docs.items():
        hits = collections.defaultdict(list)
        for index, gram in grams[key]:
            group = holders[gram]
            if len(group) > 1:
                hits[frozenset(group)].append(index)
        for group, indexes in hits.items():
            for first, last in merge_runs(indexes, width):
                tokens = document.tokens
                last = min(last, len(tokens) - 1)
                start, end = tokens[first].start, tokens[last].end
                words = tuple(token.text for token in tokens[first:last + 1])
                buckets[(group, words)].append({
                    "file": key, "start": start, "end": end,
                    "line": tokens[first].line, "end_line": tokens[last].line,
                    "heading": heading_at(document.headings, tokens[first].line),
                    "bytes": len(document.raw[start:end].encode("utf-8")),
                    "parameters": masked_content(document, start, end),
                    "text": " ".join(document.raw[start:end].split()),
                })
    return buckets


def classify(key, passages, docs):
    """Why this passage repeats: a folder's template, a restatement of a rule, or copies with no home."""
    group = key[0]
    folders = {docs[p["file"]].folder for p in passages}
    if len(group) >= SCHEMA_HOLDERS and len(folders) == 1:
        folder = next(iter(folders))
        siblings = sum(1 for d in docs.values() if d.folder == folder)
        # One heading in every holder, or most of the folder: either way it is the folder's template slot.
        if len({p["heading"] for p in passages}) == 1 or len(group) * 2 >= siblings:
            return "schema", None
    if len({p["parameters"] for p in passages}) > 1:
        # The same sentence around a different parameter: a template to factor, not a copy to delete.
        return "pattern", None
    cited = {i for p in passages for i in RULE_ID.findall(p["text"])}
    by_rule_id = {d.rule_id: name for name, d in docs.items() if d.rule_id}
    for rule_id in sorted(cited):
        if rule_id in by_rule_id:
            return "restatement", by_rule_id[rule_id]
    rules = sorted(k for k in group if docs[k].kind == "Rule")
    if len(rules) == 1:
        return "restatement", rules[0]
    # Text already in the always-loaded instructions is in context before the copy is ever opened.
    always = sorted(k for k in group if k in ALWAYS_LOADED)
    if always:
        return "restatement", always[0]
    return "copies", None


def capped(points):
    """Risk points, bounded: the scale is an ordering of candidates, not a probability."""
    return min(MAX_RISK, max(1, points))


def duplicate_candidates(docs, buckets):
    out = []
    for key, passages in buckets.items():
        group = key[0]
        reason, definition = classify(key, passages, docs)
        for passage in passages:
            document = docs[passage["file"]]
            if document.refusal() or overlaps((passage["start"], passage["end"]), document.protected):
                continue
            if passage["file"] == definition or passage["file"] in ALWAYS_LOADED:
                continue            # the definition site keeps the text; an always-loaded summary is by design
            if reason == "schema":
                continue            # a template slot: changing it is a schema change, not a compression
            points, flags = RISK["duplicate"], ["duplicate"]
            if reason != "restatement":
                points += RISK_NO_DEFINITION
                flags.append(reason if reason == "pattern" else "no-definition-site")
            if document.severity == "blocker":
                points += RISK_BLOCKER
                flags.append("blocker")
            risk = capped(points)
            others = sorted(k for k in group if k != passage["file"])
            editable = sorted(k for k in group
                              if not docs[k].refusal() and k not in ALWAYS_LOADED and k != definition)
            keep = sorted(set(RULE_ID.findall(passage["text"])) | set(PRINCIPLE_ID.findall(passage["text"])))
            out.append({
                "signal": "duplicate", "file": passage["file"], "section": passage["heading"],
                "lines": [passage["line"], passage["end_line"]], "bytes": passage["bytes"],
                "risk": risk, "flags": flags, "also_in": others,
                "definition": definition, "preserve": keep,
                "action": (f"cut the restatement, keep the citation ({', '.join(keep)})" if definition and keep
                           else f"replace with a link to {definition}" if definition
                           else "same wording, different parameter: factor the sentence, keep each parameter"
                           if reason == "pattern"
                           else f"keep one of {len(editable)} editable copies and link the rest"
                           if len(editable) > 1
                           else "the only editable copy: give this text one home and link it"),
                "text": passage["text"][:160],
            })
    return out


def prose_candidates(docs, coverage):
    """Padding and unanchored prose, summed per section: a section is the unit an editor rewrites."""
    out = []
    for key, document in docs.items():
        if document.refusal():
            continue
        uncovered = coverage is not None and not coverage.get(key)
        sections = collections.defaultdict(lambda: {"padding": [0, 0], "narrative": [0, 0], "line": 0})
        for (start, _), text, signal in document.sentences():
            line = document.raw.count("\n", 0, start) + 1
            section = sections[heading_at(document.headings, line)]
            section["line"] = section["line"] or line
            if signal:
                section[signal][0] += len(text.encode("utf-8"))
                section[signal][1] += 1
        for heading, found in sections.items():
            for signal in ("padding", "narrative"):
                size, count = found[signal]
                if size < MIN_CANDIDATE_BYTES:
                    continue
                points, flags = RISK[signal], [signal]
                if uncovered:
                    points += RISK_UNCOVERED
                    flags.append("uncovered-by-evals")
                if document.severity == "blocker":
                    points += RISK_BLOCKER
                    flags.append("blocker")
                risk = capped(points)
                out.append({
                    "signal": signal, "file": key, "section": heading, "lines": [found["line"], found["line"]],
                    "bytes": size, "risk": risk, "flags": flags, "also_in": [], "definition": None,
                    "preserve": [], "text": f"{count} sentence(s) in this section",
                    "action": ("drop the announcing phrase and keep the instruction" if signal == "padding"
                               else "read it: narrative here may be a terse instruction the signal misread"),
                })
    return out


def rank(docs, candidates, corpus):
    for candidate in candidates:
        weight = load_weight(docs[candidate["file"]], corpus)
        candidate["load_weight"] = weight
        candidate["score"] = round(candidate["bytes"] * weight / candidate["risk"], 1)
    # Risk first, so the list starts where the cut is cheap and safe rather than where it is merely long.
    candidates.sort(key=lambda c: (c["risk"], -c["score"], c["file"], c["section"]))
    return candidates


def collect(root, args):
    docs = documents(root)
    corpus = load_corpus(root, args.paths)
    coverage = eval_coverage(root)
    buckets = duplicate_passages(docs, args.shingle)
    return docs, corpus, coverage, buckets


def print_limits():
    print("\nWhat this does not tell you:")
    for line in LIMITS:
        print(f"  - {line}")


def cmd_report(root, args):
    docs, corpus, coverage, buckets = collect(root, args)
    duplicated = collections.Counter()
    for passages in buckets.values():
        for passage in passages:
            duplicated[passage["file"]] += passage["bytes"]
    rows, folders = [], collections.Counter()
    for key, document in sorted(docs.items()):
        counted = collections.Counter()
        for _, text, signal in document.sentences():
            if signal:
                counted[signal] += len(text.encode("utf-8"))
        padding, narrative = counted["padding"], counted["narrative"]
        row = {"file": key, "bytes": document.bytes, "frontmatter_ratio": document.frontmatter_ratio(),
               "load_weight": load_weight(document, corpus),
               "eval_scenarios": None if coverage is None else coverage.get(key, 0),
               "duplicated_bytes": duplicated.get(key, 0), "padding_bytes": padding,
               "narrative_bytes": narrative, "refused": document.refusal(),
               "caution": CAUTIONS.get(key)}
        rows.append(row)
        folders[document.folder] += document.bytes
    if args.json:
        print(json.dumps({"files": rows, "folders": dict(sorted(folders.items())), "limits": list(LIMITS)},
                         indent=2))
        return 0
    print(f"{'file':<58}{'bytes':>7}{'front':>6}{'load':>6}{'evals':>6}{'dup':>6}{'pad':>5}{'narr':>7}")
    for row in sorted(rows, key=lambda r: -(r["duplicated_bytes"] + r["padding_bytes"]
                                            + r["narrative_bytes"]))[:args.top]:
        evals = "-" if row["eval_scenarios"] is None else row["eval_scenarios"]
        print(f"{row['file']:<58}{row['bytes']:>7}{row['frontmatter_ratio']:>6}{row['load_weight']:>6}"
              f"{evals:>6}{row['duplicated_bytes']:>6}{row['padding_bytes']:>5}{row['narrative_bytes']:>7}"
              + (f"  refused: {row['refused']}" if row["refused"] else ""))
    print(f"\n{len(rows)} file(s), {min(args.top, len(rows))} shown, most signal first.")
    print("folders:")
    for folder, size in sorted(folders.items()):
        print(f"  {folder:<56}{size:>7}")
    print_limits()
    return 0


def cmd_duplicates(root, args):
    docs, _, _, buckets = collect(root, args)
    found = []
    for key, passages in sorted(buckets.items(), key=lambda item: -max(p["bytes"] for p in item[1])):
        reason, definition = classify(key, passages, docs)
        found.append({"reason": reason, "definition": definition, "files": sorted(key[0]),
                      "bytes": max(p["bytes"] for p in passages),
                      "copies": [{"file": p["file"], "line": p["line"], "section": p["heading"],
                                  "bytes": p["bytes"]} for p in sorted(passages, key=lambda p: p["file"])],
                      "text": max(passages, key=lambda p: p["bytes"])["text"][:200]})
    if args.json:
        print(json.dumps({"duplicates": found, "limits": list(LIMITS)}, indent=2))
        return 0
    for item in found[:args.top]:
        print(f"{item['bytes']:>5} bytes  {item['reason']}"
              + (f", defined in {item['definition']}" if item["definition"] else ""))
        for copy in item["copies"]:
            print(f"        {copy['file']}:{copy['line']}  under {copy['section']}")
        print(f"        \"{item['text']}\"")
    print(f"\n{len(found)} repeated passage(s) of {args.shingle}+ words across {len(docs)} files.")
    print("A 'schema' repeat is a folder's template, not padding; de-duplicating one is a schema change.")
    print_limits()
    return 0


def cmd_candidates(root, args):
    docs, corpus, coverage, buckets = collect(root, args)
    candidates = rank(docs, duplicate_candidates(docs, buckets)
                      + prose_candidates(docs, coverage), corpus)
    total = sum(c["bytes"] for c in candidates)
    if args.json:
        print(json.dumps({"candidates": candidates[:args.top], "identified_bytes": total,
                          "eval_coverage_available": coverage is not None, "limits": list(LIMITS)}, indent=2))
        return 0
    if coverage is None:
        print("eval coverage unavailable: risk is understated for every prose candidate below.\n")
    for index, candidate in enumerate(candidates[:args.top], 1):
        print(f"{index:>3}. score {candidate['score']:>7}  {candidate['bytes']:>4} bytes  "
              f"risk {candidate['risk']}  load {candidate['load_weight']}  [{candidate['signal']}]")
        print(f"     {candidate['file']}:{candidate['lines'][0]} under {candidate['section']}")
        print(f"     {candidate['action']}")
        if candidate["also_in"]:
            print(f"     also in: {', '.join(candidate['also_in'])}")
        if candidate["flags"][1:]:
            print(f"     flags: {', '.join(candidate['flags'][1:])}")
        print(f"     {candidate['text']}")
    print(f"\n{len(candidates)} candidate(s), {total} bytes identified"
          f" ({min(args.top, len(candidates))} shown). Suggestions, not decisions:")
    print("work down the list, one file per edit, and keep an edit only if the evals hold "
          "(/playbooks/compress-harness-prose.md).")
    print_limits()
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=pathlib.Path, default=HERE.parent.parent)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("report", "duplicates", "candidates"):
        command = sub.add_parser(name)
        command.add_argument("--json", action="store_true", help="machine-readable output")
        command.add_argument("--top", type=int, default=20, help="how many entries to print (default: 20)")
        command.add_argument("--shingle", type=int, default=SHINGLE, help=f"duplicate window in words (default: {SHINGLE})")
        command.add_argument("--paths", help="file with sample changed paths, one per line, for the load weight")
    args = parser.parse_args()
    if args.shingle < 4:
        parser.error("--shingle must be at least 4 words; shorter windows match ordinary English")
    root = args.root.resolve()
    if not root.is_dir():
        print(f"density: no bundle at {root}", file=sys.stderr)
        return 2
    handler = {"report": cmd_report, "duplicates": cmd_duplicates, "candidates": cmd_candidates}
    return handler[args.command](root, args)


if __name__ == "__main__":
    sys.exit(main())
