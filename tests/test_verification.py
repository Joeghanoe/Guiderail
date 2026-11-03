"""Registry, evidence and C# integration contracts, with no model or cloud calls."""
import copy
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
SCRIPT = ROOT / 'harness/tools/verification/verify.py'
spec = importlib.util.spec_from_file_location('verification', SCRIPT)
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = pathlib.Path(self.temp.name)
        self.repo = self.work / 'repo'
        self.repo.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.email', 'test@invalid')
        self.git('config', 'user.name', 'test')
        (self.repo / 'Widget.cs').write_text('class Widget {} class Legacy {}')
        self.git('add', '.')
        self.git('commit', '-qm', 'baseline')

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args], check=True, capture_output=True, text=True).stdout.strip()

    def cli(self, *args):
        return subprocess.run([sys.executable, '-I', str(SCRIPT), *args], capture_output=True, text=True, timeout=90)

    def test_registry_rejects_invalid_contracts(self):
        original = v.read_json(v.REGISTRY)
        self.assertGreaterEqual(len(v.registry()), 5)
        mutations = [lambda d: d.update(schema_version=2),
                     lambda d: d['requirements'].append(copy.deepcopy(d['requirements'][0])),
                     lambda d: d['requirements'][0].update(parent_rule_id='MISSING'),
                     lambda d: d['requirements'][0].update(automation_tool=[]),
                     lambda d: d['requirements'][0].update(source='../outside.md'),
                     lambda d: d['requirements'][0].update(installation='required')]
        for mutate in mutations:
            data = copy.deepcopy(original)
            mutate(data)
            file = self.work / 'registry.json'
            file.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                v.registry(file)

    def record(self, name, code):
        out = self.work / name
        run = self.cli('run', '--repo', str(self.repo), '--out', str(out),
                       '--requirement', 'T.1.verify-command', '--', sys.executable, '-c', f'print("evidence"); raise SystemExit({code})')
        return run, v.read_json(out / 'receipt.json')

    def test_command_status_and_evidence(self):
        for code, status in ((0, 'pass'), (1, 'fail'), (2, 'error')):
            with self.subTest(code=code):
                run, report = self.record(f'command-{code}', code)
                self.assertEqual(run.returncode, code, run.stderr)
                self.assertEqual(report['status'], status)
                self.assertEqual(report['approval'], 'not-assessed')
                self.assertTrue(report['checks'][0]['stdout_sha256'])
                self.assertIn('evidence', (self.work / f'command-{code}/command.stdout.txt').read_text())

    def test_command_cannot_forge_structural_or_semantic_pass(self):
        for rid in ('CODE.5.file-layout', 'CODE.5.responsibility', 'SEC.2.secret-scan'):
            run = self.cli('run', '--repo', str(self.repo), '--out', str(self.work / 'forged'),
                           '--requirement', rid, '--', sys.executable, '-c', 'pass')
            self.assertEqual(run.returncode, 2)

    def test_missing_required_result_is_incomplete_and_review_stays_pending(self):
        self.record('command', 0)
        out = self.work / 'summary.json'
        run = self.cli('report', '--out', str(out), '--required', 'T.1.verify-command', 'CODE.5.file-layout',
                       '--review', 'CODE.5.responsibility', '--results', str(self.work / 'command/receipt.json'))
        self.assertEqual(run.returncode, 2, run.stderr)
        report = v.read_json(out)
        self.assertEqual(report['missing'], ['CODE.5.file-layout'])
        self.assertEqual(report['semantic_review']['status'], 'pending')
        self.assertEqual(report['approval'], 'not-assessed')

    def test_summary_rejects_different_dirty_states(self):
        self.record('one', 0)
        (self.repo / 'Widget.cs').write_text('class Widget { int Value; } class Legacy {}')
        _, second = self.record('two', 0)
        second['requirement_id'] = 'CODE.5.file-layout'
        v.write_json(self.work / 'two/receipt.json', second)
        run = self.cli('report', '--out', str(self.work / 'summary.json'), '--required', 'T.1.verify-command',
                       '--results', str(self.work / 'one/receipt.json'), str(self.work / 'two/receipt.json'))
        self.assertEqual(run.returncode, 2)
        self.assertIn('different source', run.stderr)

    def test_timeout_and_mutation_are_errors(self):
        for name, script, extra in [('timeout', 'import time; time.sleep(3)', ['--timeout', '1']),
                                    ('mutation', 'open("changed.txt", "w").write("changed")', [])]:
            run = self.cli('run', '--repo', str(self.repo), '--out', str(self.work / name),
                           '--requirement', 'T.1.verify-command', *extra, '--', sys.executable, '-c', script)
            self.assertEqual(run.returncode, 2, run.stderr)
            self.assertEqual(v.read_json(self.work / name / 'receipt.json')['status'], 'error')

    def test_output_inside_source_is_rejected(self):
        run = self.cli('run', '--repo', str(self.repo), '--out', str(self.repo / 'evidence'),
                       '--requirement', 'T.1.verify-command', '--', sys.executable, '-c', 'pass')
        self.assertEqual(run.returncode, 2)
        self.assertFalse((self.repo / 'evidence').exists())

    def test_csharp_baseline_and_configurations(self):
        (self.repo / 'Widget.cs').write_text('class Widget {} class Legacy {} class Added {}')
        run = self.cli('code-types', '--repo', str(self.repo), '--out', str(self.work / 'types'))
        self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
        receipt = v.read_json(self.work / 'types/receipt.json')
        report = receipt['checks'][-1]['report']
        self.assertEqual([f['type'] for f in report['findings']], ['Added'])
        self.assertEqual([f['type'] for f in report['inheritedFindings']], ['Widget', 'Legacy'])
        (self.repo / 'Widget.cs').write_text('class Widget {}\n#if FEATURE\nclass Extra {}\n#endif')
        run = self.cli('code-types', '--repo', str(self.repo), '--out', str(self.work / 'conditional'))
        self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
        run = self.cli('code-types', '--repo', str(self.repo), '--out', str(self.work / 'symbols'),
                       '--symbols', 'none', '--symbols', 'FEATURE')
        self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
        receipt = v.read_json(self.work / 'symbols/receipt.json')
        self.assertEqual(receipt['configurations'], ['none', 'FEATURE'])
        self.assertEqual(receipt['checks'][1]['status'], 'pass')
        self.assertEqual(receipt['checks'][2]['status'], 'fail')

    def test_copied_bundle_does_not_claim_consumer_revision(self):
        copied = self.repo / '.harness'
        copied.mkdir()
        (copied / 'index.md').write_text('copied bundle')
        with patch.object(v, 'BUNDLE', copied):
            identity = v.harness_identity()
        self.assertIsNone(identity['harness_commit'])
        self.assertIsNone(identity['harness_dirty'])
        self.assertEqual(identity['harness_provenance'], 'copied-bundle-revision-unknown')
        self.assertTrue(identity['harness_inputs_sha256'])

    def test_malformed_receipt_fails_cleanly(self):
        result = self.work / 'malformed.json'
        result.write_text('[]')
        run = self.cli('report', '--out', str(self.work / 'summary.json'),
                       '--required', 'T.1.verify-command', '--results', str(result))
        self.assertEqual(run.returncode, 2)
        self.assertIn('receipt lacks source provenance', run.stderr)
        self.assertNotIn('Traceback', run.stderr)

    def test_untracked_types_are_checked_without_selector_input(self):
        (self.repo / 'Wrong.cs').write_text('public record Added(int Value);')
        run = self.cli('code-types', '--repo', str(self.repo), '--out', str(self.work / 'untracked'))
        self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
        receipt = v.read_json(self.work / 'untracked/receipt.json')
        self.assertEqual(receipt['paths'], ['Wrong.cs'])
        self.assertEqual(receipt['checks'][-1]['report']['findings'][0]['type'], 'Added')

    def test_unresolved_merge_cannot_report_no_changes(self):
        with patch.object(v, 'git', return_value=b'unmerged'):
            with self.assertRaisesRegex(ValueError, 'merge conflicts'):
                v.source_paths(self.repo, 'baseline', False)

    def test_semantic_plan_ignores_unrelated_masked_sources(self):
        # Reviewer evals may mask examples. Unused E-016 source must not break a CODE.5 plan.
        original = v.file_reference
        def masked(root, path):
            if path.startswith('examples/'):
                raise ValueError('masked example')
            return original(root, path)
        with patch.object(v, 'file_reference', side_effect=masked):
            plan = v.registry(parents={'CODE.5'}, semantic_only=True)
        self.assertEqual(set(plan), {'CODE.5.responsibility'})

    def test_no_csharp_changes_and_invalid_baseline(self):
        run = self.cli('code-types', '--repo', str(self.repo), '--out', str(self.work / 'empty'))
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(v.read_json(self.work / 'empty/receipt.json')['status'], 'not-applicable')
        run = self.cli('code-types', '--repo', str(self.repo), '--out', str(self.work / 'badbase'), '--baseline', 'no-such-ref')
        self.assertEqual(run.returncode, 2)
        self.assertEqual(v.read_json(self.work / 'badbase/receipt.json')['status'], 'error')


if __name__ == '__main__':
    unittest.main()
