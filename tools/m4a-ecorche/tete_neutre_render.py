"""Matched real Blender renders, inherited matte material and five lights."""
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
p.add_argument('--views', nargs='+', default=['face', 'trois-quarts', 'profil', 'arriere', 'ensemble'])
a = p.parse_args(sys.argv[sys.argv.index('--')+1:])
root = a.asset.resolve()
meta = json.loads((root/'tete.json').read_text())
master = root/(meta['baseline_master'] if a.mode == 'before' else meta['master'])
sha = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
input_sha = sha(master)
bpy.ops.wm.open_mainfile(filepath=str(master.resolve()), use_scripts=False)
scene = bpy.data.scenes[meta['source_scene'] if a.mode == 'before' else meta['scene']]
bpy.context.window.scene = scene
assert len([o for o in scene.objects if o.type == 'LIGHT']) == 5
plane = meta['median_plane_x_m']
target = Vector((plane, .035, 1.69))
cameras = {}
for name, yaw in [('face', 0), ('trois-quarts', -35), ('profil', -90), ('arriere', 180)]:
    data = bpy.data.cameras.new('TETE_NEUTRE_'+name)
    data.type, data.ortho_scale = 'ORTHO', .32
    camera = bpy.data.objects.new(data.name, data)
    scene.collection.objects.link(camera)
    angle = math.radians(yaw)
    camera.location = target+Vector((4*math.sin(angle), -4*math.cos(angle), 0))
    camera.rotation_euler = (target-camera.location).to_track_quat('-Z', 'Y').to_euler()
    cameras[name] = camera
scene.render.engine = 'CYCLES'
scene.cycles.device, scene.cycles.seed = 'CPU', 0
scene.cycles.use_denoising = False
scene.view_settings.view_transform = 'AgX'
scene.render.image_settings.file_format = 'PNG'
scene.render.use_border = False
scene.render.resolution_percentage = 100
out = a.preview.resolve() if a.preview else root/'renders'/a.mode
out.mkdir(parents=True, exist_ok=True)
record = {'master_sha256': input_sha, 'mode': a.mode, 'preview': bool(a.preview),
          'renderer_sha256': sha(Path(__file__)), 'frames': [],
          'image_processing': 'None', 'denoising': False, 'seed': 0,
          'lights': {o.name: [o.data.energy, o.data.size, list(o.location)]
                     for o in scene.objects if o.type == 'LIGHT'}}
for view in a.views:
    scene.camera = bpy.data.objects['P4P5_face'] if view == 'ensemble' else cameras[view]
    res = (600, 600) if a.preview else ((720, 1152) if view == 'ensemble' else (864, 864))
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.cycles.samples = 8 if a.preview else (32 if view == 'ensemble' else 48)
    path = out/(view+'.png')
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    assert sha(master) == input_sha
    record['frames'].append({'file': path.name, 'sha256': sha(path),
        'camera_matrix': [list(row) for row in scene.camera.matrix_world],
        'ortho_scale': scene.camera.data.ortho_scale, 'resolution': res,
        'samples': scene.cycles.samples})
    (out/'metadata.json').write_text(json.dumps(record, indent=2)+'\n')
