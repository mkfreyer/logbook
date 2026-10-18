"""Render real candidate geometry with a single shared material/light/camera protocol."""
import argparse,sys,json,math,hashlib
from pathlib import Path
import bpy
from mathutils import Vector,Matrix
p=argparse.ArgumentParser()
p.add_argument('--blend',type=Path,required=True)
p.add_argument('--objects',nargs='+',required=True)
p.add_argument('--candidate',required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--samples',type=int,default=64)
p.add_argument('--resolution',type=int,nargs=2,default=[900,1400])
p.add_argument('--subdivision',type=int,default=1)
p.add_argument('--views',default='front,three-quarter,back')
p.add_argument('--rotation-z',type=float,default=0)
p.add_argument('--normalization-from',type=Path,
               help='Reuse the exact source-space center and scale from an earlier render metadata JSON')
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
a.output.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
with bpy.data.libraries.load(str(a.blend),link=False) as (src,dst):
    missing=set(a.objects)-set(src.objects)
    if missing:raise ValueError(f'Missing objects {missing}; available: {src.objects}')
    dst.objects=a.objects
loaded=list(dst.objects)
for ob in loaded:bpy.context.collection.objects.link(ob)
bpy.context.view_layer.update()
graph=bpy.context.evaluated_depsgraph_get()
records=[];meshes=[]
rotation=Matrix.Rotation(math.radians(a.rotation_z),4,'Z')
for ob in loaded:
    if ob.type!='MESH':raise ValueError(f'{ob.name} is not mesh')
    evaluated=ob.evaluated_get(graph)
    mesh=bpy.data.meshes.new_from_object(evaluated,depsgraph=graph)
    for vertex in mesh.vertices:vertex.co=rotation @ (ob.matrix_world @ vertex.co)
    mesh.calc_loop_triangles()
    assert all(math.isfinite(c) for v in mesh.vertices for c in v.co)
    modifiers=[]
    for m in ob.modifiers:
        record={'name':m.name,'type':m.type,'show_viewport':m.show_viewport,'show_render':m.show_render}
        for key in ('levels','render_levels','sculpt_levels','total_levels'):
            if hasattr(m,key):record[key]=getattr(m,key)
        modifiers.append(record)
    ob.data.calc_loop_triangles()
    records.append({'object':ob.name,'vertices':len(mesh.vertices),'polygons':len(mesh.polygons),'triangles':len(mesh.loop_triangles),'base_mesh':{'vertices':len(ob.data.vertices),'polygons':len(ob.data.polygons),'triangles':len(ob.data.loop_triangles)},'source_modifiers':modifiers,'source_variant':ob.get('variant'),'source_shape_keys':[{ 'name':key.name,'value':key.value} for key in ob.data.shape_keys.key_blocks] if ob.data.shape_keys else [],'vertex_group_names':[g.name for g in ob.vertex_groups]})
    meshes.append((ob.name,mesh))
for ob in list(bpy.data.objects):bpy.data.objects.remove(ob,do_unlink=True)
coords=[v.co for _,m in meshes for v in m.vertices]
lo=Vector([min(v[i] for v in coords) for i in range(3)])
hi=Vector([max(v[i] for v in coords) for i in range(3)])
center=Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z));scale=1.8/(hi.z-lo.z)
if a.normalization_from:
    reference=json.loads(a.normalization_from.read_text())
    if reference['transform']['rotation_z']!=a.rotation_z:raise ValueError('Normalization rotation differs')
    center=Vector(reference['transform']['center']);scale=reference['transform']['uniform_scale']
mat=bpy.data.materials.new('Logbook common blue grey satin');mat.use_nodes=True
bsdf=mat.node_tree.nodes.get('Principled BSDF')
bsdf.inputs['Base Color'].default_value=(.23,.30,.41,1)
bsdf.inputs['Roughness'].default_value=.37;bsdf.inputs['Metallic'].default_value=.12
bsdf.inputs['Coat Weight'].default_value=.08;bsdf.inputs['Coat Roughness'].default_value=.32
for name,mesh in meshes:
    for v in mesh.vertices:v.co=(v.co-center)*scale
    ob=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(ob)
    mesh.materials.clear();mesh.materials.append(mat)
    for poly in mesh.polygons:poly.use_smooth=True
    if a.subdivision:
        mod=ob.modifiers.new('Common comparison subdivision','SUBSURF');mod.levels=a.subdivision;mod.render_levels=a.subdivision
scene=bpy.context.scene;scene.render.engine='CYCLES'
scene.cycles.samples=a.samples;scene.cycles.use_denoising=False
scene.render.resolution_x=a.resolution[0];scene.render.resolution_y=a.resolution[1];scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.009,.019,.036,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.6
scene.view_settings.view_transform='AgX'
def aim(ob,target):ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
def light(name,loc,power,size,color):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=color
    ob=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(ob);ob.location=loc;aim(ob,(0,0,1))
light('Key',(-2,-2.5,3.2),230,3,(.81,.88,1))
light('Fill',(2.6,-1.7,1.6),110,2.5,(.56,.69,1))
light('Rim',(1.6,2.3,2.8),310,2,(.58,.72,1))
light('Back fill',(-2,2,1.3),90,2.5,(.75,.82,1))
camera_data=bpy.data.cameras.new('Common comparison camera');camera=bpy.data.objects.new('Common comparison camera',camera_data)
bpy.context.collection.objects.link(camera);scene.camera=camera
camera_data.type='ORTHO';camera_data.ortho_scale=2.30
metadata={'candidate':a.candidate,'source_blend_sha256':hashlib.sha256(a.blend.read_bytes()).hexdigest(),'source_objects':records,'source_bounds':{'min':list(lo),'max':list(hi)},'transform':{'rotation_z':a.rotation_z,'center':list(center),'uniform_scale':scale},'protocol':{'blender':bpy.app.version_string,'render_engine':'CYCLES_CPU','samples':a.samples,'resolution':a.resolution,'subdivision':a.subdivision,'denoising':False,'orthographic_scale':2.30,'material':{'base_color_linear':[.23,.30,.41],'roughness':.37,'metallic':.12},'source_materials_and_textures_replaced':True,'sculpting_or_geometry_invention':any(r['source_variant'] for r in records),'geometry_modified_in_renderer':False},'frames':[]}
angles={'front':0,'three-quarter':-35,'side':90,'back':180}
if a.normalization_from:
    metadata['normalization_reference_sha256']=hashlib.sha256(a.normalization_from.read_bytes()).hexdigest()
for view in a.views.split(','):
    angle=math.radians(angles[view]);camera.location=(4.5*math.sin(angle),-4.5*math.cos(angle),.98);aim(camera,(0,0,.9))
    scene.render.filepath=str(a.output/(view+'.png'));bpy.ops.render.render(write_still=True)
    metadata['frames'].append({'view':view,'yaw_degrees':angles[view],'path':view+'.png'})
(a.output/'render-metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'candidate':a.candidate,'source_objects':records,'normalized_width':float((hi.x-lo.x)*scale)}),flush=True)
