"""Continuous B+ fitness relief. No atlas, assembled muscles or L/S geometry.

Evaluates the validated B+ Multires once, sculpts a bounded continuous normal
field, then makes a research proxy. Preserves the original B+ file unchanged.
"""
import argparse,hashlib,json,math,sys
from pathlib import Path
import bpy,bmesh,numpy as np

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--source',type=Path,required=True)
p.add_argument('--reference',type=Path,required=True)
p.add_argument('--variant',choices=['baseline','soft','premium'],required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--triangles',type=int,default=110000)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.output.mkdir(parents=True,exist_ok=True)
reference=json.loads(a.reference.read_text());center=np.array(reference['transform']['center']);scale=reference['transform']['uniform_scale']
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
names=['GEO-body_male_realistic','GEO-body_male_realistic.eye.L','GEO-body_male_realistic.eye.R']
with bpy.data.libraries.load(str(a.source.resolve()),link=False) as (src,dst):dst.objects=names
for ob in dst.objects:bpy.context.scene.collection.objects.link(ob)
bpy.context.view_layer.update();graph=bpy.context.evaluated_depsgraph_get()
objects=[]
for index,original in enumerate(list(dst.objects)):
    mesh=bpy.data.meshes.new_from_object(original.evaluated_get(graph),preserve_all_data_layers=True,depsgraph=graph)
    matrix=np.array(original.matrix_world,dtype=float)
    xyz=np.empty(len(mesh.vertices)*3,dtype=np.float64);mesh.vertices.foreach_get('co',xyz);xyz=xyz.reshape(-1,3)
    xyz=(xyz@matrix[:3,:3].T+matrix[:3,3]-center)*scale
    mesh.vertices.foreach_set('co',xyz.ravel());mesh.update()
    ob=bpy.data.objects.new(original.name+'.fitness',mesh);bpy.context.scene.collection.objects.link(ob)
    ob['m4a_render']=True;ob['m4a_role']='body' if index==0 else 'eye'
    ob['m4a_variant']=a.variant;objects.append(ob)
for original in dst.objects:bpy.data.objects.remove(original,do_unlink=True)
body=next(o for o in objects if o['m4a_role']=='body');mesh=body.data;mesh.calc_loop_triangles()
xyz=np.empty(len(mesh.vertices)*3,dtype=np.float64);mesh.vertices.foreach_get('co',xyz);xyz=xyz.reshape(-1,3)
norm=np.empty_like(xyz);mesh.vertices.foreach_get('normal',norm.ravel())
x=np.abs(xyz[:,0]);y=xyz[:,1];z=xyz[:,2]


def sig(v):
    v=np.clip(v,0,1);return v*v*(3-2*v)


def gauss(v,c,w):return np.exp(-((v-c)/w)**2)


def ellipse(cx,cz,rx,rz,tilt=0):
    angle=math.radians(tilt);dx=x-cx;dz=z-cz
    u=dx*math.cos(angle)+dz*math.sin(angle);v=-dx*math.sin(angle)+dz*math.cos(angle)
    r=np.sqrt((u/rx)**2+(v/rz)**2)
    return (1-r)*min(rx,rz)


def polygon(points):
    distance=np.full(len(x),np.inf);inside=np.zeros(len(x),dtype=bool)
    for i,(ax,az) in enumerate(points):
        bx,bz=points[(i+1)%len(points)];dx=bx-ax;dz=bz-az
        t=np.clip(((x-ax)*dx+(z-az)*dz)/(dx*dx+dz*dz),0,1)
        distance=np.minimum(distance,np.sqrt((x-ax-t*dx)**2+(z-az-t*dz)**2))
        cross=((az>z)!=(bz>z)) & (x<(bx-ax)*(z-az)/(bz-az+1e-15)+ax)
        inside ^= cross
    return np.where(inside,distance,-distance)


def rounded_box(cx,cz,hx,hz,radius):
    qx=np.abs(x-cx)-hx+radius;qz=np.abs(z-cz)-hz+radius
    return -(np.sqrt(np.maximum(qx,0)**2+np.maximum(qz,0)**2)+np.minimum(np.maximum(qx,qz),0)-radius)


def pectoral_sdf():
    fan=polygon([(.012,1.438),(.075,1.450),(.165,1.435),(.192,1.405),
                 (.178,1.355),(.120,1.302),(.038,1.304),(.010,1.325)])
    return .35*ellipse(.100,1.366,.090,.071,-8)+.65*fan


# Smooth anterior/posterior gates prevent sculpting a projection on the far side.
front=sig((-norm[:,1]-.12)/.65)*sig((.045-y)/.04)
back=sig((norm[:,1]-.12)/.65)*sig((y-.035)/.05)
field=np.zeros(len(x));regions=[]
strength={'baseline':0.,'soft':.65,'premium':1.25}[a.variant]
fibre_strength={'baseline':0.,'soft':.00022,'premium':.00055}[a.variant]


def relief(name,sdf,gate,height,groove,fibres=None):
    inside=sig((sdf+.003)/.013)
    # Broad bellies with softly recessed borders, no separate skin or sharp cuts.
    value=height*inside-groove*np.exp(-(sdf/.0045)**2)
    if fibres is not None:
        value+=fibre_strength*fibres*sig(sdf/.012)
    value*=gate
    field[:]+=strength*value
    regions.append({'name':name,'height_m_before_strength':height,'border_depth_m_before_strength':float(np.max(groove))})


pec=pectoral_sdf()
pec=np.minimum(pec,(x-.010)*.7)
pec=np.minimum(pec,(1.457-.10*x-z)*.8)
# Broad curved fibre fans run toward the axillary insertion, rather than stripes
# across the entire body. Their displacement is sub-millimetric and tapers off.
pec_angle=np.arctan2(z-1.405,x-.193)
fibres=-.5*(1+np.cos(pec_angle*21))
relief('pectoralis fan',pec,front,.0034,.0018*(.35+.65*sig((1.40-z)/.04)),fibres)
# Rectus plates stay broad and flat; source scan relief remains beneath them.
for level in [1.105,1.167,1.228]:
    sdf=rounded_box(.034,level,.026,.024,.010)
    relief('rectus abdominis '+str(level),sdf,front,.0022,.0015)
oblique=ellipse(.105,1.165,.032,.100,15)
relief('external oblique',oblique,front,.0020,.0017,-.5*(1+np.cos((z+.34*x)*310)))
# Existing B+ lower pectoral contour is reinforced without inflating its edge.
field-=strength*.0016*front*gauss(z,1.293+.16*x,.006)*gauss(x,.10,.085)
# A few wide serratus slips, not exposed ribs or dense fibre engraving.
serratus_gate=front*gauss(x,.145,.032)*gauss(z,1.255,.055)
field+=strength*.0012*serratus_gate*np.sin((z+.33*x)*235)

# Native B+ upper-arm axis in the A-pose (from its validated volume settings).
axis=.249+.39*(1.31-z)
arm_dx=x-axis;arm_angle=np.arctan2(.028-y,arm_dx)
arm_gate=sig((x-.192)/.035)*gauss(z,1.285,.135)
radial=np.sqrt((arm_dx/.061)**2+((y-.028)/.065)**2)
arm_gate*=sig((1.65-radial)/.45)
# Local angular bellies make front/back differences without attaching new parts.
for name,theta,height in [('biceps',math.pi/2,.0040),('triceps',-math.pi/2,.0042)]:
    angular=np.arctan2(np.sin(arm_angle-theta),np.cos(arm_angle-theta))
    mask=np.exp(-(angular/.64)**2)*gauss(z,1.273,.086)*arm_gate
    field+=strength*height*mask
    field-=strength*.0015*arm_gate*gauss(np.abs(angular),.80,.13)*gauss(z,1.27,.09)
    field+=fibre_strength*.7*mask*(-.5-.5*np.cos(arm_dx*330))
    regions.append({'name':name,'height_m_before_strength':height,'border_depth_m_before_strength':.0015})
delt=ellipse(.226,1.424,.060,.076,-18)
relief('deltoid',delt,sig((x-.163)/.04)*gauss(y,.025,.12),.0022,.0017*gauss(z,1.39,.070),
       -.5-.5*np.cos(arm_angle*9+z*13))
# Forearms: shallow longitudinal direction only; wrists and hands are protected.
fore_axis=.335+.42*(1.10-z)
fore=gauss(x-fore_axis,0,.039)*gauss(z,1.058,.073)*sig((x-.29)/.035)
field+=strength*.0010*fore*(-.5-.5*np.cos((x-fore_axis)*375))*sig((z-.985)/.045)

lat=polygon([(.043,1.12),(.090,1.12),(.162,1.26),(.196,1.35),(.170,1.395),(.106,1.335),(.070,1.245)])
lat_angle=np.arctan2(z-1.39,x-.185)
relief('latissimus dorsi',lat,back,.0034,0.,-.5-.5*np.cos(lat_angle*19))
trap=polygon([(.010,1.51),(.078,1.50),(.165,1.44),(.100,1.36),(.020,1.27),(.010,1.38)])
relief('trapezius',trap,back,.0024,0.,-.5-.5*np.cos((z-.5*x)*250))
field-=strength*.0013*back*gauss(x,0,.008)*gauss(z,1.34,.18)
field-=strength*.0015*back*gauss(x,.025+.75*(z-1.29),.010)*gauss(z,1.40,.085)
field-=strength*.0012*back*gauss(x,.045+.20*(z-1.15),.008)*gauss(z,1.26,.10)

# Quadriceps follow three broad, tapering heads; fibre direction is subordinate
# to their volumes and gently rounded separators.
leg_axis=.129+.01*(.73-z)
for name,offset,level,rx,rz,tilt,amp in [
 ('quadriceps rectus',0,.744,.033,.137,-2,.0034),
 ('quadriceps vastus lateralis',.043,.724,.036,.142,-9,.0026),
 ('quadriceps vastus medialis',-.036,.620,.028,.070,14,.0031)]:
    sdf=ellipse(.129+offset,level,rx,rz,tilt)
    relief(name,sdf,front*sig((.22-x)/.035),amp,.0007,
           -.5-.5*np.cos((x-leg_axis+.055*(z-.7))*360))
for center_x,curve in [(.162,.022),(.111,-.010)]:
    path=center_x+curve*np.sin(np.clip((z-.53)/.38,0,1)*math.pi)
    field-=strength*.0025*front*gauss(x,path,.0055)*gauss(z,.72,.14)
for name,cx,tilt in [('hamstrings lateral',.165,6),('hamstrings medial',.110,-4)]:
    sdf=ellipse(cx,.740,.030,.143,tilt)
    relief(name,sdf,back,.0030,.0017,-.5-.5*np.cos((x-cx+.03*(z-.7))*350))
for cx,level in [(.117,.338),(.163,.352)]:
    sdf=ellipse(cx,level,.029,.097,0)
    relief('gastrocnemius '+str(cx),sdf,back,.0025,.0017,-.5-.5*np.cos((x-cx)*350))

# Head, hands, knees and ankles keep the scan's quality. Fields never reach a
# joint as a hard horizontal ring. Silhouette-facing displacement is bounded.
protect=sig((z-.165)/.045)*sig((1.548-z)/.040)
protect*=1-sig((x-.395)/.035)*(1-sig((z-1.02)/.04))
protect*=1-.70*gauss(z,.497,.036)
field*=protect
max_displacement={'baseline':0.,'soft':.0045,'premium':.0080}[a.variant]
field=np.clip(field,-max_displacement,max_displacement)
side_limit=.0012+.0018*(1-np.abs(norm[:,0]))
side_blend=sig((np.abs(norm[:,0])-.60)/.25)
field=field*(1-side_blend)+np.clip(field,-side_limit,side_limit)*side_blend
original_xyz=xyz.copy();candidate=xyz+norm*field[:,None]
indices=np.empty(len(mesh.loop_triangles)*3,dtype=np.int32);mesh.loop_triangles.foreach_get('vertices',indices);indices=indices.reshape(-1,3)
tri=xyz[indices];before=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);before_len=np.linalg.norm(before,axis=1)
assert np.all(before_len>1e-12)
safe_scale=np.ones(len(xyz));delta=candidate-xyz
edges=np.empty(len(mesh.edges)*2,dtype=np.int32);mesh.edges.foreach_get('vertices',edges);edges=edges.reshape(-1,2)
for iteration in range(40):
    result=xyz+delta*safe_scale[:,None];t=result[indices]
    after=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);after_len=np.linalg.norm(after,axis=1)
    dots=np.sum(before*after,axis=1)/(before_len*after_len)
    bad=(dots<.85)|(~np.isfinite(dots))|(after_len<=1e-12)
    if not np.any(bad):break
    affected=np.unique(indices[bad]);damping=np.ones(len(xyz));damping[affected]=.65
    for spread in range(5):
        next_damping=damping.copy()
        np.minimum.at(next_damping,edges[:,0],damping[edges[:,1]]+.07)
        np.minimum.at(next_damping,edges[:,1],damping[edges[:,0]]+.07)
        damping=next_damping
    safe_scale*=damping
else:raise RuntimeError('Local orientation guard did not converge')
assert np.all(dots>=.85) and np.all(after_len>1e-12)
mesh.vertices.foreach_set('co',result.ravel());mesh.update()
# A production bake/export is deliberately not performed. This is a closed
# static research proxy for comparison, with source B+ and code as authoring data.
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
m=body.modifiers.new('Research proxy budget','DECIMATE');m.ratio=a.triangles/len(mesh.loop_triangles);m.use_collapse_triangulate=True
bpy.ops.object.modifier_apply(modifier=m.name)
mesh=body.data;bm=bmesh.new();bm.from_mesh(mesh)
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-8)
bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-9)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free();mesh.update()
# Two demo zones only: continuous interpolated signed-distance mask, sampled
# again on the proxy. A shader threshold produces a crisp boundary within faces,
# without splitting the body or painting an orange image.
proxy=np.empty(len(mesh.vertices)*3,dtype=np.float64);mesh.vertices.foreach_get('co',proxy);proxy=proxy.reshape(-1,3)
x=np.abs(proxy[:,0]);y=proxy[:,1];z=proxy[:,2]
sdf=pectoral_sdf()
sdf=np.minimum(sdf,(x-.010)*.7);sdf=np.minimum(sdf,(1.457-.10*x-z)*.8)
mask=.5+sdf/.06
mask=np.minimum(mask,.5+(-.015-y)/.06)
attribute=mesh.attributes.new('m4a_pectoral_mask','FLOAT','POINT');attribute.data.foreach_set('value',mask.astype(np.float32))
for side,sign in [('L',1),('R',-1)]:
    attr=mesh.attributes.new('m4a_pectoral_'+side,'FLOAT','POINT')
    values=np.where(proxy[:,0]*sign>=0,mask,-1).astype(np.float32)
    attr.data.foreach_set('value',values)
for ob in objects:
    ob.data.materials.clear()
    for face in ob.data.polygons:face.use_smooth=True
    ob.data.calc_loop_triangles()
body['m4a_demo_zones']='pectoralis.left, pectoralis.right; provisional surface mask'
body.name='BPF.body';objects[1].name='BPF.eye.L';objects[2].name='BPF.eye.R'
counts={'objects':len(objects),'body_triangles':len(mesh.loop_triangles),'body_vertices':len(mesh.vertices),
        'visible_triangles':sum(len(o.data.loop_triangles) for o in objects),'demo_surface_zones':2,
        'separate_muscle_objects':0}
report={'variant':a.variant,'source_blend_sha256':hashlib.sha256(a.source.read_bytes()).hexdigest(),
 'source_path':str(a.source),'source_name':'B+ moderate athletic v1; Dan Ulrich / Blender Studio Human Base Meshes v1.4.1, CC0',
 'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'normalization':reference['transform'],
 'L_and_S_geometry_read':False,'separate_muscles_added':False,'counts':counts,
 'relief':{'strength':strength,'fibre_amplitude_m':fibre_strength,'requested_max_displacement_m':max_displacement,
  'orientation_guard':'local damping with five-ring feather, preserving healthy regions', 'orientation_guard_iterations':iteration, 'orientation_guard_min_scale':float(safe_scale.min()), 'orientation_guard_mean_scale':float(safe_scale.mean()),'minimum_highres_normal_dot':float(dots.min()),
  'max_highres_displacement_m':float(np.linalg.norm(result-original_xyz,axis=1).max()),
  'mean_highres_displacement_m':float(np.linalg.norm(result-original_xyz,axis=1).mean()),'regions':regions},
 'highres_triangles_before_proxy':len(indices),'source_geometry_normalized_sha256':hashlib.sha256(original_xyz.astype('<f4').tobytes()).hexdigest(),
 'demo_selection':'Two procedural pectoral surface masks on the single continuous body; no final segmentation.',
 'limitations':['Proxy decimation changes topology and approximates fine scan/fibre detail.',
 'No exhaustive intersection/medical/rig/mobile-engine validation, bake or application export.',
 'Authoring source is the preserved B+ BLEND and this generator; output is a static research scene.']}
(a.output/'construction.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
bpy.data.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=str(a.output/'model.blend'),compress=True)
print('BPLUS_FITNESS',json.dumps(counts),'max displacement',report['relief']['max_highres_displacement_m'],flush=True)
