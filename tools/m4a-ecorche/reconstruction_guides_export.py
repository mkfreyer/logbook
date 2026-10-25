"""Export only the 300 evaluated mannequin pieces; no cameras or guides."""
import argparse,hashlib,json,struct,sys
from pathlib import Path
import bpy

p=argparse.ArgumentParser();p.add_argument('--asset',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.asset.resolve()
meta=json.loads((root/'reconstruction.json').read_text())
prior=json.loads((root.parent/'ecorche-beatriz-combinaison-p4-p5/combinaison.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(root/meta['master']),use_scripts=False)
source=bpy.data.scenes[meta['scene']];bpy.context.window.scene=source;source.view_layers[0].update()
graph=bpy.context.evaluated_depsgraph_get();scene=bpy.data.scenes.new('RECONSTRUCTION_EXPORT');count=0
for ob in source.objects:
    if ob.type!='MESH':continue
    mesh=bpy.data.meshes.new_from_object(ob.evaluated_get(graph),preserve_all_data_layers=True,depsgraph=graph)
    clone=bpy.data.objects.new('EXPORT__'+ob['asset_id'],mesh);scene.collection.objects.link(clone)
    clone.matrix_world=ob.matrix_world
    for slot in clone.material_slots:slot.link,slot.material='OBJECT',bpy.data.materials['PASSE3_MAT_NEUTRE']
    for key in ['asset_id','source_piece_id','side','region_hint','anatomical_label_validated',
                'interactive_muscle_zone','role']:
        if key in ob:clone[key]=ob[key]
    count+=sum(len(poly.vertices)-2 for poly in mesh.polygons)
bpy.context.window.scene=scene;path=root/'reconstruction-guides.glb'
bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=False,
    use_active_scene=True,export_animations=False,export_morph=False,export_extras=True,
    export_apply=False,export_yup=True,export_vertex_color='NONE',export_all_vertex_colors=False)
raw=path.read_bytes();size=struct.unpack_from('<I',raw,12)[0]
doc=json.loads(raw[20:20+size]);binary=raw[28+size:]
for node in doc['nodes']:
    if 'mesh' in node:node['name']=node['extras']['asset_id']
doc['asset']['copyright']=(
    'Body: Ecorche - Anatomy study — Beatriz Gomez Santamaria — CC BY 4.0. '
    'Head/eyes: Dan Ulrich / Blender Studio Human Base Meshes v1.4.1 — CC0. '
    'Logbook adaptation: P4 athletic body with P5 head and reconstructed throat; '
    'local reconstruction and densification of two deltoid grooves from validated 0fc6f0b guides. '
    'Central belly, global support silhouette and all 298 other objects preserved. No interactive segmentation.')
doc['asset']['extras']={'source':prior['source_asset']['extras']['source'],
    'source_author':prior['source_asset']['extras']['author'],'source_license':'CC-BY-4.0',
    'source_sha256':prior['source_sha256'],'baseline_commit':meta['reference_commit'],
    'guides_commit':meta['guides_commit'],'head_source':prior['head_source'],
    'modifications':'Local deltoid topology densification, old trough floor reconstruction and rounded blue-guide troughs; rest unchanged.',
    'validation_status':'INSUFFISANT_NON_VALIDE: 7 self-intersections per deltoid and residual border marks. Keep baseline 0ab3d83. Do not integrate.',
    'segmentation_status':'300 piece IDs retained; no independently selectable deltoid heads or new masks.'}
encoded=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4)
result=(struct.pack('<4sII',b'glTF',2,28+len(encoded)+len(binary))
        +struct.pack('<II',len(encoded),0x4e4f534a)+encoded
        +struct.pack('<II',len(binary),0x004e4942)+binary)
path.write_bytes(result)
actual=sum(doc['accessors'][p['indices']]['count']//3 for mesh in doc['meshes']for p in mesh['primitives'])
report={'file':path.name,'sha256':hashlib.sha256(result).hexdigest(),'bytes':len(result),
        'master_triangles':count,'exported_triangles':actual,'exporter_omitted_triangles':count-actual,
        'nodes':len(doc['nodes']),'meshes':len(doc['meshes']),'materials':len(doc['materials']),
        'no_guides_or_application_code':True}
(root/'export.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('EXPORTED',json.dumps(report),flush=True)
