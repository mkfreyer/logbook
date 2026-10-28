"""Independent preservation, geometry, texture and surface-join checks for ID5."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation
from glb_io import source,read_glb,accessor,sha
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/m4c/meshy-posterieur-droit-bord-inferieur'
OUT=ROOT/'docs/m4c/meshy-posterieurs-harmonises'
old=np.array(Image.open(BASE/'textures/muscle-ids.png'));new=np.array(Image.open(OUT/'textures/muscle-ids.png'))
a=np.array(Image.open(BASE/'textures/deltoid.left.posterior.png'));b=np.array(Image.open(OUT/'textures/deltoid.left.posterior.png'))
changed=old!=new
assert changed.any() and np.all(np.isin(old[changed],[0,5])) and np.all(np.isin(new[changed],[0,5]))
assert np.array_equal(new==5,b>=128)
spec=json.loads((OUT/'regions.json').read_text());assert spec['zones']==json.loads((BASE/'regions.json').read_text())['zones']
other=np.zeros(old.shape,np.uint8)
for z in spec['zones']:
    if z['code']!=5:
        name=z['id']+'.png';assert (OUT/'textures'/name).read_bytes()==(BASE/'textures'/name).read_bytes(),name
        other=np.maximum(other,np.array(Image.open(BASE/'textures'/name)))
        assert np.array_equal(old==z['code'],new==z['code'])
assert not np.any(b[other>0])
assert (OUT/'textures/masks-rgba-0.png').read_bytes()==(BASE/'textures/masks-rgba-0.png').read_bytes()
pa=np.array(Image.open(BASE/'textures/masks-rgba-1.png'));pb=np.array(Image.open(OUT/'textures/masks-rgba-1.png'))
assert np.array_equal(pa[:,:,1:],pb[:,:,1:]) and np.array_equal(pb[:,:,0],b)
samples=np.load(OUT/'left-surface-samples.npz');protected=samples['protectedJoin']
y,x=samples['y'][protected],samples['x'][protected];assert np.array_equal(a[y,x],b[y,x])
adjacent=(old==5)&binary_dilation(old==4,iterations=2)
assert np.array_equal(a[adjacent],b[adjacent])
geometry={}
for state,folder in [('before',BASE),('after',OUT)]:
    _,doc,binary=read_glb(folder/'exports/meshy-eight-zones-control.glb');p=doc['meshes'][0]['primitives'][0]
    geometry[state]={key:accessor(doc,binary,i) for key,i in p['attributes'].items()};geometry[state]['indices']=accessor(doc,binary,p['indices'])
    for index,name in [(0,'control-basecolor.png'),(1,'muscle-ids.png')]:
        view=doc['bufferViews'][doc['images'][index]['bufferView']];start=view.get('byteOffset',0)
        assert binary[start:start+view['byteLength']]==(folder/'textures'/name).read_bytes()
for key in geometry['before']:
    assert geometry['before'][key].dtype==geometry['after'][key].dtype
    assert geometry['before'][key].tobytes()==geometry['after'][key].tobytes(),key
source(ROOT/'assets/models/meshy-e45e5d8.glb')
manifest=json.loads((ROOT/'docs/m4c/meshy-huit-zones/application-preservation.json').read_text())
for entry in manifest['checkedFiles']:assert sha((ROOT/entry['file']).read_bytes())==entry['sha256'],entry['file']
probes=json.loads((OUT/'projected-outline.json').read_text())['probes']
for p in probes:
    xx,yy=np.clip((np.array(p['uv'])*len(old)).astype(int),0,len(old)-1)
    p.update(beforeId=int(old[yy,xx]),afterId=int(new[yy,xx]))
(OUT/'probe-verification.json').write_text(json.dumps(probes,indent=2)+'\n')
report={'referenceCommit':'977f68a','onlyEditableID':5,'immutableReferenceID':8,
    'addedID5Texels':int(((old==0)&(new==5)).sum()),'removedID5Texels':int(((old==5)&(new==0)).sum()),
    'rightAndSixOtherMasksByteIdentical':True,'rightPackedGBAChannelsBitIdentical':True,
    'leftGreenBlueJoinUnchanged':True,'protectedJoinTexels':int(protected.sum()),
    'noOtherCoverageOverlapped':True,'geometryBuffersBitIdentical':list(geometry['after']),
    'embeddedGLBImagesMatchSourcePNG':True,'triangles':len(geometry['after']['indices'])//3,
    'exportVertices':len(geometry['after']['POSITION']),
    'protectedApplicationFilesUnchanged':len(manifest['checkedFiles']),
    'eightStableIDs':[z['id'] for z in spec['zones']],
    'sourceGlbSha256':sha((ROOT/'assets/models/meshy-e45e5d8.glb').read_bytes())}
(OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
