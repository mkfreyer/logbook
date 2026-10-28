"""Independent approved-source and optional runtime checks, without UI changes."""
import argparse,base64,io,json,re,subprocess
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation
from glb_io import sha,source,read_glb,accessor
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/m4c/meshy-anterieurs-valides'
p=argparse.ArgumentParser();p.add_argument('--runtime',type=Path);args=p.parse_args()
def gitfile(commit,path):return subprocess.check_output(['git','show',f'{commit}:{path}'],cwd=ROOT)
def png(data):return np.array(Image.open(io.BytesIO(data)))
old=np.array(Image.open(ROOT/'docs/m4c/meshy-posterieurs-harmonises/textures/muscle-ids.png'))
new=np.array(Image.open(OUT/'textures/muscle-ids.png'));spec=json.loads((OUT/'regions.json').read_text())
approved='docs/m4c/experience-anterieurs-bilateraux/';ref='09c61ab'
assert (OUT/'textures/muscle-ids.png').read_bytes()==gitfile(ref,approved+'textures/muscle-ids.png')
assert np.array_equal(np.unique(new),np.arange(9))
assert np.all(np.isin(old[new!=old],[0,3,6])) and np.all(np.isin(new[new!=old],[0,3,6]))
weights=np.zeros(new.shape,np.uint16);records=[]
for z in spec['zones']:
    file='textures/'+z['id']+'.png';data=(OUT/file).read_bytes();mask=png(data);weights+=mask
    assert data==gitfile(ref,approved+file),file
    if z['code'] not in [3,6]:assert data==gitfile('06fa665','docs/m4c/meshy-posterieurs-harmonises/'+file)
    assert np.array_equal(mask>=128,new==z['code'])
    records.append({'id':z['id'],'code':z['code'],'sha256':sha(data),'approved09c61abByteIdentical':True,'protected06fa665ByteIdentical':z['code'] not in [3,6]})
assert weights.max()<=255
for group in range(2):
    pack=np.array(Image.open(OUT/f'textures/masks-rgba-{group}.png'))
    for channel,z in enumerate(spec['zones'][group*4:group*4+4]):assert np.array_equal(pack[:,:,channel],np.array(Image.open(OUT/'textures'/(z['id']+'.png'))))
for anterior,lateral in [(3,4),(6,7)]:
    a=np.array(Image.open(ROOT/'docs/m4c/meshy-posterieurs-harmonises/textures'/('deltoid.'+('left' if anterior==3 else 'right')+'.anterior.png')))
    b=np.array(Image.open(OUT/'textures'/('deltoid.'+('left' if anterior==3 else 'right')+'.anterior.png')))
    band=binary_dilation(old==lateral,iterations=4);assert np.array_equal(a[band],b[band])
    assert np.array_equal((old==anterior)&binary_dilation(old==lateral),(new==anterior)&binary_dilation(new==lateral))
assert (OUT/'meshy-anterieurs-valides.blend').read_bytes()==gitfile(ref,approved+'experience-anterieurs-bilateraux.blend')
assert (OUT/'exports/meshy-eight-zones-control.glb').read_bytes()==gitfile(ref,approved+'exports/meshy-eight-zones-control.glb')
geometry={};docs={}
for name,folder in [('old',ROOT/'docs/m4c/meshy-posterieurs-harmonises'),('approved',OUT)]:
    _,doc,binary=read_glb(folder/'exports/meshy-eight-zones-control.glb');q=doc['meshes'][0]['primitives'][0];docs[name]=doc
    geometry[name]={k:accessor(doc,binary,i) for k,i in q['attributes'].items()};geometry[name]['indices']=accessor(doc,binary,q['indices'])
for key in geometry['old']:assert geometry['old'][key].tobytes()==geometry['approved'][key].tobytes()
source(ROOT/'assets/models/meshy-e45e5d8.glb')
assert json.loads((OUT/'continuity-audit.json').read_text())['status']=='passed'
assert json.loads((OUT/'picking-audit.json').read_text())['status']=='passed'
baseline='fd737ca' if args.runtime else '168ac61'
protected_paths=['app','src','assets','tests','package.json','package-lock.json','app.json','app.config.ts','babel.config.js','tsconfig.json']
files=subprocess.check_output(['git','ls-tree','-rz','--name-only',baseline,*protected_paths],cwd=ROOT).decode().strip('\0').split('\0')
allowed={'assets/models/meshy-m4d-uv.glb','src/features/model3d/generated/selectionData.ts','src/features/model3d/generated/viewerBundle.ts','tests/muscle-selection.test.ts'} if args.runtime else set()
for file in files:
    if file not in allowed:assert (ROOT/file).read_bytes()==gitfile(baseline,file),file
report={'status':'passed','approvedReference':'09c61ab','anatomicalBase':'06fa665','eightMasks':records,
    'sixProtectedMasksByteIdentical':True,'bothAnteriorLateralBoundariesAnd4pxBandsIdentical':True,
    'atlasByteIdenticalToApproval':True,'noOverlappingWeights':True,'continuity':'passed',
    'blenderAndControlGlbByteIdenticalToApproval':True,'geometryUvNormalsIndicesBitIdentical':list(geometry['approved']),
    'triangles':len(geometry['approved']['indices'])//3,'newTriangles':0,'maxVertexDisplacementM':0,
    'masterSha256':sha((ROOT/'assets/models/meshy-e45e5d8.glb').read_bytes()),
    'protectedApplicationFilesCompared':len(files)-len(allowed),'applicationBaseline':baseline,
    'rejectedContoursUsed':False}
if args.runtime:
    _,doc,binary=read_glb(ROOT/'assets/models/meshy-m4d-uv.glb');q=doc['meshes'][0]['primitives'][0]
    actual={k:accessor(doc,binary,i) for k,i in q['attributes'].items()};actual['indices']=accessor(doc,binary,q['indices'])
    for key in actual:assert actual[key].tobytes()==geometry['approved'][key].tobytes()
    _,original,_=read_glb(ROOT/'assets/models/meshy-e45e5d8.glb')
    assert doc['materials']==original['materials'] and 'images' not in doc and 'textures' not in doc
    text=(ROOT/'src/features/model3d/generated/selectionData.ts').read_text()
    atlas=base64.b64decode(json.loads(re.search(r'muscleAtlasBase64 = (".*");',text)[1]))
    assert atlas==(OUT/'textures/muscle-ids.png').read_bytes()
    report['runtime']={'neutralMasterMaterialExact':True,'controlImagesOrMaterialsEmbedded':False,'runtimeAtlasByteIdenticalTo09c61ab':True,
        'runtimeGeometryUvNormalsExact':True,'assetSha256':sha((ROOT/'assets/models/meshy-m4d-uv.glb').read_bytes()),'atlasSha256':sha(atlas)}
dest=ROOT/args.runtime if args.runtime else OUT/'verification.json';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('APPROVED_ANTERIOR_AUDIT_PASSED',len(records),'MASKS;',report.get('runtime',{}),flush=True)
