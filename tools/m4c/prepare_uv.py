"""Create UVs only on a copy; positions, indices and original normals untouched."""
import json,math,sys
from pathlib import Path
import bpy,bmesh,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from scene import setup
root=Path(__file__).resolve().parents[2];out=root/'docs/m4c/meshy-huit-zones'
scene,ob,mat,v,n,f=setup(root);mesh=ob.data
bpy.context.view_layer.objects.active=ob;ob.select_set(True)
centroid=v[f].mean(1)
domain=(centroid[:,1]>.325)&(centroid[:,1]<.69)&(np.abs(centroid[:,0])<.327)
uv=mesh.uv_layers.new(name='M4C_SURFACE_UV');uv.active_render=True
for p in mesh.polygons:p.select=bool(domain[p.index])
bpy.context.tool_settings.mesh_select_mode=(False,False,True)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='DESELECT')
edit=bmesh.from_edit_mesh(mesh)
edit.faces.ensure_lookup_table()
for face in edit.faces: face.select_set(bool(domain[face.index]))
bmesh.update_edit_mesh(mesh,loop_triangles=False,destructive=False)
assert sum(face.select for face in edit.faces)==int(domain.sum())
bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.012,area_weight=.1,correct_aspect=True,scale_to_bounds=True)
bpy.ops.object.mode_set(mode='OBJECT')
uv=mesh.uv_layers.active
coords=np.empty((len(mesh.loops),2),np.float32);uv.data.foreach_get('uv',coords.ravel());coords=coords.reshape(-1,3,2)
coords[domain]=.025+.95*coords[domain];coords[~domain]=(.997,.997)
assert len(np.unique(coords[domain].reshape(-1,2),axis=0))>1000,'UV unwrap did not produce usable islands'
uv.data.foreach_set('uv',coords.ravel())
assert np.array_equal(np.array([p.co[:] for p in mesh.vertices],np.float32),np.column_stack([v[:,0],-v[:,2],v[:,1]]))
assert np.array_equal(np.array([p.vertices[:] for p in mesh.polygons]),f)
np.savez_compressed(out/'source-uv-binding.npz',uv_blender=coords,domain=domain)
(out/'uv-repair.json').write_text(json.dumps({'repaired_faces':[],'remaining_uv_overlap_samples':None},indent=2)+'\n')
scene['M4C']='UV only. No surface change. Awaiting anatomical placement validation.'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(out/'meshy-eight-zones.blend'),compress=True)
(out/'uv-preparation.json').write_text(json.dumps({'source_vertices':len(v),'source_triangles':len(f),'uv_support_triangles':int(domain.sum()),'source_positions_unchanged':True,'source_indices_unchanged':True,'uv_method':'Local upper-body smart project; multiple nonoverlapping UV islands with padding; elsewhere reserved neutral texel.'},indent=2)+'\n')
print('UV_ONLY_PREPARED',len(v),len(f),int(domain.sum()),flush=True)
