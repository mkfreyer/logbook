"""Local ID8 lower-edge retreat, from ad08cef. Never changes mesh or UVs.

prepare -> project_mask_outline.py -> finish. The new orange guide replaces
the preceding annotation; only green coverage below this guide is removed.
"""
import argparse
import copy
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.interpolate import UnivariateSpline
from scipy.ndimage import distance_transform_edt,label

from glb_io import source, read_glb, write_glb, sha

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/m4c/meshy-posterieur-droit-arrondi'
OUT=ROOT/'docs/m4c/meshy-posterieur-droit-bord-inferieur'
for directory in ['textures','exports','renders']:(OUT/directory).mkdir(parents=True,exist_ok=True)

def dump(name,data):
    (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

def prepare():
    _,vertices,_,faces=source(ROOT/'assets/models/meshy-e45e5d8.glb')
    binding=np.load(ROOT/'docs/m4c/meshy-huit-zones/source-uv-binding.npz')
    uv=binding['uv_blender'].copy();uv[:,:,1]=1-uv[:,:,1]
    alpha=np.array(Image.open(BASE/'textures/deltoid.right.posterior.png'))
    size=len(alpha)
    frames=json.loads((BASE/'renders/render-metadata.json').read_text())['frames']
    frame=next(f for f in frames if f['file']=='apres-trois-quarts-arriere-droit.png')
    cam=np.array(frame['cameraMatrix'])
    origin=np.array([160.,376.]);ratio=np.array([873/447,801/410])
    # A small landmark set regularizes the manual line instead of copying its noise.
    controls=np.array([[58,231],[102,309],[169,385],[240,432],[310,489],
                       [399,534],[473,572],[521,584],[584,623],[647,666],
                       [700,711],[743,761],[776,801]],float)
    weights=np.ones(len(controls));weights[[0,-1]]=10
    boundary=UnivariateSpline(controls[:,0],controls[:,1],w=weights,s=100,k=3)
    assert np.all(boundary.derivative()(np.linspace(58,776,1000))>0)
    def project(points):
        b=points[:,[0,2,1]].copy();b[:,1]*=-1
        q=(b-cam[:3,3])@cam[:3,:3]
        raw=np.column_stack([(q[:,0]/.36+.5)*1000,(.5-q[:,1]/.36)*1000])
        return (raw-origin)*ratio
    world=np.zeros((*alpha.shape,3),np.float32)
    footprint=np.zeros((*alpha.shape,2,2),np.float32)
    covered=np.zeros(alpha.shape,bool)
    for face in np.flatnonzero(binding['domain']):
        t=uv[face].astype(float)*size-.5
        lo=np.maximum(np.ceil(t.min(0)).astype(int),0);hi=np.minimum(np.floor(t.max(0)).astype(int),size-1)
        if np.any(hi<lo):continue
        xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1))
        pixels=np.column_stack([xx.ravel(),yy.ravel()])
        matrix=np.column_stack([t[1]-t[0],t[2]-t[0]])
        if abs(np.linalg.det(matrix))<1e-12:continue
        inverse=np.linalg.inv(matrix);ab=(pixels-t[0])@inverse.T
        bary=np.column_stack([1-ab.sum(1),ab]);inside=(bary>=-1e-8).all(1)
        pixels,bary=pixels[inside],bary[inside]
        if len(bary):
            x,y=pixels.T;covered[y,x]=True;world[y,x]=bary@vertices[faces[face]]
            tri=project(vertices[faces[face]])
            footprint[y,x]=np.column_stack([tri[1]-tri[0],tri[2]-tri[0]])@inverse
    _,nearest=distance_transform_edt(~covered,return_indices=True)
    y,x=np.where(alpha>0)
    ny,nx=nearest[:,y,x];points=world[ny,nx]
    actual_screen=project(points)
    # A constant nearest-pixel gutter creates a kink where a curve crosses
    # a thin UV island. Extend the triangle's projected scalar field instead.
    # These are texture padding coordinates, not moved surface vertices.
    delta=np.column_stack([x-nx,y-ny])
    screen=actual_screen+np.einsum('nij,nj->ni',footprint[ny,nx],delta)
    sx=np.clip(screen[:,0],58,776);slope=boundary.derivative()(sx)
    gradient=np.column_stack([slope,-np.ones(len(sx))]);gradient/=np.linalg.norm(gradient,axis=1)[:,None]
    signed=(boundary(sx)-screen[:,1])/np.sqrt(1+slope**2)
    aa=np.maximum(.65,np.abs(np.einsum('ni,nij->nj',gradient,footprint[ny,nx])).sum(1))
    keep=np.clip(signed/aa+.5,0,1)
    eligible=((screen[:,0]>=58)&(screen[:,0]<=776)&(actual_screen[:,1]>=231)&(keep<1))
    np.savez_compressed(OUT/'surface-candidates.npz',y=y[eligible],x=x[eligible],point=points[eligible],
                        keep=keep[eligible],screen=screen[eligible],covered=covered[y[eligible],x[eligible]])
    np.savez_compressed(OUT/'source-green-samples.npz',y=y,x=x,point=points,screen=actual_screen,
                        textureScreen=screen,covered=covered[y,x])
    curve_x=np.linspace(58,776,900)
    curve_annotation=np.column_stack([curve_x,boundary(curve_x)])
    guide={'referenceCommit':'ad08cef2ac312866d5e8375d800ec1d5dcdd6e6d',
           'cameraMatrix':cam.tolist(),'referenceResolution':[1000,1000],
           'angleDegrees':-135,'targetSourceM':[-.225,.555,-.055],'orthoScale':.36,
           'referenceCrop':[160,376,607,786],'annotationSize':[873,801],
           'cropOrigin':origin.tolist(),'annotationScale':ratio.tolist(),
           'boundaryControlsXY':controls.tolist(),'splineResidualBudget':100,
           'curveRawPixels':(curve_annotation/ratio+origin).tolist(),
           'onlyDiscreteTransition':[8,0],'upperRoundProtectedAboveAnnotationY':231,
           'uvPadding':'Triangle-linear projected field in gutters; no UV or source position change.',
           'probes':[[240,470],[400,575],[530,625],[650,705],
                     [180,320],[350,450],[500,530],[580,460],
                     [145,60],[90,145],[770,530],[300,620]]}
    dump('lower-contour-guides.json',guide)
    print('LOWER_EDGE_CANDIDATES',int(eligible.sum()),flush=True)

def finish():
    candidates=np.load(OUT/'surface-candidates.npz')
    visible=np.load(OUT/'surface-visibility.npz')['visible']
    old=np.array(Image.open(BASE/'textures/muscle-ids.png'))
    old_alpha=np.array(Image.open(BASE/'textures/deltoid.right.posterior.png'))
    alpha=old_alpha.copy()
    y,x=candidates['y'][visible],candidates['x'][visible]
    keep=np.rint(candidates['keep'][visible]*255).astype(np.uint8)
    alpha[y,x]=np.minimum(alpha[y,x],keep)
    new=old.copy();new[(old==8)&(alpha<128)]=0
    # Extrapolation can leave tiny islands made exclusively of empty UV gutter
    # texels on the removed side. Clear only these, never a covered surface texel
    # or any part of the protected upper round.
    samples=np.load(OUT/'source-green-samples.npz')
    covered_map=np.zeros(old.shape,bool)
    covered_map[samples['y'],samples['x']]=samples['covered']
    lower_map=np.zeros(old.shape,bool)
    lower_map[samples['y'],samples['x']]=samples['screen'][:,1]>=231
    parts,_=label(new==8);counts=np.bincount(parts.ravel());discard=np.zeros(old.shape,bool)
    for component in np.flatnonzero((counts>0)&(counts<=8)):
        if component==0:continue
        mask=parts==component
        if np.all(~covered_map[mask]) and np.all(lower_map[mask]):discard|=mask
    alpha[discard]=0;new[discard]=0
    changed=new!=old
    assert changed.any() and np.all(old[changed]==8) and np.all(new[changed]==0)
    assert np.all(alpha<=old_alpha) and np.array_equal(new==8,alpha>=128)
    Image.fromarray(new).save(OUT/'textures/muscle-ids.png')
    Image.fromarray(alpha).save(OUT/'textures/deltoid.right.posterior.png')
    Image.fromarray(changed.astype(np.uint8)*255).save(OUT/'textures/removed-texels.png')
    spec=json.loads((BASE/'regions.json').read_text())
    spec['lowerContourRetreat']={'referenceCommit':'ad08cef','onlyDiscreteTransition':[8,0],
        'guide':'lower-contour-guides.json','projectedCurve':'projected-outline.json',
        'status':'proposed-local-retreat-awaiting-visual-validation',
        'upperRoundPreserved':True}
    dump('regions.json',spec)
    for zone in spec['zones']:
        if zone['code']!=8:
            name=zone['id']+'.png';(OUT/'textures'/name).write_bytes((BASE/'textures'/name).read_bytes())
    (OUT/'textures/masks-rgba-0.png').write_bytes((BASE/'textures/masks-rgba-0.png').read_bytes())
    rgba=np.array(Image.open(BASE/'textures/masks-rgba-1.png'));rgba[:,:,3]=alpha
    Image.fromarray(rgba).save(OUT/'textures/masks-rgba-1.png')
    color=np.array(Image.open(BASE/'textures/control-basecolor.png'))
    neutral=color[(old==0)&(old_alpha==0)][0]/255.;green=color[old_alpha==255][0]/255.
    y,x=np.where(alpha!=old_alpha);w=alpha[y,x,None]/255.
    def lin(c):return np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
    c=lin(neutral)*(1-w)+lin(green)*w
    rgb=np.where(c<=.0031308,c*12.92,1.055*np.maximum(c,0)**(1/2.4)-.055)
    color[y,x]=np.rint(np.clip(rgb,0,1)*255).astype(np.uint8)
    Image.fromarray(color).save(OUT/'textures/control-basecolor.png')
    _,doc,binary=read_glb(BASE/'exports/meshy-eight-zones-control.glb');doc=copy.deepcopy(doc)
    replacements={doc['images'][0]['bufferView']:(OUT/'textures/control-basecolor.png').read_bytes(),
                  doc['images'][1]['bufferView']:(OUT/'textures/muscle-ids.png').read_bytes()}
    data=bytearray()
    for index,view in enumerate(doc['bufferViews']):
        payload=replacements.get(index,binary[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']])
        data.extend(b'\0'*((-len(data))%4));view['byteOffset']=len(data);view['byteLength']=len(payload);data.extend(payload)
    doc['buffers'][0]['byteLength']=len(data)
    doc['nodes'][0]['extras']['right_posterior_lower_retreat']='ad08cef: ID8 to neutral below the new lower guide only'
    write_glb(OUT/'exports/meshy-eight-zones-control.glb',doc,bytes(data))
    valid=samples['covered']&(new[samples['y'],samples['x']]==8)
    points=samples['point'][valid]
    reg=json.loads((BASE/'region-binding.json').read_text())
    for zone in reg['zones']:
        if zone['code']==8:
            zone['boundsSourceM']={'min':points.min(0).tolist(),'max':points.max(0).tolist()}
            zone['boundsMethod']='remaining discrete ID8 surface samples after lower-contour retreat'
    dump('region-binding.json',reg)
    (OUT/'picking-witnesses.json').write_bytes((BASE/'picking-witnesses.json').read_bytes())
    protected=samples['screen'][:,1]<231
    assert np.array_equal(alpha[samples['y'][protected],samples['x'][protected]],
                          old_alpha[samples['y'][protected],samples['x'][protected]])
    dump('correction.json',{'referenceCommit':'ad08cef','onlyTransition':[8,0],
         'removedIDTexels':int(changed.sum()),'previousID8Texels':int((old==8).sum()),
         'remainingID8Texels':int((new==8).sum()),'upperRoundCoverageBitIdentical':True,
         'protectedUpperTexels':int(protected.sum()),'sevenOtherMasksByteIdentical':True,
         'isolatedEmptyGutterTexelsCleared':int(discard.sum()),
         'controlGlbSha256':sha((OUT/'exports/meshy-eight-zones-control.glb').read_bytes())})
    print((OUT/'correction.json').read_text(),flush=True)

parser=argparse.ArgumentParser();parser.add_argument('step',choices=['prepare','finish'])
args=parser.parse_args()
prepare() if args.step=='prepare' else finish()
