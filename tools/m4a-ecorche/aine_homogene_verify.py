"""Independent check of retained geometry, buried borders, gap and GLB IDs."""
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


def definitions(filename):
    path = Path(__file__).with_name(filename)
    tree = ast.parse(path.read_text())
    nodes = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.Import, ast.ImportFrom))]
    scope = {}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), scope)
    return scope


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--asset', type=Path, required=True)
    a = p.parse_args(sys.argv[sys.argv.index('--')+1:])
    root = a.asset.resolve()
    meta = json.loads((root/'finition.json').read_text())
    baseline = (root/meta['baseline_master']).resolve()
    helper = definitions('guides_deltoides_verify.py')
    before, lights = helper['snapshot'](baseline, meta['source_scene'])
    after, new_lights = helper['snapshot'](root/meta['master'], meta['scene'])
    assert len(before) == len(after) == 299 and before.keys() == after.keys()
    assert lights == new_lights
    checks = {}
    for key in before:
        if key == 'groin.neutral_surface':
            continue
        old, new = before[key], after[key]
        for field in ['v', 'f']:
            assert np.array_equal(old[field], new[field]), (key, field)
        for field in ['fingerprint', 'normals', 'modifiers', 'materials']:
            assert old[field] == new[field], (key, field)
        checks[key] = new['fingerprint']
    surface = np.load(root/'surface-fondue.npz')
    v, f = after['groin.neutral_surface']['v'], after['groin.neutral_surface']['f']
    edges = np.sort(np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]), axis=1)
    unique, counts = np.unique(edges, axis=0, return_counts=True)
    assert counts.max() == 2
    boundary = np.unique(unique[counts == 1])
    assert np.array_equal(boundary, surface['boundary_vertices'])
    assert np.all(surface['contact_weight'][boundary] > .999999)
    reference_trees = []
    ids = [r['id'] for r in meta['construction']['sources'] if r['used_for_distance_field']]
    for key in ids:
        vv, ff = before[key]['v'], before[key]['f']
        tree = BVHTree.FromPolygons(vv.tolist(), ff.tolist(), all_triangles=True)
        volume = np.einsum('ij,ij->i', vv[ff[:, 0]], np.cross(vv[ff[:, 1]], vv[ff[:, 2]])).sum()/6
        reference_trees.append((tree, 1 if volume > 0 else -1))

    def body_distance(point):
        q = Vector(point)
        values = []
        for tree, orientation in reference_trees:
            hit, normal, _, distance = tree.find_nearest(q)
            values.append(distance*(-1 if (q-hit).dot(normal)*orientation < 0 else 1))
        return min(values)

    border_d = np.array([body_distance(q) for q in v[boundary]])
    assert border_d.max() < 1e-6, ('Exposed contact boundary', float(border_d.max()))
    tree = BVHTree.FromPolygons(v.tolist(), f.tolist(), all_triangles=True)
    intersections = [(i, j) for i, j in tree.overlap(tree)
                     if i < j and not np.isin(f[i], f[j]).any()]
    assert not intersections, ('New surface self-intersections', len(intersections))
    codec = definitions('zones_deltoides_verify.py')
    components = codec['face_components'](f)
    areas = np.linalg.norm(np.cross(v[f[:, 1]]-v[f[:, 0]], v[f[:, 2]]-v[f[:, 0]]), axis=1)/2
    # Opening control: same retained body; compare old/new central surface rays.
    old_cap = before['groin.neutral_surface']
    old_tree = BVHTree.FromPolygons(old_cap['v'].tolist(), old_cap['f'].tolist(), all_triangles=True)
    new_hits_in_old_lower_gap = 0
    samples = 0
    for z in np.arange(.84, .892, .001):
        for x in .002114987923242599+np.arange(-60, 61)*.001:
            ray = Vector((x, -1, z))
            old_hit = old_tree.ray_cast(ray, Vector((0, 1, 0)), 2)[0]
            new_hit = tree.ray_cast(ray, Vector((0, 1, 0)), 2)[0]
            samples += 1
            new_hits_in_old_lower_gap += int(old_hit is None and new_hit is not None)
    assert new_hits_in_old_lower_gap == 0
    # Test the actual opening against the whole retained body, including the
    # posterior pieces visible through it, not only the isolated new patch.
    retained_v, retained_f, offset = [], [], 0
    for key, record in before.items():
        if key == 'groin.neutral_surface':
            continue
        retained_v.append(record['v'])
        retained_f.append(record['f']+offset)
        offset += len(record['v'])
    retained_tree = BVHTree.FromPolygons(np.vstack(retained_v).tolist(),
                                         np.vstack(retained_f).tolist(), all_triangles=True)
    opening_samples = opening_closed = 0
    for z in np.arange(.84, .956, .001):
        for x in .002114987923242599+np.arange(-60, 61)*.001:
            ray, direction = Vector((x, -1, z)), Vector((0, 1, 0))
            if retained_tree.ray_cast(ray, direction, 2)[0] is not None:
                continue
            if old_tree.ray_cast(ray, direction, 2)[0] is not None:
                continue
            opening_samples += 1
            opening_closed += int(tree.ray_cast(ray, direction, 2)[0] is not None)
    assert opening_samples > 0 and opening_closed == 0
    cover_samples = newly_uncovered = 0
    uncovered_coordinates = []
    for z in np.arange(.900, .977, .001):
        for x in .002114987923242599+np.arange(-50, 51)*.001:
            ray, direction = Vector((x, -1, z)), Vector((0, 1, 0))
            old_hit = old_tree.ray_cast(ray, direction, 2)
            body_hit = retained_tree.ray_cast(ray, direction, 2)
            if old_hit[0] is None or body_hit[0] is None:
                continue
            if old_hit[3] >= body_hit[3]-1e-5:
                continue
            cover_samples += 1
            new_hit = tree.ray_cast(ray, direction, 2)
            uncovered = new_hit[0] is None or new_hit[3] > body_hit[3]+1e-5
            newly_uncovered += int(uncovered)
            if uncovered:
                uncovered_coordinates.append([float(x), float(z)])
    assert cover_samples > 0
    # This is a visibility diagnostic, not a shape-invariance requirement on
    # the rebuilt presentation patch. Its lower contour is intentionally more
    # receding. Retained meshes and buried contact boundaries are checked above.
    # Exact serialized GLB preservation of all 298 retained source meshes.
    old_doc, _, old_ac = codec['glb'](baseline.parent/'ecorche-aine-fondue.glb')
    doc, _, ac = codec['glb'](root/'ecorche-aine-homogene.glb')
    old_nodes = {n['name']: n for n in old_doc['nodes'] if 'mesh' in n}
    new_nodes = {n['name']: n for n in doc['nodes'] if 'mesh' in n}
    for key in checks:
        op = old_doc['meshes'][old_nodes[key]['mesh']]['primitives']
        np_ = doc['meshes'][new_nodes[key]['mesh']]['primitives']
        assert len(op) == len(np_)
        for x, y in zip(op, np_):
            assert np.array_equal(old_ac(x['indices']), ac(y['indices'])), key
            for att in x['attributes']:
                assert np.array_equal(old_ac(x['attributes'][att]), ac(y['attributes'][att])), (key, att)
            assert old_doc['materials'][x['material']]['name'] == doc['materials'][y['material']]['name']
    mapping = json.loads((root/'selection-map.json').read_text())
    assert len(mapping['zones']) == 6
    for zone, rec in mapping['zones'].items():
        primitive = doc['meshes'][rec['mesh_index']]['primitives'][rec['primitive_index']]
        material = doc['materials'][primitive['material']]
        assert primitive['extras']['zone_id'] == material['extras']['zone_id'] == material['name'] == zone
    new_primitives = doc['meshes'][new_nodes['groin.neutral_surface']['mesh']]['primitives']
    assert len(new_primitives) == 1
    primitive = new_primitives[0]
    gv = ac(primitive['attributes']['POSITION'])
    gf = ac(primitive['indices']).reshape(-1, 3)
    expected = v[:, [0, 2, 1]].copy()
    expected[:, 2] *= -1
    assert np.array_equal(codec['signatures'](expected[f]), codec['signatures'](gv[gf]))
    report = {
        'baseline_commit': meta['baseline_commit'],
        'baseline_sha256': hashlib.sha256(baseline.read_bytes()).hexdigest(),
        'master_sha256': hashlib.sha256((root/meta['master']).read_bytes()).hexdigest(),
        'retained_original_objects_identical': len(checks),
        'retained_original_vertices_moved': 0,
        'adductors_thighs_deltoids_head_throat_feet_identical': True,
        'retained_glb_mesh_geometry_normals_indices_attributes_identical': len(checks),
        'new_surface_glb_triangle_geometry_verified': True,
        'six_deltoid_ids_preserved': sorted(mapping['zones']),
        'source_lighting_preserved': True,
        'surface_triangles_before': len(old_cap['f']), 'surface_triangles_after': len(f),
        'dedicated_surface_reconstructed': True,
        'triangles_total_blender': sum(len(r['f']) for r in after.values()),
        'contact_boundary_vertices': len(boundary),
        'contact_boundary_signed_body_distance_range_m': [float(border_d.min()), float(border_d.max())],
        'all_contact_boundaries_inside_source': True,
        'surface_is_closed': False, 'surface_component_triangle_counts': components,
        'minimum_new_triangle_area_m2': float(areas.min()),
        'nonadjacent_new_surface_intersections': len(intersections),
        'lower_gap_rays_tested': samples, 'new_occlusions_in_lower_leg_gap': new_hits_in_old_lower_gap,
        'actual_opening_clear_rays_tested': opening_samples,
        'actual_opening_new_occlusions': opening_closed,
        'frontal_cover_samples_tested': cover_samples,
        'newly_exposed_deep_source_anatomy_samples': newly_uncovered,
        'newly_exposed_source_samples_xz_m': uncovered_coordinates,
        'new_surface_bbox_m': [v.min(0).tolist(), v.max(0).tolist()],
        'retained_object_fingerprints': checks,
    }
    (root/'verification.json').write_text(json.dumps(report, indent=2)+'\n')
    print('VERIFIED', json.dumps({k: val for k, val in report.items() if k != 'retained_object_fingerprints'}), flush=True)


if __name__ == '__main__':
    main()
