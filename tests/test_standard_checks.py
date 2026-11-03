"""Calibrate real Gitleaks and PSRule. No cloud, model, or network during verification."""
import json
import os
import pathlib
import secrets
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'harness/tools/verification/verify.py'
TOOLS = os.environ.get('HARNESS_CHECK_TOOLS')


@unittest.skipUnless(TOOLS, 'Set HARNESS_CHECK_TOOLS to the pinned installation; CI requires real tools')
class StandardChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = pathlib.Path(self.temp.name).resolve()
        self.repo = self.base / 'repo'
        self.repo.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.name', 'test')
        self.git('config', 'user.email', 'test@invalid')
        (self.repo / 'README.md').write_text('Synthetic scanner fixture')
        self.commit()
        self.number = 0

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args], check=True, capture_output=True, text=True).stdout.strip()

    def commit(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')
        return self.git('rev-parse', 'HEAD')

    def run_check(self, command, expected, *options):
        self.number += 1
        out = self.base / f'result-{self.number}'
        run = subprocess.run([sys.executable, '-I', str(SCRIPT), command, '--repo', str(self.repo),
                              '--tools', TOOLS, '--out', str(out), *options], capture_output=True, text=True, timeout=120)
        self.assertEqual(run.returncode, expected, run.stdout + run.stderr + (out / 'receipt.json').read_text() + ''.join(p.read_text() for p in out.glob('*.stderr.txt')))
        return out, json.loads((out / 'receipt.json').read_text())

    def test_gitleaks_detects_generated_secret_and_retains_no_secret(self):
        baseline = self.git('rev-parse', 'HEAD')
        token = 'ghp_' + secrets.token_hex(18)
        (self.repo / 'leak.txt').write_text('credential=' + token + '\n')
        self.commit()
        out, receipt = self.run_check('gitleaks', 1, '--baseline', baseline)
        self.assertEqual(receipt['status'], 'fail')
        self.assertTrue(receipt['findings'])
        for file in out.rglob('*'):
            if file.is_file():
                self.assertNotIn(token.encode(), file.read_bytes(), file.name)
        # Inline comments and repository-local ignore files must not waive the shared policy.
        (self.repo / 'leak.txt').write_text('credential=' + token + ' # gitleaks:allow\n')
        self.run_check('gitleaks', 1, '--working-tree')

    def test_gitleaks_pr_scope_does_not_silently_scan_other_history(self):
        (self.repo / 'old.txt').write_text('credential=' + 'ghp_' + secrets.token_hex(18))
        baseline = self.commit()
        (self.repo / 'README.md').write_text('Benign change')
        self.commit()
        self.run_check('gitleaks', 0, '--baseline', baseline)
        self.run_check('gitleaks', 1)

    def test_psrule_expands_parameters_missing_settings_and_exact_scope(self):
        template = self.repo / 'vault.bicep'
        source = """param rbac bool = true
resource vault 'Microsoft.KeyVault/vaults@2023-07-01' = {
 name: 'synthetic-vault'
 location: 'westeurope'
 properties: {
  tenantId: '00000000-0000-0000-0000-000000000000'
  sku: { family: 'A', name: 'standard' }
  enableRbacAuthorization: rbac
  enableSoftDelete: true
  enablePurgeProtection: true
 }
}
""".replace("sku: { family: 'A', name: 'standard' }", "sku: {\n family: 'A'\n name: 'standard'\n}")
        template.write_text(source)
        _, receipt = self.run_check('psrule', 0, '--template', str(template))
        self.assertEqual(len(receipt['report']['results']), 3)
        parameters = self.repo / 'parameters.json'
        parameters.write_text(json.dumps({'$schema':'https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#', 'contentVersion':'1.0.0.0','parameters':{'rbac':{'value':False}}}))
        _, bad = self.run_check('psrule', 1, '--template', str(template), '--parameters', str(parameters))
        failures = [r['rule'] for r in bad['report']['results'] if r['outcome']=='Fail']
        self.assertEqual(failures, ['Azure.KeyVault.RBAC'])
        # A disabled legacy resource is absent after standard template expansion.
        legacy_resource = source[source.index('resource vault'):].replace('resource vault', 'resource legacyVault', 1)
        legacy_resource = legacy_resource.replace(' = {', ' = if (exposeLegacy) {', 1)
        legacy_resource = legacy_resource.replace("name: 'synthetic-vault'", "name: 'legacy-vault'")
        legacy_resource = legacy_resource.replace('enablePurgeProtection: true', 'enablePurgeProtection: false')
        template.write_text('param exposeLegacy bool = false\n' + source + '\n' + legacy_resource)
        covered, _ = self.run_check('psrule', 0, '--template', str(template))
        legacy = ROOT / 'harness/tools/iac/check-iac.py'
        result = subprocess.run([sys.executable, '-I', str(legacy), '--psrule-receipt', str(covered / 'receipt.json')],
                                input='vault.bicep\n', cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        template.write_text(template.read_text() + "\n// changed source\n")
        result = subprocess.run([sys.executable, '-I', str(legacy), '--psrule-receipt', str(covered / 'receipt.json')],
                                input='vault.bicep\n', cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)  # Stale evidence cannot suppress changed source.
        template.write_text(source.replace('enablePurgeProtection: true', ''))
        self.run_check('psrule', 1, '--template', str(template))
        template.write_text("param value string = 'synthetic'\noutput result string = value\n")
        _, no_vault = self.run_check('psrule', 0, '--template', str(template))
        self.assertEqual(no_vault['status'], 'not-applicable')
        template.write_text('not valid bicep')
        self.run_check('psrule', 2, '--template', str(template))


if __name__ == '__main__':
    unittest.main()
