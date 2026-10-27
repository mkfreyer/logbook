"""Matched true Blender views for the six corrected masks. No source geometry edits."""
import sys,json,math
from pathlib import Path
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/m4c'))
from scene import camera,render,bv
from glb_io import sha,source
BASE=ROOT/'docs/m4c/meshy-posterieurs-harmonises';OUT=ROOT/'docs/m4c/meshy-deltoides-reperes-iphone'
preview='--preview' in sys.argv;dest=(ROOT.parent/'m4c-iphone-preview') if preview else OUT/'renders';dest.mkdir(exist_ok=True)
refs=json.loads((OUT/'iphone-reference-guides.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(BASE/'meshy-posterieurs-harmonises.blend'),use_scripts=False)
s=bpy.context.scene;mesh=bpy.data.objects['MESHY_M4C'].data;mat=mesh.materials[0];nodes=mat.node_tree.nodes
s.cycles.samples=4 if preview else 16;s.cycles.use_denoising=False;s.cycles.seed=0
original_colors={n.name:tuple(n.outputs[0].default_value) for n in nodes if n.name.startswith('COLOR::')}
meta={'engine':'Blender 4.3.2 Cycles CPU','samples':s.cycles.samples,'denoising':False,'seed':0,'referenceCommit':'06fa665','frames':[]}
def hashes():
 co=np.empty(len(mesh.vertices)*3,np.float32);mesh.vertices.foreach_get('co',co)
 ix=np.empty(len(mesh.loops),np.uint32);mesh.loops.foreach_get('vertex_index',ix)
 uv=np.empty(len(mesh.loops)*2,np.float32);mesh.uv_layers['M4C_SURFACE_UV'].data.foreach_get('uv',uv)
 norm=np.array([v.vector[:] for v in mesh.corner_normals],np.float32)
 return {k:sha(v.tobytes()) for k,v in [('positions',co),('indices',ix),('uv',uv),('normals',norm)]}
_,sv,_,_=source(ROOT/'assets/models/meshy-e45e5d8.glb');center=(sv.min(0)+sv.max(0))/2
before=hashes();assert before==json.loads((BASE/'blender-preservation.json').read_text())['after']
def palette(only=None,neutral=False):
 for n in nodes:
  if n.name.startswith('SHOW::'):n.outputs[0].default_value=int(not neutral and (only is None or n.name=='SHOW::'+only))
  if n.name in original_colors:n.outputs[0].default_value=original_colors[n.name]
 if only:
  rgb=np.array([1,147/255,43/255]);rgb=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
  nodes['COLOR::'+only].outputs[0].default_value=(*rgb,1)
def reference_camera(key):
 ref=refs[key];co=s.camera;co.location=bv(ref['cameraPositionSourceM']);co.rotation_euler=(bv(ref['cameraTargetSourceM'])-co.location).to_track_quat('-Z','Y').to_euler();co.data.type='PERSP';co.data.sensor_fit='VERTICAL';co.data.sensor_height=36;co.data.lens=36/(2*math.tan(math.radians(18)))
 s.render.resolution_x,s.render.resolution_y=(471,593) if preview else (754,950)
def shot(name):
 s.render.use_border=False;s.render.use_crop_to_border=False;render(s,dest/(name+'.png'));assert hashes()==before
 bpy.context.view_layer.update();meta['frames'].append({'file':name+'.png','cameraMatrix':[list(r) for r in s.camera.matrix_world],'cameraType':s.camera.data.type,'lens':s.camera.data.lens,'sensorFit':s.camera.data.sensor_fit,'sensorHeight':s.camera.data.sensor_height,'orthoScale':s.camera.data.ortho_scale,'resolution':[s.render.resolution_x,s.render.resolution_y],'sha256':sha((dest/(name+'.png')).read_bytes())});(dest/'render-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
def swap():
 count=0
 for n in nodes:
  if n.type=='TEX_IMAGE' and Path(n.image.filepath).name in ['masks-rgba-0.png','masks-rgba-1.png']:
   path=OUT/'textures'/Path(n.image.filepath).name;im=bpy.data.images.load(str(path),check_existing=False);im.colorspace_settings.name='Non-Color';im.alpha_mode='CHANNEL_PACKED';im.pack();im.filepath='//textures/'+path.name;n.image=im;count+=1
 assert count==2
if not preview:
 for key in refs:reference_camera(key);palette('deltoid.right.'+key);shot('avant-reference-'+key)
 s.camera.data.type='ORTHO';palette(neutral=True);camera(s,0,tuple(center),2.2,(850,1100));shot('avant-neutre')
swap()
for key in refs:reference_camera(key);palette('deltoid.right.'+key);shot('apres-reference-'+key)
if preview:sys.exit(0)
palette();s.camera.data.type='ORTHO';camera(s,180,(0,.55,-.04),.75,(1100,820));bpy.context.preferences.filepaths.save_version=0
bpy.data.texts.new('M4C_IPHONE_SURFACE_GUIDES.json').write((OUT/'surface-guides.json').read_text())
bpy.data.texts.new('M4C_SHARED_FRONTIERS.json').write((OUT/'shared-frontiers.json').read_text())
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'meshy-deltoides-reperes-iphone.blend'),compress=True)
for name,ang in [('face',0),('dos',180),('trois-quarts-avant-gauche',45),('trois-quarts-avant-droit',-45),('trois-quarts-arriere-gauche',135),('trois-quarts-arriere-droit',-135)]:
 palette();camera(s,ang,(0,.55,-.04),.75,(1100,820));shot('apres-'+name)
for side,x,sign in [('left',.225,1),('right',-.225,-1)]:
 for part,ang in [('anterior',45),('lateral',90),('posterior',135)]:
  palette('deltoid.'+side+'.'+part);camera(s,ang*sign,(x,.56,-.055),.35,(760,760));shot('controle-'+side+'-'+part)
palette(neutral=True);camera(s,0,tuple(center),2.2,(850,1100));shot('apres-neutre')
def pixel_hash(name):
 im=bpy.data.images.load(str(dest/(name+'.png')),check_existing=False);pixels=np.empty(len(im.pixels),np.float32);im.pixels.foreach_get(pixels);value=sha(pixels.tobytes());bpy.data.images.remove(im);return value
assert pixel_hash('avant-neutre')==pixel_hash('apres-neutre')
(OUT/'blender-preservation.json').write_text(json.dumps({'before':before,'after':hashes(),'identical':True,'neutralRenderPixelIdentical':True,'vertices':len(mesh.vertices),'triangles':len(mesh.polygons),'blendSha256':sha((OUT/'meshy-deltoides-reperes-iphone.blend').read_bytes())},indent=2)+'\n')
print('RENDERED_IPHONE_DELTOIDS',len(meta['frames']),flush=True)
