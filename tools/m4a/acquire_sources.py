#!/usr/bin/env python3
"""Acquire the seven exact data inputs recorded by the M4A BodyParts3D audit.

Uses curl with the caller's normal proxy/CA configuration. Existing verified
files are reused. A changed upstream LATEST resource fails checksum validation;
it must never silently replace the audit's pinned input.
HTML pages are historical provenance observations, not pinned pipeline inputs:
their dynamic nonces can change without changing the data being audited.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from urllib.parse import urlsplit

DATA_FILES = (
    'isa_BP3D_4.0_obj_99.zip',
    'isa_parts_list_e.txt',
    'isa_element_parts.txt',
    'isa_inclusion_relation_list.txt',
    'partof_parts_list_e.txt',
    'partof_element_parts.txt',
    'partof_inclusion_relation_list.txt',
)


def verify(path, record):
    if not path.is_file():
        raise ValueError(f"Missing source: {path}")
    size = path.stat().st_size
    if size != record['bytes']:
        raise ValueError(f"{path}: {size} bytes, expected {record['bytes']}")
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    if digest.hexdigest() != record['sha256']:
        raise ValueError(f"{path}: SHA-256 mismatch; expected {record['sha256']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--provenance', type=Path, default=Path(__file__).resolve().parents[2] / 'docs/m4a/bodyparts3d/provenance.json')
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--verify-only', action='store_true', help='Read existing local files only; never access the network')
    args = parser.parse_args()
    provenance = json.loads(args.provenance.read_text(encoding='utf-8'))
    records = {record['file']: record for record in provenance['files']}
    missing = set(DATA_FILES) - records.keys()
    if missing:
        parser.error(f'Missing data provenance entries: {sorted(missing)}')
    if not args.verify_only:
        args.output_dir.mkdir(parents=True, exist_ok=True)
    for name in DATA_FILES:
        record = records[name]
        name = record['file']
        parsed = urlsplit(record['url'])
        if Path(name).name != name or name in ('.', '..'):
            parser.error(f'Unsafe source filename: {name!r}')
        if parsed.scheme != 'https' or parsed.netloc != 'dbarchive.biosciencedbc.jp':
            parser.error(f'Non-official source URL: {record["url"]}')
        target = args.output_dir / name
        if target.exists() or args.verify_only:
            try:
                verify(target, record)
            except ValueError as error:
                parser.exit(1, f'{error}\nExisting files are not overwritten. Check provenance before retrying.\n')
        else:
            partial = args.output_dir / (name + '.part')
            if partial.is_symlink():
                parser.error(f'Refusing symlink download target: {partial}')
            subprocess.run([
                'curl', '--fail', '--location', '--show-error', '--retry', '3',
                '--connect-timeout', '20', '--max-time', '300',
                '--continue-at', '-', '--output', str(partial), record['url'],
            ], check=True)
            try:
                verify(partial, record)
            except ValueError as error:
                parser.exit(1, f'{error}\nDownload retained as .part; no validated file was published.\n')
            partial.replace(target)
        print(f'Verified {name}: {record["bytes"]} bytes, SHA-256 {record["sha256"]}', flush=True)


if __name__ == '__main__':
    main()
