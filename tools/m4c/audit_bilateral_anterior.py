"""Verify only ID3 changed; immutable right source, UV/geometry, all old files."""
import json,subprocess
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation
from glb_io import source,read_glb,accessor,sha
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'docs/m4c/experience-anterieur-droit';OUT=ROOT/'docs/m4c/experience-anterieurs-bilateraux'
old=np.array(Image.open(BASE/'textures/muscle-ids.png'));new=np.array(Image.open(OUT/'textures/muscle-ids.png'))
a=np.array(Image.open(BASE/'textures/deltoid.left.anterior.png'));b=np.array(Image.open(OUT/'textures/deltoid.left.anterior.png'))
changed=old!=new;assert changed.any() and np.all(np.isin(old[changed],[0,3])) and np.all(np.isin(new[changed],[0,3]))
assert np.array_equal(np.unique(new),np.arange(9)) and np.array_equal(new==3,b>=128)
spec=json.loads((OUT/'regions.json').read_text());assert spec['zones']==json.loads((BASE/'regions.json').read_text())['zones']
weights=np.zeros(new.shape,np.uint16);records=[]
for z in spec['zones']:
    file='textures/'+z['id']+'.png';im=np.array(Image.open(OUT/file));weights+=im
    assert np.array_equal(im>=128,new==z['code'])
    if z['code']!=3:
        assert (OUT/file).read_bytes()==(BASE/file).read_bytes(),z['id']
        records.append({'id':z['id'],'sha256':sha((OUT/file).read_bytes()),'byteIdentical':True})
assert weights.max()<=255,'Overlapping mask weights'
for group in range(2):
    packed=np.array(Image.open(OUT/f'textures/masks-rgba-{group}.png'))
    for channel,z in enumerate(spec['zones'][group*4:group*4+4]):assert np.array_equal(packed[:,:,channel],np.array(Image.open(OUT/'textures'/(z['id']+'.png'))))
assert (OUT/'textures/masks-rgba-1.png').read_bytes()==(BASE/'textures/masks-rgba-1.png').read_bytes()
protected=binary_dilation(old==4,iterations=4);assert np.array_equal(a[protected],b[protected])
for anterior,lateral in [(3,4),(6,7)]:
    interface=lambda ids:(ids==anterior)&binary_dilation(ids==lateral)
    assert np.array_equal(interface(old),interface(new))
reg_old=json.loads((BASE/'region-binding.json').read_text());reg_new=json.loads((OUT/'region-binding.json').read_text())
for a_zone,b_zone in zip(reg_old['zones'],reg_new['zones']):
    if a_zone['code']!=3:assert a_zone==b_zone
geometry={}
for key,folder in [('before',BASE),('after',OUT)]:
    _,doc,blob=read_glb(folder/'exports/meshy-eight-zones-control.glb');p=doc['meshes'][0]['primitives'][0]
    geometry[key]={name:accessor(doc,blob,index) for name,index in p['attributes'].items()};geometry[key]['indices']=accessor(doc,blob,p['indices'])
    for index,name in [(0,'control-basecolor.png'),(1,'muscle-ids.png')]:
        view=doc['bufferViews'][doc['images'][index]['bufferView']];at=view.get('byteOffset',0)
        assert blob[at:at+view['byteLength']]==(folder/'textures'/name).read_bytes()
for key in geometry['before']:assert geometry['before'][key].tobytes()==geometry['after'][key].tobytes(),key
source(ROOT/'assets/models/meshy-e45e5d8.glb')
files=subprocess.check_output(['git','ls-tree','-rz','--name-only','7b69e3d'],cwd=ROOT).decode().strip('\0').split('\0')
for file in files:assert (ROOT/file).read_bytes()==subprocess.check_output(['git','show',f'7b69e3d:{file}'],cwd=ROOT),file
blender=json.loads((OUT/'blender-preservation.json').read_text());assert blender['identical']
for left,right in [('reference-droite-avant','epaule-droite-validee'),('neutre-avant','neutre-complet')]:assert (OUT/'renders'/(left+'.png')).read_bytes()==(OUT/'renders'/(right+'.png')).read_bytes()
assert json.loads((OUT/'continuity-audit.json').read_text())['status']=='passed'
transfer=json.loads((OUT/'surface-transfer.json').read_text())
assert transfer['referenceMaskSha256']==sha((BASE/'textures/deltoid.right.anterior.png').read_bytes())
assert all(p['point'][0]>0 for p in transfer['newLeftCurve'])
assert all(p['point'][0]<0 for p in transfer['referenceRightCurve'])
assert transfer['maxProjectionDistanceM']<.015
report={'status':'passed','referenceCommit':'7b69e3d','editableID':3,'immutableReferenceID':6,
    'sevenOtherMasks':records,'rightMaskAndPackedAtlasByteIdentical':True,
    'bothAnteriorLateralBoundariesIdentical':True,'leftProtectedFilteringBandTexels':4,
    'eightStableIDs':[z['id'] for z in spec['zones']],
    'geometryBuffersBitIdentical':list(geometry['after']),'trianglesBefore':len(geometry['before']['indices'])//3,'trianglesAfter':len(geometry['after']['indices'])//3,
    'newTriangles':0,'maxPositionDisplacementM':0,'masterSha256':sha((ROOT/'assets/models/meshy-e45e5d8.glb').read_bytes()),
    'noOverlappingWeights':True,'continuityAudit':'passed','neutralRenderBytesIdentical':True,'rightRenderBytesIdentical':True,
    'allPreviouslyTrackedFilesByteIdentical':len(files),'actualLeftSourceSurfaceProjection':True,'uvPixelsReflected':False,
    'applicationIntegration':False,'visualApprovalLeft':False}
(OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report),flush=True)
