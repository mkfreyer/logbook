"""Real Blender views for boundary control; all original cameras preserved."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--asset', type=Path, required=True)
    p.add_argument('--mode', choices=['neutral', 'zones'], required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--views', nargs='+', required=True)
    args = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
    root, output = args.asset.resolve(), args.output.resolve()
    meta = json.loads((root / 'zones.json').read_text())
    bpy.ops.wm.open_mainfile(filepath=str(root / meta['master']), use_scripts=False)
    scene = bpy.data.scenes[meta['scene']]
    bpy.context.window.scene = scene
    plane = meta['median_plane_x_m']
    for side, x in [('droite', -.19), ('gauche', 2 * plane + .19)]:
        name = 'P4P5_epaule-face-' + side
        data = bpy.data.cameras.new(name)
        data.type, data.ortho_scale = 'ORTHO', .34
        ob = bpy.data.objects.new(name, data)
        scene.collection.objects.link(ob)
        target = Vector((x, .06, 1.4))
        ob.location = target + Vector((0, -4, 0))
        ob.rotation_euler = (target - ob.location).to_track_quat('-Z', 'Y').to_euler()
    if args.mode == 'zones':
        for rec in meta['regions']:
            material = bpy.data.materials[rec['material_name']]
            color = rec['control_color_rgba_linear']
            material.diffuse_color = color
            material.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = color
    output.mkdir(parents=True, exist_ok=True)
    scene.render.engine = 'CYCLES'
    scene.cycles.device, scene.cycles.samples, scene.cycles.seed = 'CPU', 48, 0
    scene.cycles.use_denoising = False
    scene.view_settings.view_transform = 'AgX'
    scene.render.image_settings.file_format = 'PNG'
    frames = []
    for view in args.views:
        scene.camera = bpy.data.objects['P4P5_' + view]
        res = (1200, 640) if view.startswith('epaules-') else (960, 864)
        scene.render.resolution_x, scene.render.resolution_y = res
        scene.render.resolution_percentage = 100
        path = output / (view + '.png')
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        frames.append({'file': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                       'camera': scene.camera.name,
                       'camera_matrix': [list(row) for row in scene.camera.matrix_world],
                       'ortho_scale': scene.camera.data.ortho_scale, 'resolution': res})
        (output / 'metadata.json').write_text(json.dumps({
            'master_sha256': hashlib.sha256((root / meta['master']).read_bytes()).hexdigest(),
            'mode': args.mode, 'samples': 48, 'denoising': False,
            'frames': frames, 'pixels_retouched': False,
            'renderer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        }, indent=2) + '\n')
    print('RENDERED', args.mode, len(frames), flush=True)


if __name__ == '__main__':
    main()
