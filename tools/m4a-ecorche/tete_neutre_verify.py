"""Independent unchanged-body, fixed-throat, new-head and GLB verification."""
import argparse
import ast
import hashlib
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def definitions(name):
    path = Path(__file__).with_name(name)
    tree = ast.parse(path.read_text())
    nodes = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.Import, ast.ImportFrom))]
    scope = {}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), scope)
    return scope


def head_normals(path, scene_name):
    bpy.ops.wm.open_mainfile(filepath=str(path.resolve()), use_scripts=False)
    scene = bpy.data.scenes[scene_name]
    bpy.context.window.scene = scene
    scene.view_layers[0].update()
    graph = bpy.context.evaluated_depsgraph_get()
    ob = next(o for o in scene.objects if o.get('asset_id') == 'head_throat.neutral_surface')
    ev = ob.evaluated_get(graph)
    m = ev.to_mesh()
    normals = np.array([n.vector[:] for n in m.corner_normals]).reshape(-1, 3, 3)
    ev.to_mesh_clear()
    return normals


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--asset', type=Path, required=True)
    a = p.parse_args(sys.argv[sys.argv.index('--')+1:])
    root = a.asset.resolve()
    meta = json.loads((root/'tete.json').read_text())
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    baseline = root/meta['baseline_master']
    assert sha(baseline) == meta['baseline_blend_sha256']
    assert sha(root/meta['master']) == meta['master_sha256']
    helper = definitions('guides_deltoides_verify.py')
    before, lights = helper['snapshot'](baseline, meta['source_scene'])
    after, new_lights = helper['snapshot'](root/meta['master'], meta['scene'])
    key = 'head_throat.neutral_surface'
    removed = set(meta['removed_objects'])
    assert removed == {'head.eye.l', 'head.eye.r'}
    assert len(before) == 299 and len(after) == 297
    assert set(after) == set(before)-removed
    assert lights == new_lights and len(lights) == 5
    preserved = {}
    for ident in set(before)-removed-{key}:
        for field in ['v', 'f']:
            assert np.array_equal(before[ident][field], after[ident][field]), (ident, field)
        for field in ['fingerprint', 'normals', 'modifiers', 'materials']:
            assert before[ident][field] == after[ident][field], (ident, field)
        preserved[ident] = after[ident]['fingerprint']
    assert len(preserved) == 296
    assert before[key]['materials'] == after[key]['materials']
    old_v, old_f = before[key]['v'], before[key]['f']
    v, f = after[key]['v'], after[key]['f']
    cut = meta['neck_protected_through_z_m']
    neck_faces = np.max(old_v[old_f, 2], axis=1) <= cut+1e-8
    n = int(neck_faces.sum())
    assert n == meta['retained_neck_triangles'] == 10637
    assert np.array_equal(old_v[old_f[neck_faces]], v[f[:n]])
    original_normals = head_normals(baseline, meta['source_scene'])[neck_faces]
    retained_normals = head_normals(root/meta['master'], meta['scene'])[:n]
    normal_error = float(np.max(np.abs(original_normals-retained_normals)))
    cosine = np.sum(original_normals*retained_normals, axis=2)/(
        np.linalg.norm(original_normals, axis=2)*np.linalg.norm(retained_normals, axis=2))
    normal_angle = float(np.degrees(np.arccos(np.clip(cosine, -1, 1))).max())
    # Blender encodes custom normals relative to the local normal fan. Replacing
    # the head changes that basis at the shared cervical border; allow only a
    # sub-degree encoding difference, while testing positions/faces exactly.
    assert normal_angle < .15, ('Cervical normal encoding error too large', normal_angle)
    assert np.max(v[f[n:], 2]) <= 1.800001
    assert np.min(v[f[n:], 2]) >= cut-1e-8
    edges = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
    unique, counts = np.unique(np.sort(edges, axis=1), axis=0, return_counts=True)
    assert np.all(counts == 2), 'Head/throat contains an open or non-manifold edge'
    assert len(v)-len(unique)+len(f) == 2
    # Each edge must occur once in each direction (consistent orientation).
    assert np.array_equal(np.unique(edges, axis=0), np.unique(edges[:, ::-1], axis=0))
    area = np.linalg.norm(np.cross(v[f[:, 1]]-v[f[:, 0]], v[f[:, 2]]-v[f[:, 0]]), axis=1)/2
    assert np.min(area) > 1e-12
    volume = float(np.einsum('ij,ij->i', v[f[:, 0]], np.cross(v[f[:, 1]], v[f[:, 2]])).sum()/6)
    assert volume > 0
    tree = BVHTree.FromPolygons(v.tolist(), f.tolist(), all_triangles=True)
    contacts = [(i, j) for i, j in tree.overlap(tree)
                if i < j and not np.isin(f[i], f[j]).any()]
    assert not contacts, ('New head self-intersections', len(contacts), contacts[:8])
    codec = definitions('zones_deltoides_verify.py')
    components = codec['face_components'](f)
    assert components == [len(f)]
    # Check that previously hidden cervical/anatomical objects do not emerge
    # through the replacement head from the four validation directions.
    bv, bf, offset = [], [], 0
    for ident in preserved:
        vv, ff = before[ident]['v'], before[ident]['f']
        ff = ff[np.max(vv[ff, 2], axis=1) > 1.59]
        if not len(ff):
            continue
        bv.append(vv)
        bf.append(ff+offset)
        offset += len(vv)
    body = BVHTree.FromPolygons(np.vstack(bv).tolist(), np.vstack(bf).tolist(), all_triangles=True)
    original_head = BVHTree.FromPolygons(old_v.tolist(), old_f.tolist(), all_triangles=True)
    visibility = {}
    for yaw in [0, -35, 35, -90, 90, 180]:
        theta = np.radians(yaw)
        direction = Vector((-np.sin(theta), np.cos(theta), 0))
        horizontal = direction.cross(Vector((0, 0, 1))).normalized()
        count = exposed = 0
        for xx in np.arange(-.10, .1001, .001):
            for zz in np.arange(1.59, 1.8001, .001):
                ray = Vector((meta['median_plane_x_m'], .035, float(zz)))+float(xx)*horizontal-3*direction
                old_hit = original_head.ray_cast(ray, direction, 6)
                body_hit = body.ray_cast(ray, direction, 6)
                if old_hit[0] is None or body_hit[0] is None or old_hit[3] >= body_hit[3]-1e-5:
                    continue
                count += 1
                new_hit = tree.ray_cast(ray, direction, 6)
                exposed += int(new_hit[0] is None or new_hit[3] > body_hit[3]+1e-5)
        visibility[str(yaw)] = {'previously_covered_samples': count, 'newly_exposed_body_samples': exposed}
        assert exposed == 0, ('Underlying anatomy protrudes', yaw, exposed)
    old_doc, _, old_ac = codec['glb'](root/meta['baseline_glb'])
    doc, _, ac = codec['glb'](root/meta['export_file'])
    old_nodes = {n['name']: n for n in old_doc['nodes'] if 'mesh' in n}
    nodes = {n['name']: n for n in doc['nodes'] if 'mesh' in n}
    assert set(nodes) == set(after)
    for ident in preserved:
        op = old_doc['meshes'][old_nodes[ident]['mesh']]['primitives']
        np_ = doc['meshes'][nodes[ident]['mesh']]['primitives']
        assert len(op) == len(np_)
        for x, y in zip(op, np_):
            assert np.array_equal(old_ac(x['indices']), ac(y['indices'])), ident
            assert x['attributes'].keys() == y['attributes'].keys()
            for attribute in x['attributes']:
                assert np.array_equal(old_ac(x['attributes'][attribute]), ac(y['attributes'][attribute])), (ident, attribute)
            assert old_doc['materials'][x['material']]['name'] == doc['materials'][y['material']]['name']
    prims = doc['meshes'][nodes[key]['mesh']]['primitives']
    assert len(prims) == 1
    prim = prims[0]
    gv, gf = ac(prim['attributes']['POSITION']), ac(prim['indices']).reshape(-1, 3)
    expected = v[:, [0, 2, 1]].copy()
    expected[:, 2] *= -1
    assert np.array_equal(codec['signatures'](expected[f]), codec['signatures'](gv[gf]))
    mapping = json.loads((root/'selection-map.json').read_text())
    assert len(mapping['zones']) == 6
    for zone, record in mapping['zones'].items():
        pr = doc['meshes'][record['mesh_index']]['primitives'][record['primitive_index']]
        mat = doc['materials'][pr['material']]
        assert pr['extras']['zone_id'] == mat['extras']['zone_id'] == mat['name'] == zone
    report = {
        'baseline_commit': meta['baseline_commit'], 'baseline_sha256': sha(baseline),
        'master_sha256': sha(root/meta['master']), 'retained_other_objects_identical': len(preserved),
        'retained_other_vertices_moved': 0, 'retained_glb_all_attributes_identical': len(preserved),
        'neck_original_triangles_identical': n, 'neck_preserved_through_z_m': cut,
        'neck_normals_max_component_error_after_encoding': normal_error,
        'neck_normals_max_angular_error_degrees_after_encoding': normal_angle,
        'head_removed_objects': sorted(removed), 'head_closed_two_manifold': True,
        'head_connected_components': components, 'head_euler_characteristic': 2,
        'head_consistent_outward_orientation': True, 'head_self_intersections': len(contacts),
        'head_minimum_triangle_area_m2': float(area.min()), 'head_volume_m3': volume,
        'underlying_anatomy_visibility_samples': visibility,
        'head_glb_surface_exact': True, 'six_deltoid_ids_preserved': sorted(mapping['zones']),
        'source_neutral_material_and_lighting_preserved': True,
        'triangles_before': sum(len(row['f']) for row in before.values()),
        'triangles_after': sum(len(row['f']) for row in after.values()),
        'preserved_object_fingerprints': preserved, 'verifier_sha256': sha(Path(__file__)),
    }
    (root/'verification.json').write_text(json.dumps(report, indent=2)+'\n')
    print('VERIFIED_HEAD', json.dumps({k: v for k, v in report.items() if k != 'preserved_object_fingerprints'}), flush=True)


if __name__ == '__main__':
    main()
