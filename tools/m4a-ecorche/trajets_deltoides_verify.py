"""Independently check protected parts, edited geometry, serialized GLB and matched renders."""
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
meta = json.loads((root / 'trajets.json').read_text())
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


baseline_file = root.parent / 'ecorche-beatriz-combinaison-p4-p5/ecorche-p4-p5.blend'
assert sha(baseline_file) == meta['baseline_blend_sha256']
baseline = snapshot(baseline_file, '16_COMBINAISON_P4_P5')
after = snapshot(root / 'ecorche-trajets-deltoides.blend', meta['scene'])
assert baseline.keys() == after.keys()
for key in set(after) - deltoids:
    equal(baseline[key], after[key], key, raw=True)
from mathutils.bvhtree import BVHTree
surface = np.load(root / 'surface.npz')
delta = surface['v'] - surface['source_v']
checks = {}
for key in sorted(deltoids):
    base, result = baseline[key], after[key]
    v, f = result['v'], result['f']
    assert np.array_equal(base['f'], f)
    expected_delta = delta.copy()
    if key.endswith('.left'):
        expected_delta[:, 0] *= -1
    intended_error = float(np.abs(v - base['v'] - expected_delta).max())
    assert intended_error < 1e-7, (key, intended_error)
    untouched = np.linalg.norm(expected_delta, axis=1) < 1e-10
    outside_error = float(np.abs(v[untouched]-base['v'][untouched]).max())
    assert outside_error < 1e-9  # Float cancellation in the added relative shape key.
    edges = np.sort(np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]), axis=1)
    ue, counts = np.unique(edges, axis=0, return_counts=True)
    assert (counts == 2).all()
    area = np.cross(v[f[:,1]] - v[f[:,0]], v[f[:,2]] - v[f[:,0]])
    oldarea = np.cross(base['v'][f[:,1]] - base['v'][f[:,0]], base['v'][f[:,2]] - base['v'][f[:,0]])
    assert (np.einsum('ij,ij->i', area, oldarea) > 0).all()
    tree = BVHTree.FromPolygons(v.tolist(), f.tolist(), all_triangles=True)
    contacts = [(i,j) for i,j in tree.overlap(tree) if i<j and not np.isin(f[i], f[j]).any()]
    assert not contacts
    vol = lambda q: float(np.einsum('ij,ij->i', q[f[:,0]], np.cross(q[f[:,1]], q[f[:,2]])).sum()/6)
    ratio = vol(v) / vol(base['v'])
    assert .99 < ratio < 1.001
    bbox_error = float(np.abs(np.ptp(v,axis=0)-np.ptp(base['v'],axis=0)).max())
    assert bbox_error < 1e-6
    checks[key] = {'triangles':len(f),'vertices':len(v),'topology_identical':True,
        'vertices_outside_roi':int(untouched.sum()),'outside_roi_max_coordinate_difference_m':outside_error,
        'intended_coordinate_error_m':intended_error,
        'volume_ratio':ratio,'bbox_max_difference_m':bbox_error,'closed_two_manifold':True,
        'euler_characteristic':len(v)-len(ue)+len(f),'self_contacts':len(contacts),
        'min_triangle_area_m2':float(np.linalg.norm(area,axis=1).min()/2)}
r = after['deltoid.right']['v'].copy()
r[:,0] = 2*meta['median_plane_x_m'] - r[:,0]
reflection_error = float(np.abs(r-after['deltoid.left']['v']).max())
assert reflection_error < 1e-7

def frontal_width(v, f, z):
    points=[]
    for k,l in [(0,1),(1,2),(2,0)]:
        A,B=v[f[:,k]],v[f[:,l]]
        keep=(A[:,2]-z)*(B[:,2]-z)<0
        A,B=A[keep],B[keep]
        t=(z-A[:,2])/(B[:,2]-A[:,2])
        points.append(A+t[:,None]*(B-A))
    return 2*(meta['median_plane_x_m']-float(np.concatenate(points)[:,0].min()))

widths=[]
for z in np.linspace(1.33,1.485,41):
    b,n=baseline['deltoid.right'],after['deltoid.right']
    widths.append({'z_m':float(z),'before_m':frontal_width(b['v'],b['f'],z),'after_m':frontal_width(n['v'],n['f'],z)})
max_frontal_increase=max(row['after_m']-row['before_m']for row in widths)
assert max_frontal_increase < .001

def signatures(v, f):
    q = np.rint(v[f] * 1e6).astype('<i4')
    order = np.lexsort((q[:,:,2],q[:,:,1],q[:,:,0]),axis=1)
    q = np.ascontiguousarray(np.take_along_axis(q,order[:,:,None],axis=1).reshape(-1,9))
    return np.sort(q.view(np.dtype([(f'c{i}','<i4')for i in range(9)])).ravel())
scene = bpy.data.scenes[meta['scene']]
prior = bpy.data.scenes[meta['before_scene']]
assert {o.name for o in scene.objects if o.type in ['LIGHT','CAMERA']} == {o.name for o in prior.objects if o.type in ['LIGHT','CAMERA']}
assert len([o for o in scene.objects if o.type=='LIGHT'])==5
for ob in scene.objects:
    if ob.type=='MESH':
        assert ob.material_slots[0].material == bpy.data.materials['PASSE3_MAT_NEUTRE']
# Check the actual serialized GLB rather than relying on exporter counters.
raw = (root / 'ecorche-trajets-deltoides.glb').read_bytes()
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
bpy.ops.import_scene.gltf(filepath=str(root / 'ecorche-trajets-deltoides.glb'), merge_vertices=False)
meshes = [o for o in test_scene.objects if o.type == 'MESH']
assert len(meshes) == len(after)
assert sum(sum(len(f.vertices) - 2 for f in o.data.polygons) for o in meshes) == triangles
frames = json.loads((root / 'renders/metadata.json').read_text())
assert len(frames['frames']) == 20
assert frames['final_blend_sha256'] == sha(root / 'ecorche-trajets-deltoides.blend')
assert all(sha(root / 'renders' / f['file']) == f['sha256'] for f in frames['frames'])
for view in ['reference','epaule-gauche','epaules-face','epaules-dos','epaule-profil','epaule-arriere','face','profil','trois-quarts','dos']:
    pair = [row for row in frames['frames'] if row['file'] in ['avant-'+view+'.png','apres-'+view+'.png']]
    assert len(pair)==2 and pair[0]['camera_matrix_world']==pair[1]['camera_matrix_world']
    assert pair[0]['ortho_scale']==pair[1]['ortho_scale'] and pair[0]['size']==pair[1]['size']
report = {'new_master_sha256':sha(root/'ecorche-trajets-deltoides.blend'),
    'baseline_sha256':sha(baseline_file),'protected_other_objects_exact':len(after)-2,
    'head_throat_pectorals_arms_back_legs_unchanged':True,'surface_checks':checks,
    'shoulder_symmetry_max_error_m':reflection_error,
    'frontal_width_profiles':widths,'max_bilateral_frontal_width_increase_m':max_frontal_increase,
    'objects':len(after),'master_triangles':sum(len(r['f'])for r in after.values()),
    'glb_sha256':sha(root/'ecorche-trajets-deltoides.glb'),'glb_triangles':triangles,
    'glb_vertices':vertices,'glb_duplicate_faces_removed':omissions,
    'glb_surface_match_at_micron_quantization':True,'glb_reimport_verified':True,
    'render_files_hash_verified':20,'paired_cameras_and_lights_identical':True,
    'new_segmentation':False,'verifier_sha256':sha(Path(__file__)),
    'scope':'Geometric integrity and preservation checks; not a guarantee of aesthetic or medical validity. No mobile performance test.'}
(root/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('TRAJETS_VERIFIED',json.dumps(report),flush=True)
