"""Coherent six-zone partition on the existing shoulder chart; no mesh changes."""
import json,copy
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.interpolate import PchipInterpolator,UnivariateSpline
from scipy.spatial import cKDTree
from scipy.ndimage import label,binary_fill_holes
from glb_io import source,read_glb,write_glb,sha
from iphone_deltoid_guides import cache,project,ROOT,BASE,OUT
from uv_zone_components import stitched

def dump(name,data):(OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def angle(points):return np.arctan2(points[:,2]+.055,np.abs(points[:,0])-.177)
def smoothstep(x):x=np.clip(x,0,1);return x*x*(3-2*x)
def curve(points):
 if points[0,1]>points[-1,1]:points=points[np.argmax(points[:,1]):]
 else:points=points[:np.argmax(points[:,1])+1]
 y=points[:,1];a=angle(points);order=np.argsort(y);y,a=y[order],a[order];unique=np.r_[True,np.diff(y)>1e-6];y,a=y[unique],a[unique]
 # Shape-preserving interpolation, then gentle regularization of ray/triangle noise.
 levels=np.linspace(y[0],y[-1],40);values=PchipInterpolator(y,a)(levels)
 fit=UnivariateSpline(levels,values,s=.0015,k=3)
 return lambda yy:fit(np.clip(yy,levels[0],levels[-1]))

def main():
 c=cache();world=c['world'];normals=c['normal'];sourceface=c['face'];covered=c['covered'];eligible=sourceface>=0
 old=np.array(Image.open(BASE/'textures/muscle-ids.png'));spec=json.loads((BASE/'regions.json').read_text());guides=json.loads((OUT/'surface-guides.json').read_text());ids=old.copy();ids[ids>=3]=0
 pectoral=np.maximum(np.array(Image.open(BASE/'textures/pectoralis.left.png')),np.array(Image.open(BASE/'textures/pectoralis.right.png')))
 diagnostic={};fields={}
 for side,codes in [('right',[6,7,8]),('left',[3,4,5])]:
  points={}
  for g in guides['curves']:points[g['view']+'.'+g['name']]=np.array([p[side+'Point'] for p in g['samples']])
  insertion=np.array(guides['insertion'][side]);y0=float(insertion[1]);a0=float(angle(insertion[None])[0]);y1=.50
  def blended(name):
   chosen=[p for k,p in points.items() if k.endswith('.'+name)];curves=[curve(p) for p in chosen]
   def fun(y):
    raw=sum(f(y) for f in curves)/len(curves)
    if name=='posterior_lateral':
     primary=curve(points['posterior.'+name]);ow=smoothstep((y-.595)/.025);raw=raw*(1-ow)+primary(y)*ow
    w=smoothstep((y-y0)/(y1-y0));return a0+(raw-a0)*w
   return fun
  anterior=blended('anterior_lateral');posterior=blended('posterior_lateral');front=curve(points['anterior.anterior_outer'])
  oldpoints=world[covered&np.isin(old,codes)];backpoints=world[covered&(old==codes[2])];aa=angle(backpoints)
  levels=np.linspace(y0,.615,48);extrema=[]
  for y in levels:
   selected=np.abs(backpoints[:,1]-y)<.0025
   extrema.append(float(np.quantile(aa[selected],.001)) if selected.any() else a0)
  back=UnivariateSpline(levels,np.array(extrema),s=.012,k=3);upper=curve(points['posterior.posterior_outer_upper'])
  top_a=np.mean([p[np.argmax(p[:,1])] for k,p in points.items() if k.endswith('.anterior_lateral')],axis=0)
  q=points['posterior.posterior_lateral'];top_p=q[np.argmax(q[:,1])]
  atop=float(angle(top_a[None])[0]);ptop=float(angle(top_p[None])[0]);ytop_a=top_a[1];ytop_p=top_p[1];crown=max(ytop_a,ytop_p)+.009
  cap=PchipInterpolator([ptop-.35,ptop,0,atop,atop+.35],[ytop_p-.025,ytop_p,crown,ytop_a,ytop_a-.025])
  y,x=np.where(eligible&(np.abs(world[:,:,0])>.112)&(np.abs(world[:,:,0])<.30)&(world[:,:,1]>=y0)&(world[:,:,1]<.67)&(world[:,:,2]>-.195)&(world[:,:,2]<.14)&((world[:,:,0]<0) if side=='right' else (world[:,:,0]>0)))
  p=world[y,x];theta=angle(p);yy=p[:,1];w=smoothstep((yy-y0)/(y1-y0))
  lower_back=back(np.clip(yy,levels[0],levels[-1]));blend=smoothstep((yy-.569)/.012)
  outer_back=lower_back*(1-blend)+upper(yy)*blend
  outer_back=a0+(outer_back-a0)*w;outer_front=a0+(front(yy)-a0)*w
  ap=anterior(yy);pp=posterior(yy)
  # The crown above each origin belongs to the middle head, not a vertical band.
  pp=np.where(yy>ytop_p,ptop,pp);ap=np.where(yy>ytop_a,atop,ap)
  outer_back=np.where(yy>ytop_p,ptop,outer_back);outer_front=np.where(yy>ytop_a,atop,outer_front)
  distance,_=cKDTree(oldpoints).query(p,workers=1)
  cap_y=cap(np.clip(theta,ptop-.35,atop+.35))
  inside=(theta>=outer_back)&(theta<=outer_front)&(yy<=cap_y)&(distance<.029)&(pectoral[y,x]==0)
  code=np.where(theta>ap,codes[0],np.where(theta<pp,codes[2],codes[1])).astype(np.uint8)
  ids[y[inside],x[inside]]=code[inside]
  # Store the same shared boundaries once. Both neighboring regions use these fields.
  samples=np.linspace(y0+.0001,max(crown,ytop_a,ytop_p),220)
  fields[side]={'insertion':insertion.tolist(),'chartAxisSourceM':[.177,-.055],
    'rows':[{'y':float(q),'anteriorLateralAngle':float(anterior(np.array([q]))[0]),'posteriorLateralAngle':float(posterior(np.array([q]))[0])} for q in samples],
    'originAnterior':top_a.tolist(),'originPosterior':top_p.tolist(),'crownY':float(crown)}
  diagnostic[side]={'candidateTexels':len(y),'selectedTexels':int(inside.sum()),'commonInsertionSourceM':insertion.tolist(),'manualEndpointsSourceM':{k:p[-1].tolist() for k,p in points.items() if not k.endswith('posterior_outer_upper')}}
 # Constrain the upper posterior arc to the projected 3D guide. This avoids
 # a chart fold near the origin: the excess on the shared side belongs to lateral.
 refs=json.loads((OUT/'iphone-reference-guides.json').read_text());ref=refs['posterior'];params=np.array(ref['parameters']);center=c['center'].copy()
 cap_corrections={}
 for side,posterior_code,lateral_code in [('right',8,7),('left',5,4)]:
  side_params=params.copy();side_center=center.copy()
  if side=='left':side_params[0]*=-1;side_center[0]*=-1
  def screen(p):
   q=project(p,side_params,side_center);q[:,1]+=261
   if side=='left':q[:,0]=942-q[:,0]
   return q
  curves={g['name']:np.array([p[side+'Point'] for p in g['samples']]) for g in guides['curves'] if g['view']=='posterior'}
  outer=screen(curves['posterior_outer_upper']);shared=screen(curves['posterior_lateral']);outer=outer[np.argmin(outer[:,0]):];shared=shared[(shared[:,0]>outer[-1,0]+.01)&(shared[:,0]<640)]
  arc=np.r_[outer,shared];order=np.argsort(arc[:,0]);arc=arc[order];arc=arc[np.r_[True,np.diff(arc[:,0])>1e-4]]
  cap=PchipInterpolator(arc[:,0],arc[:,1]);join=float(outer[-1,0]);yy,xx=np.where(((ids==posterior_code)|(ids==lateral_code))&(world[:,:,1]>.59));q=screen(world[yy,xx]);inside=(q[:,0]>=arc[0,0])&(q[:,0]<=arc[-1,0]);below=q[:,1]>=cap(np.clip(q[:,0],arc[0,0],arc[-1,0]));excess=inside&~below&(ids[yy,xx]==posterior_code);added=inside&below&(ids[yy,xx]==lateral_code)&(q[:,1]<=arc[:,1].max()+6)
  ids[yy[excess],xx[excess]]=np.where(q[excess,0]>=join,lateral_code,0);ids[yy[added],xx[added]]=posterior_code
  cap_corrections[side]={'upperArcTexelsRegularized':int(excess.sum()),'sharedSideAssignedToLateral':int((excess&(q[:,0]>=join)).sum()),'sharedSideAssignedToPosterior':int(added.sum())}
 # Keep pectoral IDs AND their AA fringes exact. All other changes are six deltoids or background.
 assert np.array_equal(ids[old<=2][old[old<=2]>0],old[old<=2][old[old<=2]>0])
 assert np.array_equal(ids[pectoral>0],old[pectoral>0])
 # Remove only microscopic disconnected boundary fragments after actual UV seam stitching.
 _,_,_,faces=source(ROOT/'assets/models/meshy-e45e5d8.glb');uv=np.load(ROOT/'docs/m4c/meshy-huit-zones/source-uv-binding.npz')['uv_blender'].copy();uv[:,:,1]=1-uv[:,:,1]
 roots=stitched(ids,uv,faces);fragments=[]
 for code in range(3,9):
  unique,counts=np.unique(roots[ids==code],return_counts=True);mainroot=unique[np.argmax(counts)]
  for key,count in zip(unique,counts):
   if key==mainroot:continue
   m=(roots==key)&(ids==code);p=world[m&covered]
   assert count<=128,('Unexpected disconnected surface patch',code,int(count))
   assert len(p)==0 or np.max(np.ptp(p,axis=0))<.006,('Nonlocal boundary fragment',code,int(count))
   ids[m]=0;fragments.append({'code':code,'texels':int(count),'coveredTexels':len(p),'sourceSpanM':np.ptp(p,axis=0).tolist() if len(p) else [0,0,0]})
 for z in spec['zones']:
  path='textures/'+z['id']+'.png'
  if z['code']<=2:(OUT/path).write_bytes((BASE/path).read_bytes())
  else:Image.fromarray(np.where(ids==z['code'],255,0).astype(np.uint8)).save(OUT/path)
 Image.fromarray(ids).save(OUT/'textures/muscle-ids.png')
 for pack in range(2):
  rgba=np.array(Image.open(BASE/f'textures/masks-rgba-{pack}.png'))
  for ch in range(4):
   code=pack*4+ch+1
   if code>=3:rgba[:,:,ch]=np.where(ids==code,255,0).astype(np.uint8)
  Image.fromarray(rgba).save(OUT/f'textures/masks-rgba-{pack}.png')
 color=np.array(Image.open(BASE/'textures/control-basecolor.png'));neutral=color[(old==0)&(pectoral==0)][0];color[(old>=3)|(ids>=3)]=neutral
 for z in spec['zones']:
  if z['code']>=3:color[ids==z['code']]=np.array(Image.open(BASE/'textures/control-basecolor.png'))[old==z['code']][0]
 Image.fromarray(color).save(OUT/'textures/control-basecolor.png');Image.fromarray(np.where(ids!=old,255,0).astype(np.uint8)).save(OUT/'textures/changed-texels.png')
 spec['anatomicalRevision']={'baseCommit':'06fa665','guides':'surface-guides.json','sharedFrontiers':'shared-frontiers.json','method':'Coupled intrinsic shoulder chart on actual 3D triangle positions; no UV mirroring. Shared distal insertion reconciles manual endpoints.','status':'awaiting-user-visual-validation'}
 dump('regions.json',spec);dump('shared-frontiers.json',fields)
 reg=json.loads((BASE/'region-binding.json').read_text());witnesses=json.loads((BASE/'picking-witnesses.json').read_text());changes={}
 for z in reg['zones']:
  code=z['code'];yy,xx=np.where(covered&(ids==code));p=world[yy,xx]
  if code>=3:
   z['boundsSourceM']={'min':p.min(0).tolist(),'max':p.max(0).tolist()};z['centerMethod']='interior texel in corrected three-dimensional region';z.pop('sourceFaceCenterSamples',None);z.pop('faceCenterDiagnosticComponentCounts',None)
   # Prefer an upper-mid-head sample, away from any seam and frontier.
   from scipy.ndimage import distance_transform_edt
   distance=distance_transform_edt(ids==code)[yy,xx];score=distance-120*np.abs(p[:,1]-.565);score[(normals[yy,xx,1]>.55)|(p[:,1]>.602)]=-1e6
   if code in [4,7]:score[(np.abs(normals[yy,xx,1])>.25)|(p[:,1]>.575)]=-1e6
   best=int(np.argmax(score));point=p[best];face=int(sourceface[yy[best],xx[best]]);uv=[float((xx[best]+.5)/2048),float((yy[best]+.5)/2048)];normal=normals[yy[best],xx[best]].copy();normal/=np.linalg.norm(normal)
   z['centerSourceM']=point.tolist()
   for witness in witnesses:
    if witness['expectedId']==z['id']:witness.update({'faceIndex':face,'point':dict(zip(['x','y','z'],map(float,point))),'normal':normal.tolist(),'uvGltf':uv})
  changes[z['id']]={'before':int((old==code).sum()),'after':int((ids==code).sum()),'removed':int(((old==code)&(ids!=code)).sum()),'added':int(((old!=code)&(ids==code)).sum())}
 dump('region-binding.json',reg);dump('picking-witnesses.json',witnesses)
 _,doc,binary=read_glb(BASE/'exports/meshy-eight-zones-control.glb');doc=copy.deepcopy(doc)
 replace={doc['images'][0]['bufferView']:(OUT/'textures/control-basecolor.png').read_bytes(),doc['images'][1]['bufferView']:(OUT/'textures/muscle-ids.png').read_bytes()};data=bytearray()
 for i,view in enumerate(doc['bufferViews']):
  payload=replace.get(i,binary[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']]);data.extend(b'\0'*((-len(data))%4));view['byteOffset']=len(data);view['byteLength']=len(payload);data.extend(payload)
 doc['buffers'][0]['byteLength']=len(data);doc['nodes'][0]['extras']['deltoid_revision']='Six shoulder zones from iPhone guides; immutable source surface';write_glb(OUT/'exports/meshy-eight-zones-control.glb',doc,bytes(data))
 dump('correction.json',{'baseCommit':'06fa665','zones':changes,'sideDiagnostics':diagnostic,'upperPosteriorArcRegularization':cap_corrections,'microscopicBoundaryFragmentsRemoved':fragments,'geometryChanged':False,'uvChanged':False,'normalsChanged':False,'pectoralMaskBytesIdentical':True})
 print(json.dumps(changes,indent=2),flush=True)
if __name__=='__main__':main()
