"""Actual Cycles renders of prepared inspection assets, using one shared protocol."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
import bpy
from mathutils import Vector

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--prepared', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--samples', type=int, default=128)
p.add_argument('--resolution', type=int, nargs=2, default=[600, 1000])
p.add_argument('--views', default='front,three-quarter,back,selection')
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
a.output.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(a.prepared / 'muscles-only.blend'), use_scripts=False)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = a.samples
scene.cycles.use_denoising = False
scene.render.resolution_x, scene.render.resolution_y = a.resolution
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.009, .019, .036, 1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .6
scene.view_settings.view_transform = 'AgX'

def material(name, color, roughness, metallic):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n = m.node_tree.nodes.get('Principled BSDF')
    n.inputs['Base Color'].default_value = (*color, 1)
    n.inputs['Roughness'].default_value = roughness
    n.inputs['Metallic'].default_value = metallic
    n.inputs['Coat Weight'].default_value = .08
    n.inputs['Coat Roughness'].default_value = .32
    return m

satin = material('Common blue grey satin', (.23, .30, .41), .37, .12)
orange = material('Actual left pectoralis major selection', (1, .19, .035), .35, .06)
meshes = [ob for ob in scene.objects if ob.type == 'MESH']
assert all('audit_identity' in ob for ob in meshes)
assert sum(bool(ob['audit_orange']) for ob in meshes) == 3
for ob in meshes:
    ob.data.materials.clear()
    ob.data.materials.append(satin)
    for poly in ob.data.polygons:
        poly.material_index = 0

def aim(ob, target):
    ob.rotation_euler = (Vector(target) - ob.location).to_track_quat('-Z', 'Y').to_euler()

def light(name, loc, power, size, color):
    d = bpy.data.lights.new(name, 'AREA')
    d.energy, d.shape, d.size, d.color = power, 'DISK', size, color
    ob = bpy.data.objects.new(name, d)
    scene.collection.objects.link(ob)
    ob.location = loc
    aim(ob, (0, 0, 1))

light('Key', (-2, -2.5, 3.2), 230, 3, (.81, .88, 1))
light('Fill', (2.6, -1.7, 1.6), 110, 2.5, (.56, .69, 1))
light('Rim', (1.6, 2.3, 2.8), 310, 2, (.58, .72, 1))
light('Back fill', (-2, 2, 1.3), 90, 2.5, (.75, .82, 1))
data = bpy.data.cameras.new('Shared orthographic camera')
cam = bpy.data.objects.new('Shared orthographic camera', data)
scene.collection.objects.link(cam)
scene.camera = cam
data.type, data.ortho_scale = 'ORTHO', 2.30
inventory = json.loads((a.prepared / 'inventory.json').read_text())
metadata = {'candidate': inventory['candidate'], 'counts': inventory['counts'],
            'prepared_sha256': hashlib.sha256((a.prepared / 'muscles-only.blend').read_bytes()).hexdigest(),
            'protocol': {'blender': bpy.app.version_string, 'engine': 'CYCLES_CPU',
                         'samples': a.samples, 'resolution': a.resolution, 'denoising': False,
                         'orthographic_scale': 2.30, 'camera_target': [0, 0, .9],
                         'material': {'base_color_linear': [.23, .30, .41], 'roughness': .37, 'metallic': .12},
                         'source_textures_vertex_colors_replaced': True, 'subdivision': 0,
                         'anatomical_geometry_synthesized': False},
            'orange_selection': inventory['orange_selection'], 'frames': []}
angles = {'front': 0, 'three-quarter': -35, 'back': 180, 'side': 90, 'selection': -35}
for view in a.views.split(','):
    for ob in meshes:
        ob.data.materials[0] = orange if view == 'selection' and ob['audit_orange'] else satin
    angle = math.radians(angles[view])
    cam.location = (4.5 * math.sin(angle), -4.5 * math.cos(angle), .98)
    aim(cam, (0, 0, .9))
    scene.render.filepath = str(a.output / (view + '.png'))
    bpy.ops.render.render(write_still=True)
    metadata['frames'].append({'view': view, 'yaw_degrees': angles[view], 'path': view + '.png',
                               'sha256': hashlib.sha256((a.output / (view + '.png')).read_bytes()).hexdigest()})
    (a.output / 'render-metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
