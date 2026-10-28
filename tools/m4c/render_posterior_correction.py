"""Replace one packed mask image only; render matched before/after cameras."""
import json,sys,hashlib
from pathlib import Path
import bpy,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from scene import camera,render
from glb_io import sha
root=Path(__file__).resolve().parents[2];base=root/'docs/m4c/meshy-huit-zones';out=root/'docs/m4c/meshy-deltoides-limite-inferieure';dest=out/'renders'
bpy.ops.wm.open_mainfile(filepath=str(base/'meshy-eight-zones.blend'),use_scripts=False)
s=bpy.context.scene;ob=bpy.data.objects['MESHY_M4C'];mesh=ob.data;mat=mesh.materials[0]
def geometry_hashes():
    co=np.empty(len(mesh.vertices)*3,np.float32);mesh.vertices.foreach_get('co',co)
    indices=np.empty(len(mesh.loops),np.uint32);mesh.loops.foreach_get('vertex_index',indices)
    uv=np.empty(len(mesh.loops)*2,np.float32);mesh.uv_layers['M4C_SURFACE_UV'].data.foreach_get('uv',uv)
    normals=np.array([p.vector[:] for p in mesh.corner_normals],np.float32)
    return {name:sha(array.tobytes()) for name,array in [('positions',co),('indices',indices),('uv',uv),('corner_normals',normals)]}
before=geometry_hashes()
for node in mat.node_tree.nodes:
    if node.type=='TEX_IMAGE' and Path(node.image.filepath).name=='masks-rgba-1.png':
        image=bpy.data.images.load(str(out/'textures/masks-rgba-1.png'),check_existing=False);image.colorspace_settings.name='Non-Color';image.alpha_mode='CHANNEL_PACKED';image.pack();image.filepath='//textures/masks-rgba-1.png';node.image=image
assert before==geometry_hashes()
block=bpy.data.texts.get('M4C_POSTERIOR_CORRECTION.json') or bpy.data.texts.new('M4C_POSTERIOR_CORRECTION.json');block.write((out/'correction.json').read_text())
ob['posterior_mask_correction']='Only posterior lower protrusion to neutral; no geometry/UV changes, no lateral reassignment.'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(out/'meshy-eight-zones-corrected.blend'),compress=True)
(out/'blender-preservation.json').write_text(json.dumps({'base_commit':'8b723d9','before':before,'after':geometry_hashes(),'identical':True,'vertices':len(mesh.vertices),'triangles':len(mesh.polygons)},indent=2)+'\n')
s.cycles.samples=24;s.cycles.use_denoising=False
record={'blend_sha256':sha((out/'meshy-eight-zones-corrected.blend').read_bytes()),'samples':24,'engine':'Blender 4.3.2 / Cycles CPU','seed':0,'denoising':False,'frames':[]}
frames=json.loads((base/'renders/render-metadata.json').read_text())['frames'];prior={p['file']:p for p in frames}
def shot(file,angle,target,scale,res,reference):
    camera(s,angle,target,scale,res);render(s,dest/file)
    current={'file':file,'reference':reference,'camera_matrix':[list(r) for r in s.camera.matrix_world],'resolution':list(res),'ortho_scale':scale,'sha256':sha((dest/file).read_bytes())}
    old=prior[reference];assert current['camera_matrix']==old['camera_matrix'] and current['resolution']==old['resolution'] and scale==old['ortho_scale']
    record['frames'].append(current);(dest/'render-metadata.json').write_text(json.dumps(record,indent=2)+'\n')
# Exact original cameras, including the right-front frame identified in annotation.
for side,x,sign in [('gauche',.225,1),('droit',-.225,-1)]:
    for view,angle in [('avant',45),('arriere',135)]:
        file='deltoide-'+side+'-'+view+'.png';shot(file,sign*angle,(x,.555,-.055),.29,(640,640),file)
for side,angle in [('gauche',90),('droit',-90)]:
    file='zones-profil-'+side+'.png';shot(file,angle,(0,.505,-.02),.7,(900,780),file)
shot('zones-trois-quarts-arriere.png',135,(0,.505,-.02),.7,(900,780),'zones-trois-quarts-arriere.png')
shot('zones-face.png',0,(0,.505,-.02),.7,(900,780),'zones-face.png')
for node in mat.node_tree.nodes:
    if node.name.startswith('SHOW::'):node.outputs[0].default_value=0
shot('neutre-face.png',0,(0,.505,-.02),.7,(900,780),'neutre-face.png')
shot('neutre-profil.png',90,(0,.505,-.02),.7,(900,780),'neutre-profil.png')
print('MATCHED_CORRECTION_RENDERED',len(record['frames']),flush=True)
