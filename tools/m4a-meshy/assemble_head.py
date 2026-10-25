"""Fit the supplied faceless Meshy head onto the unchanged Anatomical Form body.

Only the removed source head and the new head's lower attachment are affected.
No smoothing, scaling or remeshing of the retained body.
"""
import argparse
import hashlib
import json
import math
import os
import sys
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mesh_io import load_glb


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def components(v, f):
    parent = np.arange(len(v))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for a, b in np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]):
        parent[find(int(b))] = find(int(a))
    return np.array([find(i) for i in range(len(v))])


def source(path):
    _, doc, v, f = load_glb(path)
    # glTF Y-up -> Blender Z-up, with no rescaling or recentering.
    v = v[:, [0, 2, 1]].astype(float)
    v[:, 1] *= -1
    return v, f.astype(np.int32), doc


def clip(v, f, z, above, source_ids=None, plane_normal=(0, 0, 1)):
    mesh = bpy.data.meshes.new('TEMP_CUT')
    mesh.from_pydata(v.tolist(), [], f.tolist())
    bm = bmesh.new()
    bm.from_mesh(mesh)
    layer = bm.faces.layers.int.new('SOURCE_FACE')
    for i, face in enumerate(bm.faces):
        face[layer] = i if source_ids is None else int(source_ids[i])
    bmesh.ops.bisect_plane(bm, geom=list(bm.verts)+list(bm.edges)+list(bm.faces),
        dist=1e-7, plane_co=(0, 0, z), plane_no=plane_normal,
        clear_inner=above, clear_outer=not above)
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    bm.verts.index_update()
    vertices = np.array([x.co[:] for x in bm.verts])
    faces = np.array([[x.index for x in p.verts] for p in bm.faces], np.int32)
    ids = np.array([p[layer] for p in bm.faces], np.int32)
    bm.free()
    bpy.data.meshes.remove(mesh)
    return vertices, faces, ids


def compact(v, f):
    used = np.unique(f)
    mapping = np.full(len(v), -1, np.int32)
    mapping[used] = np.arange(len(used))
    return v[used], mapping[f]


def boundary(v, f, center):
    edges = np.sort(np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]), axis=1)
    unique, counts = np.unique(edges, axis=0, return_counts=True)
    assert counts.max() == 2
    border = unique[counts == 1]
    adjacency = {}
    for a, b in border:
        adjacency.setdefault(int(a), []).append(int(b))
        adjacency.setdefault(int(b), []).append(int(a))
    assert all(len(neighbors) == 2 for neighbors in adjacency.values())
    ring = np.array(sorted(adjacency))
    angle = np.arctan2(v[ring, 0]-center[0], -(v[ring, 1]-center[1])) % (2*np.pi)
    order = np.argsort(angle)
    ring, angle = ring[order], angle[order]
    expected = np.sort(np.column_stack([ring, np.roll(ring, -1)]), axis=1)
    # A non-star-shaped border must not silently be reconnected by angle.
    assert set(map(tuple, expected)) == set(map(tuple, border)), 'Attachment border is not a simple star-shaped loop'
    return ring, angle


def smooth(t):
    t = np.clip(t, 0, 1)
    return t*t*(3-2*t)


def cyclic(at, angle, values):
    return np.column_stack([np.interp(at, np.r_[angle-2*np.pi, angle, angle+2*np.pi],
                                       np.tile(values[:, k], 3)) for k in range(values.shape[1])])


def smooth_normals(v, f):
    mesh = bpy.data.meshes.new('TEMP_NORMALS')
    mesh.from_pydata(v.tolist(), [], f.tolist())
    for p in mesh.polygons:
        p.use_smooth = True
    mesh.update()
    n = np.array([x.vector[:] for x in mesh.corner_normals]).reshape(-1, 3, 3)
    bpy.data.meshes.remove(mesh)
    return n


class Sampler:
    def __init__(self, v, f, n):
        self.v, self.f, self.n = v, f, n
        self.tree = BVHTree.FromPolygons(v.tolist(), f.tolist(), all_triangles=True)

    def normal(self, point):
        hit, _, index, _ = self.tree.find_nearest(Vector(point))
        tri = self.v[self.f[index]]
        xy = np.linalg.lstsq(np.column_stack([tri[1]-tri[0], tri[2]-tri[0]]),
                            np.array(hit)-tri[0], rcond=None)[0]
        result = np.array([1-xy.sum(), *xy])@self.n[index]
        return result/max(np.linalg.norm(result), 1e-12)


def slopes(normals):
    result = -normals[:, :2]*normals[:, 2:3]/np.maximum(np.sum(normals[:, :2]**2, axis=1, keepdims=True), .05)
    return result*np.minimum(1, 3/np.maximum(np.linalg.norm(result, axis=1, keepdims=True), 1e-9))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--body', type=Path, required=True)
    p.add_argument('--head-source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(sys.argv[sys.argv.index('--')+1:])
    root = a.output.resolve()
    root.mkdir(parents=True, exist_ok=True)
    assert sha(a.body) == '9fab861a65407e69b9401bec077bf7b40f58d36404e80bad9db6147f24320a14'
    assert sha(a.head_source) == '1879f3f79f419ca0552adf8776cf3b0e6d3a25dcf11b7a98a351eeb71747a35d'
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bv, bf, _ = source(a.body)
    dv, df, _ = source(a.head_source)
    labels = components(dv, df)
    main_id = np.argmax(np.bincount(labels))
    main_mask = labels[df[:, 0]] == main_id
    original_donor_ids = np.flatnonzero(main_mask)
    donor_cut, body_cut, head_base = .510, .695, .7025
    hv, hf, head_ids = clip(dv, df[main_mask], donor_cut, True, original_donor_ids)
    head_labels = components(hv, hf)
    seed = np.argmin(np.linalg.norm(hv-np.array([-.018, .10, .66]), axis=1))
    mask = head_labels[hf[:, 0]] == head_labels[seed]
    hf, head_ids = hf[mask], head_ids[mask]
    hv, hf = compact(hv, hf)
    assert hv[:, 0].min() > -.12 and hv[:, 0].max() < .10
    donor_head_original = hv.copy()
    v, f, body_ids = clip(bv, bf, body_cut, False)
    v, f = compact(v, f)
    old_head = bv[bv[:, 2] > body_cut+.05]
    donor_core = hv[hv[:, 2] > .545]
    body_center = (old_head[:, :2].min(0)+old_head[:, :2].max(0))/2
    donor_center = (donor_core[:, :2].min(0)+donor_core[:, :2].max(0))/2
    scale = float((bv[:, 2].max()-head_base)/(hv[:, 2].max()-.520))
    translation = np.r_[body_center-scale*donor_center, head_base-scale*.520]
    head_unmodified = hv*scale+translation
    # Keep the donor head rigid above a new short attachment surface. Its
    # lowest neck strip contains shoulder flares and must not be folded inward.
    core_slope = .15
    core_offset = scale*(.525-core_slope*.05)+translation[2]-core_slope*translation[1]
    core_normal = (0, -core_slope, 1)
    hv, hf, head_ids = clip(head_unmodified, hf, core_offset, True, head_ids, core_normal)
    hv, hf = compact(hv, hf)
    head_unmodified = hv.copy()
    donor_head_original = (hv-translation)/scale
    attachment_center = np.array([body_center[0], .015])
    body_ring, body_angle = boundary(v, f, attachment_center)
    head_center = (hv[:, :2].min(0)+hv[:, :2].max(0))/2
    head_ring, head_angle = boundary(hv, hf, head_center)
    core_cut = float(hv[head_ring, 2].max())
    body_normals = smooth_normals(bv, bf)
    body_sample = Sampler(bv, bf, body_normals)
    donor_normals = smooth_normals(dv, df)
    donor_sample = Sampler(dv, df, donor_normals)
    body_ring_normals = np.array([body_sample.normal(q) for q in v[body_ring]])
    head_ring_normals = np.array([donor_sample.normal(q) for q in donor_head_original[head_ring]])
    body_slope = slopes(body_ring_normals)
    head_slope = slopes(head_ring_normals)
    theta = np.arctan2(hv[:, 0]-head_center[0], -(hv[:, 1]-head_center[1])) % (2*np.pi)
    # Fair only the new collar's tangents, never body coordinates.
    for _ in range(4):
        body_slope = .5*body_slope+.25*(np.roll(body_slope, 1, axis=0)+np.roll(body_slope, -1, axis=0))
        head_slope = .5*head_slope+.25*(np.roll(head_slope, 1, axis=0)+np.roll(head_slope, -1, axis=0))
    body_slope *= np.minimum(1, 1.5/np.maximum(np.linalg.norm(body_slope, axis=1, keepdims=True), 1e-9))
    head_slope *= np.minimum(1, 1.5/np.maximum(np.linalg.norm(head_slope, axis=1, keepdims=True), 1e-9))
    top_points = cyclic(body_angle, head_angle, hv[head_ring])
    top_xy = top_points[:, :2]
    top_slope = cyclic(body_angle, head_angle, head_slope)
    span = top_points[:, 2]-body_cut
    assert span.min() > .004
    vertices = v.tolist()
    faces = f.tolist()
    n_body_faces, n_body_vertices = len(faces), len(vertices)
    lower = body_ring
    collar_rings = 15
    for step in range(1, collar_rings+1):
        t = step/(collar_rings+1)
        xy = ((2*t**3-3*t*t+1)*v[body_ring, :2]
              +(t**3-2*t*t+t)*span[:, None]*body_slope
              +(-2*t**3+3*t*t)*top_xy
              +(t**3-t*t)*span[:, None]*top_slope)
        q = np.column_stack([xy, body_cut+t*span])
        upper = np.arange(len(vertices), len(vertices)+len(q))
        vertices.extend(q.tolist())
        for i in range(len(lower)):
            j = (i+1) % len(lower)
            faces.extend([[int(lower[i]), int(lower[j]), int(upper[i])],
                          [int(lower[j]), int(upper[j]), int(upper[i])]])
        lower = upper
    head_offset = len(vertices)
    vertices.extend(hv.tolist())
    upper = head_ring+head_offset
    i = j = 0
    while i < len(lower) or j < len(upper):
        na = body_angle[(i+1) % len(lower)]+(2*np.pi if i+1 >= len(lower) else 0) if i < len(lower) else float('inf')
        nb = head_angle[(j+1) % len(upper)]+(2*np.pi if j+1 >= len(upper) else 0) if j < len(upper) else float('inf')
        x, y = int(lower[i % len(lower)]), int(upper[j % len(upper)])
        if na < nb:
            faces.append([x, int(lower[(i+1) % len(lower)]), y])
            i += 1
        else:
            faces.append([x, int(upper[(j+1) % len(upper)]), y])
            j += 1
    n_bridge_faces = len(faces)-n_body_faces
    faces.extend((hf+head_offset).tolist())
    vertices, faces = np.asarray(vertices), np.asarray(faces, np.int32)
    mesh = bpy.data.meshes.new('MESHY_CORPS_ORIGINAL_TETE_DONNEUSE')
    mesh.from_pydata(vertices.tolist(), [], faces.tolist())
    for poly in mesh.polygons:
        poly.use_smooth = True
    mesh.update()
    custom_normals = np.array([n.vector[:] for n in mesh.corner_normals]).reshape(-1, 3, 3)
    sampled_body_normals = np.array([body_sample.normal(q) for q in vertices[:n_body_vertices]])
    custom_normals[:n_body_faces] = sampled_body_normals[faces[:n_body_faces]]
    # Copy body shading and fade only new collar normals into source normals.
    for fi in range(n_body_faces, n_body_faces+n_bridge_faces):
        for k, vi in enumerate(faces[fi]):
            if vi < n_body_vertices:
                custom_normals[fi, k] = sampled_body_normals[vi]
            elif vi >= head_offset:
                custom_normals[fi, k] = donor_sample.normal(donor_head_original[vi-head_offset])
            else:
                phi = body_angle[(vi-n_body_vertices) % len(body_ring)]
                z = vertices[vi, 2]
                index = (vi-n_body_vertices) % len(body_ring)
                top_z = top_points[index, 2]
                fade = min(.01, (top_z-body_cut)/2)
                wb = 1-float(smooth((z-body_cut)/fade))
                wh = 1-float(smooth((top_z-z)/fade))
                bn = cyclic(np.array([phi]), body_angle, body_ring_normals)[0]
                hn = cyclic(np.array([phi]), head_angle, head_ring_normals)[0]
                custom_normals[fi, k] = (1-wb-wh)*custom_normals[fi, k]+wb*bn+wh*hn
    head_normals = np.array([donor_sample.normal(q) for q in donor_head_original])
    custom_normals[n_body_faces+n_bridge_faces:] = head_normals[hf]
    mesh.normals_split_custom_set(custom_normals.reshape(-1, 3).tolist())
    provenance = np.r_[np.zeros(n_body_faces, np.int32), np.full(n_bridge_faces, 2, np.int32), np.ones(len(hf), np.int32)]
    attr = mesh.attributes.new('surface_source', 'INT', 'FACE')
    attr.data.foreach_set('value', provenance)
    attr = mesh.attributes.new('source_triangle', 'INT', 'FACE')
    attr.data.foreach_set('value', np.r_[body_ids, np.full(n_bridge_faces, -1, np.int32), head_ids])
    material = bpy.data.materials.new('MESHY_MAT_NEUTRE')
    material.use_nodes = True
    material.diffuse_color = (.50, .52, .55, 1)
    bsdf = material.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = material.diffuse_color
    bsdf.inputs['Roughness'].default_value = .86
    bsdf.inputs['Metallic'].default_value = 0
    mesh.materials.append(material)
    rig = bpy.data.collections.new('CAMERAS_LUMIERES_COMMUNES')
    before = bpy.context.scene
    before.name = '00_CORPS_ORIGINAL'
    before.collection.children.link(rig)
    after = bpy.data.scenes.new('01_ASSEMBLAGE_CORPS_TETE')
    after.collection.children.link(rig)
    before.use_fake_user = after.use_fake_user = True
    original_mesh = bpy.data.meshes.new('CORPS_SOURCE_INTACT')
    original_mesh.from_pydata(bv.tolist(), [], bf.tolist())
    for poly in original_mesh.polygons:
        poly.use_smooth = True
    original_mesh.materials.append(material)
    original = bpy.data.objects.new('AVANT__Anatomical_Form', original_mesh)
    before.collection.objects.link(original)
    ob = bpy.data.objects.new('ASSEMBLAGE__Anatomical_Form_Rib_Reach', mesh)
    after.collection.objects.link(ob)
    ob['asset_id'] = 'meshy.anatomical_form.with_rib_reach_head'
    ob['source_body_sha256'], ob['source_head_sha256'] = sha(a.body), sha(a.head_source)
    ob['muscle_segmentation_performed'] = False
    ob['role'] = 'Original supplied body; only source head removed, donor head fitted above fixed neck.'
    center = Vector((float((bv[:, 0].min()+bv[:, 0].max())/2), 0, float((bv[:, 2].min()+bv[:, 2].max())/2)))
    def aim(item, target):
        item.rotation_euler = (Vector(target)-item.location).to_track_quat('-Z', 'Y').to_euler()
    for label, x, y, z, power, size in [('Avant', 3, -3, 2.6, 200, 2.2), ('Dos', 2, 3, 3, 180, 2.2)]:
        for side in [-1, 1]:
            data = bpy.data.lights.new(f'NEUTRE_{label}_{side}', 'AREA')
            data.energy, data.shape, data.size = power, 'DISK', size
            light = bpy.data.objects.new(data.name, data)
            rig.objects.link(light)
            light.location = center+Vector((side*x, y, z))
            aim(light, center)
    data = bpy.data.lights.new('NEUTRE_Centre', 'AREA')
    data.energy, data.shape, data.size = 100, 'DISK', 2
    light = bpy.data.objects.new(data.name, data)
    rig.objects.link(light)
    light.location = center+Vector((0, -4, 4))
    aim(light, center)
    world = bpy.data.worlds.new('FOND_NEUTRE')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[0].default_value = (.035, .04, .05, 1)
    world.node_tree.nodes['Background'].inputs[1].default_value = .35
    for scene in [before, after]:
        scene.world = world
    master = root/'meshy-corps-tete-assemble.blend'
    meta = {
        'body_source': os.path.relpath(a.body.resolve(), root),
        'head_source': os.path.relpath(a.head_source.resolve(), root),
        'body_filename_uploaded': 'Meshy_AI_Anatomical_Form_1025014819_generate.glb',
        'head_filename_uploaded': 'Meshy_AI_Rib_Reach_Exercise_In_1025014903_generate.glb',
        'body_source_sha256': sha(a.body), 'head_source_sha256': sha(a.head_source),
        'original_body_triangles': len(bf), 'original_donor_triangles': len(df),
        'donor_extracted_head_triangles': len(hf), 'retained_body_triangles_after_cut': n_body_faces,
        'bridge_triangles': n_bridge_faces, 'assembled_triangles': len(faces),
        'body_cut_z_m': body_cut, 'donor_cut_z_m': donor_cut, 'head_attachment_z_m': head_base,
        'head_scale_uniform': scale, 'head_translation_m': translation.tolist(),
        'head_rotation_degrees': [0, 0, 0], 'head_local_attachment_height_m': core_cut-body_cut,
        'head_original_surface_retained_above_z_m': core_cut, 'new_attachment_profile_rings': collar_rings,
        'head_cut_plane_normal': list(core_normal), 'head_cut_plane_offset_m': float(core_offset),
        'body_boundary_vertices': len(body_ring), 'head_boundary_vertices': len(head_ring),
        'body_vertex_count_after_cut': n_body_vertices, 'head_offset': head_offset,
        'retained_body_vertices_moved': 0, 'head_core_unchanged_above_z_m': core_cut,
        'scene_before': before.name, 'scene_after': after.name, 'master': master.name,
        'export': 'meshy-corps-tete-assemble.glb',
        'builder_sha256': sha(Path(__file__)),
    }
    bpy.data.texts.new('ASSEMBLAGE.json').write(json.dumps(meta, indent=2))
    bpy.data.texts.new('ATTRIBUTION.txt').write('Model created with Meshy – CC BY 4.0 License. Logbook adaptation: donor head extracted, uniformly fitted and connected to the preserved source body. No new generation or muscle segmentation.')
    bpy.context.window.scene = after
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(master), compress=True)
    meta['master_sha256'] = sha(master)
    (root/'assemblage.json').write_text(json.dumps(meta, indent=2)+'\n')
    np.savez_compressed(root/'assembly-provenance.npz', head_original=donor_head_original,
                        head_rigid=head_unmodified, head_fitted=hv, head_faces=hf,
                        body_clipped=v, body_faces=f, body_source_faces=body_ids,
                        head_source_faces=head_ids)
    print('ASSEMBLED', json.dumps(meta), flush=True)


if __name__ == '__main__':
    main()
