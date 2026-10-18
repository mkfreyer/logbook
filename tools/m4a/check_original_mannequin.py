"""Numerical M4A checks for an original continuous shell and its surface zones.

No claim of medical validation, production retopology or iPhone performance.
"""
import argparse, hashlib, json, sys
from collections import Counter
from pathlib import Path
import bpy
import bmesh
import numpy as np

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--prepared', type=Path, required=True)
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
bpy.ops.wm.open_mainfile(filepath=str(a.prepared / 'logbook-original.blend'), use_scripts=False)
base = bpy.data.objects['LB.Construction.closed-surface']
mesh = base.data
mesh.calc_loop_triangles()
xyz = np.empty(len(mesh.vertices) * 3, dtype=np.float64)
mesh.vertices.foreach_get('co', xyz)
xyz = xyz.reshape((-1, 3))
assert np.isfinite(xyz).all()
indices = np.empty(len(mesh.loop_triangles) * 3, dtype=np.int32)
mesh.loop_triangles.foreach_get('vertices', indices)
indices = indices.reshape((-1, 3))
triangles = xyz[indices]
double_area = np.linalg.norm(np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0]), axis=1)
assert np.all(double_area > 1e-12), 'Collapsed triangle in authored shell'
bm = bmesh.new()
bm.from_mesh(mesh)
bm.verts.ensure_lookup_table()
nonmanifold = sum(not e.is_manifold for e in bm.edges)
boundary = sum(e.is_boundary for e in bm.edges)
loose = sum(not v.link_faces for v in bm.verts)
components = []
unseen = set(bm.verts)
while unseen:
    first = unseen.pop()
    pending, count = [first], 0
    while pending:
        vertex = pending.pop()
        count += 1
        for edge in vertex.link_edges:
            other = edge.other_vert(vertex)
            if other in unseen:
                unseen.remove(other)
                pending.append(other)
    components.append(count)
volume = bm.calc_volume(signed=True)
euler = len(bm.verts) - len(bm.edges) + len(bm.faces)
bm.free()
assert nonmanifold == 0 and boundary == 0 and loose == 0
assert len(components) == 1, f'Body must be one connected shell, got {components}'
assert volume > 0
assert euler == 2, 'The authored closed figure must have no accidental topological handles'
labels = [d.value for d in mesh.attributes['logbook_surface_zone'].data]
construction = json.loads((a.prepared / 'construction.json').read_text())
zones = construction['zone_names']
visible = [ob for ob in bpy.context.scene.objects if ob.type == 'MESH' and ob.get('logbook_render')]
assert len(visible) == len(zones) == 23
seen = Counter()
rows = []
for ob in visible:
    zone = ob['logbook_zone']
    source_faces = [d.value for d in ob.data.attributes['logbook_source_face'].data]
    source_vertices = [d.value for d in ob.data.attributes['logbook_source_vertex'].data]
    assert all(labels[i] == zones.index(zone) for i in source_faces)
    for local, source_index in zip(ob.data.vertices, source_vertices):
        assert tuple(local.co) == tuple(mesh.vertices[source_index].co)
    for poly, source_index in zip(ob.data.polygons, source_faces):
        assert tuple(source_vertices[i] for i in poly.vertices) == tuple(mesh.polygons[source_index].vertices)
    seen.update(source_faces)
    ob.data.calc_loop_triangles()
    center = [sum(v.co[i] for v in ob.data.vertices) / len(ob.data.vertices) for i in range(3)]
    if zone.endswith('.left'):
        assert center[0] > 0
    if zone.endswith('.right'):
        assert center[0] < 0
    rows.append({'zone': zone, 'vertices': len(ob.data.vertices), 'triangles': len(ob.data.loop_triangles), 'centroid': center, 'selectable': bool(ob['logbook_selectable'])})
    adjacency = {i: set() for i in range(len(ob.data.vertices))}
    for edge in ob.data.edges:
        i, j = edge.vertices
        adjacency[i].add(j)
        adjacency[j].add(i)
    remaining = set(adjacency)
    sizes = []
    while remaining:
        pending = [remaining.pop()]
        count = 0
        while pending:
            i = pending.pop()
            count += 1
            for j in adjacency[i]:
                if j in remaining:
                    remaining.remove(j)
                    pending.append(j)
        sizes.append(count)
    rows[-1]['connected_components'] = len(sizes)
    rows[-1]['component_vertex_counts'] = sorted(sizes, reverse=True)
assert set(seen) == set(range(len(mesh.polygons))) and all(n == 1 for n in seen.values())
assert sum(r['triangles'] for r in rows) == len(mesh.loop_triangles)
assert sum(r['selectable'] for r in rows) == 22
report = {'variant': construction['variant'], 'blender': bpy.app.version_string,
          'source_blend_sha256': hashlib.sha256((a.prepared / 'logbook-original.blend').read_bytes()).hexdigest(),
          'continuous_shell': {'vertices': len(xyz), 'triangles': len(indices), 'connected_components': len(components),
                               'boundary_edges': boundary, 'nonmanifold_edges': nonmanifold, 'loose_vertices': loose,
                               'nonfinite_coordinates': 0, 'near_degenerate_triangles': 0,
                               'minimum_double_triangle_area_m2': float(double_area.min()), 'signed_volume_m3': volume,
                               'euler_characteristic': euler, 'surface_genus': (2 - euler) / 2,
                               'bounds_min': xyz.min(axis=0).tolist(), 'bounds_max': xyz.max(axis=0).tolist()},
          'surface_zones': {'selectable': 22, 'support_objects': 1, 'all_source_faces_used_once': True,
                            'duplicated_source_faces': 0, 'lost_source_faces': 0,
                            'shared_border_positions_identical': True, 'named_sides_centroids_correct': True, 'zones': rows},
          'limitations': ['Surface zones are stylised design regions, not anatomical muscle organs.',
                         'Individual patches have open borders by design; the aggregated source shell is closed.',
                         'No exhaustive self-intersection/occlusion/medical test.',
                         'Voxel/decimated triangles are a research mesh, not animation-ready quad retopology.',
                         'No interactive engine, raycast, rig, GLB export or iPhone benchmark.']}
(a.prepared / 'geometry-check.json').write_text(json.dumps(report, indent=2) + '\n')
print('ORIGINAL_CHECK', json.dumps(report['continuous_shell']), 'zones', 22, flush=True)
