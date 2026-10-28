"""Independent source, texture, geometry and 3D probe checks of the ID8 extension."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from glb_io import source, read_glb, accessor, sha

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/m4c/meshy-deltoides-residu-local'
OUT=ROOT/'docs/m4c/meshy-posterieur-droit-arrondi'
a=np.array(Image.open(BASE/'textures/muscle-ids.png'))
b=np.array(Image.open(OUT/'textures/muscle-ids.png'))
alpha=np.array(Image.open(OUT/'textures/deltoid.right.posterior.png'))
changed=a!=b
assert changed.any() and np.all(a[changed]==0) and np.all(b[changed]==8)
assert np.all(b[a==8]==8) and np.all(alpha[a==8]==255)
assert np.array_equal(b==8,alpha>=128)
assert np.all(alpha[(a>0)&(a!=8)]==0)
spec=json.loads((OUT/'regions.json').read_text())
assert spec['zones']==json.loads((BASE/'regions.json').read_text())['zones']
for zone in spec['zones']:
    name=zone['id']+'.png'
    if zone['code']!=8:
        assert (OUT/'textures'/name).read_bytes()==(BASE/'textures'/name).read_bytes(),name
        assert np.array_equal(a==zone['code'],b==zone['code'])
assert (OUT/'textures/masks-rgba-0.png').read_bytes()==(BASE/'textures/masks-rgba-0.png').read_bytes()
old=np.array(Image.open(BASE/'textures/masks-rgba-1.png'))
new=np.array(Image.open(OUT/'textures/masks-rgba-1.png'))
assert np.array_equal(old[:,:,:3],new[:,:,:3]) and np.array_equal(new[:,:,3],alpha)
geometry={}
for key,folder in [('before',BASE),('after',OUT)]:
    _,doc,binary=read_glb(folder/'exports/meshy-eight-zones-control.glb')
    primitive=doc['meshes'][0]['primitives'][0]
    geometry[key]={name:accessor(doc,binary,i) for name,i in primitive['attributes'].items()}
    geometry[key]['indices']=accessor(doc,binary,primitive['indices'])
for key in geometry['before']:
    assert geometry['before'][key].dtype==geometry['after'][key].dtype
    assert geometry['before'][key].tobytes()==geometry['after'][key].tobytes(),key
source(ROOT/'assets/models/meshy-e45e5d8.glb')
preservation=json.loads((ROOT/'docs/m4c/meshy-huit-zones/application-preservation.json').read_text())
for item in preservation['checkedFiles']:
    assert sha((ROOT/item['file']).read_bytes())==item['sha256'],item['file']

def weight(array,uv):
    x,y=np.clip(np.array(uv)*array.shape[0]-.5,0,array.shape[0]-1)
    i,j=int(x),int(y);u,v=x-i,y-j
    return float(((1-u)*(1-v)*array[j,i]+u*(1-v)*array[j,min(i+1,len(array)-1)]
                  +(1-u)*v*array[min(j+1,len(array)-1),i]+u*v*array[min(j+1,len(array)-1),min(i+1,len(array)-1)])/255)
probes=json.loads((OUT/'projected-outline.json').read_text())['probes']
for p in probes:
    x,y=np.clip((np.array(p['uv'])*len(a)).astype(int),0,len(a)-1)
    p.update(beforeId=int(a[y,x]),afterId=int(b[y,x]),
             greenWeightBefore=weight(old[:,:,3],p['uv']),greenWeightAfter=weight(alpha,p['uv']))
added=[p for p in probes if p['beforeId']==0 and p['afterId']==8]
assert len(added)>=3,'Annotated expansion must be present on multiple real 3D hits'
for p in probes:
    if p['annotationPixel'] in [[70,140],[96,245]]:
        assert p['beforeId']==p['afterId']==0 and p['greenWeightAfter']<.001
    if p['beforeId'] in [7,8]:
        assert p['afterId']==p['beforeId']
(OUT/'probe-verification.json').write_text(json.dumps(probes,indent=2)+'\n')
report={'referenceCommit':'18e1a44','onlyIDTransition':[0,8],
        'addedIDTexels':int(changed.sum()),'oldGreenFullyPreserved':True,
        'sevenOtherMasksByteIdentical':True,'otherPackedChannelsBitIdentical':True,
        'antialiasingOnlyOnID8NeutralBoundary':True,'geometryBuffersBitIdentical':list(geometry['after']),
        'triangles':len(geometry['after']['indices'])//3,'exportVertices':len(geometry['after']['POSITION']),
        'eightStableIDs':[z['id'] for z in spec['zones']],
        'protectedApplicationFilesUnchanged':len(preservation['checkedFiles']),
        'newGreen3DSurfaceProbes':len(added),'outsideNeutralGuards':2,
        'sourceGlbSha256':sha((ROOT/'assets/models/meshy-e45e5d8.glb').read_bytes())}
(OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)
