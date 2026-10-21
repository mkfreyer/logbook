"""Partition approved P4 surfaces by material only. No geometric operations.

Run in Blender 4.3.2, --background --disable-autoexec --python this.py --
  --baseline .../ecorche-p4-p5.blend --output .../ecorche-beatriz-zones-deltoides
"""
import argparse
import hashlib
import heapq
import json
import sys
from pathlib import Path

import bpy
import numpy as np

BASE_SHA = 'f8b6a232a18335221af3cafc62b37837fedc1caaf9bc6cb48e1cb583f222d9ab'
BASE_COMMIT = '0ab3d838c728a88f2d325edff7a6884400c9ed78'
HEADS = ['anterior', 'lateral', 'posterior']
COLORS = [[.72, .035, .025, 1], [.025, .16, .8, 1], [.025, .55, .10, 1]]
# Approximate anatomical landmarks, in original asset coordinates (metres).
# Independent surface-distance partition, NOT argmax of old sculpt weights.
# Each path runs proximal attachment -> superficial belly -> distal convergence.
LANDMARKS = [
    [[-.125, .014, 1.482], [-.250, .026, 1.405], [-.243, .068, 1.312]],
    [[-.210, .060, 1.500], [-.274, .075, 1.405], [-.247, .080, 1.308]],
    [[-.130, .128, 1.465], [-.252, .128, 1.398], [-.240, .093, 1.310]],
]


def distances(graph, seeds, target=None):
    """Dijkstra on original mesh edges, deterministically tie-broken by index."""
    result = np.full(len(graph), np.inf)
    predecessor = np.full(len(graph), -1, dtype=np.int32)
    queue = []
    for seed in seeds:
        result[seed] = 0
        heapq.heappush(queue, (0., int(seed)))
    while queue:
        value, node = heapq.heappop(queue)
        if value != result[node]:
            continue
        if node == target:
            break
        for other, length in graph[node]:
            candidate = value + length
            if candidate < result[other]:
                result[other], predecessor[other] = candidate, node
                heapq.heappush(queue, (candidate, other))
    return result, predecessor


def partition(vertices, faces):
    edges = np.unique(np.sort(np.concatenate(
        [faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]]), axis=1), axis=0)
    graph = [[] for _ in vertices]
    for first, second in edges:
        length = float(np.linalg.norm(vertices[first] - vertices[second]))
        graph[first].append((int(second), length))
        graph[second].append((int(first), length))
    paths, distance_fields, projected = [], [], []
    for landmarks in LANDMARKS:
        anchors = [int(np.argmin(np.linalg.norm(vertices - p, axis=1))) for p in landmarks]
        path = []
        for start, end in zip(anchors[:-1], anchors[1:]):
            _, previous = distances(graph, [start], end)
            segment = [end]
            while segment[-1] != start:
                assert previous[segment[-1]] >= 0
                segment.append(int(previous[segment[-1]]))
            path += segment[::-1]
        seeds = sorted(set(path))
        paths.append(path)
        projected.append(vertices[anchors].tolist())
        distance_fields.append(distances(graph, seeds)[0])
    scores = np.asarray(distance_fields).T[faces].mean(axis=1)
    labels = np.argmin(scores, axis=1).astype(np.int32)
    assert np.isfinite(scores).all() and set(labels) == {0, 1, 2}
    return labels, paths, projected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    assert hashlib.sha256(args.baseline.read_bytes()).hexdigest() == BASE_SHA
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(args.baseline.resolve()), use_scripts=False)
    scene = bpy.data.scenes['16_COMBINAISON_P4_P5']
    bpy.context.window.scene = scene
    scene.view_layers[0].update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    right = bpy.data.objects['P4P5__deltoid.right']
    evaluated = right.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = np.array([v.co[:] for v in mesh.vertices])
    faces = np.array([f.vertices[:] for f in mesh.polygons], dtype=np.int32)
    labels, paths, projected = partition(vertices, faces)
    evaluated.to_mesh_clear()
    neutral = bpy.data.materials['PASSE3_MAT_NEUTRE']
    regions = []
    for side in ['right', 'left']:
        ob = bpy.data.objects['P4P5__deltoid.' + side]
        # Preserve raw geometry, keys, weights, UVs and custom normals verbatim.
        ob.data = ob.data.copy()
        ob.data.materials.clear()
        ob['selection_regions'] = {str(i): f'deltoid.{side}.{head}'
                                   for i, head in enumerate(HEADS)}
        ob['segmentation_method'] = 'P4 original triangles, disjoint geodesic surface-distance regions'
        ob['anatomical_boundaries_validated'] = False
        for index, head in enumerate(HEADS):
            zone_id = f'deltoid.{side}.{head}'
            mat = neutral.copy()
            mat.name = zone_id
            mat['zone_id'] = zone_id
            mat['control_color_rgba_linear'] = COLORS[index]
            ob.data.materials.append(mat)
            # Original material was object-linked: explicitly replace overrides.
            ob.material_slots[index].link = 'DATA'
            ob.material_slots[index].material = mat
            ids = np.flatnonzero(labels == index)
            regions.append({'id': zone_id, 'object_asset_id': ob['asset_id'],
                            'material_name': mat.name, 'material_slot': index,
                            'control_color_rgba_linear': COLORS[index],
                            'source_polygon_indices': ids.tolist(),
                            'triangles': int(len(ids))})
        ob.data.polygons.foreach_set('material_index', labels)
        ob.data.update()
    for other in list(bpy.data.scenes):
        if other != scene:
            bpy.data.scenes.remove(other)
    scene.name = '20_ZONES_DELTOIDES_P4'
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=False, do_recursive=True)
    scene['reference_commit'] = BASE_COMMIT
    scene['geometry_modified'] = False
    scene['zone_boundaries_status'] = 'Proposed, awaiting visual validation; not medical segmentation'
    scene.camera = bpy.data.objects['P4P5_face']
    bpy.context.preferences.filepaths.save_version = 0
    master = out / 'ecorche-p4-p5-zones.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(master), compress=True)
    meta = {
        'baseline_commit': BASE_COMMIT, 'baseline_blend_sha256': BASE_SHA,
        'source_scene': '16_COMBINAISON_P4_P5', 'scene': scene.name,
        'master': master.name, 'master_sha256': hashlib.sha256(master.read_bytes()).hexdigest(),
        'method': 'Nearest longitudinal landmark path by original-edge geodesic distance; '
                  'mean vertex distances per original triangle; mirrored face correspondence.',
        'coordinate_system': 'Z up, anterior -Y, anatomical right -X',
        'median_plane_x_m': .002114987923242599,
        'topology_changed': False, 'vertices_moved': 0,
        'source_landmarks_right_m': LANDMARKS,
        'landmarks_projected_to_original_vertices_m': projected,
        'source_path_vertex_indices': paths,
        'old_vertex_groups_used_as_labels': False,
        'regions': regions,
        'anatomical_boundaries_validated': False,
        'builder_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (out / 'zones.json').write_text(json.dumps(meta, indent=2) + '\n')
    print('ZONES_BUILT', [(r['id'], r['triangles']) for r in regions], flush=True)


if __name__ == '__main__':
    main()
