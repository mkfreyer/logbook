"""Stitch texture components across real source UV seams; not triangle labels."""
import json,argparse
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import label,binary_fill_holes
from glb_io import source
root=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser();parser.add_argument('--asset-dir',type=Path,default=root/'docs/m4c/meshy-huit-zones');out=parser.parse_args().asset_dir.resolve()
spec=json.loads((out/'regions.json').read_text())
_,v,n,f=source(root/'assets/models/meshy-e45e5d8.glb');uv=np.load(out/spec.get('uvSource','source-uv-binding.npz'))['uv_blender'].copy();uv[:,:,1]=1-uv[:,:,1]
coverage=np.array(Image.open(out/spec.get('coverageSource','textures/uv-covered-pixels.png')))>0
ids=np.array(Image.open(out/'textures/muscle-ids.png'));spec=json.loads((out/'regions.json').read_text());size=ids.shape[0]
components=np.zeros(ids.shape,np.int32);parent=[0];records=[];offset=0
for zone in spec['zones']:
    mask=ids==zone['code'];parts,count=label(mask)
    components[mask]=parts[mask]+offset
    counts=np.bincount(parts.ravel())[1:];component_ids=list(range(offset+1,offset+1+count));parent.extend(component_ids)
    records.append({'id':zone['id'],'uv_components_before_seam_stitch':count,'components':component_ids,'pixels':counts.tolist(),'enclosed_zero_pixels_in_UV':int(((binary_fill_holes(mask)&~mask)&(ids==0)&coverage).sum())});offset+=count

def find(i):
    while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
    return i

def union(a,b):
    a,b=find(int(a)),find(int(b))
    if a!=b:parent[max(a,b)]=min(a,b)
edges=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]);edgeuv=np.concatenate([uv[:,[0,1]],uv[:,[1,2]],uv[:,[2,0]]])
swap=edges[:,0]>edges[:,1];edgeuv[swap]=edgeuv[swap,::-1];edges=np.sort(edges,axis=1)
order=np.lexsort((edges[:,1],edges[:,0]));edges=edges[order];edgeuv=edgeuv[order]
starts=np.r_[0,1+np.flatnonzero(np.any(edges[1:]!=edges[:-1],axis=1))];counts=np.diff(np.r_[starts,len(edges)]);starts=starts[counts==2]
a=edgeuv[starts];b=edgeuv[starts+1];seam=np.any(np.abs(a-b)>1e-7,axis=(1,2));a=a[seam];b=b[seam]
for t in np.linspace(.001,.999,33):
    aa=np.minimum(((a[:,0]*(1-t)+a[:,1]*t)*size).astype(int),size-1);bb=np.minimum(((b[:,0]*(1-t)+b[:,1]*t)*size).astype(int),size-1)
    ia=ids[aa[:,1],aa[:,0]];ib=ids[bb[:,1],bb[:,0]];good=(ia==ib)&(ia>0)
    pairs=np.unique(np.column_stack([components[aa[good,1],aa[good,0]],components[bb[good,1],bb[good,0]]]),axis=0)
    for c,d in pairs:union(c,d)
for r in records:
    sizes={}
    for c,pixels in zip(r.pop('components'),r.pop('pixels')):sizes[find(c)]=sizes.get(find(c),0)+pixels
    r['stitched_surface_component_pixel_counts']=sorted(sizes.values(),reverse=True)
    centers=uv.mean(1);q=np.clip((centers*size).astype(int),0,size-1);cs=components[q[:,1],q[:,0]]
    details=[]
    for component,count in sorted(sizes.items(),key=lambda item:-item[1]):
        selected=np.array([i for i,c in enumerate(cs) if c and find(int(c))==component],int)
        details.append({'root':component,'pixels':count,'sourceFaceCenterCount':len(selected),'firstSourceFaces':selected[:12].tolist(),'sourceCenterBounds':{'min':v[f[selected]].mean(1).min(0).tolist(),'max':v[f[selected]].mean(1).max(0).tolist()} if len(selected) else None})
    r['component_diagnostics']=details
report={'method':'4-connected ID pixel components, stitched at 33 samples on every real shared source edge with distinct corner UVs. Includes 4px island padding. This is finite sampling, not a medical/anatomical proof.','uv_seam_edges_tested':len(a),'zones':records}
report['status']='passed' if all(len(z['stitched_surface_component_pixel_counts'])==1 and z['enclosed_zero_pixels_in_UV']==0 for z in records) else 'failed'
(out/'continuity-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)

assert report['status']=='passed','Disconnected or perforated atlas footprint; inspect before publication'
