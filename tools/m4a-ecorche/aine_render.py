"""Identical Cycles cameras, neutral material and lighting before/after."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--asset', type=Path, required=True)
    p.add_argument('--mode', choices=['before', 'after'], required=True)
    p.add_argument('--views', nargs='+', default=['aine-face', 'aine-trois-quarts', 'face', 'trois-quarts'])
    a = p.parse_args(sys.argv[sys.argv.index('--')+1:])
    root = a.asset.resolve()
    meta = json.loads((root/'finition.json').read_text())
    master = root/meta['master'] if a.mode == 'after' else root/meta['baseline_master']
    bpy.ops.wm.open_mainfile(filepath=str(master.resolve()), use_scripts=False)
    scene = bpy.data.scenes[meta['scene'] if a.mode == 'after' else meta['source_scene']]
    bpy.context.window.scene = scene
    for name, yaw in [('aine-face', 0), ('aine-trois-quarts', -35)]:
        data = bpy.data.cameras.new('AINE_'+name)
        data.type, data.ortho_scale = 'ORTHO', .32
        cam = bpy.data.objects.new('AINE_'+name, data)
        scene.collection.objects.link(cam)
        target = Vector((.002114987923242599, -.005, .932))
        cam.location = target+Vector((4*math.sin(math.radians(yaw)), -4*math.cos(math.radians(yaw)), 0))
        cam.rotation_euler = (target-cam.location).to_track_quat('-Z', 'Y').to_euler()
    out = root/'renders'/a.mode
    out.mkdir(parents=True, exist_ok=True)
    scene.render.engine = 'CYCLES'
    scene.cycles.device, scene.cycles.samples, scene.cycles.seed = 'CPU', 32, 0
    scene.cycles.use_denoising = False
    scene.view_settings.view_transform = 'AgX'
    scene.render.image_settings.file_format = 'PNG'
    frames = []
    for view in a.views:
        scene.camera = bpy.data.objects[('AINE_' if view.startswith('aine-') else 'P4P5_')+view]
        res = (1000, 850) if view.startswith('aine-') else (720, 1152)
        scene.render.resolution_x, scene.render.resolution_y = res
        scene.render.resolution_percentage = 100
        path = out/(view+'.png')
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        frames.append({'file': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                       'camera_matrix': [list(r) for r in scene.camera.matrix_world],
                       'ortho_scale': scene.camera.data.ortho_scale, 'resolution': res})
        (out/'metadata.json').write_text(json.dumps({
            'master_sha256': hashlib.sha256(master.read_bytes()).hexdigest(),
            'samples': 32, 'denoising': False, 'seed': 0,
            'renderer': 'Blender 4.3.2 Cycles CPU; AgX; inherited five neutral lights',
            'image_editing': 'None; Blender render output', 'frames': frames,
        }, indent=2)+'\n')


if __name__ == '__main__':
    main()
