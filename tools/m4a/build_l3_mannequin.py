"""L3 original anatomical design: authored muscle bellies, continuous surface zones.

No external mesh, texture, atlas, addon or anatomical dataset is read. The named
regions are designed surface groups for a stylised product, not muscle organs.
Run with Blender 4.3.2 --factory-startup --disable-autoexec --background.
"""
import argparse
import hashlib
import heapq
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import bpy
import bmesh
import numpy as np
from mathutils import Vector, kdtree

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--variant', choices=['l3'], default='l3')
p.add_argument('--output', type=Path, required=True)
p.add_argument('--voxel', type=float, default=.0025)
p.add_argument('--triangles', type=int, default=72000)
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
a.output.mkdir(parents=True, exist_ok=True)
strength = 1.
groove = .00045
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
parts = []
controls = {}
profile_cache = {}


def g(x, center, width):
    return math.exp(-((x - center) / width) ** 2)


def smooth_profile(rows, t):
    """Monotone cubic Hermite profiles, continuous slope without ring-shaped stops."""
    key = id(rows)
    if key not in profile_cache:
        values = np.array(rows, dtype=float)
        stations, samples = values[:, 0], values[:, 1:]
        intervals = np.diff(stations)
        slopes = np.diff(samples, axis=0) / intervals[:, None]
        derivatives = np.zeros_like(samples)
        derivatives[0], derivatives[-1] = slopes[0], slopes[-1]
        for i in range(1, len(stations) - 1):
            w1, w2 = 2 * intervals[i] + intervals[i - 1], intervals[i] + 2 * intervals[i - 1]
            same = slopes[i - 1] * slopes[i] > 0
            derivatives[i, same] = (w1 + w2) / (w1 / slopes[i - 1, same] + w2 / slopes[i, same])
        profile_cache[key] = (stations, samples, derivatives)
    stations, samples, derivatives = profile_cache[key]
    if t <= rows[0][0]:
        return np.array(rows[0][1:])
    if t >= rows[-1][0]:
        return np.array(rows[-1][1:])
    for i, (lo, hi) in enumerate(zip(rows, rows[1:])):
        if lo[0] <= t <= hi[0]:
            s = (t - lo[0]) / (hi[0] - lo[0])
            h = hi[0] - lo[0]
            return ((2*s**3 - 3*s*s + 1) * samples[i] + (s**3 - 2*s*s + s) * h * derivatives[i]
                    + (-2*s**3 + 3*s*s) * samples[i+1] + (s**3 - s*s) * h * derivatives[i+1])


def mesh_object(name, verts, faces):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    ob = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(ob)
    parts.append(ob)
    return ob


def loft(name, rows, sections=72, around=64, deformation=None):
    # Each row: station, center X/Y/Z, transverse radius, front/back radius.
    controls[name] = rows
    verts, faces = [], []
    for i in range(sections + 1):
        t = rows[0][0] + (rows[-1][0] - rows[0][0]) * i / sections
        values = smooth_profile(rows, t)
        center = Vector(values[:3])
        ta = max(rows[0][0], t - .001)
        tb = min(rows[-1][0], t + .001)
        tangent = Vector(smooth_profile(rows, tb)[:3] - smooth_profile(rows, ta)[:3]).normalized()
        front = Vector((0, -1, 0))
        if abs(tangent.dot(front)) > .90:
            front = Vector((0, 0, 1))  # Horizontal foot loft: upper surface reference.
        transverse = tangent.cross(front).normalized()
        if transverse.x < 0:
            transverse = -transverse
        # Radius variations are authored profiles, never sampled from a model.
        for j in range(around):
            angle = 2 * math.pi * j / around
            point = center + transverse * (values[3] * math.cos(angle)) + front * (values[4] * math.sin(angle))
            if deformation:
                point = deformation(point, t, angle, center, transverse)
            verts.append(tuple(point))
    for i in range(sections):
        for j in range(around):
            nxt = (j + 1) % around
            faces.append((i * around + j, i * around + nxt, (i + 1) * around + nxt, (i + 1) * around + j))
    faces.append(tuple(range(around - 1, -1, -1)))
    faces.append(tuple(sections * around + j for j in range(around)))
    return mesh_object(name, verts, faces)


def ellipsoid(name, location, scale):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=20, location=location)
    ob = bpy.context.object
    ob.name = name
    ob.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    controls[name] = {'center': location, 'radii': scale}
    parts.append(ob)
    return ob


# L3 reauthors the body rather than applying a global inflation to L2. Muscle
# relief exists in geometry before remeshing; no normal map or texture is used.
def ag(angle, center, width):
    d = math.atan2(math.sin(angle-center), math.cos(angle-center))
    return math.exp(-(d/width)**2)


def window(x, lo, hi, feather):
    return .25 * (1+math.tanh((x-lo)/feather)) * (1+math.tanh((hi-x)/feather))


def radial(point, center, amount):
    direction = point-center
    if direction.length:
        point += direction.normalized()*amount
    return point


torso_rows = [
    [.895,0,.014,.895,.060,.045], [.96,0,.014,.96,.132,.082],
    [1.025,0,.012,1.025,.158,.087], [1.09,0,.006,1.09,.140,.079],
    [1.155,0,.002,1.155,.133,.078], [1.225,0,0,1.225,.151,.086],
    [1.295,0,0,1.295,.177,.095], [1.365,0,0,1.365,.191,.096],
    [1.425,0,.004,1.425,.195,.082], [1.465,0,.010,1.465,.193,.065],
    [1.488,0,.014,1.488,.180,.060], [1.520,0,.018,1.520,.111,.049],
    [1.548,0,.020,1.548,.048,.041]]


def torso_shape(point,t,angle,center,transverse):
    x,y,z=point; ax=abs(x)
    front=max(math.sin(angle),0)**2; back=max(-math.sin(angle),0)**2
    # A pectoral fan: sloped clavicle above, curved lower insertion, sternal gap.
    lower=1.329+.068*(ax/.19)**2
    upper=1.469-.14*ax
    pec_mask=window(z,lower,upper,.011)*window(ax,.010,.188,.012)
    pec=.022*pec_mask*g(ax,.094,.105)
    pec_cut=.0035*g(z,lower,.007)*g(ax,.095,.090)
    sternum=.005*g(x,0,.008)*g(z,1.395,.09)
    clavicle=.0065*g(z,1.467-.16*ax,.009)*g(ax,.105,.095)
    # Three paired rounded abdominal plates, broad edges, no fibre striation.
    abs_relief=sum(h*math.exp(-((z-level)/width)**4)*g(ax,.034,.029)
                   for level,h,width in [(1.125,.009,.028),(1.198,.012,.028),(1.269,.012,.027)])
    linea=.004*g(x,0,.0065)*g(z,1.20,.13)
    abs_border=.004*g(ax,.066+.09*(1.23-z),.009)*g(z,1.205,.12)
    oblique=.013*g(ax,.104+.15*(z-1.18),.029)*g(z,1.18,.105)
    # A few broad serratus slips, deliberately low contrast, not rib exposure.
    serratus=sum(.0045*g(z,level-.22*(ax-.13),.013)*g(ax,.142,.035)
                 for level in (1.255,1.288,1.319))
    inguinal=.004*g(z,1.035+.40*ax,.010)*g(ax,.085,.070)
    point.y-=front*(pec-pec_cut-sternum+clavicle+abs_relief-linea-abs_border+oblique+serratus-inguinal)
    # Back: scapular planes, descending trapezius, diagonal lats, lumbar columns.
    lat_center=.090+.42*(z-1.20)
    lat=.033*g(ax,lat_center,.048)*g(z,1.29,.12)
    scap=.022*g(ax,.108,.057)*g(z,1.409,.051)
    trap=.013*g(ax,.047+.24*(z-1.33),.040)*g(z,1.405,.115)
    lat_edge=.007*g(ax,.044+.38*(1.36-z),.009)*g(z,1.275,.105)
    spine=.006*g(x,0,.010)*g(z,1.30,.23)
    lumbar=.009*g(ax,.034,.018)*g(z,1.145,.12)
    glute=.030*g(ax,.082,.071)*g(z,1.005,.063)
    cleft=.007*g(x,0,.010)*g(z,.982,.058)
    point.y+=back*(lat+scap+trap-lat_edge-spine+lumbar+glute-cleft)
    return point


loft('L3 rib cage and anatomical torso',torso_rows,175,144,torso_shape)
# Short, broad neck, overlapping the thoracic trapezius and jaw.
def neck_shape(point,t,angle,center,transverse):
    ax=abs(point.x)
    point.y-=.004*max(math.sin(angle),0)**2*g(ax,.027,.012)*g(t,.5,.40)
    return point
loft('L3 short neck',[[0,0,.017,1.487,.062,.049],[.4,0,.021,1.542,.047,.041],
                     [1,0,.019,1.614,.043,.040]],60,80,neck_shape)
head_rows=[[1.578,0,-.020,1.578,.024,.029],[1.605,0,-.010,1.605,.052,.052],
           [1.637,0,.001,1.637,.063,.059],[1.676,0,.007,1.676,.073,.068],
           [1.715,0,.012,1.715,.075,.071],[1.751,0,.015,1.751,.073,.069],
           [1.781,0,.015,1.781,.054,.049],[1.800,0,.013,1.800,.008,.008]]


def face_shape(point,t,angle,center,transverse):
    x,y,z=point; ax=abs(x); front=max(math.sin(angle),0)**3
    nose=.018*g(x,0,.011)*g(z,1.687,.031)+.015*g(x,0,.015)*g(z,1.673,.009)
    sockets=.008*g(ax,.030,.019)*g(z,1.711,.010)
    brow=.006*g(ax,.030,.025)*g(z,1.726,.008)
    cheek=.007*g(ax,.048,.019)*g(z,1.682,.020)
    mouth=.0035*g(x,0,.024)*g(z,1.638,.0038)
    lip=.003*g(x,0,.023)*g(z,1.644,.004)
    chin=.007*g(x,0,.030)*g(z,1.609,.014)
    point.y-=front*(nose-sockets+brow+cheek-mouth+lip+chin)
    return point
loft('L3 closed face and jaw',head_rows,140,128,face_shape)
for side in (-1,1):
    ellipsoid('L3 ear '+str(side),(side*.075,.014,1.694),(.009,.016,.026))
    shoulder=np.array([side*.210,.005,1.464]); elbow=np.array([side*.300,-.003,1.176])
    wrist=np.array([side*.350,-.011,.948])

    def arm_shape(point,t,angle,center,transverse):
        # A tapered three-headed deltoid integrated into one arm loft. No sphere.
        outward=angle if side==1 else math.pi-angle
        delt=.0075*g(t,.13,.17)*(ag(outward,.30,.65)+.55*ag(outward,1.20,.55)+.62*ag(outward,-.95,.65))
        biceps=.025*g(t,.54,.22)*ag(angle,math.pi/2,.57)
        brachialis=.006*g(t,.66,.20)*ag(outward,.25,.48)
        triceps=.026*g(t,.48,.26)*ag(angle,-math.pi/2,.75)
        triceps_split=.0035*g(t,.55,.23)*ag(angle,-math.pi/2,.12)
        delt_border=.004*g(t,.33,.12)*ag(outward,.58,.16)
        return radial(point,center,delt+biceps+brachialis+triceps-triceps_split-delt_border)
    arms=[(-.12,.026,.030),(0,.050,.048),(.15,.053,.052),(.32,.047,.047),
          (.52,.043,.045),(.73,.035,.037),(.91,.031,.032),(1,.032,.032)]
    arm_rows=[[t,*(shoulder*(1-t)+elbow*t),r,d] for t,r,d in arms]
    arm_rows[0][1:4]=[side*.157,.009,1.476]
    loft('L3 deltoid biceps triceps '+str(side),arm_rows,125,112,arm_shape)

    def forearm_shape(point,t,angle,center,transverse):
        outward=angle if side==1 else math.pi-angle
        amount=.0055*g(t,.30,.25)*ag(outward,.7,.48)+.004*g(t,.40,.30)*ag(angle,-1.1,.6)
        amount-=.002*g(t,.40,.25)*ag(outward,.08,.15)
        return radial(point,center,amount)
    forearms=[(-.13,.030,.031),(0,.032,.032),(.19,.040,.039),(.40,.037,.035),(.68,.028,.027),(1,.021,.020)]
    loft('L3 forearm '+str(side),[[t,*(elbow*(1-t)+wrist*t),r,d] for t,r,d in forearms],80,64,forearm_shape)
    loft('L3 palm '+str(side),[[-.1,side*.348,-.011,.959,.021,.018],[0,*wrist,.021,.018],
                              [.45,side*.362,-.014,.905,.033,.016],[1,side*.371,-.015,.863,.030,.012]],44,56)
    for finger,(offset,length,radius) in enumerate([(-.029,.063,.0075),(-.008,.074,.008),(.014,.069,.0075),(.035,.053,.0065)]):
        start=np.array([side*(.371+offset),-.015,.873])
        end=start+np.array([side*(.006+offset*.18),-.013,-length])
        mid=start*.45+end*.55; mid[1]-=.002
        loft('L3 finger '+str((side,finger)),[[0,*start,radius,radius],[.55,*mid,radius*.91,radius*.91],
                                           [1,*end,radius*.66,radius*.66]],28,24)
        ellipsoid('L3 fingertip '+str((side,finger)),tuple(end),(radius*.66,radius*.66,radius*.85))
    thumb_a=[side*.339,-.017,.909]; thumb_b=[side*.317,-.025,.878]; thumb_c=[side*.312,-.031,.854]
    loft('L3 thumb '+str(side),[[0,*thumb_a,.011,.010],[.6,*thumb_b,.008,.008],[1,*thumb_c,.0065,.006]],32,28)
    ellipsoid('L3 thumb tip '+str(side),thumb_c,(.0065,.006,.008))
    hip=np.array([side*.104,.015,1.073]); knee=np.array([side*.116,-.006,.527]); ankle=np.array([side*.122,.012,.074])

    def thigh_shape(point,t,angle,center,transverse):
        outward=angle if side==1 else math.pi-angle
        # Separate long rectus, lateral vastus and distal medial teardrop.
        rectus=.020*g(t,.45,.30)*ag(angle,math.pi/2,.39)
        lateral=.020*g(t,.44,.29)*ag(outward,.55,.46)
        medial=.023*g(t,.76,.16)*ag(outward,2.48,.43)
        front_split=.0055*g(t,.55,.30)*(ag(outward,1.00,.12)+ag(outward,2.02,.12))
        ham=.020*g(t,.47,.28)*(ag(outward,-.85,.43)+.85*ag(outward,-2.12,.46))
        ham_split=.0055*g(t,.51,.28)*ag(angle,-math.pi/2,.14)
        return radial(point,center,rectus+lateral+medial-front_split+ham-ham_split)
    thighs=[(0,.035,.042),(.15,.073,.074),(.30,.084,.080),(.48,.073,.073),(.66,.058,.062),(.83,.044,.048),(1,.038,.040)]
    loft('L3 quadriceps hamstrings '+str(side),[[t,*(hip*(1-t)+knee*t),r,d] for t,r,d in thighs],140,112,thigh_shape)

    def calf_shape(point,t,angle,center,transverse):
        outward=angle if side==1 else math.pi-angle
        heads=.013*g(t,.31,.19)*ag(outward,-2.05,.48)+.010*g(t,.26,.18)*ag(outward,-1.02,.46)
        split=.004*g(t,.33,.20)*ag(angle,-math.pi/2,.13)
        tibia=.0035*g(t,.44,.40)*ag(angle,1.64,.22)
        soleus=.0045*g(t,.52,.22)*ag(outward,-.4,.6)
        return radial(point,center,heads-split+tibia+soleus)
    calves=[(-.09,.039,.041),(0,.038,.040),(.18,.043,.044),(.36,.046,.049),(.56,.036,.039),(.78,.023,.027),(1,.023,.027)]
    loft('L3 calf soleus tibia '+str(side),[[t,*(knee*(1-t)+ankle*t),r,d] for t,r,d in calves],112,88,calf_shape)
    ellipsoid('L3 patella '+str(side),(side*.116,-.038,.530),(.025,.014,.030))
    foot=[(0,.069,.048,.009,.013),(.14,.042,.050,.028,.037),(.31,-.003,.063,.031,.042),
          (.50,-.052,.053,.033,.032),(.70,-.095,.037,.041,.023),(.88,-.132,.031,.044,.018),(1,-.153,.029,.032,.013)]
    loft('L3 foot contour '+str(side),[[t,side*.122,y,z,rx,rz] for t,y,z,rx,rz in foot],76,64)
    for toe,(offset,length,radius) in enumerate([(-.029,.043,.012),(-.009,.044,.010),(.009,.038,.009),(.025,.031,.008),(.038,.023,.0065)]):
        ellipsoid('L3 toe '+str((side,toe)),(side*(.122+offset),-.145-length*.40,.029),(radius,length*.62,radius))

# Join authored construction solids, orient each closed input outward, then union.
bpy.ops.object.select_all(action='DESELECT')
for ob in parts:
    ob.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
body = bpy.context.object
body.name = 'Original continuous construction'
bm = bmesh.new()
bm.from_mesh(body.data)
bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
bm.to_mesh(body.data)
bm.free()
mod = body.modifiers.new('Union of original lofts', 'REMESH')
mod.mode = 'VOXEL'
mod.voxel_size = a.voxel
mod.use_smooth_shade = True
bpy.ops.object.modifier_apply(modifier=mod.name)
mod = body.modifiers.new('Soften union junctions', 'SMOOTH')
mod.factor, mod.iterations = .68, 5
bpy.ops.object.modifier_apply(modifier=mod.name)
# Bisect once, mirror the authored half with shared plane vertices. Do not leave
# duplicate/capping faces on the sagittal plane as a modifier stack can do.
bm = bmesh.new()
bm.from_mesh(body.data)
bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces),
                      dist=1e-7, plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_inner=True)
for vertex in bm.verts:
    if abs(vertex.co.x) < 1e-6:
        vertex.co.x = 0
bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-7)
bm.verts.ensure_lookup_table()
bm.verts.index_update()
verts = [tuple(v.co) for v in bm.verts]
faces = [tuple(v.index for v in f.verts) for f in bm.faces]
mirror = {}
for i, point in enumerate(list(verts)):
    if point[0] == 0:
        mirror[i] = i
    else:
        mirror[i] = len(verts)
        verts.append((-point[0], point[1], point[2]))
faces += [tuple(mirror[i] for i in reversed(face)) for face in list(faces)]
bm.free()
old_mesh = body.data
body.data = bpy.data.meshes.new('Original symmetric union')
body.data.from_pydata(verts, [], faces)
body.data.update()
bpy.data.meshes.remove(old_mesh)
body.data.calc_loop_triangles()
before = len(body.data.loop_triangles)
mod = body.modifiers.new('Research triangle budget', 'DECIMATE')
mod.ratio = min(1., a.triangles / before)
mod.use_collapse_triangulate = True
bpy.ops.object.modifier_apply(modifier=mod.name)
bm = bmesh.new()
bm.from_mesh(body.data)
bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-7)
bmesh.ops.dissolve_degenerate(bm, edges=list(bm.edges), dist=1e-8)
bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
bm.to_mesh(body.data)
bm.free()

# Design-space regions: surface ownership, not anatomical volumetric segmentation.
zone_names = ['support']
groups = [('pectoralis', 'Pectoral'), ('deltoid', 'Deltoïde'), ('biceps', 'Biceps'),
          ('triceps', 'Triceps'), ('latissimus', 'Grand dorsal'), ('oblique', 'Oblique'),
          ('quadriceps', 'Quadriceps'), ('hamstrings', 'Ischio-jambiers'),
          ('gluteal', 'Fessier'), ('calf', 'Mollet')]
for group, _ in groups:
    zone_names.extend([group + '.left', group + '.right'])
zone_names.extend(['trapezius.midline', 'rectus-abdominis.midline'])
zone_lookup = {name: i for i, name in enumerate(zone_names)}


def classify(point):
    x,y,z=point; ax=abs(x); side='.left' if x>=0 else '.right'
    if .135<z<.490 and y>-.006 and abs(ax-.121)<.078:
        return 'calf'+side
    if .565<z<.943 and abs(ax-.111)<.105:
        if y<-.015 and ax>.055: return 'quadriceps'+side
        if y>.023 and ax>.053: return 'hamstrings'+side
    if .919<z<1.076 and y>.037 and ax<.166: return 'gluteal'+side
    s=Vector((.210,.005,1.464)); e=Vector((.300,-.003,1.176)); pos=Vector((ax,y,z))
    direction=e-s; t=(pos-s).dot(direction)/direction.length_squared
    distance=(pos-(s+t*direction)).length
    if ax>.175 and -.08<t<.34 and distance<.088: return 'deltoid'+side
    if .34<t<.95 and distance<.083 and ax>.204:
        if y<-.010: return 'biceps'+side
        if y>.012: return 'triceps'+side
    if ax<.193 and y<-.022:
        if 1.329+.068*(ax/.19)**2<z<1.469-.14*ax and .009<ax<.188: return 'pectoralis'+side
        if 1.070<z<1.326 and ax<.062: return 'rectus-abdominis.midline'
        if 1.070<z<1.330 and .070<ax<.182: return 'oblique'+side
    if y>.020 and ax<.195:
        width=.019+.145*max(0,min(1,(z-1.235)/.240))
        if 1.235<z<1.520 and ax<width: return 'trapezius.midline'
        if 1.098<z<1.393 and ax>.030+.30*(1.393-z): return 'latissimus'+side
    return 'support'

mesh = body.data
mesh.update()
# Cut the actual shell along the authored design boundaries instead of assigning
# a stair-stepped set of whole triangles from centroid tests. Intersections are
# cached per source edge, so every neighboring face shares the same new vertex.
mesh.calc_loop_triangles()
source_coordinates = [vertex.co.copy() for vertex in mesh.vertices]
source_zones = [zone_lookup[classify(point)] for point in source_coordinates]
new_coordinates = list(source_coordinates)
new_faces, labels, cuts = [], [], {}


def edge_cut(i, j):
    key = tuple(sorted((i, j)))
    if key in cuts:
        return cuts[key]
    i, j = key
    lo, hi = 0., 1.
    for _ in range(22):
        t = (lo + hi) / 2
        identity = zone_lookup[classify(source_coordinates[i].lerp(source_coordinates[j], t))]
        if identity == source_zones[i]:
            lo = t
        else:
            hi = t
    # Avoid numerical slivers when an input vertex sits exactly on a design line.
    t = min(.98, max(.02, (lo + hi) / 2))
    cuts[key] = len(new_coordinates)
    new_coordinates.append(source_coordinates[i].lerp(source_coordinates[j], t))
    return cuts[key]


for triangle in mesh.loop_triangles:
    ids = list(triangle.vertices)
    identities = [source_zones[i] for i in ids]
    distinct = set(identities)
    if len(distinct) == 1:
        new_faces.append(tuple(ids))
        labels.append(identities[0])
    elif len(distinct) == 2:
        singleton = next(i for i in range(3) if identities.count(identities[i]) == 1)
        i, j, k = ids[singleton], ids[(singleton + 1) % 3], ids[(singleton + 2) % 3]
        ij, ki = edge_cut(i, j), edge_cut(k, i)
        new_faces.extend([(i, ij, ki), (ij, j, k, ki)])
        labels.extend([source_zones[i], source_zones[j]])
    else:
        center = len(new_coordinates)
        new_coordinates.append(sum((source_coordinates[i] for i in ids), Vector()) / 3)
        for corner in range(3):
            i, j, k = ids[corner], ids[(corner + 1) % 3], ids[(corner + 2) % 3]
            new_faces.append((i, edge_cut(i, j), center, edge_cut(k, i)))
            labels.append(source_zones[i])
old_mesh = mesh
mesh = bpy.data.meshes.new('Original shell with authored zone boundaries')
mesh.from_pydata([tuple(v) for v in new_coordinates], [], new_faces)
mesh.update()
body.data = mesh
bpy.data.meshes.remove(old_mesh)
attribute = mesh.attributes.new('logbook_surface_zone', 'INT', 'FACE')
for value, label in zip(attribute.data, labels):
    value.value = label
bm = bmesh.new()
bm.from_mesh(mesh)
bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method='BEAUTY', ngon_method='BEAUTY')
bm.to_mesh(mesh)
bm.free()
mesh.update()
labels = [d.value for d in mesh.attributes['logbook_surface_zone'].data]
pre_relief_normals = [poly.normal.copy() for poly in mesh.polygons]
assert set(labels) == set(zone_lookup.values()), 'Every requested zone must exist'
edge_faces = defaultdict(list)
for poly in mesh.polygons:
    for edge in poly.edge_keys:
        edge_faces[tuple(sorted(edge))].append(poly.index)
boundary = set()
boundary_weight = {}


def seam_weight(point, identities):
    """Feather authored relief along useful borders, not horizontal sleeve rings."""
    x, y, z = point
    names = [zone_names[i] for i in identities if i]
    weight = 0.
    for name in names:
        if name.startswith('pectoralis.'):
            weight = max(weight, .8)
        elif name.startswith('deltoid.'):
            weight = max(weight, .65 * g(z, 1.405, .067))
        elif name.startswith(('biceps.', 'triceps.')):
            weight = max(weight, math.exp(-((z - 1.30) / .075) ** 4))
        elif name.startswith(('quadriceps.', 'hamstrings.')):
            weight = max(weight, math.exp(-((z - .758) / .123) ** 4))
        elif name.startswith('calf.'):
            weight = max(weight, math.exp(-((z - .32) / .115) ** 4))
        elif name == 'rectus-abdominis.midline' and abs(x) > .048:
            weight = max(weight, .6 * g(z, 1.18, .09))
        elif name.startswith('latissimus.') or name == 'trapezius.midline':
            weight = max(weight, .7 * g(z, 1.29, .125))
    return weight


for (i, j), faces in edge_faces.items():
    identities = {labels[f] for f in faces}
    if len(identities) > 1:
        for vertex in (i, j):
            weight = seam_weight(mesh.vertices[vertex].co, identities)
            if weight > .01:
                boundary.add(vertex)
                boundary_weight[vertex] = max(boundary_weight.get(vertex, 0), weight)
neighbors = defaultdict(set)
for edge in mesh.edges:
    i, j = edge.vertices
    neighbors[i].add(j)
    neighbors[j].add(i)
# Smooth design seams along the existing surface; the same vertex belongs to
# all adjacent patches, so no inter-patch crack/overlap is introduced.
coordinates = [v.co.copy() for v in mesh.vertices]
normals = [v.normal.copy() for v in mesh.vertices]
distance = {i: 0. for i in boundary}
queue = [(0., i) for i in boundary]
heapq.heapify(queue)
relief_width = .0045
while queue:
    current, i = heapq.heappop(queue)
    if current > distance[i]:
        continue
    for j in neighbors[i]:
        candidate = current + (coordinates[i] - coordinates[j]).length
        if candidate < .014 and candidate < distance.get(j, float('inf')):
            distance[j] = candidate
            boundary_weight[j] = boundary_weight[i]
            heapq.heappush(queue, (candidate, j))
for i, vertex in enumerate(mesh.vertices):
    if i in distance:
        vertex.co -= normals[i] * (groove * boundary_weight[i] * math.exp(-(distance[i] / relief_width) ** 2))
mesh.update()
relief_dots = [poly.normal.dot(before) for poly, before in zip(mesh.polygons, pre_relief_normals)]
desired_displacements = [vertex.co - origin for vertex, origin in zip(mesh.vertices, coordinates)]
relief_scale = 1.
while min(relief_dots) < .80 and relief_scale > 1/128:
    # Exact boundary cuts can create small triangles. Bound the relief globally
    # rather than allowing a steep fold there; the authored muscle volumes remain.
    relief_scale *= .5
    for vertex, origin, displacement in zip(mesh.vertices, coordinates, desired_displacements):
        vertex.co = origin + displacement * relief_scale
    mesh.update()
    relief_dots = [poly.normal.dot(before) for poly, before in zip(mesh.polygons, pre_relief_normals)]
assert min(relief_dots) >= .80, 'Relief must preserve the pre-relief triangle orientation'
for poly in mesh.polygons:
    poly.use_smooth = True

bm = bmesh.new()
bm.from_mesh(mesh)
bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
bm.to_mesh(mesh)
bm.free()
# Recalc does not change face order, so keep the authored ownership map.
labels = [d.value for d in mesh.attributes['logbook_surface_zone'].data]
mesh.calc_loop_triangles()
points = [vertex.co.copy() for vertex in mesh.vertices]
geometric_normals = [vertex.normal.copy() for vertex in mesh.vertices]
vertex_areas = [0.] * len(points)
for triangle in mesh.loop_triangles:
    for index in triangle.vertices:
        vertex_areas[index] += triangle.area / 3
tree = kdtree.KDTree(len(points))
for i, point in enumerate(points):
    tree.insert(point, i)
tree.balance()
shading_normals = []
for i, point in enumerate(points):
    # Preserve small facial/hand/foot features; homogenize broad body reflections.
    if point.z < .14 or (point.z < .97 and abs(point.x) > .28):
        shading_normals.append(tuple(geometric_normals[i]))
        continue
    normal = Vector()
    for _, neighbor, distance_m in tree.find_range(point, .004 if point.z > 1.56 else .008):
        weight = vertex_areas[neighbor] * math.exp(-(distance_m / (.002 if point.z > 1.56 else .004)) ** 2)
        normal += geometric_normals[neighbor] * weight
    assert normal.length > 0
    shading_normals.append(tuple(normal.normalized()))
mesh.normals_split_custom_set_from_vertices(shading_normals)
counts = Counter(labels)
records = []
for zone, zone_id in zone_lookup.items():
    polygons = [poly for poly in mesh.polygons if labels[poly.index] == zone_id]
    remap, vertices, faces = {}, [], []
    for polygon in polygons:
        face = []
        for index in polygon.vertices:
            if index not in remap:
                remap[index] = len(vertices)
                vertices.append(tuple(mesh.vertices[index].co))
            face.append(remap[index])
        faces.append(tuple(face))
    part_mesh = bpy.data.meshes.new(zone)
    part_mesh.from_pydata(vertices, [], faces)
    part_mesh.update()
    # Preserve the continuous shell's split normals across logical selection seams.
    for poly in part_mesh.polygons:
        poly.use_smooth = True
    source_indices = sorted(remap, key=remap.get)
    part_mesh.normals_split_custom_set_from_vertices([shading_normals[i] for i in source_indices])
    source_face_attribute = part_mesh.attributes.new('logbook_source_face', 'INT', 'FACE')
    for item, polygon in zip(source_face_attribute.data, polygons):
        item.value = polygon.index
    source_vertex_attribute = part_mesh.attributes.new('logbook_source_vertex', 'INT', 'POINT')
    for item, index in zip(source_vertex_attribute.data, source_indices):
        item.value = index
    ob = bpy.data.objects.new('LB.' + zone, part_mesh)
    bpy.context.scene.collection.objects.link(ob)
    ob['logbook_zone'] = zone
    ob['logbook_selectable'] = zone != 'support'
    ob['logbook_render'] = True
    ob['logbook_original_geometry'] = True
    part_mesh.calc_loop_triangles()
    records.append({'object': ob.name, 'zone': zone, 'selectable': zone != 'support',
                    'vertices': len(vertices), 'triangles': len(part_mesh.loop_triangles),
                    'source_faces': len(polygons),
                    'source_face_indices_sha256': hashlib.sha256(np.array([poly.index for poly in polygons], dtype='<i4').tobytes()).hexdigest()})
body.hide_render = True
body.hide_set(True)
body['logbook_render'] = False
body['logbook_purpose'] = 'Continuous closed authoring surface; same faces as the visible logical patches'
body.name = 'LB.Construction.closed-surface'
report = {'variant': a.variant, 'authored_original': True, 'art_direction': 'L3 stylised fitness atlas; entirely reauthored anatomical profiles and radial muscle relief', 'pipeline_origin': 'Shared mesh processing and patch partition algorithm derived from build_original_mannequin.py at f3bfda6; historical files unchanged', 'external_assets_read': [],
          'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'blender': bpy.app.version_string, 'parameters': {'volume_strength': strength, 'requested_seam_depth_m': groove, 'seam_depth_m': groove * relief_scale, 'relief_scale_after_orientation_guard': relief_scale, 'relief_width_m': relief_width, 'voxel_size_m': a.voxel, 'triangle_target': a.triangles},
          'controls': controls,
          'semantics': 'Original stylised surface zones, not medical muscle organs or a validated atlas. Objects are exact disjoint face subsets of the continuous shell.',
          'zone_names': zone_names, 'selectable_zones': len(zone_names) - 1,
          'counts': {'continuous_vertices': len(mesh.vertices), 'continuous_triangles': len(mesh.loop_triangles),
                     'visible_objects': len(records), 'visible_vertices_including_shared_seams': sum(r['vertices'] for r in records),
                     'visible_triangles': sum(r['triangles'] for r in records)},
          'zone_boundary_cut_vertices': len(cuts),
          'relief_geometry_check': {'triangles_inverted_relative_to_pre_relief': 0, 'minimum_normal_dot_before_after_relief': min(relief_dots), 'distance_metric': 'shortest surface edge distance in metres'},
          'shading_normal_filter': {'radius_m': .008, 'gaussian_sigma_m': .004, 'weighting': 'incident triangle area', 'head_radius_m': .004, 'head_gaussian_sigma_m': .002, 'hands_feet_preserved': True, 'geometry_moved_by_filter': False, 'shared_normals_transferred_to_zone_objects': True},
          'records': records}
assert report['counts']['continuous_triangles'] == report['counts']['visible_triangles']
assert report['selectable_zones'] == 22
(a.output / 'construction.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
bpy.data.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=str(a.output / 'logbook-original.blend'), compress=True)
print('ORIGINAL', json.dumps(report['counts']), 'zones', report['selectable_zones'], flush=True)
