"""Stitch ID footprints across actual shared mesh edges; no geometry writes."""
import numpy as np
from scipy.ndimage import label

def stitched(ids,uv,faces):
 size=len(ids);components=np.zeros(ids.shape,np.int32);parents=[0];offset=0
 for code in range(1,9):
  parts,n=label(ids==code);m=parts>0;components[m]=parts[m]+offset;parents.extend(range(offset+1,offset+n+1));offset+=n
 def find(i):
  while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
  return i
 edges=np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]);eu=np.concatenate([uv[:,[0,1]],uv[:,[1,2]],uv[:,[2,0]]]);swap=edges[:,0]>edges[:,1];eu[swap]=eu[swap,::-1];edges=np.sort(edges,axis=1);order=np.lexsort((edges[:,1],edges[:,0]));edges,eu=edges[order],eu[order]
 starts=np.r_[0,1+np.flatnonzero(np.any(edges[1:]!=edges[:-1],axis=1))];count=np.diff(np.r_[starts,len(edges)]);starts=starts[count==2];a,b=eu[starts],eu[starts+1];seam=np.any(np.abs(a-b)>1e-7,axis=(1,2));a,b=a[seam],b[seam]
 for t in np.linspace(.001,.999,33):
  x=np.clip(((a[:,0]*(1-t)+a[:,1]*t)*size).astype(int),0,size-1);y=np.clip(((b[:,0]*(1-t)+b[:,1]*t)*size).astype(int),0,size-1);ca,cb=ids[x[:,1],x[:,0]],ids[y[:,1],y[:,0]];ok=(ca==cb)&(ca>0)
  pairs=np.unique(np.column_stack([components[x[ok,1],x[ok,0]],components[y[ok,1],y[ok,0]]]),axis=0)
  for p,q in pairs:
   p,q=find(int(p)),find(int(q))
   if p!=q:parents[max(p,q)]=min(p,q)
 mapping=np.array([find(i) for i in range(len(parents))]);return mapping[components]
