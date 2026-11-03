#!/usr/bin/env python3
"""Validate requirement mappings, execute checks and write evidence receipts.

check: validate the distributed registry without changing OKF.
run: capture one explicit command, its result and repository revision.
code-types: run existing Roslyn checker on independently discovered C# changes.
report: combine receipts, exposing missing checks and pending semantic review.

Outputs must be outside the source repository. Exit 0 means the requested check
completed successfully, 1 a violation, 2 unavailable/invalid verification. A report
never grants approval. Commands are argv arrays, never shell-evaluated strings.
"""
import argparse
import datetime
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode = True
BUNDLE = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BUNDLE / 'tools/harness'))
import bundle

REGISTRY = pathlib.Path(__file__).with_name('requirements.json')
METHODS = {'deterministic', 'static-analysis', 'behavioral-test', 'llm-judge', 'human-review', 'none'}
AUTOMATION = {'implemented', 'standard-tool-candidate', 'custom-automation-candidate', 'hybrid', 'semantic-only', 'guidance-only'}
STATUSES = {'pass', 'fail', 'error', 'inconclusive', 'not-applicable', 'skipped', 'waived'}


def read_json(path):
    return json.loads(pathlib.Path(path).read_text(encoding='utf-8'))


def write_json(path, data):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, delete=False, encoding='utf-8') as stream:
        json.dump(data, stream, indent=2)
        stream.write('\n')
        temporary = pathlib.Path(stream.name)
    temporary.replace(path)


def file_reference(root, value):
    if not isinstance(value, str) or not bundle.safe_repo_path(value):
        raise ValueError(f'unsafe reference: {value!r}')
    target = (root / value).resolve()
    if not target.is_relative_to(root.resolve()) or not target.is_file():
        raise ValueError(f'missing/outside reference: {value}')
    return target


def registry(path=REGISTRY, parents=None, semantic_only=False):
    data = read_json(path)
    if not isinstance(data, dict) or type(data.get('schema_version')) is not int or data['schema_version'] != 1:
        raise ValueError('unsupported verification registry schema_version')
    if not isinstance(data.get('requirements'), list) or not data['requirements']:
        raise ValueError('requirements must be a nonempty list')
    result = {}
    for item in data['requirements']:
        if not isinstance(item, dict):
            raise ValueError('each requirement must be an object')
        rid = item.get('requirement_id', '')
        if not isinstance(rid, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+', rid) or rid in result:
            raise ValueError(f'invalid/duplicate requirement_id: {rid!r}')
        if parents is not None and item.get('parent_rule_id') not in parents:
            continue
        if semantic_only and not any(m in {'llm-judge', 'human-review'} for m in item.get('verification_method', [])):
            continue
        source = file_reference(BUNDLE, item.get('source'))
        meta, _ = bundle.parse(source)
        parent = item.get('parent_rule_id')
        if not meta or parent != bundle.unquote(meta.get('rule_id', meta.get('example_id', meta.get('principle_id', '')))):
            raise ValueError(f'{rid}: parent does not match source identity')
        methods = item.get('verification_method')
        if not isinstance(methods, list) or not methods or any(m not in METHODS for m in methods):
            raise ValueError(f'{rid}: invalid verification_method')
        status = item.get('automation_status')
        if status not in AUTOMATION:
            raise ValueError(f'{rid}: invalid automation_status')
        tools = item.get('automation_tool')
        if not isinstance(tools, list) or (status == 'implemented' and not tools):
            raise ValueError(f'{rid}: implemented requirements need a tool')
        for tool in tools:
            if not isinstance(tool, dict) or not tool.get('name'):
                raise ValueError(f'{rid}: invalid tool')
            if 'path' in tool:
                file_reference(BUNDLE, tool['path'])
            elif status == 'implemented':
                raise ValueError(f'{rid}: implemented tool needs a local evidence path')
        coverage = item.get('coverage')
        if not isinstance(coverage, dict) or not coverage.get('scope') or not isinstance(coverage.get('exclusions'), list) or not isinstance(coverage.get('residual'), list):
            raise ValueError(f'{rid}: coverage scope, exclusions and residual required')
        if not all(isinstance(item.get(key), str) and item[key].strip() for key in ('owner', 'statement')):
            raise ValueError(f'{rid}: owner and statement required')
        if status == 'semantic-only' and not set(methods) <= {'llm-judge', 'human-review'}:
            raise ValueError(f'{rid}: semantic-only cannot claim deterministic verification')
        if status == 'guidance-only' and methods != ['none']:
            raise ValueError(f'{rid}: guidance-only has no pass/fail method')
        if item.get('rubric'):
            file_reference(BUNDLE, item['rubric'])
        if 'installation' in item:
            raise ValueError(f'{rid}: installation is consumer evidence, not a shared-registry assertion')
        result[rid] = item
    return result


def git(repo, *args, optional=False, binary=False):
    run = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, timeout=30)
    if run.returncode and not optional:
        raise ValueError(run.stderr.decode(errors='replace').strip() or 'git inspection failed')
    return run.stdout if binary else run.stdout.decode('utf-8', errors='strict').strip()


def workspace_state(repo):
    if pathlib.Path(git(repo, 'rev-parse', '--show-toplevel')).resolve() != repo.resolve():
        raise ValueError('--repo must name the Git repository root')
    commit = git(repo, 'rev-parse', '--verify', 'HEAD', optional=True) or None
    state = hashlib.sha256(git(repo, 'status', '--porcelain', '-z', binary=True, optional=True))
    if commit:
        state.update(git(repo, 'diff', '--binary', 'HEAD', '--', binary=True))
    # Untracked paths are fingerprinted by metadata, never by opening potential env/credential files.
    for raw in git(repo, 'ls-files', '--others', '--exclude-standard', '-z', binary=True).split(b'\0'):
        if raw:
            path = repo / raw.decode('utf-8')
            stat = path.lstat()
            state.update(raw + f'{stat.st_size}:{stat.st_mtime_ns}'.encode())
    return state.hexdigest()


def harness_identity():
    # A copied/ignored .harness directory does not inherit its consumer's Git revision.
    root_text = git(BUNDLE, 'rev-parse', '--show-toplevel', optional=True)
    root = pathlib.Path(root_text).resolve() if root_text else None
    tracked = False
    if root:
        anchor = (BUNDLE.resolve() / 'index.md').relative_to(root).as_posix()
        tracked = bool(git(root, 'ls-files', '--error-unmatch', '--', anchor, optional=True))
    paths = {'index.md', 'tools/harness/bundle.py', 'tools/harness/context.py',
             'tools/verification/verify.py', 'tools/verification/requirements.json',
             'tools/verification/standard_checks.py', 'tools/verification/tool-lock.json',
             'tools/verification/keyvault.ps1', 'tools/verification/gitleaks.toml',
             'tools/verification/gitleaks.ignore',
             'tools/code/Program.cs', 'tools/code/CheckTypes.csproj', 'tools/code/NuGet.Config'}
    for item in read_json(REGISTRY)['requirements']:
        paths.add(item['source'])
        if item.get('rubric'):
            paths.add(item['rubric'])
        paths.update(tool['path'] for tool in item['automation_tool'] if tool.get('path'))
    hashes = {path: hashlib.sha256((BUNDLE / path).read_bytes()).hexdigest()
              if (BUNDLE / path).is_file() else None for path in sorted(paths)}
    return {'harness_commit': git(root, 'rev-parse', 'HEAD', optional=True) or None if tracked else None,
            'harness_dirty': bool(git(root, 'status', '--porcelain', optional=True)) if tracked else None,
            'harness_provenance': 'git-checkout' if tracked else 'copied-bundle-revision-unknown',
            'harness_inputs_sha256': hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()}


def provenance(repo):
    return {'repository': str(repo), 'commit': git(repo, 'rev-parse', '--verify', 'HEAD', optional=True) or None,
            'dirty': bool(git(repo, 'status', '--porcelain', optional=True)),
            'source_state_sha256': workspace_state(repo),
            **harness_identity(),
            'registry_sha256': hashlib.sha256(REGISTRY.read_bytes()).hexdigest()}


def output_dir(value, repo):
    out = pathlib.Path(value).resolve()
    if out.is_relative_to(repo.resolve()) or out.is_relative_to(BUNDLE.resolve()):
        raise ValueError('receipt output must be outside repository and harness')
    if out.exists() and any(out.iterdir()):
        raise ValueError('receipt output directory must be new or empty')
    out.mkdir(parents=True, exist_ok=True)
    return out


def base_receipt(rid, repo, stage):
    return {'schema_version': 1, 'requirement_id': rid, 'stage': stage,
            'recorded_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'provenance': provenance(repo), 'status': 'error', 'approval': 'not-assessed'}


def execute(command, repo, out, name, timeout, env=None):
    started = time.monotonic()
    info = {'argv': command, 'cwd': str(repo), 'timeout_seconds': timeout,
            'stdout': f'{name}.stdout.txt', 'stderr': f'{name}.stderr.txt'}
    # Logs are deliberately retained rather than copied to the model's context.
    with (out / info['stdout']).open('wb') as stdout, (out / info['stderr']).open('wb') as stderr:
        try:
            process = subprocess.Popen(command, cwd=repo, stdout=stdout, stderr=stderr,
                                       start_new_session=(os.name != 'nt'), env=env)
            try:
                code = process.wait(timeout=timeout)
                info['exit_code'] = code
                info['status'] = 'pass' if code == 0 else 'error' if code < 0 or code in {2, 126, 127} else 'fail'
            except subprocess.TimeoutExpired:
                if os.name != 'nt':
                    import signal
                    os.killpg(process.pid, signal.SIGKILL)
                else:
                    subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True)
                process.wait()
                info.update(status='error', exit_code=None, error='timeout')
        except OSError as error:
            info.update(status='error', exit_code=None, error=str(error))
    info['elapsed_seconds'] = round(time.monotonic() - started, 3)
    for key in ('stdout', 'stderr'):
        info[key + '_sha256'] = hashlib.sha256((out / info[key]).read_bytes()).hexdigest()
    return info


def run_command(args):
    items = registry(parents={'T.1'})
    item = items.get(args.requirement)
    if not item or item['automation_status'] != 'implemented' or set(item['verification_method']) & {'llm-judge', 'human-review', 'none'}:
        raise ValueError('run requires an implemented machine-verifiable requirement')
    if args.requirement != 'T.1.verify-command':
        raise ValueError('generic run observes command completion only; use a property-specific adapter for other requirements')
    command = args.argv[1:] if args.argv[:1] == ['--'] else args.argv
    if not command:
        raise ValueError('missing command after --')
    repo = args.repo.resolve()
    out = output_dir(args.out, repo)
    receipt = base_receipt(args.requirement, repo, args.stage)
    check = execute(command, repo, out, 'command', args.timeout)
    receipt.update(status=check['status'], checks=[check], coverage=item['coverage'])
    if provenance(repo) != receipt['provenance']:
        receipt.update(status='error', error='Source state changed during verification; rerun checks')
    write_json(out / 'receipt.json', receipt)
    print(f"{receipt['status']}: {args.requirement}; evidence {out / 'receipt.json'}")
    return {'pass': 0, 'fail': 1}.get(receipt['status'], 2)


def source_paths(repo, baseline, audit):
    # Discover independently of selected guidance. Include staged, unstaged and untracked edits.
    if git(repo, 'ls-files', '--unmerged', '-z', binary=True):
        raise ValueError('Unresolved merge conflicts; structural verification is incomplete')
    raw = git(repo, 'ls-files', '-z', binary=True) if audit or not baseline else git(
        repo, 'diff', '--name-only', '--no-renames', '--diff-filter=ACMRT', '-z', baseline, '--', binary=True)
    raw += git(repo, 'ls-files', '--others', '--exclude-standard', '-z', binary=True)
    paths = sorted(set(p.decode('utf-8') for p in raw.split(b'\0') if p))
    return [p for p in paths if p.endswith('.cs') and not {'bin', 'obj', '.harness'} & {part.lower() for part in pathlib.PurePosixPath(p).parts}
            and (repo / p).is_file()]


def code_types(args):
    item = registry(parents={'CODE.5'})['CODE.5.file-layout']
    repo = args.repo.resolve()
    out = output_dir(args.out, repo)
    receipt = base_receipt('CODE.5.file-layout', repo, args.stage)
    receipt.update(checks=[], coverage=item['coverage'], configurations=args.symbols or [None])
    try:
        git(repo, 'rev-parse', '--show-toplevel')
        baseline = None
        if not args.audit:
            ref = args.baseline or 'HEAD'
            if ref == 'HEAD' and not git(repo, 'rev-parse', '--verify', 'HEAD', optional=True):
                baseline = None  # Unborn repository: every tracked/untracked declaration is new.
            else:
                baseline = git(repo, 'rev-parse', '--verify', ref + '^{commit}')
        receipt.update(baseline=baseline, mode='audit' if args.audit else 'change')
        paths = source_paths(repo, baseline, args.audit)
        for path in paths:
            if not bundle.safe_repo_path(path) or not (repo / path).resolve().is_relative_to(repo):
                raise ValueError(f'unsafe source path: {path}')
        receipt['paths'] = paths
        receipt['source_sha256'] = {p: hashlib.sha256((repo / p).read_bytes()).hexdigest() for p in paths}
        if not paths:
            receipt.update(status='not-applicable', reason='No C# changes in the inspected scope')
        else:
            with tempfile.TemporaryDirectory(prefix='harness-code-types-') as temp:
                work = pathlib.Path(temp)
                project = work / 'checker'
                project.mkdir()
                for name in ('CheckTypes.csproj', 'Program.cs', 'NuGet.Config'):
                    shutil.copyfile(BUNDLE / 'tools/code' / name, project / name)
                receipt['tool_sha256'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in project.iterdir()}
                build = execute(['dotnet', 'build', str(project / 'CheckTypes.csproj'), '--disable-build-servers',
                                 '-p:UseSharedCompilation=false', '-c', 'Release', '-o', str(work / 'out'), '--nologo', '-v', 'quiet'],
                                repo, out, 'checker-build', args.timeout)
                receipt['checks'].append(build)
                if build['status'] != 'pass':
                    receipt.update(status='error', error='Checker could not build')
                else:
                    receipt['sdk'] = subprocess.run(['dotnet', '--version'], cwd=repo, capture_output=True, text=True, timeout=30).stdout.strip()
                    old = work / 'baseline'
                    old.mkdir()
                    if baseline:
                        for path in paths:
                            entry = subprocess.run(['git', '-C', str(repo), 'cat-file', '-e', f'{baseline}:{path}'], capture_output=True)
                            if entry.returncode == 0:
                                target = old / path
                                target.parent.mkdir(parents=True, exist_ok=True)
                                target.write_bytes(git(repo, 'show', f'{baseline}:{path}', binary=True))
                    statuses = []
                    for index, symbols in enumerate(args.symbols or [None]):
                        command = ['dotnet', str(work / 'out/CheckTypes.dll'), *paths]
                        if not args.audit:
                            command += ['--baseline', str(old)]
                        if symbols is not None:
                            command += ['--symbols', symbols]
                        check = execute(command, repo, out, f'code-types-{index}', args.timeout)
                        receipt['checks'].append(check)
                        try:
                            report = read_json(out / check['stdout'])
                            if report.get('version') != 2 or not all(isinstance(report.get(k), list) for k in ('findings', 'inheritedFindings', 'evidence', 'errors')):
                                raise ValueError('invalid checker report')
                            expected = 'error' if report['errors'] else 'fail' if report['findings'] else 'pass'
                            if expected != check['status']:
                                raise ValueError('checker exit code disagrees with report')
                            check['report'] = report
                            for error in report['errors']:
                                print(f'CODE.5 verification error: {error}', file=sys.stderr)
                            for finding in report['findings']:
                                print(f"{finding['path']}:{finding['line']}: CODE.5 {finding['reason']} ({finding['type']})")
                        except (ValueError, OSError) as error:
                            check.update(status='error', error=str(error))
                        statuses.append(check['status'])
                    receipt['status'] = 'error' if 'error' in statuses else 'fail' if 'fail' in statuses else 'pass'
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        receipt.update(status='error', error=str(error))
    if provenance(repo) != receipt['provenance']:
        receipt.update(status='error', error='Source state changed during verification; rerun checks')
    write_json(out / 'receipt.json', receipt)
    print(f"{receipt['status']}: CODE.5.file-layout; evidence {out / 'receipt.json'}")
    return {'pass': 0, 'not-applicable': 0, 'fail': 1}.get(receipt['status'], 2)


def summarize(args):
    records = read_json(REGISTRY)['requirements']
    receipts = [read_json(p) for p in args.results]
    requested = set(args.required) | set(args.review) | {r.get('requirement_id') for r in receipts if isinstance(r, dict)}
    parents = {r['parent_rule_id'] for r in records if r['requirement_id'] in requested}
    items = registry(parents=parents)
    for r in receipts:
        if not isinstance(r, dict) or not isinstance(r.get('provenance'), dict) or not r['provenance'].get('source_state_sha256'):
            raise ValueError('receipt lacks source provenance')
        if type(r.get('schema_version')) is not int or r['schema_version'] != 1 or r.get('status') not in STATUSES or r.get('requirement_id') not in items:
            raise ValueError('invalid result receipt')
        if not isinstance(r['provenance'].get('repository'), str):
            raise ValueError('receipt lacks repository identity')
    target = pathlib.Path(args.out).resolve()
    if target.is_relative_to(BUNDLE) or target.is_relative_to(pathlib.Path.cwd()) or any(
            target.is_relative_to(pathlib.Path(r['provenance']['repository'])) for r in receipts):
        raise ValueError('summary output must be outside source repositories and harness')
    # These explicit required IDs are the consumer's contract, independent of retrieval.
    for rid in args.required:
        if rid not in items:
            raise ValueError(f'unknown required requirement: {rid}')
    missing = [rid for rid in args.required if not any(r['requirement_id'] == rid for r in receipts)]
    if len({r['requirement_id'] for r in receipts}) != len(receipts):
        raise ValueError('duplicate requirement receipts; choose the final attempt explicitly')
    checks = [r for r in receipts if r['requirement_id'] in args.required]
    failed = any(r['status'] == 'fail' for r in checks)
    incomplete = bool(missing) or any(r['status'] not in {'pass', 'not-applicable'} for r in checks)
    # Refuse to aggregate receipts from different source states or registry revisions.
    identities = {json.dumps(r.get('provenance'), sort_keys=True) for r in receipts}
    if len(identities) > 1:
        raise ValueError('receipts have different source/harness states; rerun checks on the same state')
    result = {'schema_version': 1, 'status': 'fail' if failed else 'incomplete' if incomplete else 'checks-passed',
              'required': args.required, 'missing': missing, 'results': receipts,
              'semantic_review': {'status': 'pending' if args.review else 'not-requested', 'requirements': list(args.review)},
              'approval': 'not-assessed'}
    for rid in args.review:
        if rid not in items or not set(items[rid]['verification_method']) & {'llm-judge', 'human-review'}:
            raise ValueError(f'unknown semantic requirement: {rid}')
    write_json(args.out, result)
    print(f"{result['status']}; semantic review {result['semantic_review']['status']}; evidence {args.out}")
    return 1 if failed else 2 if incomplete else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)
    check = commands.add_parser('check')
    check.add_argument('--registry', type=pathlib.Path, default=REGISTRY)
    run = commands.add_parser('run')
    types = commands.add_parser('code-types')
    for command in (run, types):
        command.add_argument('--repo', type=pathlib.Path, default=pathlib.Path.cwd())
        command.add_argument('--out', required=True)
        command.add_argument('--stage', choices=['local', 'fast', 'ci'], default='local')
        command.add_argument('--timeout', type=int, default=300)
    run.add_argument('--requirement', required=True)
    run.add_argument('argv', nargs=argparse.REMAINDER)
    modes = types.add_mutually_exclusive_group()
    modes.add_argument('--baseline', help='Git ref; default HEAD, CI must supply its PR base')
    modes.add_argument('--audit', action='store_true', help='Explicitly inspect all current C# files')
    types.add_argument('--symbols', action='append', help='Repeat per supported configuration, e.g. none or DEBUG,FEATURE')
    for name in ('gitleaks', 'psrule'):
        scanner = commands.add_parser(name)
        scanner.add_argument('--repo', type=pathlib.Path, default=pathlib.Path.cwd())
        scanner.add_argument('--out', required=True)
        scanner.add_argument('--tools', type=pathlib.Path, required=True)
        scanner.add_argument('--stage', choices=['local', 'ci'], default='local')
        scanner.add_argument('--timeout', type=int, default=300)
        if name == 'gitleaks':
            scanner.add_argument('--baseline')
            scanner.add_argument('--working-tree', action='store_true')
        else:
            scanner.add_argument('--template', type=pathlib.Path, required=True)
            scanner.add_argument('--parameters', type=pathlib.Path)
    plan = commands.add_parser('review-plan')
    plan.add_argument('--selected', type=pathlib.Path, required=True)
    plan.add_argument('--out', required=True)
    report = commands.add_parser('report')
    report.add_argument('--out', required=True)
    report.add_argument('--required', nargs='+', required=True)
    report.add_argument('--review', nargs='*', default=[])
    report.add_argument('--results', nargs='*', default=[])
    args = parser.parse_args()
    try:
        if getattr(args, 'timeout', 1) <= 0:
            raise ValueError('timeout must be positive')
        if args.command == 'check':
            print(f'verification registry: {len(registry(args.registry))} valid requirements')
            return 0
        if args.command in {'gitleaks', 'psrule'}:
            sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
            from standard_checks import run
            return run(args)
        if args.command == 'review-plan':
            selected = read_json(args.selected)
            parents = set(selected['rules'].values())
            requirements = [item for item in registry(parents=parents, semantic_only=True).values()
                            if item['parent_rule_id'] in parents
                            and set(item['verification_method']) & {'llm-judge', 'human-review'}]
            write_json(args.out, {'schema_version': 1, 'status': 'pending', 'requirements': requirements,
                                  'instruction': 'Use these scopes and rubrics for evidence-based review. Keep public rule IDs and the existing findings JSON contract. No structural pass establishes a semantic pass.'})
            return 0
        return {'run': run_command, 'code-types': code_types, 'report': summarize}[args.command](args)
    except (ValueError, OSError, TypeError, KeyError, subprocess.SubprocessError) as error:
        print(f'verification error: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
