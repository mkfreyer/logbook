"""Reproducible BodyParts3D visual audit. Run with Blender --background --python this.py -- ...
Source vertices are only translated and uniformly scaled. No anatomical geometry is invented.
Smooth face shading (and optional true subdivision) is recorded in render-metadata.json.
"""
import bpy, json, math, argparse, sys
from pathlib import Path
from mathutils import Vector

argsv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
p=argparse.ArgumentParser()
p.add_argument('--obj-dir',required=True)
p.add_argument('--anatomy-dir',required=True)
p.add_argument('--out-dir',required=True)
p.add_argument('--mode',choices=['skin','muscles','muscles-bones'],default='muscles')
p.add_argument('--views',default='front,three-quarter,side,back')
p.add_argument('--subdivision',type=int,default=0)
p.add_argument('--orange-pectorals',action='store_true')
p.add_argument('--samples',type=int,default=32)
a=p.parse_args(argsv)
views=a.views.split(',')
angles={'front':0,'three-quarter':-35,'side':-90,'back':180}
if any(view not in angles for view in views):p.error('--views must contain front,three-quarter,side,back')
if a.subdivision<0 or a.samples<1:p.error('subdivision must be nonnegative and samples positive')
obj_dir=Path(a.obj_dir); anatomy_dir=Path(a.anatomy_dir); out_dir=Path(a.out_dir)/a.mode;out_dir.mkdir(parents=True,exist_ok=True)
manifest=json.loads((anatomy_dir/'selection-candidate.json').read_text())
pectoral_ids={x for sel in manifest['selection_candidates'] if sel['group_id']=='pectoralis-major' for x in sel['element_ids']}
ids={'FJ2810'} if a.mode=='skin' else set(manifest['audit_all_muscle_element_ids'])
if a.mode=='muscles-bones':
 bone_file=anatomy_dir/'bone-obj-ids.txt'
 if not bone_file.exists():raise SystemExit(f'No verified bone ID list {bone_file}')
 ids |= set(bone_file.read_text().split())

def raw_obj(path):
 verts=[];faces=[]
 for raw in path.read_text().splitlines():
  bits=raw.split()
  if not bits:continue
  if bits[0]=='v':verts.append(tuple(float(v) for v in bits[1:4]))
  elif bits[0]=='f':faces.append(tuple(int(c.split('/')[0])-1 if int(c.split('/')[0])>0 else len(verts)+int(c.split('/')[0]) for c in bits[1:]))
 original_count=len(verts)
 # Identical positions inside one source element only: no movement or cross-element union.
 unique=[];position_to_index={};remap=[]
 for v in verts:
  if v not in position_to_index:
   position_to_index[v]=len(unique);unique.append(v)
  remap.append(position_to_index[v])
 faces=[tuple(remap[i] for i in face) for face in faces]
 return unique,faces,original_count
skin_verts,_,_=raw_obj(obj_dir/'FJ2810.obj')
lo=Vector([min(v[i] for v in skin_verts) for i in range(3)])
hi=Vector([max(v[i] for v in skin_verts) for i in range(3)])
center=Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z))
scale=1.80/(hi.z-lo.z)

bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.samples=a.samples;scene.cycles.use_denoising=False
scene.render.resolution_x=600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(0.009,0.019,0.036,1);scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=0.6
scene.view_settings.view_transform='AgX'

def material(name,color,roughness,metallic=0.0):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes.get('Principled BSDF')
 n.inputs['Base Color'].default_value=(*color,1);n.inputs['Roughness'].default_value=roughness;n.inputs['Metallic'].default_value=metallic
 n.inputs['Coat Weight'].default_value=0.08;n.inputs['Coat Roughness'].default_value=.32
 return m
satin=material('Satin blue grey',(0.23,0.30,0.41),0.37,0.12)
orange=material('Selected pectorals',(1.0,0.19,0.035),0.35,0.06)
floor=material('Midnight floor',(0.009,0.018,0.032),.8)
counts={'objects':0,'vertices':0,'polygons':0,'source_vertices_before_exact_weld':0}
for ix,element in enumerate(sorted(ids)):
 path=obj_dir/(element+'.obj')
 if not path.exists():raise SystemExit(f'Missing source OBJ {path}')
 verts,faces,original_count=raw_obj(path)
 normed=[tuple((Vector(v)-center)*scale) for v in verts]
 mesh=bpy.data.meshes.new(element);mesh.from_pydata(normed,[],faces);mesh.update()
 ob=bpy.data.objects.new(element,mesh);bpy.context.collection.objects.link(ob)
 ob.data.materials.append(orange if a.orange_pectorals and element in pectoral_ids else satin)
 for poly in mesh.polygons:poly.use_smooth=True
 if a.subdivision:
  mod=ob.modifiers.new('Audit subdivision','SUBSURF');mod.levels=a.subdivision;mod.render_levels=a.subdivision
 counts['source_vertices_before_exact_weld']+=original_count;counts['objects']+=1;counts['vertices']+=len(verts);counts['polygons']+=len(faces)
 if ix%100==0:print(f'Imported {ix+1}/{len(ids)}',flush=True)

# Uniform midnight backdrop; no ground surface obscures silhouette in the audit.

def aim(ob,target):ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
def light(name,loc,power,size,color):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color
 ob=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(ob);ob.location=loc;aim(ob,(0,0,1))
light('Key',(-2.0,-2.5,3.2),230,3.0,(.81,.88,1.0))
light('Fill',(2.6,-1.7,1.6),110,2.5,(.56,.69,1.0))
light('Rim',(1.6,2.3,2.8),310,2.0,(.58,.72,1.0))
light('Back fill',(-2,2,1.3),90,2.5,(.75,.82,1.0))
cam_data=bpy.data.cameras.new('Audit camera');cam=bpy.data.objects.new('Audit camera',cam_data);bpy.context.collection.objects.link(cam);scene.camera=cam
cam_data.type='ORTHO';cam_data.ortho_scale=2.02;cam_data.lens=70
metadata={'source_archive_sha256':'40665852c49f218326590e204db91064a1ecfc3c6f8cbd7bbbcaac62c7cd409e','mode':a.mode,'source_element_ids':sorted(ids),'source_skin_bounds':{'min':list(lo),'max':list(hi)},'source_axes':{'+Z':'superior','-Y':'anterior','+X':'anatomical left'},'transform':{'translation_before_scale':list(-center),'uniform_scale':scale},'exact_coordinate_weld_within_each_source_element':True,'smooth_face_normals':True,'denoising':False,'denoising_unavailable_reason':'Disabled to reproduce the original audit, whose Blender build lacked OpenImageDenoise support','render_samples':a.samples,'resolution':[600,1000],'material':{'base_color_linear':[0.23,0.30,0.41],'roughness':0.37,'metallic':0.12},'subdivision_levels':a.subdivision,'orange_pectorals':a.orange_pectorals,'counts':counts,'frames':[],'note':'Audit candidate, no visual approval. Skin and muscle renders show the source as separate alternatives, not an invented complete mannequin.'}
for view in views:
 angle=math.radians(angles[view]);cam.location=(4.5*math.sin(angle),-4.5*math.cos(angle),.98);aim(cam,(0,0,.90))
 scene.render.filepath=str(out_dir/(view+'.png'));bpy.ops.render.render(write_still=True)
 metadata['frames'].append({'view':view,'camera_yaw_degrees':angles[view],'path':view+'.png'})
 (out_dir/'render-metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(metadata['counts']),flush=True)
