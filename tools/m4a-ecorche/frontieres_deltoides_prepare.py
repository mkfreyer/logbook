"""Cut original triangles by continuous material-region fields; no sculpting.

System Python: NumPy/SciPy. Input is an evaluated snapshot of fb68f5e.
All new vertices carry barycentric source-surface provenance.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.sparse import coo_matrix, diags
from scipy.sparse.csgraph import dijkstra
from scipy.sparse.linalg import spsolve


def fields(vertices, faces, paths):
    edges = np.unique(np.sort(np.concatenate([
        faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]]), axis=1), axis=0)
    lengths = np.linalg.norm(vertices[edges[:, 0]] - vertices[edges[:, 1]], axis=1)
    graph = coo_matrix((np.r_[lengths, lengths],
        (np.r_[edges[:, 0], edges[:, 1]], np.r_[edges[:, 1], edges[:, 0]])),
        shape=(len(vertices), len(vertices))).tocsr()
    raw = np.column_stack([dijkstra(graph, indices=np.unique(path), min_only=True) for path in paths])
    # Cotangent FEM heat diffusion of LABEL FIELDS only; coordinates never enter
    # a smoothing operation. Linear interpolation then defines surface curves.
    tri = vertices[faces]
    double_area = np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1)
    rows, cols, weights = [], [], []
    mass = np.zeros(len(vertices))
    for k in range(3):
        a, b = (k + 1) % 3, (k + 2) % 3
        cot = np.einsum('ij,ij->i', tri[:, a] - tri[:, k], tri[:, b] - tri[:, k]) / double_area / 2
        rows.extend([faces[:, a], faces[:, b]])
        cols.extend([faces[:, b], faces[:, a]])
        weights.extend([cot, cot])
        np.add.at(mass, faces[:, k], double_area / 6)
    adjacency = coo_matrix((np.concatenate(weights), (np.concatenate(rows), np.concatenate(cols))),
                           shape=graph.shape).tocsr()
    laplacian = diags(np.asarray(adjacency.sum(axis=1)).ravel()) - adjacency
    smooth = spsolve(diags(mass) + .006**2 * laplacian, mass[:, None] * raw)
    return raw, smooth


def clip(poly, values):
    """Half-space clip in original triangle barycentric coordinates."""
    result = []
    for a, b in zip(poly, poly[1:] + poly[:1]):
        da, db = float(a @ values), float(b @ values)
        ina, inb = da >= 0, db >= 0
        if ina:
            result.append(a)
        if ina != inb:
            result.append(a + (b - a) * (da / (da - db)))
    cleaned = []
    for p in result:
        p[np.abs(p) < 1e-13] = 0
        p /= p.sum()
        if not cleaned or np.linalg.norm(p - cleaned[-1]) > 1e-11:
            cleaned.append(p)
    if len(cleaned) > 1 and np.linalg.norm(cleaned[0] - cleaned[-1]) < 1e-11:
        cleaned.pop()
    return cleaned


def subdivide(vertices, faces, scores):
    result_v = vertices.tolist()
    vertex_parent = np.full(len(vertices), -1, dtype=int).tolist()
    vertex_bary = np.zeros((len(vertices), 3)).tolist()
    cache = {}
    result_f, labels, parents, corner_bary = [], [], [], []
    source_counts = np.zeros(len(faces), dtype=int)

    def get_vertex(fi, bary):
        active = np.flatnonzero(bary > 1e-11)
        if len(active) == 1:
            index = int(faces[fi, active[0]])
            if vertex_parent[index] == -1:
                vertex_parent[index], vertex_bary[index] = fi, bary.tolist()
            return index
        support = sorted((int(faces[fi, k]), float(bary[k])) for k in active)
        if len(active) == 2:
            # Same mathematical edge intersection from either adjacent triangle.
            key = ('edge', support[0][0], support[1][0], round(support[1][1], 10))
        else:
            key = ('face', fi, tuple(round(float(x), 10) for x in bary))
        if key not in cache:
            cache[key] = len(result_v)
            result_v.append((bary @ vertices[faces[fi]]).tolist())
            vertex_parent.append(fi)
            vertex_bary.append(bary.tolist())
        return cache[key]

    for fi, face in enumerate(faces):
        for region in range(3):
            poly = list(np.eye(3))
            for other in range(3):
                if region != other:
                    poly = clip(poly, scores[face, other] - scores[face, region])
                    if len(poly) < 3:
                        break
            if len(poly) < 3:
                continue
            ids = [get_vertex(fi, p) for p in poly]
            for k in range(1, len(poly) - 1):
                ids3 = [ids[0], ids[k], ids[k + 1]]
                bary3 = np.array([poly[0], poly[k], poly[k + 1]])
                area_ratio = abs(np.linalg.det(bary3))
                if area_ratio < 1e-13:
                    continue
                assert len(set(ids3)) == 3
                result_f.append(ids3)
                labels.append(region)
                parents.append(fi)
                corner_bary.append(bary3)
                source_counts[fi] += 1
    assert (source_counts > 0).all()
    assert (np.array(vertex_parent) >= 0).all()
    return {'v': np.array(result_v), 'f': np.array(result_f, dtype=np.int32),
            'labels': np.array(labels, dtype=np.int32),
            'parent': np.array(parents, dtype=np.int32), 'bary': np.array(corner_bary),
            'vertex_parent': np.array(vertex_parent, dtype=np.int32),
            'vertex_bary': np.array(vertex_bary), 'source_counts': source_counts}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--zones', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = np.load(args.source)
    meta = json.loads(args.zones.read_text())
    raw, smooth = fields(source['right_v'], source['right_f'], meta['source_path_vertex_indices'])
    output = {'raw_scores': raw, 'smooth_scores': smooth}
    summary = {}
    for side in ['right', 'left']:
        result = subdivide(source[side + '_v'], source[side + '_f'], smooth)
        for key, value in result.items():
            output[side + '_' + key] = value
        summary[side] = {'source_vertices': len(source[side + '_v']),
                         'new_vertices': len(result['v']),
                         'source_triangles': len(source[side + '_f']),
                         'new_triangles': len(result['f']),
                         'cut_original_triangles': int((result['source_counts'] > 1).sum()),
                         'triangles_by_region': np.bincount(result['labels']).tolist()}
    np.savez_compressed(args.output, **output)
    args.output.with_suffix('.json').write_text(json.dumps({
        'method': '6 mm FEM heat smoothing of geodesic label fields; exact barycentric half-space triangle clipping.',
        'geometry_smoothing': False, 'field_heat_length_m': .006, 'counts': summary,
        'source_snapshot_sha256': hashlib.sha256(args.source.read_bytes()).hexdigest(),
        'prepare_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }, indent=2) + '\n')
    print('PREPARED', json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
