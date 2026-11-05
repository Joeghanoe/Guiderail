"""Packaging and document discovery contracts, with isolated native-client homes."""
import hashlib
import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path
import subprocess
import tempfile
import unittest
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('guidance', ROOT / 'harness/tools/harness/guidance.py')
guidance = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guidance)
spec = importlib.util.spec_from_file_location('process_skills', ROOT / 'harness/tools/testing/process_skills.py')
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class GuidanceTests(unittest.TestCase):
    def test_document_graph_reaches_indexes_without_directory_link_resolution(self):
        pending = [ROOT / 'README.md']
        reached = set()
        while pending:
            source = pending.pop()
            if source in reached:
                continue
            reached.add(source)
            for match in guidance.LINK.finditer(guidance.prose(source.read_text())):
                target = guidance.target_path(source, match[2], ROOT)
                if target is not None and target.is_file() and target.suffix == '.md':
                    pending.append(target)
        indexes = {p for p in guidance.markdown_files(ROOT) if p.name == 'index.md'}
        self.assertEqual(sorted(str(p.relative_to(ROOT)) for p in indexes - reached), [])

    def test_source_catalog_links_and_active_reachability(self):
        self.assertEqual(guidance.check_catalog(ROOT), [])
        self.assertEqual(guidance.audit(ROOT)['errors'], [])

    def test_link_audit_catches_broken_edges_and_unreachable_active_guidance(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / 'README.md').write_text('[Missing](missing.md)')
            active = repo / 'skills/engineering/example/SKILL.md'
            active.parent.mkdir(parents=True)
            active.write_text('Example')
            errors = guidance.audit(repo)['errors']
            self.assertTrue(any('missing link' in e for e in errors))
            self.assertTrue(any('unreachable' in e for e in errors))
            (repo / 'README.md').write_text('[Active](skills/engineering/example/SKILL.md)')
            self.assertEqual(guidance.audit(repo)['errors'], [])

    def test_standalone_bundle_validation_does_not_audit_unrelated_sibling_documents(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            bundle = repo / 'alternate-bundle'
            shutil.copytree(ROOT / 'harness', bundle, ignore=shutil.ignore_patterns('bin', 'obj', '__pycache__'))
            (repo / 'skills').mkdir()
            (repo / 'skills/processes.json').write_text('{}')
            (repo / 'unrelated.md').write_text('[Not part of this bundle](missing.md)')
            run = subprocess.run([sys.executable, '-I', str(bundle / 'tools/harness/bundle.py'),
                                  '--root', str(bundle), 'check'], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)

    def test_native_packages_keep_siblings_and_resolve_shared_links_with_spaces(self):
        with tempfile.TemporaryDirectory(prefix='skill install ') as tmp:
            root = Path(tmp)
            installed = root / 'custom harness'
            installed.mkdir()
            for name in ('harness', 'skills', 'docs'):
                (installed / name).symlink_to(ROOT / name, target_is_directory=True)
            for client in ('.claude', '.copilot'):
                for entry in guidance.packages(ROOT):
                    target = root / client / 'skills' / entry.parent.name
                    guidance.publish(entry, target, ROOT, installed)
                    for source in entry.parent.rglob('*'):
                        if source.is_file():
                            self.assertTrue((target / source.relative_to(entry.parent)).is_file())
                    for path in target.rglob('*.md'):
                        for match in guidance.LINK.finditer(guidance.prose(path.read_text())):
                            raw = unquote(match[2]).split('#')[0]
                            if '://' not in raw and not raw.startswith('#'):
                                self.assertTrue((path.parent / raw).exists(), (path, raw))
                    guidance.publish(entry, target, ROOT, installed)
                    personal = target / 'PERSONAL.md'
                    personal.write_text('keep')
                    guidance.uninstall(target)
                    self.assertEqual(personal.read_text(), 'keep')
                    self.assertFalse((target / 'SKILL.md').exists())

    def test_conflicts_and_modified_owned_files_are_preserved(self):
        entry = ROOT / 'skills/engineering/design/SKILL.md'
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'design'
            target.mkdir()
            personal = target / 'SKILL.md'
            personal.write_text('personal design skill')
            with self.assertRaisesRegex(ValueError, 'Skill-name conflict'):
                guidance.publish(entry, target, ROOT, ROOT)
            self.assertEqual(personal.read_text(), 'personal design skill')
            personal.unlink()
            guidance.publish(entry, target, ROOT, ROOT)
            personal.write_text('personal edit')
            with self.assertRaisesRegex(ValueError, 'Skill-name conflict'):
                guidance.publish(entry, target, ROOT, ROOT)
            guidance.uninstall(target)
            self.assertEqual(personal.read_text(), 'personal edit')

    def test_install_preflights_all_clients_before_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / 'home'
            path = home / '.copilot/skills/design/SKILL.md'
            path.parent.mkdir(parents=True)
            path.write_text('personal skill')
            env = dict(os.environ, HOME=str(home), GOLDEN_PATH_HOME=str(Path(tmp) / 'gp'),
                       HARNESS_VSCODE_USER_DIR=str(Path(tmp) / 'vscode'))
            run = subprocess.run(['bash', str(ROOT / 'install.sh')], env=env, capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn('Skill-name conflict', run.stderr)
            self.assertFalse((Path(tmp) / 'gp').exists())
            self.assertEqual(path.read_text(), 'personal skill')

    def test_legacy_debug_migrates_for_both_clients_and_install_roots(self):
        old = (ROOT / 'tests/fixtures/legacy-debug.txt').read_bytes()
        for custom in (False, True):
            with self.subTest(custom=custom), tempfile.TemporaryDirectory() as tmp:
                home = Path(tmp) / 'home'
                installed = Path(tmp) / 'custom harness' if custom else home / '.golden-path-harness'
                vscode = Path(tmp) / 'vscode'
                env = dict(os.environ, HOME=str(home), GOLDEN_PATH_HOME=str(installed),
                           HARNESS_VSCODE_USER_DIR=str(vscode))
                for client in ('.claude', '.copilot'):
                    directory = home / client / 'skills/debug'
                    directory.mkdir(parents=True)
                    content = old.replace(b'~/.golden-path-harness', str(installed).encode()) if custom else old
                    (directory / 'SKILL.md').write_bytes(content)
                    (directory / 'PERSONAL.md').write_text('keep')
                for _ in range(2):
                    run = subprocess.run(['bash', str(ROOT / 'install.sh')], env=env,
                                         capture_output=True, text=True)
                    self.assertEqual(run.returncode, 0, run.stderr)
                for client in ('.claude', '.copilot'):
                    directory = home / client / 'skills/debug'
                    self.assertIsNotNone(guidance.manifest(directory))
                    self.assertTrue((directory / 'HYPOTHESIS-LOOP.md').is_file())
                    self.assertEqual((directory / 'PERSONAL.md').read_text(), 'keep')
                    self.assertNotEqual((directory / 'SKILL.md').read_bytes(), old)

    def test_modified_legacy_debug_still_conflicts(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / 'debug'
            directory.mkdir()
            old = (ROOT / 'tests/fixtures/legacy-debug.txt').read_bytes() + b'\nPersonal change\n'
            (directory / 'SKILL.md').write_bytes(old)
            hashes = json.loads((ROOT / 'skills/legacy-packages.json').read_text())['debug']
            with self.assertRaisesRegex(ValueError, 'Skill-name conflict'):
                guidance.publish(ROOT / 'skills/engineering/debug/SKILL.md', directory, ROOT, ROOT, hashes)
            self.assertEqual((directory / 'SKILL.md').read_bytes(), old)

    def test_known_legacy_review_is_removed_but_personal_namesake_survives(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / 'home'
            vscode = Path(tmp) / 'vscode'
            vscode.mkdir()
            old = (ROOT / 'tests/fixtures/legacy-review.txt').read_bytes()
            for client, data in (('.claude', old), ('.copilot', b'personal review')):
                path = home / client / 'skills/tv-review/SKILL.md'
                path.parent.mkdir(parents=True)
                path.write_bytes(data)
            env = dict(os.environ, HOME=str(home), GOLDEN_PATH_HOME=str(Path(tmp) / 'gp'),
                       HARNESS_VSCODE_USER_DIR=str(vscode))
            run = subprocess.run(['bash', str(ROOT / 'install.sh')], env=env, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertFalse((home / '.claude/skills/tv-review/SKILL.md').exists())
            self.assertEqual((home / '.copilot/skills/tv-review/SKILL.md').read_text(), 'personal review')
            instructions = vscode / 'prompts/teamvalue.instructions.md'
            for match in guidance.LINK.finditer(guidance.prose(instructions.read_text())):
                self.assertTrue(Path(unquote(match[2])).exists(), match[2])

    def test_probe_packages_every_skill_and_scores_reference_routes_and_handoffs(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            hashes = probe.prepare(workspace, 'copilot')
            self.assertIn('design/COMPARE-ALTERNATIVE-DESIGNS.md', hashes)
            self.assertNotIn('tv-review/SKILL.md', hashes)
            path = workspace / '.github/skills/design/COMPARE-ALTERNATIVE-DESIGNS.md'
            calls = [{'tool': 'view', 'args': {'path': str(path)}}]
            case = {'expected_references': ['design/COMPARE-ALTERNATIVE-DESIGNS.md'],
                    'forbidden_references': ['harness/playbooks/start-greenfield.md'],
                    'expected_handoff': {'criteria': [{'id': 'A1', 'text': 'Approved'}], 'verification_status': 'failed', 'ready': False}}
            answer = json.dumps({'handoff': case['expected_handoff']})
            self.assertTrue(probe.assess_guidance(case, calls, workspace, answer)['match'])
            calls.append({'tool': 'Read', 'args': {'file_path': str(ROOT / 'harness/playbooks/start-greenfield.md')}})
            self.assertFalse(probe.assess_guidance(case, calls, workspace, answer)['match'])
            self.assertFalse(probe.assess_guidance(case, [], workspace, 'I followed the guidance')['match'])
            changed = {'handoff': dict(case['expected_handoff'], criteria=[{'id': 'A1', 'text': 'Invented'}])}
            self.assertFalse(probe.assess_guidance(case, calls[:1], workspace, json.dumps(changed))['match'])


if __name__ == '__main__':
    unittest.main()
