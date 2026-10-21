"""Matched P4/P5/P6 shoulder comparisons, plus the complete new mannequin."""
import argparse,hashlib,json,math,shutil,sys
from pathlib import Path
import bpy
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--asset',type=Path,required=True);p.add_argument('--preview',type=Path);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.asset.resolve();file=root/'ecorche-passe6.blend';out=a.preview.resolve()if a.preview else root/'renders';out.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
input_sha=sha(file);meta=json.loads((root/'passe6.json').read_text());plane=meta['median_plane_x_m'];bpy.ops.wm.open_mainfile(filepath=str(file),use_scripts=False);scenes={'p4':bpy.data.scenes['13_TEMOIN_PASSE4'],'p5':bpy.data.scenes['14_TEMOIN_PASSE5'],'p6':bpy.data.scenes['15_PASSE6_NEUTRE']};rig=bpy.data.collections.new('PASSE6_LUMIERES_SYMETRIQUES')
for s in scenes.values():s.collection.children.link(rig)
def aim(ob,target):ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
lights=[]
for label,x,y,z,power,size in [('Avant',3,-3,2.6,200,2.2),('Dos',2,3,3,180,2.2)]:
 for side in [-1,1]:
  light=bpy.data.lights.new(f'P6_{label}_{side}','AREA');light.energy=power;light.shape='DISK';light.size=size;ob=bpy.data.objects.new(light.name,light);rig.objects.link(ob);ob.location=(plane+side*x,y,z);aim(ob,(plane,0,1));lights.append({'name':ob.name,'location':list(ob.location),'energy':power,'size':size})
light=bpy.data.lights.new('P6_Centre','AREA');light.energy=100;light.shape='DISK';light.size=2;ob=bpy.data.objects.new(light.name,light);rig.objects.link(ob);ob.location=(plane,-4,4);aim(ob,(plane,0,1));lights.append({'name':ob.name,'location':list(ob.location),'energy':100,'size':2})
views=[('epaules-face',0,.68,(plane,.02,1.41),(1200,640)),('epaules-dos',180,.68,(plane,.02,1.41),(1200,640)),('epaule-droite',-55,.40,(-.19,.06,1.4),(960,864)),('epaule-gauche',55,.40,(2*plane+.19,.06,1.4),(960,864)),('epaule-profil',-90,.40,(-.19,.06,1.4),(960,864)),('epaule-arriere',-135,.40,(-.19,.06,1.4),(960,864)),('face',0,2.05,(plane,0,.9),(720,1152)),('profil',-90,2.05,(plane,0,.9),(720,1152)),('dos',180,2.05,(plane,0,.9),(720,1152))];cameras={}
for name,yaw,scale,target,res in views:
 c=bpy.data.cameras.new('P6_'+name);c.type='ORTHO';c.ortho_scale=scale;ob=bpy.data.objects.new(c.name,c);rig.objects.link(ob);theta=math.radians(yaw);ob.location=Vector(target)+Vector((4*math.sin(theta),-4*math.cos(theta),0));aim(ob,target);cameras[name]=(ob,res)
for s in scenes.values():
 s.world=bpy.data.worlds['PASSE3_FOND_NEUTRE'];s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=12 if a.preview else 48;s.cycles.seed=0;s.cycles.use_denoising=False;s.view_settings.view_transform='AgX';s.render.image_settings.file_format='PNG'
frames=[(version+'-'+view,scene,view,version)for view,*_ in views for version,scene in scenes.items()if version=='p6'or view not in ['face','profil','dos']]
if a.preview:frames=[f for f in frames if f[0]in ['p6-epaules-face','p6-epaule-droite','p6-epaule-profil','p6-epaule-arriere']]
metadata={'input_blend_sha256':input_sha,'renderer_sha256':sha(Path(__file__)),'engine':'CYCLES_CPU','samples':12 if a.preview else 48,'same_pass3_matte_material':True,'physically_symmetric_lighting':True,'lights':lights,'render_pixels_retouch':False,'frames':[]}
for name,s,view,version in frames:
 c,res=cameras[view];s.camera=c;s.render.resolution_x,s.render.resolution_y=res;s.render.resolution_percentage=70 if a.preview else 100;path=out/(name+'.png');s.render.filepath=str(path);prior=root.parent/('ecorche-beatriz-passe'+version[-1])/'renders'/('apres-'+view+'.png')
 if version=='p4'and view=='epaule-arriere'and not prior.exists():prior=root.parent/'ecorche-beatriz-passe5'/'renders'/'avant-epaule-arriere.png'
 reused=not a.preview and version!='p6'and prior.exists()
 if reused:shutil.copyfile(prior,path)
 else:bpy.ops.render.render(write_still=True,scene=s.name)
 row={'file':path.name,'sha256':sha(path),'scene':s.name,'camera':view,'size':list(res),'reused_exact_prior_capture':reused}
 if reused:row['source_file']=str(prior.relative_to(root.parent.parent.parent));row['source_sha256']=sha(prior)
 metadata['frames'].append(row);(out/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
if not a.preview:
 bpy.context.window.scene=scenes['p6'];scenes['p6'].camera=cameras['face'][0];bpy.ops.wm.save_as_mainfile(filepath=str(file),compress=True);metadata['final_blend_sha256']=sha(file);(out/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
print('PASSE6_RENDERED',len(frames),flush=True)
