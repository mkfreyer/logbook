"""Matched neutral-matte Blender renders, before/after with original cameras."""
import argparse,hashlib,json,shutil,sys
from pathlib import Path
import bpy
from mathutils import Vector

p=argparse.ArgumentParser();p.add_argument('--asset',type=Path,required=True);p.add_argument('--preview',type=Path)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.asset.resolve()
out=a.preview.resolve()if a.preview else root/'renders';out.mkdir(parents=True,exist_ok=True)
meta=json.loads((root/'reconstruction.json').read_text());c=json.loads((root.parent/'ecorche-beatriz-guides-deltoides/guides.json').read_text())['camera']
bpy.ops.wm.open_mainfile(filepath=str(root/meta['master']),use_scripts=False)
before=bpy.data.scenes[meta['before_scene']];after=bpy.data.scenes[meta['scene']]
coll=bpy.data.collections.new('RECONSTRUCTION_CAMERAS_CONTROLE')
for scene in [before,after]:scene.collection.children.link(coll)
cams={}
for side in ['droite','gauche']:
    data=bpy.data.cameras.new('RECONSTRUCTION_REFERENCE_'+side);data.type='ORTHO';data.ortho_scale=c['ortho_scale']
    ob=bpy.data.objects.new(data.name,data);coll.objects.link(ob)
    loc=c['location_m'].copy();target=c['target_m'].copy()
    if side=='gauche':loc[0]=2*.002114987923242599-loc[0];target[0]=2*.002114987923242599-target[0]
    ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();cams[side]=ob
views=[('reference',cams['droite'],(960,1152),c['pixel_aspect_x'],root.parent/'ecorche-beatriz-guides-deltoides/renders/reference-sans-guides.png'),
       ('epaule-gauche',cams['gauche'],(960,1152),c['pixel_aspect_x'],root.parent/'ecorche-beatriz-creux-localises/renders/avant-epaule-gauche.png')]
for label,oldname,res in [('face','epaules-face',(1200,640)),('profil','epaule-profil',(960,864)),
                          ('trois-quarts','epaule-droite',(960,864)),('arriere-oblique','epaule-arriere',(960,864))]:
    views.append((label,before.objects['P4P5_'+oldname],res,1.,root.parent/'ecorche-beatriz-combinaison-p4-p5/renders'/(oldname+'.png')))
if a.preview:views=views[:1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
records=[]
for scene in [before,after]:
    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16 if a.preview else 48
    scene.cycles.seed=0;scene.cycles.use_denoising=False;scene.view_settings.view_transform='AgX'
    scene.world=bpy.data.worlds['PASSE3_FOND_NEUTRE'];scene.render.image_settings.file_format='PNG'
for label,cam,res,aspect,cache in views:
    for state,scene in [('avant',before),('apres',after)]:
        if a.preview and state=='avant':continue
        scene.camera=cam;scene.render.resolution_x,scene.render.resolution_y=res
        scene.render.resolution_percentage=75 if a.preview else 100
        scene.render.pixel_aspect_x=aspect;scene.render.pixel_aspect_y=1
        path=out/(state+'-'+label+'.png');scene.render.filepath=str(path)
        reused=not a.preview and state=='avant'
        if reused:
            assert cache.exists();shutil.copyfile(cache,path)
        else:bpy.ops.render.render(write_still=True,scene=scene.name)
        scene.view_layers[0].update()
        records.append({'file':path.name,'sha256':sha(path),'camera_matrix':[list(r)for r in cam.matrix_world],
                        'ortho_scale':cam.data.ortho_scale,'resolution':res,'resolution_percentage':scene.render.resolution_percentage,
                        'pixel_aspect_x':aspect,'reused_exact_approved_baseline':reused})
        (out/'metadata.json').write_text(json.dumps({'engine':'CYCLES_CPU','samples':scene.cycles.samples,
            'same_original_five_lights':True,'same_original_matte':True,'frames':records},indent=2)+'\n')
if not a.preview:
    after.camera=cams['droite'];after.render.resolution_x=960;after.render.resolution_y=1152
    after.render.pixel_aspect_x=c['pixel_aspect_x'];bpy.context.window.scene=after
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(root/meta['master']),compress=True)
print('RENDERED',len(records),flush=True)
