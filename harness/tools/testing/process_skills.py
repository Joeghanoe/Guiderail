"""Read-only native selection, reference-routing and handoff probes; workflow execution is unscored."""
import hashlib
import importlib.util
import json
import os
import pathlib
import shutil
import sys

BUNDLE = pathlib.Path(__file__).resolve().parents[2]
REPO = BUNDLE.parent
CASES = REPO / 'benchmarks/cases/process-skills.json'
SKILLS = tuple(p.parent.name for p in sorted((REPO / 'skills/engineering').glob('*/SKILL.md')))
RETIRED_SKILLS = ('tv-review', 'tv-diagnose-pipeline')


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def prepare(workspace, engine):
    """Native project discovery, with no modification to the user's personal skills or credentials."""
    directory = workspace / ('.github/skills' if engine == 'copilot' else '.claude/skills')
    guidance = module('skill_probe_guidance', BUNDLE / 'tools/harness/guidance.py')
    hashes = {}
    for entry in guidance.packages(REPO):
        name = entry.parent.name
        target = directory / name
        for relative, data in guidance.payload(entry, target, REPO, REPO).items():
            path = target / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            hashes[name + '/' + relative] = hashlib.sha256(data).hexdigest()

    return hashes


def command(engine, executable, model, prompt, run):
    if engine == 'copilot':
        return [executable, '--prompt', prompt, '--model', model, '--trust-folder', '--silent',
                '--output-format=json', '--available-tools=read,grep,glob,skill',
                '--allow-tool=read', '--allow-tool=grep', '--allow-tool=glob', '--allow-tool=skill',
                '--disable-builtin-mcps', '--no-auto-update', '--no-custom-instructions',
                '--add-dir', str(BUNDLE), '--log-dir', str(run / 'logs'),
                '--usage-output-file', str(run / 'native-usage.json')]
    return [executable, '-p', prompt, '--model', model, '--output-format', 'stream-json', '--verbose',
            '--tools', 'Read,Glob,Grep,Skill', '--allowedTools', 'Read,Glob,Grep,Skill',
            '--setting-sources', 'project', '--strict-mcp-config', '--no-session-persistence',
            '--add-dir', str(BUNDLE)]


def observed_calls(events):
    """Use model-issued tool calls only. Mentions, tool output and self-reported skill use do not count."""
    calls = []
    for event in events:
        if event.get('type') == 'assistant':
            message = event.get('message')
            if not isinstance(message, dict) or not isinstance(message.get('content'), list):
                raise ValueError('Malformed assistant event')
            for block in message['content']:
                if isinstance(block, dict) and block.get('type') == 'tool_use':
                    calls.append({'tool': block.get('name'), 'args': block.get('input') or {}})
        elif event.get('type') == 'tool.execution_start':
            data = event.get('data', {})
            if not isinstance(data, dict):
                raise ValueError('Malformed tool event')
            calls.append({'tool': data.get('toolName'), 'args': data.get('arguments') or {}})
    return calls


def selection(calls, expected):
    selected = []
    for call in calls:
        if str(call['tool']).lower() != 'skill':
            continue
        arguments = call['args']
        if not isinstance(arguments, dict):
            continue
        name = arguments.get('skill') or arguments.get('name') or arguments.get('skill_name')
        if isinstance(name, str):
            # Plugin-qualified skill identifiers retain their namespace in raw evidence.
            selected.append(name.split(':')[-1])
    relevant = sorted(set(selected) & set(SKILLS + RETIRED_SKILLS))
    return {'expected': expected, 'selected': relevant, 'all_selected': sorted(set(selected)),
            'match': relevant == ([expected] if expected else [])}


def read_paths(calls, workspace):
    paths = set()
    for call in calls:
        if str(call['tool']).lower() not in {'read', 'view'} or not isinstance(call['args'], dict):
            continue
        value = call['args'].get('file_path') or call['args'].get('path')
        if isinstance(value, str):
            path = pathlib.Path(value)
            paths.add(str((workspace / path).resolve() if not path.is_absolute() else path.resolve()))
    return sorted(paths)


def assess_guidance(case, calls, workspace, answer):
    paths = read_paths(calls, workspace)
    missing = [ref for ref in case.get('expected_references', []) if not any(p.endswith('/' + ref) for p in paths)]
    unrelated = [ref for ref in case.get('forbidden_references', []) if any(p.endswith('/' + ref) for p in paths)]
    handoff = None
    if case.get('expected_handoff'):
        try:
            clean = answer.strip().removeprefix('```json').removeprefix('```').removesuffix('```').strip()
            handoff = json.loads(clean).get('handoff') == case['expected_handoff']
        except (ValueError, AttributeError):
            handoff = False
    return {'read_paths': paths, 'missing_references': missing, 'unrelated_references': unrelated,
            'handoff_match': handoff, 'match': not missing and not unrelated and handoff is not False}


def run(args, out, result, execute):
    case_bytes = CASES.read_bytes()
    document = json.loads(case_bytes)
    runner_sha256 = hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()
    requested = set(args.only or [])
    available = {case['id'] for case in document['cases']}
    if requested - available:
        raise ValueError('Unknown cases: ' + ', '.join(sorted(requested - available)))
    if not requested and not args.all:
        raise ValueError('Choose --only <case-id> or --all; native model calls are explicit')
    if requested and args.all:
        raise ValueError('Choose --only or --all, not both')
    if not 1 <= args.repeats <= 10:
        raise ValueError('--repeats must be 1..10')
    executable = shutil.which(args.engine)
    if not executable:
        raise ValueError(f'{args.engine} is not on PATH; no installation or authentication was attempted')
    usage = module('skill_probe_usage', BUNDLE / 'tools/review/usage.py')
    adapter = module('skill_probe_adapter', BUNDLE / f'tools/review/run-{args.engine}.py')
    environment = {key: os.environ[key] for key in adapter.CLI_ENVIRONMENT if key in os.environ}
    version_step = execute([executable, '--version'], out, out, 'engine-version', 15, environment)
    result['steps'].append(version_step)
    version = (pathlib.Path(version_step['stdout']).read_text(encoding='utf-8', errors='replace').strip()[:1024]
               if version_step['exit_code'] == 0 else None)
    records = []
    cases = [case for case in document['cases'] if args.all or case['id'] in requested]
    for case in cases:
        for repeat in range(args.repeats):
            run_dir = out / f"{case['id']}-{repeat + 1}"
            workspace = run_dir / 'workspace'
            workspace.mkdir(parents=True)
            hashes = prepare(workspace, args.engine)
            for name, value in case.get('fixtures', {}).items():
                if pathlib.Path(name).name != name:
                    raise ValueError('Fixture names must be local filenames')
                (workspace / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
            prompt = ('Choose the appropriate initial engineering process for the request below. '
                      'Read applicable process guidance using the available tools. '
                      'This probe assesses initial process selection only: do not execute commands, '
                      'change files, authenticate, or call external services. '
                      'Explain the next step and any missing information.\n\nRequest:\n' + case['request'] + '\n\nAvailable context:\n' + case['setup'])
            if case.get('expected_handoff'):
                prompt += ('\nRead the supplied fixture files. Return only a JSON object with a handoff field containing '
                           'criteria (id and exact approved text), verification_status (not-run, passed or failed), '
                           'and ready (whether the next requested action can proceed cleanly with this evidence).')
            (run_dir / 'prompt.txt').write_text(prompt, encoding='utf-8')
            step = execute(command(args.engine, executable, args.model, prompt, run_dir), workspace,
                           run_dir, 'agent', args.timeout, environment)
            result['steps'].append(step)
            events, parse_errors = [], 0
            for line in pathlib.Path(step['stdout']).read_text(encoding='utf-8', errors='replace').splitlines():
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                    if not isinstance(event, dict):
                        raise ValueError('event is not an object')
                    events.append(event)
                except ValueError:
                    parse_errors += 1
            try:
                calls = observed_calls(events)
            except ValueError:
                calls = []
                parse_errors += 1
            completed = (any(e.get('type') == 'result' and not e.get('is_error') for e in events)
                         if args.engine == 'claude' else any(e.get('type') in ('assistant.idle', 'session.idle') for e in events))
            errors = any(e.get('type') == 'session.error' for e in events)
            model_answer = any(e.get('type') == 'assistant.message' and isinstance(e.get('data'), dict)
                               and bool(e['data'].get('content')) for e in events)
            if args.engine == 'claude':
                model_answer = any(e.get('type') == 'result' and bool(e.get('result')) for e in events)
            violations = [call['tool'] for call in calls
                          if str(call['tool']).lower() not in {'read', 'view', 'grep', 'glob', 'skill'}]
            complete = (step['exit_code'] == 0 and not parse_errors and completed and not errors
                        and model_answer and not violations)
            observed = selection(calls, case['selection_skill']) if complete else None
            answer = (next((e.get('result', '') for e in reversed(events) if e.get('type') == 'result'), '')
                      if args.engine == 'claude' else '\n'.join(e.get('data', {}).get('content', '') for e in events
                      if e.get('type') == 'assistant.message' and isinstance(e.get('data'), dict)))
            guidance_result = assess_guidance(case, calls, workspace, answer) if complete else None
            metrics = {metric: None for metric in document['metrics']}
            metrics['wall_seconds'] = step['wall_seconds']
            if guidance_result:
                paths = [pathlib.Path(p) for p in guidance_result['read_paths']]
                metrics['loaded_guidance_bytes'] = sum(p.stat().st_size for p in paths if p.is_file() and p.suffix == '.md')
            native = run_dir / 'native-usage.json'
            if native.is_file():
                counts = usage.from_usage_file(json.loads(native.read_text(encoding='utf-8')))
                metrics.update({key: counts.get(key) for key in ('input_tokens', 'cached_input_tokens', 'output_tokens')})
            elif args.engine == 'claude':
                final = next((e for e in reversed(events) if e.get('type') == 'result'), {})
                counts = usage.from_claude(final)
                metrics.update({key: counts.get(key) for key in ('input_tokens', 'cached_input_tokens', 'output_tokens')})
            records.append({'case': case['id'], 'repeat': repeat + 1,
                            'status': 'completed' if complete else 'incomplete', 'selection': observed,
                            'guidance': guidance_result, 'tool_calls': calls, 'trace': step['stdout'], 'skill_hashes': hashes,
                            'fixture_hashes': {name: hashlib.sha256((workspace / name).read_bytes()).hexdigest()
                                               for name in case.get('fixtures', {})},
                            'tool_policy_violations': violations,
                            'metrics': metrics, 'workflow_status': 'not-assessed'})
    report = {'schema_version': 1, 'engine': args.engine, 'engine_version': version, 'model': args.model,
              'measurement': 'native-skill-selection-reference-routing-and-handoff-inspection',
              'limitations': ['Personal client configuration and skills may also be loaded.',
                              'Tool restrictions are not a sandbox.', 'Full workflow execution is not assessed; handoff cases inspect retained artifacts without executing code.',
                              'Loaded guidance bytes estimate full sizes of requested files; delivery success, partial reads and automatic injection are not measured.',
                              'No adoption thresholds or token-efficiency comparison are applied.'],
              'cases_sha256': hashlib.sha256(case_bytes).hexdigest(), 'runner_sha256': runner_sha256,
              'records': records}
    report_path = out / 'skill-selection.json'
    report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    result['artifacts']['skill_selection'] = str(report_path)
    result['data'] = {'runs': len(records), 'completed': sum(r['status'] == 'completed' for r in records),
                      'matches': sum(bool(r['selection'] and r['selection']['match'] and r['guidance'] and r['guidance']['match']) for r in records),
                      'workflow_status': 'not-assessed'}
    result['status'] = ('incomplete' if any(r['status'] != 'completed' for r in records) else
                        'failed' if result['data']['matches'] != len(records) else 'completed')
