#!/usr/bin/env python3
"""Deliver selected context before edits and retain successful lookup receipts per session.

Input is Claude hook JSON, or agy JSON with --agy. State lives under the system
 temporary directory. No command-attempt marker is trusted. Selection runs on every
edit; only unchanged guidance content is deduplicated. This is not an access boundary.
"""
import hashlib
import json
import os
import pathlib
import sys
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import bundle


def deliver(payload, root, state_root, agy=False):
    if not isinstance(payload, dict):
        raise ValueError('hook payload must be an object')
    sid = payload.get('conversationId' if agy else 'session_id', '')
    if agy:
        tool = payload.get('toolCall', {})
        if tool.get('name') not in {'edit_file', 'write_file', 'replace_file_content', 'multi_replace_file_content', 'write_to_file'}:
            return {'decision': 'allow'}
        args = tool.get('args', {})
        file = args.get('Path') or args.get('TargetFile', '')
        if isinstance(file, str) and file.startswith('"'):
            file = json.loads(file)
    else:
        args = payload.get('tool_input', {})
        file = args.get('file_path') or args.get('notebook_path', '')
    if not file:
        return {'decision': 'allow'} if agy else {}
    path = file.replace('\\', '/')
    workspaces = payload.get('workspacePaths', []) if agy else []
    repo = pathlib.Path(workspaces[0] if workspaces else os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())).resolve()
    if pathlib.Path(path).is_absolute():
        try:
            path = pathlib.Path(path).resolve().relative_to(repo).as_posix()
        except ValueError:
            # Broad suffix rules can still apply to explicitly edited external paths.
            path = path.lstrip('/')
    selected = bundle.select_documents(root, [path])
    references = list(selected['rules']) + selected['precedent'] + selected['hints']
    hashes = {ref: hashlib.sha256((root / ref.lstrip('/')).read_bytes()).hexdigest() for ref in references}
    signature = hashlib.sha256(json.dumps({'selected': selected, 'hashes': hashes}, sort_keys=True).encode()).hexdigest()
    lines = [f'{rid}: {summary}' for rid, summary in selected['summary'].items()]
    for category in ('precedent', 'hints'):
        lines += [f'{category}: {ref}' for ref in selected[category]]
    context = f'Guidance for {path}. Open applicable rule files and exceptions.\n' + '\n'.join(lines)
    # Without a session, deliver without caching instead of silently skipping lookup.
    if sid:
        namespace = ('agy-' if agy else 'claude-') + hashlib.sha256(str(sid).encode()).hexdigest()
        state = state_root / namespace
        state.mkdir(parents=True, exist_ok=True)
        receipt = state / f'{signature}.json'
        if receipt.exists():
            return {'decision': 'allow'} if agy else {}
        data = {'schema_version': 1, 'status': 'selected', 'path': path,
                'selection': selected, 'document_hashes': hashes, 'opened_documents': None}
        # Successful selection and readable dependencies precede a receipt; replace atomically.
        with tempfile.NamedTemporaryFile(mode='w', dir=state, delete=False, encoding='utf-8') as stream:
            json.dump(data, stream, indent=2)
            temporary = pathlib.Path(stream.name)
        temporary.replace(receipt)
    if agy:
        return {'decision': 'deny', 'reason': context + '\nRead this guidance, then retry the edit.'}
    return {'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'additionalContext': context}}


def main():
    agy = '--agy' in sys.argv
    try:
        payload = json.load(sys.stdin)
        root = pathlib.Path(__file__).resolve().parents[2]
        state = pathlib.Path(tempfile.gettempdir()) / 'golden-path-harness-lookup'
        print(json.dumps(deliver(payload, root, state, agy)))
        return 0
    except (ValueError, OSError, TypeError) as error:
        message = f'Harness lookup failed; edit requires successful retrieval: {error}'
        if agy:
            print(json.dumps({'decision': 'deny', 'reason': message}))
            return 0
        print(message, file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
