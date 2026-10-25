"""Rebuild only the head as an oval featureless surface above a fixed throat."""
import argparse
import hashlib
import json
import math
import os
import sys
from pathlib import Path

import bpy
import numpy as np


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def smooth(t):
    t = np.clip(t, 0, 1)
    return t*t*(3-2*t)


def hermite(x, y, at, last_slope):
    """Shape-preserving cubic profile, with analytic crown tangent."""
    h = np.diff(x)
    d = np.diff(y)/h
    slopes = np.zeros(len(x))
    slopes[0], slopes[-1] = d[0], last_slope
    for i in range(1, len(x)-1):
        if d[i-1]*d[i] > 0:
            a, b = 2*h[i]+h[i-1], h[i]+2*h[i-1]
            slopes[i] = (a+b)/(a/d[i-1]+b/d[i])
    i = min(len(x)-2, max(0, np.searchsorted(x, at)-1))
    t = (at-x[i])/h[i]
    return ((2*t**3-3*t*t+1)*y[i]+(t**3-2*t*t+t)*h[i]*slopes[i]
            +(-2*t**3+3*t*t)*y[i+1]+(t**3-t*t)*h[i]*slopes[i+1])


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(sys.argv[sys.argv.index('--')+1:])
    root = a.output.resolve()
    root.mkdir(parents=True, exist_ok=True)
    baseline = a.baseline.resolve()
    prior = json.loads((baseline.parent/'finition.json').read_text())
    assert sha(baseline) == prior['master_sha256']
    bpy.ops.wm.open_mainfile(filepath=str(baseline), use_scripts=False)
    old = bpy.data.scenes[prior['scene']]
    bpy.context.window.scene = old
    old.view_layers[0].update()
    graph = bpy.context.evaluated_depsgraph_get()
    key = 'head_throat.neutral_surface'
    original = next(o for o in old.objects if o.get('asset_id') == key)
    ev = original.evaluated_get(graph)
    mesh = ev.to_mesh()
    v = np.array([original.matrix_world@x.co for x in mesh.vertices])
    f = np.array([p.vertices[:] for p in mesh.polygons], np.int32)
    normals = np.array([n.vector[:] for n in mesh.corner_normals]).reshape(-1, 3, 3)
    # P4 throat ends here. The former P5 submental bridge above this level
    # belongs to the replaced head connection, not to the protected throat.
    cut = 1.5700000524520874
    keep = np.max(v[f, 2], axis=1) <= cut+1e-8
    kept = f[keep]
    used = np.unique(kept)
    remap = np.full(len(v), -1, np.int32)
    remap[used] = np.arange(len(used))
    vertices = v[used].tolist()
    faces = remap[kept].tolist()
    n_kept = len(faces)
    edges = np.sort(np.concatenate([kept[:, [0, 1]], kept[:, [1, 2]], kept[:, [2, 0]]]), axis=1)
    unique, counts = np.unique(edges, axis=0, return_counts=True)
    border = unique[counts == 1]
    ring = np.unique(border)
    assert np.max(np.abs(v[ring, 2]-cut)) < 1e-7
    plane = prior['median_plane_x_m']
    angle = np.arctan2(v[ring, 0]-plane, -(v[ring, 1]-.04)) % (2*np.pi)
    order = np.argsort(angle)
    ring, angle = ring[order], angle[order]
    assert len(ring) == len(border) == 259
    # Boundary tangents come from the existing smooth cervical normals.
    normal = np.zeros_like(v)
    n_count = np.zeros(len(v))
    for j in range(3):
        np.add.at(normal, kept[:, j], normals[keep, j])
        np.add.at(n_count, kept[:, j], 1)
    normal[ring] /= n_count[ring, None]
    slope = -normal[ring, :2]*normal[ring, 2:3]/np.maximum(
        np.sum(normal[ring, :2]**2, axis=1, keepdims=True), .05)
    slope *= np.minimum(1, 3/np.maximum(np.linalg.norm(slope, axis=1, keepdims=True), 1e-9))
    target_angle = np.arange(128)*2*np.pi/128

    def cyclic(values):
        return np.column_stack([np.interp(target_angle,
            np.r_[angle-2*np.pi, angle, angle+2*np.pi], np.tile(values[:, k], 3))
            for k in range(values.shape[1])])

    base = cyclic(v[ring, :2])
    tangent = cyclic(slope)
    z_profile = np.array([1.570, 1.59, 1.61, 1.635, 1.66, 1.69, 1.72])
    radii = np.array([.052, .0545, .0565, .070, .073, .074, .0735])
    front = np.array([-.036, -.053, -.063, -.066, -.065, -.063, -.060])
    back = np.array([.085, .093, .103, .112, .120, .125, .121])
    crown_center, crown_height = 1.715, .085
    s0 = math.sqrt(1-((1.72-crown_center)/crown_height)**2)
    crown_slope = -(1.72-crown_center)/(crown_height*crown_height*s0)
    yslope = .0035/.08
    heights = np.r_[[1.5715, 1.573, 1.575, 1.578, 1.581, 1.585, 1.590, 1.595, 1.600],
                    1.6+.2*np.sin(np.linspace(0, np.pi/2, 65)[1:-1])]
    rings = []
    for z in heights:
        if z <= 1.72:
            rx = hermite(z_profile, radii, z, .0735/s0*crown_slope)
            yf = hermite(z_profile, front, z, yslope-.0905/s0*crown_slope)
            yb = hermite(z_profile, back, z, yslope+.0905/s0*crown_slope)
        else:
            s = math.sqrt(max(0, 1-((z-crown_center)/crown_height)**2))
            rx = .0735/s0*s
            cy = .0305+yslope*(z-1.72)
            yf, yb = cy-.0905/s0*s, cy+.0905/s0*s
        ideal = np.column_stack([plane+rx*np.sin(target_angle),
                                 (yf+yb)/2-(yb-yf)/2*np.cos(target_angle)])
        w = float(smooth((z-cut)/.025))
        xy = (1-w)*(base+(z-cut)*tangent)+w*ideal
        start = len(vertices)
        vertices.extend(np.column_stack([xy, np.full(128, z)]).tolist())
        rings.append(np.arange(start, start+128))
    # Zipper the exact original edge to the first new ring without splitting or
    # moving any original throat triangle. All later rings are regular quads.
    lower = remap[ring]
    upper = rings[0]
    i = j = 0
    while i < len(lower) or j < len(upper):
        na = angle[(i+1) % len(lower)]+(2*np.pi if i+1 >= len(lower) else 0) if i < len(lower) else float('inf')
        nb = target_angle[(j+1) % len(upper)]+(2*np.pi if j+1 >= len(upper) else 0) if j < len(upper) else float('inf')
        x, y = int(lower[i % len(lower)]), int(upper[j % len(upper)])
        if na < nb:
            faces.append([x, int(lower[(i+1) % len(lower)]), y])
            i += 1
        else:
            faces.append([x, int(upper[(j+1) % len(upper)]), y])
            j += 1
    for lower, upper in zip(rings[:-1], rings[1:]):
        for j in range(128):
            k = (j+1) % 128
            faces.extend([[int(lower[j]), int(lower[k]), int(upper[j])],
                          [int(lower[k]), int(upper[k]), int(upper[j])]])
    cap = len(vertices)
    vertices.append([plane, .034, 1.8])
    for j in range(128):
        faces.append([int(rings[-1][j]), int(rings[-1][(j+1) % 128]), cap])
    new_mesh = bpy.data.meshes.new('TETE_NEUTRE_SURFACE_CONTINUE')
    new_mesh.from_pydata(vertices, [], faces)
    new_mesh.update()
    for p in new_mesh.polygons:
        p.use_smooth = True
    # Original throat loop normals are copied exactly. At its upper edge the
    # new surface receives the same interpolated normal, fading into its own
    # smooth geometric normals over 5 mm. No facial feature normal map.
    nn = np.array([x.vector[:] for x in new_mesh.corner_normals]).reshape(-1, 3, 3)
    nn[:n_kept] = normals[keep]
    vv = np.asarray(vertices)
    ff = np.asarray(faces)
    bnorm = normal[ring]
    for fi in range(n_kept, len(faces)):
        for j, vi in enumerate(faces[fi]):
            z = vv[vi, 2]
            w = 1-float(smooth((z-cut)/.005))
            if w <= 0:
                continue
            theta = math.atan2(vv[vi, 0]-plane, -(vv[vi, 1]-.04)) % (2*np.pi)
            target = np.array([np.interp(theta, np.r_[angle-2*np.pi, angle, angle+2*np.pi],
                                        np.tile(bnorm[:, k], 3)) for k in range(3)])
            nn[fi, j] = (1-w)*nn[fi, j]+w*target
    new_mesh.normals_split_custom_set(nn.reshape(-1, 3).tolist())
    # Material object slots are authoritative in the source asset.
    for slot in original.material_slots:
        new_mesh.materials.append(slot.material)
    ob = bpy.data.objects.new('TETE_NEUTRE__'+key, new_mesh)
    for name in original.keys():
        ob[name] = original[name]
    ob['role'] = 'Continuous smooth featureless fitness head above an exactly preserved cervical surface.'
    ob['interactive_muscle_zone'] = False
    scene = bpy.data.scenes.new('28_TETE_NEUTRE')
    scene.use_fake_user = True
    scene.world, scene.camera = old.world, old.camera
    removed = ['head.eye.l', 'head.eye.r']
    for item in old.objects:
        if item.get('asset_id') not in [key, *removed]:
            scene.collection.objects.link(item)
    scene.collection.objects.link(ob)
    bpy.context.window.scene = scene
    meta = {
        'baseline_commit': 'd83fc44c3d26fd8a5685e359fcefefc4dd0b941e',
        'baseline_master': os.path.relpath(baseline, root),
        'baseline_glb': os.path.relpath(baseline.parent/prior['export_file'], root),
        'baseline_blend_sha256': sha(baseline), 'source_scene': old.name,
        'scene': scene.name, 'master': 'ecorche-tete-neutre.blend',
        'export_file': 'ecorche-tete-neutre.glb',
        'changed_objects': [key], 'removed_objects': removed,
        'retained_other_objects': 296, 'median_plane_x_m': plane,
        'neck_protected_through_z_m': cut, 'retained_neck_triangles': n_kept,
        'original_head_throat_triangles': len(f), 'head_throat_triangles': len(faces),
        'new_head_triangles': len(faces)-n_kept, 'new_head_angular_samples': 128,
        'new_head_profile_rings': len(rings), 'cranial_top_z_m': 1.8,
        'profile_controls': {'z_m': z_profile.tolist(), 'half_width_m': radii.tolist(),
                             'front_y_m': front.tolist(), 'back_y_m': back.tolist()},
        'method': 'New oval ring surface with analytic rounded crown and a shared cervical boundary. Existing throat faces and positions retained; eyeballs removed.',
        'builder_sha256': sha(Path(__file__)),
    }
    bpy.data.texts.new('TETE_NEUTRE.json').write(json.dumps(meta, indent=2))
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(root/meta['master']), compress=True)
    meta['master_sha256'] = sha(root/meta['master'])
    (root/'tete.json').write_text(json.dumps(meta, indent=2)+'\n')
    print('HEAD_SAVED', json.dumps(meta), flush=True)


if __name__ == '__main__':
    main()
