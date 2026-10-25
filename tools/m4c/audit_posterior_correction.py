"""Verify strict green-to-neutral scope, unchanged buffers, IDs and application."""
import hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image
from glb_io import read_glb,accessor,source,sha
root=Path(__file__).resolve().parents[2];base=root/'docs/m4c/meshy-huit-zones';out=root/'docs/m4c/meshy-deltoides-limite-inferieure'
a=np.array(Image.open(base/'textures/muscle-ids.png'));b=np.array(Image.open(out/'textures/muscle-ids.png'));changed=a!=b
assert changed.any() and np.all(np.isin(a[changed],[5,8])) and np.all(b[changed]==0)
spec=json.loads((out/'regions.json').read_text());six=[]
for z in spec['zones']:
    mask=np.array(Image.open(out/'textures'/(z['id']+'.png')));assert np.array_equal(mask,(b==z['code'])*255)
    if z['code'] not in [5,8]:
        name=z['id']+'.png';assert (base/'textures'/name).read_bytes()==(out/'textures'/name).read_bytes();six.append(z['id'])
assert np.array_equal(np.unique(a),np.unique(b)) and len(spec['zones'])==8
assert spec['zones']==json.loads((base/'regions.json').read_text())['zones']
geometry={}
for label,path in [('before',base/'exports/meshy-eight-zones-control.glb'),('after',out/'exports/meshy-eight-zones-control.glb')]:
    _,doc,binary=read_glb(path);p=doc['meshes'][0]['primitives'][0]
    geometry[label]={key:accessor(doc,binary,value) for key,value in p['attributes'].items()};geometry[label]['indices']=accessor(doc,binary,p['indices'])
assert set(geometry['before'])==set(geometry['after'])
for key in geometry['before']:assert geometry['before'][key].dtype==geometry['after'][key].dtype and geometry['before'][key].tobytes()==geometry['after'][key].tobytes(),key
source(root/'assets/models/meshy-e45e5d8.glb')
# Verify points in the actual annotated lobe from source-local ray picks.
# Actual 3D ray hits from the annotated camera, evaluated on both ID atlases.
uv=np.load(base/'source-uv-binding.npz')['uv_blender'].copy();uv[:,:,1]=1-uv[:,:,1]
_,v,n,f=source(root/'assets/models/meshy-e45e5d8.glb');probes=[]
for probe in json.loads((out/'annotated-surface-probes.json').read_text()):
    face=probe['sourceFace'];triangle=v[f[face]].astype(float);point=np.array(probe['pointGLB'])
    basis=np.column_stack([triangle[1]-triangle[0],triangle[2]-triangle[0]]);ab=np.linalg.lstsq(basis,point-triangle[0],rcond=None)[0]
    w=np.r_[1-ab.sum(),ab];assert w.min()>-1e-4
    q=w@uv[face];col,row=np.clip(np.floor(q*len(a)).astype(int),0,len(a)-1)
    code=5 if probe['side']=='left' else 8
    assert int(a[row,col])==code and int(b[row,col])==0,(probe,a[row,col],b[row,col])
    probes.append({**probe,'beforeCode':code,'afterCode':0})
existing=json.loads((base/'application-preservation.json').read_text());checks=[]
for record in existing['checkedFiles']:
    actual=sha((root/record['file']).read_bytes())
    # m4b tools and all app files remain frozen; m4c validation tools are separate.
    assert actual==record['sha256'],record['file'];checks.append(record['file'])
report={'reference_commit':'8b723d9','changed_texels':int(changed.sum()),'only_posterior_to_neutral':True,'red_blue_boundaries_unchanged':True,'six_other_mask_files_byte_identical':six,'eight_ids_preserved':True,'export_buffers_bit_identical':list(geometry['before']),'uv_and_topology_changed':False,'vertices':len(geometry['after']['POSITION']),'triangles':len(geometry['after']['indices'])//3,'protected_application_files_unchanged':len(checks),'neutralized_witnesses':probes,'source_glb_sha256':sha((root/'assets/models/meshy-e45e5d8.glb').read_bytes())}
(out/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
