"""Reconstruct annotated iPhone views on the unchanged UV-bound Meshy surface."""
import json,sys
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import ConvexHull
from scipy.ndimage import distance_transform_edt
from PIL import Image
from glb_io import source
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/m4c/meshy-posterieurs-harmonises'
OUT=ROOT/'docs/m4c/meshy-deltoides-reperes-iphone'
CACHE=ROOT.parent/'m4c-deltoides-reperes-cache.npz'
W,H=942,1186;TOP=261
# Manually digitized guides, full original 942×2048 screenshot coordinates.
REF={
 'posterior':{'code':8,'initial':[-2.5,.35,.75,.52],
 'old':[[496,560],[536,587],[578,630],[622,684],[655,732],[675,786],[714,856],[748,944],[779,1028],[811,1102],[758,1086],[686,1059],[620,1030],[559,992],[505,944],[462,890],[426,829],[401,767],[390,707],[395,660],[435,610],[471,575]],
 'yellow':[[390,703],[381,688],[378,646],[375,611],[376,586],[401,566],[444,533],[492,522],[558,523],[596,551],[625,608],[658,673],[697,726],[730,809],[750,918],[772,1005],[776,1034],[768,1063]],
 'curves':{'posterior_outer_upper':[[390,703],[381,688],[378,646],[375,611],[376,586],[401,566],[444,533],[492,522],[558,523]],'posterior_lateral':[[558,523],[596,551],[625,608],[658,673],[697,726],[730,809],[750,918],[772,1005],[776,1034],[768,1063]]}},
 'lateral':{'code':7,'initial':[-1.55,.25,.75,.53],
 'old':[[214,470],[248,482],[300,487],[365,494],[345,553],[322,622],[299,690],[277,765],[246,856],[220,819],[192,770],[164,713],[145,654],[147,597],[171,531]],
 'yellow':[[249,465],[210,530],[182,600],[177,661],[185,716],[208,783],[247,853],[270,865],[330,801],[366,745],[390,683],[398,622],[394,558],[383,493]],
 'curves':{'posterior_lateral':[[249,465],[210,530],[182,600],[177,661],[185,716],[208,783],[258,860]],'anterior_lateral':[[383,493],[394,558],[398,622],[390,683],[366,745],[330,801],[258,860]]}},
 'anterior':{'code':6,'initial':[-.6,.1,.75,.48],
 'old':[[22,830],[39,720],[48,620],[84,523],[143,433],[201,387],[239,390],[290,409],[326,452],[340,497],[341,545],[324,599],[295,644],[244,691],[180,738],[105,785]],
 'yellow':[[300,390],[240,435],[198,500],[165,575],[142,665],[122,744],[95,818],[163,781],[213,736],[272,680],[317,635],[351,587],[377,533],[385,480],[373,435],[345,404]],
 'curves':{'anterior_lateral':[[300,390],[240,435],[198,500],[165,575],[142,665],[122,744],[95,818]],'anterior_outer':[[300,390],[345,404],[373,435],[385,480],[377,533],[351,587],[317,635],[272,680],[213,736],[163,781],[95,818]]}}
}
def cache():
 if CACHE.exists():return np.load(CACHE)
 _,v,n,f=source(ROOT/'assets/models/meshy-e45e5d8.glb');bind=np.load(ROOT/'docs/m4c/meshy-huit-zones/source-uv-binding.npz');uv=bind['uv_blender'].copy();uv[:,:,1]=1-uv[:,:,1];size=2048
 world=np.zeros((size,size,3),np.float32);normal=np.zeros_like(world);face=np.full((size,size),-1,np.int32);jac=np.zeros((size,size,3,2),np.float32)
 for i in np.flatnonzero(bind['domain']):
  t=uv[i].astype(float)*size-.5;lo=np.maximum(np.ceil(t.min(0)).astype(int),0);hi=np.minimum(np.floor(t.max(0)).astype(int),size-1)
  if np.any(hi<lo):continue
  xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1));p=np.column_stack([xx.ravel(),yy.ravel()]);mat=np.column_stack([t[1]-t[0],t[2]-t[0]])
  if abs(np.linalg.det(mat))<1e-12:continue
  inv=np.linalg.inv(mat);ab=(p-t[0])@inv.T;bary=np.column_stack([1-ab.sum(1),ab]);ok=(bary>=-1e-8).all(1);p,bary=p[ok],bary[ok]
  if len(p):
   x,y=p.T;world[y,x]=bary@v[f[i]];normal[y,x]=bary@n[f[i]];face[y,x]=i;jac[y,x]=np.column_stack([v[f[i,1]]-v[f[i,0]],v[f[i,2]]-v[f[i,0]]])@inv
 covered=face>=0;dist,near=distance_transform_edt(~covered,return_indices=True);yy,xx=np.where(~covered&(dist<=4));ny,nx=near[:,yy,xx]
 world[yy,xx]=world[ny,nx]+np.einsum('nij,nj->ni',jac[ny,nx],np.column_stack([xx-nx,yy-ny]));normal[yy,xx]=normal[ny,nx];face[yy,xx]=face[ny,nx]
 center=(v.min(0)+v.max(0))/2
 np.savez_compressed(CACHE,world=world,normal=normal,face=face,covered=covered,center=center)
 return np.load(CACHE)
def basis(params,center):
 yaw,pitch,distance,ty=params
 target=np.array([center[0],ty,center[2]]);out=np.array([np.sin(yaw)*np.cos(pitch),np.sin(pitch),np.cos(yaw)*np.cos(pitch)])
 eye=target+out*distance;right=np.cross([0,1,0],out);right/=np.linalg.norm(right);up=np.cross(out,right)
 return eye,np.column_stack([right,up,out]),target

def project(points,params,center):
 eye,rotation,_=basis(params,center);q=(points-eye)@rotation;f=H/(2*np.tan(np.deg2rad(18)))
 return np.column_stack([W/2+q[:,0]/(-q[:,2])*f,H/2-q[:,1]/(-q[:,2])*f])

def fit():
 data=cache();ids=np.array(Image.open(BASE/'textures/muscle-ids.png'));result={};directions=np.column_stack([np.cos(np.linspace(0,2*np.pi,64,endpoint=False)),np.sin(np.linspace(0,2*np.pi,64,endpoint=False))])
 for key,ref in REF.items():
  points=data['world'][(ids==ref['code'])&data['covered']][::3]
  target=np.array(ref['old'],float);target[:,1]-=TOP;support=(target@directions.T).max(0)
  def residual(params):
   q=project(points,params,data['center']);return ((q@directions.T).max(0)-support)
  a=np.array(ref['initial']);fit=least_squares(residual,a,bounds=([a[0]-.8,-.1,.35,.25],[a[0]+.8,.9,1.8,.8]),diff_step=1e-4,max_nfev=250)
  eye,rotation,target3=basis(fit.x,data['center']);entry={**ref,'parameters':fit.x.tolist(),'cameraPositionSourceM':eye.tolist(),'cameraTargetSourceM':target3.tolist(),'cameraRotationSource':rotation.tolist(),'resolution':[W,H],'fovDegrees':36,'canvasTopPixel':TOP,'supportErrorRmsPx':float(np.sqrt(np.mean(fit.fun**2))),'screenshotCameraMetadataAvailable':False}
  result[key]=entry;print(key,fit.x,'fit rms px',entry['supportErrorRmsPx'],flush=True)
 (OUT/'iphone-reference-guides.json').write_text(json.dumps(result,indent=2)+'\n')
 points=data['world'][(ids>=6)&data['covered']];points=points[(points[:,1]>.449)&(points[:,1]<.49)&(points[:,2]>-.09)&(points[:,2]<-.018)]
 errors=[]
 for key,ref in result.items():
  target=np.array(ref['curves']['anterior_lateral' if key!='posterior' else 'posterior_lateral'][-1],float)-[0,TOP]
  errors.append(np.sum((project(points,ref['parameters'],data['center'])-target)**2,axis=1))
 cost=sum(errors);best=int(np.argmin(cost));point=points[best]
 (OUT/'common-insertion-fit.json').write_text(json.dumps({'rightSourcePoint':point.tolist(),'method':'Least squared reprojection error to all three annotated endpoints, constrained to actual original shoulder surface texels near the shared insertion.','rmsPixelError':float(np.sqrt(cost[best]/3)),'perViewErrorPx':{k:float(np.sqrt(e[best])) for k,e in zip(result,errors)}},indent=2)+'\n')
 print('SHARED_INSERTION',point,'RMS px',float(np.sqrt(cost[best]/3)),flush=True)

if __name__=='__main__':fit()
