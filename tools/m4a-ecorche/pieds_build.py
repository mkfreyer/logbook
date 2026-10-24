import bpy,json,numpy as np,argparse,sys,hashlib,os
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
parser=argparse.ArgumentParser();parser.add_argument('--baseline',type=Path,required=True);parser.add_argument('--work',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);w=args.work;root=args.output.resolve();root.mkdir(parents=True,exist_ok=True)
a=np.load(w/'surface.npz');sources=np.load(w/'sources.npz');fields=np.load(w/'fields.npz');info=json.loads((w/'construction.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(args.baseline)==info['baseline_blend_sha256']
bpy.ops.wm.open_mainfile(filepath=str(args.baseline.resolve()),use_scripts=False)
old=bpy.data.scenes[info['source_scene']];s=bpy.data.scenes.new('26_FINITION_PIEDS');s.use_fake_user=True;s.world=old.world
for o in old.objects:
 if o.get('asset_id') not in ['m2_c001.left','m2_c001.right']:s.collection.objects.link(o)
bpy.context.window.scene=s
m=bpy.data.meshes.new('PIED_GAUCHE');m.from_pydata(a['v'].tolist(),[],a['f'].tolist());m.update()
o=bpy.data.objects.new('PIED_TRAVAIL',m);s.collection.objects.link(o)
# QEM simplification, with strong importance on the contact perimeter.
f=a['f'];edges=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1);u,c=np.unique(edges,axis=0,return_counts=True);bd=np.unique(u[c==1]);vg=o.vertex_groups.new(name='RACCORD_PROTEGE');vg.add(bd.tolist(),1,'REPLACE')
mod=o.modifiers.new('REDUCTION_PIED','DECIMATE');mod.ratio=min(1,16000/len(f));mod.use_collapse_triangulate=True;mod.vertex_group=vg.name;mod.vertex_group_factor=1000;mod.invert_vertex_group=True
s.view_layers[0].update();g=bpy.context.evaluated_depsgraph_get();mesh=bpy.data.meshes.new_from_object(o.evaluated_get(g),depsgraph=g);bpy.data.objects.remove(o,do_unlink=True)
v=np.array([p.co[:]for p in mesh.vertices]);f=np.array([p.vertices[:]for p in mesh.polygons],np.int32)
print('DECIMATED',len(v),len(f),flush=True)
# Trilinear sampling without a SciPy dependency inside Blender.
def sample(grid,points):
 coords=np.clip((points-fields['origin'])/float(fields['step']),0,np.array(grid.shape)-1.000001);ind=np.floor(coords).astype(int);t=coords-ind;out=np.zeros(len(points))
 for i in range(2):
  for j in range(2):
   for k in range(2):out+=np.prod(np.where([i,j,k],t,1-t),axis=1)*grid[ind[:,0]+i,ind[:,1]+j,ind[:,2]+k]
 return out
fd=sample(fields['foot'],v);weight=np.clip((fd-.005)/.004,0,1);weight=weight**2*(3-2*weight)
trees=[]
for key in sources.files:
 if not key.endswith('__f'):continue
 vv,ff,nn=sources[key[:-3]+'__v'],sources[key],sources[key[:-3]+'__n'];bt=BVHTree.FromPolygons(vv.tolist(),ff.tolist(),all_triangles=True);trees.append((bt,vv,ff,nn))
fn=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]);norm=np.zeros_like(v)
for j in range(3):np.add.at(norm,f[:,j],fn)
norm/=np.maximum(np.linalg.norm(norm,axis=1,keepdims=True),1e-12)
# Near the buried collar, transfer the smooth normal from the nearest leg face.
for i in np.flatnonzero(weight>0):
 q=Vector(v[i]);best=None
 for bt,vv,ff,nn in trees:
  hit,n,index,d=bt.find_nearest(q)
  if best is None or d<best[0]:
   tri=vv[ff[index]];ab,ac=tri[1]-tri[0],tri[2]-tri[0];rel=np.array(hit)-tri[0]
   xy=np.linalg.lstsq(np.column_stack([ab,ac]),rel,rcond=None)[0];bary=np.array([1-xy.sum(),*xy]);shade=bary@nn[index];shade/=max(np.linalg.norm(shade),1e-12);best=(d,shade)
 # Match source shading only close to the actual contact. Copying a tendon
 # normal onto a free foot surface would imprint an artificial triangular mark.
 near=np.clip(best[0]/.0004,0,1);near=1-near*near*(3-2*near)
 amount=weight[i]*near
 norm[i]=(1-amount)*norm[i]+amount*best[1]
norm/=np.maximum(np.linalg.norm(norm,axis=1,keepdims=True),1e-12)
plane=.002114987923242599
for side in ['left','right']:
 vv=v.copy();ff=f.copy();nn=norm.copy()
 if side=='right':vv[:,0]=2*plane-vv[:,0];ff=ff[:,::-1];nn[:,0]*=-1
 m=bpy.data.meshes.new('FINITION_PIED_'+side);m.from_pydata(vv.tolist(),[],ff.tolist());m.update()
 for p in m.polygons:p.use_smooth=True
 m.normals_split_custom_set([nn[l.vertex_index]for l in m.loops]);original=next(o for o in old.objects if o.get('asset_id')=='m2_c001.'+side)
 for slot in original.material_slots:m.materials.append(slot.material)
 ob=bpy.data.objects.new('PIEDS__m2_c001.'+side,m);s.collection.objects.link(ob)
 for k in original.keys():ob[k]=original[k]
 np.savez_compressed(root/('foot-'+side+'.npz'),v=vv,f=ff,normals=nn)
meta={
 'baseline_commit':info['baseline_commit'],'baseline_master':os.path.relpath(args.baseline.resolve(),root),
 'baseline_blend_sha256':sha(args.baseline),'source_scene':old.name,'scene':s.name,
 'baseline_glb':os.path.relpath(args.baseline.parent/json.loads((args.baseline.parent/'export.json').read_text())['file'],root),
 'master':'ecorche-finition-pieds.blend','changed_objects':['m2_c001.left','m2_c001.right'],
 'retained_original_objects':297,'retained_original_vertices_moved':0,
 'construction':info,'extraction':json.loads((w/'extraction.json').read_text()),
 'target_triangles_per_foot':16000,'actual_triangles_per_foot':len(f),'vertices_per_foot':len(v),
 'median_plane_x_m':plane,'builder_sha256':sha(Path(__file__)),
 'normal_transfer_source_distance_limit_m':.0004,
 'method':'Foot-only ankle taper, local implicit union to unchanged leg anatomy, mild field fairing, QEM simplification with protected contact borders, smooth neutral shading. Symmetric mirror of the left reconstruction.',
 'topology':'Two replacement foot meshes. Contact perimeters deliberately buried in unchanged leg surfaces; not a welded whole-body skin.'}
bpy.data.texts.new('FINITION_PIEDS.json').write(json.dumps(meta,indent=2))
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(root/meta['master']),compress=True)
meta['master_sha256']=sha(root/meta['master']);(root/'finition.json').write_text(json.dumps(meta,indent=2)+'\n')
print('SAVED_FEET',len(v),len(f),flush=True)
