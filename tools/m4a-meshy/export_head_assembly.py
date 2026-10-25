"""Export only the fitted scene and preserve source provenance and attribution."""
import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import bpy

p = argparse.ArgumentParser()
p.add_argument('--asset', type=Path, required=True)
a = p.parse_args(sys.argv[sys.argv.index('--')+1:])
root = a.asset.resolve()
meta = json.loads((root/'assemblage.json').read_text())
master = root/meta['master']
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(master) == meta['master_sha256']
bpy.ops.wm.open_mainfile(filepath=str(master), use_scripts=False)
scene = bpy.data.scenes[meta['scene_after']]
bpy.context.window.scene = scene
path = root/meta['export']
bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_active_scene=True,
    export_cameras=False, export_lights=False, export_animations=False,
    export_morph=False, export_extras=True, export_yup=True,
    export_vertex_color='NONE', export_all_vertex_colors=False)
helper = Path(__file__).parent.parent/'m4a-ecorche/zones_deltoides_export.py'
spec = importlib.util.spec_from_file_location('glb_codec', helper)
codec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(codec)
doc, binary = codec.read_glb(path)
for node in doc['nodes']:
    if 'mesh' in node:
        node['name'] = node['extras']['asset_id']
assert len(doc['meshes']) == 1
doc['asset']['copyright'] = 'Model created with Meshy – CC BY 4.0 License. Logbook adaptation: source Anatomical Form body preserved below the neck cut; '+meta.get('head_label', 'Rib Reach Exercise')+' head extracted, uniformly fitted and joined locally.'
doc['asset']['extras'] = {
    'source_generator': 'meshy-scene', 'license': 'CC-BY-4.0',
    'license_url': 'https://creativecommons.org/licenses/by/4.0/',
    'source_body': meta['body_filename_uploaded'], 'source_body_sha256': meta['body_source_sha256'],
    'source_head': meta['head_filename_uploaded'], 'source_head_sha256': meta['head_source_sha256'],
    'modifications': 'Only source head removed. Donor head uniformly fitted; local lower-head attachment and shared-ring connection. Retained source body vertices not moved. No muscle segmentation or app integration.',
    'body_cut_blender_z_m': meta['body_cut_z_m'],
    'head_uniform_scale': meta['head_scale_uniform'], 'head_translation_blender_m': meta['head_translation_m'],
    'master_sha256': meta['master_sha256'],
}
codec.write_glb(path, doc, binary)
assert sha(master) == meta['master_sha256']
report = {'file': path.name, 'bytes': path.stat().st_size, 'sha256': sha(path),
    'nodes': len(doc['nodes']), 'meshes': len(doc['meshes']),
    'materials': len(doc.get('materials', [])),
    'triangles': sum(doc['accessors'][p['indices']]['count']//3 for m in doc['meshes'] for p in m['primitives']),
    'textures': len(doc.get('textures', [])), 'attribution_embedded': True,
    'exporter_sha256': sha(Path(__file__))}
(root/'export.json').write_text(json.dumps(report, indent=2)+'\n')
print('EXPORTED', json.dumps(report), flush=True)
