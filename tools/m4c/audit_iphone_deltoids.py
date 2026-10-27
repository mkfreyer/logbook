"""Independent invariants: master, GLB geometry/UV/normals, two pectorals, eight IDs."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import binary_fill_holes
from glb_io import read_glb,accessor,source,sha
from iphone_deltoid_guides import ROOT,BASE,OUT,cache
old=np.array(Image.open(BASE/'textures/muscle-ids.png'));new=np.array(Image.open(OUT/'textures/muscle-ids.png'));assert old.shape==new.shape==(2048,2048);assert set(np.unique(new))==set(range(9))
assert np.array_equal(old==1,new==1) and np.array_equal(old==2,new==2)
combined_holes=binary_fill_holes(new>=3)&(new==0)&cache()['covered'];assert not combined_holes.any()
zones=json.loads((OUT/'regions.json').read_text())['zones'];assert zones==json.loads((BASE/'regions.json').read_text())['zones']
masks=[];checks={}
for z in zones:
 path='textures/'+z['id']+'.png';before=(BASE/path).read_bytes();after=(OUT/path).read_bytes();a=np.array(Image.open(OUT/path));masks.append(a)
 if z['code']<=2:assert before==after
 else:assert np.array_equal(a,np.where(new==z['code'],255,0))
 assert np.array_equal(a>=128,new==z['code'])
 checks[z['id']]={'code':z['code'],'sha256':sha(after),'texels':int((new==z['code']).sum()),'unchangedByteForByte':before==after}
assert (np.stack(masks)>0).sum(0).max()==1,'Overlapping editable mask fields'
for pack in range(2):
 a=np.array(Image.open(OUT/f'textures/masks-rgba-{pack}.png'))
 for ch in range(4):assert np.array_equal(a[:,:,ch],masks[pack*4+ch])
_,v,n,f=source(ROOT/'assets/models/meshy-e45e5d8.glb')
_,a,ab=read_glb(BASE/'exports/meshy-eight-zones-control.glb');_,b,bb=read_glb(OUT/'exports/meshy-eight-zones-control.glb');pa=a['meshes'][0]['primitives'][0];pb=b['meshes'][0]['primitives'][0]
geometry={}
for name in ['POSITION','NORMAL','TEXCOORD_0']:
 x=accessor(a,ab,pa['attributes'][name]);y=accessor(b,bb,pb['attributes'][name]);assert np.array_equal(x,y);geometry[name]=sha(y.tobytes())
x=accessor(a,ab,pa['indices']);y=accessor(b,bb,pb['indices']);assert np.array_equal(x,y);geometry['indices']=sha(y.tobytes())
# The derivatives retain the same per-corner original positions and normals.
position=accessor(b,bb,pb['attributes']['POSITION']);normal=accessor(b,bb,pb['attributes']['NORMAL']);index=y.reshape(-1,3)
assert np.array_equal(position[index],v[f]);assert np.array_equal(normal[index],n[f])
assert b['nodes'][0].get('translation')==a['nodes'][0].get('translation');assert b['nodes'][0].get('rotation')==a['nodes'][0].get('rotation');assert b['nodes'][0].get('scale')==a['nodes'][0].get('scale')
for i,file in enumerate(['control-basecolor.png','muscle-ids.png']):
 view=b['bufferViews'][b['images'][i]['bufferView']];embedded=bb[view['byteOffset']:view['byteOffset']+view['byteLength']];assert embedded==(OUT/'textures'/file).read_bytes()
guide=json.loads((OUT/'surface-guides.json').read_text());max_error=0.;minimum_bary=1.
for curve in guide['curves']:
 for row in curve['samples']:
  for side in ['right','left']:
   p=np.array(row[side+'Point']);tri=v[f[row[side+'Face']]];w=np.linalg.lstsq(np.column_stack([tri[1]-tri[0],tri[2]-tri[0]]),p-tri[0],rcond=None)[0];bary=np.r_[1-w.sum(),w];error=np.linalg.norm(bary@tri-p);max_error=max(max_error,error);minimum_bary=min(minimum_bary,float(bary.min()));assert error<1e-6 and bary.min()>-1e-4
fields=json.loads((OUT/'shared-frontiers.json').read_text())
for side,entry in fields.items():
 for row in entry['rows']:assert row['posteriorLateralAngle']<=row['anteriorLateralAngle']+1e-8
report={'status':'passed','sourceSha256':sha((ROOT/'assets/models/meshy-e45e5d8.glb').read_bytes()),'triangles':len(f),'originalVertices':len(v),'geometryAndUVHashes':geometry,'originalPerCornerPositionsAndNormalsIdentical':True,'originalNodeTransformPreserved':True,'atlasUniqueIDs':list(map(int,np.unique(new))),'editableMaskOverlapTexels':0,'combinedDeltoidFootprintInternalHoles':0,'twoPectoralsByteIdentical':True,'masks':checks,'guideMaxDistanceFromOriginalTriangleM':max_error,'guideMinimumBarycentricWeight':minimum_bary,'leftReprojectionMaxDistanceM':max(p['leftProjectionDistanceM'] for c in guide['curves'] for p in c['samples']),'sharedFrontiersOrdered':True,'controlGlbEmbeddedTexturesExact':True,'controlGlbSha256':sha((OUT/'exports/meshy-eight-zones-control.glb').read_bytes())}
(OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
