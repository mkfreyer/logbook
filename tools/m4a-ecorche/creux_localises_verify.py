"""Verify narrow bands, exact belly lock, original body, volume, silhouettes and GLB."""
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
meta = json.loads((root / 'creux.json').read_text())
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
assert sha(baseline_file)==meta['baseline_blend_sha256']
baseline=snapshot(baseline_file,'16_COMBINAISON_P4_P5')
after=snapshot(root/'ecorche-creux-localises.blend',meta['scene'])
witness=snapshot(root/'ecorche-creux-localises.blend',meta['before_scene'])
assert baseline.keys()==after.keys()
for key in baseline:equal(baseline[key],witness[key],key,raw=True)
for key in set(after)-deltoids:
    equal(baseline[key],after[key],key,raw=True)
from mathutils.bvhtree import BVHTree
surface=np.load(root/'surface.npz');allowed=surface['allowed'];belly=surface['belly'];checks={}

def hull_2d(points):
    pts=sorted(set(map(tuple,points.tolist())))
    def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lower=[]
    for pt in pts:
        while len(lower)>=2 and cross(lower[-2],lower[-1],pt)<=0:lower.pop()
        lower.append(pt)
    upper=[]
    for pt in reversed(pts):
        while len(upper)>=2 and cross(upper[-2],upper[-1],pt)<=0:upper.pop()
        upper.append(pt)
    return np.array(lower[:-1]+upper[:-1])

for key in sorted(deltoids):
    b,r=baseline[key],after[key];v,f=r['v'],r['f']
    assert np.array_equal(b['f'],f)
    assert np.array_equal(b['v'][~allowed],v[~allowed])
    assert np.array_equal(b['v'][belly],v[belly])
    assert np.array_equal(b['v'][surface['locked_support']],v[surface['locked_support']])
    expected=surface['v'].copy()
    if key.endswith('.left'):
        delta=surface['v']-surface['source_v'];delta[:,0]*=-1
        expected=b['v'].copy();expected[allowed]=(expected[allowed]+delta[allowed]).astype(np.float32)
    assert np.array_equal(expected,v)
    changed=np.linalg.norm(v-b['v'],axis=1)>0
    assert (np.minimum(surface['old_distance_m'],surface['new_distance_m'])[changed] < .003).all()
    points=surface['curve_points_3d'].copy()
    if key.endswith('.left'):points[:,0]=2*meta['median_plane_x_m']-points[:,0]
    nearest=np.sqrt(((b['v'][changed,None,:]-points[None,:,:])**2).sum(2)).min(1)
    assert nearest.max()<=.0030001
    vol=lambda q:float(np.einsum('ij,ij->i',q[f[:,0]],np.cross(q[f[:,1]],q[f[:,2]])).sum()/6)
    relative_error=abs(vol(v)/vol(b['v'])-1);assert relative_error<1e-8
    assert np.array_equal(np.ptp(v,axis=0),np.ptp(b['v'],axis=0))
    support_error={}
    for axes in [(0,2),(1,2)]:
        h=hull_2d(b['v'][:,axes]);e=np.roll(h,-1,axis=0)-h;n=np.c_[e[:,1],-e[:,0]];n/=np.linalg.norm(n,axis=1)[:,None]
        error=float(np.max(v[:,axes]@n.T-np.einsum('ij,ij->i',n,h)))
        assert error<5e-8
        support_error[str(axes)]=error
    tree=BVHTree.FromPolygons(v.tolist(),f.tolist(),all_triangles=True)
    contacts=[(i,j)for i,j in tree.overlap(tree)if i<j and not np.isin(f[i],f[j]).any()];assert not contacts
    cross=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]])
    assert (np.linalg.norm(cross,axis=1)>1e-10).all()
    edges=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1);ue,c=np.unique(edges,axis=0,return_counts=True);assert(c==2).all()
    checks[key]={'changed_vertices':int(changed.sum()),'locked_belly_vertices':int(belly.sum()),
        'belly_max_difference_m':0,'outside_bands_max_difference_m':0,
        'protected_belly_sha256':hashlib.sha256(v[belly].astype('<f4').tobytes()).hexdigest(),
        'max_distance_to_registered_curve_m':float(nearest.max()),'max_band_radius_m':.003,
        'relative_volume_error':relative_error,'volume_before_m3':vol(b['v']),'volume_after_m3':vol(v),
        'bbox_identical':True,'front_profile_support_error_m':support_error,
        'triangles':len(f),'topology_identical':True,'closed_two_manifold':True,
        'euler_characteristic':len(v)-len(ue)+len(f),'self_contacts':len(contacts)}
scene=bpy.data.scenes[meta['scene']];before=bpy.data.scenes[meta['before_scene']]
assert len([o for o in scene.objects if o.type=='LIGHT'])==5
assert {o.name for o in scene.objects if o.type=='LIGHT'}=={o.name for o in before.objects if o.type=='LIGHT'}
for ob in scene.objects:
    if ob.type=='MESH':assert ob.material_slots[0].material==bpy.data.materials['PASSE3_MAT_NEUTRE']

def signatures(v,f):
    q=np.rint(v[f]*1e6).astype('<i4');order=np.lexsort((q[:,:,2],q[:,:,1],q[:,:,0]),axis=1)
    q=np.ascontiguousarray(np.take_along_axis(q,order[:,:,None],axis=1).reshape(-1,9))
    return np.sort(q.view(np.dtype([(f'c{i}','<i4')for i in range(9)])).ravel())
# Check the actual serialized GLB rather than relying on exporter counters.
raw = (root / 'ecorche-creux-localises.glb').read_bytes()
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
    if key in deltoids:
        exported=set(map(tuple,v.tolist()))
        assert set(map(tuple,baseline[key]['v'][~allowed].tolist())).issubset(exported)
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
bpy.ops.import_scene.gltf(filepath=str(root / 'ecorche-creux-localises.glb'), merge_vertices=False)
meshes = [o for o in test_scene.objects if o.type == 'MESH']
assert len(meshes) == len(after)
assert sum(sum(len(f.vertices) - 2 for f in o.data.polygons) for o in meshes) == triangles
frames = json.loads((root / 'renders/metadata.json').read_text())
assert len(frames['frames']) == 8
assert frames['final_blend_sha256'] == sha(root / 'ecorche-creux-localises.blend')
assert all(sha(root / 'renders' / f['file']) == f['sha256'] for f in frames['frames'])
for view in ['reference','epaule-gauche','face','profil']:
    pair=[row for row in frames['frames']if row['file']in ['avant-'+view+'.png','apres-'+view+'.png']]
    assert len(pair)==2 and pair[0]['camera_matrix']==pair[1]['camera_matrix']
    assert pair[0]['ortho_scale']==pair[1]['ortho_scale']and pair[0]['pixel_aspect_x']==pair[1]['pixel_aspect_x']and pair[0]['resolution']==pair[1]['resolution']
report={'baseline_sha256':sha(baseline_file),'new_master_sha256':sha(root/'ecorche-creux-localises.blend'),
    'protected_other_objects_exact':len(after)-2,'head_throat_pectorals_rest_exact':True,
    'surface_checks':checks,'new_segmentation':False,'objects':len(after),
    'master_triangles':sum(len(r['f'])for r in after.values()),'glb_triangles':triangles,
    'glb_vertices':vertices,'glb_sha256':sha(root/'ecorche-creux-localises.glb'),
    'glb_surface_match_at_micron_quantization':True,'glb_locked_coordinates_exact':True,
    'glb_reimport_verified':True,'glb_duplicate_faces_removed':omissions,
    'paired_cameras_and_lights_verified':True,'render_files_hash_verified':8,
    'verifier_sha256':sha(Path(__file__)),
    'scope':'Exact geometry preservation and narrow-band constraints. Geometric checks do not certify the visual/anatomical quality of the grooves.'}
(root/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('VERIFIED',json.dumps(report),flush=True)
