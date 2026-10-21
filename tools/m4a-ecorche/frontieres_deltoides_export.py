"""Reuse the GLB six-ID exporter, documenting local topology and provenance."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path


def main():
    source = Path(__file__).with_name('zones_deltoides_export.py')
    spec = importlib.util.spec_from_file_location('six_zones_export', source)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    # Same --asset command-line interface and six-material serialization.
    helper.main()
    root = Path(sys.argv[sys.argv.index('--asset') + 1]).resolve()
    meta = json.loads((root / 'zones.json').read_text())
    paths = [root / n for n in ['ecorche-p4-p5-zones.glb', 'ecorche-p4-p5-zones-controle.glb']]
    for path in paths:
        doc, binary = helper.read_glb(path)
        doc['asset']['copyright'] = (
            'Body: Ecorche - Anatomy study — Beatriz Gomez Santamaria — CC BY 4.0. '
            'Head/eyes: Dan Ulrich / Blender Studio Human Base Meshes v1.4.1 — CC0. '
            'Logbook adaptation: approved P4/P5 body, six deltoid surface regions; '
            'local barycentric triangle splitting for continuous material boundaries, '
            'original surface and vertices preserved, no sculpting.')
        doc['asset']['extras'].update({
            'geometry_reference_commit': meta['geometry_reference_commit'],
            'modifications': 'Continuous material boundaries across locally split source triangles; '
                             'new vertices barycentrically on source surface; no sculpting.',
            'topology_modified': True,
            'original_vertices_moved': 0,
            'normal_method': meta['normal_method'],
            'segmentation_status': 'Six continuous surface regions; visual validation pending.',
        })
        helper.write_glb(path, doc, binary)
    report = json.loads((root / 'export.json').read_text())
    report['files'] = [{'name': p.name, 'bytes': p.stat().st_size,
                       'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]
    report['helper_exporter_sha256'] = report['exporter_sha256']
    report['exporter_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (root / 'export.json').write_text(json.dumps(report, indent=2) + '\n')
    print('LOCAL_TOPOLOGY_EXPORT', json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
