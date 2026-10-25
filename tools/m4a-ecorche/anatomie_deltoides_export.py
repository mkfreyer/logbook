"""Export anatomical fan zones using the validated six-ID GLB pipeline."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path


def load(name):
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(name.replace('.', '_'), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    helper = load('frontieres_deltoides_export.py')
    helper.main()
    codec = load('zones_deltoides_export.py')
    root = Path(sys.argv[sys.argv.index('--asset') + 1]).resolve()
    meta = json.loads((root / 'zones.json').read_text())
    paths = [root / n for n in ['ecorche-p4-p5-zones.glb', 'ecorche-p4-p5-zones-controle.glb']]
    for path in paths:
        doc, binary = codec.read_glb(path)
        doc['asset']['extras'].update({
            'modifications': 'Revision of anterior/lateral/posterior surface boundaries into a proximal '
                             'clavicular/acromial/scapular fan. Local triangle clipping only; no sculpting.',
            'boundary_method': meta['method'],
            'anatomical_boundary_validation': 'Proposed approximate surface landmarks, awaiting visual validation.',
            'anatomical_frame_right': meta['preparation']['axis_frame_right'],
        })
        codec.write_glb(path, doc, binary)
    report = json.loads((root / 'export.json').read_text())
    report['files'] = [{'name': p.name, 'bytes': p.stat().st_size,
                       'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]
    report['local_clipping_exporter_sha256'] = report['exporter_sha256']
    report['exporter_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (root / 'export.json').write_text(json.dumps(report, indent=2) + '\n')
    print('ANATOMICAL_EXPORT', json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
