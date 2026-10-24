"""Rebuild the shoulder's outer curvature from P4 sections and three smooth belly envelopes.

Existing deep sculpt troughs are replaced by a section hull; definition is made
by the envelope of three overlapping convex bellies, not by incising channels.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from scipy.spatial import ConvexHull
from scipy.ndimage import gaussian_filter
from scipy.interpolate import RegularGridInterpolator
from scipy.special import logsumexp
p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();source=np.load(a.baseline);v=source['p4__deltoid.right__v'];f=source['p4__deltoid.right__f'];T=v[f];zs=np.linspace(1.298,1.501,153);angles=np.linspace(-np.pi,np.pi,513);direction=np.array([-np.cos(angles),np.sin(angles)]).T;lo=T[:,:,2].min(1);hi=T[:,:,2].max(1)
def smooth(t):t=np.clip(t,0,1);return t*t*(3-2*t)
def volume(v):return float(np.einsum('ij,ij->i',v[f[:,0]],np.cross(v[f[:,1]],v[f[:,2]])).sum()/6)
def axis(z):t=np.clip((z-1.286)/.217,0,1);return np.stack([-.241+.057*t,.080-.010*t],axis=-1)
def radii(A,B,with_inner=False):
 e=B-A;det=direction[:,0,None]*e[None,:,1]-direction[:,1,None]*e[None,:,0];safe=np.where(abs(det)>1e-12,det,np.inf);r=(A[:,0]*e[:,1]-A[:,1]*e[:,0])[None,:]/safe;t=(A[None,:,0]*direction[:,None,1]-A[None,:,1]*direction[:,None,0])/safe;valid=(r>0)&(t>=0)&(t<=1);rad=np.where(valid,r,0).max(1);inner=np.where(valid,r,np.inf).min(1);inner=np.where(np.isfinite(inner)&(rad-inner>.0002),inner,0);good=rad>0
 if not good.all():rad=np.interp(angles,np.r_[angles[good]-2*np.pi,angles[good],angles[good]+2*np.pi],np.tile(rad[good],3))
 return(rad,inner)if with_inner else rad
raw=[];inners=[];hulls=[];xmins=[];xmaxs=[];ymins=[];ymaxs=[]
for z in zs:
 tri=T[(lo<=z)&(hi>=z)];points=[];valids=[]
 for k,l in [(0,1),(1,2),(2,0)]:
  denom=tri[:,l,2]-tri[:,k,2];t=(z-tri[:,k,2])/np.where(abs(denom)>1e-12,denom,np.inf);points.append(tri[:,k,:2]+t[:,None]*(tri[:,l,:2]-tri[:,k,:2]));valids.append((t>=0)&(t<=1)&(abs(denom)>1e-12))
 seg=np.array([[points[k][i]for k in range(3)if valids[k][i]][:2]for i in range(len(tri))if sum(valids[k][i]for k in range(3))>=2]);section=np.unique(seg.reshape(-1,2),axis=0);xmins.append(section[:,0].min());xmaxs.append(section[:,0].max());ymins.append(section[:,1].min());ymaxs.append(section[:,1].max());h=ConvexHull(section);poly=section[h.vertices];center=axis(z);outer,inner=radii(seg[:,0]-center,seg[:,1]-center,True);raw.append(outer);inners.append(inner);hulls.append(radii(poly-center,np.roll(poly,-1,axis=0)-center))
raw=np.array(raw);hull=gaussian_filter(np.array(hulls),sigma=(.8,.6),mode=('nearest','wrap'))
tt=np.clip((zs-1.286)/.217,0,1);ax=axis(zs);span=np.array(ymaxs)-np.array(ymins);extent=ax[:,0]-np.array(xmins)
# Actual overlapping elliptical belly sections, fitted inside the P4 support.
# Their convex surfaces meet through a rounded union rather than an incision.
ry=span[:,None]*np.array([.265,.245,.270]);rx=extent[:,None]*np.array([.60,.62,.58]);cx=ax[:,0,None]-(extent[:,None]-rx);spread=.88+.12*smooth((tt-.25)/.60);fractions=.5+(np.array([.26,.50,.74])-.5)*spread[:,None];cy=np.array(ymins)[:,None]+span[:,None]*fractions
cx-=ax[:,0,None];cy-=ax[:,1,None];dx=direction[None,:,0,None];dy=direction[None,:,1,None];A=(dx/rx[:,None,:])**2+(dy/ry[:,None,:])**2;B=-2*(cx[:,None,:]*dx/rx[:,None,:]**2+cy[:,None,:]*dy/ry[:,None,:]**2);C=(cx/rx)**2+(cy/ry)**2-1;disc=B*B-4*A*C[:,None,:];roots=(-B+np.sqrt(np.maximum(disc,0)))/(2*A);valid=(disc>=0)&(roots>0);roots=np.where(valid,roots,-10);union=.0008*logsumexp(roots/.0008,axis=2);union=np.where(valid.any(2),np.minimum(union,hull),hull)
envelope=smooth((zs-1.312)/.052)*smooth((1.499-zs)/.023);lateral=smooth((1.95-abs(angles))/.30);target=hull+(union-hull)*envelope[:,None]*lateral[None,:]
raw_interp=RegularGridInterpolator((zs,angles),raw,bounds_error=False,fill_value=None);inner_interp=RegularGridInterpolator((zs,angles),np.array(inners),bounds_error=False,fill_value=None);target_interp=RegularGridInterpolator((zs,angles),target,bounds_error=False,fill_value=None)
ax=axis(v[:,2]);offset=v[:,:2]-ax;rho_v=np.linalg.norm(offset,axis=1);theta=np.arctan2(offset[:,1],-offset[:,0]);coords=np.column_stack([np.clip(v[:,2],zs[0],zs[-1]),theta]);old_r=raw_interp(coords);inner_r=inner_interp(coords);new_r=target_interp(coords);radial=np.column_stack([offset/np.maximum(rho_v[:,None],1e-12),np.zeros(len(v))]);outer=np.clip((rho_v-inner_r)/np.maximum(old_r-inner_r,.0002),0,1);angular=smooth((2.35-abs(theta))/.35);ends=smooth((v[:,2]-1.312)/.045)*smooth((1.498-v[:,2])/.022);mask=outer*angular*ends
def surface(inset):
 effective=np.maximum(new_r-inset,inner_r+np.minimum(.0015,.7*np.maximum(old_r-inner_r,0)));q=v+radial*((effective-old_r)*mask)[:,None]
 # Do not expand the frontal silhouette beyond P4 at any sampled height.
 xmin=np.interp(v[:,2],zs,xmins);q[:,0]=np.where(mask>1e-6,np.maximum(q[:,0],xmin+.0002*mask),q[:,0]);return q
goal=min(volume(v)*.970,volume(surface(0)));low=0.;high=.025
for _ in range(48):
 mid=(low+high)/2;q=surface(mid)
 if volume(q)>goal:low=mid
 else:high=mid
q=surface((low+high)/2)
a.output.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(a.output,v=q,f=f,source_v=v,mask=mask,z_samples=zs,theta_samples=angles,source_radius=raw,section_hull_radius=hull,belly_envelope_radius=target)
metadata={'method':'P4 section convex hull replaces pre-existing deep troughs. Three overlapping elliptical belly volumes are fitted inside the P4 support, joined by a rounded union and attenuated toward common attachments. No outward volume compensation.','base':'P4 deltoid only; all other objects remain P5','maximum_target_volume_ratio_to_p4':.970,'volume_ratio_to_p4':volume(q)/volume(v),'inward_offset_m':(low+high)/2,'max_displacement_from_p4_m':float(np.linalg.norm(q-v,axis=1).max()),'x_bbox_before_m':[float(v[:,0].min()),float(v[:,0].max())],'x_bbox_after_m':[float(q[:,0].min()),float(q[:,0].max())],'belly_centers_y_fraction':[.26,.50,.74],'belly_x_radius_fraction':[.60,.62,.58],'belly_y_radius_fraction':[.265,.245,.270],'smooth_union_softness_m':.0008,'longitudinal_sections':len(zs),'angular_samples':len(angles),'new_triangles':0,'builder_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'surface_sha256':hashlib.sha256(a.output.read_bytes()).hexdigest()}
a.output.with_suffix('.json').write_text(json.dumps(metadata,indent=2)+'\n');print(json.dumps(metadata),flush=True)
