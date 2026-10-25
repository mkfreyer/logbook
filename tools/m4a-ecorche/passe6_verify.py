"""Independent P4/P5/P6 geometry, preservation, silhouette, contact and GLB checks."""
import argparse,hashlib,json,struct,sys
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=argparse.ArgumentParser();p.add_argument('--asset',type=Path,required=True);p.add_argument('--geometry-only',action='store_true');a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.asset.resolve();meta=json.loads((root/'passe6.json').read_text());plane=meta['median_plane_x_m']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(root.parent/'ecorche-beatriz-passe5/ecorche-passe5.blend')==meta['baseline_blend_sha256'];assert sha(root.parent/'ecorche-beatriz-passe4/ecorche-passe4.blend')==meta['p4_blend_sha256']
bpy.ops.wm.open_mainfile(filepath=str(root/'ecorche-passe6.blend'),use_scripts=False)
def arrays(name):
 s=bpy.data.scenes[name];bpy.context.window.scene=s;s.view_layers[0].update();g=bpy.context.evaluated_depsgraph_get();out={}
 for o in s.objects:
  if o.type!='MESH':continue
  ev=o.evaluated_get(g);m=ev.to_mesh();v=np.array([o.matrix_world@x.co for x in m.vertices]);f=np.array([q.vertices[:]for q in m.polygons],int);out[o['asset_id']]=(v,f);ev.to_mesh_clear()
 return out
p4=arrays('10_PASSE4_NEUTRE');p5=arrays('12_PASSE5_NEUTRE');w4=arrays('13_TEMOIN_PASSE4');w5=arrays('14_TEMOIN_PASSE5');after=arrays('15_PASSE6_NEUTRE');assert p4.keys()==w4.keys()and p5.keys()==w5.keys()==after.keys()
for original,witness in [(p4,w4),(p5,w5)]:
 for key in original:assert np.array_equal(original[key][0],witness[key][0])and np.array_equal(original[key][1],witness[key][1]),key
changed={'deltoid.right','deltoid.left'}
for key in set(p5)-changed:assert np.array_equal(p5[key][0],after[key][0])and np.array_equal(p5[key][1],after[key][1]),('Changed protected object',key)
def volume(v,f):return float(np.einsum('ij,ij->i',v[f[:,0]],np.cross(v[f[:,1]],v[f[:,2]])).sum()/6)
surface_checks={}
for key in sorted(changed):
 v,f=after[key];edges=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1);ue,c=np.unique(edges,axis=0,return_counts=True);assert(c==2).all()
 area=np.linalg.norm(np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]),axis=1)/2;assert np.all(area>1e-12)
 parents=np.arange(len(v))
 def find(i):
  while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
  return i
 for i,j in ue:
  x,y=find(int(i)),find(int(j))
  if x!=y:parents[y]=x
 components=len(set(find(i)for i in range(len(v))));assert components==1
 tree=BVHTree.FromPolygons(v.tolist(),f.tolist(),all_triangles=True);contacts=[(i,j)for i,j in tree.overlap(tree)if i<j and not np.isin(f[i],f[j]).any()];assert not contacts
 ratio=volume(v,f)/volume(*p4[key]);assert .85<ratio<1.005
 surface_checks[key]={'triangles':len(f),'closed_two_manifold':True,'components':components,'euler_characteristic':len(v)-len(ue)+len(f),'min_triangle_area_m2':float(area.min()),'nonadjacent_self_contacts_detected':len(contacts),'volume_ratio_to_p4':ratio,'bbox_p4_m':np.ptp(p4[key][0],axis=0).tolist(),'bbox_p5_m':np.ptp(p5[key][0],axis=0).tolist(),'bbox_p6_m':np.ptp(v,axis=0).tolist()}
r=after['deltoid.right'][0].copy();r[:,0]=2*plane-r[:,0];reflection=float(np.abs(r-after['deltoid.left'][0]).max());assert reflection<2e-7
def slice_width(v,f,z):
 points=[]
 for k,l in [(0,1),(1,2),(2,0)]:
  A=v[f[:,k]];B=v[f[:,l]];keep=(A[:,2]-z)*(B[:,2]-z)<0;A=A[keep];B=B[keep];t=(z-A[:,2])/(B[:,2]-A[:,2]);points.append(A+t[:,None]*(B-A))
 points=np.concatenate(points);return 2*(plane-float(points[:,0].min()))
widths=[{'z_m':float(z),'p4_m':slice_width(*p4['deltoid.right'],z),'p5_m':slice_width(*p5['deltoid.right'],z),'p6_m':slice_width(*after['deltoid.right'],z)}for z in np.linspace(1.33,1.485,41)];excess=max(x['p6_m']-x['p4_m']for x in widths);assert excess<.0015,('Frontal silhouette grew',excess)
integrate=getattr(np,'trapezoid',None)or np.trapz;area_ratio=integrate([x['p6_m']for x in widths],[x['z_m']for x in widths])/integrate([x['p4_m']for x in widths],[x['z_m']for x in widths]);assert area_ratio<1.005
# Fixed source patch samples, projected onto each actual shoulder surface.
v4,f4=p4['deltoid.right'];cross=np.cross(v4[f4[:,1]]-v4[f4[:,0]],v4[f4[:,2]]-v4[f4[:,0]]);norm=np.zeros_like(v4)
for k in range(3):np.add.at(norm,f4[:,k],cross)
norm/=np.maximum(np.linalg.norm(norm,axis=1)[:,None],1e-12);pv,pf=p5['pectoralis_major.right'];pec=BVHTree.FromPolygons(pv.tolist(),pf.tolist(),all_triangles=True);witness=[]
for i,point in enumerate(v4):
 if not(1.37<point[2]<1.48 and point[0]>-.225 and point[1]<.06 and .45*norm[i,0]-.75*norm[i,1]>.10):continue
 hit=pec.find_nearest(Vector(point),.014)
 if hit[0]is not None and np.dot(point-np.array(hit[0]),np.array(hit[1]))>=-.0002:witness.append(point)
contact_metrics={}
for label,state in [('p4',p4),('p5',p5),('p6',after)]:
 vv,ff=state['deltoid.right'];tree=BVHTree.FromPolygons(vv.tolist(),ff.tolist(),all_triangles=True);distances=[];signed=[]
 for point in witness:
  actual=tree.find_nearest(Vector(point))[0];hit=pec.find_nearest(actual);distances.append(float(hit[3]));signed.append(float((actual-hit[0]).dot(hit[1])))
 contact_metrics[label]={'samples':len(witness),'median_gap_m':float(np.median(distances)),'gap_p10_p90_m':np.percentile(distances,[10,90]).tolist(),'samples_signed_below_minus_1mm':int((np.array(signed)<-.001).sum())}
assert len(witness)>50
for name in ['13_TEMOIN_PASSE4','14_TEMOIN_PASSE5','15_PASSE6_NEUTRE']:
 scene=bpy.data.scenes[name]
 if not a.geometry_only:assert len([o for o in scene.objects if o.type=='LIGHT'])==5
 for ob in scene.objects:
  if ob.type=='MESH':assert ob.material_slots[0].material==bpy.data.materials['PASSE3_MAT_NEUTRE']
for side in ['right','left']:
 ob=bpy.data.scenes['15_PASSE6_NEUTRE'].objects['P6__deltoid.'+side];ids=[ob.vertex_groups[k].index for k in ['DELT_ANTERIEUR','DELT_MOYEN','DELT_POSTERIEUR']]
 for vertex in ob.data.vertices:assert abs(sum(g.weight for g in vertex.groups if g.group in ids)-1)<1e-3
report={'baseline_p5_sha256':meta['baseline_blend_sha256'],'baseline_p4_sha256':meta['p4_blend_sha256'],'new_master_sha256':sha(root/'ecorche-passe6.blend'),'comparison_witness_scenes_exact':True,'unchanged_objects':len(p5)-2,'head_throat_eyes_pectorals_arms_back_legs_exact_p5':True,'max_unchanged_coordinate_difference_m':0,'changed_objects':sorted(changed),'surface_checks':surface_checks,'deltoid_reflection_error_m':reflection,'frontal_width_profiles':widths,'max_frontal_width_excess_over_p4_m':excess,'frontal_support_area_ratio_to_p4':float(area_ratio),'deltopectoral_fixed_patch_projection':contact_metrics,'deltopectoral_method_scope':'Distances between actual surfaces at source-guided fixed patch samples, not a complete medical contact audit.','neutral_matte_material_verified':True,'authoring_weights_normalized':True,'objects':len(after),'master_triangles':sum(len(f)for v,f in after.values()),'new_triangles':meta['new_triangles'],'verifier_sha256':sha(Path(__file__))}
if a.geometry_only:
 print('PASSE6_GEOMETRY_VERIFIED',json.dumps(report),flush=True);sys.exit(0)

# Decode every serialized glTF triangle and compare it against the final master.
raw=(root/'ecorche-passe6.glb').read_bytes();size=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+size]);binary=raw[28+size:]
def accessor(index):
 ac=doc['accessors'][index];view=doc['bufferViews'][ac['bufferView']];width={'SCALAR':1,'VEC3':3,'VEC4':4}[ac['type']];dtype=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2'}[ac['componentType']]);return np.ndarray((ac['count'],width),dtype=dtype,buffer=binary,offset=view.get('byteOffset',0)+ac.get('byteOffset',0),strides=(view.get('byteStride',width*dtype.itemsize),dtype.itemsize)).copy()
def signatures(v,f):
 q=np.rint(v[f]*1e6).astype('<i4');order=np.lexsort((q[:,:,2],q[:,:,1],q[:,:,0]),axis=1);q=np.ascontiguousarray(np.take_along_axis(q,order[:,:,None],axis=1).reshape(-1,9));return np.sort(q.view(np.dtype([(f'c{i}','<i4')for i in range(9)])).ravel())
triangles=vertices=0;omissions=[];assert len(doc['nodes'])==len(after)and len(doc['materials'])==1
for node in doc['nodes']:
 key=node['name'];assert key in after and not any(k in node for k in ['matrix','translation','rotation','scale']);primitive=doc['meshes'][node['mesh']]['primitives'][0];assert not any(k.startswith('COLOR_')for k in primitive['attributes']);v=accessor(primitive['attributes']['POSITION']).astype(float);v=v[:,[0,2,1]];v[:,1]*=-1;f=accessor(primitive['indices']).reshape(-1,3);triangles+=len(f);vertices+=len(v);expected=signatures(*after[key]);actual=signatures(v,f);assert not len(np.setdiff1d(actual,expected))
 if not np.array_equal(expected,actual):
  s0,c0=np.unique(expected,return_counts=True);s1,c1=np.unique(actual,return_counts=True);remain=np.zeros(len(s0),int);remain[np.searchsorted(s0,s1)]=c1;difference=c0-remain;assert(difference>=0).all()
  for i in np.flatnonzero(difference):assert remain[i]>0;omissions.append({'asset_id':key,'removed_copies':int(difference[i]),'copies_remaining':int(remain[i])})
assert 'CC BY 4.0'in doc['asset']['copyright']and 'CC0'in doc['asset']['copyright']and doc['asset']['extras']['baseline_commit']==meta['baseline_commit']
scene=bpy.data.scenes.new('VERIFY_PASSE6_IMPORT');bpy.context.window.scene=scene;bpy.ops.import_scene.gltf(filepath=str(root/'ecorche-passe6.glb'),merge_vertices=False);imported=[o for o in scene.objects if o.type=='MESH'];assert len(imported)==len(after)and sum(sum(len(f.vertices)-2 for f in o.data.polygons)for o in imported)==triangles
frames=json.loads((root/'renders/metadata.json').read_text());assert len(frames['frames'])==21 and frames['final_blend_sha256']==sha(root/'ecorche-passe6.blend');assert all(sha(root/'renders'/f['file'])==f['sha256']for f in frames['frames']);report.update({'glb_sha256':sha(root/'ecorche-passe6.glb'),'glb_triangles':triangles,'glb_vertices':vertices,'glb_surface_match_at_micron_quantization':True,'glb_duplicate_faces_removed':omissions,'glb_reimport_verified':True,'render_files_hash_verified':21,'scope':'Asset geometry/export checks only; no clinical certification, exhaustive inter-object contact audit or mobile FPS test.'})
(root/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('PASSE6_VERIFIED',json.dumps(report),flush=True)
