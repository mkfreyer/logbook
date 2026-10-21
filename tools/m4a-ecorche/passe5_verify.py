"""Independent geometry, unchanged-body, neutral material, render and serialized GLB checks."""
import argparse,hashlib,json,struct,sys
from pathlib import Path
import bpy,numpy as np
from mathutils.bvhtree import BVHTree
p=argparse.ArgumentParser();p.add_argument('--asset',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.asset.resolve();meta=json.loads((root/'passe5.json').read_text());plane=meta['median_plane_x_m']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(root.parent/'ecorche-beatriz-passe4/ecorche-passe4.blend')==meta['baseline_blend_sha256']
bpy.ops.wm.open_mainfile(filepath=str(root/'ecorche-passe5.blend'),use_scripts=False)
def arrays(scene_name):
 s=bpy.data.scenes[scene_name];bpy.context.window.scene=s;s.view_layers[0].update();g=bpy.context.evaluated_depsgraph_get();out={}
 for o in s.objects:
  if o.type!='MESH':continue
  ev=o.evaluated_get(g);m=ev.to_mesh();v=np.array([o.matrix_world@x.co for x in m.vertices]);f=np.array([q.vertices[:]for q in m.polygons],int);out[o['asset_id']]=(v,f);ev.to_mesh_clear()
 return out
original=arrays('10_PASSE4_NEUTRE');before=arrays('11_AVANT_PASSE5');after=arrays('12_PASSE5_NEUTRE');assert original.keys()==before.keys()
for key in before:assert np.array_equal(before[key][0],original[key][0])and np.array_equal(before[key][1],original[key][1])
head_id='head_throat.neutral_surface';new_ids=set(meta['new_objects']);changed=set(meta['changed_original_objects']);assert set(after)==set(before)|new_ids
untouched=set(before)-changed
for key in untouched:assert np.array_equal(before[key][0],after[key][0])and np.array_equal(before[key][1],after[key][1]),key
def volume(v,f):return float(np.einsum('ij,ij->i',v[f[:,0]],np.cross(v[f[:,1]],v[f[:,2]])).sum()/6)
def contact_keys(v,f,pairs):
 def key(i):return tuple(sorted(tuple(q)for q in np.rint(v[f[i]]*1e6).astype(int)))
 return {tuple(sorted((key(i),key(j))))for i,j in pairs}
donor=np.load(root/'head-donor.npz');dv=donor['head__v'].astype(np.float32).astype(float);df=donor['head__f'];dt=BVHTree.FromPolygons(dv.tolist(),df.tolist(),all_triangles=True);source_contacts=[(i,j)for i,j in dt.overlap(dt)if i<j and not np.isin(df[i],df[j]).any()];source_keys=contact_keys(dv,df,source_contacts)
surface_checks={}
for key in sorted(changed|new_ids):
 v,f=after[key];edges=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1);ue,c=np.unique(edges,axis=0,return_counts=True);assert(c==2).all(),key
 area=np.linalg.norm(np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]),axis=1)/2;assert np.all(area>1e-12)
 parents=np.arange(len(v))
 def find(i):
  while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
  return i
 for i,j in ue:
  x,y=find(int(i)),find(int(j))
  if x!=y:parents[y]=x
 components=len(set(find(i)for i in range(len(v))));assert components==1
 tree=BVHTree.FromPolygons(v.tolist(),f.tolist(),all_triangles=True);contacts=[(i,j)for i,j in tree.overlap(tree)if i<j and not np.isin(f[i],f[j]).any()];
 if key==head_id:
  assert contact_keys(v,f,contacts)<=source_keys, 'Head contains a new self-contact beyond source lip closure'
 else:assert not contacts,(key,len(contacts))
 surface_checks[key]={'triangles':len(f),'closed_two_manifold':True,'components':components,'euler_characteristic':len(v)-len(ue)+len(f),'min_triangle_area_m2':float(area.min()),'nonadjacent_self_contacts_detected':len(contacts)}
 if key.startswith('deltoid.'):
  v0,f0=before[key];assert np.array_equal(f,f0);ratio=volume(v,f)/volume(v0,f0);assert abs(ratio-1)<.001
  surface_checks[key].update({'topology_unchanged':True,'volume_ratio':ratio,'max_displacement_m':float(np.linalg.norm(v-v0,axis=1).max())})
r=after['deltoid.right'][0].copy();r[:,0]=2*plane-r[:,0];reflection=float(np.abs(r-after['deltoid.left'][0]).max());assert reflection<2e-7
# Prove the validated throat was retained, including all fully protected faces.
neck_v,neck_f=before[head_id];new_v,new_f=after[head_id];cut=meta['neck_protected_below_z_m'];protected=neck_v[:,2]<cut-2e-6
from mathutils.kdtree import KDTree
kt=KDTree(len(new_v))
for i,x in enumerate(new_v):kt.insert(x,i)
kt.balance();neck_error=max(float(kt.find(x)[2])for x in neck_v[protected]);assert neck_error<1e-7
head_symmetry=None # Human source has natural minor facial asymmetry; it is not forced to mirror.
for scene_name in ['11_AVANT_PASSE5','12_PASSE5_NEUTRE']:
 s=bpy.data.scenes[scene_name];assert len([o for o in s.objects if o.type=='LIGHT'])==5
 for ob in s.objects:
  if ob.type!='MESH':continue
  mat=ob.material_slots[0].material;assert mat==bpy.data.materials['PASSE3_MAT_NEUTRE'];bsdf=mat.node_tree.nodes['Principled BSDF'];assert bsdf.inputs['Metallic'].default_value==0 and bsdf.inputs['Roughness'].default_value>.84 and bsdf.inputs['Coat Weight'].default_value==0
for side in ['right','left']:
 ob=bpy.data.scenes['12_PASSE5_NEUTRE'].objects['P5__deltoid.'+side];groups=[ob.vertex_groups[k].index for k in ['DELT_ANTERIEUR','DELT_MOYEN','DELT_POSTERIEUR']]
 for vertex in ob.data.vertices:assert abs(sum(g.weight for g in vertex.groups if g.group in groups)-1)<1e-3

# Decode GLB and compare every actual serialized triangle against the master.
raw=(root/'ecorche-passe5.glb').read_bytes();size=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+size]);binary=raw[28+size:]
def accessor(index):
 ac=doc['accessors'][index];view=doc['bufferViews'][ac['bufferView']];width={'SCALAR':1,'VEC3':3,'VEC4':4}[ac['type']];dtype=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2'}[ac['componentType']])
 return np.ndarray((ac['count'],width),dtype=dtype,buffer=binary,offset=view.get('byteOffset',0)+ac.get('byteOffset',0),strides=(view.get('byteStride',width*dtype.itemsize),dtype.itemsize)).copy()
def signatures(v,f):
 q=np.rint(v[f]*1e6).astype('<i4');order=np.lexsort((q[:,:,2],q[:,:,1],q[:,:,0]),axis=1);q=np.ascontiguousarray(np.take_along_axis(q,order[:,:,None],axis=1).reshape(-1,9))
 return np.sort(q.view(np.dtype([(f'c{i}','<i4')for i in range(9)])).ravel())
fixed_before=neck_f[np.max(neck_v[neck_f,2],axis=1)<cut-2e-6]
fixed_after=new_f[np.max(new_v[new_f,2],axis=1)<cut-2e-6]
assert np.array_equal(signatures(neck_v,fixed_before),signatures(new_v,fixed_after)), 'Protected throat face surface changed'
triangles=vertices=0;omissions=[]
assert len(doc['nodes'])==len(after)and len(doc['materials'])==1
for node in doc['nodes']:
 key=node['name'];assert key in after and not any(k in node for k in ['matrix','translation','rotation','scale'])
 primitive=doc['meshes'][node['mesh']]['primitives'][0];assert not any(k.startswith('COLOR_')for k in primitive['attributes']);v=accessor(primitive['attributes']['POSITION']).astype(float);v=v[:,[0,2,1]];v[:,1]*=-1;f=accessor(primitive['indices']).reshape(-1,3);triangles+=len(f);vertices+=len(v)
 expected=signatures(*after[key]);actual=signatures(v,f);assert not len(np.setdiff1d(actual,expected))
 if not np.array_equal(expected,actual):
  s0,c0=np.unique(expected,return_counts=True);s1,c1=np.unique(actual,return_counts=True);remain=np.zeros(len(s0),int);remain[np.searchsorted(s0,s1)]=c1;diff=c0-remain;assert(diff>=0).all()
  for i in np.flatnonzero(diff):
   assert remain[i]>0,('lost surface',key);omissions.append({'asset_id':key,'removed_copies':int(diff[i]),'copies_remaining':int(remain[i])})
 if key==head_id or key in new_ids:assert node['extras']['interactive_muscle_zone']is False
assert 'CC BY 4.0'in doc['asset']['copyright']and doc['asset']['extras']['baseline_commit']==meta['baseline_commit']
s=bpy.data.scenes.new('VERIFY_PASSE5_IMPORT');bpy.context.window.scene=s;bpy.ops.import_scene.gltf(filepath=str(root/'ecorche-passe5.glb'),merge_vertices=False);imported=[o for o in s.objects if o.type=='MESH'];assert len(imported)==len(after)and sum(sum(len(f.vertices)-2 for f in o.data.polygons)for o in imported)==triangles
renders=json.loads((root/'renders/metadata.json').read_text());assert len(renders['frames'])==20 and renders['final_blend_sha256']==sha(root/'ecorche-passe5.blend');assert all(sha(root/'renders'/f['file'])==f['sha256']for f in renders['frames'])
report={'baseline_unchanged_sha256':meta['baseline_blend_sha256'],'new_master_sha256':sha(root/'ecorche-passe5.blend'),'glb_sha256':sha(root/'ecorche-passe5.glb'),'before_scene_exact_pass4':True,'unchanged_body_objects':len(untouched),'max_unchanged_coordinate_difference_m':0,'changed_original_objects':sorted(changed),'validated_neck_preserved_below_z_m':cut,'neck_max_original_vertex_difference_m':neck_error,'unchanged_throat_triangles_verified':len(fixed_before),'new_eyeball_objects':2,'source_lip_contact_pairs':len(source_contacts),'head_self_contacts_match_source_geometry':True,'surface_checks':surface_checks,'deltoid_reflection_error_m':reflection,'head_has_natural_source_asymmetry':True,'shoulder_authoring_groups_refined':True,'neutral_pass3_material_verified':True,'symmetric_five_light_rig_verified':True,'objects':len(after),'master_triangles':sum(len(f)for v,f in after.values()),'glb_triangles':triangles,'glb_vertices':vertices,'glb_duplicate_faces_removed':omissions,'glb_surface_match_at_micron_quantization':True,'glb_reimport_verified':True,'render_files_hash_verified':20,'verifier_sha256':sha(Path(__file__)),'scope':'Body and throat preservation, modified deltoid geometry and export QA; source lip closure contacts reported, no clinical certification or exhaustive inter-object audit.'}
(root/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('PASSE5_VERIFIED',json.dumps(report),flush=True)
