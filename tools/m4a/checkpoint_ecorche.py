"""Save selected geometry only, purge unused atlas data, preserve numerical mesh digest."""
import argparse, hashlib, json, sys
from pathlib import Path
import bpy
import numpy as np

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--prepared', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
a.output.mkdir(parents=True, exist_ok=True)
source = a.prepared / 'muscles-only.blend'
original_sha = hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
inventory = json.loads((a.prepared / 'inventory.json').read_text())
assert set(o.name for o in bpy.context.scene.objects) == set(r['object'] for r in inventory['objects'])

def geometry_digest():
    h = hashlib.sha256()
    for ob in sorted(bpy.context.scene.objects, key=lambda o: o.name):
        assert ob.type == 'MESH'
        h.update(ob.name.encode() + b'\0')
        co = np.empty(len(ob.data.vertices) * 3, dtype='<f4')
        ob.data.vertices.foreach_get('co', co)
        ix = np.empty(len(ob.data.loops), dtype='<i4')
        ob.data.loops.foreach_get('vertex_index', ix)
        lengths = np.empty(len(ob.data.polygons), dtype='<i4')
        ob.data.polygons.foreach_get('loop_total', lengths)
        for array in (co, ix, lengths):
            h.update(array.tobytes())
    return h.hexdigest()

before = geometry_digest()
# Old appended/imported atlas mesh datablocks are not part of this checkpoint.
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)
for text in list(bpy.data.texts):
    bpy.data.texts.remove(text)
for image in list(bpy.data.images):
    bpy.data.images.remove(image)
bpy.data.orphans_purge(do_recursive=True)
assert geometry_digest() == before
assert len(bpy.data.meshes) == len(inventory['objects'])
target = a.output / 'muscles-only.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(target), compress=False)
bpy.ops.wm.open_mainfile(filepath=str(target), use_scripts=False)
assert geometry_digest() == before
(a.output / 'checkpoint-origin.json').write_text(json.dumps({
    'original_render_preparation_sha256': original_sha,
    'checkpoint_blend_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
    'selected_mesh_geometry_sha256_before_and_after_reload': before,
    'difference': 'Unused source mesh/material/image/text datablocks purged; selected vertex positions, loop indices, polygon lengths, names and audit properties unchanged.',
    'unused_atlas_mesh_datablocks_retained': 0}, indent=2) + '\n')
for name in ('inventory.json', 'geometry-check.json'):
    (a.output / name).write_bytes((a.prepared / name).read_bytes())
print('CHECKPOINT', inventory['candidate'], len(bpy.data.meshes), before, flush=True)
