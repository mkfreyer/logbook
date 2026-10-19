#!/usr/bin/env python3
"""Download and verify the exact official Blender Studio bundle used for M4A."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import urllib.request
import zipfile

URL = 'https://download.blender.org/demo/asset-bundles/human-base-meshes/human-base-meshes-bundle-v1.4.1.zip'
SIZE = 50643039
SHA256 = '811f43accbb31a88266d932f8f5563b2d13586fca0ba2693aad1f5fe582b3515'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, required=True)
    args = parser.parse_args()
    args.destination.mkdir(parents=True, exist_ok=True)
    archive = args.destination / URL.rsplit('/', 1)[1]
    if not archive.exists():
        temporary = archive.with_suffix('.zip.part')
        with urllib.request.urlopen(URL, timeout=60) as source, temporary.open('xb') as output:
            while block := source.read(1024 * 1024):
                output.write(block)
        if temporary.stat().st_size != SIZE or digest(temporary) != SHA256:
            raise ValueError('Downloaded bundle size/SHA-256 mismatch; partial file retained')
        temporary.rename(archive)
    if archive.stat().st_size != SIZE or digest(archive) != SHA256:
        raise ValueError('Bundle size/SHA-256 mismatch; existing file left untouched')
    with zipfile.ZipFile(archive) as bundle:
        if bundle.testzip() is not None:
            raise ValueError('Bundle CRC verification failed')
        entries = bundle.infolist()
        for entry in entries:
            name = PurePosixPath(entry.filename)
            if name.is_absolute() or '..' in name.parts or chr(92) in entry.filename:
                raise ValueError(f'Unsafe archive member: {entry.filename}')
        target = args.destination / 'extracted'
        if not target.exists():
            bundle.extractall(target)
    print(json.dumps({'url': URL, 'bytes': SIZE, 'sha256': SHA256,
                      'crc': 'all entries verified', 'archive': str(archive)}, indent=2))


def digest(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


if __name__ == '__main__':
    main()
