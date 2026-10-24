"""Read the supplied, uncompressed single-primitive Meshy GLB without reindexing."""
import hashlib
import json
import struct
from pathlib import Path
import numpy as np

EXPECTED_SHA='9fab861a65407e69b9401bec077bf7b40f58d36404e80bad9db6147f24320a14'

def sha(data):return hashlib.sha256(data).hexdigest()

def load_glb(path):
    raw=Path(path).read_bytes();magic,version,total=struct.unpack_from('<4sII',raw)
    assert magic==b'glTF' and version==2 and total==len(raw)
    offset=12;chunks={}
    while offset<total:
        size,kind=struct.unpack_from('<II',raw,offset);offset+=8
        assert kind not in chunks and offset+size<=total
        chunks[kind]=raw[offset:offset+size];offset+=size
    doc=json.loads(chunks[0x4e4f534a]);binary=chunks[0x004e4942]
    assert len(doc['meshes'])==1 and len(doc['meshes'][0]['primitives'])==1
    assert len(doc['nodes'])==1 and doc['nodes'][0]['mesh']==0
    assert doc['nodes'][0].get('matrix',[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1])==[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]
    primitive=doc['meshes'][0]['primitives'][0];assert primitive.get('mode',4)==4
    assert 'extensions' not in primitive and set(primitive['attributes'])=={'POSITION'}
    def read(index,dtype,width):
        accessor=doc['accessors'][index];view=doc['bufferViews'][accessor['bufferView']]
        assert not accessor.get('sparse') and not view.get('byteStride') and view.get('buffer',0)==0
        start=view.get('byteOffset',0)+accessor.get('byteOffset',0)
        return np.frombuffer(binary,dtype=dtype,count=accessor['count']*width,offset=start).copy()
    assert doc['accessors'][primitive['attributes']['POSITION']]['componentType']==5126
    assert doc['accessors'][primitive['indices']]['componentType']==5125
    positions=read(primitive['attributes']['POSITION'],'<f4',3).reshape(-1,3)
    triangles=read(primitive['indices'],'<u4',1).reshape(-1,3)
    assert np.isfinite(positions).all() and triangles.max()<len(positions)
    return raw,doc,positions,triangles

def neighbors(triangles):
    n=len(triangles);edges=np.sort(np.concatenate([triangles[:,[0,1]],triangles[:,[1,2]],triangles[:,[2,0]]]),axis=1)
    owners=np.tile(np.arange(n),3);order=np.lexsort((edges[:,1],edges[:,0]));edges=edges[order];owners=owners[order]
    starts=np.r_[0,1+np.flatnonzero(np.any(edges[1:]!=edges[:-1],axis=1))];ends=np.r_[starts[1:],len(edges)]
    counts=ends-starts;assert np.all(counts==2),'Source not a closed edge-manifold mesh; investigate before topology cleanup'
    pairs=np.column_stack([owners[starts],owners[starts+1]])
    adj=[[] for _ in range(n)]
    for a,b in pairs:adj[int(a)].append(int(b));adj[int(b)].append(int(a))
    return adj

def components(mask,adj):
    todo=set(np.flatnonzero(mask).tolist());out=[]
    while todo:
        stack=[min(todo)];todo.remove(stack[0]);part=[]
        while stack:
            face=stack.pop();part.append(face)
            for other in adj[face]:
                if other in todo:todo.remove(other);stack.append(other)
        out.append(part)
    return sorted(out,key=lambda c:(-len(c),min(c)))

def patch_topology(mask,triangles,adj):
    faces=triangles[mask];edges=np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1)
    _,count=np.unique(edges,axis=0,return_counts=True);euler=len(np.unique(faces))-len(count)+len(faces)
    return {'faces':int(mask.sum()),'connected_components':len(components(mask,adj)),
        'boundary_edges':int((count==1).sum()),'euler_characteristic':int(euler),
        'single_disk':bool(euler==1 and len(components(mask,adj))==1 and np.all(count<=2))}
