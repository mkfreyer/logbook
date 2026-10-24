"""Rebuild two local surface patches, rather than dragging hidden old folds.

Requires the free, permissively licensed mapbox-earcut and Shapely authoring
tools. They are NOT application/runtime dependencies. NumPy/SciPy are reused.
"""
import argparse,json,sys,hashlib
from pathlib import Path
import numpy as np
from scipy import ndimage as ndi
from scipy.spatial import cKDTree

p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--guides',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--deps',type=Path)
a=p.parse_args()
if a.deps:sys.path.insert(0,str(a.deps.resolve()))
import mapbox_earcut
from shapely.geometry import Polygon,Point
from shapely.ops import unary_union

# Share the audited P4 chart and thin-plate field, without executing the former
# vertex-displacement path. That path is not used to produce this final mesh.
helper=Path(__file__).with_name('reconstruction_guides_surface.py');code=helper.read_text()
setup=code.split('# Adaptive edge')[0]
solve='yy,xx=np.mgrid'+code.split('yy,xx=np.mgrid',1)[1].split('fair_target=',1)[0]
argv=sys.argv;sys.argv=['field','--source',str(a.source),'--guides',str(a.guides),'--output',str(a.output)]
n={'__file__':str(helper)};exec(compile(setup+'\n'+solve,str(helper),'exec'),n);sys.argv=argv
root=a.output;root.mkdir(parents=True,exist_ok=True)
v0,f0,uv0=n['original_v'],n['original_f'],n['original_uv'];D,R=n['D'],n['R']
smooth=n['smooth'];sample=n['sample'];front=n['front'];field=n['base'];paths=n['paths']
sx,sy=n['sx'],n['sy'];project=n['project'];core=n['belly_value']

centers=v0[f0].mean(1);cuv=project(centers)
L=n['domain'](centers,cuv);x,y=cuv.T
inside1=(x>L[0][0])&(x<L[0][1])&(y>281)&(y<381)
inside2=(x>L[1][0])&(x<L[1][1])&(y>68)&(y<381)
gap=sample(front,cuv)-centers@D
protected=(core(uv0)[f0]<1.18).any(1)
# Keep all silhouette-support faces and the main belly as actual original faces.
from scipy.spatial import ConvexHull
support=set()
for axis in range(3):
    support.update([int(v0[:,axis].argmin()),int(v0[:,axis].argmax())])
silhouette=np.isin(f0,list(support)).any(1)
selected=(inside1|inside2)&(gap<.020)&~protected&~silhouette
# Fill enclosed, unprotected face islands (the old folded trough bottoms).
# The exterior/back sheet and the protected belly remain large fixed components.
face_edges={}
for fi,tri in enumerate(f0):
    for edge in [(tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])]:
        face_edges.setdefault(tuple(sorted(map(int,edge))),[]).append(fi)
adj=[pair for pair in face_edges.values()if len(pair)==2]
neighbors=[[]for _ in f0]
for i,j in adj:neighbors[i].append(j);neighbors[j].append(i)
unseen=set(np.flatnonzero(~selected).tolist())
while unseen:
    stack=[unseen.pop()];component=[]
    while stack:
        fi=stack.pop();component.append(fi)
        for j in neighbors[fi]:
            if j in unseen:unseen.remove(j);stack.append(j)
    ids=np.array(component)
    if len(ids)<120 and not(protected[ids]|silhouette[ids]).any() and (inside1[ids]|inside2[ids]).any():selected[ids]=True
unseen=set(np.flatnonzero(selected).tolist());sizes=[]
while unseen:
    stack=[unseen.pop()];component=[]
    while stack:
        fi=stack.pop();component.append(fi)
        for j in neighbors[fi]:
            if j in unseen:unseen.remove(j);stack.append(j)
    sizes.append(len(component))
    if len(component)<24:selected[np.array(component)]=False
print('PATCH_COMPONENTS',sizes,flush=True)

def boundary_loops(faces):
    edge={}
    for tri in faces:
        for u,w in zip(tri,np.roll(tri,-1)):
            key=tuple(sorted((int(u),int(w))));edge[key]=edge.get(key,0)+1
    boundary=[e for e,count in edge.items()if count==1]
    graph={}
    for u,w in boundary:graph.setdefault(u,[]).append(w);graph.setdefault(w,[]).append(u)
    bad=[u for u,nb in graph.items()if len(nb)!=2]
    if bad:return None,bad
    unseen=set(graph);loops=[]
    while unseen:
        start=min(unseen);loop=[start];prev=None;cur=start
        while True:
            choices=graph[cur];nxt=choices[0]if choices[0]!=prev else choices[1]
            if nxt==start:break
            assert nxt not in loop
            loop.append(nxt);prev,cur=cur,nxt
        unseen.difference_update(loop);loops.append(loop)
    return loops,[]

# Resolve face sets touching only at one vertex before constructing the border.
for _ in range(12):
    loops,bad=boundary_loops(f0[selected])
    if not bad:break
    for vertex in bad:
        incident=(f0==vertex).any(1)
        if (protected[incident]|silhouette[incident]).any():selected[incident]=False
        else:selected[incident&(gap<.025)]=True
assert loops is not None,('non simple patch borders',bad)
polys=[Polygon(uv0[loop])for loop in loops]
from shapely.validation import explain_validity
original_v=v0.copy();original_uv=uv0.copy()
fixed_vertices=np.unique(np.r_[np.flatnonzero(core(uv0)<=1.18),np.array(list(support),int),f0[protected].ravel()])
for loop,poly in zip(loops,polys):
    if poly.is_valid:continue
    ids=np.array(loop);coords=uv0[ids].copy();frozen=np.isin(ids,fixed_vertices)
    for _ in range(80):
        trial=coords+.25*((np.roll(coords,1,axis=0)+np.roll(coords,-1,axis=0))*.5-coords)
        trial[frozen]=original_uv[ids[frozen]]
        motion=(trial-original_uv[ids])/[sx,sy];length=np.linalg.norm(motion,axis=1)
        trial=original_uv[ids]+(trial-original_uv[ids])*np.minimum(1,.0025/np.maximum(length,1e-12))[:,None]
        coords=trial
        if Polygon(coords).is_valid:break
    uv0[ids]=coords
shift=uv0-original_uv;v0=v0+shift[:,0,None]*R/sx;v0[:,2]-=shift[:,1]/sy
polys=[Polygon(uv0[loop])for loop in loops]
for i,poly in enumerate(polys):
    assert poly.is_valid and poly.area>1e-4,('invalid projected border',i,explain_validity(poly),poly.area)
print('PATCH_BORDERS',len(loops),[len(loop)for loop in loops],flush=True)

# Odd/even containment assigns holes to their outer border. Earcut retains every
# existing border segment, ensuring an exact stitch to the untouched P4 mesh.
outer=[]
for i,poly in enumerate(polys):
    depth=sum(polys[j].contains(poly.representative_point())and polys[j].area>poly.area for j in range(len(polys))if j!=i)
    if depth%2==0:outer.append(i)
patch_faces=[];domain_polys=[]
for i in outer:
    holes=[j for j in range(len(polys))if j!=i and polys[j].area<polys[i].area and polys[i].contains(polys[j].representative_point())
           and not any(polys[k].area<polys[i].area and polys[k].area>polys[j].area and polys[k].contains(polys[j].representative_point())for k in range(len(polys))if k not in [i,j])]
    rings=[loops[i]]+[loops[j]for j in holes];indices=np.array([v for ring in rings for v in ring],int)
    ends=np.cumsum([len(ring)for ring in rings]).astype(np.uint32)
    tri=mapbox_earcut.triangulate_float64(uv0[indices].astype(np.float64),ends).reshape(-1,3)
    patch_faces.extend(indices[tri].tolist())
    domain_polys.append(Polygon(uv0[loops[i]],[uv0[loops[j]]for j in holes]))
region=unary_union(domain_polys)
fpatch=np.array(patch_faces,int)
area=np.cross(uv0[fpatch[:,1]]-uv0[fpatch[:,0]],uv0[fpatch[:,2]]-uv0[fpatch[:,0]])
fpatch[area>0]=fpatch[area>0][:,[0,2,1]]
v=v0.copy();uv=uv0.copy();boundary_ids=np.unique(np.array([x for loop in loops for x in loop]))

# Split only internal patch edges; the original P4 border and outside faces do
# not change topology. Midpoint positions use the source P4 height chart.
rounds=[]
for iteration in range(8):
    edges=np.sort(np.concatenate([fpatch[:,[0,1]],fpatch[:,[1,2]],fpatch[:,[2,0]]]),axis=1)
    unique,count=np.unique(edges,axis=0,return_counts=True)
    length=np.linalg.norm((uv[unique[:,0]]-uv[unique[:,1]])/[sx,sy],axis=1)
    split=unique[(count==2)&(length>.0017)]
    if not len(split):break
    newuv=uv[split].mean(1)
    xyz=n['target']+((newuv[:,0]-160)/sx)[:,None]*R
    xyz[:,2]+=(192-newuv[:,1])/sy
    xyz+=(sample(front,newuv)-xyz@D)[:,None]*D
    ids=np.arange(len(v),len(v)+len(split));lookup={tuple(e):int(i)for e,i in zip(split,ids)}
    v=np.vstack([v,xyz]);uv=np.vstack([uv,newuv]);parts=[]
    for tri in fpatch:
        mids=[lookup.get(tuple(sorted(e)),-1)for e in [(tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])]]
        count=sum(i>=0 for i in mids);A,B,C=map(int,tri)
        if count==0:q=[(A,B,C)]
        elif count==3:
            ab,bc,ca=mids;q=[(A,ab,ca),(ab,B,bc),(ca,bc,C),(ab,bc,ca)]
        elif count==1:
            k=next(i for i,m in enumerate(mids)if m>=0);A,B,C=map(int,np.roll(tri,-k));m=mids[k];q=[(A,m,C),(m,B,C)]
        else:
            k=(next(i for i,m in enumerate(mids)if m<0)+1)%3;A,B,C=map(int,np.roll(tri,-k));ab,bc=mids[k],mids[(k+1)%3]
            if np.linalg.norm(uv[ab]-uv[C])<=np.linalg.norm(uv[A]-uv[bc]):q=[(B,bc,ab),(A,ab,C),(ab,bc,C)]
            else:q=[(B,bc,ab),(A,ab,bc),(A,bc,C)]
        parts.extend(q)
    fpatch=np.array(parts,int);rounds.append({'round':iteration+1,'new_vertices':len(split),'patch_triangles':len(fpatch)})

boundary_geometry=region.boundary
patch_vertices=np.unique(fpatch)
dist=np.array([boundary_geometry.distance(Point(p))for p in uv[patch_vertices]])/sx
blend=smooth(dist/.0028)
blend[np.isin(patch_vertices,boundary_ids)]=0
weight=np.zeros(len(v));weight[patch_vertices]=blend
target_depth=ndi.map_coordinates(field,[uv[:,1],uv[:,0]],order=3,mode='nearest')
z=v@D;cut=np.zeros(len(v))
for name,start,end in [('nouveau_1_terminaison',292,378),('nouveau_2',72,379)]:
    pts=paths[name];_,ix=cKDTree(pts).query(uv)
    tangent=np.gradient(pts,axis=0);tangent/=np.linalg.norm(tangent,axis=1)[:,None]
    normal=np.c_[-tangent[:,1],tangent[:,0]];signed=np.einsum('ij,ij->i',uv-pts[ix],normal[ix])
    distance=np.abs(signed)*np.sqrt((normal[ix,0]/sx)**2+(normal[ix,1]/sy)**2)
    profile=np.where(distance<.006,(1-(np.minimum(distance,.006)/.006)**2)**3,0)
    taper=smooth((pts[ix,1]-start)/13)*smooth((end-pts[ix,1])/13)
    cut=np.maximum(cut,.0026*profile*taper)
depth=z+weight*(target_depth-z-cut)
q=v+(depth-z)[:,None]*D
q[boundary_ids]=v0[boundary_ids]
outside=np.flatnonzero(~selected);full_f=np.vstack([f0[outside],fpatch])
parent=np.r_[outside,np.maximum(n['front_ids'][np.clip(np.rint(uv[fpatch].mean(1)[:,1]*3).astype(int),0,1151),
                                              np.clip(np.rint(uv[fpatch].mean(1)[:,0]*3).astype(int),0,959)],0)]
used=np.unique(full_f);retained=used[used<len(v0)];added=used[used>=len(v0)];order=np.r_[retained,added]
remap=np.full(len(v),-1,int);remap[order]=np.arange(len(order));full_f=remap[full_f]
q,v,uv,weight=q[order],v[order],uv[order],weight[order]
# Map reference corners to source triangles for UVs, weights and preserved normals.
corner_parent=np.repeat(parent[:,None],3,axis=1)
patch_uv=uv[full_f[len(outside):]]
corner_parent[len(outside):]=np.maximum(n['front_ids'][np.clip(np.rint(patch_uv[:,:,1]*3).astype(int),0,1151),np.clip(np.rint(patch_uv[:,:,0]*3).astype(int),0,959)],0)
tri_uv=original_uv[f0[corner_parent]];P=uv[full_f]-tri_uv[:,:,0]
U,V=tri_uv[:,:,1]-tri_uv[:,:,0],tri_uv[:,:,2]-tri_uv[:,:,0]
den=U[:,:,0]*V[:,:,1]-U[:,:,1]*V[:,:,0]
b=(P[:,:,0]*V[:,:,1]-P[:,:,1]*V[:,:,0])/den
c=(U[:,:,0]*P[:,:,1]-U[:,:,1]*P[:,:,0])/den
bary=np.stack([1-b-c,b,c],axis=2)
# For untouched original faces, exact one-hot weights avoid any projection noise.
bary[:len(outside)]=np.eye(3)[None,:,:]
vp=np.zeros(len(v),int);vb=np.zeros((len(v),3))
for k in range(3):vp[full_f[:,k]]=corner_parent[:,k];vb[full_f[:,k]]=bary[:,k]
v=np.einsum('ij,ijk->ik',vb,original_v[f0[vp]])
v[:len(retained)]=original_v[retained]
vol=lambda vv,ff:float(np.einsum('ij,ij->i',vv[ff[:,0]],np.cross(vv[ff[:,1]],vv[ff[:,2]])).sum()/6)
q=q.astype(np.float32).astype(float)
v[:len(retained)]=original_v[retained]
core_ids=np.flatnonzero(core(original_uv)<=1)
assert set(core_ids).issubset(set(retained))
assert np.array_equal(q[np.searchsorted(retained,core_ids)],original_v[core_ids])
meta={'baseline_commit':'0ab3d838c728a88f2d325edff7a6884400c9ed78','validated_guides_commit':'0fc6f0b3a0ffacc2283d26a06afa852ef3be35ad',
      'method':'Replace local old/new groove patches with conforming triangulation; biharmonic fair floor and single rounded trough per blue guide. Local border regularization capped at 2.5mm; main belly and other objects unchanged.',
      'original_vertices':len(v0),'original_triangles':len(f0),'vertices':len(v),'triangles':len(full_f),
      'removed_original_faces':int(selected.sum()),'unchanged_original_faces':len(outside),'patch_triangles':len(fpatch),
      'retained_original_vertices':len(retained),'new_vertices':len(added),'refinement_rounds':rounds,
      'original_belly_vertices':len(core_ids),'protected_belly_max_displacement_m':0,
      'max_displacement_from_reference_surface_m':float(np.linalg.norm(q-v,axis=1).max()),
      'local_border_regularization_max_m':float(np.linalg.norm(v0-original_v,axis=1).max()),
      'volume_before_m3':vol(original_v,f0),'volume_after_m3':vol(q,full_f),
      'relative_volume_change':vol(q,full_f)/vol(original_v,f0)-1,'global_volume_compensation':False,
      'authoring_tools':'mapbox-earcut 2.1.0 (ISC), Shapely 2.2.0 (BSD), NumPy/SciPy; no app dependencies',
      'patch_builder_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
np.savez_compressed(root/'surface.npz',v=q,reference_v=v,f=full_f,parent_face=parent,
    corner_parent=corner_parent,corner_bary=bary,retained_original_ids=retained,
    original_v=original_v,original_f=f0,uv=uv,reference_uv=uv,work=weight,
    original_belly=core(original_uv)<=1,direction=D,locked=(weight==0)&(np.linalg.norm(q-v,axis=1)<1e-9),
    unchanged_original_faces=outside,patch_face_start=len(outside),delta=(q-v)@D)
(root/'surface.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
print('PATCH_REBUILT',json.dumps(meta),flush=True)
