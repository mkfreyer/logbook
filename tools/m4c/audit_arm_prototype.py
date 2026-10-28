"""Two UV atlases, one unchanged surface. Independent protection/continuity audit."""
import argparse,json,subprocess,sys
from pathlib import Path
import numpy as np
from PIL import Image
from glb_io import source,sha
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'docs/m4c/meshy-anterieurs-valides';OUT=ROOT/'docs/m4c/meshy-bras-prototype';CACHE=ROOT.parent/'m4c-bras-cache'
p=argparse.ArgumentParser();p.add_argument('--final',action='store_true');args=p.parse_args()
oldspec=json.loads((BASE/'regions.json').read_text());newspec=json.loads((OUT/'regions.json').read_text())
records=[]
for z in oldspec['zones']:
    name='textures/'+z['id']+'.png';assert (OUT/name).read_bytes()==(BASE/name).read_bytes(),name
    records.append({'id':z['id'],'code':z['code'],'sha256':sha((OUT/name).read_bytes()),'byteIdenticalToD552e23':True})
for file in ['masks-rgba-0.png','masks-rgba-1.png','muscle-ids.png']:assert (OUT/'textures'/file).read_bytes()==(BASE/'textures'/file).read_bytes()
registry=json.loads((OUT/'registry-twelve.json').read_text())['zones']
assert len({z['code'] for z in registry})==len({z['id'] for z in registry})==12
assert [z['code'] for z in registry]==list(range(1,13))
for a,b in zip(oldspec['zones'],registry[:8]):
    for key in ['id','code','name','color']:assert a[key]==b[key]
newids=np.array(Image.open(OUT/'textures/muscle-ids-arms.png'))
assert np.array_equal(np.unique(newids),np.array([0,9,10,11,12]))
pack=np.array(Image.open(OUT/'textures/masks-rgba-arms.png'))
for i,z in enumerate(newspec['zones']):
    alpha=np.array(Image.open(OUT/'textures'/(z['id']+'.png')))
    assert np.array_equal(alpha,pack[:,:,i]) and np.array_equal(alpha>=128,newids==z['code'])
assert not np.any((pack>0).sum(2)>1)
# Reuse the existing checker without changing its fixed single-atlas input.
for role,spec,binding,coverage,ids in [
    ('existing',oldspec,ROOT/'docs/m4c/meshy-huit-zones/source-uv-binding.npz',ROOT/'docs/m4c/meshy-huit-zones/textures/uv-covered-pixels.png',OUT/'textures/muscle-ids.png'),
    ('arms',newspec,OUT/'arms-uv-binding.npz',OUT/'textures/uv-covered-pixels.png',OUT/'textures/muscle-ids-arms.png')]:
    tmp=CACHE/('continuity-'+role);(tmp/'textures').mkdir(parents=True,exist_ok=True)
    spec=dict(spec,uvSource=str(binding),coverageSource=str(coverage))
    (tmp/'regions.json').write_text(json.dumps(spec));(tmp/'textures/muscle-ids.png').write_bytes(ids.read_bytes())
    result=subprocess.run([sys.executable,str(ROOT/'tools/m4c/audit_continuity.py'),'--asset-dir',str(tmp)],capture_output=True,text=True,cwd=ROOT)
    report=json.loads((tmp/'continuity-audit.json').read_text());(OUT/f'continuity-{role}.json').write_text(json.dumps(report,indent=2)+'\n')
    assert result.returncode==0,(role,'Surface mask discontinuity; inspect report')
_,v,n,f=source(ROOT/'assets/models/meshy-e45e5d8.glb')
uv0=np.load(ROOT/'docs/m4c/meshy-huit-zones/source-uv-binding.npz')['uv_blender'].copy();uv0[:,:,1]=1-uv0[:,:,1]
binding=np.load(OUT/'arms-uv-binding.npz');uv1=binding['uv_blender'].copy();uv1[:,:,1]=1-uv1[:,:,1]
oldweights=np.stack([np.array(Image.open(BASE/'textures'/(z['id']+'.png'))) for z in oldspec['zones']]).astype(float).sum(0)
def sample(image,uv):
    q=np.clip(uv*2048-.5,0,2047);i=q.astype(int);a=q-i;x,y=i.T;u,w=a.T;xx=np.minimum(x+1,2047);yy=np.minimum(y+1,2047)
    return image[y,x]*(1-u)*(1-w)+image[y,xx]*u*(1-w)+image[yy,x]*(1-u)*w+image[yy,xx]*u*w
active_surface_samples=0;cross_overlap=0;new_new_overlap=0;witnesses=[]
arm_faces=np.flatnonzero(binding['domain'])
# Dense barycentric points on the actual triangles, independent of UV pixel
# centers used for painting. Includes near-edge samples across every UV seam.
for a in np.linspace(.001,.998,13):
    for b in np.linspace(.001,.998-a,13):
        if a+b>=1:continue
        bary=np.array([1-a-b,a,b]);q1=np.einsum('c,fck->fk',bary,uv1[arm_faces]);q0=np.einsum('c,fck->fk',bary,uv0[arm_faces])
        colors=np.column_stack([sample(pack[:,:,i].astype(float),q1) for i in range(4)])
        newweight=colors.sum(1);active=newweight>.01;old=sample(oldweights,q0)
        cross_overlap+=int(np.sum(active&(old>.01)));new_new_overlap+=int(np.sum((colors>.01).sum(1)>1));active_surface_samples+=int(active.sum())
        for i,z in enumerate(newspec['zones']):
            if any(w['expectedId']==z['id'] for w in witnesses):continue
            eligible=(colors[:,i]>254.99)&(old==0)
            pts=np.einsum('c,fck->fk',bary,v[f[arm_faces]])
            if eligible.any():
                target=np.array([(.25 if z['id'].endswith('left') else -.25),.38,(-.13 if z['id'].startswith('triceps') else .005)])
                candidates=np.flatnonzero(eligible);k=candidates[np.argmin(np.linalg.norm(pts[candidates]-target,axis=1))];face=int(arm_faces[k]);normal=bary@n[f[face]]
                witnesses.append({'expectedId':z['id'],'code':z['code'],'faceIndex':face,'point':pts[k].tolist(),'normal':normal.tolist(),'barycentric':bary.tolist(),'uv0':q0[k].tolist(),'uv1':q1[k].tolist()})
assert cross_overlap==new_new_overlap==0,(cross_overlap,new_new_overlap)
assert len(witnesses)==4
witnesses.sort(key=lambda w:w['code']);(OUT/'picking-witnesses.json').write_text(json.dumps(witnesses,indent=2)+'\n')
assert json.loads((OUT/'uv1-repair.json').read_text())['remainingDistinctSurfaceUVOverlaps']==0
files=subprocess.check_output(['git','ls-tree','-rz','--name-only','d552e23'],cwd=ROOT).decode().strip('\0').split('\0')
for file in files:assert (ROOT/file).read_bytes()==subprocess.check_output(['git','show',f'd552e23:{file}'],cwd=ROOT),file
report={'status':'passed','baseCommit':'d552e23','eightApprovedMasks':records,'originalPackedAtlasesByteIdentical':True,
    'stableCodes':list(range(1,13)),'oldUvSet':0,'newUvSet':1,'uvPixelsMirrored':False,
    'newMaskSurfaceComponents':'one per zone; stitched across real UV seams','existingMaskComponents':'one per zone; unchanged',
    'activeIndependentSurfaceSamples':active_surface_samples,'sampledNewVsExistingOverlap':cross_overlap,'sampledNewVsNewOverlap':new_new_overlap,
    'sampleGrid':'13x13 barycentric samples on every UV1-supported source triangle, including near-edge samples',
    'triangles':len(f),'newTriangles':0,'sourceMasterSha256':sha((ROOT/'assets/models/meshy-e45e5d8.glb').read_bytes()),
    'allPreviouslyTrackedFilesByteIdentical':len(files),'applicationIntegration':False,'fourNewMasksAwaitingUserApproval':True}
if args.final:
    preservation=json.loads((OUT/'blender-preservation.json').read_text());assert preservation['identical']
    assert (OUT/'renders/reference-neutre.png').read_bytes()==(OUT/'renders/neutre-complet.png').read_bytes()
    assert json.loads((OUT/'picking-audit.json').read_text())['status']=='passed'
    report.update(blenderGeometryNormalsUV0BitIdentical=True,neutralRenderBytesIdentical=True,maxVertexDisplacementM=0,fourRealSurfaceRaycasts='passed')
(OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('ARM_PROTOTYPE_AUDIT_PASSED',active_surface_samples,'SAMPLES; ALL',len(files),'BASE FILES EXACT',flush=True)
