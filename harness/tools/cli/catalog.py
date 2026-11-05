"""Declared public commands and private implementation inventory for the harness CLI."""
import argparse
import ast
import json
import pathlib
import re
import shutil
import subprocess
import sys

BUNDLE = pathlib.Path(__file__).resolve().parents[2]
MANIFEST = pathlib.Path(__file__).with_name('catalog.json')


def manifest():
    return json.loads(MANIFEST.read_text(encoding='utf-8'))


def subcommands(parser, depth):
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return action
    return parser.add_subparsers(dest=f'catalog_level_{depth}', required=True)


def usage(item):
    try:
        source = (BUNDLE / 'tools' / item['tool']).read_text(encoding='utf-8')
    except OSError:
        return 'Implementation unavailable; run tvh tools --check.'
    if item['runtime'] == 'python':
        try:
            tree = ast.parse(source)
            options = sorted({arg.value for call in ast.walk(tree) if isinstance(call, ast.Call)
                              and isinstance(call.func, ast.Attribute) and call.func.attr == 'add_argument'
                              for arg in call.args if isinstance(arg, ast.Constant) and isinstance(arg.value, str)})
            return ((ast.get_docstring(tree) or item['summary'])[:3200] +
                    ('\n\nNative argument names: ' + ', '.join(options) if options else ''))
        except SyntaxError:
            return 'Native source contains a syntax error; command execution will be incomplete.'
    lines = source.splitlines()
    header = []
    for line in lines[1:]:
        if line and not line.startswith(('#', '//')):
            break
        header.append(line.lstrip('#/ '))
    return '\n'.join(header)[:4000]


def add_parsers(root, common):
    for item in manifest()['commands']:
        node = root
        for depth, word in enumerate(item['path']):
            children = subcommands(node, depth)
            node = children.choices.get(word) or children.add_parser(word, help=item['summary'])
        node.description = (item['summary'] + '\n\nEffects: ' + ', '.join(item['effects']) +
                            '\n\nNative arguments follow --. CLI options precede --.\n\n' + usage(item))
        node.formatter_class = argparse.RawDescriptionHelpFormatter
        common(node)
        node.add_argument('--cwd', type=pathlib.Path, default=pathlib.Path.cwd(), help='execution directory')
        node.add_argument('--input-file', type=pathlib.Path, help='explicit stdin file; - reads piped stdin')
        if item.get('global_root'):
            node.add_argument('--bundle-root', type=pathlib.Path, help='explicit alternative bundle root')
        if item.get('human_only'):
            node.add_argument('--interactive', action='store_true', help='human terminal only; no credential capture')
        node.add_argument('native_args', nargs=argparse.REMAINDER, help='native tool arguments, after --')
        node.set_defaults(catalog_command=item)
    commands = subcommands(root, 0)
    tools = commands.add_parser('tools', help='list public commands and check complete tool coverage')
    common(tools)
    tools.add_argument('--check', action='store_true', help='fail on unclassified, missing, or duplicate entries')


def inventory():
    data = manifest()
    covered = {item['tool'] for item in data['commands'] + data['builtins']}
    internal = {item['tool'] for item in data['internal']}
    actual = {p.relative_to(BUNDLE / 'tools').as_posix() for p in (BUNDLE / 'tools').rglob('*')
              if p.is_file() and not {'__pycache__', 'bin', 'obj', 'node_modules', '.git'} & set(p.parts) and
              (p.suffix in {'.py', '.sh', '.mjs', '.ps1', '.cs'} or p.name == 'dk')}
    errors = [f'Unclassified tool: {p}' for p in sorted(actual - covered - internal)]
    errors += [f'Missing tool: {p}' for p in sorted((covered | internal) - actual)]
    errors += [f'Public tool also classified internal: {p}' for p in sorted(covered & internal)]
    paths = [tuple(item['path']) for item in data['commands'] + data['builtins']]
    if len(paths) != len(set(paths)):
        errors.append('Duplicate public command path')
    for item in data['commands']:
        if set(item['success']) & set(item['failure']):
            errors.append('Overlapping exit mapping: ' + ' '.join(item['path']))
    return {'public_commands': data['builtins'] + data['commands'], 'internal': data['internal'],
            'tool_files': len(actual), 'public_tool_files': len(covered), 'errors': errors}


def documentation():
    data = manifest()
    rows = ['# Public commands and internal implementations', '',
            'This reference comes from [catalog.json](catalog.json). Use `tvh tools --check --json` to verify coverage.', '',
            'For declared native routes, place CLI controls before `--` and native arguments after it. '
            'Use `--json` for the execution envelope or `--raw` for native stdout. '
            'Human-only commands require `--interactive` in a terminal and do not capture credentials.', '',
            '| Command | Implementation | Effects |', '| --- | --- | --- |']
    for item in sorted(data['builtins'] + data['commands'], key=lambda i: i['path']):
        effect = ', '.join(item.get('effects', ['see CLI contract']))
        if item.get('human_only'):
            effect += '; human terminal only'
        rows.append('| `tvh ' + ' '.join(item['path']) + '` | [' + item['tool'] + '](../' + item['tool'] + ') | ' + effect + ' |')
    rows += ['', '## Internal implementations', '',
             'These are reached through the public commands or hook/profile protocols. '
             'They are not separate agent-facing commands.', '',
             '| File | Reason |', '| --- | --- |']
    rows += ['| [' + item['tool'] + '](../' + item['tool'] + ') | ' + item['reason'] + ' |' for item in data['internal']]
    return '\n'.join(rows) + '\n'


def raw_arguments(args):
    native = args.native_args
    return native[1:] if native[:1] == ['--'] else native


def source_roots(args):
    if not hasattr(args, 'catalog_command'):
        return []
    native = raw_arguments(args)
    cwd = args.cwd.expanduser().resolve()
    roots = []
    for i, argument in enumerate(native):
        if argument in ('--repo', '--root') and i + 1 < len(native):
            value = native[i + 1]
        elif argument.startswith(('--repo=', '--root=')):
            value = argument.partition('=')[2]
        else:
            continue
        path = pathlib.Path(value).expanduser()
        roots.append((cwd / path).resolve())
    return roots


def validate_finding_paths(file, repo):
    original = pathlib.Path(file)
    file = original.resolve(strict=True)
    if any(p == '.env' or p.startswith('.env.') and p != '.env.example' for p in (*original.parts, *file.parts)):
        raise ValueError('A dotenv file cannot be used as findings input')
    raw = file.read_text(encoding='utf-8')
    fenced = re.search(r'```(?:json)?\s*(\[.*\])\s*```', raw, flags=re.S)
    raw = fenced.group(1) if fenced else raw[raw.find('['):raw.rfind(']') + 1]
    findings = json.loads(raw)
    if not isinstance(findings, list):
        raise ValueError('Findings must be an array')
    for finding in findings:
        if not isinstance(finding, dict):
            raise ValueError('Each finding must be an object')
        name = finding.get('file', '')
        if not isinstance(name, str):
            raise ValueError('Finding file must be a repository-relative path')
        path = pathlib.PurePosixPath(name.lstrip('/'))
        if (not path.parts or path.parts[0] in {'.git', '.harness'} or '..' in path.parts
                or '\\' in name or pathlib.PureWindowsPath(name).drive):
            raise ValueError('Unsafe finding file path')
        resolved = (repo / path).resolve()
        if not resolved.is_relative_to(repo) or any(p == '.env' or p.startswith('.env.') and p != '.env.example' for p in resolved.parts):
            raise ValueError('Finding file resolves outside its source scope or to a dotenv file')


def run(args, out, result, execute):
    if args.command == 'tools':
        result['data'] = inventory()
        result['status'] = 'failed' if args.check and result['data']['errors'] else 'completed'
        return True
    item = getattr(args, 'catalog_command', None)
    if not item:
        return False
    cwd = args.cwd.expanduser().resolve(strict=True)
    if not cwd.is_dir():
        raise ValueError('--cwd must be a directory')
    native = raw_arguments(args)
    tool = BUNDLE / 'tools' / item['tool']
    if item.get('reject_dropped') or item.get('validate_findings'):
        if not native or native[0].startswith('-'):
            if native not in (['--help'], ['-h']):
                raise ValueError('Supply a findings JSON file as the first native argument')
        else:
            repo = cwd
            if '--repo' in native:
                if native.index('--repo') + 1 >= len(native):
                    raise ValueError('--repo needs a directory')
                repo = (cwd / native[native.index('--repo') + 1]).resolve()
            validate_finding_paths(cwd / native[0], repo)
            if item.get('validate_findings'):
                if len(native) != 1:
                    raise ValueError('Posting accepts one validated findings file')
                validated = execute([sys.executable, '-I', str(BUNDLE / 'tools/harness/bundle.py'),
                                     'findings', native[0], '--repo', str(cwd)], cwd, out,
                                    'validate-findings', args.timeout)
                result['steps'].append(validated)
                if validated['exit_code'] or 'dropped finding' in pathlib.Path(validated['stderr']).read_text(errors='replace'):
                    raise ValueError('Findings validation is incomplete; nothing was posted')
                native = [validated['stdout']]
    if item['runtime'] == 'csharp':
        project = out / 'checker'
        project.mkdir()
        for name in ('Program.cs', 'CheckTypes.csproj', 'NuGet.Config'):
            shutil.copyfile(tool.parent / name, project / name)
        build = execute(['dotnet', 'build', str(project / 'CheckTypes.csproj'), '--disable-build-servers',
                         '-p:UseSharedCompilation=false', '-c', 'Release', '-o', str(out / 'bin'),
                         '--nologo', '-v', 'quiet'], cwd, out, 'checker-build', args.timeout)
        result['steps'].append(build)
        if build['exit_code']:
            raise ValueError('C# checker build incomplete; see retained build output')
        command = ['dotnet', str(out / 'bin/CheckTypes.dll')]
    else:
        command = {'python': [sys.executable, '-I'], 'bash': ['bash'], 'node': ['node']}[item['runtime']] + [str(tool)]
    if item.get('global_root') and args.bundle_root:
        command += ['--root', str(args.bundle_root.resolve())]
    command += item.get('native', [])
    generated = {}
    for flag, relative in item.get('defaults', {}).items():
        aliases = [flag] + item.get('flag_aliases', {}).get(flag, [])
        if not any(arg == alias or arg.startswith(alias + '=') for arg in native for alias in aliases):
            command += [flag, str(out / relative)]
            generated[relative] = out / relative
    if item.get('artifact_position') is not None and len(native) == item['artifact_position']:
        target = out / item['artifact_name']
        native = [*native, str(target)]
        generated[item['artifact_name']] = target
    command += native
    result['scope'] = {'cwd': str(cwd), 'tool': item['tool'], 'effects': item['effects']}
    if item.get('human_only'):
        if args.json or args.raw or not args.interactive or not sys.stdin.isatty():
            raise ValueError('Human-only operation. Run this command with --interactive in your terminal; no credentials are captured.')
        code = subprocess.call(command, cwd=cwd)
        result['data'] = {'native_exit_code': code, 'interactive': True, 'credential_capture': False}
        result['status'] = 'completed' if code == 0 else 'incomplete'
        return True
    stdin = None
    if args.input_file:
        if str(args.input_file) == '-':
            if sys.stdin.isatty():
                raise ValueError('--input-file - requires piped input')
            stdin = out / 'input.txt'
            stdin.write_bytes(sys.stdin.buffer.read())
        else:
            stdin = args.input_file.resolve(strict=True)
        if any(p == '.env' or p.startswith('.env.') and p != '.env.example' for p in stdin.parts):
            raise ValueError('A dotenv file cannot be used as input')
    if item.get('requires_input') and stdin is None:
        raise ValueError('This check requires an explicit --input-file with its changed-path scope')
    step = execute(command, cwd, out, 'native', args.timeout, stdin_path=stdin)
    result['steps'].append(step)
    result['artifacts'].update({name: str(path) for name, path in generated.items() if path.exists()})
    code = step['exit_code']
    result['data'] = {'native_exit_code': code}
    if item.get('reject_dropped') and 'dropped finding' in pathlib.Path(step['stderr']).read_text(errors='replace'):
        raise ValueError('Findings were dropped; validation is incomplete')
    if code in item['success']:
        missing = [name for name, path in generated.items() if not path.exists()]
        for flag in item.get('required_artifacts', []):
            aliases = [flag] + item.get('flag_aliases', {}).get(flag, [])
            for i, arg in enumerate(command):
                if arg in aliases and i + 1 < len(command):
                    target = cwd / command[i + 1]
                elif any(arg.startswith(alias + '=') for alias in aliases):
                    target = cwd / arg.partition('=')[2]
                else:
                    continue
                if not target.exists():
                    missing.append(str(target))
                else:
                    result['artifacts'][flag.lstrip('-')] = str(target)
        if missing and '--help' not in native and '-h' not in native and not item.get('optional_output'):
            raise ValueError('Native operation returned no required artifact: ' + ', '.join(missing))
        result['status'] = 'completed'
    elif code in item['failure']:
        if item.get('failure_requires_stdout') and pathlib.Path(step['stdout']).stat().st_size == 0:
            raise ValueError('Native operation failed before producing a check result')
        result['status'] = 'failed'
    else:
        raise ValueError(f'Native operation incomplete (exit {code}); see retained diagnostics')
    return True
