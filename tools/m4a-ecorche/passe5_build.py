"""Targeted fifth pass: source-based human head, protected throat and continuous deltoid fans."""
import argparse,hashlib,json,sys,math
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils.bvhtree import BVHTree
p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--donor',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.output.resolve();root.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(a.baseline)=='15444ab13acb4232ed9d366e39b333c305b9c1be533e71d2b5eee90b9e58ff37'
prior=json.loads((a.baseline.parent/'passe4.json').read_text());plane=prior['median_plane_x_m'];donor=np.load(a.donor);bpy.ops.wm.open_mainfile(filepath=str(a.baseline.resolve()),use_scripts=False);source=bpy.data.scenes['10_PASSE4_NEUTRE'];bpy.context.window.scene=source;source.view_layers[0].update();g=bpy.context.evaluated_depsgraph_get();snap={};original={}
for o in source.objects:
 if o.type!='MESH':continue
 m=bpy.data.meshes.new_from_object(o.evaluated_get(g),preserve_all_data_layers=True,depsgraph=g);v=np.array([o.matrix_world@q.co for q in m.vertices]);f=np.array([q.vertices[:]for q in m.polygons],int);snap[o['asset_id']]=(v,f,m);original[o['asset_id']]=o
before=bpy.data.scenes.new('11_AVANT_PASSE5');after=bpy.data.scenes.new('12_PASSE5_NEUTRE');mat=bpy.data.materials['PASSE3_MAT_NEUTRE']
def smooth(t):t=np.clip(t,0,1);return t*t*(3-2*t)
def volume(v,f):return float(np.einsum('ij,ij->i',v[f[:,0]],np.cross(v[f[:,1]],v[f[:,2]])).sum()/6)
v,f,_=snap['deltoid.right'];cross=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]);normal=np.zeros_like(v);area=np.zeros(len(v))
for k in range(3):np.add.at(normal,f[:,k],cross);np.add.at(area,f[:,k],np.linalg.norm(cross,axis=1)/6)
normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-12);edges=np.unique(np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1),axis=0);edges=np.vstack([edges,edges[:,::-1]]);w=1/np.maximum(np.linalg.norm(v[edges[:,0]]-v[edges[:,1]],axis=1),.001);degree=np.bincount(edges[:,0],weights=w,minlength=len(v))
def average(q):return np.column_stack([np.bincount(edges[:,0],weights=w*q[edges[:,1],k],minlength=len(q))/degree for k in range(q.shape[1])])
for _ in range(4):normal+=average(normal);normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-12)
t=np.clip((v[:,2]-1.286)/.217,0,1);ax=-.241+.057*t;ay=.080-.010*t;r=np.column_stack([v[:,0]-ax,v[:,1]-ay,np.zeros(len(v))]);r/=np.maximum(np.linalg.norm(r,axis=1)[:,None],1e-12);theta=np.arctan2(v[:,1]-ay,ax-v[:,0]);outer=smooth((np.einsum('ij,ij->i',normal,r)-.03)/.68);mask=outer*smooth((t-.08)/.20)*smooth((.98-t)/.17)
q=v.copy()
for _ in range(14):q+=.32*mask[:,None]*(average(q)-q)
fair=q-v;length=np.linalg.norm(fair,axis=1);fair*=np.minimum(1,.0013/np.maximum(length,1e-12))[:,None]
landmarks=json.loads((a.baseline.parent.parent/'ecorche-beatriz-passe3/passe3.json').read_text())['deltoid_landmarks'];origins=np.array(landmarks['right_origins_m']);bellies=np.array(landmarks['right_belly_landmarks_m']);insertion=np.array(landmarks['right_common_insertion_m']);bellies[0]+=[.001,-.001,.005];controls=2*bellies-.5*(origins+insertion);tau=np.linspace(0,1,160);angles=[]
for origin,control in zip(origins,controls):
 curve=(1-tau[:,None])**2*origin+2*(1-tau[:,None])*tau[:,None]*control+tau[:,None]**2*insertion;x=np.interp(v[:,2],curve[::-1,2],curve[::-1,0]);y=np.interp(v[:,2],curve[::-1,2],curve[::-1,1]);angles.append(np.arctan2(y-ay,ax-x))
angles=np.column_stack(angles);width=np.array([.25,.27,.29]);raw=np.exp(-.5*((theta[:,None]-angles)/width)**2);profile=(raw*np.array([1.02,.98,.98])*np.exp(-.5*((t[:,None]-np.array([.66,.58,.59]))/.29)**2)).sum(1);mean=np.sum(area*mask*profile)/np.sum(area*mask)
# Broad convex fan bellies and the saddles between them; no narrow incised line.
delta=fair+r*(.007*(profile-mean)*mask)[:,None];q=v+delta;goal=volume(v,f);lo=-.008;hi=.008
for _ in range(45):
 mid=(lo+hi)/2;test=q+normal*(mask*mid)[:,None]
 if (volume(test,f)-goal)*np.sign(goal)>0:hi=mid
 else:lo=mid
q+=normal*(mask*((lo+hi)/2))[:,None]
tree=BVHTree.FromPolygons(q.tolist(),f.tolist(),all_triangles=True);contacts=[(i,j)for i,j in tree.overlap(tree)if i<j and not np.isin(f[i],f[j]).any()];assert not contacts,len(contacts)
left=q.copy();left[:,0]=2*plane-left[:,0];changes={'deltoid.right':q,'deltoid.left':left};score=-.5*((theta[:,None]-angles)/width)**2;weights=np.exp(score-score.max(1)[:,None]);weights/=weights.sum(1)[:,None]

def clip_surface(vertices,faces,z,keep_above):
 bm=bmesh.new();vs=[bm.verts.new(x)for x in vertices];bm.verts.ensure_lookup_table()
 for tri in faces:bm.faces.new([vs[int(i)]for i in tri])
 bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,plane_co=(0,0,z),plane_no=(0,0,1),clear_inner=keep_above,clear_outer=not keep_above)
 bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.verts.index_update();bm.faces.index_update();v=np.array([v.co[:]for v in bm.verts]);f=np.array([[x.index for x in face.verts]for face in bm.faces],int)
 boundary=set()
 for edge in bm.edges:
  if edge.is_boundary and all(abs(x.co.z-z)<2e-6 for x in edge.verts):boundary.update(x.index for x in edge.verts)
 assert len(boundary)>15
 bm.free();ids=np.array(sorted(boundary));theta=np.arctan2(v[ids,0]-plane,-(v[ids,1]-.04))%(2*np.pi);order=np.argsort(theta);return v,f,ids[order],theta[order]
neck_id='head_throat.neutral_surface';neck_cut=1.570;head_cut=1.575
nv,nf,nring,na=clip_surface(*snap[neck_id][:2],neck_cut,False);hv,hf,hring,ha=clip_surface(donor['head__v'],donor['head__f'],head_cut,True)
# Preserve every old throat vertex below the cut. Fit only the new submental edge
# toward the fixed throat boundary to avoid a collar or a seam step.
def cyclic_interp(angle,angles,values):return np.interp(angle,np.r_[angles-2*np.pi,angles,angles+2*np.pi],np.tile(values,3))
ang=np.arctan2(hv[:,0]-plane,-(hv[:,1]-.04))%(2*np.pi);blend=1-smooth((hv[:,2]-head_cut)/.035)
for k in [0,1]:
 lower=cyclic_interp(ang,na,nv[nring,k]);edge=cyclic_interp(ang,ha,hv[hring,k]);hv[:,k]+=.95*blend*(lower-edge)
# The old cervical/trapezius attachments stay fixed. Only the new posterior
# cranial/upper-nuchal surface is fitted around them so they cannot protrude.
ref_v=[];ref_f=[];offset=0
for key,(vv,ff,mm)in snap.items():
 if vv[:,2].max()<1.60:continue
 keep=np.max(vv[ff,2],axis=1)>1.56;ref_v.extend(vv.tolist());ref_f.extend((ff[keep]+offset).tolist());offset+=len(vv)
fixed_tree=BVHTree.FromPolygons(ref_v,ref_f,all_triangles=True)
from mathutils import Vector
for idx,point in enumerate(hv):
 z=point[2];back=smooth((point[1]-.025)/.045);zmask=smooth((z-1.580)/.035)*(1-smooth((z-1.700)/.030))
 if back*zmask<1e-5:continue
 hit=fixed_tree.ray_cast(Vector((float(point[0]),1,float(z))),Vector((0,-1,0)),2)
 if hit[0]is not None:hv[idx,1]+=min(.002,max(0,float(hit[0].y)+.001-point[1]))*back*zmask
N=len(nv);combined=np.vstack([nv,hv]);faces=nf.tolist()+((hf+N).tolist());i=j=0
while i<len(nring)or j<len(hring):
 aidx=int(nring[i%len(nring)]);bidx=int(hring[j%len(hring)])+N
 next_a=na[(i+1)%len(nring)]+(2*np.pi if i+1>=len(nring)else 0)if i<len(nring)else float('inf')
 next_b=ha[(j+1)%len(hring)]+(2*np.pi if j+1>=len(hring)else 0)if j<len(hring)else float('inf')
 if next_a<next_b:faces.append([aidx,int(nring[(i+1)%len(nring)]),bidx]);i+=1
 else:faces.append([aidx,int(hring[(j+1)%len(hring)])+N,bidx]);j+=1
headmesh=bpy.data.meshes.new('PASSE5_TETE_HUMAINE_GORGE_PRESERVEE');headmesh.from_pydata(combined.tolist(),[],faces);headmesh.update();bm=bmesh.new();bm.from_mesh(headmesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(headmesh);bm.free()
for poly in headmesh.polygons:poly.use_smooth=True
headmesh.materials.append(mat)
for key,(v,f,m)in snap.items():
 old=bpy.data.objects.new('P5_BASE__'+key,m);before.collection.objects.link(old);old['asset_id']=key
 for slot in old.material_slots:slot.link='OBJECT';slot.material=mat
 mesh=headmesh if key==neck_id else m.copy()if key in changes else m;ob=bpy.data.objects.new('P5__'+key,mesh);after.collection.objects.link(ob)
 for prop in original[key].keys():ob[prop]=original[key][prop]
 for slot in ob.material_slots:slot.link='OBJECT';slot.material=mat
 if key in changes:
  ob.shape_key_add(name='AVANT_PASSE5');sk=ob.shape_key_add(name='DEFINITION_TROIS_FAISCEAUX_PASSE5');sk.data.foreach_set('co',changes[key].astype(np.float32).ravel());sk.value=1
  for k,label in enumerate(['DELT_ANTERIEUR','DELT_MOYEN','DELT_POSTERIEUR']):
   group=ob.vertex_groups.new(name=label)
   for idx,wgt in enumerate(weights[:,k]):
    if wgt>1e-5:group.add([idx],float(wgt),'REPLACE')
  ob['deltoid_regions']='Source-guided convex fan bellies and broad transition saddles, volume constrained; overlapping authoring weights, not final interactive segmentation.'
 if key==neck_id:ob['role']='CC0 human head adapted above a preserved pass-four throat. Original throat surface retained below 1.570 m, new submental bridge above that boundary.'
for key in ['eye.l','eye.r']:
 mesh=bpy.data.meshes.new('PASSE5_'+key);mesh.from_pydata(donor[key+'__v'].tolist(),[],donor[key+'__f'].tolist());mesh.materials.append(mat)
 for poly in mesh.polygons:poly.use_smooth=True
 ob=bpy.data.objects.new('P5__head.'+key,mesh);after.collection.objects.link(ob);ob['asset_id']='head.'+key;ob['source_piece_id']='Blender Studio / '+key;ob['interactive_muscle_zone']=False;ob['anatomical_label_validated']=False;ob['role']='Neutral eyeball within the reconstructed human eyelids; non-muscular presentation surface.'
record={'volume_before_m3':goal,'volume_after_m3':volume(changes['deltoid.right'],snap['deltoid.right'][1]),'max_displacement_m':float(np.linalg.norm(changes['deltoid.right']-snap['deltoid.right'][0],axis=1).max()),'bbox_before_m':np.ptp(snap['deltoid.right'][0],axis=0).tolist(),'bbox_after_m':np.ptp(changes['deltoid.right'],axis=0).tolist(),'nonadjacent_self_contacts_detected':len(contacts),'fan_widths_radians':width.tolist(),'landmarks':landmarks,'topology_unchanged':True}
metadata={'baseline_commit':'9e49c787c58986b306d818a2d35a23a0e71aef87','baseline_blend_sha256':sha(a.baseline),'source_asset':prior['source_asset'],'source_sha256':prior['source_sha256'],'median_plane_x_m':plane,'before_objects':len(snap),'before_triangles':sum(len(f)for v,f,m in snap.values()),'objects':sum(o.type=='MESH'for o in after.objects),'triangles':sum(len(o.data.polygons)for o in after.objects if o.type=='MESH'),'changed_original_objects':['deltoid.left','deltoid.right',neck_id],'unchanged_original_objects':len(snap)-3,'new_objects':['head.eye.l','head.eye.r'],'neck_protected_below_z_m':neck_cut,'head_source_cut_z_m':head_cut,'neck_retained_triangles':len(nf),'head_retained_triangles':len(hf),'submental_bridge_triangles':len(faces)-len(nf)-len(hf),'head_source':json.loads(a.donor.with_suffix('.json').read_text()),'shoulder_right':record,'builder_sha256':sha(Path(__file__)),'limitations':['Head is adapted from a CC0 source, not a medical facial reconstruction.','Eye rims are intentional openings occupied by separate eyeball objects.','No app integration, mobile performance measurement or final muscle segmentation.']}
(root/'passe5.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n');bpy.data.texts.new('PASSE5_CORRECTIONS.json').write(json.dumps(metadata,ensure_ascii=False,indent=2));bpy.context.window.scene=after;bpy.ops.wm.save_as_mainfile(filepath=str(root/'ecorche-passe5.blend'),compress=True);print('PASSE5_BUILT',json.dumps(metadata),flush=True)
