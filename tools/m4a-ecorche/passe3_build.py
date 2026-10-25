"""Third anatomical refinement: anchored fan forms and volume-preserving fairing.

Keeps the entire prior asset and object IDs. Rebuilds shoulder/chest topology locally. Changes only
shoulder, chest, medial trapezius and selected lateral-thorax surface pieces.
"""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);baseline=a.baseline.resolve();root=a.output.resolve();root.mkdir(parents=True,exist_ok=True)
def sha(file):return hashlib.sha256(file.read_bytes()).hexdigest()
assert sha(baseline)=='55f4c47e0b125fb1abbb9fe89fae544b4aa02520077565819b19a7bbe9bec435'
prior=json.loads((baseline.parent/'passe2.json').read_text());plane=prior['median_plane_x_m'];bpy.ops.wm.open_mainfile(filepath=str(baseline),use_scripts=False)
source=bpy.data.scenes['05_PASSE2_NEUTRE'];bpy.context.window.scene=source;source.view_layers[0].update();graph=bpy.context.evaluated_depsgraph_get();snapshots={};source_objects={}
for ob in source.objects:
 if ob.type!='MESH':continue
 mesh=bpy.data.meshes.new_from_object(ob.evaluated_get(graph),preserve_all_data_layers=True,depsgraph=graph);v=np.array([ob.matrix_world@q.co for q in mesh.vertices]);f=np.array([q.vertices[:]for q in mesh.polygons],int);snapshots[ob['asset_id']]=(v,f,mesh);source_objects[ob['asset_id']]=ob
before=bpy.data.scenes.new('07_AVANT_PASSE3');after=bpy.data.scenes.new('08_PASSE3_NEUTRE');material=bpy.data.materials['PASSE2_MAT_NEUTRE'].copy();material.name='PASSE3_MAT_NEUTRE'
def smooth(t):t=np.clip(t,0,1);return t*t*(3-2*t)
def volume(v,f):return float(np.einsum('ij,ij->i',v[f[:,0]],np.cross(v[f[:,1]],v[f[:,2]])).sum()/6)
def topology(v,f):
 u,inverse=np.unique(v,axis=0,return_inverse=True);tri=inverse[f];cross=np.cross(u[tri[:,1]]-u[tri[:,0]],u[tri[:,2]]-u[tri[:,0]]);normal=np.zeros_like(u);area=np.zeros(len(u))
 for k in range(3):np.add.at(normal,tri[:,k],cross);np.add.at(area,tri[:,k],np.linalg.norm(cross,axis=1)/6)
 normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-12)
 edges=np.unique(np.sort(np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]),axis=1),axis=0);edges=np.vstack([edges,edges[:,::-1]]);weight=1/np.maximum(np.linalg.norm(u[edges[:,0]]-u[edges[:,1]],axis=1),.001);degree=np.bincount(edges[:,0],weights=weight,minlength=len(u))
 return u,tri,inverse,normal,area,edges,weight,degree
def average(q,e,w,degree):return np.column_stack([np.bincount(e[:,0],weights=w*q[e[:,1],k],minlength=len(q))/degree for k in range(q.shape[1])])
def fair(u,e,w,degree,mask,steps,cap):
 q=u.copy()
 for _ in range(steps):q+=.36*mask[:,None]*(average(q,e,w,degree)-q)
 delta=q-u;length=np.linalg.norm(delta,axis=1);return delta*np.minimum(1,cap/np.maximum(length,1e-12))[:,None]
def conserve(u,q,tri,normal,mask,goal):
 lo=-.008;hi=.008
 for _ in range(40):
  mid=(lo+hi)/2;trial=q+normal*(mask*mid)[:,None]
  if (volume(trial,tri)-goal)*np.sign(goal)>0:hi=mid
  else:lo=mid
 return q+normal*(mask*((lo+hi)/2))[:,None]
def reconstruct_surface(v,f,mesh):
 # Voxel reconstruction only for the two deltoids and two pectorals. It
 # removes source self-folds before broad anatomical shape edits.
 worker=bpy.data.objects.new('P3_RECONSTRUCTION_TEMP',mesh.copy());before.collection.objects.link(worker);bpy.context.window.scene=before;before.view_layers[0].objects.active=worker;worker.select_set(True)
 worker.data.remesh_voxel_size=.003;worker.data.remesh_voxel_adaptivity=0;worker.data.use_remesh_preserve_volume=True;worker.data.use_remesh_preserve_attributes=False
 bpy.ops.object.voxel_remesh()
 import bmesh
 bm=bmesh.new();bm.from_mesh(worker.data);bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(worker.data);bm.free()
 # Retain only the resolution useful for this local shape cleanup.
 decimate=worker.modifiers.new('P3_RESOLUTION_LOCALE','DECIMATE');decimate.ratio=.40;decimate.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=decimate.name)
 refined=worker.data;refined.name='PASSE3_SURFACE_RECONSTRUITE';points=np.array([q.co[:]for q in refined.vertices]);faces=np.array([q.vertices[:]for q in refined.polygons],int)
 # Reproject native colors for authoring only. Neutral validation does not use them.
 tree=BVHTree.FromPolygons(v.tolist(),f.tolist(),all_triangles=True);colors=np.array([q.color[:]for q in mesh.color_attributes['Color'].data]);col=[]
 for point in points:
  hit=tree.find_nearest(Vector(point));col.append(colors[f[hit[2]]].mean(0))
 for attr in list(refined.color_attributes):refined.color_attributes.remove(attr)
 attr=refined.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT');attr.data.foreach_set('color',np.asarray(col,dtype=np.float32).ravel())
 refined.materials.clear();refined.materials.append(material)
 for poly in refined.polygons:poly.use_smooth=True
 refined.update();bpy.data.objects.remove(worker,do_unlink=True);return points,faces,refined,None
insertion=np.array([-.243,.080,1.296])
origins=np.array([[-.125,.014,1.482],[-.210,.060,1.500],[-.130,.128,1.465]])
bellies=np.array([[-.250,.026,1.405],[-.274,.075,1.405],[-.252,.128,1.398]])
controls=2*bellies-.5*(origins+insertion);landmarks={'order':['anterior_clavicular','middle_acromial','posterior_scapular'],'right_origins_m':origins.tolist(),'right_belly_landmarks_m':bellies.tolist(),'right_common_insertion_m':insertion.tolist(),'status':'Source-guided authoring landmarks, not medically certified attachments.'}
targets=['deltoid.right','pectoralis_major.right','trapezius.right','m0_c050.right','m0_c042.right','m0_c044.right','m0_c046.right','m0_c053.right','rectus_abdominis.right'];changes={};weights_by_name={};records=[];pec_tree=None;contact_counts={};refined_meshes={}
for name in targets:
 original_v,original_f,original_mesh=snapshots[name];v,f,mesh=original_v,original_f,original_mesh;loop_positions=None
 if name in ['deltoid.right','pectoralis_major.right']:v,f,mesh,loop_positions=reconstruct_surface(v,f,mesh);refined_meshes[name]=mesh
 u,tri,inverse,normal,area,edges,edge_weight,degree=topology(v,f);mask=np.ones(len(u));delta=np.zeros_like(u);notes=[]
 if name in refined_meshes:
  for _ in range(4):normal=normal+average(normal,edges,edge_weight,degree);normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-12)
 if loop_positions is not None:
  ordered=np.zeros_like(u);np.add.at(ordered,inverse,loop_positions);ordered/=np.bincount(inverse)[:,None];delta+=ordered-u
 if name=='deltoid.right':
  t=np.clip((u[:,2]-1.286)/.217,0,1);axis_x=-.241+.057*t;axis_y=.080-.010*t;radial=np.column_stack([u[:,0]-axis_x,u[:,1]-axis_y,np.zeros(len(u))]);radial/=np.maximum(np.linalg.norm(radial,axis=1)[:,None],1e-12);theta=np.arctan2(u[:,1]-axis_y,axis_x-u[:,0])
  envelope=smooth((t-.08)/.22)*smooth((.95-t)/.18);outer=smooth((np.einsum('ij,ij->i',normal,radial)-.08)/.65);width_guard=np.ones_like(t)
  mask=envelope*outer;delta+=fair(u+delta,edges,edge_weight,degree,mask,12,.0015)
  angles=[];tau=np.linspace(0,1,100)
  for origin,control in zip(origins,controls):
   curve=(1-tau[:,None])**2*origin+2*(1-tau[:,None])*tau[:,None]*control+tau[:,None]**2*insertion
   x=np.interp(u[:,2],curve[::-1,2],curve[::-1,0]);y=np.interp(u[:,2],curve[::-1,2],curve[::-1,1]);angles.append(np.arctan2(y-axis_y,axis_x-x))
  angles=np.column_stack(angles);width=np.array([.31,.38,.40]);raw=np.exp(-.5*((theta[:,None]-angles)/width)**2);stable=np.exp(-.5*((theta[:,None]-angles)/width)**2-np.max(-.5*((theta[:,None]-angles)/width)**2,axis=1)[:,None]);weights_by_name[name]=stable/stable.sum(1)[:,None]
  profile=(raw*np.array([.98,1.12,.84])*np.exp(-.5*((t[:,None]-np.array([.61,.55,.57]))/.30)**2)).sum(1)
  field_mask=mask*width_guard;mean=float(np.sum(area*field_mask*profile)/np.maximum(np.sum(area*field_mask),1e-12))
  delta+=radial*(.0110*(profile-mean)*field_mask)[:,None]
  mask=field_mask;notes=['Source-guided three fan paths, with different belly widths and orientations.','Broad shape redistribution after removal of residual sculpt ridges; no incised separation or detached patch.','Shoulder volume constrained, distal insertion and proximal rim attenuated.']
 elif name=='pectoralis_major.right':
  front=smooth((-normal[:,1]-.04)/.65);underside=smooth((-normal[:,2]-.15)/.60)
  attachment=smooth((u[:,0]+.225)/.035)*smooth((plane-u[:,0]-.002)/.014)*smooth((1.500-u[:,2])/.025)
  mask=attachment*np.maximum(front,.65*underside);delta+=fair(u,edges,edge_weight,degree,mask,34,.0032)
  notes=['Stronger bounded curvature fairing of front and inferior edge; volume restored.','Sternal separation and humeral attachment protected.']
 elif name=='trapezius.right':
  d=plane-u[:,0];zmask=smooth((u[:,2]-1.27)/.07)*smooth((1.705-u[:,2])/.035);back=smooth((u[:,1]-.075)/.030)
  delta[:,0]+=.92*d*np.exp(-(d/.011)**2)*zmask*back
  delta[:,1]+=.0035*np.exp(-(d/.019)**2)*zmask*back*smooth((normal[:,1]-.05)/.65)
  local=np.maximum(np.exp(-(d/.045)**2),np.exp(-((u[:,0]+.135)/.035)**2-((u[:,2]-1.46)/.07)**2))*zmask*back
  delta+=fair(u,edges,edge_weight,degree,local,16,.0014)
  mask=zmask*back*smooth((normal[:,1]-.02)/.7);notes=['Near-midline contact tightened and posterior banks rounded, including upper cervical transition.','Small local surface fairing, with total trap volume constrained.']
 elif name=='rectus_abdominis.right':
  mask=smooth((-normal[:,1]-.15)/.7)*smooth((u[:,2]-.96)/.05)*smooth((1.34-u[:,2])/.025)
  delta+=fair(u,edges,edge_weight,degree,mask,16,.0013);notes=['Bounded smoothing of small anterior sculpt irregularities, abdominal blocks retained.']
 else:
  center=u.mean(0);_,basis=np.linalg.eigh((u-center).T@(u-center));axis=basis[:,-1];along=(u-center)@axis;t=(along-along.min())/(along.max()-along.min())
  mask=smooth((t-.025)/.14)*smooth((.975-t)/.14)
  if name=='m0_c053.right':mask*=smooth((u[:,2]-1.12)/.09)
  delta+=fair(u,edges,edge_weight,degree,mask,20,.0017)
  counts={'gap_vertices_approached':0,'penetration_vertices_retracted':0}
  if pec_tree is not None:
   for i,point in enumerate(u+delta):
    hit=pec_tree.find_nearest(Vector(point),.010)
    if hit[0]is None or hit[1].z>-.20 or point[2]<1.28:continue
    nearest=np.array(hit[0]);n=np.array(hit[1]);signed=float(np.dot(point-nearest,n));distance=float(hit[3]);factor=float(smooth((point[2]-1.27)/.04))
    if signed>=0:
     if distance<.0010:continue
     correction=(nearest+n*.0007-point)*factor;counts['gap_vertices_approached']+=1
    else:correction=(nearest+n*.0007-point)*factor;counts['penetration_vertices_retracted']+=1
    length=np.linalg.norm(correction);delta[i]+=correction*min(1,.0022/max(length,1e-12))
  contact_counts[name]=counts;notes=['Rounded lateral surface ridges and upper contacts toward the pectoral underside.','Original source piece IDs retained; no invented anatomical name for these pieces.']
 if name=='deltoid.right':delta+=fair(u+delta,edges,edge_weight,degree,mask,12,.0012)
 q=conserve(u,u+delta,tri,normal,mask,volume(original_v,original_f))
 # The medial plane remains a boundary between separate paired objects.
 if name=='trapezius.right':q[:,0]=np.minimum(q[:,0],plane-.000025)
 cap=.006 if name=='deltoid.right'else .0045 if name in ['pectoralis_major.right','trapezius.right']else .003
 delta=q-u;length=np.linalg.norm(delta,axis=1);delta*=np.minimum(1,cap/np.maximum(length,1e-12))[:,None]
 old_cross=np.cross(u[tri[:,1]]-u[tri[:,0]],u[tri[:,2]]-u[tri[:,0]]);valid=np.linalg.norm(old_cross,axis=1)>1e-12;correction=np.ones(len(u));protected=set()
 if name in ['deltoid.right','pectoralis_major.right']:
  # Use a smooth global limiter instead of tiny per-vertex safety islands.
  # Legitimate removal of an old concave sculpt fold can rotate its normal.
  base_tree=BVHTree.FromPolygons(u.tolist(),tri.tolist(),all_triangles=True)
  base_contacts=[(i,j)for i,j in base_tree.overlap(base_tree)if i<j and not np.isin(tri[i],tri[j]).any()]
  for attempt in range(15):
   q=u+delta*correction[:,None];cross=np.cross(q[tri[:,1]]-q[tri[:,0]],q[tri[:,2]]-q[tri[:,0]])
   bad=valid&(np.linalg.norm(cross,axis=1)<.06*np.linalg.norm(old_cross,axis=1))
   self_tree=BVHTree.FromPolygons(q.tolist(),tri.tolist(),all_triangles=True)
   contacts=[(i,j)for i,j in self_tree.overlap(self_tree)if i<j and not np.isin(tri[i],tri[j]).any()]
   print('REFINED_CONTACT_CHECK',name,attempt,'source',len(base_contacts),'after',len(contacts),'degenerate',int(bad.sum()),flush=True)
   if not bad.any()and len(contacts)<=len(base_contacts):break
   correction*=.90
  else:raise RuntimeError('Refined shoulder has unresolved collapse or nonadjacent self-contact')
  protected.update(np.flatnonzero(bad).tolist())
 for _ in range(0 if name in ['deltoid.right','pectoralis_major.right']else 36):
  q=u+delta*correction[:,None];new_cross=np.cross(q[tri[:,1]]-q[tri[:,0]],q[tri[:,2]]-q[tri[:,0]]);bad=valid&(np.einsum('ij,ij->i',old_cross,new_cross)<=0)
  if not bad.any():break
  ids=np.unique(tri[bad]);protected.update(np.flatnonzero(bad).tolist());correction[ids]*=.20;correction=np.minimum(correction,(correction+average(correction[:,None],edges,edge_weight,degree)[:,0])/2)
 else:
  if name not in ['deltoid.right','pectoralis_major.right']:raise RuntimeError('Unsafe source folds: '+name)
 q=u+delta*correction[:,None];target=q[inverse];changes[name]=target;ratio=volume(target,f)/volume(original_v,original_f)
 assert abs(ratio-1)<.020,(name,'volume change',ratio)
 records.append({'asset_id':name,'max_displacement_m':float(np.linalg.norm(target-v,axis=1).max()),'mean_displacement_m':float(np.linalg.norm(target-v,axis=1).mean()),'volume_before_m3':volume(original_v,original_f),'volume_after_m3':volume(target,f),'volume_ratio':ratio,'bbox_before_m':np.ptp(original_v,axis=0).tolist(),'bbox_after_m':np.ptp(target,axis=0).tolist(),'protected_source_fold_faces':len(protected),'displacement_reference':'reconstructed_surface'if name in refined_meshes else 'source_surface','source_triangles':len(original_f),'final_triangles':len(f),'notes':notes})
 left=name[:-5]+'left';reflection=target.copy();reflection[:,0]=2*plane-reflection[:,0];changes[left]=reflection
 if name in refined_meshes:
  mirrored=mesh.copy()
  for vert in mirrored.vertices:vert.co.x=2*plane-vert.co.x
  # Reverse face winding after reflection; preserve point attributes.
  import bmesh
  bm=bmesh.new();bm.from_mesh(mirrored);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(mirrored);bm.free();refined_meshes[left]=mirrored
 if name in weights_by_name:weights_by_name[name]=weights_by_name[name][inverse];weights_by_name[left]=weights_by_name[name]
 if name=='pectoralis_major.right':pec_tree=BVHTree.FromPolygons(target.tolist(),f.tolist(),all_triangles=True)
for name,(v,f,mesh)in snapshots.items():
 old=bpy.data.objects.new('P3_BASE__'+name,mesh);before.collection.objects.link(old)
 for slot in old.material_slots:slot.link='OBJECT';slot.material=material
 final_mesh=refined_meshes[name]if name in refined_meshes else mesh.copy()if name in changes else mesh
 ob=bpy.data.objects.new('P3__'+name,final_mesh);after.collection.objects.link(ob);ob['asset_id']=name
 for key in ['source_piece_id','side','region_hint','anatomical_label_validated']:
  if key in source_objects[name]:ob[key]=source_objects[name][key]
 for slot in ob.material_slots:slot.link='OBJECT';slot.material=material
 if name in changes:
  ob.shape_key_add(name='SURFACE_RECONSTRUITE'if name in refined_meshes else 'AVANT_PASSE3');key=ob.shape_key_add(name='CORRECTIONS_PASSE3');key.data.foreach_set('co',changes[name].astype(np.float32).ravel());key.value=1
 if name in weights_by_name:
  for i,label in enumerate(['DELT_ANTERIEUR','DELT_MOYEN','DELT_POSTERIEUR']):
   group=ob.vertex_groups.new(name=label)
   for j,w in enumerate(weights_by_name[name][:,i]):
    if w>1e-4:group.add([j],float(w),'REPLACE')
  ob['deltoid_regions']='Three continuous shape regions guided by source landmarks; overlapping authoring weights, not certified medical segmentation.'
metadata={'baseline_commit':'0297e9bc19c7adf8bbb3a369ab7691cd295821be','baseline_blend_sha256':sha(baseline),'source_asset':prior['source_asset'],'source_sha256':prior['source_sha256'],'median_plane_x_m':plane,'objects':len(snapshots),'before_triangles':sum(len(x[1])for x in snapshots.values()),'triangles':sum(len(o.data.polygons)for o in after.objects if o.type=='MESH'),'new_triangles':sum(len(o.data.polygons)for o in after.objects if o.type=='MESH')-sum(len(x[1])for x in snapshots.values()),'refined_objects':sorted(refined_meshes),'surface_reconstruction_voxel_size_m':.003,'local_decimation_ratio':.40,'changed_objects':sorted(changes),'unchanged_objects':len(snapshots)-len(changes),'records_right':records,'deltoid_landmarks':landmarks,'lateral_contact_adjustment_counts':contact_counts,'baseline_max_shoulder_reflection_error_m':float(np.abs(snapshots['deltoid.left'][0]-np.column_stack([2*plane-snapshots['deltoid.right'][0][:,0],snapshots['deltoid.right'][0][:,1:]])).max()),'builder_sha256':sha(Path(__file__)),'limitations':['Source-guided authoring, not independent medical anatomy validation.','Separate muscle meshes retained; complete semantic segmentation is not delivered.','No application integration or mobile performance claim.']}
(root/'passe3.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n');bpy.data.texts.new('PASSE3_CORRECTIONS.json').write(json.dumps(metadata,ensure_ascii=False,indent=2));bpy.context.window.scene=after;bpy.ops.wm.save_as_mainfile(filepath=str(root/'ecorche-passe3.blend'),compress=True);print('PASSE3_BUILT',json.dumps(metadata),flush=True)
