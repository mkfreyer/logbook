"""Save a texture-only Blender copy and render exact matched reference cameras."""
import json
import sys
from pathlib import Path
import bpy
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4c'))
from scene import camera,render
from glb_io import sha
BASE=ROOT/'docs/m4c/meshy-deltoides-residu-local'
OUT=ROOT/'docs/m4c/meshy-posterieur-droit-arrondi'
DEST=OUT/'renders'
bpy.ops.wm.open_mainfile(filepath=str(BASE/'meshy-residu-corrige.blend'),use_scripts=False)
s=bpy.context.scene
mesh=bpy.data.objects['MESHY_M4C'].data
mat=mesh.materials[0]
s.cycles.samples=24;s.cycles.seed=0;s.cycles.use_denoising=False

def hashes():
    co=np.empty(len(mesh.vertices)*3,np.float32);mesh.vertices.foreach_get('co',co)
    idx=np.empty(len(mesh.loops),np.uint32);mesh.loops.foreach_get('vertex_index',idx)
    uv=np.empty(len(mesh.loops)*2,np.float32);mesh.uv_layers['M4C_SURFACE_UV'].data.foreach_get('uv',uv)
    normals=np.array([n.vector[:] for n in mesh.corner_normals],np.float32)
    return {key:sha(data.tobytes()) for key,data in [('positions',co),('indices',idx),('uv',uv),('normals',normals)]}
before=hashes()
record={'referenceCommit':'18e1a44','engine':'Blender 4.3.2 / Cycles CPU',
        'samples':24,'seed':0,'denoising':False,'frames':[]}

def shot(name,angle=-135,target=(-.225,.555,-.055),scale=.36,res=(1000,1000),crop=False):
    camera(s,angle,target,scale,(2000,2000) if crop else res)
    s.render.use_border=crop;s.render.use_crop_to_border=crop
    if crop:
        s.render.border_min_x=.090;s.render.border_max_x=.645
        s.render.border_min_y=1-.805;s.render.border_max_y=1-.278
    render(s,DEST/(name+'.png'))
    assert hashes()==before
    record['frames'].append({'file':name+'.png','angle':angle,'target':list(target),
        'cameraMatrix':[list(row) for row in s.camera.matrix_world],
        'orthoScale':s.camera.data.ortho_scale,'resolution':[s.render.resolution_x,s.render.resolution_y],
        'referenceCrop':[90,278,645,805] if crop else None,
        'sha256':sha((DEST/(name+'.png')).read_bytes())})
    (DEST/'render-metadata.json').write_text(json.dumps(record,indent=2)+'\n')

shot('avant-angle-annotation',crop=True)
changed=0
for node in mat.node_tree.nodes:
    if node.type=='TEX_IMAGE' and Path(node.image.filepath).name=='masks-rgba-1.png':
        image=bpy.data.images.load(str(OUT/'textures/masks-rgba-1.png'),check_existing=False)
        image.colorspace_settings.name='Non-Color';image.alpha_mode='CHANNEL_PACKED'
        image.pack();image.filepath='//textures/masks-rgba-1.png';node.image=image;changed+=1
assert changed==1 and hashes()==before
block=bpy.data.texts.get('M4C_ROUNDED_RIGHT_POSTERIOR.json') or bpy.data.texts.new('M4C_ROUNDED_RIGHT_POSTERIOR.json')
block.write((OUT/'outline-guides.json').read_text())
camera(s,-135,(-.225,.555,-.055),.36,(1000,1000))
s.render.use_border=False;s.render.use_crop_to_border=False
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'meshy-posterieur-droit-arrondi.blend'),compress=True)
record['blendSha256']=sha((OUT/'meshy-posterieur-droit-arrondi.blend').read_bytes())
(OUT/'blender-preservation.json').write_text(json.dumps({'before':before,'after':hashes(),
    'identical':True,'vertices':len(mesh.vertices),'triangles':len(mesh.polygons)},indent=2)+'\n')
shot('apres-angle-annotation',crop=True)
shot('apres-trois-quarts-arriere-droit')
shot('apres-trois-quarts-arriere-gauche',135,(.225,.555,-.055))
shot('apres-epaules-dos',180,(0,.555,-.055),.72,(1400,900))
shot('apres-profil-droit',-90,(-.225,.555,-.055),.36)
shot('apres-avant-droit',-45,(-.225,.555,-.055),.29,(640,640))
for node in mat.node_tree.nodes:
    if node.name.startswith('SHOW::'):node.outputs[0].default_value=0
shot('neutre-face',0,(0,.505,-.02),.7,(900,780))
print('ROUNDED_POSTERIOR_RENDERED',len(record['frames']),flush=True)
