"""Independent serialized geometry, shading, closure and GLB preservation audit."""
import argparse
import ast
import hashlib
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils.bvhtree import BVHTree


def definitions(filename):
    path = Path(__file__).with_name(filename)
    tree = ast.parse(path.read_text())
    nodes = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom, ast.FunctionDef))]
    ns = {}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), ns)
    return ns


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--asset', type=Path, required=True)
    a = p.parse_args(sys.argv[sys.argv.index('--')+1:])
    root = a.asset.resolve()
    meta = json.loads((root/'finition.json').read_text())
    baseline = (root/meta['baseline_master']).resolve()
    helper = definitions('guides_deltoides_verify.py')
    before, lights_before = helper['snapshot'](baseline, meta['source_scene'])
    after, lights_after = helper['snapshot'](root/meta['master'], meta['scene'])
    assert len(before) == 300 and len(after) == 299
    assert set(after)-set(before) == {meta['added_object']}
    retired = set(meta['replaced_central_objects'])
    assert set(before)-set(after) == retired
    assert retired == {'m0_c098__CENTRAL__ATHLETIQUE', 'm1_c084__CENTRAL__ATHLETIQUE'}
    checks = {}
    for key, old in before.items():
        if key in retired:
            continue
        new = after[key]
        for field in ['v', 'f']:
            assert np.array_equal(old[field], new[field]), (key, field)
        for field in ['fingerprint', 'normals', 'modifiers', 'materials']:
            assert old[field] == new[field], (key, field)
        checks[key] = {'raw_fingerprint': new['fingerprint'],
                       'evaluated_surface_and_corner_normals_identical': True}
    assert lights_before == lights_after
    bbox_before = np.array([np.concatenate([r['v'] for r in before.values()]).min(0),
                            np.concatenate([r['v'] for r in before.values()]).max(0)])
    bbox_after = np.array([np.concatenate([r['v'] for r in after.values()]).min(0),
                           np.concatenate([r['v'] for r in after.values()]).max(0)])
    assert np.array_equal(bbox_before, bbox_after)
    historical = bpy.data.scenes[meta['source_scene']]
    history_meshes = {o['asset_id']: o for o in historical.objects if o.type == 'MESH'}
    assert len(history_meshes) == 300
    for key in retired:
        assert helper['fingerprint'](history_meshes[key]) == before[key]['fingerprint']
    patch = after[meta['added_object']]
    v, f = patch['v'], patch['f']
    edges = np.sort(np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]), axis=1)
    _, counts = np.unique(edges, axis=0, return_counts=True)
    assert np.all(counts == 2), 'Open/nonmanifold presentation mesh'
    codec = definitions('zones_deltoides_verify.py')
    assert codec['face_components'](f) == [len(f)]
    cross = np.cross(v[f[:, 1]]-v[f[:, 0]], v[f[:, 2]]-v[f[:, 0]])
    assert np.linalg.norm(cross, axis=1).min() > 1e-10
    volume = float(np.einsum('ij,ij->i', v[f[:, 0]],
                              np.cross(v[f[:, 1]], v[f[:, 2]])).sum()/6)
    assert volume > 0
    tree = BVHTree.FromPolygons(v.tolist(), f.tolist(), all_triangles=True)
    overlaps = [(i, j) for i, j in tree.overlap(tree)
                if i < j and not np.isin(f[i], f[j]).any()]
    assert not overlaps, 'Self-intersecting presentation mesh'
    plane = .002114987923242599
    mirrored = v.copy()
    mirrored[:, 0] = 2*plane-mirrored[:, 0]
    # Nearest mirrored vertices are checked independently of face indexing.
    symmetry_error = max((tree.find_nearest(tuple(point))[3] for point in mirrored))
    assert symmetry_error < 2e-7
    assert v[:, 2].min() > .889 and v[:, 2].max() < .957
    assert abs(v[:, 0]-plane).max() < .053
    old_doc, _, old_ac = codec['glb'](baseline.parent/'ecorche-p4-p5-zones.glb')
    doc, _, ac = codec['glb'](root/'ecorche-finition-aine.glb')
    old_nodes = {n['name']: n for n in old_doc['nodes'] if 'mesh' in n}
    new_nodes = {n['name']: n for n in doc['nodes'] if 'mesh' in n}
    glb_checks = {}
    for key, old in old_nodes.items():
        if key in retired:
            continue
        new = new_nodes[key]
        old_ps = old_doc['meshes'][old['mesh']]['primitives']
        new_ps = doc['meshes'][new['mesh']]['primitives']
        assert len(old_ps) == len(new_ps)
        for op, np_ in zip(old_ps, new_ps):
            assert np.array_equal(old_ac(op['indices']), ac(np_['indices'])), key
            assert op['attributes'].keys() == np_['attributes'].keys()
            for att in op['attributes']:
                assert np.array_equal(old_ac(op['attributes'][att]), ac(np_['attributes'][att])), (key, att)
            assert old_doc['materials'][op['material']]['name'] == doc['materials'][np_['material']]['name']
        glb_checks[key] = True
    mapping = json.loads((root/'selection-map.json').read_text())
    assert len(mapping['zones']) == 6
    for zone, rec in mapping['zones'].items():
        primitive = doc['meshes'][rec['mesh_index']]['primitives'][rec['primitive_index']]
        assert primitive['extras']['zone_id'] == zone
        material = doc['materials'][primitive['material']]
        assert material['name'] == material['extras']['zone_id'] == zone
    cap_node = new_nodes[meta['added_object']]
    assert cap_node['extras']['interactive_muscle_zone'] is False
    primitives = doc['meshes'][cap_node['mesh']]['primitives']
    assert len(primitives) == 1
    primitive = primitives[0]
    exported_v = ac(primitive['attributes']['POSITION'])
    exported_f = ac(primitive['indices']).reshape(-1, 3)
    expected_yup = v[:, [0, 2, 1]].copy()
    expected_yup[:, 2] *= -1
    assert np.array_equal(codec['signatures'](expected_yup[f]),
                          codec['signatures'](exported_v[exported_f]))
    report = {
        'baseline_commit': meta['baseline_commit'],
        'baseline_sha256': hashlib.sha256(baseline.read_bytes()).hexdigest(),
        'master_sha256': hashlib.sha256((root/meta['master']).read_bytes()).hexdigest(),
        'original_meshes_exactly_preserved': len(checks),
        'replaced_central_objects': sorted(retired),
        'original_vertices_moved': 0,
        'two_substituted_pieces_retained_identically_in_historical_scene': True,
        'head_P5_throat_deltoids_and_all_original_thigh_meshes_identical': True,
        'five_original_lights_identical': True,
        'global_body_bbox_identical': True,
        'global_body_bbox_m': bbox_after.tolist(),
        'added_object': meta['added_object'], 'added_triangles': len(f),
        'triangles_total_blender': sum(len(r['f']) for r in after.values()),
        'presentation_surface_closed_manifold': True,
        'presentation_surface_connected_components': 1,
        'presentation_surface_nonadjacent_self_intersections': 0,
        'presentation_surface_signed_volume_m3': volume,
        'presentation_surface_mirror_surface_error_max_m': symmetry_error,
        'presentation_surface_bbox_min_m': v.min(0).tolist(),
        'presentation_surface_bbox_max_m': v.max(0).tolist(),
        'original_glb_mesh_positions_normals_indices_and_attributes_bit_identical': len(glb_checks),
        'new_presentation_surface_glb_triangle_geometry_verified': True,
        'six_zone_material_and_primitive_ids_verified': sorted(mapping['zones']),
        'buried_joins': 'Envelope fitted behind existing muscles; intentional buried interpenetration at joins, not a welded global skin.',
        'global_body_intersection_certification': False,
        'original_objects': checks,
    }
    (root/'verification.json').write_text(json.dumps(report, indent=2)+'\n')
    print('VERIFIED', json.dumps({k: val for k, val in report.items() if k != 'original_objects'}), flush=True)


if __name__ == '__main__':
    main()
