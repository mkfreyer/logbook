"""True Blender closeups and nearby-angle controls for the local UV residue."""
import json,sys
from pathlib import Path
import bpy,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent));from scene import camera,render
from glb_io import sha
root=Path(__file__).resolve().parents[2];base=root/'docs/m4c/meshy-deltoides-limite-inferieure';out=root/'docs/m4c/meshy-deltoides-residu-local';dest=out/'renders'
bpy.ops.wm.open_mainfile(filepath=str(base/'meshy-eight-zones-corrected.blend'),use_scripts=False)
s=bpy.context.scene;o=bpy.data.objects['MESHY_M4C'];mesh=o.data;mat=mesh.materials[0];s.cycles.samples=24;s.cycles.use_denoising=False

def mesh_hashes():
    co=np.empty(len(mesh.vertices)*3,np.float32);mesh.vertices.foreach_get('co',co);idx=np.empty(len(mesh.loops),np.uint32);mesh.loops.foreach_get('vertex_index',idx);uv=np.empty(len(mesh.loops)*2,np.float32);mesh.uv_layers['M4C_SURFACE_UV'].data.foreach_get('uv',uv)
    normals=np.array([p.vector[:] for p in mesh.corner_normals],np.float32)
    return {name:sha(data.tobytes()) for name,data in [('positions',co),('indices',idx),('uv',uv),('normals',normals)]}
original=mesh_hashes();meta={'referenceCommit':'71f70dc','engine':'Blender 4.3.2 / Cycles CPU','samples':24,'seed':0,'denoising':False,'frames':[]}
def shot(name,angle,close=False,neutral=False):
    if neutral:camera(s,0,(0,.505,-.02),.7,(900,780))
    else:camera(s,angle,(-.225,.555,-.055),.29,(6400,6400) if close else (640,640))
    s.render.use_border=close;s.render.use_crop_to_border=close
    if close:
        s.render.border_min_x=196/640;s.render.border_max_x=246/640;s.render.border_min_y=1-497/640;s.render.border_max_y=1-432/640
    render(s,dest/(name+'.png'))
    meta['frames'].append({'file':name+'.png','angle':angle,'close':close,'camera_matrix':[list(row) for row in s.camera.matrix_world],'ortho_scale':s.camera.data.ortho_scale,'full_resolution':[s.render.resolution_x,s.render.resolution_y],'normalized_border':[196/640,246/640,1-497/640,1-432/640] if close else None,'sha256':sha((dest/(name+'.png')).read_bytes())})
    (dest/'render-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
shot('avant-gros-plan',-45,True)
for angle in [-35,-55]:shot('avant-angle-'+str(abs(angle)),angle)
for node in mat.node_tree.nodes:
    if node.type=='TEX_IMAGE' and Path(node.image.filepath).name=='masks-rgba-1.png':
        image=bpy.data.images.load(str(out/'textures/masks-rgba-1.png'),check_existing=False);image.colorspace_settings.name='Non-Color';image.alpha_mode='CHANNEL_PACKED';image.pack();image.filepath='//textures/masks-rgba-1.png';node.image=image
assert mesh_hashes()==original
block=bpy.data.texts.get('M4C_RESIDUE_LOCAL.json') or bpy.data.texts.new('M4C_RESIDUE_LOCAL.json');block.write((out/'correction.json').read_text())
o['local_residue_correction']='Right posterior ID8 spur only; seven other masks unchanged.'
camera(s,-45,(-.225,.555,-.055),.29,(640,640));s.render.use_border=False;s.render.use_crop_to_border=False;bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(out/'meshy-residu-corrige.blend'),compress=True)
meta['correctedBlendSha256']=sha((out/'meshy-residu-corrige.blend').read_bytes())
(out/'blender-preservation.json').write_text(json.dumps({'before':original,'after':mesh_hashes(),'identical':True,'vertices':len(mesh.vertices),'triangles':len(mesh.polygons)},indent=2)+'\n')
shot('apres-gros-plan',-45,True)
shot('apres-vue-large',-45)
for angle in [-35,-55]:shot('apres-angle-'+str(abs(angle)),angle)
for node in mat.node_tree.nodes:
    if node.name.startswith('SHOW::'):node.outputs[0].default_value=0
shot('neutre-face',0,neutral=True)
print('RESIDUE_RENDERED',len(meta['frames']),flush=True)
