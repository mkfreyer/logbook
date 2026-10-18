"""Real Blender comparisons of continuous B+ fitness proxies and shader selection."""
import argparse,hashlib,json,math,sys
from pathlib import Path
import bpy
from mathutils import Vector
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--prepared',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
p.add_argument('--samples',type=int,default=96);p.add_argument('--resolution',type=int,nargs=2,default=[720,1152])
p.add_argument('--views',default='front,three-quarter,back,side,selection')
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.output.mkdir(parents=True,exist_ok=True)
source=a.prepared/'model.blend';bpy.ops.wm.open_mainfile(filepath=str(source.resolve()),use_scripts=False)
scene=bpy.context.scene;visible=[o for o in scene.objects if o.type=='MESH' and o.get('m4a_render')]
assert len(visible)==3
m=bpy.data.materials.new('B+ blue silver satin with surface-zone selection');m.use_nodes=True
nodes=m.node_tree.nodes;links=m.node_tree.links;n=nodes.get('Principled BSDF')
n.inputs['Roughness'].default_value=.37;n.inputs['Metallic'].default_value=.12
n.inputs['Coat Weight'].default_value=.08;n.inputs['Coat Roughness'].default_value=.32
attribute=nodes.new('ShaderNodeAttribute');attribute.attribute_name='m4a_pectoral_mask'
threshold=nodes.new('ShaderNodeMath');threshold.operation='GREATER_THAN';threshold.inputs[1].default_value=.5
links.new(attribute.outputs['Fac'],threshold.inputs[0])
enabled=nodes.new('ShaderNodeValue');enabled.name='M4A selection enabled';enabled.outputs[0].default_value=0
multiply=nodes.new('ShaderNodeMath');multiply.operation='MULTIPLY';links.new(threshold.outputs[0],multiply.inputs[0]);links.new(enabled.outputs[0],multiply.inputs[1])
color=nodes.new('ShaderNodeMixRGB');color.blend_type='MIX';color.inputs[1].default_value=(.23,.30,.41,1);color.inputs[2].default_value=(1,.18,.025,1)
links.new(multiply.outputs[0],color.inputs[0]);links.new(color.outputs[0],n.inputs['Base Color'])
for ob in visible:
    ob.data.materials.clear();ob.data.materials.append(m)
    for face in ob.data.polygons:face.material_index=0
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=a.samples;scene.cycles.seed=0;scene.cycles.use_denoising=False
scene.render.resolution_x,scene.render.resolution_y=a.resolution;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.film_transparent=False
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.009,.019,.036,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.6;scene.view_settings.view_transform='AgX'

def aim(ob,target):ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
lights=[('Key',(-2,-2.5,3.2),230,3,(.81,.88,1)),('Fill',(2.6,-1.7,1.6),110,2.5,(.56,.69,1)),
        ('Rim',(1.6,2.3,2.8),310,2,(.58,.72,1)),('Back fill',(-2,2,1.3),90,2.5,(.75,.82,1))]
for name,loc,power,size,col in lights:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=col
    ob=bpy.data.objects.new(name,data);scene.collection.objects.link(ob);ob.location=loc;aim(ob,(0,0,1))
data=bpy.data.cameras.new('B+ common camera');cam=bpy.data.objects.new('B+ common camera',data);scene.collection.objects.link(cam);scene.camera=cam
cam.data.type='ORTHO';cam.data.ortho_scale=2.30
angles={'front':0,'three-quarter':-35,'back':180,'side':90,'selection':-35}
c=json.loads((a.prepared/'construction.json').read_text())
meta={'variant':c['variant'],'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'protocol':{'renderer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'blender':bpy.app.version_string,
 'engine':'CYCLES_CPU','samples':a.samples,'resolution':a.resolution,'denoising':False,'seed':0,
 'ortho_scale':2.30,'camera_target':[0,0,.9],'lights':lights,
 'material':{'base_color_linear':[.23,.30,.41],'roughness':.37,'metallic':.12,'coat':.08},
 'geometry_changed_by_renderer':False,'AI_generated_images':False},
 'selection':{'mode':'Interpolated 3D scalar attribute threshold within mesh faces, shader color only',
 'attribute':'m4a_pectoral_mask','threshold':.5,'logical_regions':['pectoralis.left','pectoralis.right'],
 'separate_muscle_objects':0,'application_interaction':False},'frames':[]}
for view in a.views.split(','):
    enabled.outputs[0].default_value=1 if view=='selection' else 0
    theta=math.radians(angles[view]);cam.location=(4.5*math.sin(theta),-4.5*math.cos(theta),.98);aim(cam,(0,0,.9))
    file=a.output/(view+'.png');scene.render.filepath=str(file);bpy.ops.render.render(write_still=True)
    meta['frames'].append({'view':view,'yaw':angles[view],'path':file.name,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'selection_enabled':view=='selection'})
    (a.output/'render-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
enabled.outputs[0].default_value=0;theta=math.radians(-35);cam.location=(4.5*math.sin(theta),-4.5*math.cos(theta),.98);aim(cam,(0,0,.9))
scene.render.filepath=str(a.output/'manual-review.png');file=a.output/'scene-review.blend';bpy.ops.wm.save_as_mainfile(filepath=str(file),compress=True)
meta['review_scene']={'path':file.name,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'selection_disabled':True}
(a.output/'render-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
