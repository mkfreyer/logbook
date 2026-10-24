"""Narrow surface bands only; explicitly lock the belly and conserve volume.

The rejected 62fe3ff surface and its broad depth-envelope operation are not used.
The old depression is bridged transversely inside its own band; a rounded new
depression is cut inside the blue band's support. Volume is balanced ONLY
between these old and new bands. No compensating deformation elsewhere.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from scipy import ndimage as ndi
from scipy.interpolate import PchipInterpolator
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import ConvexHull,cKDTree

p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--camera',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args();s=np.load(a.source);v=s['v'];f=s['f'];uv=s['uv'];D=s['direction'];N=len(v);cam=json.loads(a.camera.read_text());radius=.003
def smooth(t):t=np.clip(t,0,1);return t*t*(3-2*t)
def volume(q):return float(np.einsum('ij,ij->i',q[f[:,0]],np.cross(q[f[:,1]],q[f[:,2]])).sum()/6)
# Rasterization is used only to sample the unchanged 3D surface, not as an
# output texture or sculpting envelope. All edits have compact physical bands.
scale=3;H,W=384*scale,320*scale;pix=uv*scale;z=v@D
front=np.full((H,W),-np.inf);ids=np.full((H,W),-1,np.int32)
for i,tri in enumerate(f):
 t=pix[tri];zz=z[tri];x0=max(0,int(t[:,0].min()));x1=min(W-1,int(np.ceil(t[:,0].max())));y0=max(0,int(t[:,1].min()));y1=min(H-1,int(np.ceil(t[:,1].max())))
 if x0>x1 or y0>y1:continue
 xx,yy=np.meshgrid(np.arange(x0,x1+1),np.arange(y0,y1+1));den=(t[1,1]-t[2,1])*(t[0,0]-t[2,0])+(t[2,0]-t[1,0])*(t[0,1]-t[2,1])
 if abs(den)<1e-10:continue
 aa=((t[1,1]-t[2,1])*(xx-t[2,0])+(t[2,0]-t[1,0])*(yy-t[2,1]))/den;bb=((t[2,1]-t[0,1])*(xx-t[2,0])+(t[0,0]-t[2,0])*(yy-t[2,1]))/den
 hit=(aa>=-1e-6)&(bb>=-1e-6)&(aa+bb<=1+1e-6);depth=aa*zz[0]+bb*zz[1]+(1-aa-bb)*zz[2];replace=hit&(depth>front[y0:y1+1,x0:x1+1]);front[y0:y1+1,x0:x1+1][replace]=depth[replace];ids[y0:y1+1,x0:x1+1][replace]=i
valid=np.isfinite(front);near=ndi.distance_transform_edt(~valid,return_distances=False,return_indices=True);front=front[tuple(near)];ids=ids[tuple(near)]
def depth(points):return ndi.map_coordinates(front,[points[:,1]*scale,points[:,0]*scale],order=1,mode='nearest')
edges=np.unique(np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1),axis=0);length=np.linalg.norm(v[edges[:,0]]-v[edges[:,1]],axis=1)
# Registration uses measured concavity near the red guide, never a depression
# in the central belly. This is analysis only; these averages do not move mesh.
cross=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]);norm=np.zeros_like(v)
for k in range(3):np.add.at(norm,f[:,k],cross)
norm/=np.maximum(np.linalg.norm(norm,axis=1)[:,None],1e-15)
e=np.vstack([edges,edges[:,::-1]]);w=np.r_[1/length,1/length];degree=np.bincount(e[:,0],weights=w,minlength=N)
def average(q):return np.column_stack([np.bincount(e[:,0],weights=w*q[e[:,1],k],minlength=N)/degree for k in range(q.shape[1])])
curvature=np.einsum('ij,ij->i',average(v)-v,norm)
for _ in range(2):curvature=.6*curvature+.4*average(curvature[:,None])[:,0]
core=((uv[:,0]-132)/46)**2+((uv[:,1]-205)/97)**2<=1
candidate_ids=np.flatnonzero(s['visible']&~core);tree=cKDTree(uv[candidate_ids])
red1=np.array([[55,292],[57,300],[65,319],[78,335],[94,350]],float)
blue1=np.array([[55,292],[57,312],[57,333],[60,353],[64,370],[70,378]],float)
red2=np.array([[230,82],[233,100],[234,128],[231,160],[225,192],[217,223],[207,254],[194,286],[179,315],[161,344]],float)
blue2=np.array([[229,72],[230,90],[219,123],[213,151],[207,185],[200,217],[187,251],[174,280],[164,315],[149,352],[132,379]],float)
last=cam['blue2_last_visible_reference_px'];assert last is not None
blue2=np.vstack([blue2[blue2[:,1]<last[1]],last])
def curve(points,register=False):
 ys=np.linspace(points[0,1],points[-1,1],max(80,int((points[-1,1]-points[0,1])*3)));xs=PchipInterpolator(points[:,1],points[:,0])(ys);xy=np.c_[xs,ys]
 tangent=np.gradient(xy,axis=0);tangent/=np.linalg.norm(tangent,axis=1)[:,None];normal=np.c_[-tangent[:,1],tangent[:,0]]
 offsets=np.zeros(len(xy))
 if register:
  states=np.linspace(-12,12,33);queries=xy[:,None,:]+normal[:,None,:]*states[None,:,None]
  distance,index=tree.query(queries);score=np.maximum(curvature[candidate_ids[index]],0)*np.exp(-.5*(distance/1.5)**2)-states[None,:]**2*.000002
  score[distance>3]=-1.;transition=.00002*(states[:,None]-states[None,:])**2;value=score[0].copy();history=[]
  for row in score[1:]:
   trial=value[:,None]-transition;choice=trial.argmax(0);history.append(choice);value=trial[choice,np.arange(len(states))]+row
  path=[int(value.argmax())]
  for choice in history[::-1]:path.append(int(choice[path[-1]]))
  offsets=ndi.gaussian_filter1d(states[np.array(path[::-1])],4.)
  offsets*=smooth((ys-points[0,1])/7)
  xy+=normal*offsets[:,None]
  tangent=np.gradient(xy,axis=0);tangent/=np.linalg.norm(tangent,axis=1)[:,None];normal=np.c_[-tangent[:,1],tangent[:,0]]
 xs,ys=xy[:,0],xy[:,1]
 # The source triangles hit by the reference rays provide 3D curve samples.
 fi=ids[np.clip(np.rint(ys*scale).astype(int),0,H-1),np.clip(np.rint(xs*scale).astype(int),0,W-1)];tri=f[fi];t=uv[tri]
 den=(t[:,1,1]-t[:,2,1])*(t[:,0,0]-t[:,2,0])+(t[:,2,0]-t[:,1,0])*(t[:,0,1]-t[:,2,1]);den=np.where(abs(den)<1e-10,1e-10,den)
 aa=((t[:,1,1]-t[:,2,1])*(xs-t[:,2,0])+(t[:,2,0]-t[:,1,0])*(ys-t[:,2,1]))/den;bb=((t[:,2,1]-t[:,0,1])*(xs-t[:,2,0])+(t[:,0,0]-t[:,2,0])*(ys-t[:,2,1]))/den
 xyz=aa[:,None]*v[tri[:,0]]+bb[:,None]*v[tri[:,1]]+(1-aa-bb)[:,None]*v[tri[:,2]]
 # A virtual source connects each curve point to the corners of its triangle.
 seed=np.full(N,np.inf)
 for k in range(3):np.minimum.at(seed,tri[:,k],np.linalg.norm(v[tri[:,k]]-xyz,axis=1))
 ix=np.flatnonzero(np.isfinite(seed));row=np.r_[edges[:,0],edges[:,1],np.full(len(ix),N)];col=np.r_[edges[:,1],edges[:,0],ix];weight=np.r_[length,length,seed[ix]]
 graph=coo_matrix((weight,(row,col)),shape=(N+1,N+1)).tocsr();geodesic=dijkstra(graph,directed=True,indices=N,limit=radius)[:N]
 _,nearest=cKDTree(xy).query(uv)
 return dict(xy=xy,normal=normal,xyz=xyz,nearest=nearest,distance=geodesic,points=points,registration_offsets=offsets)
old=[curve(red1,True),curve(red2,True)];new=[curve(blue1),curve(blue2)]
dist_old=np.minimum(old[0]['distance'],old[1]['distance']);dist_new=np.minimum(new[0]['distance'],new[1]['distance'])
# Explicit belly lock, in addition to freezing EVERY vertex outside the bands.
belly=((uv[:,0]-132)/46)**2+((uv[:,1]-205)/97)**2<=1
# Keep support vertices of front/profile/reference silhouettes at their exact P4
# coordinates. No new bank may project beyond those original support envelopes.
locked_support=np.zeros(N,bool);hulls=[]
for projection in [v[:,[0,2]],v[:,[1,2]],uv]:
 hull=ConvexHull(projection);locked_support[hull.vertices]=True;hulls.append(hull)
allowed=(np.minimum(dist_old,dist_new)<radius)&s['visible']&~belly&~locked_support
fill=np.zeros(N);profile=np.zeros(N)
for record in old:
 k=record['nearest'];center=record['xy'][k];normal=record['normal'][k];signed=np.einsum('ij,ij->i',uv-center,normal);bank=6.;t=np.clip((signed+bank)/(2*bank),0,1)
 left=center-bank*normal;right=center+bank*normal;L=depth(left);R=depth(right);eps=.65
 slopeL=(depth(left+eps*normal)-depth(left-eps*normal))/(2*eps);slopeR=(depth(right+eps*normal)-depth(right-eps*normal))/(2*eps)
 bridge=(2*t**3-3*t*t+1)*L+(t**3-2*t*t+t)*(2*bank)*slopeL+(-2*t**3+3*t*t)*R+(t**3-t*t)*(2*bank)*slopeR
 bridge=np.minimum(bridge,np.maximum(L,R)+.0003)  # No Hermite bank overshoot.
 fade=smooth((radius-record['distance'])/.0011)
 # Fill through the OLD terminal point, then fade in its rounded endpoint cap.
 # Fading before that terminal would incorrectly preserve the rejected tip.
 fade*=smooth((uv[:,1]-record['points'][0,1])/7)*smooth((record['points'][-1,1]+5-uv[:,1])/5)
 local=np.maximum(bridge-z,0)*fade;local=np.minimum(local,.004);fill=np.maximum(fill,local)
for record in new:
 d=record['distance'];p=np.where(d<radius,(1-(np.minimum(d,radius)/radius)**2)**3,0)
 k=record['nearest'];along=record['xy'][k,1];p*=smooth((along-record['points'][0,1])/7)*smooth((record['points'][-1,1]-along)/7)
 profile=np.maximum(profile,p)
fill[~allowed]=0;profile[~allowed]=0
# Do not let filling an old groove enlarge the existing silhouette supports.
max_fill=np.full(N,np.inf)
for axes,hull in [([0,2],hulls[0]),([1,2],hulls[1])]:
 n=hull.equations[:,:2];b=hull.equations[:,2];rate=n@D[axes];toward=rate>1e-10
 clearance=-(v[:,axes]@n[toward].T+b[toward]);bound=np.min(clearance/rate[toward],axis=1);max_fill=np.minimum(max_fill,np.maximum(bound,0))
fill=np.minimum(fill,.98*max_fill)
V0=volume(v);Vfill=volume(v+fill[:,None]*D);Vtest=volume(v+(fill-.001*profile)[:,None]*D)
assert Vfill>V0 and Vfill>Vtest,'No old-depression volume available inside the permitted narrow bands'
estimate=.001*(Vfill-V0)/(Vfill-Vtest)
assert 0<estimate<.008,('Required depth incompatible with narrow-band constraints',estimate)
def coordinates(amplitude):
 q=v.copy();q[allowed]=(v[allowed]+(fill[allowed]-amplitude*profile[allowed])[:,None]*D).astype(np.float32);return q
lo=0.;hi=estimate*2;best=None
for _ in range(65):
 mid=(lo+hi)/2;q=coordinates(mid);err=volume(q)-V0
 if best is None or abs(err)<best[0]:best=(abs(err),mid,q)
 if err>0:lo=mid
 else:hi=mid
error,amplitude,q=best;assert error/V0<1e-7
delta=q-v;assert np.array_equal(q[~allowed],v[~allowed]);assert np.array_equal(q[belly],v[belly])
assert np.linalg.norm(delta,axis=1).max()<.0041
np.savez_compressed(a.output,v=q,source_v=v,f=f,allowed=allowed,belly=belly,locked_support=locked_support,old_distance_m=dist_old,new_distance_m=dist_new,fill_m=fill,new_profile=profile,delta=delta,curve_points_3d=np.vstack([r['xyz']for r in old+new]))
meta={'baseline_commit':'0ab3d838c728a88f2d325edff7a6884400c9ed78','method':'Only 3 mm geodesic bands: transverse Hermite bridge at old grooves and rounded new trough; volume balanced exclusively within these bands. No depth envelope, broad smoothing or belly deformation.',
 'max_band_radius_m':radius,'allowed_vertices':int(allowed.sum()),'changed_vertices':int((np.linalg.norm(delta,axis=1)>0).sum()),'locked_belly_vertices':int(belly.sum()),'belly_max_displacement_m':0.,'outside_bands_max_displacement_m':0.,'locked_silhouette_vertices':int(locked_support.sum()),'new_groove_amplitude_m':amplitude,'max_displacement_m':float(np.linalg.norm(delta,axis=1).max()),'volume_before_m3':V0,'volume_after_m3':volume(q),'relative_volume_error':error/V0,'bbox_before_m':np.ptp(v,axis=0).tolist(),'bbox_after_m':np.ptp(q,axis=0).tolist(),
 'red_paths_reference_px':[red1.tolist(),red2.tolist()],'registered_old_paths_px':[r['xy'][::10].tolist()for r in old],'max_old_registration_offset_px':[float(np.abs(r['registration_offsets']).max())for r in old],'blue_paths_reference_px':[blue1.tolist(),blue2.tolist()],'requested_blue2_end_px':[132,379],'actual_blue2_end_px':last,'blue2_clip_reason':'Requested end reaches another arm object; final taper stays on the visible deltoid.',
 'surface_builder_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
a.output.with_suffix('.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n');print('NARROW_BANDS',json.dumps(meta),flush=True)
