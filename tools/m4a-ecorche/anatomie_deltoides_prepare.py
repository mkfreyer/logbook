"""Anatomical proximal fan boundaries on 990201f; only scalar labels change.

The lateral region opens across the acromial dome and tapers toward humeral
insertion. Anterior/posterior regions wrap from clavicular/scapular origins.
Triangle clipping is the unchanged barycentric method from 990201f.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.spatial import cKDTree

# Right-side anatomical coordinate frame (metres, original asset coordinates).
DISTAL = np.array([-.24054453, .08025455, 1.28501197])
JOINT_AXIS_PROXIMAL = np.array([-.180, .074, 1.485])
STATIONS = [0., .25, .50, .72, .90, 1.12]
ANTERIOR_OPENING_DEG = [12., 18., 32., 52., 70., 82.]
POSTERIOR_OPENING_DEG = [12., 16., 28., 44., 60., 75.]
LANDMARKS = {
    'anterior_clavicular_origin': ([-.125, .014, 1.482], 0),
    'lateral_acromial_origin': ([-.210, .060, 1.500], 1),
    'posterior_scapular_origin': ([-.130, .128, 1.465], 2),
    'anterior_superficial_belly': ([-.250, .026, 1.405], 0),
    'lateral_dome_belly': ([-.274, .075, 1.405], 1),
    'posterior_superficial_belly': ([-.252, .128, 1.398], 2),
}


def anatomical_fields(vertices):
    long = JOINT_AXIS_PROXIMAL - DISTAL
    axis_length = np.linalg.norm(long)
    long /= axis_length
    anterior = np.array([0., -1., 0.])
    anterior -= np.dot(anterior, long) * long
    anterior /= np.linalg.norm(anterior)
    lateral = np.cross(anterior, long)
    lateral /= np.linalg.norm(lateral)
    relative = vertices - DISTAL
    t = np.clip(relative @ long / axis_length, STATIONS[0], STATIONS[-1])
    a, l = relative @ anterior, relative @ lateral
    theta_a = np.deg2rad(PchipInterpolator(STATIONS, ANTERIOR_OPENING_DEG)(t))
    theta_p = np.deg2rad(PchipInterpolator(STATIONS, POSTERIOR_OPENING_DEG)(t))
    # Continuous fan sheets, no atan2 branch cut on the deep surface. Minimum
    # score gives a complete disjoint partition even at common convergence.
    scores = np.column_stack([-a / np.tan(theta_a), -l, a / np.tan(theta_p)])
    return scores, {'longitudinal': long.tolist(), 'anterior': anterior.tolist(),
                    'lateral': lateral.tolist(), 'axis_length_m': float(axis_length)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--zones', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    source = np.load(args.source)
    prior = json.loads(args.zones.read_text())
    path = Path(__file__).with_name('frontieres_deltoides_prepare.py')
    spec = importlib.util.spec_from_file_location('surface_clipping', path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    output, summary = {}, {}
    plane = prior['median_plane_x_m']
    for side in ['right', 'left']:
        v, f = source[side + '_v'], source[side + '_f']
        chart_v = v.copy()
        if side == 'left':
            chart_v[:, 0] = 2 * plane - chart_v[:, 0]
        scores, frame = anatomical_fields(chart_v)
        result = helper.subdivide(v, f, scores)
        for key, value in result.items():
            output[side + '_' + key] = value
        output[side + '_anatomical_scores'] = scores
        summary[side] = {'source_vertices': len(v), 'new_vertices': len(result['v']),
                         'source_triangles': len(f), 'new_triangles': len(result['f']),
                         'cut_original_triangles': int((result['source_counts'] > 1).sum()),
                         'triangles_by_region': np.bincount(result['labels']).tolist()}
    tree = cKDTree(source['right_v'])
    landmarks = {}
    scores, frame = anatomical_fields(source['right_v'])
    for name, (location, expected) in LANDMARKS.items():
        distance, index = tree.query(location)
        actual = int(np.argmin(scores[index]))
        assert actual == expected, (name, actual, expected)
        landmarks[name] = {'reference_m': location,
                           'projected_to_source_vertex_m': source['right_v'][index].tolist(),
                           'projection_distance_m': float(distance),
                           'expected_region': expected, 'assigned_region': actual}
    np.savez_compressed(args.output, **output)
    args.output.with_suffix('.json').write_text(json.dumps({
        'method': 'Clavicular/acromial/scapular fan in an anatomical humeral frame; '
                  'continuous proximal opening profiles; unchanged barycentric local triangle clipping.',
        'geometry_smoothing': False, 'coordinate_displacement': False,
        'axis_frame_right': frame, 'distal_convergence_m': DISTAL.tolist(),
        'joint_axis_proximal_m': JOINT_AXIS_PROXIMAL.tolist(),
        'joint_axis_is_internal_reference_not_a_surface_attachment': True,
        'longitudinal_stations': STATIONS,
        'anterior_opening_degrees': ANTERIOR_OPENING_DEG,
        'posterior_opening_degrees': POSTERIOR_OPENING_DEG,
        'landmarks_right': landmarks, 'landmark_status': 'Approximate surface landmarks, visual validation pending.',
        'counts': summary,
        'source_snapshot_sha256': hashlib.sha256(args.source.read_bytes()).hexdigest(),
        'prepare_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'clipping_helper_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
    }, indent=2) + '\n')
    print('ANATOMICAL_PREPARED', json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
