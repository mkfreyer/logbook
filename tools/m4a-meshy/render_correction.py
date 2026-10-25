"""Render existing before/edited after Blender files, without rebuilding either mesh."""
import argparse,json,sys
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mesh_io import sha
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--prepared',type=Path,required=True);p.add_argument('--version',choices=['before','after'],required=True)
p.add_argument('--samples',type=int,default=48)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.prepared.resolve();out=root/'correction/renders'
file=root/'renders/meshy-masques.blend' if a.version=='before' else out/'meshy-masques.blend'
bpy.ops.wm.open_mainfile(filepath=str(file),use_scripts=False)
frames=[('left-detail',1,'DETAIL_TROIS_QUARTS',(1000,840)),('deltoid-profile',3,'CONTROLE_PROFIL',(1000,840)),('deltoid-back',3,'CONTROLE_DOS',(1000,840))]
if a.version=='after':
 frames=[('neutral-front',0,'FACE',(720,1152)),('left-front',1,'FACE',(720,1152)),('left-three-quarter',1,'TROIS_QUARTS',(720,1152)),('right-front',2,'FACE',(720,1152)),*frames,('diagnostic',4,'DETAIL_FACE',(1000,840)),('right-detail',2,'DETAIL_FACE',(1000,840)),('deltoid-front',3,'DETAIL_FACE',(1000,840))]
names=['00_NEUTRE','01_PECTORAL_GAUCHE','02_PECTORAL_DROIT','03_DELTOIDE_GAUCHE','04_CONTROLE_REGIONS']
meta={'version':a.version,'input_blend_sha256':sha(file.read_bytes()),'renderer_sha256':sha(Path(__file__).read_bytes()),'samples':a.samples,'engine':'CYCLES_CPU','blender':bpy.app.version_string,'geometry_operation':False,'frames':[]}
for name,idx,cam,res in frames:
 scene=bpy.data.scenes[names[idx]];scene.camera=bpy.data.objects['CAM_'+cam]
 scene.cycles.samples=a.samples;scene.cycles.seed=0;scene.cycles.use_denoising=False
 scene.render.resolution_x,scene.render.resolution_y=res;scene.render.resolution_percentage=100
 scene.render.image_settings.file_format='PNG';path=out/(a.version+'-'+name+'.png');scene.render.filepath=str(path)
 bpy.ops.render.render(write_still=True,scene=scene.name)
 meta['frames'].append({'file':path.name,'scene':scene.name,'camera':cam,'size':res,'selection_region':scene['selection_region'],'sha256':sha(path.read_bytes())})
 (out/(a.version+'-metadata.json')).write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
print('CORRECTION_RENDER_DONE',a.version,len(frames),flush=True)
