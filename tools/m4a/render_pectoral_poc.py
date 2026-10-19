"""Six real Blender frames for the bounded before/after anatomy experiment."""
import argparse,hashlib,json,math,sys
from pathlib import Path
import bpy
from mathutils import Vector
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
p.add_argument('--kind',choices=['before','after'],required=True);p.add_argument('--samples',type=int,default=96);p.add_argument('--preview',action='store_true')
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.output.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(a.source.resolve()),use_scripts=False)
scene=bpy.context.scene;visible=[o for o in scene.objects if o.type=='MESH' and o.get('m4a_render')];assert len(visible)==3
m=bpy.data.materials.new('Common premium satin / actual anatomical surface attributes');m.use_nodes=True
nodes=m.node_tree.nodes;links=m.node_tree.links;n=nodes.get('Principled BSDF')
n.inputs['Roughness'].default_value=.37;n.inputs['Metallic'].default_value=.12;n.inputs['Coat Weight'].default_value=.08;n.inputs['Coat Roughness'].default_value=.32
fac=None;switches={}
for zone,name in [('pectoralis.left','m4a_poc_pectoral_L'),('pectoralis.right','m4a_poc_pectoral_R'),('deltoid.right','m4a_poc_deltoid_R')]:
    attr=nodes.new('ShaderNodeAttribute');attr.attribute_name=name
    threshold=nodes.new('ShaderNodeMath');threshold.operation='GREATER_THAN';threshold.inputs[1].default_value=.5;links.new(attr.outputs['Fac'],threshold.inputs[0])
    enabled=nodes.new('ShaderNodeValue');enabled.name='Select '+zone;enabled.outputs[0].default_value=0;switches[zone]=enabled
    multiply=nodes.new('ShaderNodeMath');multiply.operation='MULTIPLY';links.new(threshold.outputs[0],multiply.inputs[0]);links.new(enabled.outputs[0],multiply.inputs[1])
    if fac is None:fac=multiply.outputs[0]
    else:
        maximum=nodes.new('ShaderNodeMath');maximum.operation='MAXIMUM';links.new(fac,maximum.inputs[0]);links.new(multiply.outputs[0],maximum.inputs[1]);fac=maximum.outputs[0]
color=nodes.new('ShaderNodeMixRGB');color.inputs[1].default_value=(.23,.30,.41,1);color.inputs[2].default_value=(1,.18,.025,1);links.new(fac,color.inputs[0]);links.new(color.outputs[0],n.inputs['Base Color'])
height=nodes.new('ShaderNodeAttribute');height.attribute_name='m4a_poc_fibre_height'
bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.55;bump.inputs['Distance'].default_value=1
links.new(height.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],n.inputs['Normal'])
for o in visible:o.data.materials.clear();o.data.materials.append(m)
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=a.samples;scene.cycles.seed=0;scene.cycles.use_denoising=False
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.film_transparent=False
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.009,.019,.036,1);scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.6;scene.view_settings.view_transform='AgX'
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
lights=[('Key',(-2,-2.5,3.2),230,3,(.81,.88,1)),('Fill',(2.6,-1.7,1.6),110,2.5,(.56,.69,1)),('Rim',(1.6,2.3,2.8),310,2,(.58,.72,1)),('Back fill',(-2,2,1.3),90,2.5,(.75,.82,1))]
for name,loc,power,size,col in lights:
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=col;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc;aim(o,(0,0,1))
d=bpy.data.cameras.new('POC common camera');cam=bpy.data.objects.new('POC common camera',d);scene.collection.objects.link(cam);scene.camera=cam;d.type='ORTHO'
meta={'kind':a.kind,'source_sha256':hashlib.sha256(a.source.read_bytes()).hexdigest(),
 'protocol':{'blender':bpy.app.version_string,'renderer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'engine':'CYCLES_CPU','samples':a.samples,'denoising':False,'seed':0,'lights':lights,
 'material':{'color':[.23,.30,.41],'roughness':.37,'metallic':.12,'coat':.08,'bump_strength':.55,'bump_attribute':'m4a_poc_fibre_height'},'AI_generated_images':False,'anatomy_repainted':False},'frames':[]}
views=[('front',0),('three-quarter',-35)] if a.kind=='before' else [('front',0),('three-quarter',-35),('detail',-25),('selection',-35)]
if a.preview:views=[('three-quarter',-35),('detail',-25)]
for view,yaw in views:
    close=view in ['detail','selection'];target=(0,0,1.39) if close else (0,0,.9)
    d.ortho_scale=.70 if close else 2.30;theta=math.radians(yaw);cam.location=(4.5*math.sin(theta),-4.5*math.cos(theta),target[2]+.08);aim(cam,target)
    resolution=(1024,768) if close else (720,1152)
    if a.preview:resolution=(640,480) if close else (450,720)
    scene.render.resolution_x,scene.render.resolution_y=resolution;scene.render.resolution_percentage=100
    for zone,switch in switches.items():switch.outputs[0].default_value=int(view=='selection' and zone=='pectoralis.left')
    file=a.output/(view+'.png');scene.render.filepath=str(file);bpy.ops.render.render(write_still=True)
    meta['frames'].append({'view':view,'yaw':yaw,'target':target,'ortho_scale':d.ortho_scale,'resolution':resolution,'path':file.name,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'orange_zones':['pectoralis.left'] if view=='selection' else []})
    (a.output/'render-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
for switch in switches.values():switch.outputs[0].default_value=0
if a.kind=='after' and not a.preview:
    scene.render.filepath=str(a.output/'manual-review.png');file=a.output/'scene-review.blend';bpy.ops.wm.save_as_mainfile(filepath=str(file),compress=True)
    meta['review_scene']={'path':file.name,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'neutral_selection_restored':True}
(a.output/'render-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
