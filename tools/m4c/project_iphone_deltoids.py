"""Project yellow guides onto original triangles; mirror guide positions to real left triangles."""
import sys,json
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from scipy.interpolate import PchipInterpolator
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/m4c'))
from glb_io import source
OUT=ROOT/'docs/m4c/meshy-deltoides-reperes-iphone'
_,v,n,f=source(ROOT/'assets/models/meshy-e45e5d8.glb')
refs=json.loads((OUT/'iphone-reference-guides.json').read_text())
tree=BVHTree.FromPolygons(v.tolist(),f.tolist(),all_triangles=True)
centers=v[f].mean(1);select=np.flatnonzero((centers[:,0]>.115)&(centers[:,1]>.43)&(centers[:,1]<.69)&(centers[:,2]>-.20)&(centers[:,2]<.15))
left=BVHTree.FromPolygons(v.tolist(),f[select].tolist(),all_triangles=True)
records=[]
for view,ref in refs.items():
 eye=np.array(ref['cameraPositionSourceM']);rotation=np.array(ref['cameraRotationSource']);focal=1186/(2*np.tan(np.deg2rad(18)))
 for name,control in ref['curves'].items():
  control=np.array(control,float);t=np.r_[0,np.cumsum(np.linalg.norm(np.diff(control,axis=0),axis=1))];t/=t[-1]
  pixels=PchipInterpolator(t,control,axis=0)(np.linspace(0,1,96));rows=[]
  for pixel in pixels:
   direction=rotation@np.array([(pixel[0]-471)/focal,-(pixel[1]-261-593)/focal,-1]);direction/=np.linalg.norm(direction)
   hit=tree.ray_cast(Vector(eye),Vector(direction));assert hit[0] is not None,(view,name,pixel)
   p=np.array(hit[0]);assert -.32<p[0]<-.09 and .42<p[1]<.71,(view,name,pixel,p)
   mirror=p.copy();mirror[0]*=-1;near=left.find_nearest(Vector(mirror));assert near[0] is not None and near[3]<.012,(view,name,near[3])
   rows.append({'pixel':pixel.tolist(),'rightPoint':p.tolist(),'rightFace':int(hit[2]),'leftPoint':list(near[0]),'leftFace':int(select[near[2]]),'leftProjectionDistanceM':float(near[3])})
  records.append({'view':view,'name':name,'samples':rows})
  pts=np.array([r['rightPoint'] for r in rows]);print(view,name,'range',pts.min(0),pts.max(0),flush=True)
anchor=tree.find_nearest(Vector(json.loads((OUT/'common-insertion-fit.json').read_text())['rightSourcePoint']));a=np.array(anchor[0]);a[0]*=-1;la=left.find_nearest(Vector(a))
anchors={'right':list(anchor[0]),'left':list(la[0]),'rightFace':int(anchor[2]),'leftFace':int(select[la[2]]),'reason':'Least-squares common surface insertion reconciles incompatible manual endpoints; no separate pointed tails.'}
(OUT/'surface-guides.json').write_text(json.dumps({'method':'First perspective ray hit on original triangles; reflected guide locations reprojected by nearest real left-shoulder triangle. No vertex or UV changes.','curves':records,'insertion':anchors},indent=2)+'\n')
