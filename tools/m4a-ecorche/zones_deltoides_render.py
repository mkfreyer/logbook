"""Render original cameras/lights, switching only six material colors in memory."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--asset', type=Path, required=True)
    parser.add_argument('--mode', choices=['neutral', 'zones'], required=True)
    parser.add_argument('--views', nargs='+', default=[
        'face', 'profil', 'dos', 'trois-quarts', 'epaules-face', 'epaules-dos',
        'epaule-droite', 'epaule-gauche', 'epaule-profil', 'epaule-arriere'])
    parser.add_argument('--preview', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    root = args.asset.resolve()
    meta = json.loads((root / 'zones.json').read_text())
    bpy.ops.wm.open_mainfile(filepath=str(root / meta['master']), use_scripts=False)
    scene = bpy.data.scenes[meta['scene']]
    bpy.context.window.scene = scene
    if args.mode == 'zones':
        for rec in meta['regions']:
            mat = bpy.data.materials[rec['material_name']]
            mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = rec['control_color_rgba_linear']
            mat.diffuse_color = rec['control_color_rgba_linear']
    # The master remains neutral; nothing is saved after recoloring.
    output = root / 'renders' / ('preview' if args.preview else args.mode)
    output.mkdir(parents=True, exist_ok=True)
    scene.render.engine = 'CYCLES'
    scene.cycles.device, scene.cycles.samples, scene.cycles.seed = 'CPU', 16 if args.preview else 48, 0
    scene.cycles.use_denoising = False
    scene.view_settings.view_transform = 'AgX'
    scene.render.image_settings.file_format = 'PNG'
    frames = []
    for view in args.views:
        camera = bpy.data.objects['P4P5_' + view]
        scene.camera = camera
        res = ((720, 1152) if view in ['face', 'profil', 'dos', 'trois-quarts'] else
               (1200, 640) if view.startswith('epaules-') else (960, 864))
        scene.render.resolution_x, scene.render.resolution_y = res
        scene.render.resolution_percentage = 50 if args.preview else 100
        path = output / (view + '.png')
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        frames.append({'file': view + '.png', 'sha256': sha(path),
                       'camera': camera.name,
                       'camera_matrix': [list(row) for row in camera.matrix_world],
                       'ortho_scale': camera.data.ortho_scale,
                       'resolution': [scene.render.resolution_x, scene.render.resolution_y],
                       'resolution_percentage': scene.render.resolution_percentage})
        (output / 'metadata.json').write_text(json.dumps({
            'master_sha256': sha(root / meta['master']), 'mode': args.mode,
            'engine': 'Cycles CPU', 'samples': scene.cycles.samples,
            'denoising': False, 'frames': frames, 'pixels_retouched': False,
            'renderer_sha256': sha(Path(__file__)),
        }, indent=2) + '\n')
    print('RENDERED', args.mode, len(frames), flush=True)


if __name__ == '__main__':
    main()
