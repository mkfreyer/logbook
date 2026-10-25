"""Matched neutral Blender views of the source body and the head assembly."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

p = argparse.ArgumentParser()
p.add_argument('--asset', type=Path, required=True)
p.add_argument('--mode', choices=['before', 'after'], required=True)
p.add_argument('--preview', type=Path)
p.add_argument('--views', nargs='+', default=['face', 'profil', 'trois-quarts', 'tete-face', 'tete-profil', 'tete-trois-quarts'])
a = p.parse_args(sys.argv[sys.argv.index('--')+1:])
root = a.asset.resolve()
meta = json.loads((root/'assemblage.json').read_text())
master = root/meta['master']
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
input_sha = sha(master)
assert input_sha == meta['master_sha256']
bpy.ops.wm.open_mainfile(filepath=str(master), use_scripts=False)
scene = bpy.data.scenes[meta['scene_before'] if a.mode == 'before' else meta['scene_after']]
bpy.context.window.scene = scene
scene.render.engine = 'CYCLES'
scene.cycles.device, scene.cycles.seed = 'CPU', 0
scene.cycles.use_denoising = False
scene.view_settings.view_transform = 'AgX'
scene.render.image_settings.file_format = 'PNG'
scene.render.resolution_percentage = 100
scene.render.use_border = False
data = bpy.data.cameras.new('ASSEMBLAGE_CAMERA')
data.type = 'ORTHO'
camera = bpy.data.objects.new(data.name, data)
scene.collection.objects.link(camera)
scene.camera = camera
out = a.preview.resolve() if a.preview else root/'renders'/a.mode
out.mkdir(parents=True, exist_ok=True)
record = {'master_sha256': input_sha, 'mode': a.mode, 'preview': bool(a.preview),
          'renderer_sha256': sha(Path(__file__)), 'frames': [], 'image_processing': 'None',
          'seed': 0, 'denoising': False,
          'lights': {o.name: [o.data.energy, o.data.size, list(o.location)]
                     for o in scene.objects if o.type == 'LIGHT'}}
for view in a.views:
    neck = view.startswith('raccord-')
    close = view.startswith('tete-') or neck
    name = view[8:] if neck else (view[5:] if close else view)
    yaw = {'face': 0, 'profil': -90, 'trois-quarts': -35}[name]
    target = Vector((-.002, -.005, .715)) if neck else (Vector((-.002, -.02, .82)) if close else Vector((-.002, 0, -.002)))
    angle = math.radians(yaw)
    camera.location = target+Vector((4*math.sin(angle), -4*math.cos(angle), 0))
    camera.rotation_euler = (target-camera.location).to_track_quat('-Z', 'Y').to_euler()
    data.ortho_scale = .235 if neck else (.38 if close else 2.15)
    size = (600, 600) if a.preview else ((864, 864) if close else (720, 1152))
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.cycles.samples = 12 if a.preview else 32
    path = out/(view+'.png')
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    assert sha(master) == input_sha
    record['frames'].append({'file': path.name, 'sha256': sha(path),
        'camera_matrix': [list(row) for row in camera.matrix_world],
        'ortho_scale': data.ortho_scale, 'resolution': size, 'samples': scene.cycles.samples})
    (out/'metadata.json').write_text(json.dumps(record, indent=2)+'\n')
