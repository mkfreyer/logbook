"""Independently compare all 300 serialized mesh objects to approved 0ab3d83."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

p = argparse.ArgumentParser()
p.add_argument('--baseline',type=Path,required=True)
p.add_argument('--asset',type=Path,required=True)
a = p.parse_args(sys.argv[sys.argv.index('--')+1:])
root = a.asset.resolve()
meta = json.loads((root/'guides.json').read_text())
sha = lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(a.baseline) == meta['baseline_blend_sha256']


def field(collection,key,size,dtype=np.float32):
    arr = np.empty(len(collection)*size,dtype=dtype)
    collection.foreach_get(key,arr)
    return arr


def fingerprint(ob):
    m = ob.data
    h = hashlib.sha256()
    for arr in [field(m.vertices,'co',3),field(m.edges,'vertices',2,np.int32),
                field(m.loops,'vertex_index',1,np.int32),
                field(m.polygons,'loop_start',1,np.int32),
                field(m.polygons,'loop_total',1,np.int32),
                field(m.polygons,'use_smooth',1,np.bool_),
                field(m.polygons,'material_index',1,np.int32),
                np.array(ob.matrix_world,dtype='<f8')]:
        h.update(arr.tobytes())
    if m.shape_keys:
        for key in m.shape_keys.key_blocks:
            h.update(json.dumps([key.name,key.value,key.relative_key.name,
                                 key.interpolation,key.mute]).encode())
            h.update(field(key.data,'co',3).tobytes())
    h.update(json.dumps([g.name for g in ob.vertex_groups]).encode())
    h.update(json.dumps([[(g.group,g.weight)for g in v.groups]for v in m.vertices]).encode())
    for uv in m.uv_layers:
        h.update(uv.name.encode())
        h.update(field(uv.data,'uv',2).tobytes())
    return h.hexdigest()


def material_signature(mat):
    nodes = []
    for node in mat.node_tree.nodes:
        sockets = []
        for inp in node.inputs:
            if hasattr(inp,'default_value'):
                value = inp.default_value
                if hasattr(value,'__len__') and not isinstance(value,str):
                    value = list(value)
                if isinstance(value,(float,int,str,list)):
                    sockets.append([inp.identifier,value])
        nodes.append([node.name,node.bl_idname,sockets])
    links = sorted([l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier]
                   for l in mat.node_tree.links)
    return [mat.name,list(mat.diffuse_color),nodes,links]


def snapshot(path,scene_name):
    bpy.ops.wm.open_mainfile(filepath=str(path.resolve()),use_scripts=False)
    scene = bpy.data.scenes[scene_name]
    bpy.context.window.scene = scene
    scene.view_layers[0].update()
    graph = bpy.context.evaluated_depsgraph_get()
    meshes = {}
    for ob in scene.objects:
        if ob.type != 'MESH':
            continue
        ev = ob.evaluated_get(graph)
        m = ev.to_mesh()
        v = np.array([ob.matrix_world@p.co for p in m.vertices])
        f = np.array([q.vertices[:]for q in m.polygons],np.int32)
        meshes[ob['asset_id']] = {
            'v':v,'f':f,'fingerprint':fingerprint(ob),
            'normals':hashlib.sha256(field(m.corner_normals,'vector',3).tobytes()).hexdigest(),
            'modifiers':[(m.name,m.type,m.show_viewport,m.show_render) for m in ob.modifiers],
            'materials':[material_signature(slot.material) for slot in ob.material_slots]}
        ev.to_mesh_clear()
    lights = {o.name:[o.data.type,o.data.energy,o.data.shape,o.data.size,list(o.data.color),
                      [list(r)for r in o.matrix_world]] for o in scene.objects if o.type=='LIGHT'}
    return meshes,lights


before,lights_before = snapshot(a.baseline,meta['source_scene'])
after,lights_after = snapshot(root/meta['master'],meta['scene'])
assert len(before) == len(after) == 300 and before.keys() == after.keys()
assert lights_before == lights_after and len(lights_after) == 5
checks = {}
for key in before:
    b,r = before[key],after[key]
    for kind in ['v','f']:
        assert np.array_equal(b[kind],r[kind]),(key,kind)
    for kind in ['fingerprint','normals','modifiers','materials']:
        assert b[kind] == r[kind],(key,kind)
    checks[key] = {'raw_and_evaluated_geometry_identical':True,
                   'sha256_raw':r['fingerprint'],'vertices':len(r['v']),
                   'triangles':len(r['f']),'max_displacement_m':0}
trees = {side:BVHTree.FromPolygons(after['deltoid.'+side]['v'].tolist(),
                                  after['deltoid.'+side]['f'].tolist(),all_triangles=True)
         for side in ['right','left']}
projection_distance = 0.
for name,rec in meta['paths'].items():
    for p in rec['points']:
        assert p['object']=='deltoid.right'
        distance = trees['right'].find_nearest(Vector(p['surface_m']))[3]
        projection_distance = max(projection_distance,distance)
assert projection_distance < 1e-6
assert meta['surface_reprojection_error_max_px'] < .005
scene = bpy.data.scenes[meta['scene']]
guides = [ob for ob in scene.objects if ob.get('guide_only')]
assert all(ob.type=='CURVE' and len(ob.modifiers)==0 for ob in guides)
assert not any(ob.type=='MESH' and ob.get('guide_only') for ob in scene.objects)
actual_guides = [ob for ob in guides if ob['role']!='outside']
assert len(actual_guides)==10  # two old + shared upper + two new, per shoulder
display_error = 0.
for ob in actual_guides:
    rows = meta['paths'][ob['part']]['points']
    surface = np.array([r['surface_m'] for r in rows])
    normals = np.array([r['normal'] for r in rows])
    if ob['side']=='left':
        surface[:,0] = 2*meta['median_plane_x_m']-surface[:,0]
        for i in range(len(surface)):
            nearest = trees['left'].find_nearest(Vector(surface[i]))
            surface[i],normals[i] = nearest[:2]
    expected = surface+meta['display_normal_lift_m']*normals
    serialized = np.array([p.co[:3]for p in ob.data.splines[0].points])
    assert len(expected)==len(serialized)
    error = float(np.max(np.linalg.norm(serialized-expected,axis=1)))
    display_error = max(display_error,error)
assert display_error < 2e-7
render = json.loads((root/'renders/metadata.json').read_text())
for frame in render['frames']:
    assert sha(root/'renders'/frame['file']) == frame['sha256']
refs = [frame for frame in render['frames'] if frame['file'].startswith('reference-')
        and frame['file']!='reference-epaule-gauche.png']
assert len(refs)==4
for fieldname in ['camera_matrix','ortho_scale','resolution','pixel_aspect_x']:
    assert all(frame[fieldname]==refs[0][fieldname] for frame in refs)
report = {'baseline_commit':meta['baseline_commit'],'baseline_sha256':sha(a.baseline),
          'master_sha256':sha(root/meta['master']),'all_300_mesh_objects_identical':True,
          'two_P4_deltoids_identical':True,'other_298_objects_identical':True,
          'head_throat_pecs_body_identical':True,'mesh_displacement_max_m':0,
          'raw_topology_shape_keys_weights_UV_matrices_normals_materials_identical':True,
          'triangles_total':sum(len(row['f']) for row in after.values()),
          'original_five_lights_identical':True,'guide_objects_type':'CURVE',
          'guide_objects_count':len(guides),
          'true_deltoid_curve_guides_count':len(actual_guides),
          'occlusion_proxies_count':len(guides)-len(actual_guides),
          'serialized_curve_display_offset_max_error_m':display_error,
          'occluded_path_points_also_projected_to_deltoid':True,
          'projected_samples_max_surface_distance_m':projection_distance,
          'surface_reprojection_error_max_px':meta['surface_reprojection_error_max_px'],
          'display_lift_m':meta['display_normal_lift_m'],
          'reference_camera_identical_in_four_control_frames':True,
          'render_hashes_verified':len(render['frames']),'sculpture_performed':False,
          'objects':checks}
(root/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
print('VERIFIED',json.dumps({k:v for k,v in report.items() if k!='objects'}),flush=True)
