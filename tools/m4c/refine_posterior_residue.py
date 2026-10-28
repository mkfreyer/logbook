"""Remove only the annotated right-green boundary spur in source UV data.

Camera-guided painting is evaluated on real 3D surface samples and visibility,
not applied to a screenshot. Geometry, UVs and the seven other masks stay intact.
"""
import copy,json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.interpolate import PchipInterpolator
from scipy.spatial import cKDTree
from scipy.ndimage import distance_transform_edt,label,binary_dilation
from glb_io import source,read_glb,write_glb,sha
root=Path(__file__).resolve().parents[2];base=root/'docs/m4c/meshy-deltoides-limite-inferieure';out=root/'docs/m4c/meshy-deltoides-residu-local'
_,v,n,f=source(root/'assets/models/meshy-e45e5d8.glb');binding=np.load(root/'docs/m4c/meshy-huit-zones/source-uv-binding.npz');uv=binding['uv_blender'].copy();uv[:,:,1]=1-uv[:,:,1]
old=np.array(Image.open(base/'textures/muscle-ids.png'));new=old.copy();size=len(old)
guides=json.loads((out/'patch-guides.json').read_text());rays=json.loads((out/'surface-samples.json').read_text());tree=cKDTree([p['point'] for p in rays])
world=np.zeros((*old.shape,3),np.float32);coverage=np.zeros(old.shape,bool)
for face in np.flatnonzero(binding['domain']):
    t=uv[face].astype(float)*size-.5;lo=np.maximum(np.ceil(t.min(0)).astype(int),0);hi=np.minimum(np.floor(t.max(0)).astype(int),size-1)
    if np.any(hi<lo):continue
    xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1));q=np.column_stack([xx.ravel(),yy.ravel()]);m=np.column_stack([t[1]-t[0],t[2]-t[0]])
    if abs(np.linalg.det(m))<1e-12:continue
    ab=(q-t[0])@np.linalg.inv(m).T;w=np.column_stack([1-ab.sum(1),ab]);inside=(w>=-1e-8).all(1);q=q[inside];w=w[inside]
    if len(w):x,y=q.T;coverage[y,x]=True;world[y,x]=w@v[f[face]]
_,nearest=distance_transform_edt(~coverage,return_indices=True)
gy,gx=np.where(old==8);points=world[gy,gx].copy();pad=~coverage[gy,gx];points[pad]=world[nearest[0][gy[pad],gx[pad]],nearest[1][gy[pad],gx[pad]]]
cam=np.array(guides['camera_matrix']);blender=points[:,[0,2,1]].copy();blender[:,1]*=-1;local=(blender-cam[:3,3])@cam[:3,:3]
screen=np.column_stack([(local[:,0]/.29+.5)*640,(.5-local[:,1]/.29)*640]);control=np.array(guides['boundaryYX']);boundary=PchipInterpolator(control[:,0],control[:,1],extrapolate=False)
box=guides['supportBoxM'];within=((points>=box['min'])&(points<=box['max'])).all(1)
distance,_=tree.query(points);cut=within&(distance<=guides['visibilityDistanceM'])&(screen[:,1]>=control[0,0])&(screen[:,1]<=control[-1,0])&(screen[:,0]<boundary(np.clip(screen[:,1],control[0,0],control[-1,0])))
removed=np.zeros(old.shape,bool);removed[gy[cut],gx[cut]]=True;new[removed]=0
# Local raster cleanup only; never touch any other zone or distant green edge.
parts,count=label(new==8);counts=np.bincount(parts.ravel());single=np.flatnonzero(counts==1);single=single[single!=0]
discard=np.isin(parts,single)&binary_dilation(removed,iterations=1);new[discard]=0;removed[discard]=True
assert removed.any() and np.all(old[removed]==8) and np.array_equal(old[~removed],new[~removed])
assert np.all(np.unique(new)==np.arange(9))
Image.fromarray(new).save(out/'textures/muscle-ids.png');Image.fromarray(removed.astype(np.uint8)*255).save(out/'textures/changed-texels.png')
spec=json.loads((base/'regions.json').read_text());spec['residueCorrection']={'referenceCommit':'71f70dc','onlyTransition':[8,0],'sourceGuides':'patch-guides.json','side':'right','method':'Local surface-projected UV border retreat with nearest visible 3D support; no global resegmentation.'}
(out/'regions.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n')
for zone in spec['zones']:
    name=zone['id']+'.png'
    if zone['code']==8:Image.fromarray((new==8).astype(np.uint8)*255).save(out/'textures'/name)
    else:(out/'textures'/name).write_bytes((base/'textures'/name).read_bytes())
(out/'textures/masks-rgba-0.png').write_bytes((base/'textures/masks-rgba-0.png').read_bytes())
rgba=np.array(Image.open(base/'textures/masks-rgba-1.png'));rgba[removed,3]=0;Image.fromarray(rgba).save(out/'textures/masks-rgba-1.png')
color=np.array(Image.open(base/'textures/control-basecolor.png'));color[removed]=color[old==0][0];Image.fromarray(color).save(out/'textures/control-basecolor.png')
# Copy every existing geometry buffer; replace only the two embedded PNGs.
_,doc,binary=read_glb(base/'exports/meshy-eight-zones-control.glb');doc=copy.deepcopy(doc);replacements={doc['images'][0]['bufferView']:(out/'textures/control-basecolor.png').read_bytes(),doc['images'][1]['bufferView']:(out/'textures/muscle-ids.png').read_bytes()};data=bytearray()
for index,view in enumerate(doc['bufferViews']):
    payload=replacements.get(index,binary[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']]);data.extend(b'\0'*((-len(data))%4));view['byteOffset']=len(data);view['byteLength']=len(payload);data.extend(payload)
doc['buffers'][0]['byteLength']=len(data);doc['nodes'][0]['extras']['local_green_residue_correction']='71f70dc right posterior spur only, ID8 to neutral'
write_glb(out/'exports/meshy-eight-zones-control.glb',doc,bytes(data))
reg=json.loads((base/'region-binding.json').read_text())
for zone in reg['zones']:
    if zone['code']==8:
        y,x=np.where((new==8)&coverage);p=world[y,x];zone['boundsSourceM']={'min':p.min(0).tolist(),'max':p.max(0).tolist()};zone['centerSourceM']=p.mean(0).tolist();center=uv.mean(1);ij=np.clip((center*size).astype(int),0,size-1);zone['sourceFaceCenterSamples']=int((new[ij[:,1],ij[:,0]]==8).sum())
(out/'region-binding.json').write_text(json.dumps(reg,ensure_ascii=False,indent=2)+'\n');(out/'picking-witnesses.json').write_bytes((base/'picking-witnesses.json').read_bytes())
report={'referenceCommit':'71f70dc','onlyTransition':[8,0],'changedTexels':int(removed.sum()),'isolatedBorderTexelsRemoved':int(discard.sum()),'rightPosteriorTexelsBefore':int((old==8).sum()),'rightPosteriorTexelsAfter':int((new==8).sum()),'rightPosteriorRetainedUVPercent':round(100*(new==8).sum()/(old==8).sum(),4),'sevenOtherMasksByteIdentical':True,'geometryAndUVUnchanged':True,'actualRemovedSurfaceBoundsM':{'min':points[cut&~pad].min(0).tolist(),'max':points[cut&~pad].max(0).tolist()},'controlGlbSha256':sha((out/'exports/meshy-eight-zones-control.glb').read_bytes())}
(out/'correction.json').write_text(json.dumps(report,indent=2)+'\n')
# Inspect exact IDs and bilinear shader weights at the visible defect and guards.
def sample(array,coord):
    x,y=np.clip(coord*size-.5,0,size-1);i,j=int(x),int(y);a,b=x-i,y-j
    return float((1-a)*(1-b)*array[j,i]+a*(1-b)*array[j,min(i+1,size-1)]+(1-a)*b*array[min(j+1,size-1),i]+a*b*array[min(j+1,size-1),min(i+1,size-1)])
before_rgba=np.array(Image.open(base/'textures/masks-rgba-1.png'))[:,:,3]/255.;after_rgba=rgba[:,:,3]/255.;probes=[]
for pixel,role in [([216,456],'remove'),([218,460],'remove'),([222,464],'remove'),([220,438],'keep-green'),([228,448],'keep-green'),([236,474],'keep-green'),([242,450],'keep-blue'),([208,468],'keep-neutral')]:
    ray=next(r for r in rays if r['pixel']==pixel);triangle=v[f[ray['face']]];ab=np.linalg.lstsq(np.column_stack([triangle[1]-triangle[0],triangle[2]-triangle[0]]),np.array(ray['point'])-triangle[0],rcond=None)[0];q=np.r_[1-ab.sum(),ab]@uv[ray['face']];x,y=np.clip((q*size).astype(int),0,size-1)
    entry={**ray,'role':role,'uv':q.tolist(),'beforeId':int(old[y,x]),'afterId':int(new[y,x]),'beforeBilinearGreenWeight':sample(before_rgba,q),'afterBilinearGreenWeight':sample(after_rgba,q)}
    if role=='remove':assert entry['beforeId']==8 and entry['beforeBilinearGreenWeight']>.99 and entry['afterId']==0 and entry['afterBilinearGreenWeight']<.001,entry
    else:assert entry['beforeId']==entry['afterId'],entry
    probes.append(entry)
(out/'cause-and-probes.json').write_text(json.dumps({'cause':'Real ID8/alpha mask footprint at the previous boundary inflection, not interpolation alone. Linear display filtering is unchanged.','probes':probes},indent=2)+'\n');print(json.dumps(report),flush=True)
