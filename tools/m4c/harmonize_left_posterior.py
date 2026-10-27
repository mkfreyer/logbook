"""Adapt the validated right outer contour to the real left surface; ID5 only.

reference -> adapt_left_surface.py -> prepare -> project_mask_outline.py -> finish.
No UV pixels are mirrored. The shared shape is a projected 3D surface curve.
"""
import argparse
import copy
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.interpolate import PchipInterpolator,UnivariateSpline
from scipy.optimize import brentq
from scipy.ndimage import distance_transform_edt,binary_dilation,binary_fill_holes,label
from scipy.spatial import cKDTree
from glb_io import source,read_glb,write_glb,sha

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/m4c/meshy-posterieur-droit-bord-inferieur'
OUT=ROOT/'docs/m4c/meshy-posterieurs-harmonises'
for d in ['textures','renders','exports']:(OUT/d).mkdir(parents=True,exist_ok=True)
def dump(name,value):(OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def reference():
    upper=np.array(json.loads((ROOT/'docs/m4c/meshy-posterieur-droit-arrondi/outline-guides.json').read_text())['curveRawPixels'])
    lower=np.array(json.loads((BASE/'lower-contour-guides.json').read_text())['curveRawPixels'])
    fx=PchipInterpolator(upper[:,1],upper[:,0]);fy=PchipInterpolator(lower[:,0],lower[:,1],extrapolate=True)
    scan=np.linspace(upper[0,1],upper[-1,1],3000);h=fy(fx(scan))-scan
    crossing=np.flatnonzero((h[:-1]>=0)&(h[1:]<0));assert len(crossing)>0
    k=int(crossing[0]);join_y=brentq(lambda y:float(fy(fx(y))-y),scan[k],scan[k+1]);join_x=float(fx(join_y))
    yy=np.linspace(upper[0,1],join_y,300,endpoint=False)
    xx=np.linspace(join_x,lower[-1,0],500)
    curve=np.r_[np.column_stack([fx(yy),yy]),np.column_stack([xx,fy(xx)])]
    frames=json.loads((BASE/'renders/render-metadata.json').read_text())['frames']
    cameras={side:next(f['cameraMatrix'] for f in frames if f['file']==f'apres-trois-quarts-arriere-{side}.png') for side in ['gauche','droit']}
    dump('right-reference-outline.json',{'referenceCommit':'977f68a0c45688d6c65c4186ab1711612f715f1f',
        'rightCurveRawPixels':curve.tolist(),'junctionRawPixel':[join_x,join_y],
        'cameraRight':cameras['droit'],'cameraLeft':cameras['gauche'],
        'method':'Validated right upper and lower 3D guide paths joined at their intersection; no texture reflection.'})
    print('RIGHT_REFERENCE_CURVE',len(curve),flush=True)

def prepare():
    _,v,_,faces=source(ROOT/'assets/models/meshy-e45e5d8.glb')
    binding=np.load(ROOT/'docs/m4c/meshy-huit-zones/source-uv-binding.npz');uv=binding['uv_blender'].copy();uv[:,:,1]=1-uv[:,:,1]
    old=np.array(Image.open(BASE/'textures/muscle-ids.png'));alpha=np.array(Image.open(BASE/'textures/deltoid.left.posterior.png'));size=len(old)
    other_coverage=np.zeros(old.shape,np.uint8)
    for zone in json.loads((BASE/'regions.json').read_text())['zones']:
        if zone['code']!=5:other_coverage=np.maximum(other_coverage,np.array(Image.open(BASE/'textures'/(zone['id']+'.png'))))
    adaptation=json.loads((OUT/'surface-adaptation.json').read_text())
    cam=np.array(adaptation['cameraLeft'])
    projected=np.array([p['leftReferencePixel'] for p in adaptation['samples']])
    # Smooth the small closest-triangle fluctuations, then ray-project this curve
    # again on the actual left surface. Keep the real shoulder asymmetry.
    order=np.argsort(projected[:,1]);projected=projected[order]
    levels=np.linspace(projected[0,1],projected[-1,1],31)
    xx=np.interp(levels,projected[:,1],projected[:,0])
    weights=np.ones(31);weights[[0,-1]]=10
    boundary=UnivariateSpline(levels,xx,w=weights,s=30,k=3)
    top,bottom=levels[[0,-1]]
    def project(points):
        b=points[:,[0,2,1]].copy();b[:,1]*=-1;q=(b-cam[:3,3])@cam[:3,:3]
        raw=np.column_stack([(q[:,0]/.36+.5)*1000,(.5-q[:,1]/.36)*1000])
        raw[:,0]=1000-raw[:,0]
        return raw
    world=np.zeros((*old.shape,3),np.float32);foot=np.zeros((*old.shape,2,2),np.float32);covered=np.zeros(old.shape,bool)
    for face in np.flatnonzero(binding['domain']):
        t=uv[face].astype(float)*size-.5;lo=np.maximum(np.ceil(t.min(0)).astype(int),0);hi=np.minimum(np.floor(t.max(0)).astype(int),size-1)
        if np.any(hi<lo):continue
        xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1));pixels=np.column_stack([xx.ravel(),yy.ravel()])
        matrix=np.column_stack([t[1]-t[0],t[2]-t[0]])
        if abs(np.linalg.det(matrix))<1e-12:continue
        inverse=np.linalg.inv(matrix);ab=(pixels-t[0])@inverse.T;bary=np.column_stack([1-ab.sum(1),ab]);inside=(bary>=-1e-8).all(1)
        pixels,bary=pixels[inside],bary[inside]
        if len(bary):
            x,y=pixels.T;covered[y,x]=True;world[y,x]=bary@v[faces[face]]
            tri=project(v[faces[face]]);foot[y,x]=np.column_stack([tri[1]-tri[0],tri[2]-tri[0]])@inverse
    dist_uv,nearest=distance_transform_edt(~covered,return_indices=True)
    eligible_domain=(covered|(dist_uv<=4))&((old==0)|(old==5))
    y,x=np.where(eligible_domain);ny,nx=nearest[:,y,x];points=world[ny,nx]
    local=(points[:,0]>.125)&(points[:,0]<.285)&(points[:,1]>.44)&(points[:,1]<.65)&(points[:,2]<-.035)
    y,x,ny,nx,points=y[local],x[local],ny[local],nx[local],points[local]
    actual=project(points);screen=actual+np.einsum('nij,nj->ni',foot[ny,nx],np.column_stack([x-nx,y-ny]))
    distance_old,_=cKDTree(world[covered&(old==5)]).query(points)
    distance_blue,_=cKDTree(world[covered&(old==4)]).query(points)
    sy=np.clip(screen[:,1],top,bottom);slope=boundary.derivative()(sy)
    gradient=np.column_stack([np.ones(len(sy)),-slope]);gradient/=np.linalg.norm(gradient,axis=1)[:,None]
    signed=(screen[:,0]-boundary(sy))/np.sqrt(1+slope**2)
    aa=np.maximum(.65,np.abs(np.einsum('ni,nij->nj',gradient,foot[ny,nx])).sum(1))
    target=np.clip(signed/aa+.5,0,1)
    previous=alpha[y,x]/255.
    target=np.where(screen[:,1]<top,previous,np.where(screen[:,1]>bottom,0,target))
    d=json.loads((BASE/'regions.json').read_text())['landmarks']['deltoid']
    t=np.clip((points[:,1]-d['insertionY'])/(d['topY']-d['insertionY']),0,1)
    posterior=d['insertionZ']+(d['posteriorOriginZ']-d['insertionZ'])*t**.85-.007*np.sin(np.pi*t)
    additions_allowed=(points[:,2]<posterior-.001)&(distance_old<.028)&(other_coverage[y,x]==0)
    target=np.where((old[y,x]==0)&~additions_allowed,0,target)
    # Preserve the actual existing green/blue join, including both UV seam sides.
    adaptation_weight=np.clip((distance_blue-.0025)/.0035,0,1)
    adaptation_weight=adaptation_weight**2*(3-2*adaptation_weight)
    target=previous*(1-adaptation_weight)+target*adaptation_weight
    adjacent_blue=binary_dilation(old==4,iterations=2)
    protected=((old[y,x]==5)&((distance_blue<=.0025)|adjacent_blue[y,x]))
    target[protected]=previous[protected]
    domain=(points[:,0]>.125)&(points[:,0]<.285)&(points[:,1]>.44)&(points[:,1]<.65)&(points[:,2]<-.035)&(distance_old<.032)
    change=domain&(np.abs(np.rint(target*255)-alpha[y,x])>0)
    np.savez_compressed(OUT/'surface-candidates.npz',y=y[change],x=x[change],point=points[change],weight=target[change],screen=screen[change],covered=covered[y[change],x[change]])
    mask=(old[y,x]==5)|(domain&(target>.1))
    np.savez_compressed(OUT/'left-surface-samples.npz',y=y[mask],x=x[mask],point=points[mask],screen=actual[mask],covered=covered[y[mask],x[mask]],protectedJoin=protected[mask])
    ys=np.linspace(top,bottom,900);curve=np.column_stack([1000-boundary(ys),ys])
    dump('left-contour-guides.json',{'referenceCommit':'977f68a','cameraMatrix':cam.tolist(),
         'referenceResolution':[1000,1000],'angleDegrees':135,'targetSourceM':[.225,.555,-.055],'orthoScale':.36,
         'cropOrigin':[1000,0],'annotationScale':[-1,1],
         'curveRawPixels':curve.tolist(),'curveTopBottomY':[top,bottom],
         'onlyEditableID':5,'immutableReferenceID':8,
         'protectedJoinBandM':.0025,'uvPadding':'Triangle-linear projected field.',
         'probes':[[205,450],[220,530],[310,675],[400,730],[300,450],[400,570],[480,680],[175,520]]})
    print('LEFT_SURFACE_CANDIDATES',int(change.sum()),flush=True)

def finish():
    c=np.load(OUT/'surface-candidates.npz');visible=np.load(OUT/'surface-visibility.npz')['visible']
    old=np.array(Image.open(BASE/'textures/muscle-ids.png'));previous=np.array(Image.open(BASE/'textures/deltoid.left.posterior.png'));alpha=previous.copy()
    y,x=c['y'][visible],c['x'][visible];alpha[y,x]=np.rint(c['weight'][visible]*255).astype(np.uint8)
    new=old.copy();editable=(old==0)|(old==5);new[editable]=np.where(alpha[editable]>=128,5,0)
    samples=np.load(OUT/'left-surface-samples.npz')
    covered=np.zeros(old.shape,bool);covered[samples['y'],samples['x']]=samples['covered']
    protected=np.zeros(old.shape,bool);protected[samples['y'],samples['x']]=samples['protectedJoin']
    parts,_=label(new==5);counts=np.bincount(parts.ravel());discard=np.zeros(old.shape,bool)
    for component in np.flatnonzero((counts>0)&(counts<=32)):
        if component==0:continue
        m=parts==component
        if np.all(~covered[m]) and not np.any(protected[m]):discard|=m
    alpha[discard]=0;new[discard]=0
    other_coverage=np.zeros(old.shape,np.uint8)
    for z in json.loads((BASE/'regions.json').read_text())['zones']:
        if z['code']!=5:other_coverage=np.maximum(other_coverage,np.array(Image.open(BASE/'textures'/(z['id']+'.png'))))
    # A one-texel threshold pinhole can occur where the adapted field meets
    # the immutable green/blue strip. Resolve only enclosed neutral texels.
    holes=binary_fill_holes(new==5)&(new==0)&(other_coverage==0)
    assert int(holes.sum())<=4,'Unexpected large hole: review adaptation instead of automatic filling'
    for yy,xx in zip(*np.where(holes)):
        patch=alpha[max(0,yy-1):yy+2,max(0,xx-1):xx+2]
        alpha[yy,xx]=max(128,int(np.rint(patch[patch>0].mean())))
        new[yy,xx]=5
    assert np.array_equal(new==5,alpha>=128)
    assert np.array_equal(old[~editable],new[~editable]) and not np.any(alpha[~editable])
    assert not np.any(alpha[other_coverage>0])
    assert np.array_equal(alpha[protected],previous[protected])
    Image.fromarray(new).save(OUT/'textures/muscle-ids.png');Image.fromarray(alpha).save(OUT/'textures/deltoid.left.posterior.png')
    Image.fromarray(((old!=new)*255).astype(np.uint8)).save(OUT/'textures/changed-texels.png')
    spec=json.loads((BASE/'regions.json').read_text());spec['leftPosteriorHarmonization']={
        'referenceCommit':'977f68a','referenceID':8,'editableID':5,'guide':'left-contour-guides.json',
        'adaptation':'surface-adaptation.json','status':'awaiting-visual-validation'};dump('regions.json',spec)
    for z in spec['zones']:
        if z['code']!=5:
            name=z['id']+'.png';(OUT/'textures'/name).write_bytes((BASE/'textures'/name).read_bytes())
    (OUT/'textures/masks-rgba-0.png').write_bytes((BASE/'textures/masks-rgba-0.png').read_bytes())
    rgba=np.array(Image.open(BASE/'textures/masks-rgba-1.png'));rgba[:,:,0]=alpha;Image.fromarray(rgba).save(OUT/'textures/masks-rgba-1.png')
    color=np.array(Image.open(BASE/'textures/control-basecolor.png'))
    neutral=color[(old==0)&(previous==0)][0]/255.;green=color[old==5][0]/255.
    y,x=np.where(alpha!=previous);w=alpha[y,x,None]/255.
    def lin(a):return np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4)
    value=lin(neutral)*(1-w)+lin(green)*w
    rgb=np.where(value<=.0031308,value*12.92,1.055*np.maximum(value,0)**(1/2.4)-.055)
    color[y,x]=np.rint(np.clip(rgb,0,1)*255).astype(np.uint8);Image.fromarray(color).save(OUT/'textures/control-basecolor.png')
    _,doc,binary=read_glb(BASE/'exports/meshy-eight-zones-control.glb');doc=copy.deepcopy(doc)
    replacements={doc['images'][0]['bufferView']:(OUT/'textures/control-basecolor.png').read_bytes(),doc['images'][1]['bufferView']:(OUT/'textures/muscle-ids.png').read_bytes()}
    data=bytearray()
    for i,view in enumerate(doc['bufferViews']):
        payload=replacements.get(i,binary[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']]);data.extend(b'\0'*((-len(data))%4));view['byteOffset']=len(data);view['byteLength']=len(payload);data.extend(payload)
    doc['buffers'][0]['byteLength']=len(data);doc['nodes'][0]['extras']['left_posterior_harmonization']='977f68a: ID5 only, right reference immutable'
    write_glb(OUT/'exports/meshy-eight-zones-control.glb',doc,bytes(data))
    keep=samples['covered']&(new[samples['y'],samples['x']]==5);points=samples['point'][keep]
    reg=json.loads((BASE/'region-binding.json').read_text())
    for z in reg['zones']:
        if z['code']==5:
            z['boundsSourceM']={'min':points.min(0).tolist(),'max':points.max(0).tolist()};z.pop('sourceFaceCenterSamples',None);z.pop('faceCenterDiagnosticComponentCounts',None)
            z['boundsAreConservativeFaceExtent']=False;z['boundsMethod']='remaining left ID5 surface texel samples after anatomical adaptation'
            z['centerMethod']='existing interior pivot retained'
    dump('region-binding.json',reg);(OUT/'picking-witnesses.json').write_bytes((BASE/'picking-witnesses.json').read_bytes())
    dump('correction.json',{'referenceCommit':'977f68a','editableID':5,'referenceID':8,
        'addedID5Texels':int(((old==0)&(new==5)).sum()),'removedID5Texels':int(((old==5)&(new==0)).sum()),
        'previousLeftID5Texels':int((old==5).sum()),'newLeftID5Texels':int((new==5).sum()),
        'protectedJoinTexels':int(protected.sum()),'emptyGutterFragmentsCleared':int(discard.sum()),
        'singleTexelJoinHolesResolved':int(holes.sum()),
        'rightAndSixOtherMasksByteIdentical':True,'controlGlbSha256':sha((OUT/'exports/meshy-eight-zones-control.glb').read_bytes())})
    print((OUT/'correction.json').read_text(),flush=True)

parser=argparse.ArgumentParser();parser.add_argument('step',choices=['reference','prepare','finish']);args=parser.parse_args()
globals()[args.step]()
