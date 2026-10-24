"""Restore the exact P4 deltoid objects on the otherwise unchanged P5 body.

No sculpting, remeshing, smoothing, displacement or new segmentation.
The P6 master is retained as an archive of the previous scenes.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy

P4_SHA = '15444ab13acb4232ed9d366e39b333c305b9c1be533e71d2b5eee90b9e58ff37'
P5_SHA = '926cadf61c4608c096cbf84e0c50ff0785eb7c5568d613206dfe57d695e4a54d'
P6_SHA = '1988d7452a028817a90e79013a2fa804afdb366d07421e5782415f660eee5758'
DELTOIDS = {'deltoid.left', 'deltoid.right'}
SCENE = '16_COMBINAISON_P4_P5'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


p = argparse.ArgumentParser()
p.add_argument('--archive', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
root = a.output.resolve()
root.mkdir(parents=True, exist_ok=True)
p4 = a.archive.parent.parent / 'ecorche-beatriz-passe4/ecorche-passe4.blend'
p5 = a.archive.parent.parent / 'ecorche-beatriz-passe5/ecorche-passe5.blend'
assert sha(p4) == P4_SHA and sha(p5) == P5_SHA and sha(a.archive) == P6_SHA
prior = json.loads((p5.parent / 'passe5.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(a.archive.resolve()), use_scripts=False)
sources = {
    'p4': {o['asset_id']: o for o in bpy.data.scenes['10_PASSE4_NEUTRE'].objects if o.type == 'MESH'},
    'p5': {o['asset_id']: o for o in bpy.data.scenes['12_PASSE5_NEUTRE'].objects if o.type == 'MESH'},
}
scene = bpy.data.scenes.new(SCENE)
for key, source in sorted(sources['p5'].items()):
    original = sources['p4'][key] if key in DELTOIDS else source
    clone = original.copy()
    clone.data = original.data.copy()
    clone.name = 'P4P5__' + key
    scene.collection.objects.link(clone)
    # Object.copy and Mesh.copy preserve original transforms, shape-key values,
    # vertex order, edges, polygon order, smoothing and existing authoring data.
    # No new groups, masks, modifiers or material tricks are introduced.

meta = {
    'baseline_commit': 'cc7af9aa1330eb37d062c1f402f61fc4bf7472ca',
    'p4_blend_sha256': P4_SHA,
    'p5_blend_sha256': P5_SHA,
    'p6_archive_sha256': P6_SHA,
    'scene': SCENE,
    'restored_objects_exact_p4': sorted(DELTOIDS),
    'remaining_objects_exact_p5': len(sources['p5']) - 2,
    'source_asset': prior['source_asset'],
    'source_sha256': prior['source_sha256'],
    'head_source': prior['head_source'],
    'median_plane_x_m': prior['median_plane_x_m'],
    'objects': len(sources['p5']),
    'sculpting': False,
    'new_segmentation': False,
    'builder_sha256': sha(Path(__file__)),
    'method': 'Exact object and mesh copies: P4 deltoids, all other parts from P5; historical scenes untouched.',
}
(root / 'combinaison.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n')
bpy.data.texts.new('COMBINAISON_P4_P5.json').write(json.dumps(meta, ensure_ascii=False, indent=2))
bpy.context.window.scene = scene
bpy.ops.wm.save_as_mainfile(filepath=str(root / 'ecorche-p4-p5.blend'), compress=True)
print('COMBINAISON_BUILT', json.dumps(meta), flush=True)
