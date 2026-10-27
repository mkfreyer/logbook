"""Isolated ID6 experiment from 168ac61. No anatomical/global resegmentation.

Run prepare, then project_experimental_anterior.py in Blender, then finish.
All outputs are new; validated source folders are read only.
"""
import argparse, copy, json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.interpolate import CubicSpline
from scipy.ndimage import distance_transform_edt, binary_fill_holes, label
from scipy.optimize import least_squares
from scipy.spatial import ConvexHull, cKDTree
from glb_io import source, read_glb, write_glb, sha

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/m4c/meshy-posterieurs-harmonises'
OUT=ROOT/'docs/m4c/experience-anterieur-droit'
CACHE=ROOT.parent/'m4c-anterieur-cache'
for p in (OUT/'textures',OUT/'exports',OUT/'renders',CACHE): p.mkdir(parents=True,exist_ok=True)
def dump(name,value): (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def maps():
    file=CACHE/'surface.npz'
    if file.exists(): return np.load(file)
    _,v,_,f=source(ROOT/'assets/models/meshy-e45e5d8.glb')
    binding=np.load(ROOT/'docs/m4c/meshy-huit-zones/source-uv-binding.npz')
    uv=binding['uv_blender'].copy();uv[:,:,1]=1-uv[:,:,1]
    size=2048;world=np.zeros((size,size,3),np.float32)
    face_map=np.full((size,size),-1,np.int32)
    for face in np.flatnonzero(binding['domain']):
        t=uv[face].astype(float)*size-.5
        lo=np.maximum(np.ceil(t.min(0)).astype(int),0);hi=np.minimum(np.floor(t.max(0)).astype(int),size-1)
        if np.any(hi<lo):continue
        xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1))
        p=np.column_stack([xx.ravel(),yy.ravel()]);m=np.column_stack([t[1]-t[0],t[2]-t[0]])
        if abs(np.linalg.det(m))<1e-12:continue
        ab=(p-t[0])@np.linalg.inv(m).T;b=np.column_stack([1-ab.sum(1),ab]);inside=(b>=-1e-8).all(1)
        p,b=p[inside],b[inside]
        if len(p):
            x,y=p.T;face_map[y,x]=face;world[y,x]=b@v[f[face]]
    _,nearest=distance_transform_edt(face_map<0,return_indices=True)
    np.savez_compressed(file,world=world,face=face_map,nearest=nearest)
    return np.load(file)

def axes(angle,elevation):
    a,e=np.radians([angle,elevation])
    toward=np.array([np.sin(a)*np.cos(e),np.sin(e),np.cos(a)*np.cos(e)])
    right=np.array([np.cos(a),0,-np.sin(a)])
    up=np.cross(toward,right)
    return right,up,toward

def project(points,params):
    angle,elevation,distance,scale,cx,cy=params
    r,u,z=axes(angle,elevation);p=points-np.array([-.2,.56,0.])
    denom=1-(p@z)/distance
    return np.column_stack([cx+scale*(p@r)/denom,cy-scale*(p@u)/denom])

def poly_samples(poly,n=240):
    p=np.vstack([poly,poly[0]]);length=np.linalg.norm(np.diff(p,axis=0),axis=1)
    t=np.r_[0,np.cumsum(length)];q=np.linspace(0,t[-1],n,endpoint=False)
    return np.column_stack([np.interp(q,t,p[:,k]) for k in range(2)])

def prepare():
    m=maps();old=np.array(Image.open(BASE/'textures/muscle-ids.png'))
    points=m['world'][(old==6)&(m['face']>=0)][::2]
    # Landmark transcription from the user's 305x221 crop; no rejected yellow
    # annotations or geometry/resources from 6817b08 are read by this experiment.
    outline=np.array([[130,75],[143,69],[155,68],[166,71],[174,79],
        [183,95],[192,114],[200,138],[205,160],[209,177],
        [185,164],[160,148],[142,132],[132,116],[126,104],[123,90]],float)
    # Compare both orientations first. The attachment places the shoulder on
    # the opposite screen side from the right muscle in the restored model.
    fit_outline=outline.copy();fit_outline[:,0]=305-fit_outline[:,0]
    target=poly_samples(fit_outline)
    def error(params):
        q=project(points,params);hull=q[ConvexHull(q).vertices];edge=poly_samples(hull)
        return np.r_[cKDTree(target).query(edge)[0],cKDTree(edge).query(target)[0]]
    best=None
    for angle in [-35,-55,-75]:
        fit=least_squares(error,[angle,8,1.5,500,140,120],
            bounds=([-110,-25,.5,200,20,30],[-10,40,5,1000,250,180]),max_nfev=300,diff_step=1e-4)
        if best is None or np.mean(fit.fun**2)<np.mean(best.fun**2):best=fit
    params=best.x
    # Orange guide on the pectoral-facing edge only. Smooth endpoints reconnect
    # to the old superior origin and the existing common inferior insertion.
    controls=np.array([[130,73],[120,82],[115,94],[120,105],[130,120],
        [138,133],[152,145],[169,157],[186,167],[200,174],[209,177]],float)
    t=np.r_[0,np.cumsum(np.linalg.norm(np.diff(controls,axis=0),axis=1))];t/=t[-1]
    curve=CubicSpline(t,controls,bc_type='natural')(np.linspace(0,1,800))
    dump('guide-camera.json',{'sourceCommit':'168ac61','maskReference':'06fa665',
        'inputCropResolution':[305,221],'originalMaskOutlinePixels':outline.tolist(),
        'guideControlsPixels':controls.tolist(),'curvePixels':curve.tolist(),
        'cameraModel':'perspective, zero roll; fitted to original orange mask silhouette',
        'cameraParameters':params.tolist(),'cameraAnchorSourceM':[-.2,.56,0.],
        'inputSide':'left','targetSide':'right','referenceViewReflectedForRightProjection':True,
        'sideTransferConfirmedByUser':True,
        'parameters':['azimuthDeg','elevationDeg','distanceM','scalePxPerMAtAnchor','centerX','centerY'],
        'maskOutlineFitRmsPx':float(np.sqrt(np.mean(best.fun**2))),
        'limit':'305x221 raster crop, no iPhone camera telemetry; alignment is reconstructed, not pixel-exact metadata.',
        'editableID':6,'protectedIDs':[1,2,3,4,5,7,8]})
    print('CAMERA',params,'RMS',np.sqrt(np.mean(best.fun**2)),flush=True)

def finish():
    old=np.array(Image.open(BASE/'textures/muscle-ids.png'))
    old_alpha=np.array(Image.open(BASE/'textures/deltoid.right.anterior.png'))
    c=np.load(OUT/'surface-edit.npz');alpha=old_alpha.copy()
    y,x=c['y'],c['x'];alpha[y,x]=c['alpha']
    # Preserve existing antialiased weights of all seven protected regions.
    weights=np.zeros(old.shape,np.uint16)
    spec=json.loads((BASE/'regions.json').read_text())
    for z in spec['zones']:
        if z['code']!=6:weights+=np.array(Image.open(BASE/'textures'/(z['id']+'.png')),np.uint16)
    changed=alpha!=old_alpha
    alpha[changed]=np.minimum(alpha[changed],np.clip(255-weights.astype(np.int32),0,255)[changed])
    new=old.copy();new[(old==0)&(alpha>=128)]=6;new[(old==6)&(alpha<128)]=0
    # Only raster artifacts created inside this new strip: fill enclosed neutral
    # pinholes and discard tiny added UV-gutter fragments, never a source zone.
    holes=binary_fill_holes(new==6)&(new==0)&(weights==0)
    alpha[holes]=255;new[holes]=6
    parts,_=label(new==6);counts=np.bincount(parts.ravel());discard=np.zeros(old.shape,bool)
    for part in np.flatnonzero((counts>0)&(counts<=5)):
        if part and not np.any((parts==part)&(old==6)):discard|=parts==part
    alpha[discard]=old_alpha[discard];new[discard]=old[discard]
    assert np.all(np.isin(old[new!=old],[0,6])) and np.all(np.isin(new[new!=old],[0,6]))
    for code in [1,2,3,4,5,7,8]:assert np.array_equal(old==code,new==code)
    assert np.array_equal(alpha>=128,new==6)
    spec['status']='experimental-right-anterior-edge-only-awaiting-user-validation'
    spec['uvSource']='../meshy-huit-zones/source-uv-binding.npz'
    spec['coverageSource']='../meshy-huit-zones/textures/uv-covered-pixels.png'
    spec['localAnteriorExperiment']={'base':'168ac61','onlyCode':6,'guide':'guide-camera.json','surfaceCurve':'projected-curve.json','interactiveIntegration':False}
    dump('regions.json',spec)
    for z in spec['zones']:
        file=z['id']+'.png'
        if z['code']!=6:(OUT/'textures'/file).write_bytes((BASE/'textures'/file).read_bytes())
    Image.fromarray(alpha).save(OUT/'textures/deltoid.right.anterior.png')
    Image.fromarray(new).save(OUT/'textures/muscle-ids.png')
    for group in range(2):
        file=f'masks-rgba-{group}.png'
        if group==0:(OUT/'textures'/file).write_bytes((BASE/'textures'/file).read_bytes())
        else:
            rgba=np.array(Image.open(BASE/'textures'/file));rgba[:,:,1]=alpha
            Image.fromarray(rgba).save(OUT/'textures'/file)
    color=np.array(Image.open(BASE/'textures/control-basecolor.png'))
    neutral=np.array([.5,.52,.55]);red=np.array([int(spec['zones'][5]['color'][i:i+2],16)/255 for i in (1,3,5)])
    red=np.where(red<=.04045,red/12.92,((red+.055)/1.055)**2.4)
    yy,xx=np.where(alpha!=old_alpha);w=(alpha[yy,xx].astype(float)-old_alpha[yy,xx])[:,None]/255
    previous=color[yy,xx]/255
    previous=np.where(previous<=.04045,previous/12.92,((previous+.055)/1.055)**2.4)
    lin=np.maximum(0,previous+(red-neutral)*w)
    rgb=np.where(lin<=.0031308,lin*12.92,1.055*lin**(1/2.4)-.055)
    color[yy,xx]=np.rint(np.clip(rgb,0,1)*255).astype(np.uint8)
    Image.fromarray(color).save(OUT/'textures/control-basecolor.png')
    Image.fromarray((new!=old).astype(np.uint8)*255).save(OUT/'textures/changed-texels.png')
    (OUT/'picking-witnesses.json').write_bytes((BASE/'picking-witnesses.json').read_bytes())
    binding=json.loads((BASE/'region-binding.json').read_text())
    new_surface=(old==0)&(new==6)&(maps()['face']>=0)
    extra=maps()['world'][new_surface]
    for zone in binding['zones']:
        if zone['code']==6:
            bounds=zone['boundsSourceM']
            bounds['min']=np.minimum(bounds['min'],extra.min(0)).tolist()
            bounds['max']=np.maximum(bounds['max'],extra.max(0)).tolist()
            zone['boundsMethod']='Union of unchanged conservative source bounds and new covered ID6 surface samples'
            zone['faceCenterDiagnosticCountsReference']='168ac61; not recomputed, not used for mask IDs'
    dump('region-binding.json',binding)
    _,doc,binary=read_glb(BASE/'exports/meshy-eight-zones-control.glb');doc=copy.deepcopy(doc)
    replacements={doc['images'][0]['bufferView']:(OUT/'textures/control-basecolor.png').read_bytes(),doc['images'][1]['bufferView']:(OUT/'textures/muscle-ids.png').read_bytes()}
    data=bytearray()
    for i,view in enumerate(doc['bufferViews']):
        payload=replacements.get(i,binary[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']])
        data.extend(b'\0'*((-len(data))%4));view['byteOffset']=len(data);view['byteLength']=len(payload);data.extend(payload)
    doc['buffers'][0]['byteLength']=len(data)
    doc['nodes'][0]['extras']['local_experiment']='Only ID6 pectoral-facing edge; base 168ac61; not integrated'
    write_glb(OUT/'exports/meshy-eight-zones-control.glb',doc,bytes(data))
    dump('correction.json',{'base':'168ac61','editableID':6,'addedIDTexels':int(((old==0)&(new==6)).sum()),'removedIDTexels':int(((old==6)&(new==0)).sum()),'changedAlphaTexels':int((alpha!=old_alpha).sum()),'localRasterPinholesFilled':int(holes.sum()),'tinyAddedGutterTexelsDiscarded':int(discard.sum()),'geometryEdits':False,'uvEdits':False,'sevenOtherMasksByteIdentical':True})
    print((OUT/'correction.json').read_text(),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('step',choices=['prepare','finish']);a=p.parse_args()
    prepare() if a.step=='prepare' else finish()
