"""Render L2 and L3 in the same blue-silver studio, real Blender geometry only."""
import argparse, hashlib, json, math, sys
from pathlib import Path
import bpy
from mathutils import Vector

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--prepared', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--resolution', type=int, nargs=2, default=[900, 1400])
p.add_argument('--samples', type=int, default=128)
p.add_argument('--views', default='front,three-quarter,back,side,selection')
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
a.output.mkdir(parents=True, exist_ok=True)
source = a.prepared / 'logbook-original.blend'
bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
scene = bpy.context.scene
visible = [o for o in scene.objects if o.type == 'MESH' and o.get('logbook_render')]
assert len(visible) == 23
assert sum(bool(o.get('logbook_selectable')) for o in visible) == 22

def material(name, color, roughness=.42, metallic=.18):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n = m.node_tree.nodes.get('Principled BSDF')
    n.inputs['Base Color'].default_value = (*color, 1)
    n.inputs['Roughness'].default_value = roughness
    n.inputs['Metallic'].default_value = metallic
    n.inputs['Coat Weight'].default_value = .10
    n.inputs['Subsurface Weight'].default_value = .05
    n.inputs['Subsurface Radius'].default_value = (.8, .55, .35)
    n.inputs['Subsurface Scale'].default_value = .006
    n.inputs['Transmission Weight'].default_value = .035
    n.inputs['IOR'].default_value = 1.44
    n.inputs['Coat Roughness'].default_value = .30
    return m

grey = material('Logbook blue grey satin', (.17, .245, .38))
orange = material('Logbook selected surface zone', (1, .18, .025), .36, .10)
for ob in visible:
    ob.data.materials.clear()
    ob.data.materials.append(grey)
    for poly in ob.data.polygons:
        poly.material_index = 0
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = a.samples
scene.cycles.seed = 0
scene.cycles.use_denoising = False
scene.render.resolution_x, scene.render.resolution_y = a.resolution
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.film_transparent = False
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.009, .019, .036, 1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .6
scene.view_settings.view_transform = 'AgX'

def aim(ob, target):
    ob.rotation_euler = (Vector(target) - ob.location).to_track_quat('-Z', 'Y').to_euler()

light_settings = [('Key', (-2, -2.5, 3.2), 230, 2.2, (.81, .88, 1)),
                  ('Fill', (2.6, -1.7, 1.6), 85, 2.5, (.56, .69, 1)),
                  ('Rim', (1.6, 2.3, 2.8), 310, 2, (.58, .72, 1)),
                  ('Back fill', (-2, 2, 1.3), 90, 2.5, (.75, .82, 1))]
for name, loc, power, size, color in light_settings:
    data = bpy.data.lights.new(name, 'AREA')
    data.energy, data.shape, data.size, data.color = power, 'DISK', size, color
    ob = bpy.data.objects.new(name, data)
    scene.collection.objects.link(ob)
    ob.location = loc
    aim(ob, (0, 0, 1))
data = bpy.data.cameras.new('Shared Logbook research camera')
cam = bpy.data.objects.new('Shared Logbook research camera', data)
scene.collection.objects.link(cam)
scene.camera = cam
data.type, data.ortho_scale = 'ORTHO', 2.15
angles = {'front': 0, 'three-quarter': 35, 'back': 180, 'side': 90, 'selection': 35}
metadata = {'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'variant': json.loads((a.prepared / 'construction.json').read_text())['variant'],
            'protocol': {'renderer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'blender': bpy.app.version_string, 'engine': 'CYCLES_CPU', 'samples': a.samples,
                         'resolution': a.resolution, 'seed': 0, 'denoising': False,
                         'orthographic_scale': 2.15, 'camera_target': [0, 0, .90],
                         'lights': light_settings, 'satin': {'base_color_linear': [.17, .245, .38], 'roughness': .42, 'metallic': .18, 'coat': .10, 'subsurface_weight': .05, 'subsurface_radius': [.8,.55,.35], 'subsurface_scale_m': .006, 'transmission_weight': .035, 'ior': 1.44},
                         'source_geometry_changed_by_renderer': False, 'AI_generated_images': False},
            'orange_zones': ['pectoralis.left','pectoralis.right'], 'frames': []}
for view in a.views.split(','):
    for ob in visible:
        ob.data.materials[0] = orange if view == 'selection' and ob['logbook_zone'] in ('pectoralis.left','pectoralis.right') else grey
    angle = math.radians(angles[view])
    cam.location = (4.5 * math.sin(angle), -4.5 * math.cos(angle), .99)
    aim(cam, (0, 0, .90))
    scene.render.filepath = str(a.output / (view + '.png'))
    bpy.ops.render.render(write_still=True)
    metadata['frames'].append({'view': view, 'yaw_degrees': angles[view], 'path': view + '.png',
                               'sha256': hashlib.sha256((a.output / (view + '.png')).read_bytes()).hexdigest(),
                               'orange_objects': [ob.name for ob in visible if ob.data.materials[0] == orange]})
    (a.output / 'render-metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
# A reviewable Blender scene opens with the common studio, neutral materials and
# three-quarter camera. This is a research artifact, never an app asset export.
for ob in visible:
    ob.data.materials[0] = grey
angle = math.radians(35)
cam.location = (4.5 * math.sin(angle), -4.5 * math.cos(angle), .99)
aim(cam, (0, 0, .90))
scene.render.filepath = str(a.output / 'manual-review.png')
review = a.output / 'scene-review.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(review), compress=True)
metadata['review_scene'] = {'path': review.name, 'sha256': hashlib.sha256(review.read_bytes()).hexdigest(),
                            'neutral_materials_restored': True, 'camera_view': 'three-quarter'}
(a.output / 'render-metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
