"""One bounded anatomical fan/shoulder-loft experiment on B+ Puissance.

Original parametrized anatomy, no imported anatomical assets. The method is
experimental and must pass visual review; a closed mesh alone is not success.
"""
import argparse,hashlib,json,math,sys
from pathlib import Path
import bpy,bmesh,numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.source=a.source.resolve();a.output.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(a.source),use_scripts=False)
body=bpy.data.objects['BPF.body'];mesh=body.data
original=np.array([v.co[:] for v in mesh.vertices]);original_triangles=len(mesh.polygons)
def sig(t):
    t=np.clip(t,0,1);return t*t*(3-2*t)
def support(points):
    x=np.abs(points[:,0]);y=points[:,1];z=points[:,2]
    chest=(x<.244)&(y<.020)&(z>1.282)&(z<1.482)
    shoulder=(points[:,0]<-.166)&(points[:,0]>-.321)&(np.abs(y-.025)<.124)&(z>1.294)&(z<1.512)
    return chest|shoulder
# Adaptive triangular refinement with shared edge midpoints. Neighboring
# triangles split conformingly; every original vertex is retained exactly.
old_faces=[tuple(f.vertices) for f in mesh.polygons];old_attributes={}
for attr in mesh.attributes:
    if attr.domain=='POINT' and attr.data_type=='FLOAT':old_attributes[attr.name]=np.array([v.value for v in attr.data])
inside=support(original);cut={}
for edge in mesh.edges:
    i,j=sorted(edge.vertices)
    if inside[i] and inside[j]:cut[(i,j)]=len(original)+len(cut)
vertices=original.tolist()+[((original[i]+original[j])*.5).tolist() for i,j in cut]
def mid(i,j):return cut.get(tuple(sorted((i,j))))
faces=[]
for aa,bb,cc in old_faces:
    ab,bc,ca=mid(aa,bb),mid(bb,cc),mid(cc,aa);count=sum(v is not None for v in [ab,bc,ca])
    if count==0:faces.append((aa,bb,cc))
    elif count==3:faces.extend([(aa,ab,ca),(ab,bb,bc),(ca,bc,cc),(ab,bc,ca)])
    else:
        ring=[aa,bb,cc]
        if count==1:
            for k in range(3):
                a0,b0,c0=ring[k:]+ring[:k];m0=mid(a0,b0)
                if m0 is not None:faces.extend([(a0,m0,c0),(m0,b0,c0)]);break
        else:
            for k in range(3):
                a0,b0,c0=ring[k:]+ring[:k];m0,m1=mid(a0,b0),mid(b0,c0)
                if m0 is not None and m1 is not None:
                    faces.extend([(m0,b0,m1),(a0,m0,c0),(m0,m1,c0)]);break
newmesh=bpy.data.meshes.new('B+ continuous local anatomical experiment');newmesh.from_pydata(vertices,[],faces);newmesh.update()
for name,values in old_attributes.items():
    expanded=np.concatenate([values,np.array([(values[i]+values[j])*.5 for i,j in cut])])
    attr=newmesh.attributes.new(name,'FLOAT','POINT');attr.data.foreach_set('value',expanded.astype(np.float32))
body.data=newmesh;mesh=newmesh
for f in mesh.polygons:f.use_smooth=True
mesh.calc_loop_triangles()
xyz=np.array([v.co[:] for v in mesh.vertices]);source=xyz.copy();x=np.abs(xyz[:,0]);y=xyz[:,1];z=xyz[:,2]
allowed=support(xyz);front=sig((.025-y)/.055)
# Smooth only the anterior chest's old stamped envelope, along its original
# edge graph; extremities, torso below the patch and opposite shoulder stay fixed.
edge_indices=np.array([e.vertices[:] for e in mesh.edges]);degree=np.bincount(edge_indices.ravel(),minlength=len(xyz))
fair=sig((x-.006)/.020)*sig((.241-x)/.028)*sig((z-1.282)/.025)*sig((1.482-z)/.025)*front
fair*=allowed
for _ in range(20):
    total=np.zeros(len(xyz));np.add.at(total,edge_indices[:,0],xyz[edge_indices[:,1],1]);np.add.at(total,edge_indices[:,1],xyz[edge_indices[:,0],1])
    xyz[:,1]+=.35*fair*(total/degree-xyz[:,1])
# Pectoral loft: medial origin spread along sternum/clavicle, broad belly,
# inferior curved border and convergence to the humeral insertion.
u=(x-.010)/.224;uc=np.clip(u,0,1)
zlo=(1-uc)*1.306+uc*1.366-.030*np.sin(np.pi*uc)
zhi=(1-uc)*1.458+uc*1.391+.010*np.sin(np.pi*uc)
v=(z-zlo)/(zhi-zlo);vc=np.clip(v,0,1)
pecmask=sig((u-.005)/.10)*sig((.995-u)/.12)*sig((v+.04)/.13)*sig((1.04-v)/.13)*front
pecmask*=allowed
origin_y=-.107+.056*vc
insertion_y=-.052+.008*vc
belly=np.sin(np.pi*uc)**.82*np.sin(np.pi*vc)**.62
loft=(1-uc)*origin_y+uc*insertion_y-.063*belly
# Fascicle widths and belly amplitudes are unequal; each converges and tapers,
# rather than running as constant-pitch stripes across a generic body.
boundaries=np.array([0,.105,.225,.365,.520,.675,.810,.920,1.0])
bundle=np.zeros(len(xyz));fibre=np.zeros(len(xyz))
for j,(lo,hi) in enumerate(zip(boundaries[:-1],boundaries[1:])):
    q=(vc-lo)/(hi-lo);active=(q>=0)&(q<=1)
    arch=np.maximum(0,1-(2*np.clip(q,0,1)-1)**2)**1.7
    taper=sig((uc-.02)/.20)*sig((.99-uc)/.15)
    amp=[.0017,.0023,.0029,.0032,.0030,.0027,.0021,.0013][j]
    bundle+=active*arch*taper*amp
    fibre+=active*arch*taper*.00055
loft-=bundle
xyz[:,1]=xyz[:,1]*(1-pecmask)+loft*pecmask
# A subtle inferior fold belongs to this loft, not a rectangular closed border.
inferior=sig((u-.06)/.12)*sig((.94-u)/.14)*np.exp(-((v+.02)/.065)**2)*front*allowed
xyz[:,1]+=.0018*inferior
# Right deltoid: a wrapped, tapered shoulder volume with anterior/lateral/
# posterior heads, originating around the clavicle/acromion/scapular spine.
origin=np.array([.218,.027,1.480]);axis=np.array([.345,0,-.939]);axis/=np.linalg.norm(axis)
lateral=np.array([axis[2]*-1,0,axis[0]]);anterior=np.array([0,-1,0])
local=np.column_stack([x,source[:,1],z])-origin
t=local@axis/.205;tc=np.clip(t,0,1);radx=local@lateral;rady=local@anterior
angle=np.arctan2(rady,radx);radius=np.hypot(radx,rady)
# Upper origins are broad; all three heads taper toward one upper-arm insertion.
base_radius=(.044+.031*np.sin(np.pi*tc)**.8)*(1-.55*tc**2)
head=np.zeros(len(xyz));deltoid_fibre=np.zeros(len(xyz))
for center,width,height in [(.85,.68,.0052),(0,.60,.0060),(-.95,.70,.0055)]:
    target_angle=center*(1-.45*tc)
    d=np.arctan2(np.sin(angle-target_angle),np.cos(angle-target_angle))
    head+=height*np.exp(-(d/width)**2)*np.sin(np.pi*tc)
# Fascicles travel along the three head domains toward the insertion.
origin_angle=angle/(1-.55*tc)
for center in [-1.42,-1.14,-.86,-.56,-.28,0,.27,.54,.82,1.10,1.35]:
    path=center+.055*np.sin(np.pi*tc)*(1 if center>=0 else -1)
    ridge=np.exp(-((origin_angle-path)/.055)**2)*np.sin(np.pi*tc)**1.2
    head+=.0011*ridge;deltoid_fibre+=.00040*ridge
wrap=sig((t+.06)/.20)*sig((1.03-t)/.25)*sig((radius-.018)/.025)
wrap*=sig((x-.167)/.025)*sig((.321-x)/.02)*(source[:,0]<0)*allowed
# Avoid reaching the medial chest. The deltopectoral junction blends both lofts.
wrap*=sig((2.25-np.abs(angle))/.32)
target=origin+tc[:,None]*.205*axis+(base_radius+head)[:,None]*(np.cos(angle)[:,None]*lateral+np.sin(angle)[:,None]*anterior)
target[:,0]*=np.sign(source[:,0]);xyz=xyz*(1-wrap[:,None])+target*wrap[:,None]
xyz[~allowed]=source[~allowed]
# The coordinates are fixed outside the experiment. A triangle orientation
# guard uses a single bounded step, avoiding per-vertex noise from cascades.
delta=xyz-source;tri=np.array([f.vertices[:] for f in mesh.loop_triangles]);old=source[tri]
before=np.cross(old[:,1]-old[:,0],old[:,2]-old[:,0]);area=np.linalg.norm(before,axis=1)
print('SOURCE_MIN_AREA',float(area.min()),flush=True)
assert np.min(area)>1e-12,'Degenerate source subdivision'
step=1.
for _ in range(24):
    candidate=source+step*delta;tt=candidate[tri];after=np.cross(tt[:,1]-tt[:,0],tt[:,2]-tt[:,0]);newarea=np.linalg.norm(after,axis=1)
    dots=np.sum(before*after,axis=1)/(area*newarea)
    print('BOUNDED_STEP',step,'minimum_dot',float(np.nanmin(dots)),'min_area',float(newarea.min()),flush=True)
    if np.all(np.isfinite(dots)) and np.min(dots)>.05 and np.min(newarea)>1e-12:break
    step*=.8
else:raise RuntimeError('Single bounded experiment failed orientation guard')
xyz=candidate;mesh.vertices.foreach_set('co',xyz.ravel());mesh.update()
for name,values in [('m4a_poc_pectoral_L',pecmask*(source[:,0]>0)),('m4a_poc_pectoral_R',pecmask*(source[:,0]<0)),
                    ('m4a_poc_deltoid_R',wrap),('m4a_poc_fibre_height',step*(fibre*pecmask+deltoid_fibre*wrap))]:
    attr=mesh.attributes.get(name) or mesh.attributes.new(name,'FLOAT','POINT');attr.data.foreach_set('value',values.astype(np.float32))
scores=np.column_stack([pecmask*(source[:,0]>0),pecmask*(source[:,0]<0),wrap])
face_scores=scores[tri].mean(axis=1);zone_ids=np.where(face_scores.max(axis=1)>.5,1+face_scores.argmax(axis=1),0).astype(np.int32)
region=mesh.attributes.new('m4a_poc_region_id','INT','FACE');region.data.foreach_set('value',zone_ids)
body['m4a_variant']='pectoral-poc';body['poc_scope']='both pectorals; right deltoid and their junctions only'
for o in bpy.context.scene.objects:
    if o.type=='MESH':o.data.calc_loop_triangles()
counts={'body_triangles':len(mesh.loop_triangles),'body_vertices':len(mesh.vertices),
        'visible_triangles':sum(len(o.data.loop_triangles) for o in bpy.context.scene.objects if o.type=='MESH'),'objects':3,'demo_surface_zones':3}
assert np.max(np.abs(xyz[~allowed]-source[~allowed]))==0
report={'variant':'pectoral-poc','source_path':'docs/m4a/bplus-power/power/model.blend','source_sha256':hashlib.sha256(a.source.read_bytes()).hexdigest(),
 'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'counts':counts,
 'method':'Original curved pectoral fan lofts and one wrapped three-head deltoid loft; integrated coordinates on a locally subdivided continuous body; unequal converging fascicle profiles plus scalar normal detail.',
 'local_subdivision_passes':1,'bounded_step':step,'minimum_triangle_normal_dot':float(dots.min()),
 'max_displacement_m':float(np.linalg.norm(xyz-source,axis=1).max()),'outside_scope_unchanged':True,
 'vertices_outside_scope':int((~allowed).sum()),'changed_vertices':int((np.linalg.norm(xyz-source,axis=1)>1e-8).sum()),
 'source_geometry_license':'CC0','third_party_anatomy_loaded':False,'full_segmentation':False,
 'zone_triangles':{name:int((zone_ids==i).sum()) for i,name in [(1,'pectoralis.left'),(2,'pectoralis.right'),(3,'deltoid.right')]},
 'selectable_zones':{'pectoralis.left':'m4a_poc_pectoral_L','pectoralis.right':'m4a_poc_pectoral_R','deltoid.right':'m4a_poc_deltoid_R'},
 'limitations':['Single experimental anatomy construction, not medically validated.','Inherited head/foot contacts remain; separate geometry and visual reviews required.','Surface masks are demonstration regions, not final anatomical partitions.']}
(a.output/'construction.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(a.output/'model.blend'),compress=True)
print('POC_BUILD',json.dumps(report),flush=True)
