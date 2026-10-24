"""Real Blender comparisons on identical cameras/lights; save the editable master rig."""
import argparse,json,math,hashlib,sys
from pathlib import Path
import bpy
from mathutils import Vector
def sha(b):return hashlib.sha256(b).hexdigest()
p=argparse.ArgumentParser();p.add_argument('--asset',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.asset.resolve();file=root/'ecorche-athletique.blend'
source=json.loads((root/'construction.json').read_text());plane=source['median_plane_x_m'];input_sha=sha(file.read_bytes())
bpy.ops.wm.open_mainfile(filepath=str(file),use_scripts=False)
scenes=[bpy.data.scenes[n]for n in ['00_SOURCE_ASYMETRIQUE','01_RECONSTRUCTION_SYMETRIQUE','02_ATHLETIQUE']];rig=bpy.data.collections.new('CAMERAS_ET_LUMIERES')
for s in scenes:s.collection.children.link(rig)
def aim(ob,target):ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,size,col in [('Key',(-2,-3,3),340,2.6,(.81,.88,1)),('Fill',(2.5,-2,1.3),140,2.5,(.56,.69,1)),('Rim',(1.6,2.3,2.8),340,2,(.58,.72,1)),('Back_fill',(-2,2,1.3),100,2.2,(.75,.82,1))]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=col;o=bpy.data.objects.new(name,d);rig.objects.link(o);o.location=loc;aim(o,(plane,0,.95))
cameras={}
for name,yaw,scale,target in [('face',0,2.05,(plane,0,.9)),('trois-quarts',-35,2.05,(plane,0,.9)),('dos',180,2.05,(plane,0,.9)),('profil',-90,2.05,(plane,0,.9)),('epaule-avant',-55,.46,(-.18,.06,1.40)),('epaule-arriere',-135,.46,(-.18,.06,1.40))]:
 d=bpy.data.cameras.new(name);d.type='ORTHO';d.ortho_scale=scale;o=bpy.data.objects.new('CAM_'+name,d);rig.objects.link(o);t=math.radians(yaw);o.location=Vector(target)+Vector((4*math.sin(t),-4*math.cos(t),0));aim(o,target);cameras[name]=o
world=bpy.data.worlds.new('BLEU_NUIT');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(.009,.019,.036,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.6
demo=bpy.data.scenes.new('03_SELECTION_PECTORAL_GAUCHE');demo.collection.children.link(rig)
orange=bpy.data.materials['PRESENTATION_BLEU_ARGENTE'].copy();orange.name='DEMO_SELECTION_ORANGE';orange.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(1,.085,.006,1)
for ob in scenes[2].objects:
 if ob.type!='MESH':continue
 clone=ob.copy();clone.name='DEMO__'+ob.name;demo.collection.objects.link(clone)
 if ob.name=='pectoralis_major.left':clone.material_slots[0].material=orange
scenes.append(demo)
for s in scenes:
 s.world=world;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=48;s.cycles.seed=0;s.cycles.use_denoising=False;s.view_settings.view_transform='AgX';s.render.image_settings.file_format='PNG'
frames=[(f'avant-{view}',0,view,(720,1152))for view in ['face','trois-quarts','dos','profil']]+[(f'apres-{view}',2,view,(720,1152))for view in ['face','trois-quarts','dos','profil']]+[('base-symetrique-trois-quarts',1,'trois-quarts',(720,1152)),('deltoide-avant',2,'epaule-avant',(1000,840)),('deltoide-arriere',2,'epaule-arriere',(1000,840)),('selection-pectorale',3,'trois-quarts',(720,1152))]
metadata={'input_blend_sha256':input_sha,'renderer_sha256':sha(Path(__file__).read_bytes()),'samples':48,'engine':'CYCLES_CPU','geometry_edited_by_renderer':False,'frames':[]}
for name,index,cam,res in frames:
 s=scenes[index];s.camera=cameras[cam];s.render.resolution_x,s.render.resolution_y=res;s.render.resolution_percentage=100;path=root/'renders'/(name+'.png');s.render.filepath=str(path);bpy.ops.render.render(write_still=True,scene=s.name)
 metadata['frames'].append({'file':path.name,'scene':s.name,'camera':cam,'size':list(res),'sha256':sha(path.read_bytes())});(root/'renders/metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
for s in scenes:s.camera=cameras['trois-quarts'];s.render.resolution_x=720;s.render.resolution_y=1152
bpy.context.window.scene=scenes[2];bpy.ops.wm.save_as_mainfile(filepath=str(file),compress=True)
metadata['final_blend_sha256']=sha(file.read_bytes());(root/'renders/metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
print('ANATOMY_RENDERS_DONE',len(frames),flush=True)
