#!/usr/bin/env python3
"""Verify/restore the selected M4A research scenes, never overwrite an existing directory."""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile
import tempfile


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for data in iter(lambda: f.read(1024 * 1024), b''):
            h.update(data)
    return h.hexdigest()


def verify(root, files):
    for r in files:
        path = root / r['path']
        if path.is_symlink() or path.stat().st_size != r['bytes'] or digest(path) != r['sha256']:
            raise ValueError('Checkpoint mismatch: ' + str(path))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--checkpoint', type=Path, default=Path(__file__).resolve().parents[2] / 'docs/m4a/ecorche/checkpoint')
    p.add_argument('--destination', type=Path, required=True)
    p.add_argument('--verify-only', action='store_true')
    a = p.parse_args()
    manifest = json.loads((a.checkpoint / 'manifest.json').read_text())
    expected = {}
    for r in manifest['files']:
        path = Path(r['path'])
        if path.is_absolute() or '..' in path.parts or str(path) != r['path']:
            raise ValueError('Unsafe member name')
        if r['path'] in expected:
            raise ValueError('Duplicate manifest member')
        expected[r['path']] = r
    if a.verify_only:
        verify(a.destination, manifest['files'])
    else:
        if a.destination.exists():
            raise ValueError('Destination already exists; use --verify-only or a new path')
        record = manifest['archive']
        if Path(record['file']).name != record['file']:
            raise ValueError('Unsafe archive filename')
        archive = a.checkpoint / record['file']
        if archive.stat().st_size != record['bytes'] or digest(archive) != record['sha256']:
            raise ValueError('Archive checksum mismatch')
        a.destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='m4a-ecorche-restore-', dir=a.destination.parent) as temp:
            root = Path(temp) / 'selected-scenes'
            root.mkdir()
            with tarfile.open(archive, 'r:xz') as t:
                members = t.getmembers()
                if len(members) != len(expected) or {m.name for m in members} != set(expected):
                    raise ValueError('Unexpected archive member set')
                for member in members:
                    if not member.isfile() or member.size != expected[member.name]['bytes']:
                        raise ValueError('Non-regular or wrong-sized member')
                    target = root / member.name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with t.extractfile(member) as source, target.open('xb') as output:
                        for data in iter(lambda: source.read(1024 * 1024), b''):
                            output.write(data)
            verify(root, manifest['files'])
            root.rename(a.destination)
    print(json.dumps({'operation': 'verify' if a.verify_only else 'restore', 'files': len(expected),
                      'bytes': sum(r['bytes'] for r in manifest['files']), 'directory': str(a.destination)}, indent=2))


if __name__ == '__main__':
    main()
