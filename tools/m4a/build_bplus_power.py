"""One stronger B+ Premium iteration, directly on its validated continuous proxy.

Topology, eyes and demonstration surface masks are preserved. No remeshing,
third-party anatomy, final segmentation or application export.
"""
import argparse,hashlib,json,math,sys
from pathlib import Path
import bpy,numpy as np
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.source=a.source.resolve();a.output.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(a.source),use_scripts=False)
objects=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.get('m4a_render')];assert len(objects)==3
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



def old_relief():
    # Smooth anterior/posterior gates prevent sculpting a projection on the far side.
    front=sig((-norm[:,1]-.12)/.65)*sig((.045-y)/.04)
    back=sig((norm[:,1]-.12)/.65)*sig((y-.035)/.05)
    field=np.zeros(len(x));regions=[]
    strength=1.25
    fibre_strength=.00055


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

    return field,regions

def stronger_relief():
    # Smooth anterior/posterior gates prevent sculpting a projection on the far side.
    front=sig((-norm[:,1]-.12)/.65)*sig((.045-y)/.04)
    back=sig((norm[:,1]-.12)/.65)*sig((y-.035)/.05)
    field=np.zeros(len(x));regions=[]
    strength=1.85
    fibre_strength=.00145


    def relief(name,sdf,gate,height,groove,fibres=None):
        width=.030 if name=='pectoralis fan' else .045 if name in ['latissimus dorsi','trapezius'] else .018
        inside=sig((sdf+.004)/width)
        # Broad bellies with softly recessed borders, no separate skin or sharp cuts.
        value=height*inside-groove*np.exp(-(sdf/.006)**2)
        if name=='pectoralis fan':
            value=height*inside*(.30+.70*gauss(x,.098,.073)*gauss(z,1.372,.060))-groove*np.exp(-(sdf/.006)**2)
        elif name=='latissimus dorsi':
            value=height*gauss(x,.125,.075)*gauss(z,1.295,.145)
        elif name=='trapezius':
            value=height*gauss(x,.065,.085)*gauss(z,1.438,.105)
        if fibres is not None:
            value+=fibre_strength*fibres*sig(sdf/.026)
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
    relief('pectoralis fan',pec,front,.0043,.0012*(.35+.65*sig((1.40-z)/.04)),fibres)
    # Rectus plates stay broad and flat; source scan relief remains beneath them.
    for level,rx,rz in [(1.105,.027,.024),(1.167,.029,.025),(1.228,.031,.027)]:
        sdf=ellipse(.035,level,rx,rz,-6)
        relief('rectus abdominis '+str(level),sdf,front,.0032,.0015)
    oblique=ellipse(.105,1.165,.032,.100,15)
    relief('external oblique',oblique,front,.0031,.0017,-.5*(1+np.cos((z+.34*x)*310)))
    # Existing B+ lower pectoral contour is reinforced without inflating its edge.
    field-=strength*.0016*front*gauss(z,1.293+.16*x,.006)*gauss(x,.10,.085)
    # A few wide serratus slips, not exposed ribs or dense fibre engraving.
    serratus_gate=front*gauss(x,.145,.032)*gauss(z,1.255,.055)
    field+=strength*.0018*serratus_gate*np.sin((z+.33*x)*235)

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
     ('quadriceps rectus',0,.744,.033,.137,-2,.0042),
     ('quadriceps vastus lateralis',.043,.724,.036,.142,-9,.0033),
     ('quadriceps vastus medialis',-.036,.620,.028,.070,14,.0038)]:
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

    return field,regions

protect=sig((z-.165)/.045)*sig((1.548-z)/.040)
protect*=1-sig((x-.395)/.035)*(1-sig((z-1.02)/.04))
protect*=1-.70*gauss(z,.497,.036)
old_field,_=old_relief();new_field,regions=stronger_relief()
# Approximate relative correction of the existing envelope, not a second full
# layer of muscles. Macro volume is separate from superficial relief.
field=np.clip(new_field-old_field,-.008,.008)*protect
front=sig((-norm[:,1]-.12)/.65)*sig((.045-y)/.04)
back=sig((norm[:,1]-.12)/.65)*sig((y-.035)/.05)
axis=.249+.39*(1.31-z);arm_dx=x-axis
radial=np.sqrt((arm_dx/.061)**2+((y-.028)/.065)**2)
fore_axis=.335+.42*(1.10-z)
volume=np.zeros_like(xyz);sign=np.sign(xyz[:,0]);volume_regions=[]
volume_front=sig((.030-y)/.100);volume_back=sig((y-.010)/.100)
def add_volume(name,weight,delta):
    volume[:]+=weight[:,None]*delta
    volume_regions.append(name)
def vector(dx=0,dy=0,dz=0):
    return np.column_stack([np.broadcast_to(dx,len(x)),np.broadcast_to(dy,len(x)),np.broadcast_to(dz,len(x))])
pec_bulk=volume_front*gauss(x,.103,.092)*gauss(z,1.371,.087)
add_volume('fuller pectorals',pec_bulk,vector(sign*.003,-.019,.0015))
delt_bulk=gauss(x,.230,.075)*gauss(z,1.426,.090)*gauss(y,.028,.140)
add_volume('rounder deltoids',delt_bulk,vector(sign*.012,(y-.028)*.19,.003))
upper=gauss(z,1.278,.112)*sig((x-.192)/.035)*sig((1.65-radial)/.45)
add_volume('upper arm radial +20 percent field',upper,vector(sign*arm_dx*.20,(y-.028)*.20,0))
fore_bulk=gauss(x-fore_axis,0,.060)*gauss(z,1.076,.083)*sig((x-.290)/.035)
add_volume('forearm radial +20 percent field',fore_bulk,vector(sign*(x-fore_axis)*.20,(y-.028)*.20,0))
lat_bulk=volume_back*gauss(x,.143,.083)*gauss(z,1.305,.148)
add_volume('latissimus breadth and depth',lat_bulk,vector(sign*.013,.014,0))
trap_bulk=volume_back*gauss(x,.072,.100)*gauss(z,1.455,.095)
add_volume('upper back trapezius depth',trap_bulk,vector(sign*.002,.012,.001))
quad_bulk=volume_front*gauss(x,.135,.075)*gauss(z,.737,.174)
add_volume('quadriceps fuller bellies',quad_bulk,vector(sign*.004,-.014,0))
ham_bulk=volume_back*gauss(x,.134,.071)*gauss(z,.741,.168)
add_volume('hamstrings stronger back silhouette',ham_bulk,vector(sign*.004,.013,0))
calf_bulk=gauss(x,.139,.054)*gauss(z,.350,.109)
add_volume('calf radial fullness',calf_bulk,vector(sign*(x-.139)*.16,(y-.040)*.15,0))
# Keep waist width stable while lifting its superficial muscle relief.
volume*=protect[:,None]

delta=volume+norm*field[:,None]
edges=np.empty(len(mesh.edges)*2,dtype=np.int32);mesh.edges.foreach_get('vertices',edges);edges=edges.reshape(-1,2)
# Feather displacement over the existing surface, preserving a continuous body.
# The source mesh itself is not smoothed; head, hands, feet stay protected.
degree=np.bincount(edges.ravel(),minlength=len(xyz))
for smoothing in range(8):
    total=np.zeros_like(delta);np.add.at(total,edges[:,0],delta[edges[:,1]]);np.add.at(total,edges[:,1],delta[edges[:,0]])
    delta=.65*delta+.35*total/degree[:,None]
delta*=protect[:,None]
indices=np.empty(len(mesh.loop_triangles)*3,dtype=np.int32);mesh.loop_triangles.foreach_get('vertices',indices);indices=indices.reshape(-1,3)
t=xyz[indices];before=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);before_len=np.linalg.norm(before,axis=1)
safe_scale=np.ones(len(xyz))
for iteration in range(80):
    result=xyz+delta*safe_scale[:,None];t=result[indices]
    after=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);after_len=np.linalg.norm(after,axis=1)
    dots=np.sum(before*after,axis=1)/(before_len*after_len)
    bad=(dots<.85)|(~np.isfinite(dots))|(after_len<=1e-12)
    if iteration%10==0:print('GUARD',iteration,'bad',int(bad.sum()),flush=True)
    if not np.any(bad):break
    damping=np.ones(len(xyz));damping[np.unique(indices[bad])]=.65
    for spread in range(8):
        next_damping=damping.copy()
        np.minimum.at(next_damping,edges[:,0],damping[edges[:,1]]+.045)
        np.minimum.at(next_damping,edges[:,1],damping[edges[:,0]]+.045)
        damping=next_damping
    safe_scale*=damping
else:raise RuntimeError('Orientation guard did not converge')
mesh.vertices.foreach_set('co',result.ravel());mesh.update()
for ob in objects:ob['m4a_variant']='power'
counts={'objects':3,'body_triangles':len(mesh.loop_triangles),'body_vertices':len(mesh.vertices),
        'visible_triangles':sum(len(o.data.loop_triangles) for o in objects),'demo_surface_zones':2,'separate_muscle_objects':0}
assert counts['visible_triangles']==112176
parent=json.loads((a.source.parent/'construction.json').read_text())
report={'variant':'power','source_path':'docs/m4a/bplus-fitness/premium/model.blend',
 'source_blend_sha256':hashlib.sha256(a.source.read_bytes()).hexdigest(),
 'source_name':'B+ Ecorche Premium selected visual direction; original base geometry Dan Ulrich / Blender Studio CC0',
 'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 'source_geometry_sha256':hashlib.sha256(xyz.astype('<f4').tobytes()).hexdigest(),
 'original_B_plus_sha256':parent['source_blend_sha256'],'normalization':parent['normalization'],
 'topology_changed':False,'remesh_or_decimation':False,'surface_masks_preserved':True,
 'L_and_S_geometry_read':False,'separate_muscles_added':False,'counts':counts,'volume_fields':volume_regions,
 'volume':{'maximum_requested_m':float(np.linalg.norm(volume,axis=1).max()),'displacement_smoothing_iterations':8},
 'relief':{'target_strength':1.85,'parent_strength':1.25,'target_fibre_amplitude_m':.00145,'parent_fibre_amplitude_m':.00055,
 'relative_field_limit_m':.008,'orientation_guard_iterations':iteration,
 'orientation_guard_min_scale':float(safe_scale.min()),'orientation_guard_mean_scale':float(safe_scale.mean()),
 'minimum_normal_dot':float(dots.min()),'max_displacement_from_parent_m':float(np.linalg.norm(result-xyz,axis=1).max()),
 'mean_displacement_from_parent_m':float(np.linalg.norm(result-xyz,axis=1).mean()),'regions':regions},
 'limitations':['Source proxy topology retained; no new high-resolution bake or production retopology.',
 'Head/foot source self-crossings are preserved; see geometry audit.',
 'Two demonstration surface masks only; no full segmentation, medical or mobile-runtime validation.']}
(a.output/'construction.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(a.output/'model.blend'),compress=True)
print('BPLUS_POWER',json.dumps(counts),report['relief'],flush=True)
