"""Compare B and B+ topology, preserved attributes and evaluated geometric defects."""
import argparse,sys,json,hashlib,collections
from pathlib import Path
import bpy,numpy as np

def coordinates(mesh):
 a=np.empty((len(mesh.vertices),3),dtype=np.float32);mesh.vertices.foreach_get('co',a.ravel());return a

def fingerprint(a):return hashlib.sha256(a.tobytes()).hexdigest()

def topology(mesh):
 return [(tuple(p.vertices),p.material_index) for p in mesh.polygons]

def evaluate(obj):
 graph=bpy.context.evaluated_depsgraph_get()
 return bpy.data.meshes.new_from_object(obj.evaluated_get(graph),depsgraph=graph)

def triangles(mesh):
 mesh.calc_loop_triangles();a=np.empty((len(mesh.loop_triangles),3),dtype=np.int32);mesh.loop_triangles.foreach_get('vertices',a.ravel());return a

def normals(a,tris):return np.cross(a[tris[:,1]]-a[tris[:,0]],a[tris[:,2]]-a[tris[:,0]])

p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--variant',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
names=['GEO-body_male_realistic','GEO-body_male_realistic.eye.L','GEO-body_male_realistic.eye.R']
loaded=[]
for path in [a.source,a.variant]:
 with bpy.data.libraries.load(str(path),link=False) as (src,dst):dst.objects=list(names)
 for o in dst.objects:bpy.context.collection.objects.link(o)
 loaded.append(list(dst.objects))
bpy.context.view_layer.update()
source,variant=loaded[0][0],loaded[1][0]
original=coordinates(source.data);variant_base=coordinates(variant.data)
basis=np.array([list(v.co) for v in variant.data.shape_keys.key_blocks[0].data],dtype=np.float32)
key=np.array([list(v.co) for v in variant.data.shape_keys.key_blocks[1].data],dtype=np.float32)
assert np.array_equal(original,variant_base) and np.array_equal(original,basis)
assert topology(source.data)==topology(variant.data)
assert [list(e.vertices) for e in source.data.edges]==[list(e.vertices) for e in variant.data.edges]
uv_same=all(np.array_equal(np.array([v.uv[:] for v in sa.data]),np.array([v.uv[:] for v in va.data])) for sa,va in zip(source.data.uv_layers,variant.data.uv_layers))
assert len(source.data.uv_layers)==len(variant.data.uv_layers) and uv_same
fs_same=[v.value for v in source.data.attributes['.sculpt_face_set'].data]==[v.value for v in variant.data.attributes['.sculpt_face_set'].data];assert fs_same
eyes=[]
for so,vo in zip(loaded[0][1:],loaded[1][1:]):
 same=np.array_equal(coordinates(so.data),coordinates(vo.data)) and so.matrix_world==vo.matrix_world;assert same;eyes.append(same)
keyblock=variant.data.shape_keys.key_blocks[1];keyblock.value=0;bpy.context.view_layer.update()
sm=evaluate(source);bm=evaluate(variant);orig_high=coordinates(sm);basis_high=coordinates(bm)
assert np.array_equal(orig_high,basis_high)
keyblock.value=1;bpy.context.view_layer.update();vm=evaluate(variant);plus_high=coordinates(vm)
st,vt=triangles(sm),triangles(vm);assert np.array_equal(st,vt)
assert np.isfinite(plus_high).all()
nt,nv=normals(orig_high,st),normals(plus_high,vt)
area_orig=np.linalg.norm(nt,axis=1)/2;area_plus=np.linalg.norm(nv,axis=1)/2
threshold=1e-12;new_degenerate=int(np.sum((area_orig>threshold)&(area_plus<=threshold)));assert new_degenerate==0
flips=int(np.sum(np.einsum('ij,ij->i',nt,nv)<0));assert flips==0
edge_counts=collections.Counter(tuple(sorted((f[i],f[(i+1)%len(f)]))) for f,_ in topology(source.data) for i in range(len(f)))
scale=1.06503615750482
displacements=np.linalg.norm(plus_high-orig_high,axis=1)*scale
base_edges=np.array([e.vertices[:] for e in source.data.edges]);oldlength=np.linalg.norm(original[base_edges[:,0]]-original[base_edges[:,1]],axis=1);newlength=np.linalg.norm(key[base_edges[:,0]]-key[base_edges[:,1]],axis=1);ratios=newlength[oldlength>1e-10]/oldlength[oldlength>1e-10]
# Fixed landmarks checked on evaluated geometry in the original normalized reference.
world=np.array([list(source.matrix_world@v.co) for v in sm.vertices]);center=np.array([-2.2643768787384033,-.033877987414598465,-.005640706978738308]);normalized=(world-center)*scale
unchanged={}
for name,mask in {'head':normalized[:,2]>=1.53,'feet':normalized[:,2]<=.20,'hands_and_wrists':(abs(normalized[:,0])>.36)&(normalized[:,2]<1.04)}.items():
 unchanged[name]=float(displacements[mask].max());assert unchanged[name]<1e-6
sections=[]
# Source vertex membership is held constant so each row compares the same surface band.
for name,zlo,zhi,absxlo,absxhi in [('upper_chest',1.31,1.43,0,.19),('deltoids',1.36,1.48,.18,.29),('upper_arms',1.18,1.33,.23,.34),('back_torso',1.16,1.37,.06,.20),('quadriceps',.62,.82,.06,.22)]:
 mask=(normalized[:,2]>=zlo)&(normalized[:,2]<=zhi)&(abs(normalized[:,0])>=absxlo)&(abs(normalized[:,0])<=absxhi)
 # Width and depth of the same bilateral surface region, not circumferences or biological metrics.
 old=orig_high[mask];new=plus_high[mask]
 sections.append({'region':name,'sampled_vertices':int(mask.sum()),'source_space_width_before':float(np.ptp(old[:,0])),'source_space_width_after':float(np.ptp(new[:,0])),'source_space_depth_before':float(np.ptp(old[:,1])),'source_space_depth_after':float(np.ptp(new[:,1]))})
r={'source_original_basis_preserved':True,'base_topology_and_material_indices_identical':True,'uv_layers_identical':uv_same,'face_sets_identical':fs_same,'eyes_geometry_and_transforms_identical':eyes,'source_and_variant_at_strength_zero_identical_evaluated_geometry':True,'base_vertices':len(original),'base_faces':len(source.data.polygons),'base_triangles':len(triangles(source.data)),'evaluated_vertices':len(plus_high),'evaluated_triangles':len(vt),'original_boundary_edges':sum(c==1 for c in edge_counts.values()),'original_nonmanifold_edges_over_two_faces':sum(c>2 for c in edge_counts.values()),'topology_changes':0,'new_degenerate_triangles_threshold_1e_12':new_degenerate,'triangle_normal_reversals_over_90_degrees':flips,'base_edge_length_ratio_min':float(ratios.min()),'base_edge_length_ratio_max':float(ratios.max()),'maximum_evaluated_displacement_at_height_1_8':float(displacements.max()),'fixed_landmark_max_displacements':unchanged,'fixed_landmark_tolerance':1e-6,'lower_leg_falloff_max_below_z_0_49':float(displacements[normalized[:,2]<=.49].max()),'source_evaluated_position_sha256':fingerprint(orig_high),'variant_evaluated_position_sha256':fingerprint(plus_high),'shape_key_position_sha256':fingerprint(key),'sections':sections,'limits':['No anatomical segmentation or medical validation','No exhaustive self-intersection or rig deformation test','No mobile GPU, FPS, GLB or interactive integration test']}
a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
