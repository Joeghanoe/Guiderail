"""CLI arguments and dispatch for local artifact workflows. Native tools own their behavior."""
import json
import importlib.util
import pathlib

BUNDLE = pathlib.Path(__file__).resolve().parents[2]


def add_parsers(commands, common):
    evaluation = commands.add_parser('eval', help='measure native skill selection, reference routing and handoffs in read-only sessions')
    skills = evaluation.add_subparsers(dest='action', required=True).add_parser('skills')
    common(skills)
    skills.add_argument('--engine', choices=('claude', 'copilot'), required=True)
    skills.add_argument('--model', required=True, help='exact provider model identifier; recorded with results')
    skills.add_argument('--only', action='append', help='case id, repeatable')
    skills.add_argument('--all', action='store_true', help='run every selection case with real model calls')
    skills.add_argument('--repeats', type=int, default=3)
    frontend = commands.add_parser('frontend', help='capture a local UI and compare capture reports')
    actions = frontend.add_subparsers(dest='action', required=True)
    capture = actions.add_parser('capture')
    common(capture)
    capture.add_argument('--url', action='append', required=True)
    capture.add_argument('--name', default='page')
    capture.add_argument('--viewports', default='320x640,390x844,768x1024,1280x800')
    capture.add_argument('--scheme', choices=('light', 'dark', 'both'), default='light')
    capture.add_argument('--wait', type=int, default=600)
    capture.add_argument('--scale', type=float, default=1)
    capture.add_argument('--full-page', action='store_true')
    capture.add_argument('--auth-state', type=pathlib.Path)
    compare = actions.add_parser('compare')
    common(compare)
    compare.add_argument('--before', type=pathlib.Path, required=True)
    compare.add_argument('--after', type=pathlib.Path, required=True)
    greenfield = commands.add_parser('greenfield', help='create design-first skeletons without overwriting')
    init = greenfield.add_subparsers(dest='action', required=True).add_parser('init')
    common(init)
    init.add_argument('--target', type=pathlib.Path, required=True)
    init.add_argument('--profile', choices=('generic', 'service', 'web-app'), default='generic')


def run(args, out, result, call, execute):
    if args.command == 'eval':
        spec = importlib.util.spec_from_file_location('tvh_skill_probe', BUNDLE / 'tools/testing/process_skills.py')
        probe = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(probe)
        # Keep process execution in the CLI so timeout, output and environment handling stay identical.
        probe.run(args, out, result, execute)
        return True
    if args.command == 'greenfield':
        argv = ['bash', str(BUNDLE / 'tools/greenfield/greenfield-init.sh')]
        if args.profile != 'generic':
            argv.append('--' + args.profile)
        target = args.target.expanduser().resolve()
        call([*argv, str(target)], 'greenfield')
        result['scope'] = {'target': str(target), 'profile': args.profile}
        result['data'] = {'design_status': 'requires-verification', 'approval': 'not-approved'}
        result['status'] = 'completed'
        return True
    if args.command != 'frontend':
        return False
    if args.action == 'compare':
        step = call(['node', str(BUNDLE / 'tools/frontend/compare-ui.mjs'), '--json',
                     '--before', str(args.before.resolve()), '--after', str(args.after.resolve())],
                    'comparison', allowed=(0, 2))
        comparison = json.loads(pathlib.Path(step['stdout']).read_text(encoding='utf-8'))
        summary = comparison.get('summary') if isinstance(comparison, dict) else None
        if not isinstance(summary, dict) or not all(type(summary.get(x)) is int for x in ('new', 'increased')):
            raise ValueError('Malformed frontend comparison')
        result['artifacts']['comparison'] = step['stdout']
        result['data'] = {'summary': summary, 'scope': comparison.get('scope')}
        result['status'] = 'failed' if step['exit_code'] == 2 else 'completed'
        return True
    if args.wait < 0 or args.scale <= 0:
        raise ValueError('--wait must be nonnegative and --scale must be positive')
    if not args.name or any(char in args.name for char in '/\\') or args.name in ('.', '..'):
        raise ValueError('--name must be a filename prefix, not a path')
    if args.auth_state and any(part == '.env' or part.startswith('.env.') and part != '.env.example'
                               for part in args.auth_state.resolve().parts):
        raise ValueError('Authentication state cannot be a dotenv file')
    capture = out / 'capture'
    argv = ['node', str(BUNDLE / 'tools/frontend/screenshot.mjs'), '--out', str(capture),
            '--name', args.name, '--viewports', args.viewports, '--scheme', args.scheme,
            '--wait', str(args.wait), '--scale', str(args.scale)]
    for url in args.url:
        argv += ['--url', url]
    if args.full_page:
        argv.append('--full-page')
    if args.auth_state:
        argv += ['--auth-state', str(args.auth_state.resolve())]
    call(argv, 'capture')
    report_path = capture / 'report.json'
    report = json.loads(report_path.read_text(encoding='utf-8'))
    if not isinstance(report, dict) or not isinstance(report.get('shots'), list) or not report['shots']:
        raise ValueError('Capture returned no evaluated screenshots')
    if any(not isinstance(shot, dict) or not isinstance(shot.get('findings'), list) for shot in report['shots']):
        raise ValueError('Capture returned a malformed screenshot report')
    result['artifacts']['capture'] = str(report_path)
    result['data'] = {'screenshots': len(report['shots']), 'axe': report.get('axe'),
                      'finding_count': sum(len(shot['findings']) for shot in report['shots']),
                      'visual_review': 'required'}
    result['status'] = 'completed'
    return True
