"""Thin adapters for pinned, off-the-shelf scanners. No custom secret/IaC rules."""
import hashlib
import json
import os
import pathlib
import subprocess

import verify as v


def run(args):
    secret = args.command == 'gitleaks'
    rid = 'SEC.2.secret-scan' if secret else 'IAC.4.resolved-vault'
    item = v.registry(parents={'SEC.2' if secret else 'IAC.4'})[rid]
    repo = args.repo.resolve()
    out = v.output_dir(args.out, repo)
    receipt = v.base_receipt(rid, repo, args.stage)
    receipt.update(checks=[], coverage=item['coverage'])
    lock_path = pathlib.Path(__file__).with_name('tool-lock.json')
    lock = v.read_json(lock_path)
    receipt['tool_lock_sha256'] = hashlib.sha256(lock_path.read_bytes()).hexdigest()
    try:
        tools = args.tools.resolve()
        if v.read_json(tools / 'tool-lock.json') != lock:
            raise ValueError('Tool installation does not match checked-in lock; run install-tools.py')
        binary = tools / ('gitleaks' if secret else 'bicep')
        env = os.environ.copy()
        env['DOTNET_BUNDLE_EXTRACT_BASE_DIR'] = str(tools / 'extract')
        version = subprocess.run([str(binary), 'version' if secret else '--version'], capture_output=True,
                                 text=True, timeout=30, env=env, check=True).stdout.strip()
        if (secret and version != lock['gitleaks']) or (not secret and not version.startswith('Bicep CLI version ' + lock['bicep'] + ' ')):
            raise ValueError('Unexpected scanner/compiler version')
        receipt['tool_version'] = version
        if secret:
            command = [str(binary), 'dir' if args.working_tree else 'git', '--no-banner', '--redact=100',
                       '--ignore-gitleaks-allow', '--gitleaks-ignore-path', str(v.BUNDLE / 'tools/verification/gitleaks.ignore'), '--config', str(v.BUNDLE / 'tools/verification/gitleaks.toml'),
                       '--report-format', 'json', '--report-path', str(out / 'findings.json')]
            if args.baseline and args.working_tree:
                raise ValueError('--baseline and --working-tree are different scan scopes')
            if not args.working_tree:
                head = v.git(repo, 'rev-parse', '--verify', 'HEAD^{commit}')
                baseline = v.git(repo, 'rev-parse', '--verify', args.baseline + '^{commit}') if args.baseline else None
                if baseline:
                    v.git(repo, 'merge-base', '--is-ancestor', baseline, head)
                receipt.update(baseline=baseline, head=head)
                command += ['--log-opts=' + (baseline + '..' + head if baseline else head)]
            receipt['scan_scope'] = 'working-tree' if args.working_tree else 'commit-range' if args.baseline else 'head-history'
            command.append(str(repo))
            check = v.execute(command, repo, out, 'gitleaks', args.timeout)
            receipt['checks'].append(check)
            findings = v.read_json(out / 'findings.json')
            if not isinstance(findings, list):
                raise ValueError('Invalid Gitleaks report')
            # Keep locations and rule IDs, never raw secret/match values, in the retained report.
            findings = [{key: f.get(key) for key in ('RuleID', 'File', 'StartLine', 'EndLine', 'Fingerprint')} for f in findings]
            v.write_json(out / 'findings.json', findings)
            receipt.update(status='fail' if findings and check['exit_code'] == 1 else 'pass' if not findings and check['exit_code'] == 0 else 'error', findings=findings)
        else:
            template = args.template.resolve()
            if not template.is_relative_to(repo) or not template.is_file():
                raise ValueError('Template must be an existing file inside --repo')
            receipt['template'] = template.relative_to(repo).as_posix()
            receipt['template_sha256'] = hashlib.sha256(template.read_bytes()).hexdigest()
            if template.suffix == '.bicep':
                compiled = out / 'template.json'
                check = v.execute([str(binary), 'build', str(template), '--no-restore', '--outfile', str(compiled)],
                                  repo, out, 'bicep', args.timeout, env=env)
                receipt['checks'].append(check)
                if check['exit_code'] != 0:
                    raise ValueError('Bicep compilation failed; inspect retained diagnostics')
            elif template.suffix == '.json':
                compiled = template
            else:
                raise ValueError('Pilot accepts Bicep or ARM template JSON plus optional ARM parameters JSON')
            command = ['pwsh', '-NoLogo', '-NoProfile', '-File', str(v.BUNDLE / 'tools/verification/keyvault.ps1'),
                       '-ToolsDirectory', str(tools), '-TemplateFile', str(compiled), '-OutputFile', str(out / 'psrule.json')]
            if args.parameters:
                parameters = args.parameters.resolve()
                if not parameters.is_relative_to(repo) or not parameters.is_file():
                    raise ValueError('Parameters must be an existing file inside --repo')
                receipt['parameters_sha256'] = hashlib.sha256(parameters.read_bytes()).hexdigest()
                command += ['-ParameterFile', str(parameters)]
            # Isolated cwd avoids loading a consumer's unreviewed rule/config scripts.
            check = v.execute(command, out, out, 'psrule', args.timeout)
            receipt['checks'].append(check)
            report = v.read_json(out / 'psrule.json')
            if report.get('schema_version') != 1 or not isinstance(report.get('results'), list):
                raise ValueError('Invalid PSRule report')
            failed = [r for r in report['results'] if r['outcome'] == 'Fail']
            expected = 1 if failed else 0
            if check['exit_code'] != expected:
                raise ValueError('PSRule exit disagrees with report')
            receipt.update(status='fail' if failed else 'pass' if report['vaults'] else 'not-applicable', report=report)
        if v.provenance(repo) != receipt['provenance']:
            receipt.update(status='error', error='Source state changed during verification')
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        receipt.update(status='error', error=str(error))
    compiled = out / 'template.json'
    if compiled.is_file():
        receipt['compiled_template_sha256'] = hashlib.sha256(compiled.read_bytes()).hexdigest()
        compiled.unlink()  # Retain evidence hashes, not a second copy of deployment configuration.
    v.write_json(out / 'receipt.json', receipt)
    print(f"{receipt['status']}: {rid}; evidence {out / 'receipt.json'}")
    return {'pass': 0, 'not-applicable': 0, 'fail': 1}.get(receipt['status'], 2)
