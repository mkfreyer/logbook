"""Reconstruct a continuous fitness atlas from verified BP3D muscle volumes.

BP3D is the anatomical source. The B+ head/eyes are finishing components only.
Two bounded constructions, no application changes or third-party atlas imports.
"""
import argparse,hashlib,json,math,sys,zipfile
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Vector,kdtree
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--groups',type=Path,required=True);p.add_argument('--head',type=Path,required=True);p.add_argument('--variant',choices=['soft','defined'],required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.output.mkdir(parents=True,exist_ok=True)
assert hashlib.sha256(a.archive.read_bytes()).hexdigest()=='40665852c49f218326590e204db91064a1ecfc3c6f8cbd7bbbcaac62c7cd409e'
groups=json.loads(a.groups.read_text());repo=Path(__file__).resolve().parents[2];ref=json.loads((repo/'docs/m4a/ecorche/bodyparts3d/inventory.json').read_text())['transform'];center=np.array(ref['center']);scale=ref['uniform_scale']
cfg={'soft':dict(inset=.90,bulk=.18,voxel=.0036,smooth=4,budget=96000),'defined':dict(inset=.84,bulk=.25,voxel=.0031,smooth=3,budget=120000)}[a.variant]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
archive=zipfile.ZipFile(a.archive);entries={Path(n).stem:n for n in archive.namelist() if n.endswith('.obj')};sources=[];pieces=[];samples=[];sample_ids=[]
def sig(t):t=np.clip(t,0,1);return t*t*(3-2*t)
def gauss(t,c,w):return np.exp(-((t-c)/w)**2)
def read_obj(element):
 raw=archive.read(entries[element]);vertices=[];faces=[]
 for line in raw.decode().splitlines():
  b=line.split()
  if b and b[0]=='v':vertices.append([float(x) for x in b[1:4]])
  elif b and b[0]=='f':faces.append([int(x.split('/')[0])-1 for x in b[1:]])
 xyz,index=np.unique(np.array(vertices),axis=0,return_inverse=True);ix=index[np.array(faces)]
 sources.append({'element_id':element,'sha256':hashlib.sha256(raw).hexdigest(),'source_triangles':len(ix)})
 return (xyz-center)*scale,ix

def warp(xyz):
 q=xyz.copy();x=np.abs(q[:,0]);y=q[:,1];z=q[:,2];side=np.sign(q[:,0])
 width=1.15+.075*gauss(z,1.43,.17)-.13*gauss(z,1.12,.13)
 xx=x*width;yy=.02+(y-.02)*1.08
 boundary=np.interp(z,[.65,.95,1.20,1.43,1.55],[.205,.195,.145,.120,.15])
 arm=sig((x-boundary)/.022)*sig((1.515-z)/.090)
 angle=-math.radians(13)*arm;dx=xx-.195*1.19;dz=z-1.47
 rx=dx*np.cos(angle)+dz*np.sin(angle)+.195*1.19
 rz=-dx*np.sin(angle)+dz*np.cos(angle)+1.47
 xx=xx*(1-arm)+rx*arm;zz=z*(1-arm)+rz*arm
 xx+=.009*sig((.94-z)/.12)*sig((z-.10)/.10)
 return np.column_stack([side*xx,yy,zz])

def activate(ob):
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob

def make(name,xyz,faces):
 m=bpy.data.meshes.new(name);m.from_pydata(xyz.tolist(),[],faces.tolist() if hasattr(faces,'tolist') else faces);m.update();o=bpy.data.objects.new(name,m);bpy.context.collection.objects.link(o);return o

def clean(ob,largest=False):
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-9)
 todo=set(bm.verts);parts=[]
 while todo:
  stack=[todo.pop()];part=[]
  while stack:
   v=stack.pop();part.append(v)
   for e in v.link_edges:
    n=e.other_vert(v)
    if n in todo:todo.remove(n);stack.append(n)
  parts.append(part)
 keep=max(parts,key=len) if parts else [];discard=[v for c in parts for v in c if (c is not keep if largest else len(c)<12)]
 if discard:bmesh.ops.delete(bm,geom=discard,context='VERTS')
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free();ob.data.update();return len(discard)

def cut(ob,point,normal,inside=True):
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-6,plane_co=point,plane_no=normal,clear_inner=inside,clear_outer=not inside)
 edges=[e for e in bm.edges if e.is_boundary]
 if edges:bmesh.ops.holes_fill(bm,edges=edges,sides=0)
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free();ob.data.update()

def smooth(ob,n):
 activate(ob);m=ob.modifiers.new('Remove source micro-noise','SMOOTH');m.factor=.55;m.iterations=n;bpy.ops.object.modifier_apply(modifier=m.name)

skin,faces=read_obj('FJ2810');x=np.abs(skin[:,0]);y=skin[:,1];z=skin[:,2];side=np.sign(skin[:,0]);q=skin.copy()
boundary=np.interp(z,[.65,.95,1.20,1.43,1.55],[.205,.195,.145,.120,.15]);arm=sig((x-boundary)/.022)*sig((1.515-z)/.090);leg=sig((.97-z)/.12)
limb_center=(.19+.06*np.clip((1.43-z)/.55,0,1))*arm+.105*leg*(1-arm)
protect=np.maximum(sig((.15-z)/.05),arm*sig((.99-z)/.05));shrink=1-(1-cfg['inset'])*(1-protect)
q[:,0]=side*(limb_center+(x-limb_center)*shrink);q[:,1]=.02+(y-.02)*shrink
neutral=sig((z-.76)/.035)*sig((1.005-z)/.045)*sig((.08-x)/.020);q[:,1]=np.maximum(q[:,1],-.055)*neutral+q[:,1]*(1-neutral)
ob=make('Recessed BP3D skin support',warp(q),faces);cut(ob,(0,0,1.555),(0,0,1),False);smooth(ob,3);pieces.append(ob)
# Skin support is explicitly nonselectable; preserve source muscle IDs elsewhere.
coords=np.array([v.co[:] for v in ob.data.vertices]);samples.extend(coords[::8]);sample_ids.extend([0]*len(coords[::8]))
for row in groups['groups']:
 for element in row['element_ids']:
  xyz,faces=read_obj(element);ob=make(element,xyz,faces);clean(ob)
  if row['family']=='obliques':cut(ob,(.055 if row['side']=='left' else -.055,0,0),(1 if row['side']=='left' else -1,0,0),True)
  if row['family']=='avant-bras':cut(ob,(0,0,.945),(0,0,1),True)
  if not len(ob.data.vertices):raise RuntimeError('Empty source group '+element)
  smooth(ob,3);xyz=np.array([v.co[:] for v in ob.data.vertices]);c=xyz.mean(0);lo=xyz[:,2].min();hi=xyz[:,2].max();belly=np.sin(np.pi*np.clip((xyz[:,2]-lo)/max(hi-lo,.001),0,1))**2
  xyz[:,:2]=c[:2]+(xyz[:,:2]-c[:2])*(1+cfg['bulk']*belly[:,None]);xyz=warp(xyz);ob.data.vertices.foreach_set('co',xyz.ravel());ob.data.update()
  samples.extend(xyz);sample_ids.extend([row['zone_id']]*len(xyz));pieces.append(ob)
 print('GROUP',row['family'],row['side'],len(row['element_ids']),flush=True)
# Original artistic complements: missing official identities are never fabricated.
for row in groups['groups']:
 if row['element_ids']:continue
 side=1 if row['side']=='left' else -1;verts=[];faces=[];rings=36;segments=32
 if row['family']=='abdominaux':
  for i in range(rings+1):
   t=i/rings;zz=1.025+.290*t;belly=np.sin(np.pi*t)**.65
   pulse=sum(.16*math.exp(-((t-c)/.075)**2) for c in [.30,.55,.80]);rx=(.023+.007*pulse)*(.22+.78*belly);ry=.014*(.35+.65*belly)*(1+pulse)
   for j in range(segments):
    a0=2*np.pi*j/segments;verts.append([side*(.032+rx*np.cos(a0)),-(.115-.025*t)+ry*np.sin(a0),zz])
 else:
  for i in range(rings+1):
   t=i/rings;zz=1.055+.380*t;cx=.045+.095*t;rx=.018+.060*np.sin(np.pi*t)**.9;ry=.010+.018*np.sin(np.pi*t)
   for j in range(segments):
    a0=2*np.pi*j/segments;verts.append([side*(cx+rx*np.cos(a0)),(.115-.025*t)+ry*np.sin(a0),zz])
 for i in range(rings):
  for j in range(segments):faces.append((i*segments+j,i*segments+(j+1)%segments,(i+1)*segments+(j+1)%segments,(i+1)*segments+j))
 faces.append(tuple(reversed(range(segments))));faces.append(tuple(rings*segments+j for j in range(segments)))
 xyz=warp(np.array(verts));ob=make('Authored '+row['family']+'.'+row['side'],xyz,faces);clean(ob);pieces.append(ob);samples.extend(xyz);sample_ids.extend([row['zone_id']]*len(xyz))
# Buried continuous tissue supports at abdomen and pelvis seal source tangencies.
for name,loc,radii in [('abdominal junction support',(0,-.050,1.16),(.106,.043,.182)),('neutral pelvic cover',(0,-.015,.89),(.085,.072,.125))]:
 bpy.ops.mesh.primitive_uv_sphere_add(segments=40,ring_count=28);ob=bpy.context.object;ob.name=name
 xyz=np.array([v.co[:] for v in ob.data.vertices])*np.array(radii)+np.array(loc);xyz=warp(xyz);ob.data.vertices.foreach_set('co',xyz.ravel());ob.data.update();pieces.append(ob)
# A small dilation before union seals millimetric source gaps, not anatomy detail.
for ob in pieces:
 ob.data.update();norm=np.array([v.normal[:] for v in ob.data.vertices]);xyz=np.array([v.co[:] for v in ob.data.vertices]);xyz+=norm*.0018;ob.data.vertices.foreach_set('co',xyz.ravel());ob.data.update()
# Only the neutral head and eyes are reused from B+, not its torso or limbs.
with bpy.data.libraries.load(str(a.head.resolve()),link=False) as (src,dst):dst.objects=['BPF.body','BPF.eye.L','BPF.eye.R']
head,eye_l,eye_r=dst.objects
for o in dst.objects:bpy.context.scene.collection.objects.link(o)
cut(head,(0,0,1.535),(0,0,1),True)
for o in dst.objects:
 for v in o.data.vertices:v.co.y+=.028
 o.data.materials.clear()
pieces.append(head);eyes=[eye_l,eye_r]
# One anatomical envelope prevents floating component meshes and hides deep layers.
bpy.ops.object.select_all(action='DESELECT')
for o in pieces:o.select_set(True)
bpy.context.view_layer.objects.active=pieces[0];bpy.ops.object.join();body=bpy.context.object;body.name='BP3D fitness continuous body'
activate(body);m=body.modifiers.new('Integrated muscle and support union','REMESH');m.mode='VOXEL';m.voxel_size=cfg['voxel'];m.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=m.name)
smooth(body,cfg['smooth']);removed=clean(body,True)
body.data.calc_loop_triangles();n=len(body.data.loop_triangles)
if n>cfg['budget']:
 activate(body);m=body.modifiers.new('Mobile research budget','DECIMATE');m.ratio=cfg['budget']/n;m.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=m.name)
clean(body,True);body.data.calc_loop_triangles()
# Transfer provisional region IDs from the actual retained source surfaces.
tree=kdtree.KDTree(len(samples))
for i,co in enumerate(samples):tree.insert(co,i)
tree.balance();ids=[]
for face in body.data.polygons:
 co=face.center;near,index,distance=tree.find(co);zone=sample_ids[index] if distance<.037 else 0
 if co.z<.145 or co.z>1.58 or (abs(co.x)>.35 and co.z<1.0):zone=0
 ids.append(zone)
attr=body.data.attributes.new('m4a_fitness_zone','INT','FACE');attr.data.foreach_set('value',np.array(ids,dtype=np.int32))
for o in [body]+eyes:
 o['m4a_render']=True;o['m4a_role']='body' if o==body else 'eye';o['m4a_variant']=a.variant
 for f in o.data.polygons:f.use_smooth=True
 o.data.calc_loop_triangles()
report={'variant':a.variant,'source_archive_sha256':hashlib.sha256(a.archive.read_bytes()).hexdigest(),'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'source_head_sha256':hashlib.sha256(a.head.read_bytes()).hexdigest(),
 'anatomy':'Direct BodyParts3D audited source OBJ volumes, selected and warped; no Ecorche or Z-Anatomy geometry.',
 'head_reuse':'B+ neutral head above z=1.535 and its two eyes only; no B+ torso or limbs.', 'settings':cfg,'source_records':sources,
 'authored_complements':['dorsaux.left','dorsaux.right','abdominaux.left','abdominaux.right'],'authoring_claim':'Approximate artistic fitness volumes, no verified BP3D element/FMA identity for these complements.',
 'counts':{'visible_triangles':sum(len(o.data.loop_triangles) for o in [body]+eyes),'body_triangles':len(body.data.loop_triangles),'body_vertices':len(body.data.vertices),'objects':3,'region_ids_available':sorted(set(ids))},
 'zone_triangles':{str(k):ids.count(k) for k in sorted(set(ids))},'source_dilation_m':.0018,'underlays':['abdominal junction support','neutral pelvic cover'],'removed_union_fragment_vertices':removed,'license_for_derived_models_and_renders':'CC-BY-SA-4.0',
 'limitations':['Region transfer is provisional nearest-source surface classification, not final anatomical segmentation.','No iPhone runtime, rig or medical validation.','Voxel union and decimation alter fine anatomical detail.']}
(a.output/'construction.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
bpy.data.orphans_purge(do_recursive=True);bpy.ops.wm.save_as_mainfile(filepath=str(a.output/'model.blend'),compress=True);print('FITNESS_BUILD',json.dumps(report['counts']),flush=True)
