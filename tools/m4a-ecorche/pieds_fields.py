"""Foot-only diagnostic construction; both body baselines have identical feet."""
import bpy,numpy as np,json,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import argparse,sys
parser=argparse.ArgumentParser()
parser.add_argument('--baseline',type=Path,required=True)
parser.add_argument('--work',type=Path,required=True)
parser.add_argument('--commit',default='d94297af21a05dacaa1f19a1ce64c7b64f447ea4')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
w=args.work.resolve();w.mkdir(parents=True,exist_ok=True)
prior=json.loads((args.baseline.parent/'finition.json').read_text())
source_sha=hashlib.sha256(args.baseline.read_bytes()).hexdigest()
assert source_sha==prior['master_sha256']
bpy.ops.wm.open_mainfile(filepath=str(args.baseline.resolve()),use_scripts=False)
scene=bpy.data.scenes[prior['scene']];bpy.context.window.scene=scene;scene.view_layers[0].update();graph=bpy.context.evaluated_depsgraph_get()
arrays={}
for ob in scene.objects:
 if ob.type!='MESH':continue
 ev=ob.evaluated_get(graph);m=ev.to_mesh()
 vv=np.array([ob.matrix_world@p.co for p in m.vertices])
 if vv[:,2].min()<.23:
  key=ob['asset_id'];arrays[key+'__v']=vv;arrays[key+'__f']=np.array([p.vertices[:]for p in m.polygons],np.int32)
  arrays[key+'__n']=np.array([n.vector[:]for n in m.corner_normals]).reshape(-1,3,3)
 ev.to_mesh_clear()
src=w/'parts.npz';np.savez_compressed(src,**arrays);a=np.load(src)
v,f=a['m2_c001.left__v'].copy(),a['m2_c001.left__f']
# Only the ankle collar of the foot is narrowed. Forefoot/toe proportions remain.
t=np.clip((v[:,2]-.085)/.06,0,1);t=t*t*(3-2*t)
center=np.array([.123,.083]);v[:,:2]=center+(v[:,:2]-center)*(1-.10*t[:,None])
h=.00125
origin=np.array([.046,-.166,-.0075]);axes=[origin[i]+np.arange(n)*h for i,n in enumerate([137,259,165])]
grid=np.stack(np.meshgrid(*axes,indexing='ij'),axis=-1);q=grid.reshape(-1,3)
def tree(v,f):
 vol=np.einsum('ij,ij->i',v[f[:,0]],np.cross(v[f[:,1]],v[f[:,2]])).sum()/6
 return BVHTree.FromPolygons(v.tolist(),f.tolist(),all_triangles=True),1 if vol>0 else -1

def signed(bvh,q,orientation):
 p=Vector(q);hit,n,idx,d=bvh.find_nearest(p)
 return d*(-1 if (p-hit).dot(n)*orientation<0 else 1)
def inside_grid(bt,lo,hi):
 inside=np.zeros(grid.shape[:3],bool)
 for ix,x in enumerate(axes[0]):
  if x<lo[0]-1e-6 or x>hi[0]+1e-6:continue
  for iy,y in enumerate(axes[1]):
   if y<lo[1]-1e-6 or y>hi[1]+1e-6:continue
   for jitter in [1e-8,3e-7,1.1e-6]:
    ray=Vector((x+jitter,y+1.7*jitter,-.03));hits=[]
    for count in range(128):
     hit=bt.ray_cast(ray,Vector((0,0,1)),1.0)[0]
     if hit is None:break
     hits.append(hit.z);ray=hit+Vector((0,0,1e-7))
    if len(hits)%2==0:break
   assert len(hits)%2==0, ('Odd scanline',ix,iy,hits)
   inside[ix,iy]=(np.searchsorted(hits,axes[2],side='right')%2)==1
 return inside.reshape(-1)
ft,orientation=tree(v,f)
reuse=False
if (w/'fields.npz').exists() and (w/'tapered-foot.npz').exists():
 cached=np.load(w/'tapered-foot.npz');previous=np.load(w/'fields.npz')
 reuse=(np.array_equal(cached['v'],v) and np.array_equal(cached['f'],f)
        and previous['foot'].shape==grid.shape[:3] and float(previous['step'])==h
        and np.array_equal(previous['origin'],origin))
if reuse:
 foot=np.abs(previous['foot']).reshape(-1).copy()
else:
 foot=np.empty(len(q),np.float32)
 for start in range(0,len(q),500000):
  end=min(start+500000,len(q));foot[start:end]=[ft.find_nearest(Vector(p))[3]for p in q[start:end]]
  print('FOOT_DISTANCE',end,'/',len(q),flush=True)
inside=inside_grid(ft,v.min(0),v.max(0));foot[inside]*=-1
print('FOOT_SIGNED_PARITY',int(inside.sum()),flush=True)
active=(q[:,2]>.073)&(foot>-.012)&(foot<.029)
body=np.full(len(q),.25,np.float32);records=[];arrays={}
for k in a.files:
 if not k.endswith('.left__f') or k.startswith('m2_c001.'):continue
 key=k[:-3];vv,ff=a[key+'__v'],a[k]
 if vv[:,2].max()<.16:continue
 unique,inv=np.unique(vv.astype(np.float32),axis=0,return_inverse=True);wf=inv[ff]
 edges=np.sort(np.concatenate([wf[:,[0,1]],wf[:,[1,2]],wf[:,[2,0]]]),axis=1);_,counts=np.unique(edges,axis=0,return_counts=True)
 if not np.all(counts==2):continue
 lo,hi=vv.min(0),vv.max(0)
 indexes=np.flatnonzero(active&np.all(q>=lo-.008,axis=1)&np.all(q<=hi+.008,axis=1))
 if not len(indexes):continue
 bt,orientation=tree(vv,ff)
 values=np.array([bt.find_nearest(Vector(q[i]))[3]for i in indexes],np.float32)
 inside=inside_grid(bt,lo,hi);values[inside[indexes]]*=-1
 body[indexes]=np.minimum(body[indexes],values)
 arrays[key+'__v'],arrays[key+'__f'],arrays[key+'__n']=vv,ff,a[key+'__n']
 records.append(key);print('CONTACT',key,len(indexes),flush=True)
shape=grid.shape[:3];foot,body=foot.reshape(shape),body.reshape(shape)
radius=.0045
blend=np.maximum(radius-np.abs(body-foot),0)/radius
union=np.minimum(body,foot)-radius*.25*blend**2
alpha=np.clip((grid[...,2]-.075)/.03,0,1);alpha=alpha**2*(3-2*alpha)
field=(1-alpha)*foot+alpha*union
np.savez_compressed(w/'fields.npz',field=field,foot=foot,body=body,origin=origin,step=h,radius=radius)
np.savez_compressed(w/'sources.npz',**arrays)
np.savez_compressed(w/'tapered-foot.npz',v=v,f=f)
(w/'construction.json').write_text(json.dumps({'baseline_commit':args.commit,'baseline_blend_sha256':source_sha,'source_scene':scene.name,'foot_id':'m2_c001.left','step_m':h,'ankle_radial_reduction':.10,'ankle_taper_z_m':[.085,.145],'ankle_center_xy_m':center.tolist(),'contact_radius_m':radius,'reference_objects':records,'parts_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'field_builder_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'inside_classification':'Vertical ray parity on closed meshes; nearest-distance magnitudes' },indent=2))
print('FIELDS_READY',shape,flush=True)
