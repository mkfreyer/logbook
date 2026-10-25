"""Rasterize camera-independent 3D regions into a padded, single-ID UV atlas."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt,label,binary_fill_holes
from glb_io import source,sha
from regions import Regions
from front_visibility import make_front_depth
root=Path(__file__).resolve().parents[2];out=root/'docs/m4c/meshy-huit-zones'
spec=json.loads((out/'regions.json').read_text())
_,v,n,f=source(root/'assets/models/meshy-e45e5d8.glb')
field=Regions(spec,make_front_depth(v,f))
binding=np.load(out/'source-uv-binding.npz');uv=binding['uv_blender'];domain=binding['domain'];size=spec['atlas']['width']
def raster(uv):
    labels=np.zeros((size,size),np.uint8);coverage=np.zeros((size,size),np.uint16)
    surface=np.zeros((size,size,3),np.float32);shared_edge_samples=0;overlap_samples=0;repair_faces=set()
    for face in np.flatnonzero(domain):
        t=uv[face].astype(float)*size-.5
        lo=np.maximum(np.ceil(t.min(0)).astype(int),0);hi=np.minimum(np.floor(t.max(0)).astype(int),size-1)
        if np.any(hi<lo):continue
        xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1));points=np.column_stack([xx.ravel(),yy.ravel()])
        matrix=np.column_stack([t[1]-t[0],t[2]-t[0]])
        if abs(np.linalg.det(matrix))<1e-12:continue
        ab=(points-t[0])@np.linalg.inv(matrix).T;w=np.column_stack([1-ab.sum(1),ab]);inside=(w>=-1e-8).all(1)
        points=points[inside];w=w[inside]
        if not len(w):continue
        x,y=points.T;position=w@v[f[face]];existing=coverage[y,x]>0
        if existing.any():
            distance=np.linalg.norm(position[existing]-surface[y[existing],x[existing]],axis=1)
            shared_edge_samples+=int((distance<1e-6).sum());overlap_samples+=int((distance>=1e-6).sum())
            if (distance>=1e-6).any():repair_faces.add(int(face))
        coverage[y,x]+=1;surface[y,x]=position;labels[y,x]=field.classify(position,w@n[f[face]])
    print('UV collision audit',shared_edge_samples,'shared-edge samples;',overlap_samples,'distinct surface overlaps',flush=True)
    return labels,coverage,shared_edge_samples,overlap_samples,repair_faces
labels,coverage,shared_edge_samples,overlap_samples,repair_faces=raster(uv)
repairs=json.loads((out/'uv-repair.json').read_text())['repaired_faces'] if (out/'uv-repair.json').exists() else []
if repair_faces:
    # Smart projection can fold a few tiny source triangles. Give only those
    # faces independent UV islands in the reserved lower margin. No geometry cut.
    for slot,face in enumerate(sorted(repair_faces)):
        p=v[f[face]].astype(float);a=p[1]-p[0];b=p[2]-p[0];length=np.linalg.norm(a)
        local=np.array([[0,0],[length,0],[np.dot(b,a)/length,np.linalg.norm(np.cross(a,b))/length]])
        local-=local.min(0);local*=24/max(local.max(),1e-12)
        new=(local+np.array([8+40*slot,8]))/size
        repairs.append({'sourceFace':face,'previousUV':uv[face].tolist(),'newUV':new.tolist()})
        uv[face]=new
    labels,coverage,shared_edge_samples,overlap_samples,remaining=raster(uv)
    assert not remaining and overlap_samples==0,'UV repair insufficient; stop'
    np.savez_compressed(out/'source-uv-binding.npz',uv_blender=uv,domain=domain)
(out/'uv-repair.json').write_text(json.dumps({'method':'UV-only isolated triangle islands in reserved margin; no geometry changes','repaired_faces':repairs,'remaining_uv_overlap_samples':overlap_samples},indent=2)+'\n')
# Context-only support border must remain neutral, never truncate a muscle.
assert not field.classify(v[f[~domain]].reshape(-1,3),n[f[~domain]].reshape(-1,3)).any()
distance,index=distance_transform_edt(coverage==0,return_indices=True)
padding=(coverage==0)&(distance<=4)
labels[padding]=labels[index[0][padding],index[1][padding]]
# Clean raster-only one-texel artifacts, never geometry or anatomical volume.
cleanup={'isolated_texels_reassigned':0,'covered_zero_hole_texels_filled':0,'scope':'Only one-pixel components and enclosed zero holes of at most four covered pixels in the 2048 atlas.'}
for code in range(1,9):
    parts,count=label(labels==code);counts=np.bincount(parts.ravel());small=np.flatnonzero(counts==1);small=small[small!=0]
    for y,x in np.argwhere(np.isin(parts,small)):
        neighbors=[labels[yy,xx] for yy,xx in [(y-1,x),(y+1,x),(y,x-1),(y,x+1)] if 0<=yy<size and 0<=xx<size]
        labels[y,x]=np.bincount(neighbors,minlength=9).argmax();cleanup['isolated_texels_reassigned']+=1
for code in range(1,9):
    holes=binary_fill_holes(labels==code)&(labels==0)&(coverage>0)
    parts,count=label(holes);counts=np.bincount(parts.ravel());small=np.flatnonzero((counts>0)&(counts<=4));small=small[small!=0]
    fill=np.isin(parts,small);labels[fill]=code;cleanup['covered_zero_hole_texels_filled']+=int(fill.sum())
(out/'mask-cleanup.json').write_text(json.dumps(cleanup,indent=2)+'\n')
def save(name,array):
    # GLB UVs are flipped from Blender UVs. PNG rows and glTF CPU lookup start at top.
    Image.fromarray(array[::-1]).save(out/'textures'/name)
save('muscle-ids.png',labels)
save('uv-covered-pixels.png',(coverage>0).astype(np.uint8)*255)
for zone in spec['zones']:save(zone['id']+'.png',(labels==zone['code']).astype(np.uint8)*255)
for group in range(2):save(f'masks-rgba-{group}.png',np.stack([(labels==i).astype(np.uint8)*255 for i in range(1+group*4,5+group*4)],axis=2))
def srgb(linear):return np.where(linear<=.0031308,linear*12.92,1.055*linear**(1/2.4)-.055)
neutral=np.round(srgb(np.array([.5,.52,.55]))*255).astype(np.uint8)
palette=np.array([neutral]+[[int(z['color'][i:i+2],16) for i in (1,3,5)] for z in spec['zones']],np.uint8)
save('control-basecolor.png',palette[labels])
# Save proposed source-space classes for geometric connectivity audit, not as primary IDs.
centroid_ids=field.classify(v[f].mean(1),n[f].mean(1));np.save(out/'face-samples.npy',centroid_ids)
report={'texture_resolution':[size,size],'uv_covered_texels':int((coverage>0).sum()),'uv_overlap_texels':overlap_samples,'shared_edge_texel_samples':shared_edge_samples,'padding_pixels':4,'label_codes':np.unique(labels).tolist(),'pixel_counts':{z['id']:int((labels==z['code']).sum()) for z in spec['zones']},'mask_png_sha256':sha((out/'textures/muscle-ids.png').read_bytes()),'geometry_changed':False,'procedure':'Continuous object-space contours sampled on each actual UV triangle. IDs exclusive, RGBA masks one-hot. Linear filtering used only on mask weights and colors, never ID values.'}
(out/'mask-bake.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
