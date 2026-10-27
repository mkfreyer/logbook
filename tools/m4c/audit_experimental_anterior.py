"""Independent identity, boundary, export and source-preservation checks."""
import json,subprocess
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation
from glb_io import source,read_glb,accessor,sha
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'docs/m4c/meshy-posterieurs-harmonises';OUT=ROOT/'docs/m4c/experience-anterieur-droit'
old=np.array(Image.open(BASE/'textures/muscle-ids.png'));new=np.array(Image.open(OUT/'textures/muscle-ids.png'))
a=np.array(Image.open(BASE/'textures/deltoid.right.anterior.png'));b=np.array(Image.open(OUT/'textures/deltoid.right.anterior.png'))
changed=new!=old;assert changed.any() and np.all(old[changed]==0) and np.all(new[changed]==6)
assert np.array_equal(new==6,b>=128) and np.array_equal(np.unique(new),np.arange(9))
spec=json.loads((OUT/'regions.json').read_text());assert spec['zones']==json.loads((BASE/'regions.json').read_text())['zones']
records=[];weights=np.zeros(new.shape,np.uint16)
for zone in spec['zones']:
    file='textures/'+zone['id']+'.png';im=np.array(Image.open(OUT/file));weights+=im
    assert np.array_equal(im>=128,new==zone['code'])
    if zone['code']!=6:
        assert (OUT/file).read_bytes()==(BASE/file).read_bytes()
        records.append({'id':zone['id'],'sha256':sha((OUT/file).read_bytes()),'byteIdentical':True})
assert np.max(weights)<=255,'Mask weights overlap'
for group in range(2):
    packed=np.array(Image.open(OUT/f'textures/masks-rgba-{group}.png'))
    for channel,zone in enumerate(spec['zones'][group*4:group*4+4]):
        assert np.array_equal(packed[:,:,channel],np.array(Image.open(OUT/'textures'/(zone['id']+'.png'))))
protected=binary_dilation(old==7,iterations=4)
assert np.array_equal(a[protected],b[protected]),'Anterior/lateral filtering neighborhood changed'
interface=lambda ids:(ids==6)&binary_dilation(ids==7)
assert np.array_equal(interface(old),interface(new))
buffers={};glb={}
for name,folder in [('before',BASE),('after',OUT)]:
    _,doc,binary=read_glb(folder/'exports/meshy-eight-zones-control.glb');p=doc['meshes'][0]['primitives'][0]
    buffers[name]={k:accessor(doc,binary,i) for k,i in p['attributes'].items()};buffers[name]['indices']=accessor(doc,binary,p['indices'])
    glb[name]=doc
    for index,file in [(0,'control-basecolor.png'),(1,'muscle-ids.png')]:
        v=doc['bufferViews'][doc['images'][index]['bufferView']];at=v.get('byteOffset',0)
        assert binary[at:at+v['byteLength']]==(folder/'textures'/file).read_bytes()
for key in buffers['before']:assert buffers['before'][key].tobytes()==buffers['after'][key].tobytes(),key
source(ROOT/'assets/models/meshy-e45e5d8.glb')
# Every previously tracked file is preserved, not only selected app paths.
files=subprocess.check_output(['git','ls-tree','-rz','--name-only','168ac61'],cwd=ROOT).decode().strip('\0').split('\0')
for file in files:
    assert (ROOT/file).read_bytes()==subprocess.check_output(['git','show',f'168ac61:{file}'],cwd=ROOT),file
preservation=json.loads((OUT/'blender-preservation.json').read_text());assert preservation['identical']
assert (OUT/'renders/avant-neutre-reference.png').read_bytes()==(OUT/'renders/apres-neutre-reference.png').read_bytes()
continuity=json.loads((OUT/'continuity-audit.json').read_text());assert continuity['status']=='passed'
curve=json.loads((OUT/'projected-curve.json').read_text())['samples']
codes=[]
for point in curve:
    x,y=np.clip((np.array(point['uv'])*2048).astype(int),0,2047);codes.append(int(old[y,x]))
report={'status':'passed','baseCommit':'168ac61','maskReference':'06fa665',
    'onlyIDTransition':[0,6],'addedIDTexels':int(changed.sum()),'removedIDTexels':0,
    'sevenOtherMasks':records,'anteriorLateralBoundaryAnd4pxNeighborhoodIdentical':True,
    'allEightIDsPresent':[z['id'] for z in spec['zones']],
    'geometryAndUVBuffersBitIdentical':list(buffers['after']),
    'trianglesBefore':len(buffers['before']['indices'])//3,'trianglesAfter':len(buffers['after']['indices'])//3,
    'newTriangles':0,'maxPositionDisplacementM':0,
    'masterSha256':sha((ROOT/'assets/models/meshy-e45e5d8.glb').read_bytes()),
    'neutralBeforeAfterRenderBytesIdentical':True,'allPreviouslyTrackedFilesByteIdentical':len(files),
    'noMaskWeightOverlaps':True,'continuityAudit':'passed',
    'guideSamplesOnProtectedPectoral':codes.count(2),'totalGuideSamples':len(codes),
    'guideLimit':'Guide is clipped to existing neutral surface to preserve pectoral ID2 exactly. The user confirmed the capture depicts the left shoulder and requested transfer to the right; the reconstructed reference view is reflected accordingly, not the UV atlas.',
    'iphoneIntegrationPerformed':False,'visualValidationByUser':False}
(OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report),flush=True)
