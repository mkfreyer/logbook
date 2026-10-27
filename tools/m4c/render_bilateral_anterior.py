"""Matched anatomical angles; unchanged right and neutral image controls."""
import json,sys
from pathlib import Path
import bpy,numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/m4c'))
from scene import camera,render,bv
from glb_io import sha
BASE=ROOT/'docs/m4c/experience-anterieur-droit';OUT=ROOT/'docs/m4c/experience-anterieurs-bilateraux';DEST=OUT/'renders'
bpy.ops.wm.open_mainfile(filepath=str(BASE/'experience-anterieur-droit.blend'),use_scripts=False)
s=bpy.context.scene;mesh=bpy.data.objects['MESHY_M4C'].data;mat=mesh.materials[0]
def hashes():
    co=np.empty(len(mesh.vertices)*3,np.float32);mesh.vertices.foreach_get('co',co)
    ix=np.empty(len(mesh.loops),np.uint32);mesh.loops.foreach_get('vertex_index',ix)
    uv=np.empty(len(mesh.loops)*2,np.float32);mesh.uv_layers['M4C_SURFACE_UV'].data.foreach_get('uv',uv)
    n=np.array([x.vector[:] for x in mesh.corner_normals],np.float32)
    return {k:sha(v.tobytes()) for k,v in [('positions',co),('indices',ix),('uv',uv),('normals',n)]}
before=hashes();assert before==json.loads((BASE/'blender-preservation.json').read_text())['after']
s.cycles.samples=24;s.cycles.seed=0;s.cycles.use_denoising=False
s.camera.data.type='ORTHO';s.camera.data.shift_x=s.camera.data.shift_y=0
c=np.array([1.,147/255,43/255]);c=np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
for name in ['deltoid.right.anterior','deltoid.left.anterior']:mat.node_tree.nodes['COLOR::'+name].outputs[0].default_value=(*c,1)
meta={'referenceCommit':'7b69e3d','engine':'Blender 4.3.2 Cycles CPU','samples':24,'seed':0,'frames':[]}
def state(ids):
    for node in mat.node_tree.nodes:
        if node.name.startswith('SHOW::'):node.outputs[0].default_value=int(node.name[6:] in ids)
def shot(name,angle,target,scale,res=(900,900),silhouette=False):
    camera(s,angle,target,scale,res);s.render.use_border=False;s.render.use_crop_to_border=False
    file=DEST/(name+'.png');render(s,file)
    # Strip Blender's per-render timestamp metadata losslessly, so equivalent
    # controls compare by file bytes as well as decoded pixels.
    with Image.open(file) as im:im.copy().save(file)
    assert hashes()==before
    meta['frames'].append({'file':name+'.png','angle':angle,'target':list(target),'scale':scale,'resolution':list(res),
        'cameraMatrix':[list(row) for row in s.camera.matrix_world],'silhouette':silhouette,'sha256':sha((DEST/(name+'.png')).read_bytes())})
    (DEST/'render-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
right=(-.2,.555,0);left=(.2,.555,0)
def outline(name,side):
    # True surface mask rendered as emission, not a painted image overlay.
    original=mesh.materials[0];world=s.world;transform=s.view_settings.view_transform
    mask=bpy.data.materials.new('MASK_CONTROL_TEMP');mask.use_nodes=True;nodes=mask.node_tree.nodes;nodes.clear();links=mask.node_tree.links
    tex=nodes.new('ShaderNodeTexImage');tex.interpolation='Linear'
    pack=1 if side=='right' else 0
    tex.image=next(n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and Path(n.image.filepath).name==f'masks-rgba-{pack}.png')
    sep=nodes.new('ShaderNodeSeparateColor');links.new(tex.outputs['Color'],sep.inputs['Color'])
    emission=nodes.new('ShaderNodeEmission');output=nodes.new('ShaderNodeOutputMaterial');links.new(emission.outputs[0],output.inputs['Surface'])
    links.new(sep.outputs['Green' if side=='right' else 'Blue'],emission.inputs['Color'])
    mesh.materials[0]=mask;s.view_settings.view_transform='Raw'
    shot(name,-45 if side=='right' else 45,right if side=='right' else left,.34,silhouette=True)
    mesh.materials[0]=original;s.view_settings.view_transform=transform;bpy.data.materials.remove(mask)
state({'deltoid.right.anterior'});shot('reference-droite-avant',-45,right,.34)
outline('silhouette-droite-validee','right')
state({'deltoid.left.anterior'});shot('gauche-avant',45,left,.34)
outline('silhouette-gauche-avant','left')
state(set());shot('neutre-avant',0,(0,0,0),2.05,(700,1100))
for node in mat.node_tree.nodes:
    if node.type=='TEX_IMAGE':
        filename=Path(node.image.filepath).name
        if filename in ['masks-rgba-0.png','masks-rgba-1.png']:
            im=bpy.data.images.load(str(OUT/'textures'/filename),check_existing=False);im.colorspace_settings.name='Non-Color';im.alpha_mode='CHANNEL_PACKED';im.pack();im.filepath='//textures/'+filename;node.image=im
state({'deltoid.right.anterior'});shot('epaule-droite-validee',-45,right,.34)
assert (DEST/'reference-droite-avant.png').read_bytes()==(DEST/'epaule-droite-validee.png').read_bytes()
state({'deltoid.left.anterior'});shot('epaule-gauche-nouvelle',45,left,.34)
outline('silhouette-gauche-apres','left')
state({'deltoid.right.anterior','deltoid.left.anterior'})
shot('face-bilaterale',0,(0,.55,0),.76,(1300,900))
shot('trois-quarts-avant-droit',-35,(-.10,.55,0),.62,(1100,950))
shot('trois-quarts-avant-gauche',35,(.10,.55,0),.62,(1100,950))
state(set());shot('neutre-complet',0,(0,0,0),2.05,(700,1100))
assert (DEST/'neutre-avant.png').read_bytes()==(DEST/'neutre-complet.png').read_bytes()
collection=bpy.data.collections.new('GUIDES_BILATERAUX_SURFACE__HIDDEN');s.collection.children.link(collection)
t=json.loads((OUT/'surface-transfer.json').read_text())
for name,samples in [('DROIT_VALIDE_ALPHA_05',t['referenceRightCurve']),('GAUCHE_TRANSPOSE_3D',t['newLeftCurve'])]:
    curve=bpy.data.curves.new(name,'CURVE');curve.dimensions='3D';poly=curve.splines.new('POLY');poly.points.add(len(samples)-1)
    for item,p in zip(poly.points,samples):item.co=(*bv(p['point']),1)
    ob=bpy.data.objects.new(name,curve);collection.objects.link(ob);ob.hide_viewport=True;ob.hide_render=True
state({'deltoid.right.anterior','deltoid.left.anterior'});camera(s,0,(0,.55,0),.76,(1300,900))
text=bpy.data.texts.new('BILATERAL_ANTERIOR.json');text.write(json.dumps({'sourceCommit':'7b69e3d','immutableRightID':6,'editableLeftID':3,'guide':'surface-transfer.json','integration':False},indent=2))
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'experience-anterieurs-bilateraux.blend'),compress=True)
(OUT/'blender-preservation.json').write_text(json.dumps({'before':before,'after':hashes(),'identical':True,
    'neutralRendersByteIdentical':True,'rightRendersByteIdentical':True,'triangles':len(mesh.polygons),'vertices':len(mesh.vertices)},indent=2)+'\n')
print('BILATERAL_RENDERED',len(meta['frames']),flush=True)
