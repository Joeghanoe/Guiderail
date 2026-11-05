"""Source/installed guidance links and owned native skill packages (no model calls)."""
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.parse import quote, unquote, urlsplit

LINK = re.compile(r'(?<!!)\[([^\]\n]+)\]\((<[^>]+>|[^)\s]+)(?:\s+"[^"]*")?\)')
SKIP = {'.git', '.agents', '.codex', 'node_modules', '__pycache__', 'bin', 'obj'}
MARKER = '.harness-skill.json'


def prose(text):
    """Ignore fenced examples and inline code, preserving offsets for replacements."""
    text = re.sub(r'(?ms)^(`{3,}|~{3,})[^\n]*\n.*?^\1[^\n]*(?:\n|$)', lambda m: ' ' * len(m[0]), text)
    return re.sub(r'`[^`\n]*`', lambda m: ' ' * len(m[0]), text)


def target_path(source, target, repo):
    target = unquote(target.strip('<>'))
    if not target or target.startswith('#') or urlsplit(target).scheme:
        return None
    path = target.split('#', 1)[0]
    if path.startswith('~/.golden-path-harness/'):
        return repo / path.removeprefix('~/.golden-path-harness/')
    if path.startswith('/') and source.is_relative_to(repo / 'harness'):
        # OKF links use the bundle root; metadata retains the same contract.
        return repo / 'harness' / path.lstrip('/')
    if path.startswith('~/'):
        return None  # consumer/vault paths have no repository target
    return (source.parent / path).resolve()


def markdown_files(repo):
    return sorted(p for p in repo.rglob('*.md') if not set(p.relative_to(repo).parts) & SKIP)


def exact_exists(path):
    """Catch Linux-breaking capitalization even on a case-insensitive checkout."""
    if not path.exists():
        return False
    return all(part.name in {child.name for child in part.parent.iterdir()}
               for part in [path, *path.parents] if part != part.parent)


def audit(repo):
    """Check local document edges and report navigation without judging graph density."""
    repo = Path(repo).resolve()
    files = markdown_files(repo)
    incoming, edges, errors = set(), {}, []
    for source in files:
        text = source.read_text(encoding='utf-8')
        edges[source] = []
        for match in LINK.finditer(prose(text)):
            target = target_path(source, match[2], repo)
            if target is None:
                continue
            if not exact_exists(target):
                errors.append(f'{source.relative_to(repo)}: missing link {match[2]}')
            elif target.is_file():
                edges[source].append(target.resolve())
                incoming.add(target.resolve())
            elif (target / 'index.md').is_file():
                edges[source].append((target / 'index.md').resolve())
                incoming.add((target / 'index.md').resolve())
        for match in re.finditer(r'`(~/.golden-path-harness/[^`]+)`', text):
            if prose(text[:match.start()]).strip() == '' or '\n' in match[1]:
                continue
            target = repo / match[1].removeprefix('~/.golden-path-harness/')
            if target.exists():
                errors.append(f'{source.relative_to(repo)}: bare guidance reference {match[1]}')
    roots = [repo / 'README.md', repo / 'AGENTS.base.md', repo / 'harness/index.md', repo / 'skills/index.md']
    reached, pending = set(), [p for p in roots if p.exists()]
    while pending:
        node = pending.pop()
        if node in reached:
            continue
        reached.add(node)
        pending.extend(edges.get(node, []))
    active = [p for p in files if (p.is_relative_to(repo / 'skills') or
              p.is_relative_to(repo / 'harness/playbooks') or p.is_relative_to(repo / 'harness/rules'))]
    errors += [f'{p.relative_to(repo)}: active guidance unreachable from entry points' for p in active if p not in reached]
    return {'errors': errors, 'markdown_files': len(files),
            'unlinked': [str(p.relative_to(repo)) for p in files if p not in incoming],
            'unreachable': [str(p.relative_to(repo)) for p in files if p not in reached],
            'note': 'Unlinked fixtures, templates, proposals and historical notes are informational; active guidance must be reachable.'}


def render(text, source, destination, repo, installed_root):
    """Keep siblings relative; resolve cross-package, OKF and home-root targets."""
    masked = prose(text)
    replacements = []
    for match in LINK.finditer(masked):
        target = target_path(source, match[2], repo)
        if target is None or not target.exists():
            continue
        fragment = '#' + match[2].split('#', 1)[1].rstrip('>') if '#' in match[2] else ''
        package = next((entry.parent for entry in packages(repo) if source.is_relative_to(entry.parent)), None)
        if package and target.is_relative_to(package):
            link = os.path.relpath(target, source.parent)
        else:
            relative = target.relative_to(repo)
            link = str(installed_root / relative if relative.parts[0] in {'harness', 'skills', 'docs', 'feedback'} else target)
        replacements.append((match.start(2), match.end(2), quote(link, safe='/.:_-~') + fragment))
    for start, end, replacement in reversed(replacements):
        text = text[:start] + replacement + text[end:]
    return text


def packages(repo):
    return sorted((Path(repo) / 'skills/engineering').glob('*/SKILL.md'))


def payload(entry, directory, repo, installed_root):
    result = {}
    for source in sorted(entry.parent.rglob('*')):
        if source.is_symlink():
            raise ValueError(f'Skill packages cannot contain symlinks: {source}')
        if not source.is_file():
            continue
        rel = source.relative_to(entry.parent).as_posix()
        data = source.read_bytes()
        if source.suffix == '.md':
            data = render(data.decode(), source, directory / rel, repo, installed_root).encode()
        result[rel] = data
    return result


def manifest(directory):
    marker = directory / MARKER
    if not marker.exists():
        return None
    value = json.loads(marker.read_text())
    if value.get('owner') != 'teamvalue-harness' or not isinstance(value.get('files'), dict):
        raise ValueError(f'Invalid skill ownership manifest: {marker}')
    for name in value['files']:
        if Path(name).is_absolute() or '..' in Path(name).parts:
            raise ValueError(f'Unsafe skill ownership path: {name}')
    return value['files']


def preflight(entry, directory, repo, installed_root, legacy=None):
    if directory.is_symlink():
        raise ValueError(f'Skill-name conflict: {directory} is a symlink')
    files = manifest(directory) or {}
    desired = payload(entry, directory, repo, installed_root)
    for rel in set(desired) | set(files):
        path = directory / rel
        if not path.exists():
            continue
        if path.is_symlink():
            raise ValueError(f'Skill-name conflict: {path} is a symlink')
        data = path.read_bytes()
        known = files.get(rel)
        if known and hashlib.sha256(data).hexdigest() == known:
            continue
        normalized = data.replace(str(installed_root).encode(), b'~/.golden-path-harness')
        if not files and rel == 'SKILL.md' and legacy and hashlib.sha256(normalized).hexdigest() in legacy:
            continue
        if data == desired.get(rel) and files:
            continue
        raise ValueError(f'Skill-name conflict: {path} is not an unchanged harness-owned file; preserve or rename it first')
    return desired


def publish(entry, directory, repo, installed_root, legacy=None):
    desired = preflight(entry, directory, repo, installed_root, legacy)
    old = manifest(directory) or {}
    directory.mkdir(parents=True, exist_ok=True)
    for rel in set(old) - set(desired):
        path = directory / rel
        if path.exists():
            path.unlink()
    for rel, data in desired.items():
        path = directory / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists() or path.read_bytes() != data:
            path.write_bytes(data)
    marker = {'owner': 'teamvalue-harness', 'files': {k: hashlib.sha256(v).hexdigest() for k,v in desired.items()}}
    (directory / MARKER).write_text(json.dumps(marker, indent=2) + '\n')


def uninstall(directory):
    files = manifest(directory)
    if files is None:
        return
    for rel, digest in files.items():
        path = directory / rel
        if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == digest:
            path.unlink()
    (directory / MARKER).unlink()
    for path in sorted(directory.rglob('*'), reverse=True):
        if path.is_dir():
            try:
                path.rmdir()
            except OSError:
                pass
    try:
        directory.rmdir()
    except OSError:
        pass


def check_catalog(repo):
    catalog = json.loads((repo / 'skills/processes.json').read_text())
    active = {entry.parent.name for entry in packages(repo)}
    referenced, names, errors = set(), set(), []
    for step in catalog['steps']:
        name = step['step']
        if name in names:
            errors.append(f'process catalog: duplicate step {name}')
        names.add(name)
        if step['status'] not in ('active', 'planned', 'external'):
            errors.append(f'process catalog: invalid status for {name}')
        for key in ('owner', 'inputs', 'outputs'):
            if not step.get(key):
                errors.append(f'process catalog: {name} missing {key}')
        if step['status'] == 'active':
            referenced.add(step['skill'])
            if step['skill'] not in active:
                errors.append(f'process catalog: missing active skill {step["skill"]}')
        elif step.get('skill') or not step.get('gap'):
            errors.append(f'process catalog: {name} needs a gap and must not publish a placeholder skill')
    errors += [f'process catalog: unmapped skill {name}' for name in sorted(active - referenced)]
    for entry in packages(repo):
        match = re.search(r'^name: (.+)$', entry.read_text(), re.M)
        if not match or match[1] != entry.parent.name or match[1].startswith('tv-'):
            errors.append(f'Invalid skill identity: {entry}')
    if (repo / 'skills/index.md').read_text() != process_index(catalog):
        errors.append('skills/index.md: out of date; regenerate from guidance.process_index and skills/processes.json')
    return errors


def process_index(catalog):
    lines = ['# Engineering processes', '',
             'The [process catalog](processes.json) maps current and future coverage. Select the step appropriate to the request; this is not a mandatory lifecycle or a chain of skill invocations. Pass artifacts, criterion identifiers and open questions between steps rather than the full conversation.', '',
             '| Step | Skill | Status | Owner | Inputs | Outputs or gap |',
             '| --- | --- | --- | --- | --- | --- |']
    for step in catalog['steps']:
        link = f'[{step["skill"]}](engineering/{step["skill"]}/SKILL.md)' if step['skill'] else 'Not installed'
        output = step['outputs'] + (f'. Gap: {step["gap"]}' if step['gap'] else '')
        lines.append(f'| {step["step"]} | {link} | {step["status"]} | {step["owner"]} | {step["inputs"]} | {output} |')
    lines += ['',
              'Shared procedures remain in [playbooks](../harness/playbooks/index.md). Review and business acceptance procedures live beside their owning skills; design, implementation, test and debugging details load conditionally from flat supporting files. Security, compatibility, migrations, privacy, performance, recovery and UX remain conditional concerns under the [coverage assessment](../docs/proposals/development-process-coverage.md). A missing organizational decision remains a visible planned gap.', '',
              'Native installation currently targets Claude Code and Copilot. Codex parity is unassessed. A source or installed-link check establishes packaging, not actual model selection or successful workflow completion.']
    return '\n'.join(lines) + '\n'
