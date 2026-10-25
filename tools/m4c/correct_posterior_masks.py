"""Local mask-only correction from 8b723d9. Only codes 5/8 may become neutral.

Original UVs, triangles, coordinates and normals are read, never modified.
The previous complete prototype remains intact alongside the correction.
"""
import copy,json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import distance_transform_edt,label,binary_dilation
from glb_io import source,read_glb,write_glb,sha
root=Path(__file__).resolve().parents[2];base=root/'docs/m4c/meshy-huit-zones';out=root/'docs/m4c/meshy-deltoides-limite-inferieure'
_,v,n,f=source(root/'assets/models/meshy-e45e5d8.glb');b=np.load(base/'source-uv-binding.npz');uv=b['uv_blender'].copy();uv[:,:,1]=1-uv[:,:,1];domain=b['domain']
old=np.array(Image.open(base/'textures/muscle-ids.png'));size=len(old);new=old.copy();coverage=np.zeros(old.shape,bool);world=np.zeros((*old.shape,3),np.float32)
landmarks=json.loads((out/'crease-landmarks.json').read_text());curves={};curve_metadata={}
for side,rows in landmarks['sides'].items():
    # Crease points were ray-picked on each real shoulder, not mirrored vertices.
    picked=[(p['pointGLB'][2],p['pointGLB'][1]) for p in rows[:4]]
    anchors=sorted([(-.15,.48),(-.125,.491),*picked,(-.058,.452)])
    zz,yy=np.array(anchors).T;assert np.diff(zz).min()>0
    curves[side]=PchipInterpolator(zz,yy,extrapolate=False);curve_metadata[side]=anchors
for face in np.flatnonzero(domain):
    t=uv[face].astype(float)*size-.5;lo=np.maximum(np.ceil(t.min(0)).astype(int),0);hi=np.minimum(np.floor(t.max(0)).astype(int),size-1)
    if np.any(hi<lo):continue
    xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1));q=np.column_stack([xx.ravel(),yy.ravel()]);matrix=np.column_stack([t[1]-t[0],t[2]-t[0]])
    if abs(np.linalg.det(matrix))<1e-12:continue
    ab=(q-t[0])@np.linalg.inv(matrix).T;w=np.column_stack([1-ab.sum(1),ab]);inside=(w>=-1e-8).all(1);q=q[inside];w=w[inside]
    if not len(q):continue
    x,y=q.T;coverage[y,x]=True;world[y,x]=w@v[f[face]]
# Evaluate existing gutter texels from their nearest actual surface sample.
# No new UV paint or global mask rebake is performed.
_,nearest=distance_transform_edt(~coverage,return_indices=True)
green=np.isin(old,[5,8]);gy,gx=np.where(green)
position=world[gy,gx].copy();padding=~coverage[gy,gx];position[padding]=world[nearest[0][gy[padding],gx[padding]],nearest[1][gy[padding],gx[padding]]]
removed=np.zeros(old.shape,bool);stats={}
for side,code in [('left',5),('right',8)]:
    relevant=old[gy,gx]==code;p=position[relevant];floor=curves[side](np.clip(p[:,2],-.15,-.058))
    cut=p[:,1]<floor;ry,rx=gy[relevant][cut],gx[relevant][cut];removed[ry,rx]=True;new[ry,rx]=0
    count=int((old==code).sum());remaining=int((new==code).sum());changed_points=p[cut & coverage[gy[relevant],gx[relevant]]]
    stats[side]={'code':code,'before_texels':count,'after_texels':remaining,'removed_texels':count-remaining,'retained_percent':round(100*remaining/count,3),'removed_source_bounds_m':{'min':changed_points.min(0).tolist(),'max':changed_points.max(0).tolist()}}
# Clipping can leave one-texel green fragments beside the new boundary.
# Remove only such fragments adjacent to this correction; leave all other IDs.
cleanup=0;near=binary_dilation(removed,iterations=3)
for code in [5,8]:
    parts,count=label(new==code);counts=np.bincount(parts.ravel());single=np.flatnonzero(counts==1);single=single[single!=0]
    discard=np.isin(parts,single)&near;cleanup+=int(discard.sum());new[discard]=0;removed[discard]=True
for side,code in [('left',5),('right',8)]:
    remaining=int((new==code).sum());stats[side].update(after_texels=remaining,removed_texels=stats[side]['before_texels']-remaining,retained_percent=round(100*remaining/stats[side]['before_texels'],3))
assert np.all(np.isin(old[removed],[5,8])) and np.all(new[removed]==0)
assert np.array_equal(old[~removed],new[~removed])
assert all(s['retained_percent']>70 for s in stats.values()),'Excessive posterior loss; inspect before proceeding'
Image.fromarray(new).save(out/'textures/muscle-ids.png')
spec=json.loads((base/'regions.json').read_text());spec['uvSource']='../meshy-huit-zones/source-uv-binding.npz';spec['coverageSource']='../meshy-huit-zones/textures/uv-covered-pixels.png';spec['correction']={'referenceCommit':'8b723d9','onlyTransitions':[[5,0],[8,0]],'surfaceAssignment':'neutral / upper arm unassigned, no automatic triceps or lateral deltoid label','creaseCurveYZ':curve_metadata}
(out/'regions.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n')
for z in spec['zones']:
    target=out/'textures'/(z['id']+'.png')
    if z['code'] in [5,8]:Image.fromarray((new==z['code']).astype(np.uint8)*255).save(target)
    else:target.write_bytes((base/'textures'/target.name).read_bytes())
(out/'textures/masks-rgba-0.png').write_bytes((base/'textures/masks-rgba-0.png').read_bytes())
Image.fromarray(np.stack([(new==code).astype(np.uint8)*255 for code in range(5,9)],2)).save(out/'textures/masks-rgba-1.png')
color=np.array(Image.open(base/'textures/control-basecolor.png'));neutral=color[old==0][0];color[removed]=neutral;Image.fromarray(color).save(out/'textures/control-basecolor.png')
Image.fromarray(removed.astype(np.uint8)*255).save(out/'textures/changed-texels.png')
# Update only embedded PNG views, copying every geometry/UV buffer byte-for-byte.
raw,doc,binary=read_glb(base/'exports/meshy-eight-zones-control.glb');doc=copy.deepcopy(doc)
replacement={doc['images'][0]['bufferView']:(out/'textures/control-basecolor.png').read_bytes(),doc['images'][1]['bufferView']:(out/'textures/muscle-ids.png').read_bytes()}
rebuilt=bytearray()
for index,view in enumerate(doc['bufferViews']):
    data=replacement.get(index,binary[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']]);rebuilt.extend(b'\0'*((-len(rebuilt))%4));view['byteOffset']=len(rebuilt);view['byteLength']=len(data);rebuilt.extend(data)
doc['buffers'][0]['byteLength']=len(rebuilt);doc['nodes'][0]['extras']['posterior_mask_correction']='8b723d9 posterior lower boundary only; removed upper-arm tongue to neutral'
write_glb(out/'exports/meshy-eight-zones-control.glb',doc,bytes(rebuilt))
report={'referenceCommit':'8b723d9','only_id_transitions':[[5,0],[8,0]],'all_other_id_pixels_identical':True,'six_other_mask_files_byte_identical':True,'uvs_unchanged':True,'geometry_unchanged':True,'zones':stats,'curveYZ':curve_metadata,'changed_texels':int(removed.sum()),'isolated_border_texels_removed':cleanup,'control_glb_sha256':sha((out/'exports/meshy-eight-zones-control.glb').read_bytes()),'new_id_sha256':sha((out/'textures/muscle-ids.png').read_bytes())}
(out/'correction.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
# Prepare updated optional bounds, retaining all six other zone records exactly.
binding=json.loads((base/'region-binding.json').read_text());binding['boundFaces']='../meshy-huit-zones/exports/source-face-indices.u32';binding['cornerUV']='../meshy-huit-zones/exports/source-corner-uv.f32'
for zone in binding['zones']:
    if zone['code'] not in [5,8]:continue
    py,px=np.where((new==zone['code'])&coverage);p=world[py,px]
    zone.pop('faceCenterDiagnosticComponentCounts',None)
    center_uv=uv.mean(1);ij=np.clip(np.floor(center_uv*size).astype(int),0,size-1)
    zone['sourceFaceCenterSamples']=int((new[ij[:,1],ij[:,0]]==zone['code']).sum())
    zone.update(boundsSourceM={'min':p.min(0).tolist(),'max':p.max(0).tolist()},centerSourceM=p.mean(0).tolist(),boundsAreConservativeFaceExtent=False,boundsMethod='remaining ID texel surface samples after posterior correction')
(out/'region-binding.json').write_text(json.dumps(binding,ensure_ascii=False,indent=2)+'\n')

(out/'picking-witnesses.json').write_bytes((base/'picking-witnesses.json').read_bytes())
