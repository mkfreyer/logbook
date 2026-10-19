"""Measure BP3D fitness research meshes without claiming visual approval."""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils.bvhtree import BVHTree
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prepared',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.prepared=a.prepared.resolve()
bpy.ops.wm.open_mainfile(filepath=str(a.prepared/'model.blend'),use_scripts=False)
c=json.loads((a.prepared/'construction.json').read_text());rows=[]

def crossings(xyz,ix):
    tree=BVHTree.FromPolygons(xyz.tolist(),ix.tolist(),all_triangles=True,epsilon=0)
    pairs=np.array(tree.overlap(tree),dtype=np.int32).reshape(-1,2)
    pairs=pairs[pairs[:,0]<pairs[:,1]]
    if len(pairs):
        shared=np.any(ix[pairs[:,0]][:,:,None]==ix[pairs[:,1]][:,None,:],axis=(1,2))
        pairs=pairs[~shared]
    if not len(pairs):return {'nonadjacent_BVH_candidates':0,'proper_triangle_crossings':0,'coplanar_candidates':0,'crossings_by_region':{},'examples':[]}
    A=xyz[ix[pairs[:,0]]];B=xyz[ix[pairs[:,1]]];hit=np.zeros(len(pairs),dtype=bool)
    # Segment/triangle narrow phase, not merely overlapping bounding boxes.
    for start,end in [(A,B),(B,A)]:
        e1=end[:,1]-end[:,0];e2=end[:,2]-end[:,0]
        for edge in range(3):
            origin=start[:,edge];direction=start[:,(edge+1)%3]-origin
            h=np.cross(direction,e2);det=np.sum(e1*h,axis=1);valid=np.abs(det)>1e-15
            inv=np.divide(1,det,out=np.zeros_like(det),where=valid)
            s=origin-end[:,0];u=np.sum(s*h,axis=1)*inv;q=np.cross(s,e1)
            v=np.sum(direction*q,axis=1)*inv;t=np.sum(e2*q,axis=1)*inv
            eps=1e-7
            hit|=valid&(u>=-eps)&(v>=-eps)&(u+v<=1+eps)&(t>eps)&(t<1-eps)
    na=np.cross(A[:,1]-A[:,0],A[:,2]-A[:,0]);nb=np.cross(B[:,1]-B[:,0],B[:,2]-B[:,0])
    parallel=np.linalg.norm(np.cross(na,nb),axis=1)<1e-8*np.linalg.norm(na,axis=1)*np.linalg.norm(nb,axis=1)
    distance=np.abs(np.sum((B[:,0]-A[:,0])*na,axis=1))/np.linalg.norm(na,axis=1)
    coplanar=parallel&(distance<1e-9)
    centers=xyz[ix[pairs[hit]]].mean(axis=(1,2))
    regions={'feet':0,'head':0,'hands':0,'sculptable_body':0}
    for co in centers:
        region='feet' if co[2]<.165 else 'head' if co[2]>1.548 else 'hands' if abs(co[0])>.395 and co[2]<1.02 else 'sculptable_body'
        regions[region]+=1
    return {'crossings_by_region':regions,'crossing_centers_min':centers.min(0).tolist() if len(centers) else None,
            'crossing_centers_max':centers.max(0).tolist() if len(centers) else None,'nonadjacent_BVH_candidates':len(pairs),'proper_triangle_crossings':int(hit.sum()),
            'coplanar_candidates':int(coplanar.sum()),
            'examples':[{'faces':[int(i),int(j)],'center':xyz[ix[[i,j]]].mean(axis=(0,1)).tolist()} for i,j in pairs[hit][:20]]}

for ob in [o for o in bpy.context.scene.objects if o.type=='MESH' and o.get('m4a_render')]:
 mesh=ob.data;mesh.calc_loop_triangles();xyz=np.array([v.co[:] for v in mesh.vertices]);ix=np.array([t.vertices[:] for t in mesh.loop_triangles])
 finite=bool(np.isfinite(xyz).all());t=xyz[ix];area=np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1)
 bm=bmesh.new();bm.from_mesh(mesh);todo=set(bm.verts);parts=[]
 while todo:
  stack=[todo.pop()];count=0
  while stack:
   v=stack.pop();count+=1
   for e in v.link_edges:
    n=e.other_vert(v)
    if n in todo:todo.remove(n);stack.append(n)
  parts.append(count)
 boundary=sum(e.is_boundary for e in bm.edges);nonmanifold=sum(not e.is_manifold for e in bm.edges);loose=sum(not v.link_faces for v in bm.verts)
 euler=len(bm.verts)-len(bm.edges)+len(bm.faces);volume=bm.calc_volume(signed=True);bm.free()
 r={'object':ob.name,'role':ob['m4a_role'],'vertices':len(xyz),'triangles':len(ix),'components':len(parts),'boundary_edges':boundary,'nonmanifold_edges':nonmanifold,'loose_vertices':loose,'coordinates_finite':finite,'near_degenerate_triangles':int((area<=1e-12).sum()),'euler':euler,'genus_if_closed_orientable':int((2*len(parts)-euler)/2) if nonmanifold==0 else None,'signed_volume':volume}
 if ob['m4a_role']=='body':
  r['self_crossing_check']=crossings(xyz,ix)
  attr=mesh.attributes['m4a_fitness_zone'];assert attr.domain=='FACE' and attr.data_type=='INT'
  labels=np.array([v.value for v in attr.data]);r['region_ids']=sorted(set(int(x) for x in labels));assert r['region_ids']==list(range(31))
 r['geometry_signature']=hashlib.sha256(xyz.tobytes()+ix.tobytes()+(labels.tobytes() if ob['m4a_role']=='body' else b'')).hexdigest()
 rows.append(r)
assert len(rows)==3 and sum(r['triangles'] for r in rows)==c['counts']['visible_triangles']
report={'variant':c['variant'],'source_sha256':hashlib.sha256((a.prepared/'model.blend').read_bytes()).hexdigest(),'objects':rows,'segmentation':'Provisional face labels; not a final anatomical partition.','limitations':['A closed connected mesh can retain handles or anatomically poor junctions.','Nonadjacent triangle intersections use segment/triangle narrow phase; coplanar candidates are reported, not classified.','Separate fitted eyes are intentional; body/eye contacts are not tested.','No rig, iPhone performance or medical validation.']}
review=a.prepared/'renders/scene-review.blend'
if review.exists():
 bpy.ops.wm.open_mainfile(filepath=str(review),use_scripts=False)
 by_name={r['object']:r for r in rows}
 for ob in [o for o in bpy.context.scene.objects if o.type=='MESH' and o.get('m4a_render')]:
  mesh=ob.data;mesh.calc_loop_triangles();xyz=np.array([v.co[:] for v in mesh.vertices]);ix=np.array([t.vertices[:] for t in mesh.loop_triangles]);labels=np.array([d.value for d in mesh.attributes['m4a_fitness_zone'].data]) if ob['m4a_role']=='body' else None
  signature=hashlib.sha256(xyz.tobytes()+ix.tobytes()+(labels.tobytes() if labels is not None else b'')).hexdigest()
  assert signature==by_name[ob.name]['geometry_signature'],ob.name
 report['review_scene_geometry_and_labels_unchanged']=True
 report['review_scene_sha256']=hashlib.sha256(review.read_bytes()).hexdigest()
(a.prepared/'geometry-check.json').write_text(json.dumps(report,indent=2)+'\n')
print('BP3D_FITNESS_AUDIT',json.dumps(rows),flush=True)
