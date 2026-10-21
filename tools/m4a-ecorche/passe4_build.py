"""Pass four: anterior deltoid redistribution and a locally rebuilt neutral head/throat.

Prior scenes and muscles remain available; only the new proposal substitutes
the fine head dissection with a source-guided continuous presentation surface.
"""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils.bvhtree import BVHTree
p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--surface',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.output.resolve();root.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(a.baseline)=='cfe710f5efd581922f46c0d25d4178cc81de74137fd2761716ad95516fdf13b8'
prior=json.loads((a.baseline.parent/'passe3.json').read_text());plane=prior['median_plane_x_m'];surface=np.load(a.surface);bpy.ops.wm.open_mainfile(filepath=str(a.baseline.resolve()),use_scripts=False)
source=bpy.data.scenes['08_PASSE3_NEUTRE'];bpy.context.window.scene=source;source.view_layers[0].update();g=bpy.context.evaluated_depsgraph_get();snap={};original={}
for o in source.objects:
 if o.type!='MESH':continue
 m=bpy.data.meshes.new_from_object(o.evaluated_get(g),preserve_all_data_layers=True,depsgraph=g);v=np.array([o.matrix_world@q.co for q in m.vertices]);f=np.array([q.vertices[:]for q in m.polygons],int);snap[o['asset_id']]=(v,f,m);original[o['asset_id']]=o
before=bpy.data.scenes.new('09_AVANT_PASSE4');after=bpy.data.scenes.new('10_PASSE4_NEUTRE');mat=bpy.data.materials['PASSE3_MAT_NEUTRE']
def smooth(t):t=np.clip(t,0,1);return t*t*(3-2*t)
def volume(v,f):return float(np.einsum('ij,ij->i',v[f[:,0]],np.cross(v[f[:,1]],v[f[:,2]])).sum()/6)
v,f,_=snap['deltoid.right'];cross=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]);normal=np.zeros_like(v)
for k in range(3):np.add.at(normal,f[:,k],cross)
normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-12)
t=np.clip((v[:,2]-1.286)/.217,0,1);ax=-.241+.057*t;ay=.080-.010*t;r=np.column_stack([v[:,0]-ax,v[:,1]-ay,np.zeros(len(v))]);r/=np.maximum(np.linalg.norm(r,axis=1)[:,None],1e-12);theta=np.arctan2(v[:,1]-ay,ax-v[:,0]);outer=smooth((np.einsum('ij,ij->i',normal,r)-.05)/.65);ends=smooth((t-.12)/.20)*smooth((.96-t)/.17)
# Move the front/middle transition posteriorly over a broad fan, not an incision.
front=np.exp(-.5*((theta+.67)/.34)**2);middle_front=np.exp(-.5*((theta+.18)/.28)**2);belly=np.exp(-.5*((t-.64)/.25)**2);mask=outer*ends
angular=np.exp(-.5*((theta+.36)/.36)**2)*belly*mask
tangent=np.column_stack([np.sin(theta),np.cos(theta),np.zeros(len(v))]);delta=.0028*tangent*angular[:,None]
delta+=r*(.0022*(front-.72*middle_front)*belly*mask)[:,None]
delta[:,2]+=.0030*front*belly*mask
q=v+delta
# Restore the original closed shoulder volume through broad normal compensation.
goal=volume(v,f);lo=-.005;hi=.005
for _ in range(45):
 mid=(lo+hi)/2;test=q+normal*(mask*mid)[:,None]
 if (volume(test,f)-goal)*np.sign(goal)>0:hi=mid
 else:lo=mid
q+=normal*(mask*((lo+hi)/2))[:,None]
# Reject contact/collapse instead of introducing patchy per-vertex constraints.
tree=BVHTree.FromPolygons(q.tolist(),f.tolist(),all_triangles=True);contacts=[(i,j)for i,j in tree.overlap(tree)if i<j and not np.isin(f[i],f[j]).any()]
assert not contacts,('shoulder self-contact',len(contacts))
newcross=np.cross(q[f[:,1]]-q[f[:,0]],q[f[:,2]]-q[f[:,0]]);assert np.all(np.linalg.norm(newcross,axis=1)>.08*np.linalg.norm(cross,axis=1))
left=q.copy();left[:,0]=2*plane-left[:,0];changes={'deltoid.right':q,'deltoid.left':left};removed=[]
for key,(v,f,m)in snap.items():
 old=bpy.data.objects.new('P4_BASE__'+key,m);before.collection.objects.link(old);old['asset_id']=key
 for slot in old.material_slots:slot.link='OBJECT';slot.material=mat
 # Entirely cranial / facial pieces are kept in all historical/before scenes.
 # They are substituted only in the new presentation scene, not merged into muscles.
 if v[:,2].min()>=1.57:removed.append(key);continue
 mesh=m.copy()if key in changes else m
 ob=bpy.data.objects.new('P4__'+key,mesh);after.collection.objects.link(ob)
 for prop in original[key].keys():ob[prop]=original[key][prop]
 for slot in ob.material_slots:slot.link='OBJECT';slot.material=mat
 if key in changes:
  ob.shape_key_add(name='AVANT_PASSE4');sk=ob.shape_key_add(name='FINITION_ANTERIEURE_PASSE4');sk.data.foreach_set('co',changes[key].astype(np.float32).ravel());sk.value=1
  # Keep the existing authoring groups, shifting their transition with the shape.
  src=original[key]
  for group in src.vertex_groups:
   ng=ob.vertex_groups.new(name=group.name)
   for vertex in src.data.vertices:
    for entry in vertex.groups:
     if entry.group==group.index:ng.add([vertex.index],entry.weight,'REPLACE')
  ob['deltoid_regions']='Three overlapping source-guided authoring groups, anterior belly raised and front/middle transition redistributed in pass four; not final medical segmentation.'
mesh=bpy.data.meshes.new('PASSE4_TETE_GORGE_CONTINUE');mesh.from_pydata(surface['v'].tolist(),[],surface['f'].tolist());mesh.update();bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free();ob=bpy.data.objects.new('P4__head_throat.neutral_surface',mesh);after.collection.objects.link(ob);bpy.context.window.scene=after;after.view_layers[0].objects.active=ob;ob.select_set(True)
dec=ob.modifiers.new('RESOLUTION_TETE_GORGE','DECIMATE');dec.ratio=.23;dec.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=dec.name)
for poly in ob.data.polygons:poly.use_smooth=True
ob.data.materials.append(mat);ob['asset_id']='head_throat.neutral_surface';ob['source_piece_id']='source_guided_head_and_throat_envelope';ob['anatomical_label_validated']=False;ob['interactive_muscle_zone']=False;ob['role']='Simplified continuous neutral presentation surface for head and anterior throat; not an independently selectable training muscle.'
record={'volume_before_m3':goal,'volume_after_m3':volume(changes['deltoid.right'],snap['deltoid.right'][1]),'max_displacement_m':float(np.linalg.norm(changes['deltoid.right']-snap['deltoid.right'][0],axis=1).max()),'bbox_before_m':np.ptp(snap['deltoid.right'][0],axis=0).tolist(),'bbox_after_m':np.ptp(changes['deltoid.right'],axis=0).tolist(),'nonadjacent_self_contacts_detected':len(contacts),'topology_unchanged':True}
metadata={'baseline_commit':'033a92ae274d26f6043404ba1a435e0cc8a9ff8f','baseline_blend_sha256':sha(a.baseline),'source_asset':prior['source_asset'],'source_sha256':prior['source_sha256'],'median_plane_x_m':plane,'before_objects':len(snap),'before_triangles':sum(len(x[1])for x in snap.values()),'objects':sum(o.type=='MESH'for o in after.objects),'triangles':sum(len(o.data.polygons)for o in after.objects if o.type=='MESH'),'changed_original_objects':sorted(changes),'substituted_head_pieces':sorted(removed),'unchanged_original_objects':len(snap)-len(changes)-len(removed),'new_surface':{'asset_id':ob['asset_id'],'triangles':len(ob.data.polygons),'z_range_m':[float(surface['v'][:,2].min()),float(surface['v'][:,2].max())],'interactive_muscle_zone':False},'shoulder_right':record,'surface_method':json.loads(a.surface.with_suffix('.json').read_text()),'builder_sha256':sha(Path(__file__)),'limitations':['Neutral head is a stylized presentation envelope; not a clinically validated facial reconstruction.','Authoring groups do not provide final selectable deltoid head segmentation.','No full-body intersection certification or mobile performance validation.']}
(root/'passe4.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n');bpy.data.texts.new('PASSE4_CORRECTIONS.json').write(json.dumps(metadata,ensure_ascii=False,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(root/'ecorche-passe4.blend'),compress=True);print('PASSE4_BUILT',json.dumps(metadata),flush=True)
