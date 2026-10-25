"""Fit contact margins under the exact source and transfer its shading normals."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def sample(array, points, origin, step):
    coords = np.clip((points-origin)/step, 0, np.array(array.shape)-1.000001)
    index = np.floor(coords).astype(int)
    fraction = coords-index
    result = np.zeros(len(points))
    for i in range(2):
        for j in range(2):
            for k in range(2):
                weight = np.prod(np.where([i, j, k], fraction, 1-fraction), axis=1)
                result += weight*array[index[:, 0]+i, index[:, 1]+j, index[:, 2]+k]
    return result


def smooth(t):
    t = np.clip(t, 0, 1)
    return t*t*(3-2*t)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--work', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(sys.argv[sys.argv.index('--')+1:])
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    info = json.loads((a.work/'fields.json').read_text())
    assert sha(a.baseline) == info['baseline_blend_sha256']
    raw = np.load(a.work/'patch.npz')
    v, f = raw['v'].astype(float), raw['f'].astype(np.int32)
    fields, sources = np.load(a.work/'fields.npz'), np.load(a.work/'sources.npz')
    origin, step, radius = fields['origin'], float(fields['step']), float(fields['radius'])
    trees = []
    for key in sources.files:
        if not key.endswith('__f'):
            continue
        verts, faces, normals = sources[key[:-3]+'__v'], sources[key], sources[key[:-3]+'__n']
        tree = BVHTree.FromPolygons(verts.tolist(), faces.tolist(), all_triangles=True)
        volume = np.einsum('ij,ij->i', verts[faces[:, 0]], np.cross(verts[faces[:, 1]], verts[faces[:, 2]])).sum()/6
        trees.append((tree, verts, faces, normals, 1 if volume > 0 else -1))

    def nearest(point):
        best = None
        q = Vector(point)
        for tree, verts, faces, normals, orientation in trees:
            hit, normal, index, distance = tree.find_nearest(q)
            sign = -1 if (q-hit).dot(normal)*orientation < 0 else 1
            value = distance*sign
            if best is None or value < best[0]:
                triangle = verts[faces[index]]
                ab, ac = triangle[1]-triangle[0], triangle[2]-triangle[0]
                rel = np.array(hit)-triangle[0]
                gram = np.array([[ab@ab, ab@ac], [ab@ac, ac@ac]])
                weights = np.linalg.solve(gram, [rel@ab, rel@ac])
                bary = np.array([1-weights.sum(), *weights])
                shade = bary@normals[index]
                shade /= max(np.linalg.norm(shade), 1e-12)
                best = (value, np.array(hit), np.array(normal)*orientation, shade)
        return best

    core_d = sample(fields['core'], v, origin, step)
    body_d = sample(fields['body'], v, origin, step)
    weight = smooth((core_d-(radius-.0020))/.0010)
    # At contact, position and shading converge to the actual neighbour.
    # The last margin is 0.15 mm inside that neighbour, so no exposed rim.
    shade_body, body_points, body_normals = [], [], []
    for q in v:
        _, hit, normal, shade = nearest(q)
        body_points.append(hit)
        body_normals.append(normal)
        shade_body.append(shade)
    body_points, body_normals, shade_body = map(np.array, [body_points, body_normals, shade_body])
    target = body_points-.00015*body_normals

    def signed_body(point):
        q = Vector(point)
        result = np.inf
        for tree, _, _, _, orientation in trees:
            hit, normal, _, distance = tree.find_nearest(q)
            sign = -1 if (q-hit).dot(normal)*orientation < 0 else 1
            result = min(result, distance*sign)
        return result

    # At sharp source edges, a single face normal can leave a point outside
    # the adjacent face. Choose an inward direction verified on the real body.
    for i in np.flatnonzero(weight > .98):
        if signed_body(target[i]) < -.00006:
            continue
        directions = [shade_body[i], body_normals[i]+shade_body[i]]
        candidates = [target[i]]
        for direction in directions:
            direction /= max(np.linalg.norm(direction), 1e-12)
            candidates.extend([body_points[i]-depth*direction for depth in [.00015, .00030]])
        target[i] = min(candidates, key=signed_body)
    v = (1-weight[:, None])*v+weight[:, None]*target
    # Analytic rounded tilted-core normal blended with original smooth normals.
    u, w = v[:, 0]-.002114987923242599, v[:, 2]-.933
    y = v[:, 1]+.023+.45*w
    core_n = np.column_stack([u/.052**2, y/.028**2, .45*y/.028**2+w/.035**2])
    core_n /= np.maximum(np.linalg.norm(core_n, axis=1, keepdims=True), 1e-12)
    body_weight = np.clip(.5+.5*(core_d-body_d)/radius, 0, 1)
    body_weight = np.maximum(body_weight, weight)
    normals = body_weight[:, None]*shade_body+(1-body_weight[:, None])*core_n
    normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-12)
    # The surrounding source already supplies these hidden faces; removing
    # them keeps only useful fillets, with all new perimeter vertices buried.
    f = f[~np.all(weight[f] > .999999, axis=1)]
    used, inverse = np.unique(f, return_inverse=True)
    v, normals, weight, shade_body, f = v[used], normals[used], weight[used], shade_body[used], inverse.reshape(-1, 3)
    cross = np.cross(v[f[:, 1]]-v[f[:, 0]], v[f[:, 2]]-v[f[:, 0]])
    if np.einsum('ij,ij->', cross, normals[f].mean(1)) < 0:
        f = f[:, ::-1]
    # Projection across a sharp contact can fold a few fully buried triangles.
    # Remove only faces whose corners AND interior samples lie in the source;
    # all resulting borders remain hidden and source geometry is untouched.
    test_v = v.astype(np.float32).astype(float)
    test_tree = BVHTree.FromPolygons(test_v.tolist(), f.tolist(), all_triangles=True)
    overlaps = [(i, j) for i, j in test_tree.overlap(test_tree)
                if i < j and not np.isin(f[i], f[j]).any()]
    hidden = {}

    def fully_buried(index):
        if index not in hidden:
            triangle = test_v[f[index]]
            samples = np.vstack([triangle, (triangle+np.roll(triangle, -1, axis=0))/2,
                                 triangle.mean(0)])
            hidden[index] = all(signed_body(q) < -1e-6 for q in samples)
        return hidden[index]

    remove = set()
    unresolved = []
    for i, j in overlaps:
        if i in remove or j in remove:
            continue
        candidates = [k for k in [i, j] if fully_buried(k)]
        if candidates:
            remove.add(candidates[0])
        else:
            unresolved.append((i, j))
    assert not unresolved, ('Visible/non-buried intersection requires correction', len(unresolved))
    f = np.delete(f, sorted(remove), axis=0)
    used, inverse = np.unique(f, return_inverse=True)
    v, normals, weight, shade_body, f = v[used], normals[used], weight[used], shade_body[used], inverse.reshape(-1, 3)
    # Use the same smooth-surface language as the mannequin feet. Source
    # anatomical corner normals are needed only at contact, not on the free
    # neutral patch where nearest internal layers can produce dark marks.
    face_n = np.cross(v[f[:, 1]]-v[f[:, 0]], v[f[:, 2]]-v[f[:, 0]])
    geometric = np.zeros_like(v)
    for corner in range(3):
        np.add.at(geometric, f[:, corner], face_n)
    geometric /= np.maximum(np.linalg.norm(geometric, axis=1, keepdims=True), 1e-12)
    normals = (1-weight[:, None])*geometric+weight[:, None]*shade_body
    normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-12)
    # No new objects, transforms or vertex positions on the 298 retained meshes.
    bpy.ops.wm.open_mainfile(filepath=str(a.baseline.resolve()), use_scripts=False)
    old = bpy.data.scenes[info['source_scene']]
    scene = bpy.data.scenes.new('24_AINE_RACCORDS_FONDUS')
    scene.use_fake_user, scene.world = True, old.world
    for ob in old.objects:
        if ob.get('asset_id') != 'groin.neutral_surface':
            scene.collection.objects.link(ob)
    mesh = bpy.data.meshes.new('AINE_CONTACTS_FONDUS')
    mesh.from_pydata(v.tolist(), [], f.tolist())
    mesh.update()
    for poly in mesh.polygons:
        poly.use_smooth = True
    mesh.normals_split_custom_set([normals[loop.vertex_index] for loop in mesh.loops])
    mesh.materials.append(bpy.data.materials['PASSE3_MAT_NEUTRE'])
    ob = bpy.data.objects.new('FINITION__groin.neutral_surface', mesh)
    scene.collection.objects.link(ob)
    for key in ['asset_id', 'role', 'interactive_muscle_zone', 'anatomical_label_validated']:
        ob[key] = bpy.data.objects['FINITION__groin.neutral_surface'][key]
    ob['source_piece_id'] = 'cf5569b_local_compact_contact_fillet'
    root = a.output.resolve()
    root.mkdir(parents=True, exist_ok=True)
    edges = np.sort(np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]), axis=1)
    unique, counts = np.unique(edges, axis=0, return_counts=True)
    boundary = np.unique(unique[counts == 1])
    np.savez_compressed(root/'surface-fondue.npz', v=v, f=f, normals=normals,
                        boundary_vertices=boundary, contact_weight=weight)
    meta = {
        'baseline_commit': info['baseline_commit'], 'baseline_blend_sha256': sha(a.baseline),
        'baseline_master': '../ecorche-beatriz-finition-aine/ecorche-finition-aine.blend',
        'source_scene': old.name, 'scene': scene.name, 'master': 'ecorche-aine-fondue.blend',
        'added_object': 'groin.neutral_surface', 'replaced_object': 'groin.neutral_surface',
        'retained_original_objects': 298, 'retained_original_vertices_moved': 0,
        'surface_triangles': len(f), 'surface_vertices': len(v),
        'contact_boundary_vertices': len(boundary), 'boundary_inset_m': .00015,
        'fully_buried_triangles_removed': True,
        'fully_buried_intersecting_triangles_removed': len(remove),
        'construction': info,
        'method': 'Compact local implicit union; smooth geometric shading like the reference feet; source shading normals transferred only at buried contact margins; receding rounded core.',
        'topology': 'Open presentation patch; all contact boundaries deliberately inside unchanged neighbour surfaces. Not a welded whole-body skin.',
        'builder_sha256': sha(Path(__file__)),
        'foot_reference': 'Actual unchanged feet of this mannequin; no new reference image file received.',
    }
    bpy.data.texts.new('AINE_FONDUE.json').write(json.dumps(meta, indent=2))
    bpy.context.window.scene = scene
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(root/meta['master']), compress=True)
    meta['master_sha256'] = sha(root/meta['master'])
    (root/'finition.json').write_text(json.dumps(meta, indent=2)+'\n')
    print('BUILT', len(v), len(f), 'boundary', len(boundary), flush=True)


if __name__ == '__main__':
    main()
