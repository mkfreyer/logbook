"""Original Logbook research mannequin: analytic lofts, voxel union, surface zones.

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
p.add_argument('--variant', choices=['soft', 'defined'], required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--voxel', type=float, default=.0025)
p.add_argument('--triangles', type=int, default=72000)
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
a.output.mkdir(parents=True, exist_ok=True)
strength = .55 if a.variant == 'soft' else 1.35
groove = .00065 if a.variant == 'soft' else .00135
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


torso_rows = [
    [.90, 0, 0, .90, .065, .050],
    [.95, 0, .004, .95, .128, .081],
    [1.015, 0, .004, 1.015, .174, .095],
    [1.075, 0, .001, 1.075, .150, .090],
    [1.145, 0, 0, 1.145, .137, .081],
    [1.22, 0, 0, 1.22, .159, .088],
    [1.29, 0, 0, 1.29, .180, .095],
    [1.36, 0, 0, 1.36, .194, .096],
    [1.415, 0, 0, 1.415, .196, .084],
    [1.455, 0, .003, 1.455, .152, .066],
    [1.495, 0, .005, 1.495, .062, .052],
]


def torso_shape(point, t, angle, center, transverse):
    x, y, z = point
    ax = abs(x)
    front = max(math.sin(angle), 0)
    back = max(-math.sin(angle), 0)
    # Broad pectoral planes taper at their upper/lateral insertion.
    pec = .025 * strength * g(ax, .100, .077) * math.exp(-((z - 1.352) / .060) ** 4)
    sternum = .006 * strength * g(x, 0, .012) * g(z, 1.36, .085)
    lower_pec = .004 * strength * g(z, 1.295 + .09 * (ax / .19) ** 3, .009) * g(ax, .10, .087)
    abs_volume = sum(.009 * strength * g(z, level, .024) * g(ax, .031, .028) for level in (1.105, 1.172, 1.235))
    linea = .0035 * strength * g(x, 0, .006) * g(z, 1.175, .11)
    inguinal = .003 * strength * g(z, 1.035 + .35 * ax, .008) * g(ax, .08, .07)
    oblique = .009 * strength * g(ax, .108, .036) * g(z, 1.16, .10)
    oblique_border = .004 * strength * g(ax, .061 + .20 * (1.25 - z), .007) * g(z, 1.16, .09)
    point.y -= front ** 2 * (pec - sternum - lower_pec + abs_volume - linea - inguinal + oblique - oblique_border)
    # Rear masses: fan-shaped latissimus, central trapezius and gluteal lobes.
    lat = .019 * strength * g(ax, .113, .065) * g(z, 1.275, .12)
    trap = .013 * strength * g(ax, .055, .07) * g(z, 1.407, .075)
    spine = .005 * strength * g(x, 0, .008) * g(z, 1.29, .18)
    glute = .023 * strength * g(ax, .083, .074) * g(z, 1.003, .065)
    cleft = .005 * strength * g(x, 0, .010) * g(z, .981, .06)
    lat_border = .007 * strength * g(ax, .035 + .32 * (1.37 - z), .010) * g(z, 1.275, .11)
    point.y += back ** 2 * (lat + trap - spine + glute - cleft - lat_border)
    return point


loft('Torso original', torso_rows, 130, 96, torso_shape)
loft('Neck original', [[0, 0, .012, 1.470, .058, .051], [.5, 0, .023, 1.550, .044, .040], [1, 0, .025, 1.625, .038, .036]], 48, 64)


head_rows = [[1.580, 0, -.015, 1.580, .018, .025],
             [1.612, 0, -.010, 1.612, .050, .049],
             [1.645, 0, .003, 1.645, .062, .061],
             [1.680, 0, .006, 1.680, .073, .067],
             [1.721, 0, .010, 1.721, .075, .071],
             [1.758, 0, .013, 1.758, .073, .067],
             [1.786, 0, .013, 1.786, .050, .045],
             [1.802, 0, .012, 1.802, .004, .004]]


def face_shape(point, t, angle, center, transverse):
    x, y, z = point
    front = max(math.sin(angle), 0) ** 4
    # Closed stylised face: eye sockets are shallow relief, never empty holes.
    nose = .018 * g(x, 0, .012) * g(z, 1.690, .031) + .011 * g(x, 0, .018) * g(z, 1.677, .011)
    sockets = .010 * sum(g(x, side * .031, .020) * g(z, 1.711, .012) for side in (-1, 1))
    brow = .005 * sum(g(x, side * .031, .026) * g(z, 1.729, .009) for side in (-1, 1))
    cheeks = .005 * sum(g(x, side * .046, .022) * g(z, 1.684, .019) for side in (-1, 1))
    lips = .003 * g(x, 0, .027) * g(z, 1.648, .005)
    chin = .005 * g(x, 0, .028) * g(z, 1.621, .014)
    point.y -= front * (nose - sockets + brow + cheeks + lips + chin)
    return point


loft('Head original closed', head_rows, 100, 96, face_shape)
for side in (-1, 1):
    ellipsoid('Ear ' + str(side), (side * .075, .014, 1.695), (.010, .017, .027))
    # Shoulder mass has one continuous junction to the thorax and upper arm.
    ellipsoid('Deltoid construction ' + str(side), (side * .207, .001, 1.418),
              (.071 + .004 * strength, .070 + .004 * strength, .071))
    shoulder = np.array([side * .222, 0, 1.423])
    elbow = np.array([side * .302, -.004, 1.166])
    wrist = np.array([side * .346, -.008, .939])

    def arm_deform(point, t, angle, center, transverse):
        front, back = max(math.sin(angle), 0), max(-math.sin(angle), 0)
        point.y -= .008 * strength * front ** 3 * g(t, .53, .23)
        point.y += .008 * strength * back ** 3 * g(t, .45, .29)
        point += transverse * (-.003 * strength * math.cos(angle) * g(math.sin(angle), 0, .22) * g(t, .55, .3))
        return point

    arm_radii = [(0, .063, .063), (.17, .068, .067), (.36, .055, .056),
                 (.59, .050, .055), (.80, .040, .043), (1, .035, .036)]
    loft('Upper arm ' + str(side), [[t, *(shoulder * (1 - t) + elbow * t), r1, r2] for t, r1, r2 in arm_radii], 72, 64, arm_deform)
    forearm_radii = [(-.12, .034, .034), (0, .035, .035), (.20, .044, .041), (.42, .042, .038),
                     (.68, .032, .030), (1, .023, .022)]
    loft('Forearm ' + str(side), [[t, *(elbow * (1 - t) + wrist * t), r1, r2] for t, r1, r2 in forearm_radii], 64, 48)
    loft('Palm ' + str(side), [[-.15, side * .342, -.008, .950, .022, .020], [0, *wrist, .023, .020],
                              [.48, side * .358, -.009, .895, .033, .016],
                              [1, side * .365, -.010, .856, .027, .012]], 32, 40)
    # Clear inter-finger gaps exceed the voxel size: no accidental bridges/handles.
    for finger, (offset, length, radius) in enumerate([(-.027, .057, .007), (-.008, .066, .0075), (.012, .061, .007), (.031, .046, .006)]):
        start = np.array([side * (.365 + offset), -.011, .864])
        end = start + np.array([side * (.006 + offset * .16), -.009, -length])
        loft('Finger ' + str((side, finger)), [[0, *start, radius, radius], [.5, *((start + end) / 2), radius * .91, radius * .91], [1, *end, radius * .65, radius * .65]], 22, 20)
        ellipsoid('Fingertip ' + str((side, finger)), tuple(end), (radius * .65, radius * .65, radius * .80))
    thumb_a = [side * .334, -.010, .901]
    thumb_b = [side * .317, -.018, .870]
    thumb_c = [side * .312, -.025, .849]
    loft('Thumb ' + str(side), [[0, *thumb_a, .010, .009], [.6, *thumb_b, .008, .007], [1, *thumb_c, .006, .006]], 24, 24)
    ellipsoid('Thumb tip ' + str(side), thumb_c, (.006, .006, .008))
    hip = np.array([side * .104, .011, 1.082])
    knee = np.array([side * .112, -.008, .528])
    ankle = np.array([side * .115, .010, .074])

    def thigh_deform(point, t, angle, center, transverse):
        front, back = max(math.sin(angle), 0), max(-math.sin(angle), 0)
        point.y -= strength * .010 * front ** 3 * g(t, .48, .28)
        point.y += strength * .008 * back ** 3 * g(t, .40, .26)
        point.y += strength * .004 * front ** 2 * g(abs(math.cos(angle)), .48, .14) * g(t, .57, .29)
        point.y -= strength * .004 * back ** 3 * g(math.cos(angle), 0, .20) * g(t, .48, .28)
        # Two broad quadriceps bellies, no medical fibre striations.
        point += transverse * (strength * .005 * math.cos(angle) * g(t, .65, .25))
        return point

    thigh_radii = [(0, .035, .043), (.14, .079, .078), (.29, .091, .088), (.47, .082, .084),
                   (.67, .070, .073), (.85, .053, .056), (1, .046, .047)]
    loft('Thigh ' + str(side), [[t, *(hip * (1 - t) + knee * t), r1, r2] for t, r1, r2 in thigh_radii], 96, 72, thigh_deform)

    def calf_deform(point, t, angle, center, transverse):
        point.y += .010 * strength * max(-math.sin(angle), 0) ** 2 * g(t, .37, .24)
        point.y -= .004 * strength * max(-math.sin(angle), 0) ** 3 * g(math.cos(angle), 0, .22) * g(t, .36, .22)
        return point

    calf_radii = [(-.08, .046, .046), (0, .046, .046), (.19, .052, .053), (.38, .057, .059),
                  (.59, .047, .050), (.80, .031, .034), (1, .025, .028)]
    loft('Lower leg ' + str(side), [[t, *(knee * (1 - t) + ankle * t), r1, r2] for t, r1, r2 in calf_radii], 80, 64, calf_deform)
    ellipsoid('Covered knee ' + str(side), (side * .112, -.041, .528), (.031, .018, .032))
    # One authored foot contour, rather than three bulb-shaped construction solids.
    foot_profile = [(0, .075, .050, .010, .016), (.12, .045, .055, .033, .041),
                    (.30, -.002, .070, .035, .048), (.50, -.050, .061, .038, .038),
                    (.68, -.090, .044, .045, .027), (.85, -.128, .035, .047, .022),
                    (1, -.151, .032, .035, .015)]
    loft('Foot original ' + str(side), [[t, side * .115, y, z, rx, rz] for t, y, z, rx, rz in foot_profile], 64, 48)
    for toe, (offset, length, radius) in enumerate([(-.030, .040, .013), (-.010, .042, .010), (.008, .036, .009), (.024, .029, .008), (.037, .022, .007)]):
        ellipsoid('Toe ' + str((side, toe)), (side * (.115 + offset), -.144 - length * .42, .032), (radius, length * .65, radius))

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
    x, y, z = point
    ax = abs(x)
    side = '.left' if x >= 0 else '.right'
    if .139 < z < .491 and y > -.007 and abs(ax - .115) < .080:
        return 'calf' + side
    if .568 < z < .946 and abs(ax - .110) < .112:
        dx = ax - (.104 + (.112 - .104) * (1.005 - z) / .477)
        if y < -.017 and dx > -.061:
            return 'quadriceps' + side
        if y > .025 and dx > -.057:
            return 'hamstrings' + side
    if .912 < z < 1.076 and y > .033 and ax < .177:
        return 'gluteal' + side
    # Upper-arm coordinate follows the designed shoulder/elbow segment.
    s = Vector((.222, 0, 1.423))
    e = Vector((.302, -.004, 1.166))
    pos = Vector((ax, y, z))
    direction = e - s
    t = (pos - s).dot(direction) / direction.length_squared
    axis_distance = (pos - (s + t * direction)).length
    if ax > .162 and 1.318 < z < 1.505 and (pos - Vector((.207, .001, 1.426))).length < .092:
        return 'deltoid' + side
    if .26 < t < .94 and axis_distance < .085 and ax > .195:
        if y < -.009:
            return 'biceps' + side
        if y > .012:
            return 'triceps' + side
    if ax < .191 and y < -.018:
        if 1.295 + .09 * (ax / .19) ** 3 < z < 1.434 - .12 * ax and .009 < ax < .190:
            return 'pectoralis' + side
        if 1.068 < z < 1.293 and ax < .055 + .012 * g(z, 1.21, .07):
            return 'rectus-abdominis.midline'
        if 1.071 < z < 1.300 and ax > .068 and ax < .183:
            return 'oblique' + side
    if y > .017 and ax < .194:
        trap_width = .018 + .150 * max(0, min(1, (z - 1.225) / .225))
        if 1.222 < z < 1.495 and ax < trap_width:
            return 'trapezius.midline'
        if 1.098 < z < 1.368 and ax > .027 + .32 * (1.368 - z) and ax < .190:
            return 'latissimus' + side
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
    if point.z > 1.56 or point.z < .14 or (point.z < .97 and abs(point.x) > .28):
        shading_normals.append(tuple(geometric_normals[i]))
        continue
    normal = Vector()
    for _, neighbor, distance_m in tree.find_range(point, .008):
        weight = vertex_areas[neighbor] * math.exp(-(distance_m / .004) ** 2)
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
report = {'variant': a.variant, 'authored_original': True, 'external_assets_read': [],
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
          'shading_normal_filter': {'radius_m': .008, 'gaussian_sigma_m': .004, 'weighting': 'incident triangle area', 'head_hands_feet_preserved': True, 'geometry_moved_by_filter': False, 'shared_normals_transferred_to_zone_objects': True},
          'records': records}
assert report['counts']['continuous_triangles'] == report['counts']['visible_triangles']
assert report['selectable_zones'] == 22
(a.output / 'construction.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
bpy.data.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=str(a.output / 'logbook-original.blend'), compress=True)
print('ORIGINAL', json.dumps(report['counts']), 'zones', report['selectable_zones'], flush=True)
