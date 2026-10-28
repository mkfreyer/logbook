"""Independent controls: removal below the guide only, no geometry or other masks."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from glb_io import source,read_glb,accessor,sha

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/m4c/meshy-posterieur-droit-arrondi'
OUT=ROOT/'docs/m4c/meshy-posterieur-droit-bord-inferieur'
old=np.array(Image.open(BASE/'textures/muscle-ids.png'));new=np.array(Image.open(OUT/'textures/muscle-ids.png'))
a=np.array(Image.open(BASE/'textures/deltoid.right.posterior.png'))
b=np.array(Image.open(OUT/'textures/deltoid.right.posterior.png'))
changed=old!=new
assert changed.any() and np.all(old[changed]==8) and np.all(new[changed]==0)
assert np.all(b<=a) and np.array_equal(new==8,b>=128)
spec=json.loads((OUT/'regions.json').read_text())
assert spec['zones']==json.loads((BASE/'regions.json').read_text())['zones']
for z in spec['zones']:
    if z['code']!=8:
        f=z['id']+'.png';assert (OUT/'textures'/f).read_bytes()==(BASE/'textures'/f).read_bytes(),f
        assert np.array_equal(old==z['code'],new==z['code'])
assert (OUT/'textures/masks-rgba-0.png').read_bytes()==(BASE/'textures/masks-rgba-0.png').read_bytes()
packed_old=np.array(Image.open(BASE/'textures/masks-rgba-1.png'))
packed_new=np.array(Image.open(OUT/'textures/masks-rgba-1.png'))
assert np.array_equal(packed_old[:,:,:3],packed_new[:,:,:3]) and np.array_equal(packed_new[:,:,3],b)
samples=np.load(OUT/'source-green-samples.npz')
upper=samples['screen'][:,1]<231
uy,ux=samples['y'][upper],samples['x'][upper]
assert np.array_equal(a[uy,ux],b[uy,ux]) and np.array_equal(old[uy,ux],new[uy,ux])
geometry={}
for state,folder in [('before',BASE),('after',OUT)]:
    _,doc,binary=read_glb(folder/'exports/meshy-eight-zones-control.glb');p=doc['meshes'][0]['primitives'][0]
    geometry[state]={key:accessor(doc,binary,i) for key,i in p['attributes'].items()}
    geometry[state]['indices']=accessor(doc,binary,p['indices'])
    for index,name in [(0,'control-basecolor.png'),(1,'muscle-ids.png')]:
        view=doc['bufferViews'][doc['images'][index]['bufferView']]
        start=view.get('byteOffset',0)
        assert binary[start:start+view['byteLength']]==(folder/'textures'/name).read_bytes()
for key in geometry['before']:
    assert geometry['before'][key].dtype==geometry['after'][key].dtype
    assert geometry['before'][key].tobytes()==geometry['after'][key].tobytes(),key
source(ROOT/'assets/models/meshy-e45e5d8.glb')
manifest=json.loads((ROOT/'docs/m4c/meshy-huit-zones/application-preservation.json').read_text())
for entry in manifest['checkedFiles']:assert sha((ROOT/entry['file']).read_bytes())==entry['sha256'],entry['file']

def weight(image,uv):
    x,y=np.clip(np.array(uv)*len(image)-.5,0,len(image)-1);i,j=int(x),int(y);u,v=x-i,y-j
    return float(((1-u)*(1-v)*image[j,i]+u*(1-v)*image[j,min(i+1,len(image)-1)]
                 +(1-u)*v*image[min(j+1,len(image)-1),i]+u*v*image[min(j+1,len(image)-1),min(i+1,len(image)-1)])/255)
projected=json.loads((OUT/'projected-outline.json').read_text())
probes=projected['probes']
for p in probes:
    x,y=np.clip((np.array(p['uv'])*len(old)).astype(int),0,len(old)-1)
    p.update(beforeId=int(old[y,x]),afterId=int(new[y,x]),
             greenWeightBefore=weight(a,p['uv']),greenWeightAfter=weight(b,p['uv']))
removed=[p for p in probes if p['beforeId']==8 and p['afterId']==0]
assert len(removed)>=3,'The excessive green below the new annotation must actually disappear'
for p in probes:
    if p['annotationPixel'] in [[180,320],[350,450],[500,530],[580,460],[145,60],[90,145],[770,530],[300,620]]:
        assert p['beforeId']==p['afterId'],p
(OUT/'probe-verification.json').write_text(json.dumps(probes,indent=2)+'\n')
seam=[]
for p in projected['curveSurfaceSamples']:
    annotation_x=(p['pixel'][0]-160)*873/447
    if 430<annotation_x<520:seam.append(weight(b,p['uv']))
assert .25<min(seam) and max(seam)<.75,'The new contour must cross the central UV seam without a retained full-green spur'
report={'referenceCommit':'ad08cef','onlyIDTransition':[8,0],'removedIDTexels':int(changed.sum()),
        'noGreenAdded':True,'upperRoundCoverageAndIDsBitIdentical':True,'protectedUpperTexels':int(upper.sum()),
        'sevenOtherMasksByteIdentical':True,'otherPackedChannelsBitIdentical':True,
        'embeddedGLBAtlasAndPaletteMatchSourcePNG':True,
        'geometryBuffersBitIdentical':list(geometry['after']),'triangles':len(geometry['after']['indices'])//3,
        'exportVertices':len(geometry['after']['POSITION']),
        'eightStableIDs':[z['id'] for z in spec['zones']],
        'protectedApplicationFilesUnchanged':len(manifest['checkedFiles']),
        'neutralizedSurfaceProbes':len(removed),
        'centralSeamCurveCoverageRange':[min(seam),max(seam)],
        'sourceGlbSha256':sha((ROOT/'assets/models/meshy-e45e5d8.glb').read_bytes())}
(OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)
