"""Editable Blender copy + genuine orange selections on the same surface."""
import json,sys
from pathlib import Path
import bpy,numpy as np
from PIL import Image
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/m4c'))
from scene import camera,render,bv
from glb_io import sha
BASE=ROOT/'docs/m4c/meshy-anterieurs-valides';OUT=ROOT/'docs/m4c/meshy-bras-prototype';DEST=OUT/'renders'
bpy.ops.wm.open_mainfile(filepath=str(BASE/'meshy-anterieurs-valides.blend'),use_scripts=False)
s=bpy.context.scene;ob=bpy.data.objects['MESHY_M4C'];mesh=ob.data;mat=mesh.materials[0]
def hashes():
    co=np.empty(len(mesh.vertices)*3,np.float32);mesh.vertices.foreach_get('co',co)
    ix=np.empty(len(mesh.loops),np.uint32);mesh.loops.foreach_get('vertex_index',ix)
    uv=np.empty(len(mesh.loops)*2,np.float32);mesh.uv_layers['M4C_SURFACE_UV'].data.foreach_get('uv',uv)
    no=np.array([n.vector[:] for n in mesh.corner_normals],np.float32)
    return {k:sha(v.tobytes()) for k,v in [('positions',co),('indices',ix),('uv0',uv),('normals',no)]}
before=hashes();assert before==json.loads((OUT/'uv-preparation.json').read_text())['oldSurfaceAndUV0']
s.cycles.samples=24;s.cycles.seed=0;s.cycles.use_denoising=False;s.camera.data.type='ORTHO';s.camera.data.sensor_fit='AUTO';s.camera.data.shift_x=s.camera.data.shift_y=0
for node in mat.node_tree.nodes:
    if node.name.startswith('SHOW::'):node.outputs[0].default_value=0
meta={'baseCommit':'d552e23','engine':'Blender 4.3.2 Cycles CPU','samples':24,'seed':0,'geometryEdited':False,'frames':[]}
def state(active):
    for node in mat.node_tree.nodes:
        if node.name.startswith('SHOW::'):node.outputs[0].default_value=int(node.name[6:] in active)
def shot(name,angle,target,scale,res=(900,1000)):
    camera(s,angle,target,scale,res);s.render.use_border=False;s.render.use_crop_to_border=False
    file=DEST/(name+'.png');render(s,file)
    with Image.open(file) as im:im.copy().save(file)
    assert hashes()==before
    meta['frames'].append({'file':file.name,'angle':angle,'target':list(target),'scale':scale,'resolution':list(res),
        'cameraMatrix':[list(row) for row in s.camera.matrix_world],'sensorFit':s.camera.data.sensor_fit,'active':[n.name[6:] for n in mat.node_tree.nodes if n.name.startswith('SHOW::') and n.outputs[0].default_value],
        'sha256':sha(file.read_bytes())})
    (DEST/'render-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
shot('reference-neutre',0,(0,0,0),2.05,(720,1120))
layer=mesh.uv_layers.new(name='M4C_ARMS_UV');layer.data.foreach_set('uv',np.load(OUT/'arms-uv-binding.npz')['uv_blender'].ravel())
mesh.uv_layers.active=mesh.uv_layers['M4C_SURFACE_UV'];mesh.uv_layers['M4C_SURFACE_UV'].active_render=True
nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=nodes['Principled BSDF'];oldcolor=bs.inputs['Base Color'].links[0].from_socket
uv=nodes.new('ShaderNodeUVMap');uv.uv_map='M4C_ARMS_UV';uv.label='UV1 — four experimental arm zones only'
im=bpy.data.images.load(str(OUT/'textures/masks-rgba-arms.png'),check_existing=False);im.colorspace_settings.name='Non-Color';im.alpha_mode='CHANNEL_PACKED';im.pack();im.filepath='//textures/masks-rgba-arms.png'
tex=nodes.new('ShaderNodeTexImage');tex.image=im;tex.interpolation='Linear';links.new(uv.outputs['UV'],tex.inputs['Vector'])
separate=nodes.new('ShaderNodeSeparateColor');links.new(tex.outputs['Color'],separate.inputs['Color']);channels=[separate.outputs['Red'],separate.outputs['Green'],separate.outputs['Blue'],tex.outputs['Alpha']]
zones=json.loads((OUT/'regions.json').read_text())['zones'];colors=[];weights=[]
c=np.array([1.,147/255,43/255]);c=np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
for z,ch in zip(zones,channels):
    show=nodes.new('ShaderNodeValue');show.name='SHOW::'+z['id'];show.label=z['name']+' — 0 neutre / 1 orange';show.outputs[0].default_value=0
    rgb=nodes.new('ShaderNodeRGB');rgb.name='COLOR::'+z['id'];rgb.outputs[0].default_value=(*c,1)
    weight=nodes.new('ShaderNodeMath');weight.operation='MULTIPLY';links.new(ch,weight.inputs[0]);links.new(show.outputs[0],weight.inputs[1]);weights.append(weight.outputs[0])
    color=nodes.new('ShaderNodeVectorMath');color.operation='SCALE';links.new(rgb.outputs[0],color.inputs[0]);links.new(weight.outputs[0],color.inputs['Scale']);colors.append(color.outputs[0])
def add(values,kind):
    result=values[0]
    for value in values[1:]:
        n=nodes.new(kind);n.operation='ADD';links.new(result,n.inputs[0]);links.new(value,n.inputs[1]);result=n.outputs[0]
    return result
remaining=nodes.new('ShaderNodeMath');remaining.operation='SUBTRACT';remaining.inputs[0].default_value=1;links.new(add(weights,'ShaderNodeMath'),remaining.inputs[1])
oldscale=nodes.new('ShaderNodeVectorMath');oldscale.operation='SCALE';links.new(oldcolor,oldscale.inputs[0]);links.new(remaining.outputs[0],oldscale.inputs['Scale'])
links.new(add([oldscale.outputs[0]]+colors,'ShaderNodeVectorMath'),bs.inputs['Base Color'])
# Pack the frozen old atlas images at correct local paths as well.
for node in nodes:
    if node.type=='TEX_IMAGE' and Path(node.image.filepath).name in ['masks-rgba-0.png','masks-rgba-1.png']:
        name=Path(node.image.filepath).name;copy=bpy.data.images.load(str(OUT/'textures'/name),check_existing=False)
        copy.colorspace_settings.name='Non-Color';copy.alpha_mode='CHANNEL_PACKED';copy.pack();copy.filepath='//textures/'+name;node.image=copy
state(set());shot('neutre-complet',0,(0,0,0),2.05,(720,1120))
assert (DEST/'reference-neutre.png').read_bytes()==(DEST/'neutre-complet.png').read_bytes()
allarms={z['id'] for z in zones};state(allarms)
shot('face-complete',0,(0,0,0),2.05,(900,1300));shot('dos-complet',180,(0,0,0),2.05,(900,1300))
for side,sign in [('gauche',1),('droit',-1)]:
    ids={'biceps.'+('left' if sign==1 else 'right'),'triceps.'+('left' if sign==1 else 'right')};state(ids)
    shot('profil-bras-'+side,sign*90,(sign*.27,.37,-.07),.50,(900,1100))
for z in zones:
    side='gauche' if z['id'].endswith('left') else 'droit';sign=1 if side=='gauche' else -1
    kind=z['id'].split('.')[0];angle=sign*(25 if kind=='biceps' else 155);state({z['id']})
    shot(kind+'-'+side,angle,(sign*.25,.38,-.06),.38,(900,1000))
# Actual independent surface raycasts for the four proposed region IDs.
tree=BVHTree.FromPolygons([v.co[:] for v in mesh.vertices],[p.vertices[:] for p in mesh.polygons],all_triangles=True)
vertices=np.array([[v.co.x,v.co.z,-v.co.y] for v in mesh.vertices]);faces=np.array([p.vertices[:] for p in mesh.polygons])
uv0=np.load(ROOT/'docs/m4c/meshy-huit-zones/source-uv-binding.npz')['uv_blender'].copy();uv0[:,:,1]=1-uv0[:,:,1]
uv1=np.load(OUT/'arms-uv-binding.npz')['uv_blender'].copy();uv1[:,:,1]=1-uv1[:,:,1]
oldids=np.array(Image.open(OUT/'textures/muscle-ids.png'));newids=np.array(Image.open(OUT/'textures/muscle-ids-arms.png'));checks=[]
for w in json.loads((OUT/'picking-witnesses.json').read_text()):
    point=np.array(w['point']);normal=np.array(w['normal']);normal/=np.linalg.norm(normal)
    hit=tree.ray_cast(bv(point+normal*.025),bv(-normal));assert hit[0] is not None
    p=np.array([hit[0].x,hit[0].z,-hit[0].y]);tri=vertices[faces[hit[2]]]
    ab=np.linalg.lstsq(np.column_stack([tri[1]-tri[0],tri[2]-tri[0]]),p-tri[0],rcond=None)[0];bary=np.r_[1-ab.sum(),ab]
    q0=np.clip((bary@uv0[hit[2]]*2048).astype(int),0,2047);q1=np.clip((bary@uv1[hit[2]]*2048).astype(int),0,2047)
    assert oldids[q0[1],q0[0]]==0 and newids[q1[1],q1[0]]==w['code']
    checks.append({'id':w['expectedId'],'code':w['code'],'sourceFace':int(hit[2]),'firstSurfaceHit':p.tolist(),'protectedID':0})
(OUT/'picking-audit.json').write_text(json.dumps({'status':'passed','engine':'Blender BVH ray on unchanged real mesh, two UV ID atlases; no application UI','fourIndependentRegions':checks},indent=2)+'\n')
collection=bpy.data.collections.new('ARM_SURFACE_GUIDES__HIDDEN');s.collection.children.link(collection)
for z in json.loads((OUT/'surface-guides.json').read_text())['zones']:
    curve=bpy.data.curves.new(z['id']+'__SURFACE_CONTOUR','CURVE');curve.dimensions='3D';poly=curve.splines.new('POLY');poly.points.add(len(z['surfaceCurve'])-1);poly.use_cyclic_u=True
    for item,p in zip(poly.points,z['surfaceCurve']):item.co=(*bv(p['point']),1)
    guide=bpy.data.objects.new(z['id']+' guide',curve);collection.objects.link(guide);guide.hide_render=True;guide.hide_viewport=True
ob['prototype_registry']=json.dumps(json.loads((OUT/'registry-twelve.json').read_text()));ob['only_four_new_masks']=True;ob['application_integration']=False
text=bpy.data.texts.new('ARM_PROTOTYPE_METHOD.json');text.write((OUT/'regions.json').read_text())
state(allarms);camera(s,0,(0,.34,0),.9,(1200,1000));bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'meshy-bras-prototype.blend'),compress=True)
(OUT/'blender-preservation.json').write_text(json.dumps({'before':before,'after':hashes(),'identical':before==hashes(),'sourceVertices':len(mesh.vertices),'triangles':len(mesh.polygons),'newUvLayers':1,'oldUv0Changed':False,'neutralRendersByteIdentical':True},indent=2)+'\n')
print('ARM_PROTOTYPE_RENDERED',len(meta['frames']),'FOUR_RAYCASTS_PASSED',flush=True)
