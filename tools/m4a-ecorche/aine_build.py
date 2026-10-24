"""Extract the approved local reference or add one presentation mesh on a copy."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
import bmesh
import numpy as np


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--extract', type=Path)
    p.add_argument('--surface', type=Path)
    p.add_argument('--output', type=Path)
    a = p.parse_args(sys.argv[sys.argv.index('--')+1:])
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    assert sha(a.baseline) == 'e2c39435afb038306580e6df4ef889ba0a292188cdb255de9143b4b5ffefb528'
    bpy.ops.wm.open_mainfile(filepath=str(a.baseline.resolve()), use_scripts=False)
    source = bpy.data.scenes['22_ANATOMIE_DELTOIDES_P4']
    bpy.context.window.scene = source
    if a.extract:
        graph = bpy.context.evaluated_depsgraph_get()
        arrays, rows = {}, []
        for ob in source.objects:
            if ob.type != 'MESH':
                continue
            ev = ob.evaluated_get(graph)
            mesh = ev.to_mesh()
            v = np.array([ob.matrix_world@q.co for q in mesh.vertices])
            f = np.array([q.vertices[:] for q in mesh.polygons], np.int32)
            normals = np.array([n.vector[:] for n in mesh.corner_normals]).reshape(-1, 3, 3)
            ev.to_mesh_clear()
            lo, hi = v.min(0), v.max(0)
            if lo[2] < 1.04 and hi[2] > .75 and lo[0] < .16 and hi[0] > -.16:
                key = ob['asset_id']
                arrays[key+'__v'], arrays[key+'__f'] = v, f
                arrays[key+'__n'] = normals
                rows.append({'id': key, 'min': lo.tolist(), 'max': hi.tolist()})
        a.extract.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(a.extract/'parts.npz', **arrays)
        (a.extract/'parts.json').write_text(json.dumps(rows, indent=2)+'\n')
        return
    assert a.surface and a.output
    root = a.output.resolve()
    root.mkdir(parents=True, exist_ok=True)
    surface_meta = json.loads(a.surface.with_suffix('.json').read_text())
    retired = surface_meta['replaced_original_objects']
    scene = bpy.data.scenes.new('23_FINITION_AINE_LOCALISEE')
    scene.world = source.world
    for original in source.objects:
        if original.get('asset_id') not in retired:
            scene.collection.objects.link(original)
    scene.use_fake_user = True
    bpy.context.window.scene = scene
    data = np.load(a.surface)
    mesh = bpy.data.meshes.new('AINE_SURFACE_PRESENTATION_NEUTRE')
    mesh.from_pydata(data['v'].tolist(), [], data['f'].tolist())
    mesh.update()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    for poly in mesh.polygons:
        poly.use_smooth = True
    mesh.materials.append(bpy.data.materials['PASSE3_MAT_NEUTRE'])
    ob = bpy.data.objects.new('FINITION__groin.neutral_surface', mesh)
    # Direct scene link keeps the inherited source collection completely intact.
    scene.collection.objects.link(ob)
    ob['asset_id'] = 'groin.neutral_surface'
    ob['role'] = 'Local neutral presentation envelope, not a training muscle or anatomical reconstruction.'
    ob['interactive_muscle_zone'] = False
    ob['anatomical_label_validated'] = False
    ob['source_piece_id'] = 'd79692f_source_guided_local_presentation'
    bpy.context.preferences.filepaths.save_version = 0
    meta = {
        'baseline_commit': 'd79692f380e39312939290ab0d3e038e448aa9b2',
        'baseline_blend_sha256': sha(a.baseline),
        'baseline_master': '../ecorche-beatriz-anatomie-deltoides/ecorche-p4-p5-zones.blend',
        'source_scene': source.name, 'scene': scene.name,
        'master': 'ecorche-finition-aine.blend',
        'added_object': ob['asset_id'], 'original_mesh_objects': 300,
        'original_mesh_objects_edited': 0,
        'replaced_central_objects': retired,
        'original_objects_preserved_in_proposal': 298,
        'objects_after': sum(o.type == 'MESH' for o in scene.objects),
        'added_triangles': len(mesh.polygons),
        'surface_method': json.loads(a.surface.with_suffix('.json').read_text()),
        'surface_npz_sha256': sha(a.surface),
        'builder_sha256': sha(Path(__file__)),
        'reference_image': 'No new image attachment was available; scope follows the written anatomical region.',
        'limitations': ['Two exposed central pieces substituted only in the new presentation scene; original scene and source file retained.',
                       'Not a replacement anatomical muscle and not an interactive zone.',
                       'Not a mobile-optimized or clinically certified model.'],
    }
    bpy.data.texts.new('FINITION_AINE.json').write(json.dumps(meta, ensure_ascii=False, indent=2))
    bpy.ops.wm.save_as_mainfile(filepath=str(root/meta['master']), compress=True)
    meta['master_sha256'] = sha(root/meta['master'])
    (root/'finition.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2)+'\n')
    print('BUILT', meta['objects_after'], meta['added_triangles'], flush=True)


if __name__ == '__main__':
    main()
