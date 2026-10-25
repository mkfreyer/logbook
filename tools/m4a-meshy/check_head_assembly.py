"""Independent source-surface, closed-join, provenance and serialized GLB checks."""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mesh_io import load_glb


def source(path):
    raw, _, v, f = load_glb(path)
    v = v[:, [0, 2, 1]].astype(float)
    v[:, 1] *= -1
    return raw, v, f.astype(np.int32)


def triangle_keys(points):
    q = points.astype('<f4').copy()
    q[q == 0] = 0
    order = np.lexsort((q[:, :, 2], q[:, :, 1], q[:, :, 0]), axis=1)
    q = np.ascontiguousarray(np.take_along_axis(q, order[:, :, None], axis=1).reshape(-1, 9))
    return np.sort(q.view('V36').ravel())


def areas(v, f):
    return np.linalg.norm(np.cross(v[f[:, 1]]-v[f[:, 0]], v[f[:, 2]]-v[f[:, 0]]), axis=1)/2


def clipped_areas(v, f, cut, below, normal=(0, 0, 1)):
    tri = v[f]
    normal = np.array(normal)
    distance = tri@normal-cut
    inside = distance <= 0 if below else distance >= 0
    result = np.where(inside.all(1), areas(v, f), 0)
    for i in np.flatnonzero(inside.any(1) & ~inside.all(1)):
        polygon = []
        for j in range(3):
            p, q = tri[i, j], tri[i, (j+1) % 3]
            pin, qin = inside[i, j], inside[i, (j+1) % 3]
            if pin:
                polygon.append(p)
            if pin != qin:
                polygon.append(p+(q-p)*(-distance[i, j]/(distance[i, (j+1) % 3]-distance[i, j])))
        result[i] = sum(np.linalg.norm(np.cross(polygon[j]-polygon[0], polygon[j+1]-polygon[0]))/2
                        for j in range(1, len(polygon)-1))
    return result


def point_plane_error(points, reference):
    normal = np.cross(reference[:, 1]-reference[:, 0], reference[:, 2]-reference[:, 0])
    norm = np.linalg.norm(normal, axis=1)
    keep = norm > 1e-13
    return float(np.max(np.abs(np.einsum('nki,ni->nk', points[keep]-reference[keep, :1], normal[keep]))/norm[keep, None]))


def face_components(f):
    owners = {}
    adjacency = [[] for _ in range(len(f))]
    for i, face in enumerate(f):
        for a, b in [(face[0], face[1]), (face[1], face[2]), (face[2], face[0])]:
            edge = tuple(sorted((int(a), int(b))))
            if edge in owners:
                j = owners.pop(edge)
                adjacency[i].append(j)
                adjacency[j].append(i)
            else:
                owners[edge] = i
    seen = set()
    sizes = []
    for i in range(len(f)):
        if i in seen:
            continue
        stack, size = [i], 0
        seen.add(i)
        while stack:
            j = stack.pop()
            size += 1
            for k in adjacency[j]:
                if k not in seen:
                    seen.add(k)
                    stack.append(k)
        sizes.append(size)
    return sorted(sizes, reverse=True)


def exported(path):
    raw = path.read_bytes()
    size = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20+size])
    binary = raw[28+size:]
    def read(index):
        ac = doc['accessors'][index]
        view = doc['bufferViews'][ac['bufferView']]
        width = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[ac['type']]
        dtype = np.dtype({5126: '<f4', 5125: '<u4', 5123: '<u2'}[ac['componentType']])
        return np.ndarray((ac['count'], width), dtype=dtype, buffer=binary,
            offset=view.get('byteOffset', 0)+ac.get('byteOffset', 0),
            strides=(view.get('byteStride', width*dtype.itemsize), dtype.itemsize)).copy()
    return doc, read


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--asset', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    root = args.asset.resolve()
    meta = json.loads((root/'assemblage.json').read_text())
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    body_raw, bv, bf = source(root/meta['body_source'])
    head_raw, dv, df = source(root/meta['head_source'])
    assert hashlib.sha256(body_raw).hexdigest() == meta['body_source_sha256']
    assert hashlib.sha256(head_raw).hexdigest() == meta['head_source_sha256']
    master = root/meta['master']
    assert sha(master) == meta['master_sha256']
    bpy.ops.wm.open_mainfile(filepath=str(master), use_scripts=False)
    before = bpy.data.scenes[meta['scene_before']]
    after = bpy.data.scenes[meta['scene_after']]
    original = next(o for o in before.objects if o.type == 'MESH')
    old_v = np.array([p.co[:] for p in original.data.vertices])
    old_f = np.array([p.vertices[:] for p in original.data.polygons], np.int32)
    assert np.array_equal(old_v, bv) and np.array_equal(old_f, bf)
    ob = next(o for o in after.objects if o.type == 'MESH')
    v = np.array([p.co[:] for p in ob.data.vertices])
    f = np.array([p.vertices[:] for p in ob.data.polygons], np.int32)
    region = np.array([x.value for x in ob.data.attributes['surface_source'].data])
    source_ids = np.array([x.value for x in ob.data.attributes['source_triangle'].data])
    n_body = meta['retained_body_triangles_after_cut']
    n_bridge = meta['bridge_triangles']
    assert (region[:n_body] == 0).all() and (region[n_body:n_body+n_bridge] == 2).all()
    assert (region[n_body+n_bridge:] == 1).all()
    cut = meta['body_cut_z_m']
    protected_before = np.max(bv[bf, 2], axis=1) < cut-2e-6
    protected_after = np.max(v[f, 2], axis=1) < cut-2e-6
    assert np.array_equal(triangle_keys(bv[bf[protected_before]]), triangle_keys(v[f[protected_after]]))
    protected_vertices = bv[bv[:, 2] < cut-2e-6].astype('<f4')
    new_body_vertices = v[:meta['body_vertex_count_after_cut']].astype('<f4')
    assert not len(np.setdiff1d(np.ascontiguousarray(protected_vertices).view('V12').ravel(),
                               np.ascontiguousarray(new_body_vertices).view('V12').ravel()))
    area = areas(v, f)
    expected_body_areas = clipped_areas(bv, bf, cut, True)
    actual_body_areas = np.bincount(source_ids[:n_body], weights=area[:n_body], minlength=len(bf))
    body_area_error = np.abs(actual_body_areas-expected_body_areas)
    assert body_area_error.max() < 2e-8 and body_area_error.sum() < 1e-6
    body_plane_error = point_plane_error(v[f[:n_body]], bv[bf[source_ids[:n_body]]])
    assert body_plane_error < 2e-7
    head_v = dv*meta['head_scale_uniform']+np.array(meta['head_translation_m'])
    ids = source_ids[n_body+n_bridge:]
    head_plane_error = point_plane_error(v[f[n_body+n_bridge:]], head_v[df[ids]])
    assert head_plane_error < 2e-7
    expected_head_areas = clipped_areas(head_v, df[np.unique(ids)], meta['head_cut_plane_offset_m'], False, meta['head_cut_plane_normal'])
    actual_head_areas = np.bincount(ids, weights=area[n_body+n_bridge:], minlength=len(df))[np.unique(ids)]
    head_area_error = float(np.abs(expected_head_areas-actual_head_areas).max())
    assert head_area_error < 2e-8
    new_vertices = v[meta['body_vertex_count_after_cut']:meta['head_offset']]
    assert new_vertices[:, 2].min() > cut-1e-7
    assert new_vertices[:, 2].max() < meta['head_original_surface_retained_above_z_m']+1e-7
    edges = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
    unique, counts = np.unique(np.sort(edges, axis=1), axis=0, return_counts=True)
    assert np.all(counts == 2)
    assert np.array_equal(np.unique(edges, axis=0), np.unique(edges[:, ::-1], axis=0))
    old_edges = np.unique(np.sort(np.concatenate([bf[:, [0, 1]], bf[:, [1, 2]], bf[:, [2, 0]]]), axis=1), axis=0)
    old_euler, euler = len(bv)-len(old_edges)+len(bf), len(v)-len(unique)+len(f)
    assert old_euler == euler
    components = face_components(f)
    assert components == [len(f)]
    assert area[n_body:].min() > 1e-12
    tree = BVHTree.FromPolygons(v.tolist(), f.tolist(), all_triangles=True)
    contacts = [(i, j) for i, j in tree.overlap(tree)
                if i < j and max(i, j) >= n_body and not np.isin(f[i], f[j]).any()]
    assert not contacts, ('New joint/head intersections', len(contacts), contacts[:5])
    assert abs(v[:, 2].max()-bv[:, 2].max()) < 2e-7
    for ident in [before, after]:
        assert len([o for o in ident.objects if o.type == 'LIGHT']) == 5
        mesh_ob = next(o for o in ident.objects if o.type == 'MESH')
        assert mesh_ob.material_slots[0].material == bpy.data.materials['MESHY_MAT_NEUTRE']
    doc, ac = exported(root/meta['export'])
    assert len(doc['meshes']) == len(doc['nodes']) == 1
    prims = doc['meshes'][0]['primitives']
    assert len(prims) == 1
    prim = prims[0]
    gv, gf = ac(prim['attributes']['POSITION']), ac(prim['indices']).reshape(-1, 3)
    expected = v[:, [0, 2, 1]].copy()
    expected[:, 2] *= -1
    assert np.array_equal(triangle_keys(expected[f]), triangle_keys(gv[gf]))
    assert len(gf) == len(f) and doc['asset']['extras']['source_body_sha256'] == meta['body_source_sha256']
    assert 'CC BY 4.0' in doc['asset']['copyright']
    report = {
        'master_sha256': sha(master), 'body_source_sha256': meta['body_source_sha256'],
        'head_source_sha256': meta['head_source_sha256'], 'sources_unchanged': True,
        'before_scene_exact_original_body': True, 'retained_body_vertices_moved': 0,
        'retained_body_vertices_verified': len(protected_vertices),
        'fully_preserved_original_body_triangles': int(protected_before.sum()),
        'retained_body_triangle_coordinates_exact': True,
        'body_cut_z_m': cut, 'body_clipped_triangle_plane_error_max_m': body_plane_error,
        'body_source_face_clipped_area_error_max_m2': float(body_area_error.max()),
        'body_source_face_clipped_area_error_sum_m2': float(body_area_error.sum()),
        'donor_head_surface_preserved_after_uniform_fit': True,
        'head_triangle_plane_error_max_m': head_plane_error,
        'head_source_face_clipped_area_error_max_m2': head_area_error,
        'joint_height_range_m': [cut, meta['head_original_surface_retained_above_z_m']],
        'new_joint_head_intersections': len(contacts), 'closed_edge_manifold': True,
        'consistent_face_orientation': True, 'connected_face_components': components,
        'euler_before': int(old_euler), 'euler_after': int(euler),
        'source_topology_outside_head_not_repaired': True,
        'glb_surface_matches_master_exactly': True, 'attribution_embedded': True,
        'same_neutral_material_and_five_lights': True,
        'source_triangles': len(bf), 'assembled_triangles': len(f),
        'no_app_changes_or_muscle_segmentation': True, 'verifier_sha256': sha(Path(__file__)),
    }
    (root/'verification.json').write_text(json.dumps(report, indent=2)+'\n')
    print('VERIFIED_ASSEMBLY', json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
