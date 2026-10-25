"""Render the restored combination using the unchanged neutral matte setup."""
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
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
root = a.asset.resolve()
out = root / 'renders'
out.mkdir(parents=True, exist_ok=True)
file = root / 'ecorche-p4-p5.blend'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


meta = json.loads((root / 'combinaison.json').read_text())
plane = meta['median_plane_x_m']
bpy.ops.wm.open_mainfile(filepath=str(file), use_scripts=False)
scene = bpy.data.scenes[meta['scene']]
bpy.context.window.scene = scene
rig = bpy.data.collections.new('COMBINAISON_LUMIERES_SYMETRIQUES')
scene.collection.children.link(rig)


def aim(ob, target):
    ob.rotation_euler = (Vector(target) - ob.location).to_track_quat('-Z', 'Y').to_euler()


lights = []
for label, x, y, z, power, size in [('Avant', 3, -3, 2.6, 200, 2.2), ('Dos', 2, 3, 3, 180, 2.2)]:
    for side in [-1, 1]:
        light = bpy.data.lights.new(f'P4P5_{label}_{side}', 'AREA')
        light.energy, light.shape, light.size = power, 'DISK', size
        ob = bpy.data.objects.new(light.name, light)
        rig.objects.link(ob)
        ob.location = (plane + side * x, y, z)
        aim(ob, (plane, 0, 1))
        lights.append({'location': list(ob.location), 'energy': power, 'size': size})
light = bpy.data.lights.new('P4P5_Centre', 'AREA')
light.energy, light.shape, light.size = 100, 'DISK', 2
ob = bpy.data.objects.new(light.name, light)
rig.objects.link(ob)
ob.location = (plane, -4, 4)
aim(ob, (plane, 0, 1))
lights.append({'location': list(ob.location), 'energy': 100, 'size': 2})
views = [
    ('face', 0, 2.05, (plane, 0, .9), (720, 1152)),
    ('profil', -90, 2.05, (plane, 0, .9), (720, 1152)),
    ('dos', 180, 2.05, (plane, 0, .9), (720, 1152)),
    ('trois-quarts', -45, 2.05, (plane, 0, .9), (720, 1152)),
    ('epaules-face', 0, .68, (plane, .02, 1.41), (1200, 640)),
    ('epaules-dos', 180, .68, (plane, .02, 1.41), (1200, 640)),
    ('epaule-droite', -55, .40, (-.19, .06, 1.4), (960, 864)),
    ('epaule-gauche', 55, .40, (2 * plane + .19, .06, 1.4), (960, 864)),
    ('epaule-profil', -90, .40, (-.19, .06, 1.4), (960, 864)),
    ('epaule-arriere', -135, .40, (-.19, .06, 1.4), (960, 864)),
]
scene.world = bpy.data.worlds['PASSE3_FOND_NEUTRE']
scene.render.engine = 'CYCLES'
scene.cycles.device, scene.cycles.samples, scene.cycles.seed = 'CPU', 48, 0
scene.cycles.use_denoising = False
scene.view_settings.view_transform = 'AgX'
scene.render.image_settings.file_format = 'PNG'
metadata = {
    'input_blend_sha256': sha(file), 'renderer_sha256': sha(Path(__file__)),
    'engine': 'CYCLES_CPU', 'samples': 48, 'lights': lights,
    'same_pass3_matte_material': True, 'render_pixels_retouched': False,
    'frames': [],
}
cameras = {}
for name, yaw, scale, target, res in views:
    camera = bpy.data.cameras.new('P4P5_' + name)
    camera.type, camera.ortho_scale = 'ORTHO', scale
    ob = bpy.data.objects.new(camera.name, camera)
    rig.objects.link(ob)
    theta = math.radians(yaw)
    ob.location = Vector(target) + Vector((4 * math.sin(theta), -4 * math.cos(theta), 0))
    aim(ob, target)
    cameras[name] = ob
    scene.camera = ob
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    path = out / (name + '.png')
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True, scene=scene.name)
    metadata['frames'].append({'file': path.name, 'sha256': sha(path), 'yaw_degrees': yaw,
                               'ortho_scale': scale, 'target': list(target), 'size': list(res)})
    (out / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
scene.camera = cameras['face']
bpy.ops.wm.save_as_mainfile(filepath=str(file), compress=True)
metadata['final_blend_sha256'] = sha(file)
(out / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
print('COMBINAISON_RENDERED', len(views), flush=True)
