"""S1/S2/S3: build from genuine superficial muscle volumes, never from L1/L2/L3.

Input is the audited muscles-only Ecorche checkpoint (CC BY-SA 4.0). New neutral
covers hide skull, bones, fingers' tendons and joint gaps. Output derivatives and
renders retain CC BY-SA 4.0; application code is not relicensed.
"""
import argparse, hashlib, json, math, sys
from collections import defaultdict
from pathlib import Path
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix, kdtree

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--source', type=Path, required=True)
p.add_argument('--variant', choices=['s1','s2','s3'], required=True)
p.add_argument('--output', type=Path, required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.output.mkdir(parents=True,exist_ok=True)
settings={
 's1':dict(width=1.12,bulk=.14,waist=.08,method='continuous anatomical union',voxel=.003,smooth=9,budget=74000),
 's2':dict(width=1.18,bulk=.24,waist=.13,method='grouped rounded muscle masses over recessed support',voxel=.0026,smooth=5,budget=100000),
 's3':dict(width=1.15,bulk=.19,waist=.10,method='separate simplified superficial anatomical pieces',voxel=.0025,smooth=3,budget=108000)}
cfg=settings[a.variant]
bpy.ops.wm.open_mainfile(filepath=str(a.source.resolve()),use_scripts=False)
source_rows=[];kept=[];rejected=[]
arm_groups={'deltoid','biceps','triceps','brachialis','forearm-flexors','forearm-extensors'}


def family(name):
    n=name.lower()
    for needle,group in [('pectoralis major','pectoralis'),('deltoid','deltoid'),('biceps brachii','biceps'),
                         ('triceps brachii','triceps'),('brachialis','brachialis'),('latissimus','latissimus'),
                         ('trapezius','trapezius'),('rectus abdominis','rectus-abdominis'),
                         ('external oblique','oblique'),('serratus anterior','serratus'),
                         ('infraspinatus','scapular'),('teres major','scapular'),('teres minor','scapular'),
                         ('rectus femoris','quadriceps-rectus'),('vastus lateralis','quadriceps-lateral'),
                         ('vastus medialis','quadriceps-medial'),('biceps femoris','hamstrings-lateral'),
                         ('semitendinosus','hamstrings-medial'),('semimembranosus','hamstrings-medial'),
                         ('adductor longus','adductors'),('adductor magnus','adductors'),('gracilis','adductors'),
                         ('sartorius','sartorius'),('tensor fasciae','hip-abductors'),
                         ('gluteus medius','gluteal'),('gluteus maximus','gluteal'),
                         ('gastrocnemius','calf'),('soleus','soleus'),('tibialis anterior','tibialis'),
                         ('fibularis longus','fibularis'),('sternocleidomastoid','neck')]:
        if needle in n:return group
    if any(s in n for s in ['brachioradialis','extensor carpi radialis','extensor carpi ulnaris','extensor digitorum']):
        return 'forearm-extensors' if 'longus' not in n or 'digitorum' not in n else None
    if any(s in n for s in ['flexor carpi','pronator teres','flexor digitorum superficialis']):return 'forearm-flexors'
    return None


def gaussian(v,c,w):return math.exp(-((v-c)/w)**2)


def transform(point,side,group='support'):
    x,y,z=point;ax=abs(x)
    body=group not in arm_groups and group!='hand'
    width=cfg['width']*(1-cfg['waist']*gaussian(z,1.13,.13)) if body and z>.88 else cfg['width']
    x=x*width
    if z<1.0 and group not in arm_groups and group not in {'hand','support'}:x+=math.copysign(.012*gaussian(z,.45,.55),x)
    y=.025+(y-.025)*1.09
    if group in arm_groups or group=='hand':
        pivot=Vector((.195*cfg['width'],.03,1.47))
        v=Vector((x,y,z))-pivot
        v=Matrix.Rotation(math.radians(-11),3,'Y')@v
        x,y,z=v+pivot
    return Vector((x*side,y,z))


def activate(ob):
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob


def clean(ob):
    bm=bmesh.new();bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
    bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-8)
    # Tiny detached splinters and source triangles do not become product details.
    todo=set(bm.verts);discard=[]
    while todo:
        pending=[todo.pop()];component=[]
        while pending:
            v=pending.pop();component.append(v)
            for e in v.link_edges:
                other=e.other_vert(v)
                if other in todo:todo.remove(other);pending.append(other)
        if len(component)<10:discard.extend(component)
    if discard:bmesh.ops.delete(bm,geom=discard,context='VERTS')
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free();ob.data.update()


def soften(ob,iterations,factor=.55):
    activate(ob);m=ob.modifiers.new('Remove medical fibre noise','SMOOTH');m.factor=factor;m.iterations=iterations
    bpy.ops.object.modifier_apply(modifier=m.name)


def decimate(ob,target):
    ob.data.calc_loop_triangles();n=len(ob.data.loop_triangles)
    if n>target:
        activate(ob);m=ob.modifiers.new('Prototype triangle budget','DECIMATE');m.ratio=target/n;m.use_collapse_triangulate=True
        bpy.ops.object.modifier_apply(modifier=m.name)
    clean(ob)


def join(obs,name):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in obs:ob.select_set(True)
    bpy.context.view_layer.objects.active=obs[0];bpy.ops.object.join();ob=bpy.context.object;ob.name=name;return ob


def union(ob,voxel,iterations):
    activate(ob);m=ob.modifiers.new('Muscle volume union','REMESH');m.mode='VOXEL';m.voxel_size=voxel;m.use_smooth_shade=True
    bpy.ops.object.modifier_apply(modifier=m.name);soften(ob,iterations,.55);clean(ob)


def solidify_if_open(ob):
    bm=bmesh.new();bm.from_mesh(ob.data);open_edges=sum(not e.is_manifold for e in bm.edges);bm.free()
    if open_edges:
        activate(ob);m=ob.modifiers.new('Close thin anatomical sheet','SOLIDIFY');m.thickness=.0028;m.offset=0
        bpy.ops.object.modifier_apply(modifier=m.name)
    return open_edges


# Select real superficial left-side meshes; reflect this explicit side. Do not
# infer the entire atlas from proximity, import skeleton or include facial organs.
for ob in list(bpy.context.scene.objects):
    if ob.type!='MESH':bpy.data.objects.remove(ob,do_unlink=True);continue
    name=ob.get('audit_identity',ob.name);group=family(name)
    if ob.get('layer')!='superficial muscles' or ob.get('audit_side')!='left' or not group or (a.variant=='s2' and group=='neck'):
        rejected.append(name);bpy.data.objects.remove(ob,do_unlink=True);continue
    ob.data=ob.data.copy();ob.data.materials.clear()
    clean(ob)
    if group=='oblique':
        # Remove the source's central aponeurotic sheath, which covers the abs.
        bm=bmesh.new();bm.from_mesh(ob.data)
        bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-6,
                              plane_co=(.067,0,0),plane_no=(1,0,0),clear_inner=True)
        bm.to_mesh(ob.data);bm.free();clean(ob)
    cut_z = 1.01 if group in {'oblique','rectus-abdominis'} else .936 if group in {'forearm-flexors','forearm-extensors'} else .14 if group in {'tibialis','fibularis'} else None
    if cut_z:
        bm=bmesh.new();bm.from_mesh(ob.data)
        bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-6,
                              plane_co=(0,0,cut_z),plane_no=(0,0,1),clear_inner=True)
        bm.to_mesh(ob.data);bm.free();clean(ob)
    center=sum((v.co for v in ob.data.vertices),Vector())/len(ob.data.vertices)
    lo=min(v.co.z for v in ob.data.vertices);hi=max(v.co.z for v in ob.data.vertices)
    for v in ob.data.vertices:
        point=v.co.copy();t=(point.z-lo)/max(hi-lo,.001);belly=math.sin(math.pi*t)**2
        gain=cfg['bulk']*belly
        point.x=center.x+(point.x-center.x)*(1+gain)
        point.y=center.y+(point.y-center.y)*(1+gain)
        if group=='rectus-abdominis':
            front= max(0,min(1,(-point.y-.04)/.05))
            point.y-=front*sum(.007*gaussian(point.z,z,.027) for z in [1.08,1.16,1.24])
        if group=='pectoralis':point.y-=.005*belly
        if group in {'oblique','rectus-abdominis'}:
            taper=max(0,min(1,(1.10-point.z)/.09))
            point.y+=.040*taper*taper*max(0,min(1,(.02-point.y)/.07))
        v.co=transform(point,1,group)
    ob['zone']=group+'.left';ob['source_names']=json.dumps([name]);ob['role']='muscle';ob['selectable']=True
    open_edges=solidify_if_open(ob)
    # Subdivision here interpolates sparse source bellies; final decimation follows.
    if len(ob.data.polygons)<3500:
        activate(ob);m=ob.modifiers.new('Round sparse anatomical contours','SUBSURF');m.levels=1
        bpy.ops.object.modifier_apply(modifier=m.name)
    soften(ob,3 if a.variant=='s3' else 5,.50)
    clean(ob)
    print('STRUCTURE',name,flush=True)
    if group=='rectus-abdominis':
        plates=[]
        for level in [1.085,1.165,1.245]:
            bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=32)
            plate=bpy.context.object
            for v in plate.data.vertices:
                point=Vector((.035+v.co.x*.031,-.119+v.co.y*.013,level+v.co.z*.033))
                v.co=transform(point,1,'rectus-abdominis')
            plates.append(plate)
        ob=join([ob]+plates,'Authored rounded rectus plates over source');union(ob,.0025,2)
        ob['zone']=group+'.left';ob['source_names']=json.dumps([name]);ob['role']='muscle';ob['selectable']=True
    if a.variant=='s3' and group in {'serratus','oblique'}:
        union(ob,.0026,3)
    source_rows.append({'name':name,'family':group,'original_open_edges':open_edges})
    kept.append(ob)

# Organise actual anatomy differently for each construction, not just materials.
if a.variant=='s2':
    grouped=defaultdict(list)
    for ob in kept:grouped[ob['zone']].append(ob)
    kept=[]
    for zone,obs in grouped.items():
        names=[n for ob in obs for n in json.loads(ob['source_names'])]
        print('GROUP',zone,flush=True)
        ob=join(obs,'S2.'+zone);union(ob,cfg['voxel'],cfg['smooth'])
        ob['zone']=zone;ob['role']='muscle';ob['source_names']=json.dumps(names);ob['selectable']=True
        if len(ob.data.polygons):kept.append(ob)
        else:raise RuntimeError('Empty anatomical group after remesh: '+zone)

# Mirror left anatomy explicitly. Author geometry remains bilateral and named.
for original in list(kept):
    other=original.copy();other.data=original.data.copy();bpy.context.scene.collection.objects.link(other)
    for v in other.data.vertices:v.co.x=-v.co.x
    bm=bmesh.new();bm.from_mesh(other.data);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(other.data);bm.free()
    other['zone']=original['zone'].replace('.left','.right')
    other['source_names']=original['source_names'];other['reflected_from_left']=True
    kept.append(other)

# Neutral covers, authored for the atlas frame. No L1, L2 or L3 mesh is loaded.
support=[]

def make(name,verts,faces):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    ob=bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(ob)
    ob['zone']='support';ob['role']='cover';ob['selectable']=False;support.append(ob);return ob


def loft(name,rows,side=1,group='support',rings=56,around=48,front_extra=0):
    verts=[];faces=[]
    for i in range(rings+1):
        t=i/rings
        scaled=t*(len(rows)-1);j=min(len(rows)-2,int(scaled));f=scaled-j
        # Smoothstep between densely authored cross sections keeps covers neutral.
        f=f*f*(3-2*f)
        x,y,z,rx,ry=[rows[j][k]*(1-f)+rows[j+1][k]*f for k in range(5)]
        for k in range(around):
            angle=2*math.pi*k/around
            point=Vector((x+rx*math.cos(angle),y+ry*math.sin(angle)-front_extra*max(-math.sin(angle),0)**2*gaussian(z,1.16,.25),z))
            verts.append(tuple(transform(point,side,group)))
    for i in range(rings):
        for k in range(around):
            n=(k+1)%around;faces.append((i*around+k,i*around+n,(i+1)*around+n,(i+1)*around+k))
    faces.extend([tuple(reversed(range(around))),tuple(rings*around+k for k in range(around))])
    return make(name,verts,faces)


def ball(name,center,radii,side=1,group='support'):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=20)
    ob=bpy.context.object;ob.name=name
    for v in ob.data.vertices:
        point=Vector([center[i]+v.co[i]*radii[i] for i in range(3)])
        v.co=transform(point,side,group)
    ob['zone']='support';ob['role']='cover';ob['selectable']=False;support.append(ob);return ob


loft('Neutral recessed trunk',[[0,.028,.855,.060,.052],[0,.030,.94,.113,.065],
 [0,.030,1.025,.119,.065],[0,.030,1.12,.107,.066],[0,.030,1.22,.119,.070],
 [0,.032,1.32,.143,.073],[0,.035,1.415,.157,.071],[0,.035,1.468,.149,.050],[0,.033,1.53,.045,.036]],rings=100,around=80,front_extra=.067)
loft('Covered sternum',[[0,-.064,1.27,.008,.012],[0,-.070,1.38,.009,.014],[0,-.025,1.48,.011,.010]],rings=36)
loft('Neutral credible neck',[[0,.035,1.485,.050,.055],[0,.037,1.55,.043,.052],[0,.033,1.62,.042,.037]],rings=52)
# A neutral head, with a closed understated face and no eye/mouth openings.
head=loft('Neutral closed head',[[0,-.005,1.575,.028,.036],[0,.006,1.605,.052,.052],
 [0,.013,1.645,.063,.060],[0,.017,1.69,.070,.068],[0,.020,1.735,.070,.066],
 [0,.020,1.775,.055,.052],[0,.020,1.800,.003,.003]],rings=90,around=80)
# Readable but deliberately low-detail profile: brow/nose, no sculpted expression.
for v in head.data.vertices:
    x,y,z=v.co
    if y<.015:
        front=max(0,min(1,(.015-y)/.05))
        v.co.y-=front*(.010*gaussian(x,0,.016)*gaussian(z,1.68,.022)+.004*gaussian(x,0,.04)*gaussian(z,1.71,.012))
for side in [-1,1]:
    ball('Neutral ear',(.070,.024,1.687),(.008,.012,.023),side)
    ball('Shoulder girdle cover',(.166,.045,1.421),(.055,.060,.073),side)
    # Core branches sit below the actual muscle surfaces, closing joint gaps.
    loft('Humerus joint cover',[[.183,.035,1.475,.034,.035],[.204,.039,1.34,.027,.025],[.228,.033,1.165,.027,.026]],side,'biceps',rings=60)
    loft('Forearm joint cover',[[.228,.033,1.185,.026,.025],[.250,.013,1.05,.022,.022],[.273,-.023,.922,.019,.017]],side,'forearm-flexors',rings=60)
    loft('Palm cover',[[.273,-.023,.936,.019,.018],[.278,-.027,.878,.031,.017],[.279,-.028,.846,.028,.012]],side,'hand',rings=34)
    for offset,length,radius in [(-.026,.060,.007),(-.007,.070,.0075),(.014,.065,.007),(.034,.051,.006)]:
        x=.279+offset
        loft('Neutral finger',[[x,-.028,.856,radius,radius],[x+offset*.08,-.031,.826,radius*.92,radius*.92],
                              [x+offset*.18,-.033,.856-length,radius*.60,radius*.60]],side,'hand',rings=24,around=24)
        ball('Finger tip',(x+offset*.18,-.033,.856-length),(radius*.60,radius*.60,radius*.75),side,'hand')
    loft('Neutral thumb',[[.250,-.030,.894,.010,.009],[.231,-.036,.867,.008,.008],[.224,-.039,.845,.006,.006]],side,'hand',rings=24,around=24)
    ball('Thumb tip',(.224,-.039,.845),(.006,.006,.008),side,'hand')
    loft('Femur joint cover',[[.089,.030,.985,.040,.043],[.090,.031,.78,.043,.040],[.081,.031,.49,.036,.036]],side,'leg',rings=70)
    loft('Tibia ankle cover',[[.081,.031,.51,.037,.037],[.084,.038,.31,.025,.028],[.092,.038,.075,.026,.027]],side,'leg',rings=70)
    ball('Joint sleeve',(.081,.031,.488),(.036,.034,.064),side,'leg')
    ball('Covered patella',(.081,-.008,.486),(.027,.015,.031),side,'leg')
    # Foot sections along Z join ankle to a separate flattened, closed sole.
    ball('Heel',(.094,.044,.046),(.034,.046,.038),side,'leg')
    ball('Midfoot',(.099,-.025,.044),(.036,.085,.030),side,'leg')
    ball('Forefoot',(.104,-.112,.027),(.045,.057,.022),side,'leg')
    for off,r in [(-.030,.013),(-.009,.010),(.010,.009),(.027,.008),(.040,.006)]:
        ball('Neutral toe',(.104+off,-.151+abs(off)*.25,.025),(r,.024,r),side,'leg')

cover=join(support,'S.'+a.variant+'.neutral-support');clean(cover);union(cover,.0028,4)
# Large source muscle masses stay visible; the core only covers underlying gaps.
if a.variant=='s1':
    # Labels travel through a source-surface nearest-normal assignment after union.
    donors=[]
    for ob in kept:
        for v in ob.data.vertices:donors.append((v.co.copy(),ob['zone']))
    for v in cover.data.vertices:donors.append((v.co.copy(),'support'))
    tree=kdtree.KDTree(len(donors))
    for i,(co,zone) in enumerate(donors):tree.insert(co,i)
    tree.balance()
    whole=join(kept+[cover],'S1.continuous-anatomical-envelope');union(whole,cfg['voxel'],cfg['smooth'])
    decimate(whole,cfg['budget'])
    zones=defaultdict(list)
    for face in whole.data.polygons:
        _,i,_=tree.find(face.center);zone=donors[i][1];zones[zone].append(face)
    final=[]
    for zone,faces in zones.items():
        remap={};verts=[];polys=[];normals=[]
        for face in faces:
            row=[]
            for i in face.vertices:
                if i not in remap:
                    remap[i]=len(verts);verts.append(tuple(whole.data.vertices[i].co));normals.append(tuple(whole.data.vertices[i].normal))
                row.append(remap[i])
            polys.append(row)
        mesh=bpy.data.meshes.new(zone);mesh.from_pydata(verts,[],polys);mesh.update()
        for f in mesh.polygons:f.use_smooth=True
        mesh.normals_split_custom_set_from_vertices(normals)
        ob=bpy.data.objects.new('S1.'+zone,mesh);bpy.context.scene.collection.objects.link(ob)
        ob['zone']=zone;ob['selectable']=zone!='support';ob['role']='surface patch';final.append(ob)
    whole.name='S1.hidden-continuous-source';whole.hide_render=True;whole.hide_set(True);whole['render']=False
else:
    final=kept+[cover]
    # Allocate a visible triangle budget by square-root area, preserving small parts.
    weights=[math.sqrt(max(sum(f.area for f in ob.data.polygons),1e-8)) for ob in final]
    for ob,w in zip(final,weights):decimate(ob,max(160,int(cfg['budget']*w/sum(weights))))

rows=[]
for i,ob in enumerate(final):
    ob['render']=True;ob['original_logbook_only']=False;ob['license']='CC-BY-SA-4.0'
    if a.variant!='s1':
        for f in ob.data.polygons:f.use_smooth=True
    ob.data.calc_loop_triangles()
    rows.append({'object':ob.name,'zone':ob['zone'],'selectable':bool(ob.get('selectable')),
                 'role':ob.get('role'),'triangles':len(ob.data.loop_triangles),'vertices':len(ob.data.vertices),
                 'source_names':json.loads(ob.get('source_names','[]')),'reflected_from_left':bool(ob.get('reflected_from_left'))})
report={'variant':a.variant,'method':cfg['method'],'settings':cfg,'blender':bpy.app.version_string,
 'source':str(a.source),'source_sha256':hashlib.sha256(a.source.read_bytes()).hexdigest(),
 'source_origin':'Charleeh/ecorche 320805e06aee51e2e6f6b22533eb2a59d43f2d4d, audited muscles-only checkpoint',
 'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 'license':'CC-BY-SA-4.0','L1_L2_L3_assets_read':False,'skeleton_organs_face_muscles_read_into_output':False,
 'source_left_structures':source_rows,'excluded_count':len(rejected),
 'modifications':['Superficial subset only; central oblique sheath clipped to expose rectus.',
 'Bilateral reflection; global athletic width, tapered waist and local belly enlargement.',
 'Arms abducted 11 degrees; neutral closed head/hands/joints built in atlas frame.',
 'Central abdominal sheath and distal threadlike tendons trimmed; rounded abdominal plates authored over source rectus. Source fibres smoothed; topology simplified; S2 grouped masses remeshed, S1 all volumes unioned.',
 'S1 regions are exploratory nearest-source surface patches, not a final segmentation.',
 'S2/S3 retain intersecting source masses over a cover; not a nonoverlapping final skin partition.'],
 'counts':{'visible_objects':len(rows),'vertices':sum(r['vertices'] for r in rows),'triangles':sum(r['triangles'] for r in rows),
 'selectable_objects':sum(r['selectable'] for r in rows),'selectable_zone_ids':len({r['zone'] for r in rows if r['selectable']})},'objects':rows}
(a.output/'construction.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
bpy.data.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=str(a.output/'model.blend'),compress=True)
print('STYLIZED',json.dumps(report['counts']),flush=True)
