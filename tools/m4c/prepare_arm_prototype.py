"""Second UV set on a COPY; all old UVs, positions, normals and faces intact."""
import json,math,sys
from pathlib import Path
import bpy,bmesh,numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/m4c'))
from scene import camera,render
from glb_io import sha,source
BASE=ROOT/'docs/m4c/meshy-anterieurs-valides';OUT=ROOT/'docs/m4c/meshy-bras-prototype';CACHE=ROOT.parent/'m4c-bras-cache'
for p in [OUT/'textures',OUT/'renders',CACHE]:p.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(BASE/'meshy-anterieurs-valides.blend'),use_scripts=False)
s=bpy.context.scene;ob=bpy.data.objects['MESHY_M4C'];mesh=ob.data
def hashes():
    co=np.empty(len(mesh.vertices)*3,np.float32);mesh.vertices.foreach_get('co',co)
    ix=np.empty(len(mesh.loops),np.uint32);mesh.loops.foreach_get('vertex_index',ix)
    uv=np.empty(len(mesh.loops)*2,np.float32);mesh.uv_layers['M4C_SURFACE_UV'].data.foreach_get('uv',uv)
    no=np.array([n.vector[:] for n in mesh.corner_normals],np.float32)
    return {k:sha(v.tobytes()) for k,v in [('positions',co),('indices',ix),('uv0',uv),('normals',no)]}
before=hashes();_,v,n,f=source(ROOT/'assets/models/meshy-e45e5d8.glb');c=v[f].mean(1)
domain=(np.abs(c[:,0])>.18)&(c[:,1]>.075)&(c[:,1]<.58)
bpy.context.view_layer.objects.active=ob;ob.select_set(True)
layer=mesh.uv_layers.new(name='M4C_ARMS_UV');mesh.uv_layers.active=layer
bpy.context.tool_settings.mesh_select_mode=(False,False,True)
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT')
edit=bmesh.from_edit_mesh(mesh);edit.faces.ensure_lookup_table()
for face in edit.faces:face.select_set(bool(domain[face.index]))
bmesh.update_edit_mesh(mesh,loop_triangles=False,destructive=False)
bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.012,area_weight=.1,correct_aspect=True,scale_to_bounds=True)
bpy.ops.object.mode_set(mode='OBJECT')
coords=np.empty(len(mesh.loops)*2,np.float32);mesh.uv_layers['M4C_ARMS_UV'].data.foreach_get('uv',coords);coords=coords.reshape(-1,3,2)
coords[domain]=.025+.95*coords[domain];coords[~domain]=(.997,.997)
mesh.uv_layers['M4C_ARMS_UV'].data.foreach_set('uv',coords.ravel())
mesh.uv_layers.active=mesh.uv_layers['M4C_SURFACE_UV'];mesh.uv_layers['M4C_SURFACE_UV'].active_render=True
# Edit-mode UV unwrap can discard Blender custom normals. Restore the exact
# validated per-corner normal vectors, without changing the source geometry.
bn=n[:,[0,2,1]].copy();bn[:,1]*=-1;mesh.normals_split_custom_set(bn[f].reshape(-1,3).tolist())
after=hashes();assert before==after,(before,after)
np.savez_compressed(OUT/'arms-uv-binding.npz',uv_blender=coords,domain=domain)
for node in mesh.materials[0].node_tree.nodes:
    if node.name.startswith('SHOW::'):node.outputs[0].default_value=0
s.camera.data.type='ORTHO';s.camera.data.sensor_fit='HORIZONTAL';s.camera.data.shift_x=s.camera.data.shift_y=0
s.cycles.samples=16;s.cycles.use_denoising=False;s.cycles.seed=0
meta={'baseCommit':'d552e23','oldSurfaceAndUV0':before,'after':after,'uv1SupportTriangles':int(domain.sum()),'geometryChanged':False,'frames':[]}
# The intermediate mesh stays in memory; the final authoring file is built
# from the frozen source plus this UV1 binding by render_arm_prototype.py.
for name,angle,target,scale,res in [
    ('reference-face',0,(0,.33,0),.90,(1200,1000)),
    ('reference-dos',180,(0,.33,0),.90,(1200,1000)),
    ('reference-profil-gauche',90,(.28,.33,-.015),.52,(900,1100)),
    ('reference-profil-droit',-90,(-.28,.33,-.015),.52,(900,1100))]:
    camera(s,angle,target,scale,res);render(s,CACHE/(name+'.png'))
    meta['frames'].append({'file':name+'.png','angle':angle,'target':list(target),'scale':scale,'resolution':list(res),'cameraMatrix':[list(r) for r in s.camera.matrix_world]})
    (CACHE/'reference-cameras.json').write_text(json.dumps(meta,indent=2)+'\n')
(OUT/'uv-preparation.json').write_text(json.dumps(meta,indent=2)+'\n');print('ARM_UV_COPY_READY',int(domain.sum()),flush=True)
