#!/usr/bin/env python3
"""Fetch pinned inspection inputs through the normal proxy/CA; never run source code.

Use --verify-only to check existing bytes offline. Source licences are independent
of Logbook code. The Z-Anatomy archive is an atlas with mixed third-party notices;
this downloader does not approve commercial use of the complete atlas.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile
from urllib.parse import urlsplit


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', type=Path, default=Path(__file__).resolve().parents[2] / 'docs/m4a/ecorche/sources.json')
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--verify-only', action='store_true')
    a = p.parse_args()
    for r in json.loads(a.manifest.read_text()):
        name = Path(r['local_path'])
        url = urlsplit(r['url'])
        assert not name.is_absolute() and '..' not in name.parts
        assert url.scheme == 'https' and url.hostname in {'raw.githubusercontent.com', 'dbarchive.biosciencedbc.jp'}
        dest = a.output_dir / name
        if not dest.exists() and not a.verify_only:
            dest.parent.mkdir(parents=True, exist_ok=True)
            partial = dest.with_name(dest.name + '.part')
            assert not partial.is_symlink()
            subprocess.run(['curl', '--fail', '--location', '--silent', '--show-error',
                            '--retry', '3', '--connect-timeout', '20', '--max-time', '600',
                            '--continue-at', '-', '--output', str(partial), r['url']], check=True)
            assert partial.stat().st_size == r['bytes']
            assert hashlib.sha256(partial.read_bytes()).hexdigest() == r['sha256']
            partial.replace(dest)
        assert dest.stat().st_size == r['bytes'], str(dest)
        assert hashlib.sha256(dest.read_bytes()).hexdigest() == r['sha256'], str(dest)
        print('Verified', name, r['bytes'], flush=True)
    if a.verify_only:
        return
    # Only the actual .blend and audited OBJ inputs are required. No atlas add-ons.
    archive = a.output_dir / 'Z-Anatomy--Models-of-human-anatomy/Z-Anatomy.zip'
    with zipfile.ZipFile(archive) as z:
        data = z.read('Z-Anatomy/Startup.blend')  # read() verifies its CRC.
        dest = archive.parent / 'extracted/Z-Anatomy/Startup.blend'
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            assert dest.read_bytes() == data
        else:
            dest.write_bytes(data)
    selection = json.loads((Path(__file__).resolve().parents[2] / 'docs/m4a/bodyparts3d/selection-candidate.json').read_text())
    ids = set(selection['audit_all_muscle_element_ids']) | {'FJ2810'}
    directory = a.output_dir / 'bodyparts3d/obj'
    directory.mkdir(exist_ok=True)
    with zipfile.ZipFile(a.output_dir / 'bodyparts3d/isa_BP3D_4.0_obj_99.zip') as z:
        found = set()
        for item in z.infolist():
            filename = Path(item.filename)
            if filename.suffix == '.obj' and filename.stem in ids:
                dest = directory / filename.name
                data = z.read(item)
                if dest.exists():
                    assert dest.read_bytes() == data
                else:
                    dest.write_bytes(data)
                found.add(filename.stem)
        assert found == ids


if __name__ == '__main__':
    main()
