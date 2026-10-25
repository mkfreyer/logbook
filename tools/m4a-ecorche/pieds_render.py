"""Matched neutral Blender renders; no image cleanup or geometry modification."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

p = argparse.ArgumentParser()
p.add_argument('--asset', type=Path, required=True)
p.add_argument('--mode', choices=['before', 'after'], required=True)
p.add_argument('--views', nargs='+', default=['face-pieds', 'profil-droit', 'profil-gauche',
                                            'trois-quarts-pieds', 'chevilles', 'ensemble'])
a = p.parse_args(sys.argv[sys.argv.index('--')+1:])
root = a.asset.resolve()
meta = json.loads((root/'finition.json').read_text())
master = root/(meta['master'] if a.mode == 'after' else meta['baseline_master'])
master_hash = hashlib.sha256(master.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(master.resolve()), use_scripts=False)
scene = bpy.data.scenes[meta['scene'] if a.mode == 'after' else meta['source_scene']]
bpy.context.window.scene = scene
plane = meta['median_plane_x_m']
cameras = {
    'face-pieds': ((plane, .02, .092), (0, -3, .30), .42, (1000, 800)),
    'profil-droit': ((-.125, .015, .09), (-3, 0, .25), .38, (1000, 700)),
    'profil-gauche': ((.129, .015, .09), (3, 0, .25), .38, (1000, 700)),
    'trois-quarts-pieds': ((plane, .025, .085), (-1.5, -3.5, 1.1), .46, (1000, 800)),
    'chevilles': ((plane, .082, .155), (-1.2, -3.5, .65), .36, (1000, 620)),
}
for name, (target, offset, scale, resolution) in cameras.items():
    data = bpy.data.cameras.new('PIEDS_'+name)
    data.type, data.ortho_scale = 'ORTHO', scale
    ob = bpy.data.objects.new('PIEDS_'+name, data)
    scene.collection.objects.link(ob)
    target = Vector(target)
    ob.location = target+Vector(offset)
    ob.rotation_euler = (target-ob.location).to_track_quat('-Z', 'Y').to_euler()
out = root/'renders'/a.mode
out.mkdir(parents=True, exist_ok=True)
scene.render.engine = 'CYCLES'
scene.cycles.device, scene.cycles.samples, scene.cycles.seed = 'CPU', 32, 0
scene.cycles.use_denoising = False
scene.view_settings.view_transform = 'AgX'
scene.render.image_settings.file_format = 'PNG'
scene.render.use_border = False
scene.render.resolution_percentage = 100
old = json.loads((out/'metadata.json').read_text()) if (out/'metadata.json').exists() else {}
frames = old.get('frames', []) if old.get('master_sha256') == master_hash else []
for view in a.views:
    scene.camera = bpy.data.objects['P4P5_face' if view == 'ensemble' else 'PIEDS_'+view]
    resolution = (720, 1152) if view == 'ensemble' else cameras[view][3]
    scene.render.resolution_x, scene.render.resolution_y = resolution
    path = out/(view+'.png')
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    assert hashlib.sha256(master.read_bytes()).hexdigest() == master_hash
    frames = [f for f in frames if f['file'] != path.name]
    frames.append({'file': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                   'camera_matrix': [list(row) for row in scene.camera.matrix_world],
                   'ortho_scale': scene.camera.data.ortho_scale,
                   'resolution': resolution, 'samples': 32})
    (out/'metadata.json').write_text(json.dumps({
        'master_sha256': master_hash, 'frames': frames, 'samples': 32,
        'denoising': False, 'seed': 0, 'image_editing': 'None',
        'renderer': 'Blender 4.3.2 Cycles CPU; AgX; inherited neutral material and five lights',
        'renderer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }, indent=2)+'\n')
