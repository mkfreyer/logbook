"""Independent serialized-body, foot-contact, symmetry and GLB checks."""
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


def inside(tree, point):
    # Closed-source volume membership does not depend on the orientation of a
    # single face near an edge. Retry a near-grazing vertical ray if necessary.
    for jitter in [1e-8, 3e-7, 1.1e-6]:
        ray = Vector((point[0]+jitter, point[1]+1.7*jitter, -.03))
        hits = []
        for _ in range(128):
            hit = tree.ray_cast(ray, Vector((0, 0, 1)), 1)[0]
            if hit is None:
                break
            hits.append(hit.z)
            ray = hit+Vector((0, 0, 1e-7))
        if len(hits) % 2 == 0:
            return sum(z < point[2] for z in hits) % 2 == 1
    raise AssertionError('Ambiguous source-contact ray')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--asset', type=Path, required=True)
    a = p.parse_args(sys.argv[sys.argv.index('--')+1:])
    root = a.asset.resolve()
    meta = json.loads((root/'finition.json').read_text())
    baseline = (root/meta['baseline_master']).resolve()
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    assert sha(baseline) == meta['baseline_blend_sha256']
    helper = definitions('guides_deltoides_verify.py')
    before, lights = helper['snapshot'](baseline, meta['source_scene'])
    after, new_lights = helper['snapshot'](root/meta['master'], meta['scene'])
    donor_checks = {}
    if 'donor_master' in meta:
        donor = (root/meta['donor_master']).resolve()
        assert sha(donor) == meta['donor_blend_sha256']
        donor_objects, _ = helper['snapshot'](donor, meta['donor_scene'])
        for key in meta['changed_objects']:
            for field in ['v', 'f']:
                assert np.array_equal(donor_objects[key][field], after[key][field]), (key, field, 'donor')
            for field in ['fingerprint', 'normals', 'modifiers', 'materials']:
                assert donor_objects[key][field] == after[key][field], (key, field, 'donor')
            donor_checks[key] = donor_objects[key]['fingerprint']
    assert len(before) == len(after) == 299 and before.keys() == after.keys()
    assert lights == new_lights and len(lights) == 5
    changed = set(meta['changed_objects'])
    assert changed == {'m2_c001.left', 'm2_c001.right'}
    preserved = {}
    for key in before:
        if key in changed:
            assert before[key]['materials'] == after[key]['materials'], 'Neutral foot material changed'
            continue
        old, new = before[key], after[key]
        for field in ['v', 'f']:
            assert np.array_equal(old[field], new[field]), (key, field)
        for field in ['fingerprint', 'normals', 'modifiers', 'materials']:
            assert old[field] == new[field], (key, field)
        preserved[key] = new['fingerprint']
    left, right = after['m2_c001.left'], after['m2_c001.right']
    mirrored = left['v'].copy()
    mirrored[:, 0] = 2*meta['median_plane_x_m']-mirrored[:, 0]
    symmetry_error = float(np.linalg.norm(mirrored-right['v'], axis=1).max())
    assert symmetry_error < 1e-6
    assert np.array_equal(left['f'][:, ::-1], right['f'])
    codec = definitions('zones_deltoides_verify.py')
    feet = {}
    for side in ['left', 'right']:
        key = 'm2_c001.'+side
        v, f = after[key]['v'], after[key]['f']
        assert v[:, 2].max() < .195, 'Foot work extended beyond the immediate ankle'
        edges = np.sort(np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]), axis=1)
        unique, counts = np.unique(edges, axis=0, return_counts=True)
        assert counts.max() == 2
        border = unique[counts == 1]
        assert len(border) > 0
        samples = np.vstack([v[np.unique(border)], v[border].mean(1)])
        assert samples[:, 2].min() > .075, 'Unexpected opening on the forefoot'
        trees = []
        body_vertices, body_faces, offset = [], [], 0
        for reference in meta['construction']['reference_objects']:
            reference = reference.replace('.left', '.'+side)
            vv, ff = before[reference]['v'], before[reference]['f']
            trees.append(BVHTree.FromPolygons(vv.tolist(), ff.tolist(), all_triangles=True))
            body_vertices.append(vv)
            body_faces.append(ff+offset)
            offset += len(vv)
        depths = []
        for point in samples:
            candidates = [tree.find_nearest(Vector(point))[3] for tree in trees if inside(tree, point)]
            assert candidates, ('Exposed foot contact', side, point.tolist())
            depths.append(max(candidates))
        assert min(depths) > 1e-5
        tree = BVHTree.FromPolygons(v.tolist(), f.tolist(), all_triangles=True)
        overlaps = [(i, j) for i, j in tree.overlap(tree)
                    if i < j and not np.isin(f[i], f[j]).any()]
        assert not overlaps, ('Foot self-intersections', side, len(overlaps))
        # Verify the specific defect found in the first close-up: no old tendon
        # fragment should emerge through previously covered ankle skin.
        old_tree = BVHTree.FromPolygons(before[key]['v'].tolist(), before[key]['f'].tolist(), all_triangles=True)
        body_tree = BVHTree.FromPolygons(np.vstack(body_vertices).tolist(), np.vstack(body_faces).tolist(), all_triangles=True)
        direction = Vector((1.5 if side == 'left' else -1.5, 3.5, -1.1)).normalized()
        horizontal = direction.cross(Vector((0, 0, 1))).normalized()
        vertical = horizontal.cross(direction).normalized()
        center = Vector((.125 if side == 'left' else 2*meta['median_plane_x_m']-.125, .08, .145))
        cover_samples = newly_exposed = 0
        for x in np.arange(-.07, .0701, .0005):
            for y in np.arange(-.06, .0601, .0005):
                ray = center+float(x)*horizontal+float(y)*vertical-3*direction
                old_hit = old_tree.ray_cast(ray, direction, 6)
                body_hit = body_tree.ray_cast(ray, direction, 6)
                if old_hit[0] is None or body_hit[0] is None:
                    continue
                if not .105 < old_hit[0].z < .165 or old_hit[3] >= body_hit[3]-1e-5:
                    continue
                cover_samples += 1
                hit = tree.ray_cast(ray, direction, 6)
                newly_exposed += int(hit[0] is None or hit[3] > body_hit[3]+1e-5)
        assert cover_samples > 0 and newly_exposed == 0, ('Tendon fragment re-exposed', side, newly_exposed)
        original = before[key]['v']
        forefoot = original[(original[:, 2] < .075) & (original[:, 1] < .035)]
        error = np.array([tree.find_nearest(Vector(q))[3] for q in forefoot])
        assert error.max() < .002, ('Forefoot changed excessively', side, float(error.max()))
        old_low, new_low = original[original[:, 2] < .075], v[v[:, 2] < .075]
        old_bounds, new_bounds = np.vstack([old_low.min(0), old_low.max(0)]), np.vstack([new_low.min(0), new_low.max(0)])
        assert np.abs(old_bounds-new_bounds).max() < .002
        feet[side] = {
            'vertices': len(v), 'triangles_before': len(before[key]['f']), 'triangles_after': len(f),
            'boundary_edges': len(border), 'buried_contact_samples': len(samples),
            'contact_depth_range_m': [float(min(depths)), float(max(depths))],
            'boundary_height_range_m': [float(samples[:, 2].min()), float(samples[:, 2].max())],
            'self_intersections': len(overlaps), 'face_component_triangle_counts': codec['face_components'](f),
            'ankle_old_covered_rays_tested': cover_samples,
            'ankle_source_fragments_newly_visible_rays': newly_exposed,
            'forefoot_reference_vertices_tested': len(forefoot),
            'forefoot_distance_p50_p95_max_m': np.quantile(error, [.5, .95, 1]).tolist(),
            'lower_foot_bounds_before_m': old_bounds.tolist(), 'lower_foot_bounds_after_m': new_bounds.tolist(),
            'bbox_m': [v.min(0).tolist(), v.max(0).tolist()],
        }
    old_doc, _, old_ac = codec['glb'](root/meta['baseline_glb'])
    doc, _, ac = codec['glb'](root/meta.get('export_file', 'ecorche-finition-pieds.glb'))
    old_nodes = {n['name']: n for n in old_doc['nodes'] if 'mesh' in n}
    nodes = {n['name']: n for n in doc['nodes'] if 'mesh' in n}
    assert old_nodes.keys() == nodes.keys()
    for key in preserved:
        op = old_doc['meshes'][old_nodes[key]['mesh']]['primitives']
        np_ = doc['meshes'][nodes[key]['mesh']]['primitives']
        assert len(op) == len(np_)
        for x, y in zip(op, np_):
            assert np.array_equal(old_ac(x['indices']), ac(y['indices'])), key
            assert x['attributes'].keys() == y['attributes'].keys()
            for attribute in x['attributes']:
                assert np.array_equal(old_ac(x['attributes'][attribute]), ac(y['attributes'][attribute])), (key, attribute)
            assert old_doc['materials'][x['material']]['name'] == doc['materials'][y['material']]['name']
    for key in changed:
        prims = doc['meshes'][nodes[key]['mesh']]['primitives']
        assert len(prims) == 1
        prim = prims[0]
        gv, gf = ac(prim['attributes']['POSITION']), ac(prim['indices']).reshape(-1, 3)
        expected = after[key]['v'][:, [0, 2, 1]].copy()
        expected[:, 2] *= -1
        assert np.array_equal(codec['signatures'](expected[after[key]['f']]), codec['signatures'](gv[gf]))
    mapping = json.loads((root/'selection-map.json').read_text())
    assert len(mapping['zones']) == 6
    for zone, record in mapping['zones'].items():
        prim = doc['meshes'][record['mesh_index']]['primitives'][record['primitive_index']]
        material = doc['materials'][prim['material']]
        assert prim['extras']['zone_id'] == material['extras']['zone_id'] == material['name'] == zone
    report = {
        'baseline_commit': meta['baseline_commit'], 'baseline_sha256': sha(baseline),
        'master_sha256': sha(root/meta['master']), 'changed_objects': sorted(changed),
        'retained_other_objects_identical': len(preserved), 'retained_other_vertices_moved': 0,
        'groin_head_throat_deltoids_calves_legs_identical': True,
        'retained_glb_geometry_normals_indices_attributes_identical': len(preserved),
        'new_foot_glb_geometry_verified': True, 'neutral_foot_material_preserved': True,
        'source_lighting_preserved': True, 'symmetry_error_max_m': symmetry_error,
        'feet': feet, 'six_deltoid_zone_ids_preserved': sorted(mapping['zones']),
        'triangles_before': sum(len(r['f']) for r in before.values()),
        'triangles_after': sum(len(r['f']) for r in after.values()),
        'contact_validation': 'Vertices and edge midpoints tested inside unchanged closed source volumes by ray parity. Contacts are buried, not welded.',
        'preserved_object_fingerprints': preserved,
        'verifier_sha256': sha(Path(__file__)),
    }
    if donor_checks:
        report['donor_commit'] = meta['donor_commit']
        report['donor_sha256'] = meta['donor_blend_sha256']
        report['feet_identical_to_donor_including_normals_materials_topology'] = donor_checks
    (root/'verification.json').write_text(json.dumps(report, indent=2)+'\n')
    print('VERIFIED_FEET', json.dumps({k: v for k, v in report.items() if k != 'preserved_object_fingerprints'}), flush=True)


if __name__ == '__main__':
    main()
