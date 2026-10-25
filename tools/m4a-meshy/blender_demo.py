"""Create an editable Blender material-mask demonstration of the exact Meshy GLB."""
import argparse,json,math,sys
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mesh_io import EXPECTED_SHA,load_glb,sha
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--regions',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--samples',type=int,default=96);p.add_argument('--preview',action='store_true')
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.output.mkdir(parents=True,exist_ok=True)
raw,doc,v,ix=load_glb(a.source);assert sha(raw)==EXPECTED_SHA
regions=json.loads(a.regions.read_text());labels=np.frombuffer((a.regions.parent/regions['labels']['file']).read_bytes(),dtype=np.uint8)
assert sha(labels.tobytes())==regions['labels']['sha256'] and len(labels)==len(ix)
for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
for m in list(bpy.data.meshes):
 if m.users==0:bpy.data.meshes.remove(m)
main=bpy.context.scene;main.name='00_NEUTRE'
for c in list(main.collection.children):main.collection.children.unlink(c)
rig=bpy.data.collections.new('CAMERAS_LUMIERES');main.collection.children.link(rig)
mesh=bpy.data.meshes.new('MESHY_GEOMETRIE_INTACTE');mesh.from_pydata(v.tolist(),[],ix.tolist());mesh.update()
base=(.19,.28,.42,1);orange=(1,.18,.025,1)
def material(name,col):
 m=bpy.data.materials.new(name);m.diffuse_color=col;m.use_nodes=True;n=m.node_tree.nodes.get('Principled BSDF')
 n.inputs['Base Color'].default_value=col;n.inputs['Roughness'].default_value=.37;n.inputs['Metallic'].default_value=.12;n.inputs['Coat Weight'].default_value=.08;return m
blue=[material(name,base) for name in ['00_unassigned','01_pectoralis.left','02_pectoralis.right','03_deltoid.left']];selected=material('ORANGE_SELECTION',orange)
for mat in blue:mesh.materials.append(mat)
for f in mesh.polygons:f.use_smooth=True;f.material_index=int(labels[f.index])
for name,values in [('source_triangle_index',np.arange(len(ix),dtype=np.int32)),('muscle_zone',labels.astype(np.int32))]:
 attr=mesh.attributes.new(name,'INT','FACE');attr.data.foreach_set('value',values)
scenes=[];objects=[]
for index,name in enumerate(['00_NEUTRE','01_PECTORAL_GAUCHE','02_PECTORAL_DROIT','03_DELTOIDE_GAUCHE','04_CONTROLE_REGIONS']):
 scene=main if index==0 else bpy.data.scenes.new(name)
 if index:scene.collection.children.link(rig)
 ob=bpy.data.objects.new('MESHY__'+name,mesh);scene.collection.objects.link(ob);ob.rotation_euler[0]=math.pi/2
 ob['source_glb_sha256']=EXPECTED_SHA;ob['region_binding']='Source mesh 0 / primitive 0 / original triangle ordinal';ob['geometry_changed']=False
 for i,slot in enumerate(ob.material_slots):slot.link='OBJECT';slot.material=blue[i]
 if 1<=index<=3:ob.material_slots[index].material=selected
 if index==4:
  ob.material_slots[1].material=selected
  ob.material_slots[2].material=material('DIAGNOSTIC_PEC_DROIT',(.9,.65,.03,1))
  ob.material_slots[3].material=material('DIAGNOSTIC_DELTOIDE_GAUCHE',(.02,.75,.7,1))
 scene['selection_region']=index if index<=3 else -1;scenes.append(scene);objects.append(ob)

def aim(ob,t):ob.rotation_euler=(Vector(t)-ob.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,size,color in [('Key',(-2,-3,3),320,3,(.81,.88,1)),('Fill',(2.5,-2,1.3),150,2.5,(.56,.69,1)),('Rim',(1.6,2.3,2.8),320,2,(.58,.72,1)),('Back fill',(-2,2,1.3),80,2.5,(.75,.82,1))]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color
 o=bpy.data.objects.new(name,d);rig.objects.link(o);o.location=loc;aim(o,(0,0,.25))
cameras={}
for name,yaw,scale,target in [('FACE',0,2.15,(0,0,0)),('TROIS_QUARTS',35,2.15,(0,0,0)),('DETAIL_FACE',0,.68,(0,0,.515)),('DETAIL_TROIS_QUARTS',35,.68,(.03,0,.515)),('CONTROLE_DOS',145,.68,(.06,0,.515)),('CONTROLE_PROFIL',90,.68,(.06,0,.515))]:
 d=bpy.data.cameras.new(name);d.type='ORTHO';d.ortho_scale=scale;o=bpy.data.objects.new('CAM_'+name,d);rig.objects.link(o)
 theta=math.radians(yaw);o.location=(4*math.sin(theta),-4*math.cos(theta),target[2]);aim(o,target);cameras[name]=o
world=bpy.data.worlds.new('FOND_BLEU_NUIT');world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.009,.019,.036,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.6
for scene in scenes:
 scene.world=world;scene.camera=cameras['FACE'];scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=a.samples;scene.cycles.seed=0;scene.cycles.use_denoising=False
 scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG'
bpy.data.texts.new('REGIONS.json').write(json.dumps(regions,ensure_ascii=False,indent=2))
bpy.data.texts.new('LIRE_AVANT_MODIFICATION.txt').write('Source Meshy intacte, glTF Y-up -> Blender Z-up par rotation objet +90 deg X.\nUn seul datablock mesh partage entre cinq scenes.\nLes trois IDs sont 1 pectoralis.left, 2 pectoralis.right, 3 deltoid.left; 0 non attribue.\nLes material_index de faces sont les masques editables; source_triangle_index conserve les indices originaux.\nNe pas exporter les attributs Blender en les supposant presents dans un GLB : utiliser le GLB source + regions.json + triangle-regions.u8, ou reconstruire la liaison apres tout reindexage.\n')
if a.preview:
 frames=[('pectoraux',1,'DETAIL_FACE',(900,760)),('trois-quarts',4,'DETAIL_TROIS_QUARTS',(900,760)),('dos',4,'CONTROLE_DOS',(900,760)),('profil',4,'CONTROLE_PROFIL',(900,760))]
else:frames=[('front',0,'FACE',(720,1152)),('three-quarter',0,'TROIS_QUARTS',(720,1152)),('selection',1,'TROIS_QUARTS',(720,1152)),('detail',4,'DETAIL_TROIS_QUARTS',(1000,840)),('detail-profile',4,'CONTROLE_PROFIL',(1000,840))]
metadata={'source_sha256':EXPECTED_SHA,'regions_sha256':sha(a.regions.read_bytes()),'renderer_sha256':sha(Path(__file__).read_bytes()),'blender':bpy.app.version_string,'engine':'CYCLES_CPU','samples':a.samples,'seed':0,'geometry_changed':False,'image_synthesis':False,'source_positions_sha256':sha(v.astype('<f4').tobytes()),'source_indices_sha256':sha(ix.astype('<u4').tobytes()),'material_base_linear':list(base),'roughness':.37,'metallic':.12,'axis_conversion':'Object +90 degrees X only; local source positions and face order untouched.','frames':[]}
for name,idx,cam,res in frames:
 scene=scenes[idx];scene.camera=cameras[cam];scene.render.resolution_x,scene.render.resolution_y=res;scene.render.resolution_percentage=100
 path=a.output/(name+'.png');scene.render.filepath=str(path.resolve());bpy.ops.render.render(write_still=True,scene=scene.name)
 metadata['frames'].append({'file':path.name,'scene':scene.name,'camera':cam,'size':res,'ortho_scale':scene.camera.data.ortho_scale,'selection_region':scene['selection_region'],'sha256':sha(path.read_bytes())})
 (a.output/'render-metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
for scene in scenes:scene.camera=cameras['FACE'];scene.render.resolution_x=720;scene.render.resolution_y=1152
bpy.context.window.scene=main
bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT');objects[0].select_set(True);main.view_layers[0].objects.active=objects[0]
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   s=area.spaces.active;s.shading.type='SOLID';s.shading.color_type='MATERIAL';s.overlay.show_floor=False;s.region_3d.view_location=(0,0,0);s.region_3d.view_rotation=cameras['FACE'].rotation_euler.to_quaternion();s.region_3d.view_distance=3;s.region_3d.view_perspective='ORTHO'
bpy.ops.wm.save_as_mainfile(filepath=str((a.output/'meshy-masques.blend').resolve()),compress=True)
metadata['blend_file']='meshy-masques.blend';metadata['blend_sha256']=sha((a.output/'meshy-masques.blend').read_bytes())
(a.output/'render-metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
print('MESHY_RENDER_DONE',len(v),len(ix),flush=True)
