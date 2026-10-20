"""Exact piecewise-linear triangle clipping, then independent watertight shells.
No image masks, face-centroid labels, hidden duplicate body or voxel remeshing.
Run with Python + NumPy; Blender consumes the resulting temporary NPZ.
"""
from pathlib import Path
import json,sys
import numpy as np
from mesh_io import load_glb,sha,EXPECTED_SHA
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/m4a/segmente'

def curve(points, steps=12):
    p=np.asarray(points,float);out=[]
    for i in range(len(p)):
        a,b,c,d=p[(i-1)%len(p)],p[i],p[(i+1)%len(p)],p[(i+2)%len(p)]
        for t in np.arange(steps)/steps:
            out.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
    return np.array(out)

def distance(p, contour):
    # Signed Euclidean distance to a periodic Catmull-Rom construction curve.
    yes=np.zeros(len(p),bool);dist=np.full(len(p),1e6)
    for a,b in zip(contour,np.roll(contour,-1,axis=0)):
        ab=b-a;ap=p-a;t=np.clip(ap@ab/(ab@ab),0,1)
        dist=np.minimum(dist,np.linalg.norm(ap-t[:,None]*ab,axis=1))
        if abs(ab[1])>1e-12:
            yes^=((a[1]>p[:,1])!=(b[1]>p[:,1]))&(p[:,0]<ab[0]*(p[:,1]-a[1])/ab[1]+a[0])
    return dist*np.where(yes,1,-1)

def clip(poly,k,positive):
    out=[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
        da,db=a[6+k],b[6+k];ina=da>=0 if positive else da<=0;inb=db>=0 if positive else db<=0
        if ina:out.append(a)
        if ina!=inb:out.append(a+(b-a)*(da/(da-db)))
    return out

def pack(polys):
    v=[];n=[];f=[];lookup={}
    for poly in polys:
        ids=[]
        for p in poly:
            key=tuple(np.round(p[:3],10))
            if key not in lookup:lookup[key]=len(v);v.append(p[:3]);n.append(p[3:6])
            ids.append(lookup[key])
        for k in range(1,len(ids)-1):
            tri=[ids[0],ids[k],ids[k+1]]
            if len(set(tri))==3 and np.linalg.norm(np.cross(v[tri[1]]-v[tri[0]],v[tri[2]]-v[tri[0]]))>1e-14:f.append(tri)
    v=np.array(v);n=np.array(n);n/=np.linalg.norm(n,axis=1)[:,None]
    return v,n,np.array(f,dtype=np.int32)

def stats(v,f):
    edges=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1)
    e,c=np.unique(edges,axis=0,return_counts=True)
    parent=np.arange(len(v))
    def find(a):
        while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
        return a
    for a,b in e:parent[find(a)]=find(b)
    area=np.linalg.norm(np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]),axis=1)*.5
    return dict(vertices=len(v),triangles=len(f),boundary_edges=int((c==1).sum()),nonmanifold_edges=int((c>2).sum()),components=len({find(i) for i in range(len(v))}),area=float(area.sum()),min_triangle_area=float(area.min()))

def main():
    raw,_,v,f=load_glb(OUT/'source/meshy-original.glb');assert sha(raw)==EXPECTED_SHA
    nv=np.zeros_like(v,dtype=float);fn=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]])
    for k in range(3):np.add.at(nv,f[:,k],fn)
    nv/=np.linalg.norm(nv,axis=1)[:,None]
    cfg=json.loads((ROOT/'tools/m4a-segmente/contours.json').read_text())
    fields=[];names=[]
    for side,sign in [('left',1),('right',-1)]:
        p=v.copy();p[:,0]*=sign
        for name in ['pectoralis','deltoid','biceps','triceps']:
            row=cfg[name];d=distance(p[:,:2],curve(row['front']))
            if 'rear' in row:
                back=distance(p[:,:2],curve(row['rear']));w=np.clip((p[:,2]+.065)/.13,0,1);d=d*w+back*(1-w)
            if name=='deltoid':
                # A single smooth 3D shoulder-cap boundary, avoiding front/back
                # projection folds. Its tip sits on the lateral humeral insertion.
                medial=.5*((.21-p[:,0])+np.sqrt((.21-p[:,0])**2+.003**2))
                floor=.451+2.0*medial+.12*((p[:,2]+.045)/.115)**2
                d=np.minimum(p[:,1]-floor,(1-((p[:,0]-.212)/.102)**2-((p[:,1]-.55)/.125)**2)*.04)
            if name=='pectoralis':d=np.minimum(d,p[:,2]-.025)
            if name=='biceps':d=np.minimum(d,p[:,2]-(-.075+.06*(p[:,1]-.3)))
            if name=='triceps':d=np.minimum(d,(-.065+.06*(p[:,1]-.3))-p[:,2])
            fields.append(d);names.append(name+'.'+side)
    # Global upper-body crop. The full-body source is archived only, never exported.
    fields.append(v[:,1]-.12)
    data=np.column_stack([v,nv,np.array(fields).T]);pieces=[[] for _ in names];support=[];baseline=[]
    for tri in f:
        poly=clip([data[i] for i in tri],8,True)
        if len(poly)<3:continue
        baseline.append(poly)
        for k in range(8):
            if len(poly)<3:break
            selected=clip(poly,k,True)
            if len(selected)>=3:pieces[k].append(selected)
            poly=clip(poly,k,False)
        if len(poly)>=3:support.append(poly)
    # Reassign disconnected contour spill to context, without deleting source area.
    cleanup=[]
    for k,polys in enumerate(pieces):
        pv,pn,pf=pack(polys);adj=[[] for _ in pv]
        for i,tri in enumerate(pf):
            for vid in tri:adj[vid].append(i)
        todo=set(range(len(pf)));parts=[]
        while todo:
            stack=[todo.pop()];part=[]
            while stack:
                i=stack.pop();part.append(i)
                for vid in pf[i]:
                    for j in adj[vid]:
                        if j in todo:todo.remove(j);stack.append(j)
            parts.append(part)
        parts.sort(key=len,reverse=True);data6=np.column_stack([pv,pn])
        pieces[k]=[[data6[j] for j in pf[i]] for i in parts[0]]
        spill=[i for part in parts[1:] for i in part]
        support.extend([[data6[j] for j in pf[i]] for i in spill])
        cleanup.append(dict(id=names[k],reassigned_triangles=len(spill)))
    result={};records=[]
    for name,polys in zip(names+['support','baseline'],pieces+[support,baseline]):
        pv,pn,pf=pack(polys);s=stats(pv,pf)
        result[name+'_v']=pv;result[name+'_n']=pn;result[name+'_f']=pf
        records.append(dict(id=name,**s));print(name,s,flush=True)
    baseline_area=records[-1]['area'];partition_area=sum(r['area'] for r in records[:-1])
    assert abs(baseline_area-partition_area)<1e-7
    for r in records[:8]:assert r['components']==1 and r['nonmanifold_edges']==0,r
    np.savez_compressed(sys.argv[1],**result)
    (OUT/'partition-audit.json').write_text(json.dumps(dict(source_sha256=EXPECTED_SHA,crop_source_y=.12,curve='periodic Catmull-Rom, 12 samples/segment',area_error=abs(baseline_area-partition_area),parts=records,cleanup=cleanup),indent=2)+'\n')
if __name__=='__main__':main()
