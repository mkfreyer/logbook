"""Editable eight-zone weighted palette on the intact model. No geometry edits."""
import json,sys
from pathlib import Path
import bpy,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from glb_io import sha
from scene import camera
root=Path(__file__).resolve().parents[2];out=root/'docs/m4c/meshy-huit-zones'
bpy.ops.wm.open_mainfile(filepath=str(out/'meshy-eight-zones.blend'),use_scripts=False)
scene=bpy.context.scene;ob=bpy.data.objects['MESHY_M4C'];spec=json.loads((out/'regions.json').read_text())
ob.data.uv_layers['M4C_SURFACE_UV'].data.foreach_set('uv',np.load(out/'source-uv-binding.npz')['uv_blender'].ravel())
mat=bpy.data.materials.new('M4C_HUIT_ZONES__PALETTE_EDITABLE');mat.use_nodes=True
nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=nodes['Principled BSDF'];bs.inputs['Roughness'].default_value=.86;bs.inputs['Metallic'].default_value=0
uv=nodes.new('ShaderNodeUVMap');uv.uv_map='M4C_SURFACE_UV';uv.location=(-1200,0)
channels=[]
for group in range(2):
    image=bpy.data.images.load(str(out/'textures'/f'masks-rgba-{group}.png'),check_existing=False)
    image.colorspace_settings.name='Non-Color';image.alpha_mode='CHANNEL_PACKED';image.pack()
    tex=nodes.new('ShaderNodeTexImage');tex.image=image;tex.interpolation='Linear';tex.extension='EXTEND';tex.location=(-1000,-group*400);links.new(uv.outputs['UV'],tex.inputs['Vector'])
    sep=nodes.new('ShaderNodeSeparateColor');sep.mode='RGB';sep.location=(-800,-group*400);links.new(tex.outputs['Color'],sep.inputs[0])
    channels.extend([sep.outputs['Red'],sep.outputs['Green'],sep.outputs['Blue'],tex.outputs['Alpha']])
weighted=[];weights=[]
def linear(hexcolor):
    a=[int(hexcolor[i:i+2],16)/255 for i in (1,3,5)]
    return [v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in a]
for channel,z in zip(channels,spec['zones']):
    show=nodes.new('ShaderNodeValue');show.name='SHOW::'+z['id'];show.label=z['id']+' — 0 neutre / 1 couleur';show.outputs[0].default_value=1;show.location=(-600,-z['code']*170)
    rgb=nodes.new('ShaderNodeRGB');rgb.name='COLOR::'+z['id'];rgb.label=z['name'];rgb.outputs[0].default_value=(*linear(z['color']),1);rgb.location=(-600,100-z['code']*170)
    weight=nodes.new('ShaderNodeMath');weight.operation='MULTIPLY';links.new(show.outputs[0],weight.inputs[0]);links.new(channel,weight.inputs[1]);weights.append(weight.outputs[0])
    color=nodes.new('ShaderNodeVectorMath');color.operation='SCALE';links.new(rgb.outputs[0],color.inputs[0]);links.new(weight.outputs[0],color.inputs['Scale']);weighted.append(color.outputs[0])
def add(outputs,type):
    total=outputs[0]
    for output in outputs[1:]:
        node=nodes.new(type);node.operation='ADD';links.new(total,node.inputs[0]);links.new(output,node.inputs[1]);total=node.outputs[0]
    return total
sumweight=add(weights,'ShaderNodeMath');remain=nodes.new('ShaderNodeMath');remain.operation='SUBTRACT';remain.inputs[0].default_value=1;links.new(sumweight,remain.inputs[1])
base=nodes.new('ShaderNodeVectorMath');base.operation='SCALE';base.inputs[0].default_value=(.5,.52,.55);links.new(remain.outputs[0],base.inputs['Scale'])
links.new(add([base.outputs[0]]+weighted,'ShaderNodeVectorMath'),bs.inputs['Base Color'])
ob.data.materials.clear();ob.data.materials.append(mat)
ob['muscle_zone_ids']=json.dumps([z['id'] for z in spec['zones']]);ob['anatomy_status']='PROPOSITION, awaiting user placement validation'
ob['geometry_changed']=False;ob['id_atlas']='textures/muscle-ids.png; discrete ID lookup, not linear grayscale interpolation'
for name,file in [('M4C_REGIONS.json','regions.json'),('M4C_METHOD.txt',None)]:
    block=bpy.data.texts.get(name) or bpy.data.texts.new(name)
    block.clear();block.write((out/file).read_text() if file else 'Model created with Meshy — CC BY 4.0. UV/material changes only. Eight named SHOW and COLOR nodes. Set every SHOW to 0 for the identical neutral appearance. No mobile UI integration. RGBA images are packed linear mask weights; the separate L8 ID atlas is the picking authority. Original GLB remains intact in assets/models/meshy-e45e5d8.glb.')
camera(scene,45,(0,.505,-.02),.7,(900,780))
scene['M4C']='Eight proposed surface zones, editable palette. No positions/reliefs/topology changed.'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(out/'meshy-eight-zones.blend'),compress=True)
print('EDITABLE_BLEND_PACKED',sha((out/'meshy-eight-zones.blend').read_bytes()),flush=True)
