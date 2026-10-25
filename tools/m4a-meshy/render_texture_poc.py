"""Render one texture-mask POC and one matching old-method control; never edit geometry."""
import argparse,json,sys
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mesh_io import sha
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prepared',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.prepared.resolve();out=root/'texture-poc'
file=out/'meshy-painted-mask.blend';bpy.ops.wm.open_mainfile(filepath=str(file),use_scripts=False)
meta={'blend_sha256':sha(file.read_bytes()),'renderer_sha256':sha(Path(__file__).read_bytes()),'engine':'CYCLES_CPU','samples':48,'seed':0,'denoising':False,'geometry_operation':False,'frames':[]}
def render(name,scene,cam,res):
 scene.camera=bpy.data.objects['CAM_'+cam];scene.cycles.samples=48;scene.cycles.seed=0;scene.cycles.use_denoising=False
 scene.render.resolution_x,scene.render.resolution_y=res;scene.render.resolution_percentage=100
 scene.render.image_settings.file_format='PNG';path=out/'renders'/(name+'.png');scene.render.filepath=str(path)
 bpy.ops.render.render(write_still=True,scene=scene.name)
 meta['frames'].append({'file':path.name,'scene':scene.name,'camera':cam,'size':res,'sha256':sha(path.read_bytes())})
 (out/'renders/render-metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
for name,scene,cam,res in [('neutral-front','00_NEUTRE','FACE',(720,1152)),('painted-front','01_MASQUE_PEINT','FACE',(720,1152)),('painted-three-quarter','01_MASQUE_PEINT','TROIS_QUARTS',(720,1152)),('painted-detail','01_MASQUE_PEINT','DETAIL_TROIS_QUARTS',(1000,840)),('painted-profile','01_MASQUE_PEINT','CONTROLE_PROFIL',(1000,840)),('painted-detail-front','01_MASQUE_PEINT','DETAIL_FACE',(1000,840))]:
 render(name,bpy.data.scenes[scene],cam,res)
old=root/'correction/renders/meshy-masques.blend';bpy.ops.wm.open_mainfile(filepath=str(old),use_scripts=False)
meta['triangle_control_blend_sha256']=sha(old.read_bytes())
render('triangles-profile',bpy.data.scenes['01_PECTORAL_GAUCHE'],'CONTROLE_PROFIL',(1000,840))
print('TEXTURE_POC_RENDERED',len(meta['frames']),flush=True)
