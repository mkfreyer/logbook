"""Identical neutral-matte comparisons of pass one and targeted pass two."""
import argparse,hashlib,json,math,sys
from pathlib import Path
import bpy
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--asset',type=Path,required=True);p.add_argument('--preview',type=Path);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.asset.resolve();file=root/'ecorche-passe2.blend';out=a.preview.resolve()if a.preview else root/'renders';out.mkdir(parents=True,exist_ok=True)
def sha(file):return hashlib.sha256(file.read_bytes()).hexdigest()
input_sha=sha(file);meta=json.loads((root/'passe2.json').read_text());plane=meta['median_plane_x_m'];bpy.ops.wm.open_mainfile(filepath=str(file),use_scripts=False)
before=bpy.data.scenes['04_AVANT_PASSE2'];after=bpy.data.scenes['05_PASSE2_NEUTRE'];blue=bpy.data.scenes.new('06_PASSE2_BLEU');rig=bpy.data.collections.new('PASSE2_ECLAIRAGE_NEUTRE')
for scene in [before,after,blue]:scene.collection.children.link(rig)
for ob in list(after.objects):
 if ob.type!='MESH':continue
 clone=ob.copy();clone.name='BLEU__'+ob['asset_id'];blue.collection.objects.link(clone)
 for slot in clone.material_slots:slot.material=bpy.data.materials['PRESENTATION_BLEU_ARGENTE']
def aim(ob,target):ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,size in [('Key',(-3,-4,4),450,2),('Fill',(3,-2,2),55,2.5),('Back_key',(-2,3,3),380,2),('Back_fill',(2,2,2),55,2.5)]:
 light=bpy.data.lights.new('P2_'+name,'AREA');light.energy=power;light.shape='DISK';light.size=size;light.color=(1,1,1);ob=bpy.data.objects.new(light.name,light);rig.objects.link(ob);ob.location=loc;aim(ob,(plane,0,1))
cameras={}
for name,yaw,scale,target,res in [('face',0,2.05,(plane,0,.9),(720,1152)),('profil',-90,2.05,(plane,0,.9),(720,1152)),('dos',180,2.05,(plane,0,.9),(720,1152)),('trois-quarts',-35,2.05,(plane,0,.9),(720,1152)),('epaule-avant',-55,.40,(-.19,.06,1.4),(1000,900)),('epaule-profil',-90,.40,(-.19,.06,1.4),(1000,900)),('epaule-arriere',-135,.40,(-.19,.06,1.4),(1000,900)),('haut-dos',180,.49,(plane,.11,1.45),(1000,1000))]:
 camera=bpy.data.cameras.new('P2_'+name);camera.type='ORTHO';camera.ortho_scale=scale;ob=bpy.data.objects.new(camera.name,camera);rig.objects.link(ob);theta=math.radians(yaw);ob.location=Vector(target)+Vector((4*math.sin(theta),-4*math.cos(theta),0));aim(ob,target);cameras[name]=(ob,res)
world=bpy.data.worlds.new('PASSE2_FOND_NEUTRE');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(.045,.045,.045,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.30
for scene in [before,after,blue]:
 scene.world=world;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12 if a.preview else 48;scene.cycles.seed=0;scene.cycles.use_denoising=False;scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG'
frames=[(f'{state}-{view}',scene,view)for view in ['face','profil','dos','epaule-avant','epaule-profil','epaule-arriere','haut-dos']for state,scene in [('avant',before),('apres',after)]]+[('apres-bleu-trois-quarts',blue,'trois-quarts')]
if a.preview:frames=[f for f in frames if f[0]in ['avant-epaule-avant','apres-epaule-avant','avant-epaule-profil','apres-epaule-profil','apres-dos']]
metadata={'input_blend_sha256':input_sha,'renderer_sha256':sha(Path(__file__)),'engine':'CYCLES_CPU','samples':12 if a.preview else 48,'same_matte_material_lights_cameras_for_before_after':True,'render_pixels_retouch':False,'frames':[]}
for name,scene,view in frames:
 camera,res=cameras[view];scene.camera=camera;scene.render.resolution_x,scene.render.resolution_y=res;scene.render.resolution_percentage=100;path=out/(name+'.png');scene.render.filepath=str(path);bpy.ops.render.render(write_still=True,scene=scene.name)
 metadata['frames'].append({'file':path.name,'sha256':sha(path),'scene':scene.name,'camera':view,'size':list(res)});(out/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
if not a.preview:
 bpy.context.window.scene=after;after.camera=cameras['trois-quarts'][0];bpy.ops.wm.save_as_mainfile(filepath=str(file),compress=True);metadata['final_blend_sha256']=sha(file);(out/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
print('PASSE2_RENDERED',len(frames),flush=True)
