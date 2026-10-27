"""Matched real Blender renders and editable copy; no geometry/UV edits."""
import json,sys
from pathlib import Path
import bpy,numpy as np
from mathutils import Matrix
from PIL import Image,ImageOps
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/m4c'))
from experimental_anterior import BASE,OUT,axes
from scene import bv,camera,render
from glb_io import sha
bpy.ops.wm.open_mainfile(filepath=str(BASE/'meshy-posterieurs-harmonises.blend'),use_scripts=False)
s=bpy.context.scene;ob=bpy.data.objects['MESHY_M4C'];mesh=ob.data;mat=mesh.materials[0]
def hashes():
    co=np.empty(len(mesh.vertices)*3,np.float32);mesh.vertices.foreach_get('co',co)
    ix=np.empty(len(mesh.loops),np.uint32);mesh.loops.foreach_get('vertex_index',ix)
    uv=np.empty(len(mesh.loops)*2,np.float32);mesh.uv_layers['M4C_SURFACE_UV'].data.foreach_get('uv',uv)
    normals=np.array([n.vector[:] for n in mesh.corner_normals],np.float32)
    return {k:sha(v.tobytes()) for k,v in [('positions',co),('indices',ix),('uv',uv),('normals',normals)]}
before=hashes();assert before==json.loads((BASE/'blender-preservation.json').read_text())['after']
s.cycles.samples=32;s.cycles.seed=0;s.cycles.use_denoising=False
g=json.loads((OUT/'guide-camera.json').read_text())
meta={'baseCommit':'168ac61','cameraAlignment':'Right shoulder matched to the 305x221 left-shoulder reference, as requested by user. Reference-only frames reflected for comparison; UV atlas never reflected. No iPhone camera metadata.',
    'engine':'Blender 4.3.2 Cycles CPU','samples':32,'seed':0,'denoising':False,'frames':[]}
def fitted():
    angle,elevation,distance,scale,cx,cy=g['cameraParameters'];r,u,z=axes(angle,elevation)
    s.camera.location=bv(np.array(g['cameraAnchorSourceM'])+z*distance)
    s.camera.rotation_euler=Matrix([bv(r),bv(u),bv(z)]).transposed().to_euler()
    s.camera.data.type='PERSP';s.camera.data.sensor_fit='HORIZONTAL';s.camera.data.sensor_width=36
    s.camera.data.lens=scale*distance/305*36;s.camera.data.shift_x=(305/2-cx)/305;s.camera.data.shift_y=(cy-221/2)/305
    s.render.resolution_x=1220;s.render.resolution_y=884
    bpy.context.view_layer.update()
def standard(angle,target,scale,res):
    s.camera.data.type='ORTHO';s.camera.data.shift_x=s.camera.data.shift_y=0
    camera(s,angle,target,scale,res)
def state(selected):
    for node in mat.node_tree.nodes:
        if node.name.startswith('SHOW::'):node.outputs[0].default_value=int(node.name=='SHOW::deltoid.right.anterior' and selected)
    c=np.array([1.,147/255,43/255]);c=np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
    mat.node_tree.nodes['COLOR::deltoid.right.anterior'].outputs[0].default_value=(*c,1)
def shot(name,mirrored=False):
    file=OUT/'renders'/(name+'.png');s.render.use_border=False;s.render.use_crop_to_border=False;render(s,file)
    if mirrored:
        with Image.open(file) as im:ImageOps.mirror(im).save(file)
    assert hashes()==before
    meta['frames'].append({'file':file.name,'cameraMatrix':[list(row) for row in s.camera.matrix_world],
        'cameraType':s.camera.data.type,'resolution':[s.render.resolution_x,s.render.resolution_y],
        'mirrorForReferenceOnly':mirrored,'sha256':sha(file.read_bytes())})
    (OUT/'renders/render-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
state(True);fitted();shot('avant-reference',True)
state(False);shot('avant-neutre-reference',True)
for node in mat.node_tree.nodes:
    if node.type=='TEX_IMAGE' and Path(node.image.filepath).name=='masks-rgba-1.png':
        im=bpy.data.images.load(str(OUT/'textures/masks-rgba-1.png'),check_existing=False)
        im.colorspace_settings.name='Non-Color';im.alpha_mode='CHANNEL_PACKED';im.pack();im.filepath='//textures/masks-rgba-1.png';node.image=im
# Put both atlas packs in editable local paths, packed for standalone use.
for node in mat.node_tree.nodes:
    if node.type=='TEX_IMAGE' and Path(node.image.filepath).name=='masks-rgba-0.png':
        im=bpy.data.images.load(str(OUT/'textures/masks-rgba-0.png'),check_existing=False)
        im.colorspace_settings.name='Non-Color';im.alpha_mode='CHANNEL_PACKED';im.pack();im.filepath='//textures/masks-rgba-0.png';node.image=im
state(True);fitted();shot('apres-reference',True)
state(False);shot('apres-neutre-reference',True)
assert (OUT/'renders/avant-neutre-reference.png').read_bytes()==(OUT/'renders/apres-neutre-reference.png').read_bytes()
state(True)
for name,angle,target,scale,res in [
    ('face',0,(0,.54,0),.76,(1100,850)),
    ('profil-droit',-90,(-.22,.555,-.02),.36,(1000,1000)),
    ('trois-quarts-avant-droit',-45,(-.2,.55,0),.38,(1000,1000)),
    ('gros-plan-contour',-35,(-.19,.555,.035),.26,(1100,1100))]:
    standard(angle,target,scale,res);shot(name)
state(False);standard(0,(0,0,0),2.05,(700,1100));shot('neutre-complet')
# Surface curve guide is a hidden, non-sculpting helper in its own collection.
collection=bpy.data.collections.new('GUIDE_ID6_EXPERIMENTAL__HIDDEN');s.collection.children.link(collection)
curve=bpy.data.curves.new('Pectoral-facing border — projected actual triangles','CURVE');curve.dimensions='3D'
poly=curve.splines.new('POLY');samples=json.loads((OUT/'projected-curve.json').read_text())['samples'];poly.points.add(len(samples)-1)
for item,pt in zip(poly.points,samples):item.co=(*bv(pt['point']),1)
guide=bpy.data.objects.new('Guide projection input (not final boundary at protected pectoral)',curve);collection.objects.link(guide);guide.hide_render=True;guide.hide_viewport=True
state(True);fitted()
block=bpy.data.texts.new('EXPERIMENT_RIGHT_ANTERIOR.json');block.write(json.dumps({'base':'168ac61','onlyID':6,'sourceGuide':'guide-camera.json','doNotIntegrate':'Await user visual approval','protectedSevenMasks':True},indent=2))
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'experience-anterieur-droit.blend'),compress=True)
(OUT/'blender-preservation.json').write_text(json.dumps({'before':before,'after':hashes(),'identical':True,'vertices':len(mesh.vertices),'triangles':len(mesh.polygons),'neutralReferenceRendersByteIdentical':True},indent=2)+'\n')
print('EXPERIMENT_RENDERED',len(meta['frames']),flush=True)
