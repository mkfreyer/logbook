"""Read source glTF attributes and recover geometric components, never muscle names."""
import json,struct,hashlib
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
SOURCE_SHA='137e2e80bdcf9c87ff49ab32cb5de70f8de542870c78a7d5170e8743d241a73a'
def sha(data):return hashlib.sha256(data).hexdigest()
def source_parts(file):
 raw=Path(file).read_bytes();assert sha(raw)==SOURCE_SHA;n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);blob=raw[28+n:]
 def ac(i,width):
  a=doc['accessors'][i];b=doc['bufferViews'][a['bufferView']];dtype={5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']]
  return np.frombuffer(blob,dtype=dtype,count=a['count']*width,offset=b.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,width)
 world={}
 def visit(i,parent):
  node=doc['nodes'][i];local=np.array(node.get('matrix',np.eye(4).T.ravel().tolist())).reshape(4,4).T
  assert not any(k in node for k in ['translation','rotation','scale']);m=parent@local
  if 'mesh'in node:world[node['mesh']]=m
  for c in node.get('children',[]):visit(c,m)
 for i in doc['scenes'][doc.get('scene',0)]['nodes']:visit(i,np.eye(4))
 arrays=[]
 for i,m in enumerate(doc['meshes']):
  p=m['primitives'][0];v=ac(p['attributes']['POSITION'],3);points=np.c_[v,np.ones(len(v))]@world[i].T
  points=points[:,[0,2,1]];points[:,1]*=-1
  normal=ac(p['attributes']['NORMAL'],3).astype(float)@np.linalg.inv(world[i][:3,:3]);normal=normal[:,[0,2,1]];normal[:,1]*=-1;normal/=np.linalg.norm(normal,axis=1)[:,None]
  arrays.append({'v':points,'n':normal,'c':ac(p['attributes']['COLOR_0'],4),'f':ac(p['indices'],1).reshape(-1,3),'mat':p['material']})
 allv=np.concatenate([a['v'] for a in arrays]);lo=allv.min(0);hi=allv.max(0);origin=np.array([(lo[0]+hi[0])/2,(lo[1]+hi[1])/2,lo[2]]);scale=1.8/(hi[2]-lo[2])
 parts=[]
 for material in range(len(doc['materials'])):
  selected=[a for a in arrays if a['mat']==material];vs=[];cs=[];ns=[];fs=[];offset=0
  for a in selected:vs.append(a['v']);cs.append(a['c']);ns.append(a['n']);fs.append(a['f']+offset);offset+=len(a['v'])
  v=np.concatenate(vs);c=np.concatenate(cs);normal=np.concatenate(ns);f=np.concatenate(fs)
  unique,inverse=np.unique(v,axis=0,return_inverse=True);tri=inverse[f];edges=np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]);graph=coo_matrix((np.ones(len(edges),bool),(edges[:,0],edges[:,1])),shape=(len(unique),len(unique))).tocsr();count,labels=connected_components(graph,directed=False)
  face_component=labels[tri[:,0]]
  for component in range(count):
   faces=f[face_component==component];ids,remap=np.unique(faces,return_inverse=True)
   if not len(ids):continue
   points=(v[ids]-origin)*scale
   parts.append({'id':f'm{material}_c{component:03d}','component':component,'material':material,'v':points,'n':normal[ids],'c':c[ids],'f':remap.reshape(-1,3).astype(np.int32)})
 return doc,parts,{'normalization_height_m':1.8,'source_world_origin':origin.tolist(),'uniform_scale':float(scale),'source_vertices':sum(len(a['v'])for a in arrays),'source_triangles':sum(len(a['f'])for a in arrays),'source_components':len(parts)}
