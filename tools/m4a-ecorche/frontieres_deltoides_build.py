"""Snapshot fb68f5e or build its barycentrically subdivided deltoid surfaces."""
import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

import bpy
import numpy as np

BASE_SHA = '2a60e801d8ba76b473f552b993dc73d4cf1778e8230b97e50a6df25470d0d4a8'
BASE_COMMIT = 'fb68f5ee9ab3b47f3ae046cd7a1ce11129a98857'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--snapshot', type=Path)
    parser.add_argument('--prepared', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    assert hashlib.sha256(args.baseline.read_bytes()).hexdigest() == BASE_SHA
    prior = json.loads((args.baseline.parent / 'zones.json').read_text())
    bpy.ops.wm.open_mainfile(filepath=str(args.baseline.resolve()), use_scripts=False)
    scene = bpy.data.scenes[prior['scene']]
    bpy.context.window.scene = scene
    scene.view_layers[0].update()
    graph = bpy.context.evaluated_depsgraph_get()
    snapshot = {}
    evaluated = {}
    for side in ['right', 'left']:
        ob = bpy.data.objects['P4P5__deltoid.' + side]
        mesh = bpy.data.meshes.new_from_object(ob.evaluated_get(graph),
                     preserve_all_data_layers=True, depsgraph=graph)
        evaluated[side] = mesh
        snapshot[side + '_v'] = np.array([v.co[:] for v in mesh.vertices])
        snapshot[side + '_f'] = np.array([p.vertices[:] for p in mesh.polygons], dtype=np.int32)
        snapshot[side + '_n'] = np.array([n.vector[:] for n in mesh.corner_normals]).reshape(-1, 3, 3)
    if args.snapshot:
        np.savez(args.snapshot, **snapshot)
        print('SNAPSHOT', args.snapshot, flush=True)
        return
    assert args.prepared and args.output
    prepared = np.load(args.prepared)
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    regions = []
    for side in ['right', 'left']:
        ob = bpy.data.objects['P4P5__deltoid.' + side]
        old, old_raw = evaluated[side], ob.data
        materials = [s.material for s in ob.material_slots]
        v, f, labels = [prepared[side + '_' + k] for k in ['v', 'f', 'labels']]
        parent, bary = prepared[side + '_parent'], prepared[side + '_bary']
        vp, vb = prepared[side + '_vertex_parent'], prepared[side + '_vertex_bary']
        original_faces = snapshot[side + '_f']
        assert np.array_equal(v[:len(old.vertices)], snapshot[side + '_v'])
        mesh = bpy.data.meshes.new('P4_TRIANGLES_DECOUPES_' + side)
        mesh.from_pydata(v.tolist(), [], f.tolist())
        mesh.update()
        for material in materials:
            mesh.materials.append(material)
        mesh.polygons.foreach_set('material_index', labels)
        mesh.polygons.foreach_set('use_smooth', np.ones(len(f), dtype=bool))
        # Custom loop normals: same source-corner field on both sides of every
        # new material boundary. No global normal recalculation or smoothing.
        normals = np.einsum('tij,tjk->tik', bary, snapshot[side + '_n'][parent])
        normals /= np.linalg.norm(normals, axis=2, keepdims=True)
        mesh.normals_split_custom_set(normals.reshape(-1, 3).tolist())
        for uv in old.uv_layers:
            original = np.array([p.uv[:] for p in uv.data]).reshape(-1, 3, 2)
            new = mesh.uv_layers.new(name=uv.name)
            new.data.foreach_set('uv', np.einsum('tij,tjk->tik', bary, original[parent]).astype(np.float32).ravel())
        for attr in old.color_attributes:
            dest = mesh.color_attributes.new(name=attr.name, domain=attr.domain, type=attr.data_type)
            original = np.array([p.color[:] for p in attr.data])
            if attr.domain == 'POINT':
                colors = np.einsum('vi,vij->vj', vb, original[original_faces[vp]])
                colors[:len(old.vertices)] = original
            else:
                colors = np.einsum('tij,tjk->tik', bary, original.reshape(-1, 3, 4)[parent]).reshape(-1, 4)
            dest.data.foreach_set('color', colors.astype(np.float32).ravel())
        source_attr = mesh.attributes.new('p4_source_triangle', 'INT', 'FACE')
        source_attr.data.foreach_set('value', parent)
        # Keep old authoring group weights, interpolated only at added vertices.
        group_names = [g.name for g in ob.vertex_groups]
        weights = np.zeros((len(old_raw.vertices), len(group_names)))
        for p in old_raw.vertices:
            for group in p.groups:
                weights[p.index, group.group] = group.weight
        new_weights = np.einsum('vi,vij->vj', vb, weights[original_faces[vp]])
        new_weights[:len(old_raw.vertices)] = weights
        ob.data = mesh
        ob.vertex_groups.clear()
        for gi, name in enumerate(group_names):
            group = ob.vertex_groups.new(name=name)
            for vi in np.flatnonzero(new_weights[:, gi] > 0):
                group.add([int(vi)], float(new_weights[vi, gi]), 'REPLACE')
        for index, material in enumerate(materials):
            ob.material_slots[index].link = 'DATA'
            ob.material_slots[index].material = material
        ob['segmentation_method'] = 'Continuous surface label fields; barycentric local triangle clipping'
        ob['original_surface_preserved'] = True
        ob['shape_keys_baked_at_approved_P4_pose'] = True
        for index, head in enumerate(['anterior', 'lateral', 'posterior']):
            old_rec = next(r for r in prior['regions'] if r['id'] == f'deltoid.{side}.{head}')
            rec = {k: value for k, value in old_rec.items() if k not in ['source_polygon_indices', 'triangles']}
            rec['source_polygon_indices'] = np.flatnonzero(labels == index).tolist()
            rec['triangles'] = int((labels == index).sum())
            regions.append(rec)
    scene.name = '21_FRONTIERES_DELTOIDES_P4'
    scene['geometry_modified'] = False  # Piecewise-linear surface conserved.
    scene['local_topology_modified'] = True
    scene['reference_commit'] = BASE_COMMIT
    scene['zone_boundaries_status'] = 'Continuous boundaries proposed for visual validation'
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=False, do_recursive=True)
    bpy.context.preferences.filepaths.save_version = 0
    master = out / 'ecorche-p4-p5-zones.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(master), compress=True)
    shutil.copyfile(args.prepared, out / 'provenance-surface.npz')
    preparation = json.loads(args.prepared.with_suffix('.json').read_text())
    meta = {
        'baseline_commit': BASE_COMMIT, 'geometry_reference_commit': prior['baseline_commit'],
        'baseline_blend_sha256': BASE_SHA, 'source_scene': prior['scene'], 'scene': scene.name,
        'master': master.name, 'master_sha256': hashlib.sha256(master.read_bytes()).hexdigest(),
        'method': preparation['method'], 'topology_changed': True, 'original_vertices_moved': 0,
        'shape_keys': 'P4 deltoid shape keys baked at approved evaluated pose; other objects unchanged.',
        'normal_method': 'Normalized barycentric interpolation of original evaluated corner normals.',
        'regions': regions, 'preparation': preparation,
        'median_plane_x_m': prior['median_plane_x_m'],
        'anatomical_boundaries_validated': False,
        'builder_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (out / 'zones.json').write_text(json.dumps(meta, indent=2) + '\n')
    print('BUILT', meta['master_sha256'], flush=True)


if __name__ == '__main__':
    main()
