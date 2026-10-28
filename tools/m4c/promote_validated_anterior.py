"""Promote only the approved 09c61ab source, preserving all previous versions."""
import json,subprocess
from pathlib import Path
import numpy as np
from PIL import Image
from glb_io import sha,read_glb,accessor,source
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/m4c/meshy-anterieurs-valides'
REF='09c61ab937464f47133ece32944c568311583545';PREFIX='docs/m4c/experience-anterieurs-bilateraux/'
def gitfile(commit,file):return subprocess.check_output(['git','show',f'{commit}:{file}'],cwd=ROOT)
def dump(file,data):(OUT/file).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
spec=json.loads(gitfile(REF,PREFIX+'regions.json'))
files={f'textures/{z["id"]}.png':f'textures/{z["id"]}.png' for z in spec['zones']}
files.update({f:f for f in ['textures/control-basecolor.png','exports/meshy-eight-zones-control.glb',
    'region-binding.json','picking-witnesses.json','surface-transfer.json','contour-comparison.json']})
files.update({'meshy-anterieurs-valides.blend':'experience-anterieurs-bilateraux.blend',
    'renders/face-bilaterale.png':'renders/face-bilaterale.png',
    'renders/epaule-droite-validee.png':'renders/epaule-droite-validee.png',
    'renders/epaule-gauche-validee.png':'renders/epaule-gauche-nouvelle.png'})
records=[]
for dest,src in files.items():
    data=gitfile(REF,PREFIX+src);file=OUT/dest;file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(data)
    records.append({'file':dest,'source':PREFIX+src,'sha256':sha(data),'byteIdentical':True})
masks=[np.array(Image.open(OUT/'textures'/(z['id']+'.png'))) for z in spec['zones']]
weights=np.stack(masks).astype(np.uint16);assert weights.sum(0).max()<=255
ids=np.zeros((2048,2048),np.uint8)
for z,mask in zip(spec['zones'],masks):ids[mask>=128]=z['code']
derived={'textures/muscle-ids.png':ids,
    'textures/masks-rgba-0.png':np.stack(masks[:4],axis=2),
    'textures/masks-rgba-1.png':np.stack(masks[4:],axis=2)}
for file,array in derived.items():
    Image.fromarray(array).save(OUT/file)
    expected=gitfile(REF,PREFIX+file);assert (OUT/file).read_bytes()==expected,file
    records.append({'file':file,'source':PREFIX+file,'sha256':sha(expected),'byteIdentical':True,'regeneratedFromEightApprovedMasks':True})
protected=[]
for z in spec['zones']:
    file='textures/'+z['id']+'.png'
    if z['code'] not in [3,6]:
        assert (OUT/file).read_bytes()==gitfile('06fa665','docs/m4c/meshy-posterieurs-harmonises/'+file)
        protected.append(z['id'])
_,doc,blob=read_glb(OUT/'exports/meshy-eight-zones-control.glb')
for index,file in [(0,'textures/control-basecolor.png'),(1,'textures/muscle-ids.png')]:
    view=doc['bufferViews'][doc['images'][index]['bufferView']];at=view.get('byteOffset',0)
    assert blob[at:at+view['byteLength']]==(OUT/file).read_bytes()
source(ROOT/'assets/models/meshy-e45e5d8.glb')
spec['status']='user-approved-bilateral-anterior-09c61ab-official-m4c-reference'
spec['approval']={'commit':REF,'userValidatedBothAnteriorContours':True,'immutableProtectedMasks':protected,
    'sourceBlenderAndControlGlbCopiedExactly':True,'source':'PR #19; approved by user before promotion to PR #17'}
dump('regions.json',spec)
dump('provenance.json',{'referenceCommit':REF,'anatomicalBase':'06fa665','sourcePrefix':PREFIX,
    'sourceFiles':records,'sixProtectedMasksByteIdenticalTo06fa665':protected,
    'regeneratedAtlasesByteIdenticalToApprovedReference':True,
    'modelMasterSha256':sha((ROOT/'assets/models/meshy-e45e5d8.glb').read_bytes()),
    'geometryEdited':False,'uvEdited':False,'rejectedSourcesUsed':False})
print('PROMOTED_APPROVED_ANTERIORS',len(records),'FILES; SIX PROTECTED MASKS EXACT; ATLASES REGENERATED EXACT',flush=True)
