"""Reuse 990201f's clipping builder on its exact preserved surface."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import bpy

BASE_COMMIT = '990201f214c91272a5274a53c28e049670128064'
BASE_SHA = '34af46851680f8edce0d55b138603caa6df0d2eb0253d587499d3be866d70c91'


def main():
    path = Path(__file__).with_name('frontieres_deltoides_build.py')
    spec = importlib.util.spec_from_file_location('local_surface_builder', path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    helper.BASE_SHA, helper.BASE_COMMIT = BASE_SHA, BASE_COMMIT
    helper.main()
    if '--snapshot' in sys.argv:
        return
    root = Path(sys.argv[sys.argv.index('--output') + 1]).resolve()
    meta = json.loads((root / 'zones.json').read_text())
    bpy.ops.wm.open_mainfile(filepath=str(root / meta['master']), use_scripts=False)
    scene = bpy.data.scenes[meta['scene']]
    bpy.context.window.scene = scene
    source_scene = meta['scene']
    scene.name = '22_ANATOMIE_DELTOIDES_P4'
    scene['zone_boundaries_status'] = 'Proposed clavicular/acromial/scapular fan boundaries; visual validation pending'
    for ob in scene.objects:
        if ob.type == 'MESH' and ob.get('asset_id') in ['deltoid.left', 'deltoid.right']:
            ob['segmentation_method'] = 'Anatomical proximal fan; broad lateral dome, anterior wrap and posterior scapular region'
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(root / meta['master']), compress=True)
    meta.update({
        'scene': scene.name, 'source_scene': source_scene,
        'geometry_reference_commit': '0ab3d838c728a88f2d325edff7a6884400c9ed78',
        'master_sha256': hashlib.sha256((root / meta['master']).read_bytes()).hexdigest(),
        'builder_helper_sha256': meta['builder_sha256'],
        'builder_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'shape_keys': 'No new shape keys; 990201f already fixes the deltoid pose at evaluated P4.',
    })
    (root / 'zones.json').write_text(json.dumps(meta, indent=2) + '\n')
    print('ANATOMICAL_MASTER', meta['master_sha256'], flush=True)


if __name__ == '__main__':
    main()
