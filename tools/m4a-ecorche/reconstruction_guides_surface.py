"""Local, continuous surface reconstruction using the validated 0fc6f0b guides.

The main P4 belly is a hard lock. A biharmonic fair surface replaces the
old/new groove domain; one rounded trough is then formed on each blue guide.
Only local triangles are adaptively bisected. No global smoothing, remeshing,
volume compensation or deformation from the rejected trials is used.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi
from scipy.interpolate import PchipInterpolator
from scipy.spatial import ConvexHull,cKDTree
from scipy.sparse import coo_matrix,eye
from scipy.sparse.linalg import spsolve

p=argparse.ArgumentParser()
p.add_argument('--source',type=Path,required=True)
p.add_argument('--guides',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
root=a.output;root.mkdir(parents=True,exist_ok=True)
s=np.load(a.source);original_v=s['v'];original_f=s['f'];original_uv=s['uv']
guides=json.loads(a.guides.read_text());cam=guides['camera'];D=s['direction'];R=s['right']
assert guides['baseline_commit'].startswith('0ab3d83') and not guides['sculpture_performed']
sx,sy=cam['pixels_per_meter_x'],cam['pixels_per_meter_y'];target=np.array(cam['target_m'])
smooth=lambda t:np.clip(t,0,1)**3*(10-15*np.clip(t,0,1)+6*np.clip(t,0,1)**2)
def project(q):return np.c_[160+(q-target)@R*sx,192-(q[:,2]-target[2])*sy]
def belly_value(uv):return ((uv[:,0]-132)/46)**2+((uv[:,1]-205)/97)**2
core_original=belly_value(original_uv)<=1
protected_faces=core_original[original_f].any(axis=1)
protected_vertices=np.unique(original_f[protected_faces])
protected_tree=cKDTree(original_v[protected_vertices])

# Exact triangle height raster of the unchanged P4 surface. This is an authoring
# coordinate chart, never a texture, normal map or output image modification.
scale=3;H,W=1152,960
front=np.full((H,W),-np.inf);back=np.full((H,W),np.inf);front_ids=np.full((H,W),-1,int)
pix=original_uv*scale;depth=original_v@D
for fi,tri in enumerate(original_f):
    t=pix[tri];zz=depth[tri]
    x0,y0=np.maximum(np.floor(t.min(0)).astype(int),0)
    x1,y1=np.minimum(np.ceil(t.max(0)).astype(int),[W-1,H-1])
    if x0>x1 or y0>y1:continue
    e1,e2=t[1]-t[0],t[2]-t[0];den=e1[0]*e2[1]-e1[1]*e2[0]
    if abs(den)<1e-10:continue
    xx,yy=np.meshgrid(np.arange(x0,x1+1),np.arange(y0,y1+1))
    bb=((xx-t[0,0])*(t[2,1]-t[0,1])-(yy-t[0,1])*(t[2,0]-t[0,0]))/den
    cc=((t[1,0]-t[0,0])*(yy-t[0,1])-(t[1,1]-t[0,1])*(xx-t[0,0]))/den
    inside=(bb>=-1e-7)&(cc>=-1e-7)&(bb+cc<=1+1e-7)
    values=zz[0]+bb*(zz[1]-zz[0])+cc*(zz[2]-zz[0])
    cell=front[y0:y1+1,x0:x1+1];replace=inside&(values>cell)
    cell[replace]=values[replace];front_ids[y0:y1+1,x0:x1+1][replace]=fi
    cell_back=back[y0:y1+1,x0:x1+1]
    np.minimum(cell_back,np.where(inside,values,np.inf),out=cell_back)
valid=np.isfinite(front)
nearest=ndi.distance_transform_edt(~valid,return_distances=False,return_indices=True)
front=front[tuple(nearest)]
back=back[tuple(nearest)];middle=.5*(front+back)
bank_field=ndi.gaussian_filter(front,5.)
edge_dist=ndi.distance_transform_edt(valid)/scale
def sample(field,uv):return ndi.map_coordinates(field,[uv[:,1]*scale,uv[:,0]*scale],order=1,mode='nearest')

paths={name:np.array([r['reference_px']for r in record['points']])
       for name,record in guides['paths'].items()}
def path_x(name,y):
    pts=paths[name];return PchipInterpolator(pts[:,1],pts[:,0],extrapolate=True)(y)

def domain(q,uv):
    x,y=uv.T
    # Only the lower first branch is replaced; its upper common groove is kept.
    l1=path_x('nouveau_1_terminaison',np.clip(y,292,378))-11
    r1=path_x('ancien_1',np.clip(y,292,350))+13
    l2=np.minimum(path_x('nouveau_2',np.clip(y,72,379))-18,
                  path_x('ancien_2',np.clip(y,82,344))-38)
    r2=np.maximum(path_x('nouveau_2',np.clip(y,72,379))+15,
                  path_x('ancien_2',np.clip(y,82,344))+13)
    # A smooth end cap preserves the existing insertions and their neighbours.
    w1=smooth((y-286)/13)*smooth((384-y)/11)
    w2=smooth((y-72)/13)*smooth((384-y)/12)
    # Include small hidden folds without admitting the distinct rear sheet of
    # the closed deltoid. Visibility labels alone leave isolated untreated pits.
    gap=np.maximum(sample(front,uv)-q@D,0)
    front_weight=smooth((.006-gap)/.002)
    core_dist=protected_tree.query(q)[0]
    belly_lock=smooth(core_dist/.0035)
    belly_lock[belly_value(uv)<=1]=0
    edge_lock=smooth((sample(edge_dist,uv)-1.5)/4)
    rows=[]
    for left,right,end in [(l1,r1,w1),(l2,r2,w2)]:
        mask=smooth((x-left)/5)*smooth((right-x)/5)*end*front_weight*belly_lock*edge_lock
        rows.append((left,right,mask))
    return rows

# Adaptive edge bisection creates a conforming mesh without any global subdiv.
v=original_v.copy();f=original_f.copy();parent_face=np.arange(len(f),dtype=np.int32)
rounds=[]
for iteration in range(6):
    uv=project(v);weight=np.maximum.reduce([t[2]for t in domain(v,uv)])
    edges=np.unique(np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1),axis=0)
    mids=v[edges].mean(axis=1);muv=project(mids)
    mw=np.maximum.reduce([t[2]for t in domain(mids,muv)])
    strength=np.maximum(mw,weight[edges].max(axis=1))
    lengths=np.linalg.norm(v[edges[:,1]]-v[edges[:,0]],axis=1)
    target_edge=.0014+(.003-.0014)*(1-strength)
    split=(strength>.005)&(lengths>target_edge*1.25)
    selected=edges[split]
    if len(selected)==0:break
    indices=np.arange(len(v),len(v)+len(selected))
    lookup={tuple(edge):int(index)for edge,index in zip(selected,indices)}
    v=np.vstack([v,mids[split]])
    faces=[];parents=[]
    for tri,pid in zip(f,parent_face):
        A,B,C=map(int,tri)
        mid=[lookup.get(tuple(sorted(edge)),-1)for edge in [(A,B),(B,C),(C,A)]]
        n=sum(i>=0 for i in mid)
        if n==0:parts=[(A,B,C)]
        elif n==3:
            ab,bc,ca=mid;parts=[(A,ab,ca),(ab,B,bc),(ca,bc,C),(ab,bc,ca)]
        elif n==1:
            k=next(i for i,j in enumerate(mid)if j>=0)
            A,B,C=map(int,np.roll(tri,-k));m=mid[k]
            parts=[(A,m,C),(m,B,C)]
        else:
            k=(next(i for i,j in enumerate(mid)if j<0)+1)%3
            A,B,C=map(int,np.roll(tri,-k));ab,bc=mid[k],mid[(k+1)%3]
            # Pick the shorter of the two interior diagonals.
            if np.linalg.norm(v[ab]-v[C])<=np.linalg.norm(v[A]-v[bc]):
                parts=[(B,bc,ab),(A,ab,C),(ab,bc,C)]
            else:parts=[(B,bc,ab),(A,ab,bc),(A,bc,C)]
        faces.extend(parts);parents.extend([pid]*len(parts))
    f=np.array(faces,np.int32);parent_face=np.array(parents,np.int32)
    rounds.append({'round':iteration+1,'split_edges':len(selected),'vertices':len(v),'triangles':len(f)})

uv=project(v);z=v@D
initial_uv=uv.copy()
fixed=(belly_value(initial_uv)<=1.18)|np.isin(np.arange(len(v)),protected_vertices)
hull=ConvexHull(original_v)
fixed[hull.vertices]=True
# Positive-weight local 2D embedding regularizes the tiny folded projections.
# Both outside and belly anchors stay fixed; no change to the global mesh.
edges=np.unique(np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1),axis=0)
rows=np.r_[edges[:,0],edges[:,1]];cols=np.r_[edges[:,1],edges[:,0]]
degree=np.bincount(rows,minlength=len(v))
reg=np.maximum.reduce([t[2]for t in domain(v,uv)])
reg[fixed]=0
P=coo_matrix((reg[rows]/degree[rows],(rows,cols)),shape=(len(v),len(v))).tocsr()
uv=spsolve(eye(len(v),format='csr')-P,(1-reg[:,None])*initial_uv)
uv[belly_value(uv)<=1.18]=initial_uv[belly_value(uv)<=1.18]
shift=uv-initial_uv
shift3d=shift[:,0,None]*R/sx
shift3d[:,2]-=shift[:,1]/sy
domains=domain(v,uv)
work=np.maximum.reduce([r[2]for r in domains])
# A 2D thin-plate solve reconstructs the old groove floor in BOTH directions.
# Row-by-row interpolation can inherit transverse ridges from noisy old banks.
yy,xx=np.mgrid[0:384,0:320];grid_uv=np.c_[xx.ravel(),yy.ravel()]
grid_z=sample(front,grid_uv)
grid_q=target+((grid_uv[:,0]-160)/sx)[:,None]*R
grid_q[:,2]+=(192-grid_uv[:,1])/sy
grid_q+=(grid_z-grid_q@D)[:,None]*D
grid_work=np.maximum.reduce([r[2]for r in domain(grid_q,grid_uv)]).reshape(384,320)
unknown=(grid_work>.02)&(belly_value(grid_uv).reshape(384,320)>1.18)
unknown[:3]=False;unknown[-3:]=False;unknown[:,:3]=False;unknown[:,-3:]=False
index=np.full((384,320),-1,int);index[unknown]=np.arange(unknown.sum())
base=sample(bank_field,grid_uv).reshape(384,320)
ys,xs=np.where(unknown);I=np.arange(len(ys));rr=[];cc=[];ww=[];rhs=np.zeros(len(I))
ax,ay=1.,(sy/sx)**2
stencil=[(0,0,6*ax*ax+8*ax*ay+6*ay*ay),
         (0,1,-4*ax*(ax+ay)),(0,-1,-4*ax*(ax+ay)),
         (1,0,-4*ay*(ax+ay)),(-1,0,-4*ay*(ax+ay)),
         (1,1,2*ax*ay),(1,-1,2*ax*ay),(-1,1,2*ax*ay),(-1,-1,2*ax*ay),
         (0,2,ax*ax),(0,-2,ax*ax),(2,0,ay*ay),(-2,0,ay*ay)]
for dy,dx,value in stencil:
    neighbor=index[ys+dy,xs+dx];inside=neighbor>=0
    rr.extend(I[inside]);cc.extend(neighbor[inside]);ww.extend(np.full(inside.sum(),value))
    rhs[~inside]-=value*base[ys[~inside]+dy,xs[~inside]+dx]
solution=spsolve(coo_matrix((ww,(rr,cc)),shape=(len(I),len(I))).tocsr(),rhs)
base[unknown]=solution
fair_target=ndi.map_coordinates(base,[uv[:,1],uv[:,0]],order=3,mode='nearest')
fair=z+work*(fair_target-z)

new_cut=np.zeros(len(v));groove_data=[]
for name,start,end in [('nouveau_1_terminaison',292,378),('nouveau_2',72,379)]:
    pts=paths[name]
    _,ix=cKDTree(pts).query(uv)
    tangent=np.gradient(pts,axis=0);tangent/=np.linalg.norm(tangent,axis=1)[:,None]
    normal=np.c_[-tangent[:,1],tangent[:,0]]
    diff=uv-pts[ix];signed=np.einsum('ij,ij->i',diff,normal[ix])
    # 6 mm support radius in the reference tangent plane, with a rounded bottom.
    per_pixel=np.sqrt((normal[ix,0]/sx)**2+(normal[ix,1]/sy)**2)
    distance=np.abs(signed)*per_pixel
    radius=.006
    profile=np.where(distance<radius,(1-(np.minimum(distance,radius)/radius)**2)**3,0)
    along=pts[ix,1]
    taper=smooth((along-start)/13)*smooth((end-along)/13)
    cut=.0026*profile*taper
    new_cut=np.maximum(new_cut,cut)
    groove_data.append({'guide':name,'radius_tangent_m':radius,'depth_along_camera_m':.0026})
delta=fair-z-work*new_cut
delta[work<1e-7]=0
delta[np.isin(np.arange(len(v)),protected_vertices)]=0
delta[belly_value(uv)<=1]=0
delta[fixed]=0

# Keep the complete original convex support envelope. This prevents an old
# trough fill from inflating any global shoulder silhouette; never compensates
# volume by deforming another part of the muscle.
rate=hull.equations[:,:3]@D
fill_limit=np.full(len(v),np.inf);cut_limit=np.full(len(v),np.inf)
for block in np.array_split(np.arange(len(v)),24):
    clearance=-(v[block]@hull.equations[:,:3].T+hull.equations[:,3])
    fill_limit[block]=np.maximum((clearance[:,rate>1e-8]/rate[rate>1e-8]).min(1),0)
    cut_limit[block]=np.maximum((clearance[:,rate<-1e-8]/-rate[rate<-1e-8]).min(1),0)
delta=np.minimum(np.maximum(delta,-.999*cut_limit),.999*fill_limit)
delta[np.isin(np.arange(len(v)),hull.vertices)]=0
q=v.copy();changed=(np.abs(delta)>1e-9)|(np.linalg.norm(shift3d,axis=1)>1e-9)
q[changed]=(v[changed]+shift3d[changed]+delta[changed,None]*D).astype(np.float32)
motion=q-v;alpha=np.ones(len(v))
for block in np.array_split(np.arange(len(v)),24):
    clearance=-(v[block]@hull.equations[:,:3].T+hull.equations[:,3])
    rate=motion[block]@hull.equations[:,:3].T
    limit=np.where(rate>1e-12,np.maximum(clearance,0)/np.maximum(rate,1e-12),np.inf)
    alpha[block]=np.minimum(limit.min(1),1)
q[changed]=(v[changed]+alpha[changed,None]*motion[changed]).astype(np.float32)
locked=fixed
assert np.array_equal(q[locked],v[locked])
work[locked]=0
vol=lambda v,f:float(np.einsum('ij,ij->i',v[f[:,0]],np.cross(v[f[:,1]],v[f[:,2]])).sum()/6)
meta={'baseline_commit':'0ab3d838c728a88f2d325edff7a6884400c9ed78',
      'validated_guides_commit':'0fc6f0b3a0ffacc2283d26a06afa852ef3be35ad',
      'method':'Local biharmonic thin-plate reconstruction across old/new groove domain; harmonic local embedding, then one rounded depression per validated blue guide; conforming local bisection only.',
      'original_vertices':len(original_v),'original_triangles':len(original_f),
      'vertices':len(v),'triangles':len(f),'refinement_rounds':rounds,
      'original_belly_vertices':int(core_original.sum()),'protected_original_vertices':len(protected_vertices),
      'locked_surface_vertices_including_subdivision':int(locked.sum()),
      'modified_vertices':int(changed.sum()),'max_displacement_m':float(np.linalg.norm(q-v,axis=1).max()),
      'max_fill_along_camera_m':float(delta.max()),'max_inward_along_camera_m':float(-delta.min()),
      'local_embedding':'Positive-weight harmonic solve with fixed belly/outside anchors','thin_plate_unknowns':int(unknown.sum()),'max_local_tangent_regularization_m':float(np.linalg.norm(shift3d,axis=1).max()),
      'protected_belly_max_displacement_m':0.,'grooves':groove_data,
      'volume_before_m3':vol(original_v,original_f),'volume_refined_reference_m3':vol(v,f),
      'volume_after_m3':vol(q,f),'relative_volume_change':vol(q,f)/vol(original_v,original_f)-1,
      'global_volume_compensation':False,'sculptor_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
np.savez_compressed(root/'surface.npz',v=q,reference_v=v,f=f,parent_face=parent_face,
                    original_v=original_v,original_f=original_f,uv=project(q),reference_uv=initial_uv,work=work,
                    fair_depth=fair,cut_depth=work*new_cut,delta=delta,locked=locked,
                    original_belly=core_original,direction=D)
(root/'surface.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
print('RECONSTRUCTION',json.dumps(meta),flush=True)
