"""Check locality, unchanged topology/head/body, and serialized surface quality."""
import argparse,json,sys
from pathlib import Path
import bpy,numpy as np
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from assemble_head import sha
from check_head_assembly import triangle_keys,exported,areas,face_components
p=argparse.ArgumentParser();p.add_argument('--asset',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.asset.resolve();meta=json.loads((root/'assemblage.json').read_text())
assert sha(root/meta['master'])==meta['master_sha256']
assert sha(root/meta['comparison_master'])==meta['comparison_master_sha256']
assert sha(root/meta['comparison_glb'])==meta['comparison_glb_sha256']
bpy.ops.wm.open_mainfile(filepath=str(root/meta['master']),use_scripts=False)
scenes=[bpy.data.scenes[meta[k]] for k in ['scene_before','scene_after']]
objects=[next(o for o in s.objects if o.type=='MESH') for s in scenes]
v0,v=[np.array([p.co[:] for p in o.data.vertices]) for o in objects]
f0,f=[np.array([p.vertices[:] for p in o.data.polygons],np.int32) for o in objects]
assert np.array_equal(f0,f) and v0.shape==v.shape
z,x,y=v0[:,2],abs(v0[:,0]),v0[:,1]
# Conservative hard envelope independent of the smooth falloff implementation.
upper=.735+.04*np.clip((y+.005)/.04,0,1)**2*(3-2*np.clip((y+.005)/.04,0,1))
allowed=(z>.645)&(z<upper)&(x<.135)&(y>-.065)
delta=np.linalg.norm(v-v0,axis=1);changed=delta>0
assert not changed[~allowed].any() and delta.max()<.0030001
assert int(changed.sum())==meta['modified_vertices']
chin=(y<-.065)&(z>.695);hair=z>=.775;face=(y<-.005)&(z>=.735)
assert np.array_equal(v0[chin|hair|face],v[chin|hair|face])
assert np.array_equal(v0[z<=.645],v[z<=.645]) and np.array_equal(v0[x>=.135],v[x>=.135])
assert np.array_equal(v0.min(0),v.min(0)) and np.array_equal(v0.max(0),v.max(0))
oldn,n=[np.array([q.vector[:] for q in o.data.corner_normals]).reshape(-1,3,3) for o in objects]
protected=~allowed[f].any(1)
normal_error=float(np.linalg.norm(oldn[protected]-n[protected],axis=2).max());assert normal_error<.001
edge=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]);unique,counts=np.unique(np.sort(edge,axis=1),axis=0,return_counts=True)
assert (counts==2).all() and np.array_equal(np.unique(edge,axis=0),np.unique(edge[:,::-1],axis=0));assert areas(v,f).min()>1e-12
assert face_components(f)==[len(f)]
tree=BVHTree.FromPolygons(v.tolist(),f.tolist(),all_triangles=True);affected=changed[f].any(1)
contacts=[(i,j) for i,j in tree.overlap(tree) if i<j and (affected[i] or affected[j]) and not np.isin(f[i],f[j]).any()]
assert not contacts,('New local intersections',len(contacts),contacts[:5])
for path,vertices,faces in [(root/meta['export'],v,f),(root/meta['comparison_glb'],v0,f0)]:
 doc,ac=exported(path);prim=doc['meshes'][0]['primitives'][0];gv,gf=ac(prim['attributes']['POSITION']),ac(prim['indices']).reshape(-1,3)
 expected=vertices[:,[0,2,1]].copy();expected[:,2]*=-1
 assert np.array_equal(triangle_keys(expected[faces]),triangle_keys(gv[gf]))
 assert len(doc['meshes'])==len(doc['nodes'])==len(doc['materials'])==1 and not doc.get('textures')
assert objects[0].data.materials[0]==objects[1].data.materials[0]
lights=[{o.name:[o.data.energy,o.data.size,list(o.location)] for o in s.objects if o.type=='LIGHT'} for s in scenes]
assert lights[0]==lights[1] and len(lights[0])==5
# Local geometric roughness: adjacent face-normal angles on the interior domain.
sorted_edges=np.sort(edge,axis=1);order=np.lexsort((sorted_edges[:,1],sorted_edges[:,0]));pairs=np.tile(np.arange(len(f)),3)[order].reshape(-1,2)
interior=(allowed[f].all(1))
sel=interior[pairs].all(1)
def roughness(vertices):
 normals=np.cross(vertices[f[:,1]]-vertices[f[:,0]],vertices[f[:,2]]-vertices[f[:,0]])
 normals/=np.linalg.norm(normals,axis=1)[:,None]
 angles=np.degrees(np.arccos(np.clip(np.sum(normals[pairs[sel,0]]*normals[pairs[sel,1]],axis=1),-1,1)))
 return {'mean_adjacent_face_angle_degrees':float(angles.mean()),'p95_adjacent_face_angle_degrees':float(np.quantile(angles,.95))}
radial0=np.linalg.norm(v0[changed,:2]-np.array([-.0016,.015]),axis=1);radial=np.linalg.norm(v[changed,:2]-np.array([-.0016,.015]),axis=1)
report={'master_sha256':meta['master_sha256'],'reference_commit':'62000ae','before_surface_matches_published_glb':True,
 'topology_identical':True,'vertices_before':len(v0),'vertices_after':len(v),'triangles_before':len(f0),'triangles_after':len(f),'added_triangles':0,
 'modified_vertices':int(changed.sum()),'displacement_max_m':float(delta.max()),'displacement_mean_m':float(delta[changed].mean()),
 'local_modified_z_range_m':[float(z[changed].min()),float(z[changed].max())],
 'vertices_moved_outside_allowed_domain':0,'face_chin_and_hair_vertices_moved':0,'distant_body_vertices_moved':0,
 'protected_vertices_identical':int((~allowed).sum()),'global_bounds_identical':True,'protected_corner_normal_error_max':normal_error,
 'closed_edge_manifold':True,'consistent_face_orientation':True,'connected_components':1,'new_local_intersections':0,
 'glb_surface_matches_master_exactly':True,'same_material_and_five_lights':True,
 'mean_radial_change_among_modified_vertices_m':float((radial-radial0).mean()),
 'geometric_roughness_before':roughness(v0),'geometric_roughness_after':roughness(v),'verifier_sha256':sha(Path(__file__))}
(root/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('VERIFIED',json.dumps(report),flush=True)
