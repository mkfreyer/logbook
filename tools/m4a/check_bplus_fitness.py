"""Audit closed B+ fitness proxy surfaces and non-adjacent triangle crossings."""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils.bvhtree import BVHTree
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prepared',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.prepared=a.prepared.resolve()
bpy.ops.wm.open_mainfile(filepath=str(a.prepared/'model.blend'),use_scripts=False)
c=json.loads((a.prepared/'construction.json').read_text());objects=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.get('m4a_render')]
assert len(objects)==3
rows=[]

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

for ob in objects:
    mesh=ob.data;mesh.calc_loop_triangles()
    xyz=np.empty(len(mesh.vertices)*3,dtype=np.float64);mesh.vertices.foreach_get('co',xyz);xyz=xyz.reshape(-1,3)
    ix=np.empty(len(mesh.loop_triangles)*3,dtype=np.int32);mesh.loop_triangles.foreach_get('vertices',ix);ix=ix.reshape(-1,3)
    assert np.isfinite(xyz).all();t=xyz[ix];areas=np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1)
    assert np.all(areas>1e-12)
    bm=bmesh.new();bm.from_mesh(mesh);todo=set(bm.verts);parts=[]
    while todo:
        pending=[todo.pop()];count=0
        while pending:
            v=pending.pop();count+=1
            for edge in v.link_edges:
                other=edge.other_vert(v)
                if other in todo:todo.remove(other);pending.append(other)
        parts.append(count)
    boundary=sum(e.is_boundary for e in bm.edges);nonmanifold=sum(not e.is_manifold for e in bm.edges)
    loose=sum(not v.link_faces for v in bm.verts);euler=len(bm.verts)-len(bm.edges)+len(bm.faces);volume=bm.calc_volume(signed=True);bm.free()
    assert boundary==nonmanifold==loose==0 and len(parts)==1 and euler==2 and volume>0
    row={'object':ob.name,'role':ob['m4a_role'],'vertices':len(xyz),'triangles':len(ix),'components':len(parts),
         'boundary_edges':boundary,'nonmanifold_edges':nonmanifold,'loose_vertices':loose,
         'nonfinite_coordinates':0,'near_degenerate_triangles':0,'minimum_double_triangle_area_m2':float(areas.min()),
         'euler':euler,'genus':0,'signed_volume_m3':volume,'bounds_min':xyz.min(0).tolist(),'bounds_max':xyz.max(0).tolist()}
    if ob['m4a_role']=='body':
        row['self_crossing_check']=crossings(xyz,ix)
        for name in ['m4a_pectoral_mask','m4a_pectoral_L','m4a_pectoral_R']:
            attr=mesh.attributes[name];v=np.array([d.value for d in attr.data]);assert np.isfinite(v).all() and np.any(v>.5)
        row['demo_mask_attributes_present']=True
    rows.append(row)
assert sum(r['triangles'] for r in rows)==c['counts']['visible_triangles']
report={'variant':c['variant'],'source_sha256':hashlib.sha256((a.prepared/'model.blend').read_bytes()).hexdigest(),
        'objects':rows,'continuous_body':True,'separate_muscle_objects':0,
        'all_objects_closed_single_component_genus_zero':True,
        'limitations':['Self-crossing audit is on the research proxy, not every high-resolution authoring triangle.',
        'Non-coplanar crossings use segment/triangle narrow phase; coplanar candidates are reported, not classified.',
        'Eyes are intentionally separate fitted meshes; body/eye contact is not classified as an error.',
        'No rig, medical validation, application integration or iPhone performance test.']}
(a.prepared/'geometry-check.json').write_text(json.dumps(report,indent=2)+'\n')
print('BPLUS_FITNESS_CHECK',json.dumps({r['role']:r.get('self_crossing_check',{'closed':True}) for r in rows}),flush=True)
