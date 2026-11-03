#!/usr/bin/env python3
"""Install checksum-pinned public check tools into an explicit external directory.

Network access is confined to installation. Verification never downloads tools.
PowerShell itself must already be installed. No global profiles or modules change.
"""
import argparse
import hashlib
import io
import json
import pathlib
import platform
import tarfile
import urllib.request
import zipfile


def install(out, cache=None):
    out = out.resolve()
    if out.is_relative_to(pathlib.Path(__file__).resolve().parents[3]):
        raise ValueError('install tools outside the source repository')
    lock = json.loads(pathlib.Path(__file__).with_name('tool-lock.json').read_text())
    target = platform.system() + '-' + platform.machine()
    assets = lock['platforms'].get(target)
    if not assets:
        raise ValueError(f'unsupported tool platform: {target}')
    out.mkdir(parents=True, exist_ok=True)
    def fetch(spec):
        name = spec['url'].rsplit('/', 1)[-1]
        cached = cache / name if cache else None
        if cached and cached.is_file():
            data = cached.read_bytes()
        else:
            data = urllib.request.urlopen(spec['url'], timeout=120).read()
        if hashlib.sha256(data).hexdigest() != spec['sha256']:
            raise ValueError(f'checksum mismatch for {name}')
        return data
    data = fetch(assets['gitleaks'])
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
        for name in ('gitleaks', 'LICENSE'):
            member = archive.getmember(name)
            if not member.isfile():
                raise ValueError('unexpected Gitleaks archive member')
            (out / name).write_bytes(archive.extractfile(member).read())
    (out / 'gitleaks').chmod(0o755)
    (out / 'bicep').write_bytes(fetch(assets['bicep']))
    (out / 'bicep').chmod(0o755)
    for name, spec in lock['modules'].items():
        # PowerShell Gallery download URLs end in a version rather than a filename.
        package = cache / f'{name}.{spec["version"]}.nupkg' if cache else None
        if package and package.is_file():
            data = package.read_bytes()
            if hashlib.sha256(data).hexdigest() != spec['sha256']:
                raise ValueError(f'checksum mismatch for {name}')
        else:
            data = fetch(spec)
        dest = out / 'modules' / name / spec['version']
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            for entry in archive.infolist():
                path = pathlib.PurePosixPath(entry.filename)
                if path.is_absolute() or '..' in path.parts or '\\' in entry.filename:
                    raise ValueError('unsafe module package member')
                if entry.is_dir():
                    continue
                file = dest / entry.filename
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(archive.read(entry))
    (out / 'tool-lock.json').write_text(json.dumps(lock, indent=2) + '\n')
    print(f'Installed pinned check tools in {out}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=pathlib.Path, required=True)
    parser.add_argument('--cache', type=pathlib.Path, help='Optional directory of already downloaded release files')
    args = parser.parse_args()
    try:
        install(args.out, args.cache)
    except Exception as error:
        parser.exit(2, f'tool installation failed: {error}\n')
