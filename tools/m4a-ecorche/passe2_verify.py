"""Independent preservation, topology, morphology and serialized-GLB checks."""
import argparse,hashlib,json,struct,sys
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
p=argparse.ArgumentParser();p.add_argument('--asset',type=Path,required=True);p.add_argument('--geometry-only',action='store_true');a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.asset.resolve();meta=json.loads((root/'passe2.json').read_text());plane=meta['median_plane_x_m']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(root.parent/'ecorche-beatriz-retouche/ecorche-athletique.blend')==meta['baseline_blend_sha256']
bpy.ops.wm.open_mainfile(filepath=str(root/'ecorche-passe2.blend'),use_scripts=False)
def scene_arrays(name,prefix):
 scene=bpy.data.scenes[name];bpy.context.window.scene=scene;scene.view_layers[0].update();graph=bpy.context.evaluated_depsgraph_get();out={}
 for ob in scene.objects:
  if ob.type!='MESH':continue
  ev=ob.evaluated_get(graph);mesh=ev.to_mesh();v=np.array([ob.matrix_world@x.co for x in mesh.vertices]);f=np.array([p.vertices[:]for p in mesh.polygons],int);out[ob.name.removeprefix(prefix)]=(v,f);ev.to_mesh_clear()
 return out
original=scene_arrays('02_ATHLETIQUE','');before=scene_arrays('04_AVANT_PASSE2','P2_BASE__');after=scene_arrays('05_PASSE2_NEUTRE','P2__');assert original.keys()==before.keys()==after.keys()
changed=[];flips=0;seam_error=0.;reflection_error=0.;max_unchanged=0.
for name,(v,f)in after.items():
 v0,f0=before[name];assert np.array_equal(f,f0)and np.array_equal(f0,original[name][1]);assert np.array_equal(v0,original[name][0])
 error=float(np.max(np.abs(v-v0)))
 if name not in meta['changed_objects']:assert np.array_equal(v,v0);max_unchanged=max(max_unchanged,error)
 elif error>1e-7:changed.append(name)
 _,inverse=np.unique(v0,axis=0,return_inverse=True);n=inverse.max()+1;low=np.full((n,3),np.inf);high=np.full((n,3),-np.inf);delta=v-v0
 np.minimum.at(low,inverse,delta);np.maximum.at(high,inverse,delta);seam_error=max(seam_error,float(np.max(high-low)))
 c0=np.cross(v0[f[:,1]]-v0[f[:,0]],v0[f[:,2]]-v0[f[:,0]]);c1=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]])
 flips+=int(np.sum((np.linalg.norm(c0,axis=1)>1e-10)&(np.einsum('ij,ij->i',c0,c1)<=0)))
 if name.endswith('.right'):
  reflection=v.copy();reflection[:,0]=2*plane-reflection[:,0];mate=after[name[:-5]+'left'][0];reflection_error=max(reflection_error,float(np.max(np.abs(reflection-mate))))
assert set(changed)==set(meta['changed_objects'])and seam_error<1e-7 and flips==0 and reflection_error<2e-7
def volume(v,f):return float(np.einsum('ij,ij->i',v[f[:,0]],np.cross(v[f[:,1]],v[f[:,2]])).sum()/6)
ratios={name:volume(*after[name])/volume(*before[name])for name in changed if name.endswith('.right')}
assert abs(ratios['deltoid.right']-1)<.012
assert ratios['m0_c015.right']>ratios['m0_c014.right']>1 and ratios['m0_c016.right']>ratios['m0_c014.right']
for side in ['left','right']:
 ob=bpy.data.scenes['05_PASSE2_NEUTRE'].objects['P2__deltoid.'+side];groups=[ob.vertex_groups[n].index for n in ['DELT_ANTERIEUR','DELT_MOYEN','DELT_POSTERIEUR']]
 for vert in ob.data.vertices:assert abs(sum(g.weight for g in vert.groups if g.group in groups)-1)<1e-3
for name in ['04_AVANT_PASSE2','05_PASSE2_NEUTRE']:
 for ob in bpy.data.scenes[name].objects:
  if ob.type!='MESH':continue
  material=ob.material_slots[0].material;shader=material.node_tree.nodes['Principled BSDF']
  assert shader.inputs['Metallic'].default_value==0 and shader.inputs['Coat Weight'].default_value==0 and shader.inputs['Roughness'].default_value>.8
def median_gap(v,f,z):
 points=[]
 for i,j in [(0,1),(1,2),(2,0)]:
  p=v[f[:,i]];q=v[f[:,j]];keep=(p[:,2]-z)*(q[:,2]-z)<0;p=p[keep];q=q[keep];t=(z-p[:,2])/(q[:,2]-p[:,2]);points.append(p+t[:,None]*(q-p))
 points=np.concatenate(points);points=points[(points[:,1]>.10)&(points[:,0]<plane)&(points[:,0]>plane-.03)]
 return 2*float(np.min(plane-points[:,0]))if len(points)else None
gaps=[{'z_m':z,'before_gap_m':median_gap(*before['trapezius.right'],z),'after_gap_m':median_gap(*after['trapezius.right'],z)}for z in [1.35,1.40,1.45,1.50]]
assert all(r['after_gap_m']<r['before_gap_m']for r in gaps)

# Compare actual glTF face surfaces, not exporter-reported counts.
raw=(root/'ecorche-passe2.glb').read_bytes();size=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+size]);binary=raw[28+size:]
def accessor(index):
 ac=doc['accessors'][index];view=doc['bufferViews'][ac['bufferView']];width={'SCALAR':1,'VEC3':3,'VEC4':4}[ac['type']];dtype=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2'}[ac['componentType']])
 return np.ndarray((ac['count'],width),dtype=dtype,buffer=binary,offset=view.get('byteOffset',0)+ac.get('byteOffset',0),strides=(view.get('byteStride',width*dtype.itemsize),dtype.itemsize)).copy()
def signatures(v,f):
 q=np.rint(v[f]*1e6).astype('<i4');order=np.lexsort((q[:,:,2],q[:,:,1],q[:,:,0]),axis=1);q=np.ascontiguousarray(np.take_along_axis(q,order[:,:,None],axis=1).reshape(-1,9))
 return np.sort(q.view(np.dtype([(f'c{i}','<i4')for i in range(9)])).ravel())
triangles=0;vertices=0;omissions=[]
for node in doc['nodes']:
 assert 'mesh'in node and node['name']in after;assert not any(k in node for k in ['matrix','translation','rotation','scale'])
 primitive=doc['meshes'][node['mesh']]['primitives'][0];assert not any(k.startswith('COLOR_')for k in primitive['attributes'])
 v=accessor(primitive['attributes']['POSITION']).astype(float);v=v[:,[0,2,1]];v[:,1]*=-1;f=accessor(primitive['indices']).reshape(-1,3);triangles+=len(f);vertices+=len(v)
 expected=signatures(*after[node['name']]);actual=signatures(v,f);assert not len(np.setdiff1d(actual,expected))
 if not np.array_equal(expected,actual):
  sig0,count0=np.unique(expected,return_counts=True);sig1,count1=np.unique(actual,return_counts=True);remaining=np.zeros(len(sig0),int);remaining[np.searchsorted(sig0,sig1)]=count1;difference=count0-remaining;assert(difference>=0).all()
  for i in np.flatnonzero(difference):
   assert remaining[i]>0,('lost surface',node['name']);omissions.append({'asset_id':node['name'],'removed_copies':int(difference[i]),'copies_remaining':int(remaining[i])})
assert len(doc['nodes'])==len(after)and 'CC BY 4.0'in doc['asset']['copyright']
assert doc['asset']['extras']['baseline_commit']==meta['baseline_commit']
import_scene=bpy.data.scenes.new('VERIFY_PASSE2_IMPORT');bpy.context.window.scene=import_scene;bpy.ops.import_scene.gltf(filepath=str(root/'ecorche-passe2.glb'),merge_vertices=False)
imported=[o for o in import_scene.objects if o.type=='MESH'];assert len(imported)==len(after)and sum(sum(len(f.vertices)-2 for f in o.data.polygons)for o in imported)==triangles
report={'baseline_unchanged_sha256':meta['baseline_blend_sha256'],'new_master_sha256':sha(root/'ecorche-passe2.blend'),'glb_sha256':sha(root/'ecorche-passe2.glb'),'objects':len(after),'master_triangles':sum(len(f)for v,f in after.values()),'new_triangles':0,'changed_objects':len(changed),'untouched_objects':len(after)-len(changed),'max_untouched_coordinate_difference_m':max_unchanged,'source_triangle_indices_unchanged':True,'triangle_inversions_above_cross_norm_1e_minus_10':flips,'duplicate_seam_displacement_error_m':seam_error,'bilateral_reflection_error_m':reflection_error,'closed_muscle_volume_ratios_right':ratios,'trapezius_median_gap_profiles':gaps,'neutral_matte_material_checked':True,'deltoid_weight_groups_checked':True,'deltoid_medical_certification':False,'glb_objects':len(doc['nodes']),'glb_triangles':triangles,'glb_vertices':vertices,'glb_surface_match_at_micron_quantization':True,'glb_duplicate_faces_removed':omissions,'blender_glb_reimport_checked':True,'verifier_sha256':sha(Path(__file__))}
if not a.geometry_only:
 renders=json.loads((root/'renders/metadata.json').read_text());assert len(renders['frames'])==15 and renders['final_blend_sha256']==sha(root/'ecorche-passe2.blend')
 assert all(sha(root/'renders'/f['file'])==f['sha256']for f in renders['frames']);report['renders_verified']=len(renders['frames'])
 (root/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('PASSE2_VERIFIED',json.dumps(report),flush=True)
