"""Texture-only Blender delivery plus colored and unlit silhouette controls."""
import json,sys
from pathlib import Path
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/m4c'))
from scene import camera,render
from glb_io import sha
BASE=ROOT/'docs/m4c/meshy-posterieur-droit-bord-inferieur';OUT=ROOT/'docs/m4c/meshy-posterieurs-harmonises';DEST=OUT/'renders'
bpy.ops.wm.open_mainfile(filepath=str(BASE/'meshy-posterieur-droit-bord-inferieur.blend'),use_scripts=False)
s=bpy.context.scene;mesh=bpy.data.objects['MESHY_M4C'].data;mat=mesh.materials[0]
s.cycles.samples=24;s.cycles.seed=0;s.cycles.use_denoising=False
def hashes():
    co=np.empty(len(mesh.vertices)*3,np.float32);mesh.vertices.foreach_get('co',co)
    ix=np.empty(len(mesh.loops),np.uint32);mesh.loops.foreach_get('vertex_index',ix)
    uv=np.empty(len(mesh.loops)*2,np.float32);mesh.uv_layers['M4C_SURFACE_UV'].data.foreach_get('uv',uv)
    normals=np.array([n.vector[:] for n in mesh.corner_normals],np.float32)
    return {key:sha(value.tobytes()) for key,value in [('positions',co),('indices',ix),('uv',uv),('normals',normals)]}
before=hashes();assert before==json.loads((BASE/'blender-preservation.json').read_text())['after']
meta={'referenceCommit':'977f68a','engine':'Blender 4.3.2 / Cycles CPU','samples':24,'seed':0,'denoising':False,'frames':[]}
def shot(name,angle,target,scale=.36,res=(1000,1000),silhouette=False):
    camera(s,angle,target,scale,res);s.render.use_border=False;s.render.use_crop_to_border=False
    render(s,DEST/(name+'.png'));assert hashes()==before
    meta['frames'].append({'file':name+'.png','angle':angle,'target':list(target),'cameraMatrix':[list(r) for r in s.camera.matrix_world],
        'orthoScale':s.camera.data.ortho_scale,'resolution':list(res),'silhouette':silhouette,'sha256':sha((DEST/(name+'.png')).read_bytes())})
    (DEST/'render-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')

def mask_controls(prefix):
    world,transform,look=s.world,s.view_settings.view_transform,s.view_settings.look
    dark=bpy.data.worlds.new('SILHOUETTE_BLACK');dark.use_nodes=True;dark.node_tree.nodes['Background'].inputs[1].default_value=0
    s.world=dark;s.view_settings.view_transform='Raw'
    mask=bpy.data.materials.new('SILHOUETTE_CONTROL_ONLY');mask.use_nodes=True;nodes=mask.node_tree.nodes;nodes.clear();links=mask.node_tree.links
    tex=nodes.new('ShaderNodeTexImage');tex.interpolation='Linear'
    tex.image=next(n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and Path(n.image.filepath).name=='masks-rgba-1.png')
    separate=nodes.new('ShaderNodeSeparateColor');links.new(tex.outputs['Color'],separate.inputs['Color'])
    emit=nodes.new('ShaderNodeEmission');output=nodes.new('ShaderNodeOutputMaterial');links.new(emit.outputs[0],output.inputs['Surface'])
    mesh.materials[0]=mask
    for side,angle,x,socket in [('gauche',135,.225,separate.outputs['Red']),('droit',-135,-.225,tex.outputs['Alpha'])]:
        for link in list(emit.inputs['Color'].links):links.remove(link)
        links.new(socket,emit.inputs['Color'])
        shot(prefix+'-silhouette-'+side,angle,(x,.555,-.055),silhouette=True)
    mesh.materials[0]=mat;s.world=world;s.view_settings.view_transform=transform;s.view_settings.look=look
    bpy.data.materials.remove(mask);bpy.data.worlds.remove(dark)

shot('avant-dos-grand',180,(0,.555,-.055),.72,(2000,1280))
mask_controls('avant')
count=0
for node in mat.node_tree.nodes:
    if node.type=='TEX_IMAGE' and Path(node.image.filepath).name=='masks-rgba-1.png':
        image=bpy.data.images.load(str(OUT/'textures/masks-rgba-1.png'),check_existing=False);image.colorspace_settings.name='Non-Color';image.alpha_mode='CHANNEL_PACKED';image.pack();image.filepath='//textures/masks-rgba-1.png';node.image=image;count+=1
assert count==1 and hashes()==before
block=bpy.data.texts.new('M4C_LEFT_SURFACE_ADAPTATION.json');block.write((OUT/'surface-adaptation.json').read_text())
camera(s,180,(0,.555,-.055),.72,(2000,1280));bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'meshy-posterieurs-harmonises.blend'),compress=True)
meta['blendSha256']=sha((OUT/'meshy-posterieurs-harmonises.blend').read_bytes())
(OUT/'blender-preservation.json').write_text(json.dumps({'before':before,'after':hashes(),'identical':True,'vertices':len(mesh.vertices),'triangles':len(mesh.polygons)},indent=2)+'\n')
shot('apres-trois-quarts-arriere-gauche',135,(.225,.555,-.055))
shot('apres-trois-quarts-arriere-droit',-135,(-.225,.555,-.055))
shot('apres-dos-grand',180,(0,.555,-.055),.72,(2000,1280))
mask_controls('apres')
for node in mat.node_tree.nodes:
    if node.name.startswith('SHOW::'):node.outputs[0].default_value=0
shot('neutre-face',0,(0,.505,-.02),.7,(900,780))
print('LEFT_HARMONIZATION_RENDERED',len(meta['frames']),flush=True)
