"""Reconstruct bilateral superficial anatomy from the more complete right side.

Source components remain distinct authoring objects. Belly deformations taper
to zero at both longitudinal ends and are limited against source neighbors.
No generic spheres, remeshing, full muscle-name mapping or application code.
"""
import argparse,json,sys,hashlib
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prepared',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);out=a.output.resolve();prepared=a.prepared.resolve();manifest=json.loads((prepared/'parts.json').read_text());data=np.load(prepared/'parts.npz')
bpy.ops.wm.read_factory_settings(use_empty=True);original=bpy.context.scene;original.name='00_SOURCE_ASYMETRIQUE';base=bpy.data.scenes.new('01_RECONSTRUCTION_SYMETRIQUE');final=bpy.data.scenes.new('02_ATHLETIQUE')
asset=manifest['source_asset'];allv=np.concatenate([data[f'{i}_v']for i in range(len(manifest['parts']))]);head=allv[(allv[:,2]>1.63)&(allv[:,2]<1.72)];plane=float((head[:,0].min()+head[:,0].max())/2)
verts=[];faces=[];offset=0
for i in range(len(manifest['parts'])):
 v=data[f'{i}_v'];f=data[f'{i}_f'];verts.extend(v.tolist());faces.extend((f+offset).tolist());offset+=len(v)
tree=BVHTree.FromPolygons(verts,faces,all_triangles=True);del verts,faces
materials=[]
for i,rough in enumerate([.4529344512,.9346417683,.6419588415]):
 m=bpy.data.materials.new(f'ORIGINAL_material_{i}');m.use_nodes=True;n=m.node_tree.nodes['Principled BSDF'];n.inputs['Roughness'].default_value=rough;n.inputs['Metallic'].default_value=.0687881098 if i==0 else 0
 color=m.node_tree.nodes.new('ShaderNodeVertexColor');color.layer_name='Color';m.node_tree.links.new(color.outputs['Color'],n.inputs['Base Color']);materials.append(m)
silver=bpy.data.materials.new('PRESENTATION_BLEU_ARGENTE');silver.use_nodes=True;n=silver.node_tree.nodes['Principled BSDF'];n.inputs['Base Color'].default_value=(.19,.28,.42,1);n.inputs['Metallic'].default_value=.12;n.inputs['Roughness'].default_value=.43;n.inputs['Coat Weight'].default_value=.06
known={17:('deltoid',.18),18:('pectoralis_major',.20),19:('latissimus_dorsi',.16),24:('trapezius',.14),81:('rectus_abdominis',.06)}
records=[];discarded=[];collision_limits=0
def smooth(t):t=np.clip(t,0,1);return t*t*(3-2*t)
def make(name,v,f,c,material,scene):
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(v.tolist(),[],f.tolist());mesh.update();mesh.materials.append(material)
 color=mesh.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT');color.data.foreach_set('color',np.asarray(c,dtype=np.float32).ravel())
 for p in mesh.polygons:p.use_smooth=True
 ob=bpy.data.objects.new(name,mesh);scene.collection.objects.link(ob);return ob
def mesh_arrays(ob):return np.array([v.co[:]for v in ob.data.vertices]),np.array([p.vertices[:]for p in ob.data.polygons],int),np.array([d.color[:]for d in ob.data.color_attributes['Color'].data])
def gain_for(row,v,f):
 lo=v.min(0);hi=v.max(0);center=(lo+hi)/2
 if row['material']!=0:return ('structure_originale',0)
 if row['component']in known:return known[row['component']]
 if hi[2]>1.53:return ('piece_source',0)
 if len(f)<500:return ('piece_source',0)
 if center[0]<-.16 and 1.06<center[2]<1.42 and hi[2]-lo[2]>.12:return ('bras',.18)
 if center[0]<-.20 and .85<center[2]<1.13 and hi[2]-lo[2]>.10:return ('avant_bras',.10)
 if center[1]>.065 and .83<center[2]<1.07:return ('fessier',.12)
 if .51<center[2]<.86 and hi[2]-lo[2]>.13:return ('cuisse',.18)
 if .17<center[2]<.47 and hi[2]-lo[2]>.13:return ('mollet',.16)
 if .97<center[2]<1.25 and hi[0]-lo[0]<.17:return ('abdomen_obliques',.06)
 return ('piece_source',0)
def bulge(v,f,c,n,gain,is_deltoid):
 global collision_limits
 if gain==0:return v.copy(),{'gain_radial_max':0,'deplacement_max_m':0,'vertices_changed':0}
 center=v.mean(0);cov=(v-center).T@(v-center);_,basis=np.linalg.eigh(cov);axis=basis[:,-1];long=(v-center)@axis;minimum=long.min();maximum=long.max();t=(long-minimum)/(maximum-minimum)
 radial=(v-center)-long[:,None]*axis;weight=smooth((t-.12)/.18)*smooth((.88-t)/.18)
 redness=np.clip((c[:,0]-(c[:,1]+c[:,2])/2)/.12,0,1);weight*=redness
 if is_deltoid:
  lateral=np.array([-1.,0,0]);lateral-=axis*np.dot(lateral,axis);lateral/=np.linalg.norm(lateral)
  front=np.array([0.,-1,0]);front-=axis*np.dot(front,axis);front-=lateral*np.dot(front,lateral);front/=np.linalg.norm(front)
  angle=np.arctan2(radial@front,radial@lateral)
  lobes=sum(np.exp(-.5*((angle-cen)/.30)**2)for cen in [-1.0,0,1.0]);weight*=.70+.30*np.minimum(lobes,1)
 delta=gain*weight[:,None]*radial;length=np.linalg.norm(delta,axis=1);direction=delta/np.maximum(length[:,None],1e-12)
 # Keep concave folds/contact surfaces conservative rather than inflating them.
 outward=np.clip((np.einsum('ij,ij->i',direction,n)-.10)/.65,0,1);limit=outward.copy()
 for i in np.flatnonzero((length>1e-6)&(outward>0)):
  hit=tree.ray_cast(Vector(v[i]+direction[i]*.0001),Vector(direction[i]),float(length[i]+.001))
  if hit[2] is not None:
   cap=max(0,float(hit[3])-.001)/length[i]
   if cap<limit[i]:limit[i]=cap;collision_limits+=1
 # Smooth the limiter only downward; never override a clearance constraint.
 edge=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]);edge=np.vstack([edge,edge[:,::-1]]);degree=np.bincount(edge[:,0],minlength=len(v))
 for _ in range(2):
  total=np.bincount(edge[:,0],weights=limit[edge[:,1]],minlength=len(v));average=(total+limit)/(degree+1);limit=np.minimum(limit,average)
 # Source points duplicated at normal/color/buffer seams must move identically.
 _,inverse=np.unique(v,axis=0,return_inverse=True);groups=int(inverse.max())+1
 scalar=gain*weight*limit;group_min=np.full(groups,np.inf);np.minimum.at(group_min,inverse,scalar)
 delta=group_min[inverse,None]*radial;old_cross=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]);valid=np.linalg.norm(old_cross,axis=1)>1e-12
 correction=np.ones(len(v));protected=set();fallback=False
 # Numerical safety only: protect thin source folds locally, without a new visual variant.
 for attempt in range(24):
  result=v+delta*correction[:,None];new_cross=np.cross(result[f[:,1]]-result[f[:,0]],result[f[:,2]]-result[f[:,0]])
  bad=valid&(np.einsum('ij,ij->i',old_cross,new_cross)<=0)
  if not bad.any():break
  ids=np.unique(f[bad]);protected.update(ids.tolist());correction[ids]*=.2
  total=np.bincount(edge[:,0],weights=correction[edge[:,1]],minlength=len(v));correction=np.minimum(correction,(total+correction)/(degree+1))
  group_min=np.full(groups,np.inf);np.minimum.at(group_min,inverse,correction);correction=group_min[inverse]
 else:correction[:]=0;fallback=True
 delta*=correction[:,None];result=v+delta
 new_cross=np.cross(result[f[:,1]]-result[f[:,0]],result[f[:,2]]-result[f[:,0]])
 assert np.all(np.einsum('ij,ij->i',old_cross,new_cross)[valid]>0)
 return result,{'gain_radial_max':gain,'deplacement_max_m':float(np.linalg.norm(delta,axis=1).max()),'vertices_changed':int((np.linalg.norm(delta,axis=1)>1e-7).sum()),'end_anchor_bands_unchanged':True,'thin_fold_vertices_protected':len(protected),'retouch_cancelled_to_protect_source':fallback}
for i,row in enumerate(manifest['parts']):
 v=data[f'{i}_v'].copy();f=data[f'{i}_f'];c=data[f'{i}_c'];normal=data[f'{i}_n'];mid=float(np.median(v[:,0]));lo=v[:,0].min();hi=v[:,0].max()
 source=make('SOURCE__'+row['id'],v,f,c,materials[row['material']],original)
 # Balanced structures crossing the median plane are reconstructed by bisect/mirror.
 both=(lo<plane-.006 and hi>plane+.006 and np.mean(v[:,0]<plane)>.18 and np.mean(v[:,0]>plane)>.18)
 # Preserve portions crossing the reference half even when their parent
 # component lies mainly on the dissected side (e.g. median aponeurosis).
 central=both or (lo<plane<hi and abs(mid-plane)<.005) or (mid>plane and lo<plane-1e-6)
 if not central and mid>plane:discarded.append(row['id']);continue
 name,gain=gain_for(row,v,f)
 if central:
  ob=make(row['id']+'__CENTRAL',v,f,c,materials[row['material']],base)
  bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,plane_co=(plane,0,0),plane_no=(1,0,0),clear_outer=True,clear_inner=False)
  for vert in bm.verts:
   if abs(vert.co.x-plane)<1e-6:vert.co.x=plane
   vert.co.x-=plane
  bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bm.to_mesh(ob.data);bm.free()
  if not ob.data.polygons:bpy.data.objects.remove(ob,do_unlink=True);continue
  bpy.context.window.scene=base;base.view_layers[0].objects.active=ob;ob.select_set(True)
  mod=ob.modifiers.new('Reconstitution_median','MIRROR');mod.use_clip=True;mod.use_mirror_merge=True;mod.merge_threshold=1e-5;bpy.ops.object.modifier_apply(modifier=mod.name)
  for vert in ob.data.vertices:vert.co.x+=plane
  ob.data.update();bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
  q,faces,color=mesh_arrays(ob);after=make(ob.name+'__ATHLETIQUE',q,faces,color,materials[row['material']],final)
  after['source_piece_id']=row['id'];after['anatomical_label_validated']=False
  records.append({'source_id':row['id'],'object':after.name,'side':'central','region':'structure_mediane','gain_radial_max':0,'deplacement_max_m':0,'vertices_changed':0,'triangles':len(faces)})
 else:
  target,stats=bulge(v,f,c,normal,gain,name=='deltoid')
  # Retain a small median groove between paired muscles. The map is monotone.
  if row['material']==0 and hi>plane-.02:
   for points in [v,target]:points[:,0]=plane-.002-.004*np.logaddexp(0,(plane-.002-points[:,0])/.004)
  for side in ['right','left']:
   q=v.copy();tgt=target.copy();faces=f.copy()
   if side=='left':q[:,0]=2*plane-q[:,0];tgt[:,0]=2*plane-tgt[:,0];faces=faces[:,::-1]
   tag=(name+'.'+side) if row['material']==0 and row['component']in known else (row['id']+'.'+side)
   original_part=make(tag+'__BASE',q,faces,c,materials[row['material']],base);after=make(tag,q,faces,c,materials[row['material']],final)
   after.shape_key_add(name='BASE_RECONSTITUEE');key=after.shape_key_add(name='ATHLETIQUE');key.data.foreach_set('co',tgt.astype(np.float32).ravel());key.value=1
   after['source_piece_id']=row['id'];after['side']=side;after['region_hint']=name;after['anatomical_label_validated']=False
   records.append({'source_id':row['id'],'object':after.name,'side':side,'region':name,**stats,'triangles':len(faces)})
for scene in [original,base,final]:
 for o in scene.objects:
  if o.type=='MESH':
   for slot in o.material_slots:slot.link='OBJECT';slot.material=silver
 scene['asset_scope']='Anatomical authoring master, not final mobile segmentation.'
metadata={'source_asset':asset,'source_sha256':'137e2e80bdcf9c87ff49ab32cb5de70f8de542870c78a7d5170e8743d241a73a','normalization':manifest['normalization'],'median_plane_x_m':plane,'reference_side':'anatomical right, more complete superficial anatomy','discarded_deep_or_incomplete_left_source_components':discarded,'source_components':len(manifest['parts']),'final_objects':len(records),'final_triangles':sum(r['triangles']for r in records),'neighbor_clearance_constraints_applied':collision_limits,'records':records,'builder_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'limitations':['Geometric piece IDs are not a validated muscle-name map.','The deltoid remains one source muscle piece per side; three fiber portions are not three independent validated segments.','Symmetry and source-derived insertions are geometric reconstructions, not medical certification.']}
out.mkdir(parents=True,exist_ok=True);(out/'construction.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
bpy.data.texts.new('PROVENANCE_ET_CONSTRUCTION.json').write(json.dumps(metadata,ensure_ascii=False,indent=2));bpy.context.window.scene=final
bpy.ops.wm.save_as_mainfile(filepath=str(out/'ecorche-athletique.blend'),compress=True)
print('RECONSTRUCTION_BUILT',len(records),'objects',metadata['final_triangles'],'triangles',flush=True)
