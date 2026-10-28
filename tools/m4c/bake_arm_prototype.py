"""Intrinsic arm regions on UV1, eight frozen masks on UV0. No mesh edits."""
import json,shutil
from pathlib import Path
import numpy as np
from PIL import Image
from matplotlib.path import Path as Polygon
from scipy.ndimage import distance_transform_edt,label,binary_fill_holes
from scipy.spatial import cKDTree
from glb_io import source,sha
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'docs/m4c/meshy-anterieurs-valides';OUT=ROOT/'docs/m4c/meshy-bras-prototype';SIZE=2048
_,vertices,normals,faces=source(ROOT/'assets/models/meshy-e45e5d8.glb')
original=np.load(ROOT/'docs/m4c/meshy-huit-zones/source-uv-binding.npz');uv0=original['uv_blender'].copy();uv0[:,:,1]=1-uv0[:,:,1]
binding=np.load(OUT/'arms-uv-binding.npz');uv1b=binding['uv_blender'].copy();domain=binding['domain']
def raster(uv,selected,need_uv=False):
    world=np.zeros((SIZE,SIZE,3),np.float32);owner=np.full((SIZE,SIZE),-1,np.int32)
    olduv=np.zeros((SIZE,SIZE,2),np.float32) if need_uv else None;repairs=set();collisions=0
    for face in np.flatnonzero(selected):
        t=uv[face].astype(float)*SIZE-.5;lo=np.maximum(np.ceil(t.min(0)).astype(int),0);hi=np.minimum(np.floor(t.max(0)).astype(int),SIZE-1)
        if np.any(hi<lo):continue
        xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1));p=np.column_stack([xx.ravel(),yy.ravel()])
        matrix=np.column_stack([t[1]-t[0],t[2]-t[0]])
        if abs(np.linalg.det(matrix))<1e-12:continue
        ab=(p-t[0])@np.linalg.inv(matrix).T;bary=np.column_stack([1-ab.sum(1),ab]);inside=(bary>=-1e-8).all(1);p,bary=p[inside],bary[inside]
        if len(p):
            x,y=p.T;position=bary@vertices[faces[face]];occupied=owner[y,x]>=0
            if occupied.any():
                bad=np.linalg.norm(position[occupied]-world[y[occupied],x[occupied]],axis=1)>1e-6
                if bad.any():repairs.add(int(face));collisions+=int(bad.sum())
            world[y,x]=position;owner[y,x]=face
            if need_uv:olduv[y,x]=bary@uv0[face]
    return world,owner,olduv,repairs,collisions
def gltf(uv):
    result=uv.copy();result[:,:,1]=1-result[:,:,1];return result
world,owner,oldcoords,repairs,count=raster(gltf(uv1b),domain,True)
repair_records=[]
if repairs:
    for slot,face in enumerate(sorted(repairs)):
        p=vertices[faces[face]].astype(float);a=p[1]-p[0];b=p[2]-p[0];length=np.linalg.norm(a)
        local=np.array([[0,0],[length,0],[b@a/length,np.linalg.norm(np.cross(a,b))/length]])
        local*=18/max(local.max(),1e-12);new=(local+np.array([8+28*slot,8]))/SIZE
        repair_records.append({'sourceFace':face,'oldUV1':uv1b[face].tolist(),'newUV1':new.tolist()});uv1b[face]=new
    world,owner,oldcoords,remaining,count=raster(gltf(uv1b),domain,True);assert not remaining and count==0
    np.savez_compressed(OUT/'arms-uv-binding.npz',uv_blender=uv1b,domain=domain)
(OUT/'uv1-repair.json').write_text(json.dumps({'onlyUV1Changed':True,'geometryChanged':False,'uv0Changed':False,'remainingDistinctSurfaceUVOverlaps':count,'repairedFaces':repair_records},indent=2)+'\n')
spec_old=json.loads((BASE/'regions.json').read_text());oldweights=np.stack([np.array(Image.open(BASE/'textures'/(z['id']+'.png'))) for z in spec_old['zones']]).astype(np.uint16)
protected_sum=oldweights.sum(0)
oldworld,oldowner,_,_,oldcollisions=raster(uv0,original['domain']);assert oldcollisions==0
protected_points=oldworld[(oldowner>=0)&(protected_sum>0)]
tree_old=cKDTree(protected_points);del oldworld,oldowner
covered=owner>=0;dist,nearest=distance_transform_edt(~covered,return_indices=True)
y,x=np.where(covered|(dist<=4));ny,nx=nearest[:,y,x];points=world[ny,nx].astype(float);oldtex=oldcoords[ny,nx]
foot=np.zeros((len(y),3,2),np.float32);uv1=gltf(uv1b);faceids=owner[ny,nx]
for face in np.unique(faceids):
    selected=faceids==face;t=uv1[face].astype(float)*SIZE-.5
    foot[selected]=np.column_stack([vertices[faces[face]][1]-vertices[faces[face]][0],vertices[faces[face]][2]-vertices[faces[face]][0]])@np.linalg.inv(np.column_stack([t[1]-t[0],t[2]-t[0]]))
# Extend the triangle-linear surface field into padding only. No surface moves.
points+=np.einsum('nij,nj->ni',foot,np.column_stack([x-nx,y-ny]))
aa=np.maximum(.00005,.5*np.linalg.norm(foot,axis=1).sum(1))
def sample(image,uv):
    q=np.clip(uv*SIZE-.5,0,SIZE-1);i=q.astype(int);a=q-i;x0,y0=i.T;u,v=a.T;x1=np.minimum(x0+1,SIZE-1);y1=np.minimum(y0+1,SIZE-1)
    return image[y0,x0]*(1-u)*(1-v)+image[y0,x1]*u*(1-v)+image[y1,x0]*(1-u)*v+image[y1,x1]*u*v
old_at_points=sample(protected_sum,oldtex)
oldids=np.array(Image.open(BASE/'textures/muscle-ids.png'));q=np.clip((oldtex*SIZE).astype(int),0,SIZE-1);old_codes=oldids[q[:,1],q[:,0]]
guides=json.loads((OUT/'surface-guides.json').read_text());alphas=[];conflicts=[]
for z in guides['zones']:
    delta=points-z['root'];axis=np.array(z['axis']);s=delta@axis;radial=delta-s[:,None]*axis
    f=radial@z['front']*(-1 if z['posterior'] else 1);l=radial@z['lateral'];theta=np.arctan2(l,f)
    param=np.column_stack([theta*z['angularScaleM'],s]);poly=np.array([p['parameter'] for p in z['surfaceCurve']])
    roi=np.all((param>=poly.min(0)-aa.max())&(param<=poly.max(0)+aa.max()),axis=1)
    inside=Polygon(poly,closed=True).contains_points(param[roi]);distance=cKDTree(poly).query(param[roi])[0];signed=np.where(inside,distance,-distance)
    target=np.zeros(len(y));target[roi]=np.clip(signed/aa[roi]+.5,0,1)
    sign=1 if z['id'].endswith('left') else -1
    target[(points[:,0]*sign<.18)|(np.linalg.norm(radial,axis=1)>.105)]=0
    active=target>0;distance_old=np.full(len(y),1.,float);distance_old[active]=tree_old.query(points[active])[0]
    fade=np.clip((distance_old-.0015)/.001,0,1);fade=fade*fade*(3-2*fade)
    candidate=target>=.5;blocked=candidate&((old_at_points>0)|(distance_old<.0015))
    conflicts.append({'id':z['id'],'candidateCoveredTexels':int((candidate&covered[y,x]).sum()),
        'clippedCoveredTexels':int((blocked&covered[y,x]).sum()),'protectedIDsEncountered':{str(code):int(np.sum(blocked&covered[y,x]&(old_codes==code))) for code in range(1,9) if np.any(blocked&covered[y,x]&(old_codes==code))},
        'neutralSafetyMarginM':.0015,'fadeToFullAtM':.0025})
    target*=fade;target[old_at_points>0]=0
    alpha=np.zeros((SIZE,SIZE),np.uint8);alpha[y,x]=np.rint(target*255).astype(np.uint8)
    # Remove only tiny added padding fragments; do not erase real surface parts.
    parts,_=label(alpha>=128);counts=np.bincount(parts.ravel())
    for part in np.flatnonzero((counts>0)&(counts<=32)):
        if part and not np.any((parts==part)&covered):alpha[parts==part]=0
    alphas.append(alpha);print('BAKED',z['id'],int((alpha>=128).sum()),flush=True)
weights=np.stack(alphas).astype(np.uint16)
assert not np.any((weights>0).sum(0)>1),'New masks overlap; inspect surface guides'
ids=np.zeros((SIZE,SIZE),np.uint8)
for z,alpha in zip(guides['zones'],alphas):
    Image.fromarray(alpha).save(OUT/'textures'/(z['id']+'.png'));ids[alpha>=128]=z['code']
Image.fromarray(ids).save(OUT/'textures/muscle-ids-arms.png');Image.fromarray(np.stack(alphas,axis=2)).save(OUT/'textures/masks-rgba-arms.png')
Image.fromarray(covered.astype(np.uint8)*255).save(OUT/'textures/uv-covered-pixels.png')
for z in spec_old['zones']:
    file=z['id']+'.png';shutil.copyfile(BASE/'textures'/file,OUT/'textures'/file)
for file in ['masks-rgba-0.png','masks-rgba-1.png','muscle-ids.png']:shutil.copyfile(BASE/'textures'/file,OUT/'textures'/file)
zones=[{k:z[k] for k in ['id','code','name','uvSet','atlas','channel']} for z in guides['zones']]
regions={'schemaVersion':2,'status':'experimental-four-arm-zones-awaiting-user-validation','sourceCommit':'d552e23','sourceMasterSha256':sha((ROOT/'assets/models/meshy-e45e5d8.glb').read_bytes()),
    'uvSource':'arms-uv-binding.npz','coverageSource':'textures/uv-covered-pixels.png','atlas':{'file':'textures/muscle-ids-arms.png','width':2048,'height':2048,'uvSet':1,'format':'L8','neutralCode':0,'sampling':'nearest; no mipmaps'},'zones':zones,
    'protectedAtlas':{'file':'textures/muscle-ids.png','uvSet':0,'codes':list(range(1,9))},'applicationIntegration':False}
(OUT/'regions.json').write_text(json.dumps(regions,ensure_ascii=False,indent=2)+'\n')
registry=[dict(z,uvSet=0,atlas='textures/muscle-ids.png') for z in spec_old['zones']]+zones
assert len({z['id'] for z in registry})==len({z['code'] for z in registry})==12
(OUT/'registry-twelve.json').write_text(json.dumps({'schemaVersion':2,'zones':registry,'status':'8 approved, 4 experimental; no viewer integration'},ensure_ascii=False,indent=2)+'\n')
(OUT/'conflicts.json').write_text(json.dumps({'existingEightMasksModified':False,'policy':'Do not paint any protected weight; add 1.5mm neutral safety margin on actual surface. Counts are atlas samples, not physical areas.','zones':conflicts},ensure_ascii=False,indent=2)+'\n')
active=(weights>0).any(0)[y,x]
np.savez_compressed(OUT/'arms-surface-samples.npz',y=y[active],x=x[active],point=points[active].astype(np.float32),covered=covered[y[active],x[active]],oldUv=oldtex[active],oldWeight=old_at_points[active].astype(np.float32),oldDistanceM=tree_old.query(points[active])[0].astype(np.float32))
print('FOUR_ARM_MASKS_READY; EIGHT ORIGINAL MASKS COPIED EXACT',flush=True)
