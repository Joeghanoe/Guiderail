"""Public tool coverage and real command boundaries. External operations use stand-ins only."""
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
CLI = ROOT / 'harness/tvh'
spec = importlib.util.spec_from_file_location('cli_catalog', ROOT / 'harness/tools/cli/catalog.py')
catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='tvh catalog ')
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.cwd = self.root / 'source'
        self.cwd.mkdir()
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.env = dict(os.environ, PATH=str(self.bin) + os.pathsep + os.environ['PATH'],
                        GOLDEN_PATH_HOME=str(self.root / 'runtime'))

    def run_cli(self, *args, input_text=None):
        proc = subprocess.run([sys.executable, '-I', str(CLI), *args], cwd=self.cwd,
                              env=self.env, input=input_text, capture_output=True, text=True, timeout=90)
        self.assertTrue(proc.stdout.strip(), proc.stderr)
        return proc, json.loads(proc.stdout)

    def stub(self, name, body):
        path = self.bin / name
        path.write_text('#!/usr/bin/env python3\n' + body)
        path.chmod(0o755)

    def test_every_executable_tool_is_classified_and_every_route_has_offline_help(self):
        coverage = catalog.inventory()
        self.assertEqual(coverage['errors'], [])
        self.assertGreater(coverage['tool_files'], 60)
        for entry in coverage['public_commands']:
            with self.subTest(command=entry['path']):
                proc = subprocess.run([sys.executable, '-I', str(CLI), *entry['path'], '--help'],
                                      env=self.env, capture_output=True, text=True, timeout=15)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertIn('usage:', proc.stdout)

    def test_inventory_rejects_new_unregistered_tools_and_stale_classification(self):
        (self.root / 'tools').mkdir()
        (self.root / 'tools/new.py').write_text('raise SystemExit(0)')
        data = dict(commands=[], builtins=[], internal=[dict(tool='missing.sh', reason='stale')])
        with patch.object(catalog, 'BUNDLE', self.root), patch.object(catalog, 'manifest', return_value=data):
            errors = catalog.inventory()['errors']
        self.assertIn('Unclassified tool: new.py', errors)
        self.assertIn('Missing tool: missing.sh', errors)

    def test_bundle_registry_density_and_plan_are_available_without_script_discovery(self):
        for command in (['bundle', 'check'], ['checks', 'registry'],
                        ['context', 'candidates'], ['orchestrate', 'tier']):
            proc, data = self.run_cli(*command, '--json')
            self.assertEqual((proc.returncode, data['status']), (0, 'completed'), data)
            self.assertEqual(data['command'], ' '.join(command))
            self.assertEqual(data['data']['native_exit_code'], 0)

    def test_explicit_stdin_scope_reaches_iac_and_scenario_checks(self):
        (self.cwd / 'bad.bicep').write_text("resource r 'x@1' = { properties: { minTlsVersion: '1.0' } }\n")
        changed = self.root / 'changed.txt'
        changed.write_text('bad.bicep\n')
        proc, data = self.run_cli('checks', 'iac', '--json', '--input-file', str(changed))
        self.assertEqual((proc.returncode, data['status']), (1, 'failed'), data)
        proc, data = self.run_cli('checks', 'iac', '--json')
        self.assertEqual((proc.returncode, data['status']), (2, 'incomplete'))
        proc, data = self.run_cli('checks', 'iac', '--json', '--input-file', '-', input_text='bad.bicep\n')
        self.assertEqual(proc.returncode, 1, data)
        config = self.root / 'scenarios.json'
        config.write_text('[{"component":"src/**","scenarios":["tests/**"]}]')
        changed.write_text('src/Orders.cs\n')
        proc, data = self.run_cli('checks', 'scenarios', '--json', '--input-file', str(changed),
                                 '--', '--config', str(config))
        self.assertEqual((proc.returncode, data['status']), (1, 'failed'), data)

    def test_findings_render_and_validation_keep_rejected_findings_incomplete(self):
        findings = self.root / 'findings.json'
        findings.write_text('[{"rule_id":"UNKNOWN","file":"app.cs","line":1,"evidence":"x","confidence":"high"}]')
        proc, data = self.run_cli('findings', 'validate', '--json', '--', str(findings))
        self.assertEqual((proc.returncode, data['status']), (2, 'incomplete'), data)
        findings.write_text('[]')
        for op in ('validate', 'render'):
            proc, data = self.run_cli('findings', op, '--json', '--', str(findings))
            self.assertEqual(proc.returncode, 0, data)

    def test_spec_notes_write_only_to_the_native_vault_scope_and_do_not_overwrite(self):
        vault = self.root / 'vault'
        (vault / 'customer').mkdir(parents=True)
        native = ['--vault', str(vault), '--customer', 'customer', '--title', 'New orders']
        proc, data = self.run_cli('spec', 'new', '--json', '--', *native)
        self.assertEqual(proc.returncode, 0, data)
        proc, data = self.run_cli('spec', 'new', '--json', '--', *native)
        self.assertEqual((proc.returncode, data['status']), (2, 'incomplete'))
        proc, data = self.run_cli('spec', 'list', '--json', '--', '--vault', str(vault), '--customer', 'customer')
        self.assertEqual(proc.returncode, 0, data)

    def test_verification_outputs_default_to_the_external_evidence_directory(self):
        self.stub('gitleaks', 'raise SystemExit(0)\n')
        proc, data = self.run_cli('checks', 'review-plan', '--json', '--', '--selected', str(self.root / 'absent.json'))
        self.assertEqual((proc.returncode, data['status']), (2, 'incomplete'))
        selected = self.root / 'selected.json'
        selected.write_text('{"rules": {}}')
        proc, data = self.run_cli('checks', 'review-plan', '--json', '--', '--selected', str(selected))
        self.assertEqual(proc.returncode, 0, data)
        self.assertTrue(pathlib.Path(data['artifacts']['semantic-plan.json']).is_file())

    def test_native_repo_scope_cannot_contain_cli_evidence(self):
        proc, data = self.run_cli('checks', 'code-types', '--json', '--out', str(self.cwd / 'evidence'),
                                 '--', '--repo', str(self.cwd))
        self.assertEqual(proc.returncode, 2, data)
        self.assertFalse((self.cwd / 'evidence').exists())

    def test_read_wrappers_do_not_allow_mutations_and_do_not_evaluate_arguments(self):
        marker = self.root / 'called'
        self.stub('npm', f'from pathlib import Path\nPath({str(marker)!r}).touch()\n')
        proc, data = self.run_cli('deps', 'read', '--json', '--', 'npm', 'install', 'untrusted')
        self.assertEqual(proc.returncode, 2, data)
        self.assertFalse(marker.exists())
        proc, data = self.run_cli('dev', 'read', '--json', '--', 'http', 'get', 'https://example.com')
        self.assertEqual(proc.returncode, 2, data)

    def test_human_only_operations_never_start_from_noninteractive_sessions(self):
        marker = self.root / 'called'
        self.stub('docker', f'from pathlib import Path\nPath({str(marker)!r}).touch()\n')
        for command in (['benchmark', 'candidate', 'login'], ['frontend', 'auth-msal'], ['ado', 'pr', 'mine-comments']):
            proc, data = self.run_cli(*command, '--json', '--interactive')
            self.assertEqual((proc.returncode, data['status']), (2, 'incomplete'), data)
        self.assertFalse(marker.exists())

    def test_native_arguments_and_native_exit_codes_are_retained(self):
        self.stub('node', 'import json, sys\nprint(json.dumps(sys.argv[1:]))\nraise SystemExit(1)\n')
        literal = '$(touch no-shell-evaluation)'
        proc, data = self.run_cli('frontend', 'contrast', '--json', '--', '--pair', literal)
        self.assertEqual((proc.returncode, data['status']), (1, 'failed'), data)
        argv = json.loads(pathlib.Path(data['steps'][0]['stdout']).read_text())
        self.assertEqual(argv[-1], literal)
        self.assertFalse((self.cwd / 'no-shell-evaluation').exists())


if __name__ == '__main__':
    unittest.main()
