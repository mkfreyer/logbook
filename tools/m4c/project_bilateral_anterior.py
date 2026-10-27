"""Read the VALIDATED ID6 isocontour, reflect in 3D, project to actual left.

No UV image is reflected. This produces guides only, on the unchanged mesh.
"""
import json,sys
from pathlib import Path
import bpy,numpy as np
from mathutils.bvhtree import BVHTree
from scipy.interpolate import UnivariateSpline
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/m4c'))
from experimental_anterior import axes,project
from scene import bv
from glb_io import sha
BASE=ROOT/'docs/m4c/experience-anterieur-droit';OUT=ROOT/'docs/m4c/experience-anterieurs-bilateraux'
for p in [OUT/'textures',OUT/'renders',OUT/'exports']:p.mkdir(parents=True,exist_ok=True)
g=json.loads((BASE/'guide-camera.json').read_text());params=g['cameraParameters'];angle,elevation,distance,scale,cx,cy=params
r,u,z=axes(angle,elevation);anchor=np.array(g['cameraAnchorSourceM']);loc=anchor+distance*z
bpy.ops.wm.open_mainfile(filepath=str(BASE/'experience-anterieur-droit.blend'),use_scripts=False)
mesh=bpy.data.objects['MESHY_M4C'].data
verts=np.array([[v.co.x,v.co.z,-v.co.y] for v in mesh.vertices]);faces=np.array([p.vertices[:] for p in mesh.polygons])
tree=BVHTree.FromPolygons([v.co[:] for v in mesh.vertices],[p.vertices[:] for p in mesh.polygons],all_triangles=True)
if '--visibility' in sys.argv:
    c=np.load(OUT/'surface-candidates.npz');left_loc=loc.copy();left_loc[0]*=-1;errors=[]
    for point in c['point']:
        h=tree.ray_cast(bv(left_loc),bv(point-left_loc).normalized())
        errors.append((h[0]-bv(point)).length if h[0] is not None else float('inf'))
    errors=np.array(errors);np.savez_compressed(OUT/'surface-visibility.npz',visible=errors<.0015,hitErrorM=errors)
    print('LEFT_CANDIDATES_VISIBLE',int((errors<.0015).sum()),len(errors),flush=True);sys.exit(0)
triangles=verts[faces]
selected=np.flatnonzero(np.all((triangles[:,:,0]>.12)&(triangles[:,:,1]>.43)&(triangles[:,:,1]<.67),axis=1))
left_tree=BVHTree.FromPolygons([v.co[:] for v in mesh.vertices],faces[selected].tolist(),all_triangles=True)
uv=np.load(ROOT/'docs/m4c/meshy-huit-zones/source-uv-binding.npz')['uv_blender'].copy();uv[:,:,1]=1-uv[:,:,1]
def image(name,folder=BASE):
    im=bpy.data.images.load(str(folder/'textures'/name),check_existing=False);im.colorspace_settings.name='Non-Color'
    # Source alpha files are ordinary grayscale, read with Blender once.
    data=np.empty(im.size[0]*im.size[1]*4,np.float32);im.pixels.foreach_get(data)
    return np.rint(data.reshape(im.size[1],im.size[0],4)[::-1,:,0]*255).astype(np.uint8)
alpha_right=image('deltoid.right.anterior.png');alpha_left=image('deltoid.left.anterior.png')
def weight(alpha,tex):
    x,y=np.clip(tex*2048-.5,0,2047);i,j=int(x),int(y);a,b=x-i,y-j
    return ((1-a)*(1-b)*float(alpha[j,i])+a*(1-b)*float(alpha[j,min(i+1,2047)])+
            (1-a)*b*float(alpha[min(j+1,2047),i])+a*b*float(alpha[min(j+1,2047),min(i+1,2047)]))/255
def hit(pixel,side='right'):
    px,py=305-pixel[0],pixel[1]
    direction=r*((px-cx)/(scale*distance))+u*((cy-py)/(scale*distance))-z
    origin=loc.copy()
    if side=='left':origin[0]*=-1;direction[0]*=-1
    found=tree.ray_cast(bv(origin),bv(direction).normalized())
    if found[0] is None:return None
    point=np.array([found[0].x,found[0].z,-found[0].y]);tri=verts[faces[found[2]]]
    ab=np.linalg.lstsq(np.column_stack([tri[1]-tri[0],tri[2]-tri[0]]),point-tri[0],rcond=None)[0]
    tex=np.r_[1-ab.sum(),ab]@uv[found[2]]
    return {'point':point,'face':int(found[2]),'uv':tex}
def boundary(side,alpha):
    samples=[]
    for y in np.arange(69,177.01,.25):
        previous=None
        for x in np.arange(108,216,.75):
            p=hit([x,y],side);w=weight(alpha,p['uv']) if p else 0
            if previous and previous[1]<.5 and w>=.5:
                low,high=previous[0],x
                for _ in range(14):
                    middle=(low+high)/2;q=hit([middle,y],side)
                    if q and weight(alpha,q['uv'])>=.5:high=middle
                    else:low=middle
                p=hit([(low+high)/2,y],side)
                samples.append({'pixel':[(low+high)/2,float(y)],'point':p['point'].tolist(),'sourceFace':p['face'],'uv':p['uv'].tolist(),'weight':weight(alpha,p['uv'])})
                break
            previous=(x,w)
    assert len(samples)>350,(side,len(samples))
    return samples
if '--measure' in sys.argv:
    from scipy.interpolate import PchipInterpolator
    t=json.loads((OUT/'surface-transfer.json').read_text());actual=boundary('left',image('deltoid.left.anterior.png',OUT))
    target=np.array([p['pixel'] for p in t['newLeftCurve']]);reference=np.array([p['pixel'] for p in t['referenceRightCurve']])
    original=np.array([p['pixel'] for p in t['oldLeftCurve']]);current=np.array([p['pixel'] for p in actual])
    curve=PchipInterpolator(target[:,1],target[:,0]);ref=PchipInterpolator(reference[:,1],reference[:,0]);before=PchipInterpolator(original[:,1],original[:,0])
    valid=(current[:,1]>=target[0,1])&(current[:,1]<=target[-1,1])
    sy=current[valid,1];error=np.abs(current[valid,0]-curve(sy));symmetry=np.abs(current[valid,0]-ref(sy))
    old_error=np.abs(before(sy)-ref(sy));ids=image('muscle-ids.png');protected=[]
    for p in t['newLeftCurve']:
        x,y=np.clip((np.array(p['uv'])*2048).astype(int),0,2047)
        if ids[y,x] in [1,4]:protected.append({'pixel':p['pixel'],'sourceID':int(ids[y,x]),'point':p['point']})
    intervals=[]
    for low,high in [(69,90),(90,110),(110,130),(130,150),(150,177)]:
        sel=(sy>=low)&(sy<high)
        if sel.any():intervals.append({'referenceY':[low,high],'meanLeftRightBorderDifferencePx':float(symmetry[sel].mean()),'maxAdaptedCurveDifferencePx':float(error[sel].max())})
    report={'referenceCommit':'7b69e3d','finalLeftCurve':actual,'commonRows':int(valid.sum()),
        'meanDistanceToAdaptedGuidePx':float(error.mean()),'maxDistanceToAdaptedGuidePx':float(error.max()),
        'meanLeftRightDifferenceBeforePx':float(old_error.mean()),'meanLeftRightDifferenceAfterPx':float(symmetry.mean()),
        'protectedMaskGuideSamples':protected,'protectedSampleCount':len(protected),'guideSampleCount':len(t['newLeftCurve']),
        'intervals':intervals,'units':'Pixels in the reconstructed 305x221 comparison view, not device performance or medical measurements.'}
    (OUT/'contour-comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('MEASURED_LEFT_BORDER',len(actual),'ERROR_PX',error.mean(),error.max(),'PROTECTED_SAMPLES',len(protected),flush=True);sys.exit(0)
right=boundary('right',alpha_right);left_original=boundary('left',alpha_left)
adapted=[]
for sample in right:
    reflected=np.array(sample['point']);reflected[0]*=-1
    nearest=left_tree.find_nearest(bv(reflected));assert nearest[0] is not None and nearest[3]<.015
    p=np.array([nearest[0].x,nearest[0].z,-nearest[0].y]);ref=p.copy();ref[0]*=-1
    pixel=project(ref[None,:],params)[0];pixel[0]=305-pixel[0]
    adapted.append({'rightPoint':sample['point'],'reflectedPoint':reflected.tolist(),'leftPoint':p.tolist(),
        'leftSourceFace':int(selected[nearest[2]]),'projectionDistanceM':float(nearest[3]),'leftPixel':pixel.tolist()})
pixels=np.array([p['leftPixel'] for p in adapted]);order=np.argsort(pixels[:,1]);pixels=pixels[order]
# Bin before regularizing the small nearest-triangle fluctuations. The source is
# the actual validated alpha=.5 border, including its pectoral clipping.
levels=np.linspace(pixels[0,1],pixels[-1,1],50);xx=np.interp(levels,pixels[:,1],pixels[:,0])
w=np.ones(len(levels));w[[0,-1]]=10
spline=UnivariateSpline(levels,xx,w=w,s=3,k=3)
ys=np.linspace(levels[0],levels[-1],900);guide=np.column_stack([spline(ys),ys])
final=[]
for pixel in guide:
    p=hit(pixel,'left');assert p is not None
    final.append({'pixel':pixel.tolist(),'point':p['point'].tolist(),'sourceFace':p['face'],'uv':p['uv'].tolist()})
distances=np.array([p['projectionDistanceM'] for p in adapted])
data={'referenceCommit':'7b69e3d','referenceMaskSha256':sha((BASE/'textures/deltoid.right.anterior.png').read_bytes()),
    'referenceID':6,'editableID':3,'method':'Read actual right alpha=.5 boundary by surface raycasts; reflect 3D points, nearest projection on real left triangles, regularize and ray-project again. No UV pixel reflection.',
    'cameraParametersRight':params,'leftCameraIsSpatialReflection':True,
    'referenceRightCurve':right,'oldLeftCurve':left_original,'adaptation':adapted,'newLeftCurve':final,
    'meanProjectionDistanceM':float(distances.mean()),'maxProjectionDistanceM':float(distances.max()),
    'smoothingLevels':levels.tolist(),'smoothingX':xx.tolist(),'smoothingResidualBudget':3,
    'smoothingRmsPixels':float(np.sqrt(np.mean((spline(levels)-xx)**2))),
    'geometryChanged':False,'uvChanged':False}
(OUT/'surface-transfer.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print('ACTUAL_RIGHT_BORDER',len(right),'LEFT',len(left_original),'TRANSFER_ERROR_M',distances.mean(),distances.max(),flush=True)
