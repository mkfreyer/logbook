"""Check exact restoration against the actual P4/P5 source files, plus GLB and renders."""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

import bpy
import numpy as np

p = argparse.ArgumentParser()
p.add_argument('--asset', type=Path, required=True)
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
root = a.asset.resolve()
meta = json.loads((root / 'combinaison.json').read_text())
deltoids = {'deltoid.right', 'deltoid.left'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def field(collection, key, size, dtype=np.float32):
    arr = np.empty(len(collection) * size, dtype=dtype)
    collection.foreach_get(key, arr)
    return arr


def raw_fingerprint(ob):
    """Ignore datablock names, retain all coordinate/topology/shape-key/deform data."""
    mesh = ob.data
    h = hashlib.sha256()
    for arr in [field(mesh.vertices, 'co', 3), field(mesh.edges, 'vertices', 2, np.int32),
                field(mesh.loops, 'vertex_index', 1, np.int32),
                field(mesh.polygons, 'loop_start', 1, np.int32),
                field(mesh.polygons, 'loop_total', 1, np.int32),
                field(mesh.polygons, 'use_smooth', 1, np.bool_),
                field(mesh.polygons, 'material_index', 1, np.int32),
                np.array(ob.matrix_world, dtype='<f8')]:
        h.update(arr.tobytes())
    if mesh.shape_keys:
        for key in mesh.shape_keys.key_blocks:
            h.update(json.dumps([key.name, key.value, key.relative_key.name, key.interpolation, key.mute]).encode())
            h.update(field(key.data, 'co', 3).tobytes())
    h.update(json.dumps([g.name for g in ob.vertex_groups]).encode())
    h.update(json.dumps([[(g.group, g.weight) for g in v.groups] for v in mesh.vertices]).encode())
    for uv in mesh.uv_layers:
        h.update(uv.name.encode())
        h.update(field(uv.data, 'uv', 2).tobytes())
    return h.hexdigest()


def snapshot(path, scene_name):
    bpy.ops.wm.open_mainfile(filepath=str(path), use_scripts=False)
    scene = bpy.data.scenes[scene_name]
    bpy.context.window.scene = scene
    scene.view_layers[0].update()
    graph = bpy.context.evaluated_depsgraph_get()
    out = {}
    for ob in scene.objects:
        if ob.type != 'MESH':
            continue
        ev = ob.evaluated_get(graph)
        mesh = ev.to_mesh()
        v = np.array([ob.matrix_world @ x.co for x in mesh.vertices])
        f = np.array([q.vertices[:] for q in mesh.polygons], dtype=np.int32)
        normal_sha = hashlib.sha256(field(mesh.corner_normals, 'vector', 3).tobytes()).hexdigest()
        out[ob['asset_id']] = {'v': v, 'f': f, 'raw': raw_fingerprint(ob), 'normals': normal_sha}
        ev.to_mesh_clear()
    return out


def equal(a, b, key, raw=False):
    assert np.array_equal(a['v'], b['v']), ('coordinates', key)
    assert np.array_equal(a['f'], b['f']), ('topology', key)
    assert a['normals'] == b['normals'], ('normals', key)
    if raw:
        assert a['raw'] == b['raw'], ('raw mesh/shape keys/groups', key)


p4file = root.parent / 'ecorche-beatriz-passe4/ecorche-passe4.blend'
p5file = root.parent / 'ecorche-beatriz-passe5/ecorche-passe5.blend'
p6file = root.parent / 'ecorche-beatriz-passe6/ecorche-passe6.blend'
assert sha(p4file) == meta['p4_blend_sha256']
assert sha(p5file) == meta['p5_blend_sha256']
assert sha(p6file) == meta['p6_archive_sha256']
p4 = snapshot(p4file, '10_PASSE4_NEUTRE')
p5 = snapshot(p5file, '12_PASSE5_NEUTRE')
p6 = snapshot(p6file, '15_PASSE6_NEUTRE')
after = snapshot(root / 'ecorche-p4-p5.blend', meta['scene'])
assert after.keys() == p5.keys() == p6.keys()
for key in deltoids:
    equal(p4[key], after[key], key, raw=True)
for key in set(after) - deltoids:
    equal(p5[key], after[key], key, raw=True)
    equal(p6[key], after[key], key)


def volume(record):
    v, f = record['v'], record['f']
    return float(np.einsum('ij,ij->i', v[f[:, 0]], np.cross(v[f[:, 1]], v[f[:, 2]])).sum() / 6)


def signatures(v, f):
    q = np.rint(v[f] * 1e6).astype('<i4')
    order = np.lexsort((q[:, :, 2], q[:, :, 1], q[:, :, 0]), axis=1)
    q = np.ascontiguousarray(np.take_along_axis(q, order[:, :, None], axis=1).reshape(-1, 9))
    return np.sort(q.view(np.dtype([(f'c{i}', '<i4') for i in range(9)])).ravel())


# P5 replaced the head above 1.570m, but retained the P4 throat below that line.
neck = 'head_throat.neutral_surface'
throat = {}
for label, record in [('p4', p4[neck]), ('combination', after[neck])]:
    v, f = record['v'], record['f']
    throat[label] = signatures(v, f[np.max(v[f, 2], axis=1) < 1.570 - 1e-6])
assert len(throat['p4']) > 1000 and np.array_equal(throat['p4'], throat['combination'])

scene = bpy.data.scenes[meta['scene']]
assert len([o for o in scene.objects if o.type == 'LIGHT']) == 5
for ob in scene.objects:
    if ob.type == 'MESH':
        assert ob.material_slots[0].material == bpy.data.materials['PASSE3_MAT_NEUTRE']
mat = bpy.data.materials['PASSE3_MAT_NEUTRE'].node_tree.nodes.get('Principled BSDF')
assert mat.inputs['Metallic'].default_value == 0
assert abs(mat.inputs['Roughness'].default_value - .85) < 1e-6

# Check the actual serialized GLB rather than relying on exporter counters.
raw = (root / 'ecorche-p4-p5.glb').read_bytes()
size = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20 + size])
binary = raw[28 + size:]


def accessor(index):
    ac = doc['accessors'][index]
    view = doc['bufferViews'][ac['bufferView']]
    width = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[ac['type']]
    dtype = np.dtype({5126: '<f4', 5125: '<u4', 5123: '<u2'}[ac['componentType']])
    return np.ndarray((ac['count'], width), dtype=dtype, buffer=binary,
        offset=view.get('byteOffset', 0) + ac.get('byteOffset', 0),
        strides=(view.get('byteStride', width * dtype.itemsize), dtype.itemsize)).copy()


assert len(doc['nodes']) == len(after) and len(doc['materials']) == 1
triangles = vertices = 0
omissions = []
for node in doc['nodes']:
    key = node['name']
    assert key in after and not any(k in node for k in ['matrix', 'translation', 'rotation', 'scale'])
    primitive = doc['meshes'][node['mesh']]['primitives'][0]
    v = accessor(primitive['attributes']['POSITION']).astype(float)[:, [0, 2, 1]]
    v[:, 1] *= -1
    f = accessor(primitive['indices']).reshape(-1, 3)
    expected = signatures(after[key]['v'], after[key]['f'])
    actual = signatures(v, f)
    assert not len(np.setdiff1d(actual, expected)), key
    if not np.array_equal(expected, actual):
        s0, c0 = np.unique(expected, return_counts=True)
        s1, c1 = np.unique(actual, return_counts=True)
        remaining = np.zeros(len(s0), int)
        remaining[np.searchsorted(s0, s1)] = c1
        difference = c0 - remaining
        assert (difference >= 0).all()
        for i in np.flatnonzero(difference):
            assert remaining[i] > 0
            omissions.append({'asset_id': key, 'removed_copies': int(difference[i]), 'copies_remaining': int(remaining[i])})
    triangles += len(f)
    vertices += len(v)
assert 'CC BY 4.0' in doc['asset']['copyright'] and 'CC0' in doc['asset']['copyright']
test_scene = bpy.data.scenes.new('VERIFY_COMBINAISON_IMPORT')
bpy.context.window.scene = test_scene
bpy.ops.import_scene.gltf(filepath=str(root / 'ecorche-p4-p5.glb'), merge_vertices=False)
meshes = [o for o in test_scene.objects if o.type == 'MESH']
assert len(meshes) == len(after)
assert sum(sum(len(f.vertices) - 2 for f in o.data.polygons) for o in meshes) == triangles
frames = json.loads((root / 'renders/metadata.json').read_text())
assert len(frames['frames']) == 10
assert frames['final_blend_sha256'] == sha(root / 'ecorche-p4-p5.blend')
assert all(sha(root / 'renders' / f['file']) == f['sha256'] for f in frames['frames'])
report = {
    'new_master_sha256': sha(root / 'ecorche-p4-p5.blend'),
    'source_p4_sha256': sha(p4file), 'source_p5_sha256': sha(p5file), 'archive_p6_sha256': sha(p6file),
    'deltoids_exact_p4': {key: {'raw_geometry_topology_shape_keys_groups_identical': True,
        'evaluated_coordinates_topology_normals_identical': True, 'max_coordinate_difference_m': 0,
        'raw_mesh_fingerprint': after[key]['raw'], 'triangles': len(after[key]['f']),
        'volume_p4_m3': volume(p4[key]), 'volume_combination_m3': volume(after[key]),
        'volume_difference_m3': volume(after[key]) - volume(p4[key])} for key in sorted(deltoids)},
    'unchanged_other_objects_exact_p5': len(after) - 2,
    'unchanged_other_objects_match_p6_evaluated_geometry': True,
    'head_eyes_and_entire_neck_exact_p5': True,
    'throat_below_1_570m_exact_p4': True, 'throat_compared_triangles': len(throat['p4']),
    'objects': len(after), 'master_triangles': sum(len(r['f']) for r in after.values()),
    'glb_sha256': sha(root / 'ecorche-p4-p5.glb'), 'glb_bytes': len(raw),
    'glb_triangles': triangles, 'glb_vertices': vertices,
    'glb_surface_match_at_micron_quantization': True, 'glb_duplicate_faces_removed': omissions,
    'glb_reimport_verified': True, 'render_files_hash_verified': 10,
    'neutral_matte_material_verified': True, 'new_sculpting': False, 'new_segmentation': False,
    'verifier_sha256': sha(Path(__file__)),
    'scope': 'Exact asset assembly and export checks. Existing P4 reliefs and contacts intentionally restored, not corrected. No medical certification or mobile FPS test.',
}
(root / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print('COMBINAISON_VERIFIED', json.dumps(report), flush=True)
