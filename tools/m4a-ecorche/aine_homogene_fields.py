"""Local compact smooth-union distance field; no retained source mesh edited."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

PLANE = .002114987923242599


def core_mesh():
    # Rounded, receding saddle: no flat vertical front / horizontal bottom lip.
    v, f = [], []
    n, rows = 64, 40
    for j in range(1, rows):
        t = np.pi*j/rows
        z = .941+.035*np.cos(t)
        cy = -.027-.45*(z-.941)
        for k in range(n):
            p = 2*np.pi*k/n
            v.append([PLANE+.060*np.sin(t)*np.sin(p), cy-.030*np.sin(t)*np.cos(p), z])
    top, bottom = len(v), len(v)+1
    v.extend([[PLANE, -.04275, .976], [PLANE, -.01125, .906]])
    for j in range(rows-2):
        for k in range(n):
            u, w = j*n+k, j*n+(k+1)%n
            f.extend([(u, w, w+n), (u, w+n, u+n)])
    for k in range(n):
        f.append((top, (k+1)%n, k))
        u, w = (rows-2)*n+k, (rows-2)*n+(k+1)%n
        f.append((bottom, u, w))
    return np.array(v), np.array(f, np.int32)


def signed(tree, point, orientation):
    q, normal, index, distance = tree.find_nearest(Vector(point))
    sign = -1 if (Vector(point)-q).dot(normal)*orientation < 0 else 1
    return sign*distance


def mesh_tree(v, f):
    volume = np.einsum('ij,ij->i', v[f[:, 0]], np.cross(v[f[:, 1]], v[f[:, 2]])).sum()/6
    return BVHTree.FromPolygons(v.tolist(), f.tolist(), all_triangles=True), (1 if volume > 0 else -1)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--work', type=Path, required=True)
    a = p.parse_args(sys.argv[sys.argv.index('--')+1:])
    a.work.mkdir(parents=True, exist_ok=True)
    source_hash = hashlib.sha256(a.baseline.read_bytes()).hexdigest()
    prior = json.loads((a.baseline.parent/'finition.json').read_text())
    assert source_hash == prior['master_sha256']
    bpy.ops.wm.open_mainfile(filepath=str(a.baseline.resolve()), use_scripts=False)
    scene = bpy.data.scenes[prior['scene']]
    bpy.context.window.scene = scene
    scene.view_layers[0].update()
    graph = bpy.context.evaluated_depsgraph_get()
    h, radius = .00125, .008
    xs = PLANE+np.arange(-65, 66)*h
    ys, zs = -.075+np.arange(121)*h, .885+np.arange(89)*h
    grid = np.stack(np.meshgrid(xs, ys, zs, indexing='ij'), axis=-1)
    points = grid.reshape(-1, 3)
    cv, cf = core_mesh()
    tree, orientation = mesh_tree(cv, cf)
    core = np.array([signed(tree, q, orientation) for q in points], np.float32)
    active = (core > -radius-2*h) & (core < radius+3*h)
    body = np.full(len(points), .25, np.float32)
    records, arrays = [], {}
    for ob in scene.objects:
        if ob.type != 'MESH' or ob['asset_id'] == 'groin.neutral_surface':
            continue
        ev = ob.evaluated_get(graph)
        m = ev.to_mesh()
        v = np.array([ob.matrix_world@q.co for q in m.vertices])
        f = np.array([q.vertices[:] for q in m.polygons], np.int32)
        normals = np.array([q.vector[:] for q in m.corner_normals]).reshape(-1, 3, 3)
        ev.to_mesh_clear()
        lo, hi = v.min(0), v.max(0)
        query = np.flatnonzero(active & np.all(points >= lo-radius-2*h, axis=1)
                               & np.all(points <= hi+radius+2*h, axis=1))
        if not len(query):
            continue
        # GLB UV/normal seams duplicate vertices at identical coordinates. Weld
        # these indices for the closure diagnostic only, never in the source.
        _, index_map = np.unique(v.astype(np.float32), axis=0, return_inverse=True)
        welded = index_map[f]
        edges = np.sort(np.concatenate([welded[:, [0, 1]], welded[:, [1, 2]], welded[:, [2, 0]]]), axis=1)
        _, counts = np.unique(edges, axis=0, return_counts=True)
        closed = bool(np.all(counts == 2))
        if not closed:
            records.append({'id': ob['asset_id'], 'used_for_distance_field': False,
                            'reason': 'Source component is not closed; retained unchanged in render.'})
            continue
        tree, orientation = mesh_tree(v, f)
        values = np.array([signed(tree, points[i], orientation) for i in query], np.float32)
        body[query] = np.minimum(body[query], values)
        key = ob['asset_id']
        arrays[key+'__v'], arrays[key+'__f'], arrays[key+'__n'] = v, f, normals
        records.append({'id': key, 'used_for_distance_field': True, 'samples': len(query)})
        print('FIELD', key, len(query), flush=True)
    shape = grid.shape[:3]
    body, core = body.reshape(shape), core.reshape(shape)
    body, core = (body+body[::-1])/2, (core+core[::-1])/2
    # Compact C1 smooth minimum: outside radius it equals the original union.
    blend = np.maximum(radius-np.abs(body-core), 0)/radius
    field = np.minimum(body, core)-radius*.25*blend*blend
    np.savez_compressed(a.work/'fields.npz', field=field, body=body, core=core,
                        origin=grid[0, 0, 0], step=h, radius=radius)
    np.savez_compressed(a.work/'sources.npz', **arrays)
    np.savez_compressed(a.work/'core.npz', v=cv, f=cf)
    (a.work/'fields.json').write_text(json.dumps({
        'baseline_commit': 'd94297af21a05dacaa1f19a1ce64c7b64f447ea4',
        'baseline_blend_sha256': source_hash, 'source_scene': scene.name,
        'grid_step_m': h, 'blend_radius_m': radius, 'grid_shape': shape,
        'maximum_smooth_union_offset_m': radius/4,
        'method': 'Rounded receding core and compact C1 smooth minimum of local signed distances to retained closed source components.',
        'core_parameters_m': {'center_xz': [PLANE, .941], 'radii_xyz': [.060, .030, .035],
                              'center_y': -.027, 'posterior_slope_toward_bottom': .45},
        'sources': records, 'source_meshes_modified': 0,
        'fields_sha256': hashlib.sha256((a.work/'fields.npz').read_bytes()).hexdigest(),
        'sources_sha256': hashlib.sha256((a.work/'sources.npz').read_bytes()).hexdigest(),
    }, indent=2)+'\n')
    print('FIELDS_READY', shape, flush=True)


if __name__ == '__main__':
    main()
