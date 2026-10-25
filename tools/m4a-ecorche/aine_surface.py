"""Build a small closed neutral pubic envelope fitted behind the muscle roots.

This replaces the two exposed central presentation pieces; it does not cover
or deform the anterior surfaces of the abdominal/adductor muscle bellies.
Run with system Python and NumPy. Coordinates are metres, Z up, anterior -Y.
"""
import argparse
import json
from pathlib import Path

import numpy as np


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    plane, zcenter = .002114987923242599, .923
    rx, ry, rz = .052, .035, .0305
    segments, latitudes = 48, 24
    v = []
    for j in range(1, latitudes):
        theta = np.pi*j/latitudes
        z = zcenter + rz*np.cos(theta)
        t = np.clip((.918-z)/.020, 0, 1)
        # Lower centre recedes posteriorly; no projecting genital-shaped mass.
        cy = -.016 + .022*t*t*(3-2*t)
        radius = np.sqrt(max(0, 1-np.cos(theta)**4))
        for k in range(segments):
            phi = 2*np.pi*k/segments
            v.append([plane+rx*radius*np.sin(phi),
                      cy-ry*radius*np.cos(phi), z])
    top, bottom = len(v), len(v)+1
    v.extend([[plane, -.016, zcenter+rz], [plane, .006, zcenter-rz]])
    faces = []
    for j in range(latitudes-2):
        for k in range(segments):
            u, w = j*segments+k, j*segments+(k+1)%segments
            faces.extend([(u, u+segments, w+segments), (u, w+segments, w)])
    for k in range(segments):
        faces.append((top, k, (k+1)%segments))
        u, w = (latitudes-2)*segments+k, (latitudes-2)*segments+(k+1)%segments
        faces.append((bottom, w, u))
    v, f = np.array(v), np.array(faces, dtype=np.int32)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(a.output, v=v, f=f)
    a.output.with_suffix('.json').write_text(json.dumps({
        'method': 'Small closed neutral pubic envelope; fitted behind existing adductor and lower abdominal surfaces, replacing two exposed central pieces.',
        'replaced_original_objects': ['m0_c098__CENTRAL__ATHLETIQUE', 'm1_c084__CENTRAL__ATHLETIQUE'],
        'original_muscle_vertices_edited': 0,
        'center_xz_m': [plane, zcenter], 'radii_xyz_m': [rx, ry, rz],
        'centre_y_m': -.016, 'lower_recession_max_m': .022,
        'vertical_profile_exponent': 4,
        'segments': segments, 'latitude_divisions': latitudes,
        'vertices': len(v), 'triangles': len(f),
        'bbox_min_m': v.min(0).tolist(), 'bbox_max_m': v.max(0).tolist(),
        'anatomical_purpose': 'Neutral presentation only; no claimed anatomical organ or training muscle.',
    }, indent=2)+'\n')


if __name__ == '__main__':
    main()
