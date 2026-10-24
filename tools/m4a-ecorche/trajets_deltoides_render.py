"""Original cameras/lights/matte; raw before/after geometry comparisons."""
import argparse,hashlib,json,shutil,sys
from pathlib import Path
import bpy

p=argparse.ArgumentParser();p.add_argument('--asset',type=Path,required=True);p.add_argument('--preview',type=Path)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.asset.resolve();file=root/'ecorche-trajets-deltoides.blend';out=a.preview.resolve()if a.preview else root/'renders';out.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
meta=json.loads((root/'trajets.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(file),use_scripts=False);before=bpy.data.scenes[meta['before_scene']];after=bpy.data.scenes[meta['scene']]
views=[('reference','epaule-droite',(960,864)),('epaule-gauche','epaule-gauche',(960,864)),('epaules-face','epaules-face',(1200,640)),('epaules-dos','epaules-dos',(1200,640)),('epaule-profil','epaule-profil',(960,864)),('epaule-arriere','epaule-arriere',(960,864)),('face','face',(720,1152)),('profil','profil',(720,1152)),('trois-quarts','trois-quarts',(720,1152)),('dos','dos',(720,1152))]
if a.preview:views=[v for v in views if v[0]in ['reference','epaule-profil']]
for scene in [before,after]:
    scene.world=bpy.data.worlds['PASSE3_FOND_NEUTRE'];scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12 if a.preview else 48;scene.cycles.seed=0;scene.cycles.use_denoising=False;scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG'
metadata={'input_blend_sha256':sha(file),'renderer_sha256':sha(Path(__file__)),'same_original_camera_objects':True,'same_original_light_objects':True,'neutral_pass3_matte':True,'samples':12 if a.preview else 48,'raw_pixels_retouched':False,'frames':[]}
for name,oldname,res in views:
    cam=before.objects['P4P5_'+oldname]
    for state,scene in [('avant',before),('apres',after)]:
        if a.preview and state=='avant':continue
        scene.camera=cam;scene.render.resolution_x,scene.render.resolution_y=res;scene.render.resolution_percentage=100
        path=out/(state+'-'+name+'.png');scene.render.filepath=str(path);prior=root.parent/'ecorche-beatriz-combinaison-p4-p5/renders'/(oldname+'.png')
        reused=state=='avant'and not a.preview
        if reused:shutil.copyfile(prior,path)
        else:bpy.ops.render.render(write_still=True,scene=scene.name)
        row={'file':path.name,'sha256':sha(path),'scene':scene.name,'camera':cam.name,'camera_matrix_world':[list(r)for r in cam.matrix_world],'ortho_scale':cam.data.ortho_scale,'size':list(res),'reused_exact_baseline':reused}
        if reused:row['source']=str(prior.relative_to(root.parent.parent.parent))
        metadata['frames'].append(row);(out/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
if not a.preview:
    after.camera=before.objects['P4P5_face'];bpy.context.window.scene=after;bpy.ops.wm.save_as_mainfile(filepath=str(file),compress=True);metadata['final_blend_sha256']=sha(file);(out/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
print('TRAJETS_RENDERED',len(metadata['frames']),flush=True)
