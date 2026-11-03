"""Selection compatibility and successful context delivery across hook protocols."""
import datetime
import importlib.util
import json
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
BUNDLE = ROOT / 'harness'
spec = importlib.util.spec_from_file_location('context_delivery', BUNDLE / 'tools/harness/context.py')
ctx = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ctx)


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.state = pathlib.Path(self.temp.name)

    def payload(self, path, session='session'):
        return dict(session_id=session, tool_input=dict(file_path=path))

    def test_selector_preserves_fixture_rule_sets(self):
        fixtures = json.loads((ROOT / 'tests/fixtures/selector-cases.json').read_text())
        for case in fixtures:
            selected = ctx.bundle.select_documents(BUNDLE, case['paths'])
            self.assertEqual(sorted(selected['rules'].values()), case['expected_rule_ids'], case['name'])

    def test_new_rules_for_same_extension_are_delivered(self):
        first = ctx.deliver(self.payload('src/config.json'), BUNDLE, self.state)
        self.assertNotIn('DEL.2:', json.dumps(first))
        second = ctx.deliver(self.payload('src/package.json'), BUNDLE, self.state)
        self.assertIn('DEL.2:', json.dumps(second))
        self.assertEqual(ctx.deliver(self.payload('src/package.json'), BUNDLE, self.state), {})
        records = list(self.state.rglob('*.json'))
        self.assertEqual(len(records), 2)
        self.assertIsNone(json.loads(records[0].read_text())['opened_documents'])

    def test_session_isolation_and_uncached_delivery(self):
        for session in ('one', 'two', ''):
            self.assertIn('hookSpecificOutput', ctx.deliver(self.payload('src/A.cs', session), BUNDLE, self.state))
        self.assertEqual(len(list(self.state.rglob('*.json'))), 2)

    def test_failed_selection_does_not_write_success(self):
        fake = self.state / 'bundle'
        (fake / 'rules').mkdir(parents=True)
        (fake / 'rules/bad.md').write_text('---\ntype: Rule\nrule_id: BAD\napplies_to: not-json\n---\n')
        state = self.state / 'state'
        with self.assertRaises(ValueError):
            ctx.deliver(self.payload('src/A.cs'), fake, state)
        self.assertFalse(state.exists())

    def test_changed_document_content_is_redelivered(self):
        fake = self.state / 'bundle'
        (fake / 'rules').mkdir(parents=True)
        source = fake / 'rules/a.md'
        source.write_text('---\ntype: Rule\nrule_id: TEST\ndescription: Test\napplies_to: ["**"]\n---\nFirst boundary.')
        state = self.state / 'state'
        self.assertIn('hookSpecificOutput', ctx.deliver(self.payload('A.cs'), fake, state))
        self.assertEqual(ctx.deliver(self.payload('A.cs'), fake, state), {})
        source.write_text(source.read_text() + '\nChanged boundary.')
        self.assertIn('hookSpecificOutput', ctx.deliver(self.payload('A.cs'), fake, state))

    def test_agy_uses_same_successful_selection(self):
        payload = dict(conversationId='agy', toolCall=dict(name='edit_file', args=dict(Path='"src/A.cs"')))
        self.assertEqual(ctx.deliver(payload, BUNDLE, self.state, True)['decision'], 'deny')
        self.assertEqual(ctx.deliver(payload, BUNDLE, self.state, True)['decision'], 'allow')
        payload['toolCall'] = dict(name='run_command', args=dict(CommandLine='python3 bundle.py select; false'))
        self.assertEqual(ctx.deliver(payload, BUNDLE, self.state, True)['decision'], 'allow')

    def test_invalid_staleness_is_error_and_rejections_are_hints(self):
        with self.assertRaises(ValueError):
            ctx.bundle.is_stale({'stale_after': '2020-01-01T00:00:00'}, datetime.datetime.now(datetime.timezone.utc))
        fake = self.state / 'bundle'
        (fake / 'rules').mkdir(parents=True)
        (fake / 'examples').mkdir()
        (fake / 'rules/a.md').write_text('---\ntype: Rule\nrule_id: TEST\ndescription: Test\napplies_to: ["**"]\n---\n')
        (fake / 'examples/rejected.md').write_text('---\ntype: Example\nrule: /rules/a.md\nverdict: rejected\nverified: { by: human:test }\n---\n')
        selected = ctx.bundle.select_documents(fake, ['A.cs'])
        self.assertEqual(selected['precedent'], [])
        self.assertEqual(selected['hints'], ['/examples/rejected.md'])


if __name__ == '__main__':
    unittest.main()
