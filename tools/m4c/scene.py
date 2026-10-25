"""Common matched Blender cameras/materials. Never changes source positions."""
import math
from pathlib import Path
import bpy, numpy as np
from mathutils import Vector
from glb_io import source

def bv(p): return Vector((p[0],-p[2],p[1]))
def setup(root):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene
    _,v,n,f=source(root/'assets/models/meshy-e45e5d8.glb')
    b=v[:,[0,2,1]].copy();b[:,1]*=-1
    bn=n[:,[0,2,1]].copy();bn[:,1]*=-1
    mesh=bpy.data.meshes.new('MESHY_e45e5d8_SURFACE_INTACTE');mesh.from_pydata(b.tolist(),[],f.tolist());mesh.update()
    for poly in mesh.polygons: poly.use_smooth=True
    mesh.normals_split_custom_set(bn[f].reshape(-1,3).tolist())
    ob=bpy.data.objects.new('MESHY_M4C',mesh);scene.collection.objects.link(ob)
    ob['source_sha256']='421e593cad17f60d1c0c5e67707729fb88bbf69026795e22011ecc7d90b38959'
    mat=bpy.data.materials.new('NEUTRE_REFERENCE');mat.use_nodes=True
    bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.5,.52,.55,1);bs.inputs['Roughness'].default_value=.86;bs.inputs['Metallic'].default_value=0
    mesh.materials.append(mat)
    world=bpy.data.worlds.new('Studio neutre');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.11,.13,.16,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45;scene.world=world
    for name,pos,power,size in [('Key',(-2,2.8,3),250,3),('Fill',(2,1.8,2),200,3),('Back',(-.2,2,-2),200,2)]:
        light=bpy.data.lights.new(name,'AREA');light.energy=power;light.shape='DISK';light.size=size
        item=bpy.data.objects.new(name,light);scene.collection.objects.link(item);item.location=bv(pos);item.rotation_euler=(bv((0,.3,0))-item.location).to_track_quat('-Z','Y').to_euler()
    cam=bpy.data.cameras.new('Camera');co=bpy.data.objects.new('Camera',cam);scene.collection.objects.link(co);scene.camera=co;cam.type='ORTHO'
    scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=False;scene.cycles.seed=0;scene.render.threads_mode='FIXED';scene.render.threads=4
    scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
    scene.render.resolution_percentage=100
    return scene,ob,mat,v,n,f

def camera(scene,angle,target,scale,res=(800,800)):
    rad=math.radians(angle);scene.camera.location=bv((target[0]+3*math.sin(rad),target[1]+.12,target[2]+3*math.cos(rad)))
    scene.camera.rotation_euler=(bv(target)-scene.camera.location).to_track_quat('-Z','Y').to_euler()
    scene.camera.data.ortho_scale=scale;scene.render.resolution_x,scene.render.resolution_y=res

def render(scene,file):
    scene.render.filepath=str(file);bpy.ops.render.render(write_still=True)
