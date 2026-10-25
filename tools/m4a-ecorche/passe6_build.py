"""Pass six: replace only the deltoids on the validated pass-five mannequin."""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--surface',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.output.resolve();root.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(a.baseline)=='926cadf61c4608c096cbf84e0c50ff0785eb7c5568d613206dfe57d695e4a54d'
prior=json.loads((a.baseline.parent/'passe5.json').read_text());plane=prior['median_plane_x_m'];bpy.ops.wm.open_mainfile(filepath=str(a.baseline.resolve()),use_scripts=False)
def snapshot(name):
 s=bpy.data.scenes[name];bpy.context.window.scene=s;s.view_layers[0].update();g=bpy.context.evaluated_depsgraph_get();result={}
 for ob in s.objects:
  if ob.type!='MESH':continue
  m=bpy.data.meshes.new_from_object(ob.evaluated_get(g),preserve_all_data_layers=True,depsgraph=g);v=np.array([ob.matrix_world@x.co for x in m.vertices]);f=np.array([q.vertices[:]for q in m.polygons],int);result[ob['asset_id']]=(v,f,m,ob)
 return result
p4=snapshot('10_PASSE4_NEUTRE');p5=snapshot('12_PASSE5_NEUTRE');s4=bpy.data.scenes.new('13_TEMOIN_PASSE4');s5=bpy.data.scenes.new('14_TEMOIN_PASSE5');after=bpy.data.scenes.new('15_PASSE6_NEUTRE');mat=bpy.data.materials['PASSE3_MAT_NEUTRE'];data=np.load(a.surface);v=data['source_v'];q=data['v'].copy();f=data['f'];mask=data['mask'];assert np.array_equal(v,p4['deltoid.right'][0])and np.array_equal(f,p5['deltoid.right'][1])
def smooth(t):t=np.clip(t,0,1);return t*t*(3-2*t)
def volume(v,f):return float(np.einsum('ij,ij->i',v[f[:,0]],np.cross(v[f[:,1]],v[f[:,2]])).sum()/6)
cross=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]);normal=np.zeros_like(v)
for k in range(3):np.add.at(normal,f[:,k],cross)
normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-12)
pv,pf,_,_=p5['pectoralis_major.right'];pec=BVHTree.FromPolygons(pv.tolist(),pf.tolist(),all_triangles=True);correction=np.zeros_like(q);eligible=[];gaps_before=[]
for i,point in enumerate(q):
 region=smooth((point[2]-1.35)/.035)*smooth((1.497-point[2])/.025)*smooth((point[0]+.23)/.025)*smooth((.065-point[1])/.025)*smooth((.45*normal[i,0]-.75*normal[i,1]-.05)/.5)
 if region<1e-4:continue
 hit=pec.find_nearest(Vector(point),.014)
 if hit[0]is None:continue
 nearest=np.array(hit[0]);n=np.array(hit[1]);signed=np.dot(point-nearest,n)
 original=pec.find_nearest(Vector(v[i]));old_signed=np.dot(v[i]-np.array(original[0]),np.array(original[1]))
 if old_signed<-.0002:continue # Keep source insertion contacts; do not expand them.
 distance=float(hit[3]);eligible.append(i);gaps_before.append(distance)
 if signed<.0013:move=nearest+n*.0013-point
 elif distance>.0017:move=(nearest+n*.0017-point)*.70
 else:continue
 length=np.linalg.norm(move);correction[i]=move*min(1,.0035/max(length,1e-12))*region
# Spread the collar correction over neighboring vertices to avoid a new line.
edges=np.unique(np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1),axis=0);edges=np.vstack([edges,edges[:,::-1]]);degree=np.bincount(edges[:,0],minlength=len(v))
for _ in range(3):
 avg=np.column_stack([np.bincount(edges[:,0],weights=correction[edges[:,1],k],minlength=len(v))/degree for k in range(3)]);correction=.65*correction+.35*avg
q+=correction
v4=v.copy();f4=f.copy();original_tree=BVHTree.FromPolygons(v4.tolist(),f4.tolist(),all_triangles=True)
# The old surface contains thin sculpt folds. Reconstruct only the two deltoid
# surfaces so removing those folds cannot leave intersecting strips of triangles.
worker_mesh=bpy.data.meshes.new('PASSE6_RECONSTRUCTION_TEMP');worker_mesh.from_pydata(q.tolist(),[],f.tolist());worker_mesh.update();worker=bpy.data.objects.new('PASSE6_RECONSTRUCTION_TEMP',worker_mesh);after.collection.objects.link(worker);bpy.context.window.scene=after;after.view_layers[0].objects.active=worker;worker.select_set(True);worker_mesh.remesh_voxel_size=.0018;worker_mesh.remesh_voxel_adaptivity=0;worker_mesh.use_remesh_preserve_volume=False;worker_mesh.use_remesh_preserve_attributes=False;bpy.ops.object.voxel_remesh()
bm=bmesh.new();bm.from_mesh(worker.data);bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(worker.data);bm.free();dense=worker.data.copy()
for resolution_factor in [1.,1.05,1.15,1.30,1.60,2.]:
 worker.data=dense.copy();dec=worker.modifiers.new('RESOLUTION_LOCALE_P6','DECIMATE');dec.ratio=min(1.,resolution_factor*len(f4)/len(dense.polygons));dec.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=dec.name);q=np.array([x.co[:]for x in worker.data.vertices]);f=np.array([x.vertices[:]for x in worker.data.polygons],int)
 trial=BVHTree.FromPolygons(q.tolist(),f.tolist(),all_triangles=True);pairs=[(i,j)for i,j in trial.overlap(trial)if i<j and not np.isin(f[i],f[j]).any()];print('P6_RESOLUTION_CHECK',resolution_factor,len(f),len(pairs),flush=True)
 if not pairs:break
else:raise RuntimeError('No verified local decimation resolution')
bpy.data.objects.remove(worker,do_unlink=True)
# Preserve all remaining source pieces and authoring connectivity. Reject folded
# geometry rather than hiding it with different materials or a new overlay.
tree=BVHTree.FromPolygons(q.tolist(),f.tolist(),all_triangles=True);contacts=[(i,j)for i,j in tree.overlap(tree)if i<j and not np.isin(f[i],f[j]).any()];assert not contacts,('deltoid self-contact',len(contacts))
area=np.linalg.norm(np.cross(q[f[:,1]]-q[f[:,0]],q[f[:,2]]-q[f[:,0]]),axis=1)/2;assert np.all(area>1e-12)
left=q.copy();left[:,0]=2*plane-left[:,0];changes={'deltoid.right':q,'deltoid.left':left};t=np.clip((q[:,2]-1.286)/.217,0,1);theta=np.arctan2(q[:,1]-(.08-.01*t),(-.241+.057*t)-q[:,0]);centers=np.column_stack([-1.25-.35*smooth((t-.72)/.22),np.full(len(q),-.08),1.20+.30*smooth((t-.72)/.22)]);score=-.5*((theta[:,None]-centers)/.5)**2;weights=np.exp(score-score.max(1)[:,None]);weights/=weights.sum(1)[:,None]
def clone(scene,prefix,key,record,edited=False):
 vv,ff,mesh,original=record
 if edited:
  mesh=bpy.data.meshes.new('PASSE6_SURFACE_'+key);mesh.from_pydata(changes[key].tolist(),[],(f[:,::-1]if key.endswith('.left')else f).tolist());mesh.materials.append(mat)
  for poly in mesh.polygons:poly.use_smooth=True
 ob=bpy.data.objects.new(prefix+key,mesh);scene.collection.objects.link(ob)
 for prop in original.keys():ob[prop]=original[prop]
 for slot in ob.material_slots:slot.link='OBJECT';slot.material=mat
 if edited:
  for k,label in enumerate(['DELT_ANTERIEUR','DELT_MOYEN','DELT_POSTERIEUR']):
   group=ob.vertex_groups.new(name=label)
   for idx,wgt in enumerate(weights[:,k]):
    if wgt>1e-5:group.add([idx],float(wgt),'REPLACE')
  ob['deltoid_regions']='P4 external curvature rebuilt from section hull and a smooth envelope of three convex bellies, compact silhouette, rounded deltopectoral contact; authoring weights, not final segmentation.'
 return ob
for key,record in p4.items():clone(s4,'P6_P4__',key,record)
for key,record in p5.items():clone(s5,'P6_P5__',key,record);clone(after,'P6__',key,record,key in changes)
gaps_after=[float(pec.find_nearest(Vector(data['v'][i]+correction[i]))[3])for i in eligible]
meta={'baseline_commit':'354d36486cb0d44ad51dfae35278b967153a1424','baseline_blend_sha256':sha(a.baseline),'p4_blend_sha256':sha(a.baseline.parent.parent/'ecorche-beatriz-passe4/ecorche-passe4.blend'),'source_asset':prior['source_asset'],'source_sha256':prior['source_sha256'],'head_source':prior['head_source'],'median_plane_x_m':plane,'objects':len(p5),'triangles':sum(len(o.data.polygons)for o in after.objects if o.type=='MESH'),'changed_original_objects':sorted(changes),'unchanged_original_objects':len(p5)-2,'new_objects':[],'new_triangles':2*(len(f)-len(f4)),'reconstructed_objects':sorted(changes),'reconstruction_voxel_m':.0018,'surface_method':json.loads(a.surface.with_suffix('.json').read_text()),'shoulder_right':{'volume_p4_m3':volume(v4,f4),'volume_p5_m3':volume(*p5['deltoid.right'][:2]),'volume_p6_m3':volume(q,f),'volume_ratio_to_p4':volume(q,f)/volume(v4,f4),'max_distance_to_p4_surface_m':max(float(original_tree.find_nearest(Vector(x))[3])for x in q),'bbox_p4_m':np.ptp(v4,axis=0).tolist(),'bbox_p5_m':np.ptp(p5['deltoid.right'][0],axis=0).tolist(),'bbox_p6_m':np.ptp(q,axis=0).tolist(),'nonadjacent_self_contacts_detected':len(contacts),'min_triangle_area_m2':float(area.min()),'deltopectoral_vertices_approached':int((np.linalg.norm(correction,axis=1)>1e-5).sum()),'max_deltopectoral_correction_m':float(np.linalg.norm(correction,axis=1).max()),'eligible_contact_sample_count':len(eligible),'eligible_contact_median_before_m':float(np.median(gaps_before))if eligible else None,'eligible_contact_median_after_m':float(np.median(gaps_after))if eligible else None,'contact_samples_measured_before_reconstruction':True},'builder_sha256':sha(Path(__file__)),'limitations':['Source-guided stylized shoulder reconstruction, not medical certification.','Only deltoid meshes changed; all P5 head, throat, pectorals and remaining body arrays are identical.','Complete clinical attachment/contact audit and final interactive muscle segmentation not provided.']}
(root/'passe6.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n');bpy.data.texts.new('PASSE6_CORRECTIONS.json').write(json.dumps(meta,ensure_ascii=False,indent=2));bpy.context.window.scene=after;bpy.ops.wm.save_as_mainfile(filepath=str(root/'ecorche-passe6.blend'),compress=True);print('PASSE6_BUILT',json.dumps(meta),flush=True)
