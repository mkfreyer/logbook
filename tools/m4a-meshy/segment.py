"""Label exactly three surface regions on the original Meshy triangle ordering."""
import argparse,json
from pathlib import Path
import numpy as np
from mesh_io import EXPECTED_SHA,components,load_glb,neighbors,patch_topology,sha
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--contours',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
raw,doc,v,ix=load_glb(a.source);assert sha(raw)==EXPECTED_SHA
annotation=json.loads(a.contours.read_text());centers=v[ix].mean(1);adj=neighbors(ix);labels=np.zeros(len(ix),dtype=np.uint8);records=[]
def inside(points,front,rear=None,blend=None):
    front=np.array(front);back=front if rear is None else np.array(rear)
    w=np.ones(len(points)) if blend is None else np.clip((points[:,2]-blend[0])/(blend[1]-blend[0]),0,1)
    yes=np.zeros(len(points),dtype=bool);x,y=points[:,0],points[:,1]
    for i in range(len(front)):
        j=(i-1)%len(front);a0=back[i]+w[:,None]*(front[i]-back[i]);b0=back[j]+w[:,None]*(front[j]-back[j])
        dx=b0[:,0]-a0[:,0];dy=b0[:,1]-a0[:,1];d=np.where(abs(dy)<1e-12,1e-12,dy)
        yes^=((a0[:,1]>y)!=(b0[:,1]>y))&(x<dx*(y-a0[:,1])/d+a0[:,0])
    return yes
for row in annotation['regions']:
    mask=inside(centers,row['front_xy'],row.get('rear_xy'),row.get('blend_source_z'))
    if 'min_source_z' in row:mask&=centers[:,2]>=row['min_source_z']
    mask&=labels==0;parts=components(mask,adj);assert parts
    removed=int(mask.sum()-len(parts[0]));mask[:]=False;mask[parts[0]]=True
    background=components(~mask,adj);filled=0
    for hole in background[1:]:
        assert not np.any(labels[hole]);mask[hole]=True;filled+=len(hole)
    stats=patch_topology(mask,ix,adj);assert stats['single_disk'],(row['id'],stats)
    labels[mask]=row['value'];records.append({'value':row['value'],'id':row['id'],**stats,'island_faces_unassigned':removed,'hole_faces_filled':filled})
file=a.output/'triangle-regions.u8';file.write_bytes(labels.tobytes())
meta={'schema_version':1,'source_file':a.source.name,'source_sha256':sha(raw),
 'binding':{'node_index':0,'mesh_index':0,'primitive_index':0,'topology':'TRIANGLES','triangle_count':len(ix),'vertex_count':len(v),
 'position_buffer_sha256':sha(v.astype('<f4').tobytes()),'index_buffer_sha256':sha(ix.astype('<u4').tobytes()),
 'triangle_index_rule':'Zero-based ordinal of each consecutive index triplet of source mesh 0, primitive 0. No reordering.'},
 'labels':{'file':file.name,'dtype':'uint8','byte_length':len(labels),'sha256':sha(file.read_bytes()),'unassigned_value':0},
 'regions':records,'contours_sha256':sha(a.contours.read_bytes()),'method':'Manually traced source-view contours, front-surface depth gate, interpolated front/rear deltoid boundary; triangle-centroid classification and connected disk cleanup. Visual anatomical labels, not medical segmentation.',
 'geometry_changes':False,'face_order_changed':False,'mobile_performance_validated':False}
(a.output/'regions.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(records,ensure_ascii=False))
