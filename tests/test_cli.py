"""CLI contracts against real wrappers and temporary repositories; no provider or network calls."""
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CLI = ROOT / 'harness/tvh'


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='tvh tests ')
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.repo = self.root / 'source with spaces'
        self.repo.mkdir()
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.environment = dict(os.environ, GOLDEN_PATH_HOME=str(self.root / 'gp'),
                                PATH=str(self.bin) + os.pathsep + os.environ['PATH'])
        self.git('init', '-q', '-b', 'main')
        self.git('config', 'user.email', 'test@invalid')
        self.git('config', 'user.name', 'test')
        (self.repo / 'app.cs').write_text('class App {}\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'baseline')

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args], check=True, capture_output=True)

    def invoke(self, *args, env=None):
        result = subprocess.run([sys.executable, '-I', str(CLI), *args], cwd=self.repo,
                                env=env or self.environment, capture_output=True, text=True, timeout=40)
        return result, json.loads(result.stdout)

    def stub(self, name, body):
        path = self.bin / name
        path.write_text('#!/usr/bin/env python3\n' + body)
        path.chmod(0o755)

    def test_context_preserves_selection_and_paths_with_spaces(self):
        (self.repo / 'file with spaces.cs').write_text('class Other {}')
        run, data = self.invoke('context', 'select', '--json', '--repo', str(self.repo),
                                'file with spaces.cs')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn('CODE.5', data['data']['summary'])
        self.assertTrue(pathlib.Path(data['artifacts']['result']).is_file())
        self.assertFalse(any(self.repo.glob('tvh-*')))

    def test_context_changed_requires_valid_explicit_baseline(self):
        for extra in ([], ['--baseline', 'does-not-exist']):
            with self.subTest(extra=extra):
                run, data = self.invoke('context', 'select', '--json', '--changed', *extra)
                self.assertEqual(run.returncode, 2)
                self.assertEqual(data['status'], 'incomplete')
        run, data = self.invoke('context', 'select', '--json', '--changed', '--baseline', 'HEAD')
        self.assertEqual(run.returncode, 0, run.stderr)

    def test_output_must_be_fresh_and_outside_source(self):
        for out in (self.repo / 'evidence', self.root):
            run, data = self.invoke('doctor', '--json', '--out', str(out))
            self.assertEqual(run.returncode, 2)
            self.assertEqual(data['status'], 'incomplete')
        self.assertFalse((self.repo / 'evidence').exists())
        nested = self.repo / 'nested'
        nested.mkdir()
        result = subprocess.run([sys.executable, '-I', str(CLI), 'doctor', '--json',
                                 '--out', str(self.repo / 'evidence')], cwd=nested, env=self.environment,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.repo / 'evidence').exists())

    def test_doctor_never_executes_provider_or_cloud_cli(self):
        marker = self.root / 'called'
        for name in ('az', 'claude', 'copilot'):
            self.stub(name, f'from pathlib import Path\nPath({str(marker)!r}).touch()\n')
        run, data = self.invoke('doctor', '--json')
        self.assertEqual(run.returncode, 0)
        self.assertFalse(marker.exists())
        self.assertEqual(data['data']['credentials'], 'not inspected')

    def test_cloud_mutations_and_secret_reads_are_refused_before_cli(self):
        marker = self.root / 'called'
        self.stub('az', f'from pathlib import Path\nPath({str(marker)!r}).touch()\n')
        for command in (['group', 'delete', '--name', 'x'], ['account', 'get-access-token'], ['login']):
            run, data = self.invoke('cloud', 'read', '--json', 'az', *command)
            self.assertEqual(run.returncode, 2)
            self.assertEqual(data['status'], 'incomplete')
        self.assertFalse(marker.exists())

    def test_cloud_arguments_are_forwarded_without_shell_evaluation(self):
        self.stub('az', 'import json, sys\nprint(json.dumps(sys.argv[1:]))\n')
        literal = '$(touch should-not-exist); echo hi'
        run, data = self.invoke('cloud', 'read', '--json', 'az', 'group', 'list', '--query', literal)
        self.assertEqual(run.returncode, 0, run.stderr)
        output = json.loads(pathlib.Path(data['steps'][0]['stdout']).read_text())
        self.assertEqual(output, ['group', 'list', '--query', literal])
        self.assertFalse((self.repo / 'should-not-exist').exists())

    def test_read_failure_and_timeout_are_incomplete(self):
        self.stub('az', 'raise SystemExit(4)\n')
        run, data = self.invoke('cloud', 'read', '--json', 'az', 'group', 'list')
        self.assertEqual((run.returncode, data['status']), (2, 'incomplete'))
        self.stub('az', 'import time\ntime.sleep(10)\n')
        run, data = self.invoke('cloud', 'read', '--json', '--timeout', '1', 'az', 'group', 'list')
        self.assertEqual(run.returncode, 2)
        self.assertTrue(data['steps'][0]['timed_out'])

    def verify_script(self, body):
        scripts = self.repo / 'scripts'
        scripts.mkdir(exist_ok=True)
        (scripts / 'verify.sh').write_text('#!/usr/bin/env bash\n' + body)

    def test_verify_missing_failed_success_and_receipt(self):
        run, data = self.invoke('verify', '--json')
        self.assertEqual((run.returncode, data['status']), (2, 'incomplete'))
        self.verify_script('exit 1\n')
        run, data = self.invoke('verify', '--json')
        self.assertEqual((run.returncode, data['status']), (1, 'failed'), data)
        receipt = json.loads(pathlib.Path(data['artifacts']['verification']).read_text())
        self.assertEqual(receipt['status'], 'fail')
        self.verify_script('test "$HARNESS_REPO_ROOT" = "$PWD"\n')
        run, data = self.invoke('verify', '--json')
        self.assertEqual((run.returncode, data['status']), (0, 'completed'), data)
        receipt = json.loads(pathlib.Path(data['artifacts']['verification']).read_text())
        self.assertEqual(receipt['status'], 'pass')
        self.assertNotEqual(receipt['approval'], 'approved')

    def test_verify_detects_source_mutation(self):
        self.verify_script('echo "changed" >> app.cs\n')
        run, data = self.invoke('verify', '--json')
        self.assertEqual((run.returncode, data['status']), (2, 'incomplete'), data)

    def replay(self, findings):
        replay = self.root / 'replay.json'
        replay.write_text(findings)
        return dict(self.environment, HARNESS_REPLAY_FILE=str(replay))

    def test_review_distinguishes_findings_clean_and_dropped_output(self):
        (self.repo / 'app.cs').write_text('class App { void Run() {} }\n')
        finding = {'rule_id': 'CODE.5', 'file': 'app.cs', 'line': 1, 'severity': 'major',
                   'evidence': 'class App', 'summary': 'test finding', 'confidence': 'high'}
        for payload, code, status in ((json.dumps([finding]), 1, 'findings'), ('[]', 0, 'completed'),
                                      ('not json', 2, 'incomplete'),
                                      (json.dumps([dict(finding, rule_id='UNKNOWN')]), 2, 'incomplete')):
            with self.subTest(payload=payload):
                run, data = self.invoke('review', '--json', '--baseline', 'HEAD', '--engine', 'replay',
                                        env=self.replay(payload))
                self.assertEqual((run.returncode, data['status']), (code, status), data)
                if code in (0, 1):
                    self.assertEqual(data['data']['approval'], 'not-approved')

    def test_review_never_reads_untracked_or_tracked_dotenv(self):
        (self.repo / '.env').write_text('DO_NOT_READ=this-is-a-test\n')
        run, data = self.invoke('review', '--json', '--baseline', 'HEAD', '--engine', 'replay', env=self.replay('[]'))
        self.assertEqual(run.returncode, 2)
        self.assertIn('untracked', data['error'])
        self.git('add', '.env')
        run, data = self.invoke('review', '--json', '--baseline', 'HEAD', '--engine', 'replay', env=self.replay('[]'))
        self.assertEqual(run.returncode, 2)
        self.assertIn('dotenv', data['error'])
        for path in pathlib.Path(data['artifacts']['directory']).iterdir():
            self.assertNotIn('this-is-a-test', path.read_text())

    def test_review_detects_source_changes_from_a_provider(self):
        (self.repo / 'app.cs').write_text('class Changed {}\n')
        self.stub('claude', 'import json, pathlib\npathlib.Path("app.cs").write_text("mutated")\n'
                            'print(json.dumps({"result": "[]"}))\n')
        run, data = self.invoke('review', '--json', '--baseline', 'HEAD', '--engine', 'claude')
        self.assertEqual((run.returncode, data['status']), (2, 'incomplete'))
        self.assertIn('Source state changed', data['error'])

    def test_human_preview_is_bounded_but_complete_output_is_retained(self):
        self.stub('az', 'print("a" * 20000)\n')
        result = subprocess.run([sys.executable, '-I', str(CLI), 'cloud', 'read', 'az', 'group', 'list'],
                                cwd=self.repo, env=self.environment, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertLess(len(result.stdout), 14000)
        evidence = pathlib.Path(result.stdout.split('Evidence: ')[-1].strip())
        data = json.loads((evidence / 'result.json').read_text())
        self.assertEqual(len(pathlib.Path(data['steps'][0]['stdout']).read_text().strip()), 20000)

    def test_ado_uses_restricted_reader_and_preserves_project_spaces(self):
        self.stub('az', 'print("fake-reader-token")\n')
        self.stub('curl', '''import json, pathlib, sys
sys.stdin.read()
args = sys.argv[1:]
url = args[-1]
if '/timeline?' in url:
    body = {'records': []}
else:
    assert '/Team%20Project/' in url
    body = {'id': 123, 'buildNumber': 'build-123', 'result': 'failed', 'definition': {'name': 'build'}}
pathlib.Path(args[args.index('-o') + 1]).write_text(json.dumps(body))
print('200', end='')
''')
        run, data = self.invoke('ado', 'run', 'diagnose', '--json', '--organization', 'https://dev.azure.com/test',
                                '--project', 'Team Project', '--id', '123')
        self.assertEqual(run.returncode, 0, data)
        stdout = pathlib.Path(data['steps'][0]['stdout']).read_text()
        self.assertIn('Run build-123', stdout)
        self.assertNotIn('fake-reader-token', json.dumps(data) + stdout)
        run, data = self.invoke('ado', 'run', 'diagnose', '--json', '--organization', 'https://evil.invalid/test',
                                '--project', 'Team Project', '--id', '123')
        self.assertEqual((run.returncode, data['status']), (2, 'incomplete'))

    def test_pipeline_watch_maps_a_failed_run_and_streams_without_duplication(self):
        self.stub('az', 'print("reader-token")\n')
        self.stub('curl', '''import json, pathlib, sys
sys.stdin.read()
args = sys.argv[1:]
body = {'records': []} if '/timeline?' in args[-1] else {
    'id': 123, 'buildNumber': 'build', 'status': 'completed', 'result': 'failed',
    'sourceBranch': 'refs/heads/main', 'sourceVersion': 'abcdef123'}
pathlib.Path(args[args.index('-o') + 1]).write_text(json.dumps(body))
print('200', end='')
''')
        command = ['ado', 'run', 'watch', '--organization', 'https://dev.azure.com/test',
                   '--project', 'Team Project', '--run', '123']
        run, data = self.invoke(*command, '--json')
        self.assertEqual((run.returncode, data['status']), (1, 'failed'))
        native = subprocess.run([sys.executable, '-I', str(CLI), *command], cwd=self.repo,
                                env=self.environment, capture_output=True, text=True)
        self.assertEqual(native.returncode, 1, native.stderr)
        self.assertEqual(native.stdout.count('WATCHING'), 1)
        self.assertEqual(native.stdout.count('DONE run 123'), 1)

    def test_frontend_comparison_maps_regression_to_failure_and_bad_input_to_incomplete(self):
        def report(path, findings):
            path.write_text(json.dumps({'axe': 'run', 'shots': [
                {'url': 'http://localhost:1234', 'viewport': '320x640', 'scheme': 'light',
                 'file': 'synthetic.png', 'findings': findings}]}))
        before, after = self.root / 'before.json', self.root / 'after.json'
        report(before, [])
        report(after, [{'check': 'contrast', 'wcag': '1.4.3', 'detail': '1 node'}])
        run, data = self.invoke('frontend', 'compare', '--json', '--before', str(before), '--after', str(after))
        self.assertEqual((run.returncode, data['status']), (1, 'failed'), data)
        self.assertEqual(data['steps'][0]['exit_code'], 2)
        report(after, [])
        run, data = self.invoke('frontend', 'compare', '--json', '--before', str(before), '--after', str(after))
        self.assertEqual((run.returncode, data['status']), (0, 'completed'), data)
        after.write_text('invalid')
        run, data = self.invoke('frontend', 'compare', '--json', '--before', str(before), '--after', str(after))
        self.assertEqual((run.returncode, data['status']), (2, 'incomplete'))

    def test_capture_refuses_remote_urls_and_path_prefixes(self):
        for extra in (['--url', 'https://example.com'],
                      ['--url', 'http://localhost:1234', '--name', '../escape']):
            run, data = self.invoke('frontend', 'capture', '--json', *extra)
            self.assertEqual((run.returncode, data['status']), (2, 'incomplete'))
        self.assertFalse((self.repo / 'escape').exists())

    def test_capture_records_report_without_claiming_visual_review(self):
        self.stub('node', '''import json, pathlib, sys
args = sys.argv[1:]
out = pathlib.Path(args[args.index('--out') + 1])
out.mkdir()
(out / 'report.json').write_text(json.dumps({'axe': 'not run', 'shots': [{'findings': []}]}))
''')
        run, data = self.invoke('frontend', 'capture', '--json', '--url', 'http://localhost:1234')
        self.assertEqual((run.returncode, data['status']), (0, 'completed'), data)
        self.assertEqual(data['data']['visual_review'], 'required')
        self.assertTrue(pathlib.Path(data['artifacts']['capture']).is_file())

    def test_greenfield_initialization_is_idempotent_and_preserves_existing_design(self):
        target = self.root / 'new service'
        run, data = self.invoke('greenfield', 'init', '--json', '--target', str(target), '--profile', 'service')
        self.assertEqual((run.returncode, data['status']), (0, 'completed'), data)
        design = target / 'docs/solution-design.md'
        self.assertTrue(design.is_file())
        design.write_text('An existing design')
        run, data = self.invoke('greenfield', 'init', '--json', '--target', str(target), '--profile', 'service')
        self.assertEqual(run.returncode, 0)
        self.assertEqual(design.read_text(), 'An existing design')
        self.assertFalse((target / 'src').exists())

    def test_verify_design_forwards_the_mode(self):
        self.verify_script('test "${1:-}" = --design\n')
        run, data = self.invoke('verify', '--json', '--design')
        self.assertEqual((run.returncode, data['status']), (0, 'completed'), data)

    def test_scaffolded_design_verification_uses_the_cli_bundle_and_rejects_unfinished_design(self):
        run, data = self.invoke('greenfield', 'init', '--json', '--target', str(self.repo), '--profile', 'service')
        self.assertEqual(run.returncode, 0, data)
        run, data = self.invoke('verify', '--json', '--design')
        self.assertEqual((run.returncode, data['status']), (1, 'failed'), data)
        receipt = json.loads(pathlib.Path(data['artifacts']['verification']).read_text())
        self.assertEqual(receipt['status'], 'fail')

    def skill_probe_stub(self, events):
        self.stub('copilot', 'import json, sys\n'
                  'if "--version" in sys.argv:\n    print("fixture-cli")\n    raise SystemExit(0)\n' +
                  '\n'.join(f'print(json.dumps({event!r}))' for event in events) + '\n')

    def test_native_skill_probe_observes_calls_and_does_not_trust_self_reports(self):
        native_call = {'type': 'tool.execution_start',
                       'data': {'toolName': 'skill', 'arguments': {'skill': 'tv-review'}}}
        complete = {'type': 'assistant.idle', 'data': {}}
        answer = {'type': 'assistant.message', 'data': {'content': 'The next step is verification.'}}
        for events, code, status in (([native_call, answer, complete], 0, 'completed'),
                                      ([{'type': 'assistant.message', 'data': {'content': 'I used tv-review'}}, complete], 1, 'failed'),
                                      ([native_call], 2, 'incomplete'),
                                      ([complete], 2, 'incomplete')):
            self.skill_probe_stub(events)
            run, data = self.invoke('eval', 'skills', '--json', '--engine', 'copilot', '--model', 'test-model',
                                    '--only', 'review-change', '--repeats', '1')
            self.assertEqual((run.returncode, data['status']), (code, status), data)
            report = json.loads(pathlib.Path(data['artifacts']['skill_selection']).read_text())
            self.assertEqual(report['model'], 'test-model')
            self.assertEqual(report['records'][0]['workflow_status'], 'not-assessed')
            self.assertIsNone(report['records'][0]['metrics']['input_tokens'])
            argv = data['steps'][-1]['argv']
            self.assertIn('--available-tools=read,grep,glob,skill', argv)
            self.assertNotIn('--allow-all-tools', argv)

    def test_operational_probe_does_not_require_a_dedicated_skill(self):
        self.skill_probe_stub([{'type': 'assistant.message', 'data': {'content': 'Read the run through the CLI.'}},
                               {'type': 'assistant.idle', 'data': {}}])
        run, data = self.invoke('eval', 'skills', '--json', '--engine', 'copilot', '--model', 'test-model',
                                '--only', 'diagnose-failure', '--repeats', '1')
        self.assertEqual((run.returncode, data['status']), (0, 'completed'), data)
        workspace = pathlib.Path(data['artifacts']['directory']) / 'diagnose-failure-1/workspace'
        self.assertTrue((workspace / '.github/skills/tv-review/SKILL.md').is_file())
        self.assertFalse((workspace / '.github/skills/tv-diagnose-pipeline').exists())
        self.skill_probe_stub([{'type': 'tool.execution_start', 'data': {
            'toolName': 'skill', 'arguments': {'skill': 'tv-diagnose-pipeline'}}},
            {'type': 'assistant.message', 'data': {'content': 'Loaded a retired skill.'}},
            {'type': 'assistant.idle', 'data': {}}])
        run, data = self.invoke('eval', 'skills', '--json', '--engine', 'copilot', '--model', 'test-model',
                                '--only', 'diagnose-failure', '--repeats', '1')
        self.assertEqual((run.returncode, data['status']), (1, 'failed'))

    def test_guard_accepts_cli_reads_but_refuses_mutations_and_shell_chaining(self):
        for command, code in (('tvh cloud read az group list', 0),
                              ('~/.golden-path-harness/bin/tvh cloud read az group list', 0),
                              ('tvh cloud read az group delete --name x', 2),
                              ('tvh cloud read az group list; az group list', 2)):
            payload = json.dumps({'tool_input': {'command': command}})
            run = subprocess.run(['bash', str(ROOT / 'harness/hooks/guard-bash.sh')],
                                 input=payload, text=True, capture_output=True, env=self.environment)
            self.assertEqual(run.returncode, code, (command, run.stderr))

    def test_installer_updates_and_removes_only_owned_cli_and_skills(self):
        home = self.root / 'home'
        vscode = self.root / 'vscode'
        vscode.mkdir()
        env = dict(self.environment, HOME=str(home), HARNESS_VSCODE_USER_DIR=str(vscode))
        retired = home / '.copilot/skills/tv-diagnose-pipeline/SKILL.md'
        retired.parent.mkdir(parents=True)
        retired.write_text('---\nname: tv-diagnose-pipeline\ndescription: Investigate an actual failed Azure DevOps '
                           'pipeline run and identify its cause from run evidence.\n---\n'
                           'Follow ~/.golden-path-harness/harness/playbooks/diagnose-pipeline-failure.md')
        personal = home / '.claude/skills/tv-diagnose-pipeline/SKILL.md'
        personal.parent.mkdir(parents=True)
        personal.write_text('A personal skill referencing playbooks/diagnose-pipeline-failure.md')
        for mode in ([], [], ['--uninstall']):
            run = subprocess.run(['bash', str(ROOT / 'install.sh'), *mode], env=env, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertTrue(personal.exists())
            launcher = self.root / 'gp/bin/tvh'
            skill = home / '.copilot/skills/tv-review/SKILL.md'
            if mode:
                self.assertFalse(launcher.exists())
                self.assertFalse(skill.exists())
            else:
                result = subprocess.run([str(launcher), 'doctor', '--json'], cwd=self.repo, env=env,
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(str(self.root / 'gp'), skill.read_text())
                self.assertFalse(retired.exists())
                settings = json.loads((home / '.claude/settings.json').read_text())
                self.assertFalse(any('tvh *' in x for x in settings['permissions']['allow']))
                hook = self.root / 'gp/harness/hooks/guard-bash.sh'
                payload = json.dumps({'tool_input': {'command': f'"{launcher}" cloud read az group list'}})
                allowed = subprocess.run(['bash', str(hook)], input=payload, text=True,
                                         capture_output=True, env=env)
                self.assertEqual(allowed.returncode, 0, allowed.stderr)
        launcher.parent.mkdir(exist_ok=True)
        launcher.write_text('unrelated executable')
        run = subprocess.run(['bash', str(ROOT / 'install.sh')], env=env, capture_output=True, text=True)
        self.assertNotEqual(run.returncode, 0)
        self.assertEqual(launcher.read_text(), 'unrelated executable')


if __name__ == '__main__':
    unittest.main()
