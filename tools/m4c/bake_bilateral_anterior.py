"""ID3 only. New bilateral asset, immutable validated right source directory."""
import argparse,copy,json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import distance_transform_edt,binary_dilation,binary_fill_holes,label
from scipy.spatial import cKDTree
from experimental_anterior import maps,project
from glb_io import source,read_glb,write_glb,sha
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'docs/m4c/experience-anterieur-droit';OUT=ROOT/'docs/m4c/experience-anterieurs-bilateraux'
for p in [OUT/'textures',OUT/'renders',OUT/'exports']:p.mkdir(parents=True,exist_ok=True)
def dump(file,data):(OUT/file).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def project_left(points,params):
    p=points.copy();p[:,0]*=-1;q=project(p,params);q[:,0]=305-q[:,0];return q
def prepare():
    t=json.loads((OUT/'surface-transfer.json').read_text());params=t['cameraParametersRight']
    curve=np.array([p['pixel'] for p in t['newLeftCurve']]);previous=np.array([p['pixel'] for p in t['oldLeftCurve']])
    boundary=PchipInterpolator(curve[:,1],curve[:,0]);oldboundary=PchipInterpolator(previous[:,1],previous[:,0])
    old=np.array(Image.open(BASE/'textures/muscle-ids.png'));alpha=np.array(Image.open(BASE/'textures/deltoid.left.anterior.png'))
    m=maps();covered=m['face']>=0;distance,nearest=distance_transform_edt(~covered,return_indices=True)
    y,x=np.where((covered|(distance<=4))&np.isin(old,[0,3]));ny,nx=nearest[:,y,x];points=m['world'][ny,nx]
    local=(points[:,0]>.13)&(points[:,0]<.285)&(points[:,1]>.44)&(points[:,1]<.66)&(points[:,2]>-.075)&(points[:,2]<.085)
    y,x,ny,nx,points=y[local],x[local],ny[local],nx[local],points[local]
    screen=project_left(points,params);faceids=m['face'][ny,nx]
    _,vertices,_,faces=source(ROOT/'assets/models/meshy-e45e5d8.glb')
    uv=np.load(ROOT/'docs/m4c/meshy-huit-zones/source-uv-binding.npz')['uv_blender'].copy();uv[:,:,1]=1-uv[:,:,1]
    foot=np.zeros((len(y),2,2))
    for face in np.unique(faceids):
        selected=faceids==face;q=uv[face].astype(float)*2048-.5
        tri=project_left(vertices[faces[face]],params)
        foot[selected]=np.column_stack([tri[1]-tri[0],tri[2]-tri[0]])@np.linalg.inv(np.column_stack([q[1]-q[0],q[2]-q[0]]))
    screen+=np.einsum('nij,nj->ni',foot,np.column_stack([x-nx,y-ny]))
    sy=np.clip(screen[:,1],curve[0,1],curve[-1,1]);slope=boundary(sy,1)
    gradient=np.column_stack([np.ones(len(sy)),-slope]);gradient/=np.linalg.norm(gradient,axis=1)[:,None]
    signed=(screen[:,0]-boundary(sy))/np.sqrt(1+slope**2)
    aa=np.maximum(.12,np.abs(np.einsum('ni,nij->nj',gradient,foot)).sum(1))
    target=np.rint(np.clip(signed/aa+.5,0,1)*255).astype(np.uint8)
    dist_curve=cKDTree(np.array([p['point'] for p in t['newLeftCurve']])).query(points)[0]
    protected=binary_dilation(old==4,iterations=4)
    # Only the strip between the old medial border and the adapted new border.
    editable=(screen[:,1]>=max(curve[0,1],previous[0,1]))&(screen[:,1]<=min(curve[-1,1],previous[-1,1]))
    editable&=(screen[:,0]>=np.minimum(boundary(sy),oldboundary(sy))-1.5)
    editable&=(screen[:,0]<=np.maximum(boundary(sy),oldboundary(sy))+1.5)
    editable&=(dist_curve<.025)&~protected[y,x]&(target!=alpha[y,x])
    np.savez_compressed(OUT/'surface-candidates.npz',y=y[editable],x=x[editable],point=points[editable],
        alpha=target[editable],screen=screen[editable],covered=covered[y[editable],x[editable]])
    dump('bake-domain.json',{'onlyEditableID':3,'referenceID':6,'anteriorLateralImmutableBandTexels':4,
        'curveDomainY':curve[[0,-1],1].tolist(),'oldLeftDomainY':previous[[0,-1],1].tolist(),
        'candidateTexels':int(editable.sum()),'method':'Object-space curve transposition, actual left UV triangle interpolation, 4px padding; no texture reflection.'})
    print('LEFT_LOCAL_CANDIDATES',int(editable.sum()),flush=True)
def finish():
    old=np.array(Image.open(BASE/'textures/muscle-ids.png'));a=np.array(Image.open(BASE/'textures/deltoid.left.anterior.png'));b=a.copy()
    c=np.load(OUT/'surface-candidates.npz');vis=np.load(OUT/'surface-visibility.npz')['visible'];y,x=c['y'][vis],c['x'][vis];b[y,x]=c['alpha'][vis]
    spec=json.loads((BASE/'regions.json').read_text());weights=np.zeros(old.shape,np.uint16)
    for z in spec['zones']:
        if z['code']!=3:weights+=np.array(Image.open(BASE/'textures'/(z['id']+'.png')),np.uint16)
    changed=b!=a;b[changed]=np.minimum(b[changed],np.clip(255-weights.astype(np.int32),0,255)[changed])
    new=old.copy();eligible=np.isin(old,[0,3]);new[eligible]=np.where(b[eligible]>=128,3,0)
    protected=binary_dilation(old==4,iterations=4)
    holes=binary_fill_holes(new==3)&(new==0)&(weights==0)&~protected
    assert holes.sum()<1000,'Unexpected large hole; inspect instead of filling globally'
    b[holes]=255;new[holes]=3
    # Only added empty UV-gutter fragments and added isolated single pixels.
    parts,_=label(new==3);counts=np.bincount(parts.ravel());discard=np.zeros(old.shape,bool);covered=maps()['face']>=0
    for part in np.flatnonzero((counts>0)&(counts<=32)):
        if part:
            p=parts==part
            if (counts[part]==1 or not np.any(p&covered)) and not np.any(p&(old==3)):discard|=p
    b[discard]=a[discard];new[discard]=old[discard]
    assert np.array_equal(a[protected],b[protected])
    assert np.all(np.isin(old[new!=old],[0,3])) and np.all(np.isin(new[new!=old],[0,3]))
    assert np.array_equal(new==3,b>=128)
    for z in spec['zones']:
        name=z['id']+'.png'
        if z['code']!=3:(OUT/'textures'/name).write_bytes((BASE/'textures'/name).read_bytes())
    Image.fromarray(b).save(OUT/'textures/deltoid.left.anterior.png');Image.fromarray(new).save(OUT/'textures/muscle-ids.png')
    rgba=np.array(Image.open(BASE/'textures/masks-rgba-0.png'));rgba[:,:,2]=b;Image.fromarray(rgba).save(OUT/'textures/masks-rgba-0.png')
    (OUT/'textures/masks-rgba-1.png').write_bytes((BASE/'textures/masks-rgba-1.png').read_bytes())
    color=np.array(Image.open(BASE/'textures/control-basecolor.png'));neutral=np.array([.5,.52,.55])
    red=np.array([int(spec['zones'][2]['color'][i:i+2],16)/255 for i in (1,3,5)]);red=np.where(red<=.04045,red/12.92,((red+.055)/1.055)**2.4)
    yy,xx=np.where(b!=a);w=(b[yy,xx].astype(float)-a[yy,xx])[:,None]/255;oldrgb=color[yy,xx]/255
    lin=np.where(oldrgb<=.04045,oldrgb/12.92,((oldrgb+.055)/1.055)**2.4);lin=np.maximum(0,lin+(red-neutral)*w)
    color[yy,xx]=np.rint(np.clip(np.where(lin<=.0031308,lin*12.92,1.055*lin**(1/2.4)-.055),0,1)*255).astype(np.uint8)
    Image.fromarray(color).save(OUT/'textures/control-basecolor.png');Image.fromarray((new!=old).astype(np.uint8)*255).save(OUT/'textures/changed-texels.png')
    spec['status']='bilateral-anterior-proposal-left-awaiting-visual-validation-right-7b69e3d-approved'
    spec['bilateralAnterior']={'referenceCommit':'7b69e3d','immutableRightID':6,'onlyEditableID':3,'sourceCurve':'surface-transfer.json','integration':False}
    dump('regions.json',spec)
    reg=json.loads((BASE/'region-binding.json').read_text());m=maps();points=m['world'][(new==3)&(m['face']>=0)]
    for z in reg['zones']:
        if z['code']==3:
            z['boundsSourceM']={'min':points.min(0).tolist(),'max':points.max(0).tolist()}
            z['boundsMethod']='ID3 covered surface samples after actual 3D transfer from validated ID6'
            z.pop('sourceFaceCenterSamples',None);z.pop('faceCenterDiagnosticComponentCounts',None)
    dump('region-binding.json',reg);(OUT/'picking-witnesses.json').write_bytes((BASE/'picking-witnesses.json').read_bytes())
    _,doc,binary=read_glb(BASE/'exports/meshy-eight-zones-control.glb');doc=copy.deepcopy(doc)
    replacements={doc['images'][0]['bufferView']:(OUT/'textures/control-basecolor.png').read_bytes(),doc['images'][1]['bufferView']:(OUT/'textures/muscle-ids.png').read_bytes()};data=bytearray()
    for i,v in enumerate(doc['bufferViews']):
        payload=replacements.get(i,binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]);data.extend(b'\0'*((-len(data))%4));v['byteOffset']=len(data);v['byteLength']=len(payload);data.extend(payload)
    doc['buffers'][0]['byteLength']=len(data);doc['nodes'][0]['extras']['bilateral_anterior']='7b69e3d right ID6 immutable; actual 3D transfer to left ID3 only'
    write_glb(OUT/'exports/meshy-eight-zones-control.glb',doc,bytes(data))
    dump('correction.json',{'referenceCommit':'7b69e3d','editableID':3,'immutableReferenceID':6,
        'addedIDTexels':int(((old==0)&(new==3)).sum()),'removedIDTexels':int(((old==3)&(new==0)).sum()),
        'changedAlphaTexels':int((a!=b).sum()),'localPinholesFilled':int(holes.sum()),
        'emptyAddedGutterTexelsPruned':int((discard&~covered).sum()),'coveredSingleTexelFragmentsPruned':int((discard&covered).sum()),
        'sevenOtherMasksByteIdentical':True,'rightAtlasPackByteIdentical':True,'geometryEdits':False,'uvEdits':False})
    print((OUT/'correction.json').read_text(),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('step',choices=['prepare','finish']);args=p.parse_args();globals()[args.step]()
