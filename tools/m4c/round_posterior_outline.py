"""Extend only ID8 to the annotated rounded contour, on source surface UVs.

prepare -> project_posterior_outline.py in Blender -> finish.
No source geometry or UV coordinates are changed. Rendering weights have a
one-texel antialiased edge; picking uses a separate discrete ID atlas.
"""
import argparse
import copy
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree

from glb_io import source, read_glb, write_glb, sha

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'docs/m4c/meshy-deltoides-residu-local'
OUT = ROOT / 'docs/m4c/meshy-posterieur-droit-arrondi'
for name in ['textures', 'exports', 'renders']:
    (OUT / name).mkdir(parents=True, exist_ok=True)

def dump(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')

def prepare():
    _, vertices, _, faces = source(ROOT / 'assets/models/meshy-e45e5d8.glb')
    binding = np.load(ROOT / 'docs/m4c/meshy-huit-zones/source-uv-binding.npz')
    uv = binding['uv_blender'].copy()
    uv[:, :, 1] = 1 - uv[:, :, 1]
    old = np.array(Image.open(BASE / 'textures/muscle-ids.png'))
    size = old.shape[0]
    prior = json.loads((ROOT / 'docs/m4c/meshy-validation-arriere/renders/render-metadata.json').read_text())
    frame = next(f for f in prior['frames'] if f['file'] == 'apres-trois-quarts-arriere-droit.png')
    cam = np.array(frame['cameraMatrix'])
    crop = np.array([90., 278.])
    ratio = np.array([499 / 555, 474 / 527])
    # Regularized interpretation of the orange outline; not its hand-drawn noise.
    guides = np.array([[40,154],[56,121],[89,99],[120,84],[152,84],
                       [196,94],[242,112],[269,126],[294,151],[325,192],
                       [350,226],[365,264],[383,306],[399,351],[416,384],
                       [441,408],[455,421]], float)
    boundary = PchipInterpolator(guides[:, 0], guides[:, 1])
    # This return path is inside the protected blue region. IDs 1..7 are locked.
    inner = np.array([[40,154],[80,211],[140,269],[220,309],
                      [300,345],[380,383],[430,407],[455,421]], float)
    cap = PchipInterpolator(inner[:, 0], inner[:, 1])
    def project(points):
        b = points[:, [0, 2, 1]].copy()
        b[:, 1] *= -1
        q = (b - cam[:3, 3]) @ cam[:3, :3]
        raw = np.column_stack([(q[:, 0] / .36 + .5) * 1000,
                               (.5 - q[:, 1] / .36) * 1000])
        return (raw - crop) * ratio
    world = np.zeros((*old.shape, 3), np.float32)
    footprint = np.zeros((*old.shape, 2, 2), np.float32)
    coverage = np.zeros(old.shape, bool)
    for face in np.flatnonzero(binding['domain']):
        t = uv[face].astype(float) * size - .5
        lo = np.maximum(np.ceil(t.min(0)).astype(int), 0)
        hi = np.minimum(np.floor(t.max(0)).astype(int), size - 1)
        if np.any(hi < lo):
            continue
        xx, yy = np.meshgrid(np.arange(lo[0], hi[0]+1), np.arange(lo[1], hi[1]+1))
        pixels = np.column_stack([xx.ravel(), yy.ravel()])
        matrix = np.column_stack([t[1]-t[0], t[2]-t[0]])
        if abs(np.linalg.det(matrix)) < 1e-12:
            continue
        inverse = np.linalg.inv(matrix)
        ab = (pixels - t[0]) @ inverse.T
        w = np.column_stack([1-ab.sum(1), ab])
        inside = (w >= -1e-8).all(1)
        pixels, w = pixels[inside], w[inside]
        if len(w):
            x, y = pixels.T
            coverage[y, x] = True
            world[y, x] = w @ vertices[faces[face]]
            projected = project(vertices[faces[face]])
            footprint[y, x] = np.column_stack([projected[1]-projected[0], projected[2]-projected[0]]) @ inverse
    distance_uv, nearest = distance_transform_edt(~coverage, return_indices=True)
    valid = coverage | (distance_uv <= 4)
    y, x = np.where(valid & ((old == 0) | (old == 8)))
    nearest_y, nearest_x = nearest[:, y, x]
    points = world[nearest_y, nearest_x]
    screen = project(points)
    sy = np.clip(screen[:, 1], guides[0, 0], guides[-1, 0])
    gradient = np.column_stack([np.ones(len(sy)), -boundary.derivative()(sy)])
    gradient /= np.linalg.norm(gradient, axis=1)[:, None]
    signed = (screen[:, 0] - boundary(sy)) / np.sqrt(1 + boundary.derivative()(sy)**2)
    jac = footprint[nearest_y, nearest_x]
    aa = np.maximum(.6, np.abs(np.einsum('ni,nij->nj', gradient, jac)).sum(1))
    weight = np.clip(signed / aa + .5, 0, 1)
    distance_green, _ = cKDTree(world[coverage & (old == 8)]).query(points)
    cap_margin = 8 * np.clip(np.minimum((sy-40)/20, (455-sy)/20), 0, 1)
    eligible = ((screen[:, 1] >= 40) & (screen[:, 1] <= 455)
                & (screen[:, 0] <= cap(sy) + cap_margin) & (weight > 0)
                & (distance_green <= .04) & (points[:, 0] < -.14))
    # Only zero texels are candidates. Existing green, blue and red stay intact.
    eligible &= old[y, x] == 0
    np.savez_compressed(OUT / 'surface-candidates.npz', y=y[eligible], x=x[eligible],
                        point=points[eligible], weight=weight[eligible],
                        screen=screen[eligible], covered=coverage[y[eligible], x[eligible]])
    samples_y = np.linspace(40, 455, 831)
    points_annotation = np.column_stack([boundary(samples_y), samples_y])
    points_raw = points_annotation / ratio + crop
    guide = {'referenceCommit':'18e1a44374468b54ed00807eef8d60e49a4e64ed',
             'cameraMatrix':cam.tolist(), 'referenceResolution':[1000,1000],
             'targetSourceM':[-.225,.555,-.055], 'angleDegrees':-135, 'orthoScale':.36,
             'referenceCrop':[90,278,645,805], 'annotationSize':[499,474],
             'regularizedBoundaryYX':guides.tolist(), 'innerGuardYX':inner.tolist(),
             'curveRawPixels':points_raw.tolist(),
             'onlyDiscreteTransition':[0,8], 'protectedIds':list(range(1,8)),
             'smoothing':'Shape-preserving cubic interpolation, local texture-footprint antialiasing.',
             'probes':[[103,140],[130,245],[205,322],[320,382],[398,420],
                       [70,140],[96,245],[170,160],[260,220],[345,120]]}
    dump('outline-guides.json', guide)
    print('SURFACE_CANDIDATES', int(eligible.sum()), flush=True)

def finish():
    candidates = np.load(OUT / 'surface-candidates.npz')
    visibility = np.load(OUT / 'surface-visibility.npz')['visible']
    old = np.array(Image.open(BASE / 'textures/muscle-ids.png'))
    new = old.copy()
    alpha = np.array(Image.open(BASE / 'textures/deltoid.right.posterior.png'))
    y, x = candidates['y'][visibility], candidates['x'][visibility]
    weights = np.rint(candidates['weight'][visibility] * 255).astype(np.uint8)
    alpha[y, x] = np.maximum(alpha[y, x], weights)
    new[(old == 0) & (alpha >= 128)] = 8
    changed = new != old
    assert changed.any() and np.all(old[changed] == 0) and np.all(new[changed] == 8)
    assert np.all(alpha[old == 8] == 255) and not np.any(alpha[(old > 0) & (old != 8)])
    Image.fromarray(new).save(OUT / 'textures/muscle-ids.png')
    Image.fromarray(alpha).save(OUT / 'textures/deltoid.right.posterior.png')
    Image.fromarray(changed.astype(np.uint8)*255).save(OUT / 'textures/added-texels.png')
    spec = json.loads((BASE / 'regions.json').read_text())
    spec['roundedPosteriorOutline'] = {
        'referenceCommit':'18e1a44','onlyDiscreteTransition':[0,8],
        'guide':'outline-guides.json','projectedCurve':'projected-outline.json',
        'displayMask':'Antialiased L8 coverage; ID8 when coverage >= 128, no filtering for picking.',
        'status':'proposed-outline-awaiting-user-visual-validation'}
    dump('regions.json',spec)
    for zone in spec['zones']:
        if zone['code'] != 8:
            name=zone['id']+'.png'
            (OUT/'textures'/name).write_bytes((BASE/'textures'/name).read_bytes())
    (OUT/'textures/masks-rgba-0.png').write_bytes((BASE/'textures/masks-rgba-0.png').read_bytes())
    rgba=np.array(Image.open(BASE/'textures/masks-rgba-1.png'))
    rgba[:,:,3]=alpha
    Image.fromarray(rgba).save(OUT/'textures/masks-rgba-1.png')
    color=np.array(Image.open(BASE/'textures/control-basecolor.png'))
    neutral=color[old==0][0]/255.
    green=color[old==8][0]/255.
    def lin(c):return np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
    w=alpha[y,x,None]/255.
    c=lin(neutral)*(1-w)+lin(green)*w
    rgb=np.where(c<=.0031308,c*12.92,1.055*np.maximum(c,0)**(1/2.4)-.055)
    color[y,x]=np.rint(np.clip(rgb,0,1)*255).astype(np.uint8)
    Image.fromarray(color).save(OUT/'textures/control-basecolor.png')
    _,doc,binary=read_glb(BASE/'exports/meshy-eight-zones-control.glb')
    doc=copy.deepcopy(doc)
    replacements={doc['images'][0]['bufferView']:(OUT/'textures/control-basecolor.png').read_bytes(),
                  doc['images'][1]['bufferView']:(OUT/'textures/muscle-ids.png').read_bytes()}
    data=bytearray()
    for index,view in enumerate(doc['bufferViews']):
        payload=replacements.get(index,binary[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']])
        data.extend(b'\0'*((-len(data))%4));view['byteOffset']=len(data);view['byteLength']=len(payload);data.extend(payload)
    doc['buffers'][0]['byteLength']=len(data)
    doc['nodes'][0]['extras']['rounded_right_posterior']='18e1a44: neutral to ID8 only, source surface projected outline'
    write_glb(OUT/'exports/meshy-eight-zones-control.glb',doc,bytes(data))
    reg=json.loads((BASE/'region-binding.json').read_text())
    p=candidates['point'][visibility & (candidates['weight']>=.5) & candidates['covered']]
    for zone in reg['zones']:
        if zone['code']==8:
            zone['boundsSourceM']['min']=np.minimum(zone['boundsSourceM']['min'],p.min(0)).tolist()
            zone['boundsSourceM']['max']=np.maximum(zone['boundsSourceM']['max'],p.max(0)).tolist()
            zone.pop('sourceFaceCenterSamples',None)
            zone['boundsMethod']='union of preceding ID8 bounds and new visible surface texel samples'
            zone['centerMethod']='existing safe interior pivot retained; not a recalculated centroid'
    dump('region-binding.json',reg)
    (OUT/'picking-witnesses.json').write_bytes((BASE/'picking-witnesses.json').read_bytes())
    dump('correction.json',{'referenceCommit':'18e1a44','onlyTransition':[0,8],
                          'addedIDTexels':int(changed.sum()),'previousID8Texels':int((old==8).sum()),
                          'newID8Texels':int((new==8).sum()),'sevenOtherMasksByteIdentical':True,
                          'antialiasedFringeTexels':int(((alpha>0)&(alpha<255)).sum()),
                          'addedVisibleSurfaceBoundsM':{'min':p.min(0).tolist(),'max':p.max(0).tolist()},
                          'controlGlbSha256':sha((OUT/'exports/meshy-eight-zones-control.glb').read_bytes())})
    print((OUT/'correction.json').read_text(),flush=True)

parser=argparse.ArgumentParser()
parser.add_argument('step',choices=['prepare','finish'])
args=parser.parse_args()
prepare() if args.step=='prepare' else finish()
