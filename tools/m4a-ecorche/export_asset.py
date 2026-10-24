"""Bake current authoring shape keys into an independent GLB export scene."""
import argparse,json,struct,hashlib,sys
from pathlib import Path
import bpy
p=argparse.ArgumentParser();p.add_argument('--asset',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.asset.resolve();bpy.ops.wm.open_mainfile(filepath=str(root/'ecorche-athletique.blend'),use_scripts=False)
meta=json.loads((root/'construction.json').read_text());source=bpy.data.scenes['02_ATHLETIQUE'];bpy.context.window.scene=source;source.view_layers[0].update();graph=bpy.context.evaluated_depsgraph_get()
scene=bpy.data.scenes.new('EXPORT_GLTF');count=0;zero_area=0
for ob in source.objects:
 if ob.type!='MESH':continue
 evaluated=ob.evaluated_get(graph);mesh=bpy.data.meshes.new_from_object(evaluated,preserve_all_data_layers=True,depsgraph=graph)
 name=ob.name;ob.name='AUTHORING__'+name
 clone=bpy.data.objects.new(name,mesh);scene.collection.objects.link(clone);clone.matrix_world=ob.matrix_world
 for i,slot in enumerate(clone.material_slots):slot.link='OBJECT';slot.material=ob.material_slots[i].material
 for key in ['source_piece_id','side','region_hint','anatomical_label_validated']:
  if key in ob:clone[key]=ob[key]
 count+=len(mesh.polygons);zero_area+=sum(p.area<1e-16 for p in mesh.polygons)
bpy.context.window.scene=scene;file=root/'ecorche-athletique.glb'
bpy.ops.export_scene.gltf(filepath=str(file),export_format='GLB',use_selection=False,use_active_scene=True,export_animations=False,export_morph=False,export_extras=True,export_apply=False,export_yup=True,export_vertex_color='NONE',export_all_vertex_colors=False)
raw=file.read_bytes();size=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+size]);binary=raw[28+size:]
doc['asset']['copyright']='Ecorche - Anatomy study — Beatriz Gomez Santamaria — CC BY 4.0. Symmetric reconstruction and muscular-volume retouch for Logbook.'
doc['asset']['extras']={'source':meta['source_asset']['extras']['source'],'source_author':meta['source_asset']['extras']['author'],'source_license':meta['source_asset']['extras']['license'],'source_sha256':meta['source_sha256'],'source_generator':meta['source_asset']['generator'],'modifications':'Reconstruction from anatomical right side, median adjustments, tapered muscle-belly retouch, uniform 1.8 m height normalization. Geometric component names are not a validated anatomical atlas.'}
encoded=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4)
result=struct.pack('<4sII',b'glTF',2,28+len(encoded)+len(binary))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(binary),0x004e4942)+binary;file.write_bytes(result)
actual=sum(doc['accessors'][p['indices']]['count']//3 for mesh in doc['meshes'] for p in mesh['primitives'])
report={'sha256':hashlib.sha256(result).hexdigest(),'file':file.name,'bytes':len(result),'evaluated_master_triangles':count,'exported_triangles':actual,'exporter_omitted_triangles':count-actual,'master_near_zero_area_triangles':zero_area,'nodes':len(doc['nodes']),'meshes':len(doc['meshes']),'materials':len(doc['materials']),'shape_keys_baked_not_exported':True,'source_vertex_colors_in_master_only':True,'author_credit_preserved':True,'exporter_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'note':'Separate authoring pieces preserved; mobile optimization and complete anatomical naming remain future work. Vertex colors omitted from GLB to prevent source red colors multiplying the blue presentation material.'}
(root/'export.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('ANATOMY_GLB_EXPORTED',json.dumps(report),flush=True)
