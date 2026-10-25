"""Reconstruct a closed midline attachment surface embedded beneath trapezius banks.

This is an atlas-style connective attachment, not an independently validated
medical ligament. No original muscle mesh is fused or renamed.
"""
import argparse,json,hashlib,math,sys
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=argparse.ArgumentParser();p.add_argument('--asset',type=Path,required=True);p.add_argument('--preview',type=Path);p.add_argument('--build-only',action='store_true');a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.asset.resolve();file=root/'ecorche-passe3.blend'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
input_sha=sha(file);meta=json.loads((root/'passe3.json').read_text());plane=meta['median_plane_x_m'];bpy.ops.wm.open_mainfile(filepath=str(file),use_scripts=False);scene=bpy.data.scenes['08_PASSE3_NEUTRE'];bpy.context.window.scene=scene;scene.view_layers[0].update();graph=bpy.context.evaluated_depsgraph_get();ob=scene.objects['P3__trapezius.right'];ev=ob.evaluated_get(graph);mesh=ev.to_mesh();v=np.array([x.co[:]for x in mesh.vertices]);f=np.array([q.vertices[:]for q in mesh.polygons],int);tree=BVHTree.FromPolygons(v.tolist(),f.tolist(),all_triangles=True);ev.to_mesh_clear()
rows=[];embedding=[]
for z in np.linspace(1.29,1.685,80):
 candidates=[]
 for d in [.006,.008,.010,.012,.016]:
  hit=tree.ray_cast(Vector((plane-d,1,float(z))),Vector((0,-1,0)),2)
  if hit[0]is not None:candidates.append((d,float(hit[0].y)))
 if not candidates:continue
 width,y=candidates[min(1,len(candidates)-1)]
 # Ends taper within the surrounding attachment; side edges sit below
 # existing posterior muscle banks, which occlude the construction boundary.
 taper=min(1,(z-1.29)/.025,(1.685-z)/.025);taper=max(.18,taper);width*=taper
 hit=tree.ray_cast(Vector((plane-width,1,float(z))),Vector((0,-1,0)),2)
 if hit[0]is not None:y=float(hit[0].y)
 rows.append((float(z),width,y));embedding.append(y)
assert len(rows)>50
vertices=[];columns=17
for depth in [0,.004]:
 for z,width,y in rows:
  for s in np.linspace(-1,1,columns):vertices.append((plane+s*width,y-.00055-.0012*(1-s*s)-depth,z))
N=len(rows)*columns;faces=[]
for r in range(len(rows)-1):
 for c in range(columns-1):
  i=r*columns+c;j=i+columns;faces.extend([(i,i+1,j),(i+1,j+1,j),(N+i,N+j,N+i+1),(N+i+1,N+j,N+j+1)])
for r in range(len(rows)-1):
 for c in [0,columns-1]:
  i=r*columns+c;j=i+columns;faces.extend([(i,N+i,j),(j,N+i,N+j)]if c==0 else[(i,j,N+i),(j,N+j,N+i)])
for r in [0,len(rows)-1]:
 for c in range(columns-1):
  i=r*columns+c;faces.extend([(i,i+1,N+i),(i+1,N+i+1,N+i)]if r==0 else[(i,N+i,i+1),(i+1,N+i,N+i+1)])
mesh=bpy.data.meshes.new('ATTACHE_MEDIANE_RECONSTRUITE');mesh.from_pydata(vertices,[],faces);mesh.update()
# Recalculate consistent outward winding on the closed loft.
import bmesh
bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
for poly in mesh.polygons:poly.use_smooth=True
mesh.materials.append(bpy.data.materials['PASSE3_MAT_NEUTRE']);ob=bpy.data.objects.new('P3__trapezius_attachment.reconstructed_midline',mesh);scene.collection.objects.link(ob);ob['asset_id']='trapezius_attachment.reconstructed_midline';ob['source_piece_id']='new_reconstructed_connective_attachment';ob['anatomical_label_validated']=False;ob['interactive_muscle_zone']=False;ob['role']='Connective midline attachment, embedded under the paired trapezius surfaces; no original muscle replacement.'
addition={'asset_id':ob['asset_id'],'objects':1,'triangles':len(mesh.polygons),'construction':'Closed 4 mm deep loft; side edges embedded 0.55 mm below sampled posterior trapezius banks; shallow 1.2 mm central groove.','z_range_m':[rows[0][0],rows[-1][0]],'width_range_m':[2*min(x[1]for x in rows),2*max(x[1]for x in rows)],'anatomical_status':'Stylized connective attachment; not a certified medical ligament.','builder_sha256':sha(Path(__file__))}
def aim(ob,target):ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
if a.preview:
 rig=bpy.data.collections.new('ATTACHE_PREVIEW');scene.collection.children.link(rig)
 for label,x,y,z,power,size in [('Avant',3,-3,2.6,200,2.2),('Dos',2,3,3,180,2.2)]:
  for side in [-1,1]:
   light=bpy.data.lights.new('preview','AREA');light.energy=power;light.size=size;light.shape='DISK';lamp=bpy.data.objects.new('preview',light);rig.objects.link(lamp);lamp.location=(plane+side*x,y,z);aim(lamp,(plane,0,1))
 light=bpy.data.lights.new('centre','AREA');light.energy=100;light.size=2;lamp=bpy.data.objects.new('centre',light);rig.objects.link(lamp);lamp.location=(plane,-4,4);aim(lamp,(plane,0,1))
 camera=bpy.data.cameras.new('preview');camera.type='ORTHO';camera.ortho_scale=.49;cam=bpy.data.objects.new('preview',camera);rig.objects.link(cam);cam.location=(plane,4.11,1.45);aim(cam,(plane,.11,1.45));scene.camera=cam
 world=bpy.data.worlds.new('preview');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(.045,.045,.045,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.30;scene.world=world;scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=False;scene.render.resolution_x=960;scene.render.resolution_y=960;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG';scene.render.filepath=str(a.preview.resolve());bpy.ops.render.render(write_still=True,scene=scene.name);print('MIDLINE_PREVIEW',json.dumps(addition),flush=True)
else:
 metadata=None
 if not a.build_only:
  metadata=json.loads((root/'renders/metadata.json').read_text());assert len(metadata['frames'])==20 and metadata['final_blend_sha256']==input_sha
 meta['additional_connective_attachment']=addition;meta['objects']+=1;meta['triangles']+=len(mesh.polygons);meta['new_triangles']+=len(mesh.polygons);meta['midline_input_master_sha256']=input_sha
 (root/'passe3.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n');bpy.data.texts.new('PASSE3_ATTACHE_MEDIANE.json').write(json.dumps(addition,ensure_ascii=False,indent=2))
 if a.build_only:
  bpy.ops.wm.save_as_mainfile(filepath=str(file),compress=True);print('MIDLINE_GEOMETRY_BUILT',json.dumps(addition),flush=True);sys.exit(0)
 metadata['midline_revision']={'input_master_sha256':input_sha,'renderer_sha256':sha(Path(__file__)),'unchanged_before_frames_reused':True}
 for frame in metadata['frames']:
  if not frame['file'].startswith('apres-'):frame['retained_from_original_passe2_comparison']=True;continue
  scene.camera=bpy.data.objects['P3_'+frame['camera']];scene.render.resolution_x,scene.render.resolution_y=frame['size'];scene.render.resolution_percentage=100;scene.render.filepath=str(root/'renders'/frame['file']);bpy.ops.render.render(write_still=True,scene=scene.name);frame['sha256']=sha(root/'renders'/frame['file']);frame['revision']='midline_attachment';(root/'renders/metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
 bpy.ops.wm.save_as_mainfile(filepath=str(file),compress=True);metadata['final_blend_sha256']=sha(file);(root/'renders/metadata.json').write_text(json.dumps(metadata,indent=2)+'\n');print('MIDLINE_FINALIZED',json.dumps(addition),flush=True)
