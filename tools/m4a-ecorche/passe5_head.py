"""Extract only the CC0 realistic animation head and eyeballs from the audited bundle."""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy,bmesh,numpy as np
p=argparse.ArgumentParser();p.add_argument('--bundle',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.output.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(a.bundle)=='3c121505651140ceb4d69fd1d8923f7788ffadd81672f5be14845a5f2c75c137'
bpy.ops.wm.open_mainfile(filepath=str(a.bundle.resolve()),use_scripts=False);collection=bpy.data.collections['Head (Animation) - Realistic'];assert collection.asset_data.license=='CC0';g=bpy.context.evaluated_depsgraph_get();arrays={};rows=[]
for o in collection.all_objects:
 if o.type!='MESH'or '.iris.'in o.name:continue
 # Multires level one contains sufficient eyelid/lip/ear shape for this master.
 for modifier in o.modifiers:
  if modifier.type=='MULTIRES':modifier.levels=1;modifier.render_levels=1
 bpy.context.view_layer.update();m=bpy.data.meshes.new_from_object(o.evaluated_get(g),depsgraph=g);bm=bmesh.new();bm.from_mesh(m);bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(m);bm.free()
 v=np.array([o.matrix_world@x.co for x in m.vertices]);f=np.array([q.vertices[:]for q in m.polygons],int)
 v[:,0]=.002114987923242599+.9*(v[:,0]-1.462569)
 v[:,1]=.9*v[:,1]+.075;v[:,2]=1.8+.972*(v[:,2]-.8803073763847351)
 key='head'if o.name=='GEO-head_animation_realistic'else'eye.'+o.name[-1].lower();arrays[key+'__v']=v;arrays[key+'__f']=f;rows.append({'key':key,'source_object':o.name,'triangles':len(f),'bbox_m':[v.min(0).tolist(),v.max(0).tolist()]})
np.savez_compressed(a.output/'head-donor.npz',**arrays)
metadata={'source_url':'https://download.blender.org/demo/asset-bundles/human-base-meshes/human-base-meshes-bundle-v1.4.1.zip','bundle_blend_sha256':sha(a.bundle),'source_collection':collection.name,'author':collection.asset_data.author,'license':collection.asset_data.license,'embedded_readme':bpy.data.texts['README'].as_string(),'objects':rows,'fit':'XY scale 0.9, Z scale 0.972 to align chin and occiput to the fixed cervical attachments; cranial top at 1.8 m; X center fitted to mannequin midplane, Y offset +0.075 m to align the occipital attachment without moving the validated neck.','selected_source_only':True,'rain_rig_used':False,'multires_level':1,'builder_sha256':sha(Path(__file__)),'donor_sha256':sha(a.output/'head-donor.npz')}
(a.output/'head-donor.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n');print('PASSE5_HEAD_EXTRACTED',json.dumps(metadata),flush=True)
