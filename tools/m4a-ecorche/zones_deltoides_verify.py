"""Independent serialized Blender/GLB checks against approved 0ab3d83."""
import argparse
import ast
import hashlib
import json
import struct
import sys
from pathlib import Path

import bpy
import numpy as np


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def glb(path):
    raw = path.read_bytes()
    size = struct.unpack_from('<I', raw, 12)[0]
    doc, binary = json.loads(raw[20:20 + size]), raw[28 + size:]

    def accessor(index):
        ac = doc['accessors'][index]
        view = doc['bufferViews'][ac['bufferView']]
        width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[ac['type']]
        dtype = np.dtype({5126: '<f4', 5125: '<u4', 5123: '<u2'}[ac['componentType']])
        return np.ndarray((ac['count'], width), dtype=dtype, buffer=binary,
            offset=view.get('byteOffset', 0) + ac.get('byteOffset', 0),
            strides=(view.get('byteStride', width * dtype.itemsize), dtype.itemsize)).copy()

    return doc, binary, accessor


def signatures(corners):
    """Exact float32 coordinate signatures, independent of vertex/primitive order."""
    q = np.ascontiguousarray(corners, dtype='<f4')
    order = np.lexsort((q[:, :, 2], q[:, :, 1], q[:, :, 0]), axis=1)
    q = np.ascontiguousarray(np.take_along_axis(q, order[:, :, None], axis=1).reshape(len(q), -1))
    return np.sort(q.view(np.dtype([(f'c{i}', '<f4') for i in range(q.shape[1])])).ravel())


def face_components(faces):
    """Connectivity through common edges (not merely touching vertex tips)."""
    edge_faces = {}
    adj = [[] for _ in faces]
    for i, face in enumerate(faces):
        for a, b in zip(face, np.roll(face, -1)):
            key = tuple(sorted((int(a), int(b))))
            if key in edge_faces:
                j = edge_faces[key]
                adj[i].append(j)
                adj[j].append(i)
            else:
                edge_faces[key] = i
    unseen = set(range(len(faces)))
    sizes = []
    while unseen:
        stack = [unseen.pop()]
        size = 0
        while stack:
            i = stack.pop()
            size += 1
            for j in adj[i]:
                if j in unseen:
                    unseen.remove(j)
                    stack.append(j)
        sizes.append(size)
    return sorted(sizes, reverse=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--asset', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    root = args.asset.resolve()
    meta = json.loads((root / 'zones.json').read_text())
    assert sha(args.baseline) == meta['baseline_blend_sha256']
    # Reuse the independent byte fingerprint implementation, not the builder.
    helper = Path(__file__).with_name('guides_deltoides_verify.py')
    tree = ast.parse(helper.read_text())
    defs = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.Import, ast.ImportFrom))]
    ns = {}
    exec(compile(ast.Module(body=defs, type_ignores=[]), str(helper), 'exec'), ns)
    snapshot, fingerprint = ns['snapshot'], ns['fingerprint']

    before, lights_before = snapshot(args.baseline, meta['source_scene'])
    original_scene = bpy.context.scene
    cameras_before = {o.name: [list(map(list, o.matrix_world)), o.data.type, o.data.ortho_scale]
                      for o in original_scene.objects if o.type == 'CAMERA'}
    def world_signature(world):
        background = world.node_tree.nodes.get('Background')
        return [world.name, list(world.color),
                list(background.inputs['Color'].default_value),
                background.inputs['Strength'].default_value]

    world_before = world_signature(original_scene.world)
    after, lights_after = snapshot(root / meta['master'], meta['scene'])
    scene = bpy.context.scene
    assert before.keys() == after.keys() and len(after) == 300
    assert lights_before == lights_after
    cameras_after = {o.name: [list(map(list, o.matrix_world)), o.data.type, o.data.ortho_scale]
                     for o in scene.objects if o.type == 'CAMERA'}
    assert cameras_before == cameras_after
    assert world_before == world_signature(scene.world)
    checks = {}
    for key, old in before.items():
        new = after[key]
        assert np.array_equal(old['v'], new['v']), (key, 'vertices')
        assert np.array_equal(old['f'], new['f']), (key, 'topology')
        assert old['normals'] == new['normals'], (key, 'corner normals')
        assert old['modifiers'] == new['modifiers'], (key, 'modifiers')
        ob = next(o for o in scene.objects if o.type == 'MESH' and o['asset_id'] == key)
        if key in ['deltoid.right', 'deltoid.left']:
            labels = np.array([p.material_index for p in ob.data.polygons], dtype=np.int32)
            assert set(labels) == {0, 1, 2}
            # Compare all remaining raw attributes including shape keys and UVs.
            ob.data.polygons.foreach_set('material_index', np.zeros(len(labels), dtype=np.int32))
            raw = fingerprint(ob)
            ob.data.polygons.foreach_set('material_index', labels)
            assert raw == old['fingerprint'], (key, 'raw attributes excluding zone IDs')
            for slot in ob.material_slots:
                assert ns['material_signature'](slot.material)[1:] == old['materials'][0][1:]
            for rec in meta['regions']:
                if rec['object_asset_id'] != key:
                    continue
                ids = np.array(rec['source_polygon_indices'])
                assert np.array_equal(np.flatnonzero(labels == rec['material_slot']), ids)
                components = face_components(new['f'][ids])
                assert len(components) == 1, (rec['id'], components)
                rec['edge_connected_components'] = components
        else:
            assert old['fingerprint'] == new['fingerprint'], (key, 'raw attributes')
            assert old['materials'] == new['materials'], (key, 'material')
        checks[key] = {'vertices': len(new['v']), 'triangles': len(new['f']),
                       'evaluated_geometry_and_normals_exact': True,
                       'max_displacement_m': 0,
                       'raw_geometry_keys_groups_UV_fingerprint': old['fingerprint']}
    right, left = after['deltoid.right'], after['deltoid.left']
    reflected = right['v'].copy()
    reflected[:, 0] = 2 * meta['median_plane_x_m'] - reflected[:, 0]
    reflection_error = float(np.linalg.norm(reflected - left['v'], axis=1).max())
    assert reflection_error < 1e-7
    # Explicit test of independent material edits and exact neutral restoration.
    mats = [bpy.data.materials[r['material_name']] for r in meta['regions']]
    assert len({m.as_pointer() for m in mats}) == 6
    base = [list(m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value) for m in mats]
    for i, material in enumerate(mats):
        material.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = [.9, .25, .01, 1]
        for j, other in enumerate(mats):
            col = list(other.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value)
            assert (col != base[j]) if i == j else (col == base[j])
        material.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = base[i]
    assert all(list(m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value) == col
               for m, col in zip(mats, base))

    old_doc, _, old_ac = glb(args.baseline.with_suffix('.glb'))
    doc, binary, ac = glb(root / 'ecorche-p4-p5-zones.glb')
    colored, color_binary, _ = glb(root / 'ecorche-p4-p5-zones-controle.glb')
    assert binary == color_binary
    assert len(doc['nodes']) == len(old_doc['nodes']) == 300
    assert len(doc['materials']) == 7
    lookup = json.loads((root / 'selection-map.json').read_text())['zones']
    assert len(lookup) == 6
    old_nodes = {n['name']: n for n in old_doc['nodes']}
    exported_zones = []
    triangles = 0
    for node in doc['nodes']:
        key = node['name']
        original = old_nodes[key]
        for transform in ['matrix', 'translation', 'rotation', 'scale']:
            assert node.get(transform) == original.get(transform)
        def corners(document, accessor, n, normals=False):
            results = []
            for primitive in document['meshes'][n['mesh']]['primitives']:
                f = accessor(primitive['indices']).reshape(-1, 3)
                v = accessor(primitive['attributes']['POSITION'])
                if normals:
                    v = np.column_stack([v, accessor(primitive['attributes']['NORMAL'])])
                results.append(v[f])
            return np.concatenate(results)
        assert np.array_equal(signatures(corners(doc, ac, node)),
                              signatures(corners(old_doc, old_ac, original))), (key, 'GLB positions')
        assert np.array_equal(signatures(corners(doc, ac, node, True)),
                              signatures(corners(old_doc, old_ac, original, True))), (key, 'GLB normals')
        for pi, primitive in enumerate(doc['meshes'][node['mesh']]['primitives']):
            triangles += doc['accessors'][primitive['indices']]['count'] // 3
            if key not in ['deltoid.left', 'deltoid.right']:
                continue
            zone_id = primitive['extras']['zone_id']
            material = doc['materials'][primitive['material']]
            rec = lookup[zone_id]
            assert zone_id == material['extras']['zone_id'] == material['name']
            assert rec['primitive_index'] == pi and rec['node_name'] == key
            assert rec['material_index'] == primitive['material']
            ids = np.array(rec['blender_polygon_indices'])
            source_corners = after[key]['v'][after[key]['f'][ids]].astype(np.float32)
            source_corners = source_corners[:, :, [0, 2, 1]]
            source_corners[:, :, 2] *= -1  # Blender Z-up -> glTF Y-up
            exported = ac(primitive['attributes']['POSITION'])[ac(primitive['indices']).reshape(-1, 3)]
            assert np.array_equal(signatures(source_corners), signatures(exported)), zone_id
            color_mat = colored['materials'][primitive['material']]
            assert color_mat['pbrMetallicRoughness']['baseColorFactor'] != material['pbrMetallicRoughness']['baseColorFactor']
            exported_zones.append(zone_id)
    assert len(exported_zones) == len(set(exported_zones)) == 6
    # Reimport both serialized GLBs and recover independent regions by material name.
    imports = []
    for name in ['ecorche-p4-p5-zones.glb', 'ecorche-p4-p5-zones-controle.glb']:
        for material in list(bpy.data.materials):
            # Avoid Blender .001 suffixes in the independent import scene.
            if material.name in lookup:
                material.name = 'MASTER__' + material.name
        test = bpy.data.scenes.new('VERIFY_' + name)
        bpy.context.window.scene = test
        bpy.ops.import_scene.gltf(filepath=str(root / name), merge_vertices=False)
        meshes = [o for o in test.objects if o.type == 'MESH']
        assert len(meshes) == 300
        tri = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes)
        assert tri == triangles
        found = {slot.material.name for o in meshes for slot in o.material_slots
                 if slot.material and slot.material.name in lookup}
        assert found == set(lookup)
        imports.append({'file': name, 'mesh_objects': len(meshes), 'triangles': tri, 'zone_ids': sorted(found)})
    report = {
        'baseline_commit': meta['baseline_commit'], 'baseline_sha256': sha(args.baseline),
        'master_sha256': sha(root / meta['master']),
        'all_300_evaluated_surfaces_topology_normals_identical': True,
        'raw_coordinates_keys_groups_UV_and_matrices_identical': True,
        'only_material_assignment_changes_on_two_deltoids': True,
        'other_298_objects_and_materials_identical': True,
        'head_P5_throat_pecs_and_remaining_body_identical': True,
        'max_surface_vertex_displacement_m': 0, 'added_vertices': 0, 'added_triangles': 0,
        'topology_modified': False, 'silhouette_strictly_preserved': True,
        'no_new_holes_or_intersections_by_identical_geometry': True,
        'cameras_lights_world_identical': True,
        'original_deltoid_triangles_each': len(right['f']),
        'each_deltoid_face_assigned_exactly_once': True,
        'six_distinct_materials_color_isolation_and_neutral_reset_tested': True,
        'left_right_reflection_max_error_m': reflection_error,
        'regions': [{k: r[k] for k in ['id', 'triangles', 'edge_connected_components']} for r in meta['regions']],
        'master_triangles': sum(len(r['f']) for r in after.values()),
        'export_triangles': triangles, 'glb_geometry_and_normals_exactly_match_baseline_glb': True,
        'control_and_neutral_glb_geometry_buffers_identical': True,
        'stable_ids_survive_export_and_import': True, 'imports': imports,
        'anatomical_boundaries_status': 'Proposed superficial fitness regions; visual validation pending.',
        'mobile_fps_tested': False,
        'objects': checks, 'verifier_sha256': sha(Path(__file__)),
    }
    (root / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print('VERIFIED', json.dumps({k: v for k, v in report.items() if k != 'objects'}), flush=True)


if __name__ == '__main__':
    main()
