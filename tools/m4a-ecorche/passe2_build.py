"""Targeted second pass on the validated, immutable 03aa2eb Blender master.

One proposal: deltoid volume redistribution, small arm gain, median back contact,
and bounded surface fairing. No remesh, subdivision or application changes.
"""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.output.resolve();root.mkdir(parents=True,exist_ok=True)
baseline=a.baseline.resolve();assert hashlib.sha256(baseline.read_bytes()).hexdigest()=='6798e252ae1aa1c7d8c31d33726045c718a82854a182428ed106e4a1c44672eb'
bpy.ops.wm.open_mainfile(filepath=str(baseline),use_scripts=False)
prior=json.loads((baseline.parent/'construction.json').read_text());plane=prior['median_plane_x_m']
source=bpy.data.scenes['02_ATHLETIQUE'];bpy.context.window.scene=source;source.view_layers[0].update();graph=bpy.context.evaluated_depsgraph_get()
before=bpy.data.scenes.new('04_AVANT_PASSE2');after=bpy.data.scenes.new('05_PASSE2_NEUTRE')
neutral=bpy.data.materials.new('PASSE2_MAT_NEUTRE');neutral.use_nodes=True;shader=neutral.node_tree.nodes['Principled BSDF']
for key,value in [('Base Color',(.52,.50,.47,1)),('Metallic',0),('Roughness',.85),('Coat Weight',0),('Specular IOR Level',.25)]:shader.inputs[key].default_value=value
snapshots={};original_ob={};vertices=[];faces=[];offset=0
for ob in source.objects:
 if ob.type!='MESH':continue
 mesh=bpy.data.meshes.new_from_object(ob.evaluated_get(graph),preserve_all_data_layers=True,depsgraph=graph)
 v=np.array([ob.matrix_world@x.co for x in mesh.vertices]);f=np.array([q.vertices[:]for q in mesh.polygons],int)
 snapshots[ob.name]=(v,f,mesh);original_ob[ob.name]=ob;vertices.extend(v.tolist());faces.extend((f+offset).tolist());offset+=len(v)
tree=BVHTree.FromPolygons(vertices,faces,all_triangles=True);del vertices,faces
def smooth(t):t=np.clip(t,0,1);return t*t*(3-2*t)
def envelope(t):return smooth((t-.09)/.22)*smooth((.94-t)/.24)
def volume(v,f):return float(np.einsum('ij,ij->i',v[f[:,0]],np.cross(v[f[:,1]],v[f[:,2]])).sum()/6)
def surface_area(v,f):return np.linalg.norm(np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]),axis=1).sum()/2
def topology(v,f):
 u,inverse=np.unique(v,axis=0,return_inverse=True);tri=inverse[f]
 cross=np.cross(u[tri[:,1]]-u[tri[:,0]],u[tri[:,2]]-u[tri[:,0]])
 normal=np.zeros_like(u)
 for k in range(3):np.add.at(normal,tri[:,k],cross)
 normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-12)
 edges=np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]);ordered=np.sort(edges,axis=1);unique_edges,counts=np.unique(ordered,axis=0,return_counts=True)
 boundary=np.unique(unique_edges[counts!=2]);edges=np.vstack([unique_edges,unique_edges[:,::-1]]);degree=np.bincount(edges[:,0],minlength=len(u))
 return u,tri,inverse,normal,edges,degree,boundary
def average(v,edges,degree):return np.column_stack([np.bincount(edges[:,0],weights=v[edges[:,1],i],minlength=len(v))/np.maximum(degree,1)for i in range(v.shape[1])])
def fairing(v,edges,degree,mask,cap):
 q=v.copy()
 for _ in range(3):
  for gain in [.32,-.335]:q+=gain*mask[:,None]*(average(q,edges,degree)-q)
 delta=q-v;length=np.linalg.norm(delta,axis=1);return delta*np.minimum(1,cap/np.maximum(length,1e-12))[:,None]
targets=['deltoid.right','m0_c014.right','m0_c015.right','m0_c016.right','pectoralis_major.right','trapezius.right']
changes={};records=[];head_weights={}
for name in targets:
 v,f,mesh=snapshots[name];u,tri,inverse,normal,edges,degree,boundary=topology(v,f)
 color=np.array([q.color[:]for q in mesh.color_attributes['Color'].data]);redness=np.clip((color[:,0]-(color[:,1]+color[:,2])/2)/.12,0,1)
 color_mask=np.ones(len(u));np.minimum.at(color_mask,inverse,redness)
 protected=np.zeros(len(u));protected[boundary]=1
 for _ in range(2):protected=np.maximum(protected,average(protected[:,None],edges,degree)[:,0])
 mask=color_mask*(1-smooth(protected*2));delta=np.zeros_like(u);notes=[]
 if name=='deltoid.right':
  # Origins span lateral clavicle, acromion, scapular spine; all portions
  # converge distally toward the deltoid tuberosity. Broad continuous bellies,
  # no incised line, detached patch, paint or extra muscle object.
  t=np.clip((u[:,2]-1.286)/.217,0,1);axis_x=-.241+.057*t;axis_y=.080-.010*t
  radial=np.column_stack([u[:,0]-axis_x,u[:,1]-axis_y,np.zeros(len(u))]);rn=radial/np.maximum(np.linalg.norm(radial,axis=1)[:,None],1e-12)
  theta=np.arctan2(u[:,1]-axis_y,axis_x-u[:,0]);outer=smooth((np.einsum('ij,ij->i',normal,rn)-.10)/.65)
  outer*=smooth((np.linalg.norm(radial,axis=1)-.012)/.018)
  preserve_width=smooth((u[:,0]-u[:,0].min())/.0035)
  field_mask=envelope(t)*outer*mask*preserve_width
  centers=np.array([-1.22,0,1.22])[None,:]*(.65+.35*t[:,None])
  raw=np.exp(-.5*((theta[:,None]-centers)/(.34+.08*t[:,None]))**2)
  head_weights[name]=raw/np.maximum(raw.sum(1)[:,None],1e-12)
  profiles=raw*np.exp(-.5*((t[:,None]-np.array([.60,.54,.57]))/.30)**2)
  shape=profiles.sum(1);measure=np.zeros(len(u));area=np.linalg.norm(np.cross(u[tri[:,1]]-u[tri[:,0]],u[tri[:,2]]-u[tri[:,0]]),axis=1)/6
  for k in range(3):np.add.at(measure,tri[:,k],area)
  mean=float(np.sum(measure*field_mask*shape)/np.maximum(np.sum(measure*field_mask),1e-12))
  delta+=normal*((.0055*(shape-mean))*field_mask)[:,None]
  delta+=fairing(u,edges,degree,mask*outer,.00065)
  # Preserve signed enclosed volume by a small broad correction, not by
  # enlarging the entire shoulder. Applied before local orientation safety.
  goal=volume(u,tri);lo=-.003;hi=.003
  for _ in range(35):
   mid=(lo+hi)/2;test=volume(u+delta+normal*(field_mask*mid)[:,None],tri)
   if (test-goal)*np.sign(goal)>0:hi=mid
   else:lo=mid
  delta+=normal*(field_mask*((lo+hi)/2))[:,None]
  notes=['Broad fan-shaped redistribution across anterior/acromial/posterior portions.','Common distal insertion and proximal borders attenuated.','Enclosed volume constrained; outer shoulder width protected.']
 elif name in ['m0_c014.right','m0_c015.right','m0_c016.right']:
  # c014: anterior biceps; c015: posterior superficial triceps; c016: deeper
  # posterior/medial triceps piece. Identification checked in diagnostic views.
  center=u.mean(0);_,basis=np.linalg.eigh((u-center).T@(u-center));axis=basis[:,-1];along=(u-center)@axis;t=(along-along.min())/(along.max()-along.min())
  radial=u-center-along[:,None]*axis;direction=radial/np.maximum(np.linalg.norm(radial,axis=1)[:,None],1e-12)
  outer=smooth((np.einsum('ij,ij->i',normal,direction)-.1)/.7)
  gain=.018 if name=='m0_c014.right'else .07 if name=='m0_c015.right'else .045
  delta+=radial*(gain*envelope(t)*mask*outer)[:,None]
  delta+=fairing(u,edges,degree,mask,.0004 if name=='m0_c014.right'else .0007)
  notes=['Biceps very small gain.'if name=='m0_c014.right'else 'Small triceps belly gain, insertions attenuated.']
 elif name=='pectoralis_major.right':
  delta+=fairing(u,edges,degree,mask,.00045);notes=['Bounded high-frequency surface fairing only; no additional chest hypertrophy.']
 elif name=='trapezius.right':
  d=plane-u[:,0];zmask=smooth((u[:,2]-1.285)/.07)*smooth((1.65-u[:,2])/.08);back=smooth((u[:,1]-.085)/.03)
  near=np.exp(-((d-.002)/.012)**2)*zmask*back
  delta[:,0]+=np.minimum(.00175*near,np.maximum(0,d-.00025));delta[:,1]+=.0010*near
  zone=np.maximum(np.exp(-(d/.038)**2),np.exp(-((u[:,0]+.135)/.035)**2-((u[:,2]-1.46)/.07)**2))*zmask*back
  delta+=fairing(u,edges,degree,zone*mask,.00045)
  notes=['Only medial contact and scapular transition adjusted; no global trap enlargement.']
 # Respect nearby source surfaces for outward expansion; retain conservative
 # inward fairing and deltoid redistribution. Coincident seams share a target.
 if name.startswith('m0_c01'):
  length=np.linalg.norm(delta,axis=1);direction=delta/np.maximum(length[:,None],1e-12)
  for i in np.flatnonzero(length>1e-6):
   hit=tree.ray_cast(Vector(u[i]+direction[i]*.00005),Vector(direction[i]),float(length[i]+.0005))
   if hit[2]is not None:delta[i]*=min(1,max(0,float(hit[3])-.00035)/length[i])
 cap=.0035 if name=='deltoid.right'else .003 if name.startswith('m0_c01')else .0025
 length=np.linalg.norm(delta,axis=1);delta*=np.minimum(1,cap/np.maximum(length,1e-12))[:,None]
 old_cross=np.cross(u[tri[:,1]]-u[tri[:,0]],u[tri[:,2]]-u[tri[:,0]]);valid=np.linalg.norm(old_cross,axis=1)>1e-12;correction=np.ones(len(u));protected_faces=set()
 for _ in range(30):
  q=u+delta*correction[:,None];new_cross=np.cross(q[tri[:,1]]-q[tri[:,0]],q[tri[:,2]]-q[tri[:,0]]);bad=valid&(np.einsum('ij,ij->i',old_cross,new_cross)<=0)
  if not bad.any():break
  ids=np.unique(tri[bad]);protected_faces.update(np.flatnonzero(bad).tolist());correction[ids]*=.25;correction=np.minimum(correction,(correction+average(correction[:,None],edges,degree)[:,0])/2)
 else:raise RuntimeError('Unresolved orientation issue: '+name)
 q=u+delta*correction[:,None];target=q[inverse];changes[name]=target
 info={'asset_id':name,'side':'right','max_displacement_m':float(np.linalg.norm(target-v,axis=1).max()),'mean_displacement_m':float(np.linalg.norm(target-v,axis=1).mean()),'bbox_dimensions_before_m':np.ptp(v,axis=0).tolist(),'bbox_dimensions_after_m':np.ptp(target,axis=0).tolist(),'signed_volume_before_m3':volume(v,f),'signed_volume_after_m3':volume(target,f),'surface_area_before_m2':surface_area(v,f),'surface_area_after_m2':surface_area(target,f),'boundary_vertices':len(boundary),'triangles_guarded':len(protected_faces),'notes':notes}
 if name=='deltoid.right':
  info['volume_ratio']=abs(info['signed_volume_after_m3']/info['signed_volume_before_m3']);assert abs(info['volume_ratio']-1)<.012,info
  head_weights[name]=head_weights[name][inverse]
 records.append(info)
 left=name[:-5]+'left';reflection=target.copy();reflection[:,0]=2*plane-reflection[:,0];changes[left]=reflection
 if name in head_weights:head_weights[left]=head_weights[name]
for name,(v,f,mesh)in snapshots.items():
 ob=bpy.data.objects.new('P2_BASE__'+name,mesh);before.collection.objects.link(ob)
 for slot in ob.material_slots:slot.link='OBJECT';slot.material=neutral
 final_mesh=mesh.copy()if name in changes else mesh
 ob=bpy.data.objects.new('P2__'+name,final_mesh);after.collection.objects.link(ob)
 for key in ['source_piece_id','side','region_hint','anatomical_label_validated']:
  if key in original_ob[name]:ob[key]=original_ob[name][key]
 ob['asset_id']=name
 for slot in ob.material_slots:slot.link='OBJECT';slot.material=neutral
 if name in changes:
  ob.shape_key_add(name='PASSE1_VALIDEE');key=ob.shape_key_add(name='PASSE2_CIBLEE');key.data.foreach_set('co',changes[name].astype(np.float32).ravel());key.value=1
 if name in head_weights:
  for index,label in enumerate(['DELT_ANTERIEUR','DELT_MOYEN','DELT_POSTERIEUR']):
   group=ob.vertex_groups.new(name=label)
   for i,w in enumerate(head_weights[name][:,index]):
    if w>1e-4:group.add([i],float(w),'REPLACE')
  ob['deltoid_regions']='Three overlapping authoring weight groups, not three independently certified anatomical objects.'
after['asset_scope']='Targeted shape refinement; no app integration or complete muscle segmentation.'
metadata={'baseline_commit':'03aa2eb1d34c984e1477211576c5e9b26eae4d59','baseline_blend_sha256':hashlib.sha256(baseline.read_bytes()).hexdigest(),'source_asset':prior['source_asset'],'source_sha256':prior['source_sha256'],'median_plane_x_m':plane,'objects':len(snapshots),'triangles':sum(len(x[1])for x in snapshots.values()),'changed_objects':sorted(changes),'unchanged_objects':len(snapshots)-len(changes),'new_triangles':0,'new_muscle_objects':0,'records_right':records,'builder_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'limitations':['Deltoid portions are continuous shape regions and overlapping weights, not three separate anatomical meshes.','Geometric consistency does not certify medical anatomy.','No mobile optimization or application interaction in this pass.']}
(root/'passe2.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n');bpy.data.texts.new('PASSE2_MODIFICATIONS.json').write(json.dumps(metadata,ensure_ascii=False,indent=2))
bpy.context.window.scene=after;bpy.ops.wm.save_as_mainfile(filepath=str(root/'ecorche-passe2.blend'),compress=True)
print('PASSE2_BUILT',json.dumps(metadata),flush=True)
