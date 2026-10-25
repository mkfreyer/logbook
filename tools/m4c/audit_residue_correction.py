"""Independent binary preservation and ID/weight checks for the local residue."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from glb_io import source,read_glb,accessor,sha
root=Path(__file__).resolve().parents[2];base=root/'docs/m4c/meshy-deltoides-limite-inferieure';out=root/'docs/m4c/meshy-deltoides-residu-local'
a=np.array(Image.open(base/'textures/muscle-ids.png'));b=np.array(Image.open(out/'textures/muscle-ids.png'));changed=a!=b
assert changed.any() and np.all(a[changed]==8) and np.all(b[changed]==0)
spec=json.loads((out/'regions.json').read_text());assert spec['zones']==json.loads((base/'regions.json').read_text())['zones']
unchanged=[]
for zone in spec['zones']:
    name=zone['id']+'.png';mask=np.array(Image.open(out/'textures'/name));assert np.array_equal(mask,(b==zone['code'])*255)
    if zone['code']!=8:assert (out/'textures'/name).read_bytes()==(base/'textures'/name).read_bytes();unchanged.append(zone['id'])
assert (out/'textures/masks-rgba-0.png').read_bytes()==(base/'textures/masks-rgba-0.png').read_bytes()
old=np.array(Image.open(base/'textures/masks-rgba-1.png'));new=np.array(Image.open(out/'textures/masks-rgba-1.png'));assert np.array_equal(old[:,:,:3],new[:,:,:3]) and np.array_equal(new[:,:,3],(b==8)*255)
geometry={}
for name,p in [('before',base),('after',out)]:
    _,doc,bin=read_glb(p/'exports/meshy-eight-zones-control.glb');prim=doc['meshes'][0]['primitives'][0];geometry[name]={key:accessor(doc,bin,index) for key,index in prim['attributes'].items()};geometry[name]['indices']=accessor(doc,bin,prim['indices'])
for key in geometry['before']:assert geometry['before'][key].dtype==geometry['after'][key].dtype and geometry['before'][key].tobytes()==geometry['after'][key].tobytes()
source(root/'assets/models/meshy-e45e5d8.glb')
preservation=json.loads((root/'docs/m4c/meshy-huit-zones/application-preservation.json').read_text())
for item in preservation['checkedFiles']:assert sha((root/item['file']).read_bytes())==item['sha256'],item['file']
probes=json.loads((out/'cause-and-probes.json').read_text())['probes']
assert sum(p['role']=='remove' and p['beforeId']==8 and p['afterId']==0 and p['beforeBilinearGreenWeight']>.99 and p['afterBilinearGreenWeight']<.001 for p in probes)==3
assert all(p['beforeId']==p['afterId'] for p in probes if p['role']!='remove')
report={'baselineCommit':'71f70dc','onlyIDTransition':[8,0],'changedTexels':int(changed.sum()),'sevenUnchangedMasks':unchanged,'packedOtherChannelsBitIdentical':True,'geometryBuffersBitIdentical':list(geometry['after']),'topologyUVAndNormalsUnchanged':True,'triangles':len(geometry['after']['indices'])//3,'exportVertices':len(geometry['after']['POSITION']),'protectedApplicationFilesUnchanged':len(preservation['checkedFiles']),'defectIsPresentInSourceIDAndFullWeightBefore':True,'removedProbeCount':3,'preservedProbeCount':sum(p['role']!='remove' for p in probes),'sourceGlbSha256':sha((root/'assets/models/meshy-e45e5d8.glb').read_bytes())}
(out/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
