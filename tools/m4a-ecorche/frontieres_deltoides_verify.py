"""Independent surface, topology, seam-normal and serialized GLB checks."""
import argparse
import ast
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

import bpy
import numpy as np
from mathutils.bvhtree import BVHTree

NORMAL_VECTOR_TOLERANCE = .001  # Default retained for the 990201f audit.

def helpers(name):
    path = Path(__file__).with_name(name)
    nodes = [n for n in ast.parse(path.read_text()).body
             if isinstance(n, (ast.Import, ast.ImportFrom, ast.FunctionDef))]
    ns = {}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), ns)
    return ns


def boundary_stats(v, f, labels):
    edge_faces = defaultdict(list)
    for i, face in enumerate(f):
        for a, b in zip(face, np.roll(face, -1)):
            edge_faces[tuple(sorted((int(a), int(b))))].append(i)
    by_pair = defaultdict(lambda: defaultdict(list))
    for (a, b), faces in edge_faces.items():
        if len(faces) == 2 and labels[faces[0]] != labels[faces[1]]:
            pair = tuple(sorted((int(labels[faces[0]]), int(labels[faces[1]]))))
            by_pair[pair][a].append(b)
            by_pair[pair][b].append(a)
    result = {}
    for pair, adjacency in by_pair.items():
        turns = []
        for center, neighbors in adjacency.items():
            if len(neighbors) != 2:
                continue
            a, b = v[neighbors] - v[center]
            cosine = np.clip(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)), -1, 1)
            turns.append(180 - np.degrees(np.arccos(cosine)))
        result[str(pair)] = {'samples': len(turns),
                             'median_turn_degrees': float(np.median(turns)),
                             'p95_turn_degrees': float(np.percentile(turns, 95)),
                             'max_turn_degrees': float(np.max(turns))}
    return result


def overlap_area(first, second):
    poly = list(first[:, 1:])
    for a, b in zip(second[:, 1:], np.roll(second[:, 1:], -1, axis=0)):
        result = []
        def value(p):
            d, q = b - a, p - a
            return d[0] * q[1] - d[1] * q[0]
        for x, y in zip(poly, poly[1:] + poly[:1]):
            dx, dy = value(x), value(y)
            if dx >= 0:
                result.append(x)
            if (dx >= 0) != (dy >= 0):
                result.append(x + (y - x) * dx / (dx - dy))
        poly = result
        if len(poly) < 3:
            return 0.
    xy = np.array(poly)
    return abs(float(np.sum(xy[:, 0] * np.roll(xy[:, 1], -1)
                            - xy[:, 1] * np.roll(xy[:, 0], -1)))) / 2


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--asset', type=Path, required=True)
    args = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
    root = args.asset.resolve()
    meta = json.loads((root / 'zones.json').read_text())
    provenance = np.load(root / 'provenance-surface.npz')
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    assert sha(args.baseline) == meta['baseline_blend_sha256']
    h = helpers('guides_deltoides_verify.py')
    util = helpers('zones_deltoides_verify.py')
    before, lights_before = h['snapshot'](args.baseline, meta['source_scene'])
    old_scene = bpy.context.scene
    cameras_before = {o.name: [list(map(list, o.matrix_world)), o.data.ortho_scale]
                      for o in old_scene.objects if o.type == 'CAMERA'}
    extra_before = {}
    graph = bpy.context.evaluated_depsgraph_get()
    for side in ['left', 'right']:
        ob = bpy.data.objects['P4P5__deltoid.' + side]
        mesh = ob.evaluated_get(graph).to_mesh()
        extra_before[side] = {
            'n': np.array([n.vector[:] for n in mesh.corner_normals]).reshape(-1, 3, 3),
            'labels': np.array([p.material_index for p in mesh.polygons])}
    after, lights_after = h['snapshot'](root / meta['master'], meta['scene'])
    assert before.keys() == after.keys() and len(after) == 300
    assert lights_before == lights_after
    scene = bpy.context.scene
    cameras_after = {o.name: [list(map(list, o.matrix_world)), o.data.ortho_scale]
                     for o in scene.objects if o.type == 'CAMERA'}
    assert cameras_before == cameras_after
    for key in before:
        if key not in ['deltoid.left', 'deltoid.right']:
            for field in ['fingerprint', 'normals', 'materials', 'modifiers']:
                assert before[key][field] == after[key][field], (key, field)
            assert np.array_equal(before[key]['v'], after[key]['v'])
            assert np.array_equal(before[key]['f'], after[key]['f'])
    checks = {}
    corner_normals_after = {}
    for side in ['right', 'left']:
        key = 'deltoid.' + side
        v0, f0, v, f = before[key]['v'], before[key]['f'], after[key]['v'], after[key]['f']
        ob = bpy.data.objects['P4P5__' + key]
        labels = np.array([p.material_index for p in ob.data.polygons])
        parent, bary = provenance[side + '_parent'], provenance[side + '_bary']
        assert np.array_equal(v[:len(v0)], v0), (side, 'original surface vertices')
        assert np.array_equal(f, provenance[side + '_f'])
        assert np.array_equal(labels, provenance[side + '_labels'])
        assert np.max(np.abs(bary.sum(axis=2) - 1)) < 1e-12 and bary.min() >= -1e-12
        expected = np.einsum('tij,tjk->tik', bary, v0[f0[parent]])
        error = np.linalg.norm(v[f] - expected, axis=2)
        assert error.max() < 1e-7, (side, 'float32 surface error', error.max())
        ratios = np.linalg.det(bary)
        assert ratios.min() > 0
        partition_area = np.bincount(parent, weights=ratios, minlength=len(f0))
        assert np.max(np.abs(partition_area - 1)) < 1e-10
        intersections = 0.
        for source_face in np.flatnonzero(np.bincount(parent, minlength=len(f0)) > 1):
            children = np.flatnonzero(parent == source_face)
            for ii, first in enumerate(children):
                for second in children[ii + 1:]:
                    intersections = max(intersections, overlap_area(bary[first], bary[second]))
        assert intersections < 1e-10
        edges, counts = np.unique(np.sort(np.concatenate([
            f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]), axis=1), axis=0, return_counts=True)
        assert np.all(counts == 2) and len(v) - len(edges) + len(f) == 2
        tree = BVHTree.FromPolygons(v.tolist(), f.tolist(), all_triangles=True)
        contacts = [(a, b) for a, b in tree.overlap(tree)
                    if a < b and not set(f[a]).intersection(f[b])]
        assert not contacts, (side, 'new self intersections', len(contacts))
        regions = []
        for index, head in enumerate(['anterior', 'lateral', 'posterior']):
            rec = next(r for r in meta['regions'] if r['id'] == f'deltoid.{side}.{head}')
            ids = np.flatnonzero(labels == index)
            assert np.array_equal(ids, np.array(rec['source_polygon_indices']))
            components = util['face_components'](f[ids])
            assert len(components) == 1
            regions.append({'id': rec['id'], 'triangles': len(ids), 'components': len(components)})
        graph = bpy.context.evaluated_depsgraph_get()
        mesh = ob.evaluated_get(graph).to_mesh()
        normals = np.array([n.vector[:] for n in mesh.corner_normals]).reshape(-1, 3, 3)
        corner_normals_after[key] = normals
        desired = np.einsum('tij,tjk->tik', bary, extra_before[side]['n'][parent])
        desired /= np.linalg.norm(desired, axis=2, keepdims=True)
        difference = np.linalg.norm(normals - desired, axis=2)
        assert difference.max() < NORMAL_VECTOR_TOLERANCE
        seam = defaultdict(list)
        for face, ns, label in zip(f, normals, labels):
            for vertex, normal in zip(face, ns):
                seam[int(vertex)].append((int(label), normal))
        seam_error = 0.
        for entries in seam.values():
            if len({label for label, _ in entries}) < 2:
                continue
            normal = np.array([n for _, n in entries])
            seam_error = max(seam_error, float(np.max(np.linalg.norm(normal - normal[0], axis=1))))
        assert seam_error < .001
        def volume(points, triangles):
            return float(np.einsum('ij,ij->i', points[triangles[:, 0]],
                          np.cross(points[triangles[:, 1]], points[triangles[:, 2]])).sum() / 6)
        checks[side] = {
            'original_vertices_bitwise_unchanged': True, 'original_vertices': len(v0),
            'added_vertices': len(v) - len(v0), 'original_triangles': len(f0),
            'triangles': len(f), 'added_triangles': len(f) - len(f0),
            'source_triangles_split': int((np.bincount(parent, minlength=len(f0)) > 1).sum()),
            'max_barycentric_surface_storage_error_m': float(error.max()),
            'source_face_partition_area_error_max': float(np.max(np.abs(partition_area - 1))),
            'max_sibling_overlap_area_barycentric': intersections,
            'closed_two_manifold_euler_2': True, 'nonadjacent_self_intersections': len(contacts),
            'volume_before_m3': volume(v0, f0), 'volume_after_m3': volume(v, f),
            'normal_interpolation_max_vector_error': float(difference.max()),
            'material_boundary_max_loop_normal_difference': seam_error,
            'boundary_before': boundary_stats(v0, f0, extra_before[side]['labels']),
            'boundary_after': boundary_stats(v, f, labels), 'regions': regions,
        }
    # Independent color mutation test on six separate datablocks.
    mats = [bpy.data.materials[r['material_name']] for r in meta['regions']]
    assert len({m.as_pointer() for m in mats}) == 6
    sockets = [m.node_tree.nodes['Principled BSDF'].inputs['Base Color'] for m in mats]
    original_colors = [list(s.default_value) for s in sockets]
    for i, socket in enumerate(sockets):
        socket.default_value = [.9, .2, .01, 1]
        assert all(list(s.default_value) == original_colors[j] for j, s in enumerate(sockets) if j != i)
        socket.default_value = original_colors[i]
    # Serialized GLB buffers, IDs and all surface triangles, including actual reimport.
    glb = util['glb']
    doc, binary, accessor = glb(root / 'ecorche-p4-p5-zones.glb')
    color, color_binary, _ = glb(root / 'ecorche-p4-p5-zones-controle.glb')
    assert binary == color_binary and len(doc['nodes']) == 300 and len(doc['materials']) == 7
    mapping = json.loads((root / 'selection-map.json').read_text())['zones']
    assert len(mapping) == 6
    seen = []
    glb_normal_error = 0.
    glb_boundary_normals = defaultdict(list)
    for node in doc['nodes']:
        key = node['name']
        for primitive in doc['meshes'][node['mesh']]['primitives']:
            f = accessor(primitive['indices']).reshape(-1, 3)
            corners = accessor(primitive['attributes']['POSITION'])[f]
            # Blender -> glTF axes.
            if key in ['deltoid.left', 'deltoid.right']:
                zone_id = primitive['extras']['zone_id']
                rec = mapping[zone_id]
                material = doc['materials'][primitive['material']]
                assert material['name'] == material['extras']['zone_id'] == zone_id
                ids = rec['blender_polygon_indices']
                expected = after[key]['v'][after[key]['f'][ids]][:, :, [0, 2, 1]].astype(np.float32)
                expected_normals = corner_normals_after[key][ids][:, :, [0, 2, 1]].astype(np.float32)
                expected_normals[:, :, 2] *= -1
                exported_normals = accessor(primitive['attributes']['NORMAL'])[f]
                normal_error = float(np.max(np.abs(expected_normals - exported_normals)))
                glb_normal_error = max(glb_normal_error, normal_error)
                # new_from_object re-encodes Blender's custom normals. Bound the
                # actual quantization, and independently require matching normals
                # between regions at every duplicated material-boundary vertex.
                assert normal_error < .001, (zone_id, 'GLB custom normals', normal_error)
                positions = accessor(primitive['attributes']['POSITION'])
                ns = accessor(primitive['attributes']['NORMAL'])
                for position, normal in zip(positions, ns):
                    glb_boundary_normals[(key, position.tobytes())].append((zone_id, normal))
                seen.append(zone_id)
                assert color['materials'][primitive['material']]['pbrMetallicRoughness']['baseColorFactor'] != material['pbrMetallicRoughness']['baseColorFactor']
            else:
                expected = before[key]['v'][before[key]['f']][:, :, [0, 2, 1]].astype(np.float32)
            expected[:, :, 2] *= -1
            # One pre-existing duplicate source face is deduplicated by exporter.
            actual_sig, expected_sig = util['signatures'](corners), util['signatures'](expected)
            if len(actual_sig) == len(expected_sig):
                assert np.array_equal(actual_sig, expected_sig), key
            else:
                assert key not in ['deltoid.left', 'deltoid.right']
                assert len(expected_sig) - len(actual_sig) == 1 and not len(np.setdiff1d(actual_sig, expected_sig))
    assert len(seen) == len(set(seen)) == 6
    glb_seam_error = 0.
    for entries in glb_boundary_normals.values():
        if len({zone_id for zone_id, _ in entries}) < 2:
            continue
        normals = np.array([n for _, n in entries])
        glb_seam_error = max(glb_seam_error, float(np.max(np.abs(normals - normals[0]))))
    assert glb_seam_error < 1e-6
    for filename in ['ecorche-p4-p5-zones.glb', 'ecorche-p4-p5-zones-controle.glb']:
        for material in list(bpy.data.materials):
            if material.name in mapping:
                material.name = 'PREVIOUS__' + material.name
        test = bpy.data.scenes.new('VERIFY_' + filename)
        bpy.context.window.scene = test
        bpy.ops.import_scene.gltf(filepath=str(root / filename), merge_vertices=False)
        meshes = [o for o in test.objects if o.type == 'MESH']
        assert len(meshes) == 300
        assert {s.material.name for o in meshes for s in o.material_slots if s.material.name in mapping} == set(mapping)
    report = {
        'baseline_commit': meta['baseline_commit'], 'geometry_reference_commit': meta['geometry_reference_commit'],
        'baseline_sha256': sha(args.baseline), 'master_sha256': sha(root / meta['master']),
        'all_298_other_objects_raw_geometry_materials_normals_unchanged': True,
        'head_P5_throat_body_unchanged': True, 'all_original_surface_vertices_unchanged': True,
        'original_cameras_and_five_lights_unchanged': True,
        'no_sculpting_or_surface_smoothing': True, 'topology_changed_only_on_two_deltoids': True,
        'six_independent_materials_and_neutral_reset_tested': True,
        'six_ids_primitives_and_materials_verified_in_GLBs': True,
        'neutral_control_geometry_buffers_identical': True, 'both_GLB_reimports_verified': True,
        'GLB_custom_corner_normals_verified': True,
        'GLB_custom_normal_export_max_component_error': glb_normal_error,
        'GLB_cross_material_boundary_normal_max_component_difference': glb_seam_error,
        'master_triangles': sum(len(r['f']) for r in after.values()),
        'extra_triangles': sum(len(after[k]['f']) - len(before[k]['f']) for k in before),
        'shoulders': checks, 'mobile_FPS_measured': False,
        'verifier_sha256': sha(Path(__file__)),
    }
    (root / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print('VERIFIED', json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
