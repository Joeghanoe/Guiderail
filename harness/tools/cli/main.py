#!/usr/bin/env python3
"""Harness commands with explicit effects and retained execution evidence."""
import contextlib
import argparse
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time

BUNDLE = pathlib.Path(__file__).resolve().parents[2]
PREVIEW_BYTES = 12000
sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import workflows
import catalog


def parser():
    root = argparse.ArgumentParser(prog='tvh', description=__doc__)
    commands = root.add_subparsers(dest='command', required=True)

    def common(p, repo=False):
        output = p.add_mutually_exclusive_group()
        output.add_argument('--json', action='store_true', help='emit a schema-versioned result')
        output.add_argument('--raw', action='store_true', help='emit complete native stdout for pipes; retain the result separately')
        p.add_argument('--out', type=pathlib.Path, help='fresh evidence directory outside the repository and harness')
        p.add_argument('--timeout', type=int, default=240, help='wall-clock limit in seconds per operation, 1..86400')
        if repo:
            p.add_argument('--repo', type=pathlib.Path, default=pathlib.Path.cwd())

    doctor = commands.add_parser('doctor', help='inspect executables locally; never logs in or installs')
    common(doctor)
    context = commands.add_parser('context', help='select applicable guidance')
    ctx = context.add_subparsers(dest='action', required=True).add_parser('select')
    common(ctx, repo=True)
    ctx.add_argument('--changed', action='store_true')
    ctx.add_argument('--baseline', help='explicit baseline for --changed')
    ctx.add_argument('--brief', action='store_true')
    ctx.add_argument('--examples', action='store_true')
    ctx.add_argument('paths', nargs='*')
    verify = commands.add_parser('verify', help='execute the project verify and retain its existing receipt')
    common(verify, repo=True)
    mode = verify.add_mutually_exclusive_group()
    mode.add_argument('--fast', action='store_true')
    mode.add_argument('--design', action='store_true', help='verify the design before source is created')
    review = commands.add_parser('review', help='review a tracked diff in an independent read-only agent')
    common(review, repo=True)
    review.add_argument('--baseline', required=True, help='ref whose merge base with HEAD defines the change')
    review.add_argument('--engine', choices=('claude', 'copilot', 'codex', 'agy', 'replay'), default='claude')
    review.add_argument('--context-file', type=pathlib.Path, help='review topics, specs and prior check evidence, treated as data')
    ado = commands.add_parser('ado', help='read Azure DevOps run evidence')
    run = ado.add_subparsers(dest='action', required=True).add_parser('run')
    operations = run.add_subparsers(dest='operation', required=True)
    diagnose = operations.add_parser('diagnose')
    common(diagnose)
    diagnose.add_argument('--organization', required=True)
    diagnose.add_argument('--project', required=True)
    diagnose.add_argument('--id', required=True, type=int)
    diagnose.add_argument('--tail-lines', type=int, default=80)
    watch = operations.add_parser('watch', help='follow run changes without queueing or retrying')
    common(watch)
    watch.add_argument('--organization', required=True)
    watch.add_argument('--project', required=True)
    watch.add_argument('--run', required=True, help='numeric run id or latest:<branch>')
    watch.add_argument('--interval', type=int, default=30)
    watch.add_argument('--max-minutes', type=int, default=3)
    cloud = commands.add_parser('cloud', help='restricted cloud reads through the existing wrapper')
    read = cloud.add_subparsers(dest='action', required=True).add_parser('read')
    common(read)
    read.add_argument('cli', choices=('az', 'terraform', 'tofu', 'kubectl', 'hcloud'))
    read.add_argument('args', nargs=argparse.REMAINDER)
    sonar = commands.add_parser('sonar', help='read published Sonar results through the existing wrapper')
    read = sonar.add_subparsers(dest='action', required=True).add_parser('read')
    common(read)
    read.add_argument('endpoint', choices=('issues/search', 'hotspots/search', 'hotspots/show',
                                         'qualitygates/project_status', 'measures/component'))
    read.add_argument('params', nargs='*')
    workflows.add_parsers(commands, common)
    catalog.add_parsers(root, common)
    return root


def inside(path, parent):
    return path == parent or parent in path.parents


def git(repo, *args):
    result = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, timeout=30)
    if result.returncode:
        raise ValueError('Git operation failed: ' + result.stderr.decode(errors='replace').strip())
    return result.stdout


def repository(path):
    return pathlib.Path(os.fsdecode(git(path.resolve(), 'rev-parse', '--show-toplevel')).strip()).resolve()


def source_state(repo):
    return {'commit': git(repo, 'rev-parse', 'HEAD').decode().strip(),
            'state_sha256': hashlib.sha256(git(repo, 'status', '--porcelain', '-z') +
                                          git(repo, 'diff', '--no-ext-diff', '--no-textconv', '--binary', 'HEAD', '--')).hexdigest()}


def harness_identity():
    """Reuse the verification provenance contract and identify the CLI-specific inputs."""
    spec = importlib.util.spec_from_file_location('tvh_verification', BUNDLE / 'tools/verification/verify.py')
    verification = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verification)
    return {**verification.harness_identity(),
            'cli_inputs': {name: hashlib.sha256((BUNDLE / name).read_bytes()).hexdigest()
                           for name in ('tvh', 'tools/cli/main.py', 'tools/cli/workflows.py', 'playbooks/review-and-fix.md',
                                        'playbooks/diagnose-pipeline-failure.md')}}


def execute(argv, cwd, out, label, timeout, environment=None, stream=False, stdin_path=None):
    """Spool full output to disk; bound only the displayed preview. Kill descendants on POSIX."""
    stdout, stderr = out / f'{label}.stdout', out / f'{label}.stderr'
    started = time.monotonic()
    timed_out = False
    with (stdin_path.open('rb') if stdin_path else contextlib.nullcontext(subprocess.DEVNULL)) as input_stream, \
            stdout.open('wb') as output, stderr.open('wb') as errors:
        def pump(pipe):
            displayed = 0
            while chunk := pipe.read1(4096):
                output.write(chunk)
                output.flush()
                preview = chunk[:max(0, PREVIEW_BYTES - displayed)]
                if preview:
                    print(preview.decode(errors='replace'), end='', flush=True)
                displayed += len(chunk)
            if displayed > PREVIEW_BYTES:
                print(f'\nPreview limited; full output: {stdout}', flush=True)

        with subprocess.Popen(argv, cwd=cwd, stdout=subprocess.PIPE if stream else output,
                              stderr=errors, stdin=input_stream,
                              env=environment, start_new_session=os.name != 'nt') as child:
            if stream:
                reader = threading.Thread(target=pump, args=(child.stdout,), daemon=True)
                reader.start()
            try:
                code = child.wait(timeout=timeout)
            except (subprocess.TimeoutExpired, KeyboardInterrupt):
                timed_out = True
                if os.name == 'nt':
                    subprocess.run(['taskkill', '/PID', str(child.pid), '/T', '/F'], capture_output=True, check=False)
                else:
                    os.killpg(child.pid, signal.SIGKILL)
                child.wait()
                code = 124
            if stream:
                reader.join(timeout=5)
                if reader.is_alive():
                    raise ValueError('Output pipe did not close; operation is incomplete')
    return {'argv': list(map(str, argv)), 'exit_code': code, 'timed_out': timed_out,
            'wall_seconds': round(time.monotonic() - started, 3),
            'stdout': str(stdout), 'stderr': str(stderr), 'stdout_streamed': stream}


def load_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def require_completed(step, allowed=(0,)):
    if step['exit_code'] not in allowed:
        raise ValueError(f"Operation incomplete, exit {step['exit_code']}; see {step['stderr']}")


def run(args, out, result):
    steps = result['steps']
    py = sys.executable
    cwd = args.repo if hasattr(args, 'repo') else pathlib.Path.cwd()
    if catalog.run(args, out, result, execute):
        return

    def call(argv, label, allowed=(0,), environment=None, stream=False):
        step = execute(argv, cwd, out, label, args.timeout, environment, stream)
        steps.append(step)
        require_completed(step, allowed)
        return step

    if args.command == 'doctor':
        tools = {name: shutil.which(name) for name in ('bash', 'git', 'jq', 'curl', 'node', 'az', 'claude', 'copilot', 'codex', 'agy')}
        result['data'] = {'python': sys.executable, 'bundle': str(BUNDLE), 'executables': tools,
                          'credentials': 'not inspected', 'skills': 'installation does not prove model selection'}
        result['status'] = 'completed' if all(tools[x] for x in ('bash', 'git', 'jq', 'curl')) else 'incomplete'
        return
    if args.command == 'context':
        argv = [py, '-I', str(BUNDLE / 'tools/harness/bundle.py'), 'select']
        if args.changed:
            if not args.baseline:
                raise ValueError('--changed requires an explicit --baseline; use HEAD for local edits')
            baseline = git(cwd, 'rev-parse', '--verify', args.baseline + '^{commit}').decode().strip()
            argv += ['--changed', '--base', baseline]
        if not args.changed and not args.paths:
            raise ValueError('Supply paths or --changed --baseline <ref>')
        if args.brief:
            argv.append('--brief')
        if args.examples:
            argv.append('--examples')
        step = call(argv + ['--'] + args.paths, 'selection')
        if not args.brief:
            result['data'] = load_json(pathlib.Path(step['stdout']))
        result['status'] = 'completed'
        return
    if args.command == 'verify':
        step = call(['bash', str(BUNDLE / 'tools/code/project-verify.sh'), 'path', str(cwd)], 'verify-path')
        verify = pathlib.Path(pathlib.Path(step['stdout']).read_text().strip())
        if not verify.is_file():
            verify = cwd / 'scripts/verify.sh'
        if not verify.is_file():
            raise ValueError('No installed project verify or scripts/verify.sh; configure the repository verify first')
        argv = ['bash', str(verify)] + (['--fast'] if args.fast else ['--design'] if args.design else [])
        env = dict(os.environ, HARNESS_REPO_ROOT=str(cwd), HARNESS_BUNDLE_ROOT=str(BUNDLE))
        step = call([py, '-I', str(BUNDLE / 'tools/verification/verify.py'), 'run',
                     '--requirement', 'T.1.verify-command', '--repo', str(cwd), '--stage', 'local',
                     '--out', str(out / 'verification'), '--timeout', str(args.timeout), '--', *argv],
                    'verify', allowed=(0, 1), environment=env)
        receipt = out / 'verification/receipt.json'
        if not receipt.is_file():
            raise ValueError('Verification produced no receipt')
        result['artifacts']['verification'] = str(receipt)
        result['status'] = 'completed' if step['exit_code'] == 0 else 'failed'
        return
    if args.command == 'review':
        baseline = git(cwd, 'rev-parse', '--verify', args.baseline + '^{commit}').decode().strip()
        merge_base = git(cwd, 'merge-base', 'HEAD', baseline).decode().strip()
        untracked = os.fsdecode(git(cwd, 'ls-files', '--others', '--exclude-standard', '-z')).split('\0')
        untracked = [p for p in untracked if p]
        if untracked:
            result['data'] = {'untracked_paths': untracked}
            raise ValueError('Review scope contains untracked files. Inspect and stage intended files, then rerun; nothing was read or staged.')
        paths = os.fsdecode(git(cwd, 'diff', '--name-only', '-z', merge_base, '--')).split('\0')
        paths = [p for p in paths if p]
        # Existing reviewer inputs are line-delimited. Refuse paths that cannot be represented safely.
        if any('\n' in p or '\r' in p for p in paths):
            raise ValueError('Reviewer does not support filenames containing newlines')
        if any(part == '.env' or part.startswith('.env.') and part != '.env.example'
               for p in paths for part in pathlib.PurePosixPath(p).parts):
            raise ValueError('Review cannot read dotenv files; remove them from the tracked change')
        result['scope'].update({'baseline': baseline, 'merge_base': merge_base, 'paths': paths})
        if not paths:
            result['status'] = 'not-applicable'
            return
        state = source_state(cwd)
        result['scope']['source'] = state
        (out / 'changed.txt').write_text('\n'.join(paths) + '\n', encoding='utf-8')
        (out / 'diff.patch').write_bytes(git(cwd, 'diff', '--no-ext-diff', '--no-textconv', merge_base, '--'))
        context = ''
        if args.context_file:
            context_path = args.context_file.resolve()
            if any(part == '.env' or part.startswith('.env.') and part != '.env.example'
                   for part in context_path.parts):
                raise ValueError('Review context cannot be a dotenv file')
            context = context_path.read_text(encoding='utf-8')
        (out / 'pr.txt').write_text(context, encoding='utf-8')
        env = dict(os.environ, HARNESS_REVIEW_ENGINE=args.engine)
        call(['bash', str(BUNDLE / 'tools/review/review.sh'), str(out)], 'review', environment=env)
        if source_state(cwd) != state:
            raise ValueError('Source state changed during review; rerun against the current source')
        findings = load_json(out / 'findings.json')
        raw = (out / 'raw.txt').read_text(encoding='utf-8').strip()
        match = re.search(r'```(?:json)?\s*(\[.*\])\s*```', raw, flags=re.S)
        raw_findings = json.loads(match.group(1) if match else raw[raw.find('['):raw.rfind(']') + 1])
        if not isinstance(findings, list) or not isinstance(raw_findings, list) or len(findings) != len(raw_findings):
            raise ValueError('Reviewer output was malformed or contained dropped findings; review is incomplete')
        result['artifacts']['findings'] = str(out / 'findings.json')
        result['data'] = {'finding_count': len(findings), 'approval': 'not-approved',
                          'verification': 'separate required step'}
        result['status'] = 'findings' if findings else 'completed'
        return
    if workflows.run(args, out, result, call, execute):
        return
    if args.command == 'ado' and args.operation == 'watch':
        if args.interval < 10 or not 1 <= args.max_minutes <= 30:
            raise ValueError('--interval must be at least 10 seconds and --max-minutes must be 1..30')
        step = call(['bash', str(BUNDLE / 'tools/azure-devops/ado-run-watch.sh'), args.organization,
                     args.project, args.run, str(args.interval), str(args.max_minutes)],
                    'watch', allowed=(0, 1), stream=not (args.json or args.raw))
        result['scope'] = {'organization': args.organization, 'project': args.project, 'run': args.run}
        result['status'] = 'completed' if step['exit_code'] == 0 else 'failed'
        return
    if args.command == 'ado':
        if args.id < 1 or not 1 <= args.tail_lines <= 400:
            raise ValueError('Run id must be positive and --tail-lines must be 1..400')
        argv = ['bash', str(BUNDLE / 'tools/azure-devops/ado-run-failure.sh'),
                args.organization, args.project, str(args.id), str(args.tail_lines)]
        result['scope'] = {'organization': args.organization, 'project': args.project, 'run_id': args.id}
    elif args.command == 'cloud':
        argv = ['bash', str(BUNDLE / 'tools/cloud/cloud-read.sh'), args.cli, *args.args]
    else:
        argv = ['bash', str(BUNDLE / 'tools/sonar/sonar-read.sh'), args.endpoint, *args.params]
    call(argv, 'read')
    result['status'] = 'completed'


def main():
    args = parser().parse_args()
    command_name = ' '.join(args.catalog_command['path']) if hasattr(args, 'catalog_command') else args.command
    result = {'schema_version': 1, 'command': command_name, 'status': 'incomplete',
              'scope': {}, 'steps': [], 'artifacts': {}, 'data': None}
    out = None
    try:
        if not 1 <= args.timeout <= 86400:
            raise ValueError('--timeout must be 1..86400')
        if hasattr(args, 'repo'):
            args.repo = (args.repo.resolve(strict=True) if args.command == 'context' and not args.changed
                         else repository(args.repo))
            result['scope']['repo'] = str(args.repo)
        # Even read commands must not write evidence into the caller's source tree.
        source = args.repo if hasattr(args, 'repo') else None
        if source is None and shutil.which('git'):
            try:
                source = repository(getattr(args, 'cwd', pathlib.Path.cwd()))
            except ValueError:
                pass  # A local diagnostic may also run outside a source repository.
        candidate = args.out.expanduser().resolve() if args.out else pathlib.Path(tempfile.gettempdir()).resolve()
        if args.command == 'greenfield':
            source = args.target.expanduser().resolve()
        if (source is not None and inside(candidate, source)) or inside(candidate, BUNDLE.parent):
            raise ValueError('--out must be outside the source repository and harness checkout')
        for native_root in catalog.source_roots(args):
            if inside(candidate, native_root):
                raise ValueError('--out must be outside the native command source scope')
        if args.out:
            candidate.mkdir(parents=True, exist_ok=False)
            out = candidate
        else:
            out = pathlib.Path(tempfile.mkdtemp(prefix='tvh-', dir=candidate))
        out.chmod(0o700)
        result['artifacts']['directory'] = str(out)
        result['harness'] = harness_identity()
        run(args, out, result)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        result['status'] = 'incomplete'
        result['error'] = str(error)
    if out:
        result['artifacts']['result'] = str(out / 'result.json')
        (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    if args.raw:
        if result.get('error'):
            print(result['error'], file=sys.stderr)
        if result['steps']:
            with pathlib.Path(result['steps'][-1]['stdout']).open('rb') as output:
                shutil.copyfileobj(output, sys.stdout.buffer)
            for step in result['steps']:
                with pathlib.Path(step['stderr']).open('rb') as errors:
                    shutil.copyfileobj(errors, sys.stderr.buffer)
        elif result['data'] is not None:
            print(json.dumps(result['data'], indent=2))
    elif args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"tvh {result['command']}: {result['status']}")
        if result.get('error'):
            print(result['error'], file=sys.stderr)
        if args.command == 'doctor':
            print(json.dumps(result['data'], indent=2))
        for step in result['steps']:
            for stream in ('stdout', 'stderr'):
                if stream == 'stdout' and step.get('stdout_streamed'):
                    continue
                path = pathlib.Path(step[stream])
                with path.open('rb') as log:
                    preview = log.read(PREVIEW_BYTES)
                print(preview.decode(errors='replace'), end='', file=sys.stderr if stream == 'stderr' else sys.stdout)
                if path.stat().st_size > PREVIEW_BYTES:
                    print(f'\nPreview limited; full output: {path}')
        if out:
            print(f'Evidence: {out}')
    if result['status'] == 'incomplete':
        return 2
    return 1 if result['status'] in ('failed', 'findings') else 0


if __name__ == '__main__':
    sys.exit(main())
