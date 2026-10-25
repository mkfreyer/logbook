"""Verify native donor head/chin and preserved body, not just bounds or renders."""
import argparse,json,sys
from pathlib import Path
import bpy,numpy as np
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from assemble_head import sha,source
from check_head_assembly import triangle_keys,areas,point_plane_error,clipped_areas,face_components,exported


def compound_areas(v,f,planes):
 out=np.zeros(len(f))
 for i,face in enumerate(f):
  polygon=list(v[face])
  for plane in planes:
   n=np.array(plane['normal']);offset=plane['offset'];new=[]
   for j,p in enumerate(polygon):
    q=polygon[(j+1)%len(polygon)];a=float(p@n-offset);b=float(q@n-offset)
    if a>=0:new.append(p)
    if (a>=0)!=(b>=0):new.append(p+(q-p)*(-a/(b-a)))
   polygon=new
   if not polygon:break
  if len(polygon)>=3:out[i]=sum(np.linalg.norm(np.cross(polygon[k]-polygon[0],polygon[k+1]-polygon[0]))/2 for k in range(1,len(polygon)-1))
 return out

p=argparse.ArgumentParser();p.add_argument('--asset',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.asset.resolve();meta=json.loads((root/'assemblage.json').read_text())
assert sha(root/meta['master'])==meta['master_sha256']
for kind in ['body','head']:assert sha(root/meta[f'{kind}_source'])==meta[f'{kind}_source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(root/meta['master']),use_scripts=False)
after=bpy.data.scenes[meta['scene_after']];ob=next(o for o in after.objects if o.type=='MESH')
v=np.array([p.co[:] for p in ob.data.vertices]);f=np.array([p.vertices[:] for p in ob.data.polygons],np.int32)
ids=np.array([x.value for x in ob.data.attributes['source_triangle'].data]);nb=meta['retained_body_triangles_after_cut'];nj=meta['bridge_triangles'];nh=nb+nj
bv,bf,_=source(root/meta['body_source']);dv,df,_=source(root/meta['head_source']);dv=dv*meta['head_scale_uniform']+np.array(meta['head_translation_m']);cut=meta['body_cut_z_m']
reference=bpy.data.scenes[meta['scene_before']];ro=next(o for o in reference.objects if o.type=='MESH')
rv=np.array([p.co[:] for p in ro.data.vertices]);rf=np.array([p.vertices[:] for p in ro.data.polygons],np.int32)
assert np.array_equal(rv,dv.astype(np.float32).astype(float)) and np.array_equal(rf,df)
area=areas(v,f);body_error=point_plane_error(v[f[:nb]],bv[bf[ids[:nb]]]);assert body_error<2e-7
body_areas=clipped_areas(bv,bf,cut,True);actual=np.bincount(ids[:nb],weights=area[:nb],minlength=len(bf));assert abs(body_areas-actual).max()<2e-8 and abs(body_areas-actual).sum()<1e-6
protected=bv[bf,2].max(1)<cut-2e-6;kept=v[f,2].max(1)<cut-2e-6
assert np.array_equal(triangle_keys(bv[bf[protected]]),triangle_keys(v[f[kept]]))
bodyref=bpy.data.scenes[meta['body_reference_scene']];old=next(o for o in bodyref.objects if o.type=='MESH')
ov=np.array([p.co[:] for p in old.data.vertices]);of=np.array([p.vertices[:] for p in old.data.polygons],np.int32)
oldmask=ov[of,2].max(1)<cut-2e-6
assert np.array_equal(triangle_keys(ov[of[oldmask]]),triangle_keys(v[f[kept]]))
head_error=point_plane_error(v[f[nh:]],dv[df[ids[nh:]]]);assert head_error<2e-7
expected=compound_areas(dv,df,meta['head_cut_planes']);actual=np.bincount(ids[nh:],weights=area[nh:],minlength=len(df));error=abs(expected-actual)
assert error.max()<2e-8 and error.sum()<1e-6
full=np.ones(len(df),bool)
for plane in meta['head_cut_planes']:full&=(dv[df]@np.array(plane['normal'])>plane['offset']+2e-6).all(1)
head_full=full[ids[nh:]]
assert np.array_equal(triangle_keys(dv[df[full]]),triangle_keys(v[f[nh:][head_full]]))
chin=(dv[df][:,:,2]>.695).all(1)&(dv[df][:,:,1]<-.065).all(1)
assert full[chin].all(),('Native chin clipped',int((chin&~full).sum()))
face_hair=(dv[df][:,:,2]>.735).all(1);assert full[face_hair].all()
edges=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]);unique,counts=np.unique(np.sort(edges,axis=1),axis=0,return_counts=True)
assert (counts==2).all() and np.array_equal(np.unique(edges,axis=0),np.unique(edges[:,::-1],axis=0));assert area.min()>1e-12
assert face_components(f)==[len(f)]
tree=BVHTree.FromPolygons(v.tolist(),f.tolist(),all_triangles=True)
contacts=[(i,j) for i,j in tree.overlap(tree) if i<j and max(i,j)>=nb and not np.isin(f[i],f[j]).any()]
assert not contacts,('Head/neck intersections',len(contacts),contacts[:5])
doc,ac=exported(root/meta['export']);pr=doc['meshes'][0]['primitives'][0];gv,gf=ac(pr['attributes']['POSITION']),ac(pr['indices']).reshape(-1,3)
expected_v=v[:,[0,2,1]].copy();expected_v[:,2]*=-1
assert np.array_equal(triangle_keys(expected_v[f]),triangle_keys(gv[gf]))
assert len(doc['meshes'])==len(doc['nodes'])==len(doc['materials'])==1 and not doc.get('textures')
assert np.array_equal(v.min(0),ov.min(0)) and np.array_equal(v.max(0),ov.max(0))
report={'master_sha256':meta['master_sha256'],'native_donor_reference_scene_exact':True,
 'source_head_surface_plane_error_max_m':head_error,'source_head_clipped_area_error_max_m2':float(error.max()),
 'head_source_whole_triangles_identical':int(full.sum()),'native_chin_triangles_verified':int(chin.sum()),'native_chin_clipped_triangles':0,
 'face_and_hair_triangles_verified':int(face_hair.sum()),'head_source_vertices_sculpted_or_moved':0,
 'body_source_whole_triangles_identical':int(protected.sum()),'body_preserved_against_dbba75e':True,
 'body_source_surface_plane_error_max_m':body_error,'body_neck_strip_replaced_m':meta['restored_body_neck_strip_m'],
 'local_bridge_z_range_m':meta['local_z_range_m'],'closed_edge_manifold':True,'consistent_orientation':True,
 'new_head_neck_intersections':0,'connected_components':1,'global_bounds_identical':True,
 'glb_surface_matches_master_exactly':True,'triangles':len(f),'body_triangles':nb,'bridge_triangles':nj,'head_triangles':len(f)-nh,
 'verifier_sha256':sha(Path(__file__))}
(root/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('VERIFIED',json.dumps(report),flush=True)
