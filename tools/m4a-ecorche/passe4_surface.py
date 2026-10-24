"""Reconstruct a continuous neutral head/throat exterior from source sections.
Run with system Python (NumPy/SciPy), after passe4_prepare.py.
"""
import numpy as np,json,hashlib,argparse
from scipy.ndimage import grey_closing,gaussian_filter
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--work',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();a=np.load(args.work/'baseline.npz');plane=.002114987923242599
rows=json.loads((args.work/'parts.json').read_text())['parts']
# Exterior reference: original cranial, facial and cervical surfaces.
parts=[]
for r in rows:
 if r['id']=='trapezius_attachment.reconstructed_midline':continue
 if r['min'][2]<1.46:continue
 v=a[r['id']+'__v'];f=a[r['id']+'__f'];parts.append(v[f])
T=np.concatenate(parts);lo=T[:,:,2].min(1);hi=T[:,:,2].max(1)
zs=np.linspace(1.465,1.7995,235);theta=np.arange(256)*2*np.pi/256;d=np.array([np.sin(theta),-np.cos(theta)]).T
def cy(z):return np.interp(z,[1.485,1.58,1.64,1.80],[.045,.040,.021,.024])
radii=[]
for z in zs:
 tri=T[(lo<=z)&(hi>=z)];hits=[]
 for k,l in [(0,1),(1,2),(2,0)]:
  t=(z-tri[:,k,2])/np.where(abs(tri[:,l,2]-tri[:,k,2])>1e-12,tri[:,l,2]-tri[:,k,2],1e-12)
  valid=(t>=0)&(t<=1);v=tri[:,k,:2]+t[:,None]*(tri[:,l,:2]-tri[:,k,:2]);hits.append((v,valid))
 seg=[]
 for i in range(len(tri)):
  v=[h[0][i] for h in hits if h[1][i]]
  if len(v)>=2:seg.append(v[:2])
 seg=np.array(seg)-[plane,cy(z)];A=seg[:,0];B=seg[:,1];e=B-A
 det=d[:,0,None]*e[None,:,1]-d[:,1,None]*e[None,:,0];safe=np.where(abs(det)>1e-12,det,np.inf)
 r=(A[:,0]*e[:,1]-A[:,1]*e[:,0])[None,:]/safe;t=(A[None,:,0]*d[:,None,1]-A[None,:,1]*d[:,None,0])/safe
 rad=np.where((t>=0)&(t<=1)&(r>0)&(r<.17),r,0).max(1)
 good=rad>0
 if not good.all():rad=np.interp(theta,np.concatenate([theta[good]-2*np.pi,theta[good],theta[good]+2*np.pi]),np.tile(rad[good],3))
 radii.append(rad)
raw=np.array(radii)
# Mirror sampling before surface cleanup. Closing fills exposed dissection slots.
raw=(raw+raw[:,(-np.arange(256))%256])/2
closed=grey_closing(raw,size=(15,23),mode=('nearest','wrap'))
q=gaussian_filter(closed,sigma=(2.6,2.1),mode=('nearest','wrap'))
# Retain softly filtered facial landmarks inside the reconstructed cheek shell.
detail=gaussian_filter(grey_closing(raw,size=(7,11),mode=('nearest','wrap')),sigma=(1.1,1.1),mode=('nearest','wrap'))
xx=raw*np.sin(theta)[None,:];zz=zs[:,None];front=np.clip((np.cos(theta)[None,:]-.15)/.65,0,1)
nose=np.exp(-.5*(xx/.018)**4-.5*((zz-1.669)/.026)**4)
mouth=np.exp(-.5*(xx/.030)**4-.5*((zz-1.616)/.013)**4)
eyes=np.exp(-.5*((abs(xx)-.031)/.016)**4-.5*((zz-1.699)/.012)**4)
features=np.clip(np.maximum.reduce([nose,mouth,.72*eyes])*front,0,1)
q=(1-features)*q+features*detail
# Preserve cranial cap rather than extending the morphology filter over the pole.
top=np.clip((zs-1.77)/.022,0,1);top=top*top*(3-2*top);q=(1-top[:,None])*q+top[:,None]*gaussian_filter(raw,sigma=(.6,1),mode=('nearest','wrap'))
# Under the sternocleidomastoid/trapezius surfaces, the new throat envelope stays inset.
neck=np.clip((1.625-zs)/.055,0,1);back=np.clip((np.cos(theta)*-1+.1)/.65,0,1)
q+=neck[:,None]*(.001-.005*back[None,:])
# Smooth exposed forehead ridges and retain a modest clean mouth/nose impression.
v=np.stack([plane+q*np.sin(theta)[None,:],cy(zs)[:,None]-q*np.cos(theta)[None,:],np.broadcast_to(zs[:,None],q.shape)],axis=-1).reshape(-1,3)
faces=[];n=len(theta)
for j in range(len(zs)-1):
 for k in range(n):
  u=j*n+k;w=j*n+(k+1)%n;faces.extend([(u,w,w+n),(u,w+n,u+n)])
# Pole caps. Ensure consistent outward orientation (checked in Blender).
for j,z in [(0,zs[0]),(len(zs)-1,1.8)]:
 index=len(v);v=np.vstack([v,[plane,cy(z),z]])
 for k in range(n):
  u=j*n+k;w=j*n+(k+1)%n;faces.append((index,w,u)if j==0 else(index,u,w))
args.output.parent.mkdir(parents=True,exist_ok=True)
np.savez_compressed(args.output,v=v,f=np.array(faces),zs=zs,raw=raw,clean=q)
print(v.shape,len(faces))

args.output.with_suffix('.json').write_text(json.dumps({'method':'Horizontal radial exterior sampling from pass-three cranial, facial and cervical triangles; symmetric morphology closing and curvature filtering; finer filtered nose/mouth/eye landmarks; local throat envelope under retained cervical muscles.','z_samples':len(zs),'angular_samples':len(theta),'large_closing_samples':[15,23],'detail_closing_samples':[7,11],'large_gaussian_sigma':[2.6,2.1],'preserved_landmarks':'Softly filtered source nose, lips and orbital mass; no exposed internal facial layers.','geometry_is_source_guided':True,'new_medical_anatomy_claim':False,'baseline_sha256':json.loads((args.work/'parts.json').read_text())['baseline_sha256'],'surface_sha256':hashlib.sha256(args.output.read_bytes()).hexdigest(),'builder_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2)+'\n')
