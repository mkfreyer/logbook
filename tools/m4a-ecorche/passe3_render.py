"""Matched neutral matte views with physically symmetric white area lights."""
import argparse,hashlib,json,math,sys
from pathlib import Path
import bpy
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--asset',type=Path,required=True);p.add_argument('--preview',type=Path);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.asset.resolve();file=root/'ecorche-passe3.blend';out=a.preview.resolve()if a.preview else root/'renders';out.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
input_sha=sha(file);meta=json.loads((root/'passe3.json').read_text());plane=meta['median_plane_x_m'];bpy.ops.wm.open_mainfile(filepath=str(file),use_scripts=False);before=bpy.data.scenes['07_AVANT_PASSE3'];after=bpy.data.scenes['08_PASSE3_NEUTRE'];rig=bpy.data.collections.new('PASSE3_LUMIERES_SYMETRIQUES')
for s in [before,after]:s.collection.children.link(rig)
def aim(ob,target):ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
lights=[]
for label,x,y,z,power,size in [('Avant',3,-3,2.6,200,2.2),('Dos',2,3,3,180,2.2)]:
 for side in [-1,1]:
  light=bpy.data.lights.new(f'P3_{label}_{side}','AREA');light.energy=power;light.shape='DISK';light.size=size;light.color=(1,1,1);ob=bpy.data.objects.new(light.name,light);rig.objects.link(ob);ob.location=(plane+side*x,y,z);aim(ob,(plane,0,1));lights.append({'name':ob.name,'location':list(ob.location),'energy':power,'size':size})
light=bpy.data.lights.new('P3_Centre','AREA');light.energy=100;light.shape='DISK';light.size=2;ob=bpy.data.objects.new(light.name,light);rig.objects.link(ob);ob.location=(plane,-4,4);aim(ob,(plane,0,1));lights.append({'name':ob.name,'location':list(ob.location),'energy':100,'size':2})
cameras={}
views=[('face',0,2.05,(plane,0,.9),(720,1152)),('profil',-90,2.05,(plane,0,.9),(720,1152)),('dos',180,2.05,(plane,0,.9),(720,1152)),('epaule-droite',-55,.40,(-.19,.06,1.4),(960,864)),('epaule-gauche',55,.40,(2*plane+.19,.06,1.4),(960,864)),('epaule-profil',-90,.40,(-.19,.06,1.4),(960,864)),('epaule-arriere',-135,.40,(-.19,.06,1.4),(960,864)),('haut-dos',180,.49,(plane,.11,1.45),(960,960)),('pectoraux',0,.62,(plane,-.02,1.385),(1000,800)),('thorax-lateral',-65,.43,(-.13,-.01,1.305),(960,960))]
for name,yaw,scale,target,res in views:
 camera=bpy.data.cameras.new('P3_'+name);camera.type='ORTHO';camera.ortho_scale=scale;ob=bpy.data.objects.new(camera.name,camera);rig.objects.link(ob);theta=math.radians(yaw);ob.location=Vector(target)+Vector((4*math.sin(theta),-4*math.cos(theta),0));aim(ob,target);cameras[name]=(ob,res)
world=bpy.data.worlds.new('PASSE3_FOND_NEUTRE');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(.045,.045,.045,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.30
for s in [before,after]:
 s.world=world;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=12 if a.preview else 48;s.cycles.seed=0;s.cycles.use_denoising=False;s.view_settings.view_transform='AgX';s.render.image_settings.file_format='PNG'
frames=[(f'{state}-{name}',scene,name)for name,*_ in views for state,scene in [('avant',before),('apres',after)]]
if a.preview:frames=[f for f in frames if f[0]in ['apres-epaule-profil','apres-epaule-droite','apres-pectoraux']]
metadata={'input_blend_sha256':input_sha,'renderer_sha256':sha(Path(__file__)),'engine':'CYCLES_CPU','samples':12 if a.preview else 48,'same_matte_material_before_after':True,'physically_symmetric_lighting':True,'lights':lights,'render_pixels_retouch':False,'frames':[]}
for name,scene,view in frames:
 camera,res=cameras[view];scene.camera=camera;scene.render.resolution_x,scene.render.resolution_y=res;scene.render.resolution_percentage=100;path=out/(name+'.png');scene.render.filepath=str(path);bpy.ops.render.render(write_still=True,scene=scene.name);metadata['frames'].append({'file':path.name,'sha256':sha(path),'scene':scene.name,'camera':view,'size':list(res)});(out/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
if not a.preview:
 bpy.context.window.scene=after;after.camera=cameras['face'][0];bpy.ops.wm.save_as_mainfile(filepath=str(file),compress=True);metadata['final_blend_sha256']=sha(file);(out/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
print('PASSE3_RENDERED',len(frames),flush=True)
