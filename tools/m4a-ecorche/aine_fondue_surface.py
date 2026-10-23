"""Extract only the core/fillet contact patch from the local implicit union.

System Python: NumPy, SciPy and scikit-image (scratch tools, no app dependency).
"""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.ndimage import map_coordinates
from skimage.measure import marching_cubes


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--work', type=Path, required=True)
    a = p.parse_args()
    s = np.load(a.work/'fields.npz')
    h, radius = float(s['step']), float(s['radius'])
    v, f, _, _ = marching_cubes(s['field'], level=0, spacing=(h, h, h),
                               allow_degenerate=False, gradient_direction='ascent')
    v += s['origin']
    q = (v-s['origin']).T/h
    distance = map_coordinates(s['core'], q, order=1, mode='nearest')
    # Surface outside the fillet is the source itself, and must not be duplicated.
    limit = radius-.0006
    scalar = distance-limit
    vertices = v.tolist()
    cache, faces = {}, []

    def crossing(i, j):
        key = tuple(sorted((i, j)))
        if key not in cache:
            t = scalar[i]/(scalar[i]-scalar[j])
            cache[key] = len(vertices)
            vertices.append((v[i]+t*(v[j]-v[i])).tolist())
        return cache[key]

    for tri in f:
        poly = []
        for i, j in zip(tri, np.roll(tri, -1)):
            i, j = int(i), int(j)
            if scalar[i] <= 0:
                poly.append(i)
            if (scalar[i] < 0) != (scalar[j] < 0):
                poly.append(crossing(i, j))
        if len(poly) >= 3:
            for j in range(1, len(poly)-1):
                faces.append((poly[0], poly[j], poly[j+1]))
    f = np.array(faces, np.int32)
    used, inverse = np.unique(f, return_inverse=True)
    v, f = np.array(vertices)[used], inverse.reshape(-1, 3)
    np.savez_compressed(a.work/'patch.npz', v=v, f=f)
    print('PATCH', len(v), len(f), flush=True)


if __name__ == '__main__':
    main()
