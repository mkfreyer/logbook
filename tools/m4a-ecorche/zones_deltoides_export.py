"""GLB asset exports with six independent materials and stable primitive IDs."""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

import bpy


def read_glb(path):
    raw = path.read_bytes()
    size = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20 + size]), raw[28 + size:]


def write_glb(path, doc, binary):
    encoded = json.dumps(doc, ensure_ascii=False, separators=(',', ':')).encode()
    encoded += b' ' * ((-len(encoded)) % 4)
    path.write_bytes(struct.pack('<4sII', b'glTF', 2, 28 + len(encoded) + len(binary))
                     + struct.pack('<II', len(encoded), 0x4e4f534a) + encoded
                     + struct.pack('<II', len(binary), 0x004e4942) + binary)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--asset', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    root = args.asset.resolve()
    meta = json.loads((root / 'zones.json').read_text())
    prior = json.loads((root.parent / 'ecorche-beatriz-combinaison-p4-p5/combinaison.json').read_text())
    bpy.ops.wm.open_mainfile(filepath=str(root / meta['master']), use_scripts=False)
    source = bpy.data.scenes[meta['scene']]
    bpy.context.window.scene = source
    source.view_layers[0].update()
    graph = bpy.context.evaluated_depsgraph_get()
    scene = bpy.data.scenes.new('EXPORT_ZONES_P4')
    for ob in source.objects:
        if ob.type != 'MESH':
            continue
        mesh = bpy.data.meshes.new_from_object(ob.evaluated_get(graph),
                    preserve_all_data_layers=True, depsgraph=graph)
        clone = bpy.data.objects.new('EXPORT__' + ob['asset_id'], mesh)
        scene.collection.objects.link(clone)
        clone.matrix_world = ob.matrix_world
        for i, slot in enumerate(ob.material_slots):
            clone.material_slots[i].link = 'OBJECT'
            clone.material_slots[i].material = slot.material
        for key in ['asset_id', 'source_piece_id', 'side', 'region_hint',
                    'anatomical_label_validated', 'interactive_muscle_zone', 'role',
                    'selection_regions', 'anatomical_boundaries_validated']:
            if key in ob:
                clone[key] = ob[key]
    bpy.context.window.scene = scene
    path = root / 'ecorche-p4-p5-zones.glb'
    bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_selection=False,
        use_active_scene=True, export_animations=False, export_morph=False,
        export_extras=True, export_apply=False, export_yup=True,
        export_vertex_color='NONE', export_all_vertex_colors=False)
    doc, binary = read_glb(path)
    regions = {r['id']: r for r in meta['regions']}
    mapping = {}
    for ni, node in enumerate(doc['nodes']):
        if 'mesh' not in node:
            continue
        node['name'] = node['extras']['asset_id']
        if not node['name'].startswith('deltoid.'):
            continue
        primitives = doc['meshes'][node['mesh']]['primitives']
        assert len(primitives) == 3
        for pi, primitive in enumerate(primitives):
            material = doc['materials'][primitive['material']]
            zone_id = material['name']
            assert zone_id in regions
            material.setdefault('extras', {})['zone_id'] = zone_id
            primitive.setdefault('extras', {})['zone_id'] = zone_id
            mapping[zone_id] = {
                'node_index': ni, 'node_name': node['name'], 'mesh_index': node['mesh'],
                'primitive_index': pi, 'material_index': primitive['material'],
                'material_name': zone_id,
                'triangles': doc['accessors'][primitive['indices']]['count'] // 3,
                'blender_polygon_indices': regions[zone_id]['source_polygon_indices'],
            }
    assert set(mapping) == set(regions)
    doc['asset']['copyright'] = (
        'Body: Ecorche - Anatomy study — Beatriz Gomez Santamaria — CC BY 4.0. '
        'Head/eyes: Dan Ulrich / Blender Studio Human Base Meshes v1.4.1 — CC0. '
        'Logbook adaptation: exact P4 deltoids, P5 head and approved throat/body; '
        'six functional deltoid surface regions, materials only, no geometric changes.')
    doc['asset']['extras'] = {
        'source': prior['source_asset']['extras']['source'],
        'source_author': prior['source_asset']['extras']['author'],
        'source_license': 'CC-BY-4.0', 'source_sha256': prior['source_sha256'],
        'head_source': prior['head_source'], 'baseline_commit': meta['baseline_commit'],
        'modifications': 'Six independent deltoid materials; geometry identical to approved 0ab3d83.',
        'segmentation_status': 'Functional surface regions proposed for visual validation; not medical certification.',
        'selection_zone_ids': sorted(mapping),
    }
    write_glb(path, doc, binary)
    # Same buffers, same regions; only base color factors change for visual control.
    neutral_factors = {}
    for zone_id, rec in mapping.items():
        material = doc['materials'][rec['material_index']]
        neutral_factors[zone_id] = material['pbrMetallicRoughness']['baseColorFactor'][:]
        material['pbrMetallicRoughness']['baseColorFactor'] = regions[zone_id]['control_color_rgba_linear']
    control = root / 'ecorche-p4-p5-zones-controle.glb'
    write_glb(control, doc, binary)
    (root / 'selection-map.json').write_text(json.dumps({
        'schema_version': 1, 'baseline_commit': meta['baseline_commit'],
        'neutral_asset': path.name, 'control_asset': control.name,
        'coordinate_system': 'glTF Y up; anatomical sides refer to model, not viewer',
        'lookup_priority': 'material.extras.zone_id or material.name; primitive.extras.zone_id fallback',
        'threejs_note': 'Multi-primitive GLTFLoader meshes may become child meshes: '
                        'resolve each hit child material via extras.zone_id/name, not global faceIndex. '
                        'Primitive extras availability depends on loader; use material ID as primary key.',
        'neutral_base_color_by_zone': neutral_factors,
        'zones': mapping,
    }, indent=2) + '\n')
    report = {'files': [{'name': p.name, 'bytes': p.stat().st_size,
                        'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                       for p in [path, control]],
              'nodes': len(doc['nodes']), 'meshes': len(doc['meshes']),
              'materials': len(doc['materials']),
              'primitives': sum(len(m['primitives']) for m in doc['meshes']),
              'triangles': sum(doc['accessors'][p['indices']]['count'] // 3
                              for m in doc['meshes'] for p in m['primitives']),
              'independent_zone_materials': len(mapping),
              'shape_keys_baked_at_approved_values': True,
              'no_textures_added': True,
              'exporter_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (root / 'export.json').write_text(json.dumps(report, indent=2) + '\n')
    print('EXPORTED', json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
