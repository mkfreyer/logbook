"""Export the local presentation proposal, preserving the six deltoid primitives."""
import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import bpy


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--asset', type=Path, required=True)
    a = p.parse_args(sys.argv[sys.argv.index('--')+1:])
    root = a.asset.resolve()
    meta = json.loads((root/'finition.json').read_text())
    helper = Path(__file__).with_name('zones_deltoides_export.py')
    spec = importlib.util.spec_from_file_location('glb_codec', helper)
    codec = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(codec)
    baseline = root.parent/'ecorche-beatriz-anatomie-deltoides'
    old_doc, _ = codec.read_glb(baseline/'ecorche-p4-p5-zones.glb')
    prior_map = json.loads((baseline/'selection-map.json').read_text())
    bpy.ops.wm.open_mainfile(filepath=str(root/meta['master']), use_scripts=False)
    source = bpy.data.scenes[meta['scene']]
    bpy.context.window.scene = source
    source.view_layers[0].update()
    graph = bpy.context.evaluated_depsgraph_get()
    scene = bpy.data.scenes.new('EXPORT_FINITION_AINE')
    for ob in source.objects:
        if ob.type != 'MESH':
            continue
        mesh = bpy.data.meshes.new_from_object(ob.evaluated_get(graph),
                    preserve_all_data_layers=True, depsgraph=graph)
        clone = bpy.data.objects.new('EXPORT__'+ob['asset_id'], mesh)
        scene.collection.objects.link(clone)
        clone.matrix_world = ob.matrix_world
        for i, slot in enumerate(ob.material_slots):
            clone.material_slots[i].link = 'OBJECT'
            clone.material_slots[i].material = slot.material
        for key in ob.keys():
            clone[key] = ob[key]
    bpy.context.window.scene = scene
    path = root/'ecorche-finition-aine.glb'
    bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_selection=False,
        use_active_scene=True, export_animations=False, export_morph=False,
        export_extras=True, export_apply=False, export_yup=True,
        export_vertex_color='NONE', export_all_vertex_colors=False)
    doc, binary = codec.read_glb(path)
    mapping = {}
    for ni, node in enumerate(doc['nodes']):
        if 'mesh' not in node:
            continue
        node['name'] = node['extras']['asset_id']
        if not node['name'].startswith('deltoid.'):
            continue
        for pi, primitive in enumerate(doc['meshes'][node['mesh']]['primitives']):
            mat = doc['materials'][primitive['material']]
            zone = mat['name']
            assert zone in prior_map['zones']
            mat.setdefault('extras', {})['zone_id'] = zone
            primitive.setdefault('extras', {})['zone_id'] = zone
            mapping[zone] = {**prior_map['zones'][zone], 'node_index': ni,
                            'mesh_index': node['mesh'], 'primitive_index': pi,
                            'material_index': primitive['material']}
    assert set(mapping) == set(prior_map['zones'])
    doc['asset'] = old_doc['asset'].copy()
    doc['asset']['copyright'] = (
        'Body: Ecorche - Anatomy study — Beatriz Gomez Santamaria — CC BY 4.0. '
        'Head/eyes: Dan Ulrich / Blender Studio Human Base Meshes v1.4.1 — CC0. '
        'Logbook adaptation: P4 deltoids, P5 head, deltoid region partition; '
        'local neutral groin presentation envelope; 298 original meshes unchanged from d79692f; two central pieces replaced.')
    doc['asset']['extras'] = {**old_doc['asset'].get('extras', {}),
        'baseline_commit': meta['baseline_commit'],
        'modifications': 'Two exposed central groin pieces replaced by one closed neutral envelope; 298 other objects unchanged.',
        'presentation_surface_id': meta['added_object'],
        'presentation_surface_is_training_muscle': False,
        'deltoid_partition_inherited_without_changes': 'd79692f',
        'master_sha256': meta['master_sha256']}
    codec.write_glb(path, doc, binary)
    (root/'selection-map.json').write_text(json.dumps({
        **prior_map, 'baseline_commit': meta['baseline_commit'],
        'neutral_asset': path.name, 'control_asset': None, 'zones': mapping,
        'excluded_from_training_selection': [meta['added_object']],
    }, indent=2)+'\n')
    report = {
        'file': path.name, 'bytes': path.stat().st_size,
        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'nodes': len(doc['nodes']), 'meshes': len(doc['meshes']),
        'materials': len(doc['materials']),
        'primitives': sum(len(m['primitives']) for m in doc['meshes']),
        'triangles': sum(doc['accessors'][p['indices']]['count']//3
                         for m in doc['meshes'] for p in m['primitives']),
        'selection_zone_ids': sorted(mapping), 'textures_added': 0,
        'shape_keys_baked_at_existing_values': True,
        'exporter_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (root/'export.json').write_text(json.dumps(report, indent=2)+'\n')
    print('EXPORTED', json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
