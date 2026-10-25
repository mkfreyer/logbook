import numpy as np,json,hashlib,argparse
from pathlib import Path
from scipy.ndimage import gaussian_filter,map_coordinates
from skimage.measure import marching_cubes
parser=argparse.ArgumentParser();parser.add_argument('--work',type=Path,required=True);args=parser.parse_args();w=args.work;a=np.load(w/'fields.npz');h=float(a['step']);origin=a['origin'];foot=a['foot'];raw=a['field']
alpha=np.clip((np.indices(raw.shape)[2]*h+origin[2]-.06)/.05,0,1);alpha=alpha**2*(3-2*alpha)
field=(1-alpha)*gaussian_filter(raw,.35)+alpha*gaussian_filter(raw,.7)
t=np.clip((foot-.009)/.008,0,1);collar=t*t*(3-2*t)
# Keep sharp original tendon tips under the reconstructed ankle envelope.
# Field smoothing alone can recede behind those unchanged source triangles.
z=np.indices(raw.shape)[2]*h+origin[2]
ankle=np.clip((z-.09)/.03,0,1);ankle=ankle*ankle*(3-2*ankle)
field+=.0015*collar-.0006*ankle*(1-collar)
v,f,_,_=marching_cubes(field,0,spacing=(h,h,h),allow_degenerate=False,gradient_direction='ascent');v+=origin
q=(v-origin).T/h;d=map_coordinates(foot,q,order=1,mode='nearest');scalar=d-.022
vertices=v.tolist();cache={};faces=[]
def crossing(i,j):
 key=tuple(sorted([i,j]))
 if key not in cache:
  t=scalar[i]/(scalar[i]-scalar[j]);cache[key]=len(vertices);vertices.append((v[i]+t*(v[j]-v[i])).tolist())
 return cache[key]
for tri in f:
 poly=[]
 for i,j in zip(tri,np.roll(tri,-1)):
  i,j=int(i),int(j)
  if scalar[i]<=0:poly.append(i)
  if (scalar[i]<0)!=(scalar[j]<0):poly.append(crossing(i,j))
 if len(poly)>2:
  faces.extend((poly[0],poly[j],poly[j+1])for j in range(1,len(poly)-1))
f=np.array(faces,np.int32);used,inv=np.unique(f,return_inverse=True);v=np.array(vertices)[used];f=inv.reshape(-1,3)
# Orient from the actual construction gradient.
grad=np.array([map_coordinates(g,(v-origin).T/h,order=1,mode='nearest')for g in np.gradient(field,h)]).T
cross=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]])
if np.einsum('ij,ij->',cross,grad[f].mean(1))<0:f=f[:,::-1]
np.savez_compressed(w/'surface.npz',v=v,f=f)
print('SURFACE',len(v),len(f),v.min(0),v.max(0))

(w/'extraction.json').write_text(json.dumps({'forefoot_filter_sigma_m':.35*h,'ankle_filter_sigma_m':.7*h,'filter_height_transition_m':[.06,.11],'ankle_cover_outset_m':.0006,'ankle_cover_height_transition_m':[.09,.12],'contact_inset_m':.0015,'contact_clip_distance_m':.022,'extractor_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2)+'\n')
