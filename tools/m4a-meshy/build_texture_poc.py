"""One projection-painted left-pectoral mask on a local angle-based UV chart.

Only UVs, materials and informational attributes are edited; source geometry is
checked byte for byte. The SVG contour is the painted selection, not face labels.
"""
import argparse,json,sys
from pathlib import Path
import bpy,numpy as np
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mesh_io import load_glb,sha,EXPECTED_SHA,neighbors,components,patch_topology
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prepared',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.prepared.resolve();out=root/'texture-poc'
raw,source,v,ix=load_glb(root/'source.glb');assert sha(raw)==EXPECTED_SHA
input_file=root/'correction/renders/meshy-masques.blend';bpy.ops.wm.open_mainfile(filepath=str(input_file),use_scripts=False)
scene=bpy.data.scenes['00_NEUTRE'];bpy.context.window.scene=scene
ob=next(o for o in scene.objects if o.type=='MESH');mesh=ob.data
def check_geometry():
 assert np.array([p.co[:] for p in mesh.vertices],dtype='<f4').tobytes()==v.tobytes()
 assert np.array([f.vertices[:] for f in mesh.polygons],dtype='<u4').tobytes()==ix.tobytes()
 assert not ob.modifiers and not mesh.shape_keys
check_geometry()
adj=neighbors(ix);old=np.frombuffer((root/'correction/regions/triangle-regions.u8').read_bytes(),dtype=np.uint8)
domain=old==1
for _ in range(12):
 expanded=domain.copy()
 for f in np.flatnonzero(domain):expanded[adj[f]]=True
 domain=expanded
# This domain is UV working space only, never the final selected area.
comp=components(~domain,adj)
for small in comp[1:]:domain[small]=True
assert patch_topology(domain,ix,adj)['single_disk']
blue=ob.material_slots[0].material
bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);scene.view_layers[0].objects.active=ob
uv=mesh.uv_layers.new(name='UV_LOCAL_PECTORAL');uv.active_render=True
edges=np.sort(np.concatenate([ix[domain][:,[0,1]],ix[domain][:,[1,2]],ix[domain][:,[2,0]]]),axis=1)
edges,count=np.unique(edges,axis=0,return_counts=True);border={tuple(e) for e in edges[count==1]}
for e in mesh.edges:e.use_seam=tuple(sorted(e.vertices)) in border
for vertex in mesh.vertices:vertex.select=False
for e in mesh.edges:e.select=False
for f in mesh.polygons:f.select=bool(domain[f.index])
bpy.context.tool_settings.mesh_select_mode=(False,False,True)
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.uv.unwrap(method='ANGLE_BASED',margin=.01);bpy.ops.object.mode_set(mode='OBJECT')
check_geometry();uv=mesh.uv_layers['UV_LOCAL_PECTORAL']
coords=np.array([p.uv[:] for p in uv.data],dtype=np.float64).reshape(-1,3,2)
uv_min=coords[domain].reshape(-1,2).min(0);uv_max=coords[domain].reshape(-1,2).max(0)
coords[domain]=.04+.92*(coords[domain]-uv_min)/(uv_max-uv_min)
coords[~domain]=(.005,.005);coords=coords.astype('<f4');uv.data.foreach_set('uv',coords.ravel())
(out/'uv-loops.f32').write_bytes(coords.tobytes());(out/'uv-chart-triangles.u32').write_bytes(np.flatnonzero(domain).astype('<u4').tobytes())
cam=bpy.data.objects['CAM_DETAIL_TROIS_QUARTS'];scene.camera=cam
scene.render.resolution_x=1000;scene.render.resolution_y=840;scene.render.resolution_percentage=100
screen=np.array([tuple(world_to_camera_view(scene,cam,ob.matrix_world@Vector(p)))[:2] for p in v]);screen[:,0]*=1000;screen[:,1]=(1-screen[:,1])*840
stencil=bpy.data.images.load(str(out/'textures/projection-stencil.png'),check_existing=False);stencil.colorspace_settings.name='Non-Color'
st=np.array(stencil.pixels[:],dtype=np.float32).reshape(840,1000,4)[::-1,:,0]
def sample(array,x,y):
 x=np.clip(x,0,array.shape[1]-1);y=np.clip(y,0,array.shape[0]-1);i=np.floor(x).astype(int);j=np.floor(y).astype(int)
 ii=np.minimum(i+1,array.shape[1]-1);jj=np.minimum(j+1,array.shape[0]-1);u=x-i;w=y-j
 return (1-u)*(1-w)*array[j,i]+u*(1-w)*array[j,ii]+(1-u)*w*array[jj,i]+u*w*array[jj,ii]
size=1024;paint=np.zeros((size,size),np.float32);coverage=np.zeros((size,size),np.uint16)
tree=BVHTree.FromPolygons(v.tolist(),ix.tolist(),all_triangles=True)
to_camera=(ob.matrix_world.inverted().to_3x3()@cam.rotation_euler.to_matrix()@Vector((0,0,1))).normalized();direction=-to_camera
rays=hidden=overlap=0
for f in np.flatnonzero(domain):
 t=coords[f].astype(float)*size-.5;lo=np.maximum(np.floor(t.min(0)).astype(int),0);hi=np.minimum(np.ceil(t.max(0)).astype(int),size-1)
 if np.any(hi<lo):continue
 xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1));points=np.column_stack([xx.ravel(),yy.ravel()])
 matrix=np.column_stack([t[1]-t[0],t[2]-t[0]])
 if abs(np.linalg.det(matrix))<1e-10:continue
 bc=(points-t[0])@np.linalg.inv(matrix).T;weights=np.column_stack([1-bc.sum(1),bc]);inside=np.all(weights>=-1e-7,axis=1)
 points=points[inside];weights=weights[inside]
 if not len(points):continue
 px,py=points[:,0],points[:,1];coverage[py,px]+=1
 projected=weights@screen[ix[f]];values=sample(st,projected[:,0]-.5,projected[:,1]-.5)
 for i in np.flatnonzero(values>0):
  pos=Vector(weights[i]@v[ix[f]]);hit=tree.ray_cast(pos+to_camera*4,direction,8);rays+=1
  if hit[0] is None or (hit[0]-pos).length>.0001:values[i]=0;hidden+=1
 overlap+=int(np.count_nonzero((paint[py,px]>0)&(values>0)))
 paint[py,px]=np.maximum(paint[py,px],values)
assert overlap==0,'UV overlap beneath the painted area; do not continue with an ambiguous chart'
rgba=np.ones((size,size,4),np.float32);rgba[:,:,:3]=paint[:,:,None]
image=bpy.data.images.new('MASK__pectoralis.left__linear',width=size,height=size,alpha=False)
image.colorspace_settings.name='Non-Color';image.pixels.foreach_set(rgba.ravel());image.update()
image.filepath_raw=str(out/'textures/pectoralis-left-mask.png');image.file_format='PNG';image.save();image.pack()
# Prove that the UV working-space seam lies outside the painted selection.
seam_max=0.
for f in np.flatnonzero(domain):
 for corner in range(3):
  if tuple(sorted((int(ix[f,corner]),int(ix[f,(corner+1)%3])))) not in border:continue
  ts=np.linspace(0,1,17)[:,None];qs=(1-ts)*coords[f,corner]+ts*coords[f,(corner+1)%3]
  seam_max=max(seam_max,float(sample(paint,qs[:,0]*size-.5,qs[:,1]*size-.5).max()))
assert seam_max==0,'Paint reaches a UV seam; stop rather than hide a triangle-cut boundary'
selected=blue.copy();selected.name='PECTORAL_GAUCHE__MASQUE_PEINT'
nodes=selected.node_tree.nodes;links=selected.node_tree.links;bsdf=nodes['Principled BSDF']
tex=nodes.new('ShaderNodeTexImage');tex.image=image;tex.interpolation='Linear';tex.extension='EXTEND';tex.label='Masque peint lineaire, 1024 px, pectoral gauche seulement'
mapping=nodes.new('ShaderNodeUVMap');mapping.uv_map=uv.name;links.new(mapping.outputs['UV'],tex.inputs['Vector'])
mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MIX';mix.inputs[1].default_value=(.19,.28,.42,1);mix.inputs[2].default_value=(1,.085,.006,1)
links.new(tex.outputs['Color'],mix.inputs[0]);links.new(mix.outputs[0],bsdf.inputs['Base Color'])
for name,mult,add in [('Roughness',-.05,.37),('Metallic',-.04,.12),('Coat Weight',.04,.08)]:
 n=nodes.new('ShaderNodeMath');n.operation='MULTIPLY_ADD';n.inputs[1].default_value=mult;n.inputs[2].default_value=add;links.new(tex.outputs['Color'],n.inputs[0]);links.new(n.outputs[0],bsdf.inputs[name])
mesh.materials.clear();mesh.materials.append(blue)
for f in mesh.polygons:f.material_index=0
neutral=scene;neutral.name='00_NEUTRE';active=bpy.data.scenes['01_PECTORAL_GAUCHE'];active.name='01_MASQUE_PEINT'
for s in list(bpy.data.scenes):
 if s not in [neutral,active]:
  for o in list(s.objects):
   if o.type=='MESH':bpy.data.objects.remove(o,do_unlink=True)
  bpy.data.scenes.remove(s)
for s,mat in [(neutral,blue),(active,selected)]:
 o=next(o for o in s.objects if o.type=='MESH');o.material_slots[0].link='OBJECT';o.material_slots[0].material=mat
 o['selection_method']='UV_LOCAL_PECTORAL + painted linear mask; no triangle region used for selection'
 s['selection_region']='unassigned' if s==neutral else 'pectoralis.left';s.camera=bpy.data.objects['CAM_FACE'];s.render.resolution_x=720;s.render.resolution_y=1152
check_geometry()
metadata={'baseline_commit':'898aac640dee6fdba27d4a16484035843a35d053','source_sha256':EXPECTED_SHA,'input_blend_sha256':sha(input_file.read_bytes()),'builder_sha256':sha(Path(__file__).read_bytes()),
 'stencil_sha256':sha((out/'painted-contour.svg').read_bytes()),'stencil_png_sha256':sha((out/'textures/projection-stencil.png').read_bytes()),'mask_sha256':sha((out/'textures/pectoralis-left-mask.png').read_bytes()),
 'uv_loops_sha256':sha(coords.tobytes()),'uv_chart_triangles':int(domain.sum()),'uv_chart_topology':patch_topology(domain,ix,adj),'uv_chart_name':uv.name,'uv_seam_mask_max':seam_max,'painted_uv_overlap_texels':overlap,
 'mask_resolution':[size,size],'visible_projection_ray_tests':rays,'occluded_projection_samples_rejected':hidden,'geometry_changed':False,'source_vertex_count':len(v),'source_triangle_count':len(ix),
 'paint_method':'Authored cubic SVG stencil projected once from the existing Meshy three-quarter camera onto a local angle-based UV chart, with per-texel BVH visibility rejection. No face-label blur.','selection_id':'pectoralis.left','image_origin':'PNG top-left; Blender UV bottom-left; invert V for glTF UVs.'}
for name,text in [('PAINTED_CONTOUR.svg',(out/'painted-contour.svg').read_text()),('TEXTURE_POC.json',json.dumps(metadata,ensure_ascii=False,indent=2))]:
 block=bpy.data.texts.new(name);block.write(text)
for s in [neutral,active]:
 for o in s.objects:
  if o.type=='MESH':o.select_set(False)
bpy.context.window.scene=active;obj=next(o for o in active.objects if o.type=='MESH');obj.select_set(True);active.view_layers[0].objects.active=obj
nodes.active=tex
bpy.ops.wm.save_as_mainfile(filepath=str(out/'meshy-painted-mask.blend'),compress=True)
metadata['blend_sha256']=sha((out/'meshy-painted-mask.blend').read_bytes());(out/'build.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
print('PAINTED_POC_BUILT',json.dumps(metadata),flush=True)
