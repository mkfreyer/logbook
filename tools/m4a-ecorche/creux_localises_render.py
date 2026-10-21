"""Matched matte renders, including the calibrated reference and locked belly."""
import argparse,hashlib,json,shutil,sys
from pathlib import Path
import bpy
from mathutils import Vector

p=argparse.ArgumentParser();p.add_argument('--asset',type=Path,required=True);p.add_argument('--preview',type=Path);p.add_argument('--before-cache',type=Path)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.asset.resolve();file=root/'ecorche-creux-localises.blend';out=a.preview.resolve()if a.preview else root/'renders';out.mkdir(parents=True,exist_ok=True);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
meta=json.loads((root/'creux.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(file),use_scripts=False);before=bpy.data.scenes[meta['before_scene']];after=bpy.data.scenes[meta['scene']];rig=bpy.data.collections.new('CREUX_CAMERAS_REFERENCE')
for scene in [before,after]:scene.collection.children.link(rig)
c=meta['camera'];cams={}
for side in ['droite','gauche']:
 data=bpy.data.cameras.new('CREUX_REFERENCE_'+side);data.type='ORTHO';data.ortho_scale=c['ortho_scale'];ob=bpy.data.objects.new(data.name,data);rig.objects.link(ob);loc=c['location_m'].copy();target=c['target_m'].copy()
 if side=='gauche':loc[0]=2*meta['median_plane_x_m']-loc[0];target[0]=2*meta['median_plane_x_m']-target[0]
 ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();cams[side]=ob
views=[('reference',cams['droite'],(960,1152),c['pixel_aspect_x'],None),('epaule-gauche',cams['gauche'],(960,1152),c['pixel_aspect_x'],None),('face',before.objects['P4P5_epaules-face'],(1200,640),1.,'epaules-face'),('profil',before.objects['P4P5_epaule-profil'],(960,864),1.,'epaule-profil')]
if a.preview:views=views[:1]
for scene in [before,after]:
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12 if a.preview else 48;scene.cycles.seed=0;scene.cycles.use_denoising=False;scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG';scene.world=bpy.data.worlds['PASSE3_FOND_NEUTRE']
metadata={'input_blend_sha256':sha(file),'renderer_sha256':sha(Path(__file__)),'same_matte_material':True,'same_five_original_light_objects':True,'samples':12 if a.preview else 48,'frames':[]}
cached={r['file']:r for r in json.loads((a.before_cache/'metadata.json').read_text())['frames']}if a.before_cache else {}
for view,camera,res,aspect,oldname in views:
 for state,scene in [('avant',before),('apres',after)]:
  scene.camera=camera;scene.render.resolution_x,scene.render.resolution_y=res;scene.render.resolution_percentage=100;scene.render.pixel_aspect_x=aspect;scene.render.pixel_aspect_y=1;path=out/(state+'-'+view+'.png');scene.render.filepath=str(path)
  cache=not a.preview and state=='avant'and path.name in cached
  reused=not a.preview and state=='avant'and oldname is not None
  if cache:
   scene.view_layers[0].update();row=cached[path.name];assert row['camera_matrix']==[list(r)for r in camera.matrix_world]and row['ortho_scale']==camera.data.ortho_scale and row['pixel_aspect_x']==aspect and row['resolution']==list(res)
   prior=a.before_cache/path.name;assert sha(prior)==row['sha256'];shutil.copyfile(prior,path)
  elif reused:
   prior=root.parent/'ecorche-beatriz-combinaison-p4-p5/renders'/(oldname+'.png');shutil.copyfile(prior,path)
  else:bpy.ops.render.render(write_still=True,scene=scene.name)
  row={'file':path.name,'sha256':sha(path),'camera':camera.name,'camera_matrix':[list(r)for r in camera.matrix_world],'ortho_scale':camera.data.ortho_scale,'pixel_aspect_x':aspect,'resolution':res,'reused_exact_baseline':reused or cache}
  metadata['frames'].append(row);(out/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
if not a.preview:
 bpy.context.window.scene=after;after.camera=cams['droite'];after.render.resolution_x=960;after.render.resolution_y=1152;after.render.pixel_aspect_x=c['pixel_aspect_x'];bpy.ops.wm.save_as_mainfile(filepath=str(file),compress=True);metadata['final_blend_sha256']=sha(file);(out/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
print('RENDERED',len(metadata['frames']),flush=True)
