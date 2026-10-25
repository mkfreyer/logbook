"""Export the exact sixth-pass shape with stable source piece IDs, neutral matte PBR."""
import argparse,hashlib,json,struct,sys
from pathlib import Path
import bpy
p=argparse.ArgumentParser();p.add_argument('--asset',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.asset.resolve();meta=json.loads((root/'passe6.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(root/'ecorche-passe6.blend'),use_scripts=False);source=bpy.data.scenes['15_PASSE6_NEUTRE'];bpy.context.window.scene=source;source.view_layers[0].update();graph=bpy.context.evaluated_depsgraph_get();scene=bpy.data.scenes.new('PASSE6_EXPORT');count=0
for ob in source.objects:
 if ob.type!='MESH':continue
 mesh=bpy.data.meshes.new_from_object(ob.evaluated_get(graph),preserve_all_data_layers=True,depsgraph=graph);clone=bpy.data.objects.new('EXPORT__'+ob['asset_id'],mesh);scene.collection.objects.link(clone);clone.matrix_world=ob.matrix_world
 for slot in clone.material_slots:slot.link='OBJECT';slot.material=bpy.data.materials['PASSE3_MAT_NEUTRE']
 for key in ['asset_id','source_piece_id','side','region_hint','anatomical_label_validated','deltoid_regions','interactive_muscle_zone','role']:
  if key in ob:clone[key]=ob[key]
 count+=len(mesh.polygons)
bpy.context.window.scene=scene;file=root/'ecorche-passe6.glb'
bpy.ops.export_scene.gltf(filepath=str(file),export_format='GLB',use_selection=False,use_active_scene=True,export_animations=False,export_morph=False,export_extras=True,export_apply=False,export_yup=True,export_vertex_color='NONE',export_all_vertex_colors=False)
raw=file.read_bytes();size=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+size]);binary=raw[28+size:]
for node in doc['nodes']:
 if 'mesh'in node:node['name']=node['extras']['asset_id']
doc['asset']['copyright']='Body: Ecorche - Anatomy study — Beatriz Gomez Santamaria — CC BY 4.0. Head and eyeballs: Dan Ulrich / Blender Studio Human Base Meshes v1.4.1 — CC0. Adaptation Logbook: symmetric athletic body, sixth-pass compact P4-based deltoid reconstruction and rounded deltopectoral contact; validated P5 head, throat and remaining body unchanged.'
doc['asset']['extras']={'source':meta['source_asset']['extras']['source'],'source_author':meta['source_asset']['extras']['author'],'source_license':meta['source_asset']['extras']['license'],'source_sha256':meta['source_sha256'],'baseline_commit':meta['baseline_commit'],'modifications':'Sixth pass: P4-based shoulder envelope, removal of inherited deep sculpt troughs, three convex belly transitions without added incision, modest shoulder volume reduction, local deltopectoral approach and two locally reconstructed deltoid surfaces. P5 head, throat and all other body meshes unchanged; all earlier scenes preserved. No medical certification.','deltoid_weights':'Three overlapping authoring groups in Blender only, not separate anatomical segments or exported interactive masks.'}
doc['asset']['extras']['head_source']=meta['head_source']
encoded=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4)
result=struct.pack('<4sII',b'glTF',2,28+len(encoded)+len(binary))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(binary),0x004e4942)+binary;file.write_bytes(result)
actual=sum(doc['accessors'][p['indices']]['count']//3 for mesh in doc['meshes']for p in mesh['primitives'])
report={'file':file.name,'sha256':hashlib.sha256(result).hexdigest(),'bytes':len(result),'master_triangles':count,'exported_triangles':actual,'exporter_omitted_triangles':count-actual,'nodes':len(doc['nodes']),'meshes':len(doc['meshes']),'materials':len(doc['materials']),'material':'neutral matte PBR, identical parameters to the validation material','shape_keys_baked':True,'deltoid_authoring_weights_in_blender_only':True,'exporter_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(root/'export.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('PASSE6_EXPORTED',json.dumps(report),flush=True)
