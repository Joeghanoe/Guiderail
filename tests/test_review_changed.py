"""Changes to every supported reviewer/selector implementation must request evals."""
import pathlib
import subprocess
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / 'infra/scripts/review-changed.sh'


class ReviewChangedTests(unittest.TestCase):
    def test_changed_path_matrix(self):
        cases = {'harness/tools/harness/bundle.py': True, 'harness/tools/harness/context.py': True,
                 'harness/tools/review/run-codex.py': True, 'harness/tools/review/run-copilot.py': True,
                 'harness/tools/review/run-agy.py': True, 'harness/tools/review/thresholds.json': True,
                 'harness/tools/verification/requirements.json': True, 'harness/hooks/edit-gate.sh': True,
                 'AGENTS.base.md': True, 'adapters/tv-review.skill.md': True,
                 'harness/tvh': True, 'harness/tools/cli/main.py': True,
                 'harness/tools/cli/catalog.json': True,
                 'harness/rules/code/rule.md': True, 'docs/audits/note.md': False}
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            def git(*args):
                subprocess.run(['git', '-C', temp, *args], check=True, capture_output=True)
            git('init', '-q', '-b', 'main')
            git('config', 'user.email', 'test@invalid')
            git('config', 'user.name', 'test')
            (root / 'base.txt').write_text('baseline')
            git('add', '.')
            git('commit', '-qm', 'baseline')
            git('update-ref', 'refs/remotes/origin/main', 'HEAD')
            for path, expected in cases.items():
                with self.subTest(path=path):
                    git('reset', '--hard', '-q', 'origin/main')
                    target = root / path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text('change')
                    git('add', '.')
                    git('commit', '-qm', 'change')
                    result = subprocess.run(['bash', str(SCRIPT)], cwd=root, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual('EvalsNeeded' in result.stdout, expected)


if __name__ == '__main__':
    unittest.main()
