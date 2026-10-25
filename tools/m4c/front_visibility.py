"""Conservative object-space front depth, not a viewport paint projection.

Prevents pectoral labels on deeper axillary surfaces behind the visible belly.
The deltoid fields wrap in full 3D and do not use this front-surface restriction.
"""
import numpy as np
from scipy.ndimage import maximum_filter

def make_front_depth(v,f):
    size=np.array([2048,1024]);lo=np.array([-.235,.39]);span=np.array([.47,.255]);depth=np.full(tuple(size[::-1]),-np.inf,np.float32)
    xyz=v[f].astype(float);use=((xyz[:,:,:2].max(1)>=lo)&(xyz[:,:,:2].min(1)<=lo+span)).all(1)
    for triangle in xyz[use]:
        t=(triangle[:,:2]-lo)/span*size-.5
        low=np.maximum(np.ceil(t.min(0)).astype(int),0);high=np.minimum(np.floor(t.max(0)).astype(int),size-1)
        if np.any(high<low):continue
        m=np.column_stack([t[1]-t[0],t[2]-t[0]])
        if abs(np.linalg.det(m))<1e-10:continue
        xx,yy=np.meshgrid(np.arange(low[0],high[0]+1),np.arange(low[1],high[1]+1));points=np.column_stack([xx.ravel(),yy.ravel()])
        ab=(points-t[0])@np.linalg.inv(m).T;w=np.column_stack([1-ab.sum(1),ab]);inside=(w>=-1e-8).all(1)
        x,y=points[inside].T;z=w[inside]@triangle[:,2];depth[y,x]=np.maximum(depth[y,x],z)
    # Small conservative footprint avoids sampling a subpixel hole in a thin fold.
    depth=maximum_filter(depth,size=3)
    def visible(points,tolerance=.006):
        index=np.clip(np.floor((points[:,:2]-lo)/span*size).astype(int),0,size-1)
        front=depth[index[:,1],index[:,0]]
        return points[:,2]>=front-tolerance
    return visible
