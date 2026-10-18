"""Prepare inspection scenes from genuine assets. No anatomy is sculpted or synthesized.

Run in Blender 4.3.2 with --factory-startup --disable-autoexec --background.
The original atlas, add-ons and any embedded scripts are never executed.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector, Matrix

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--candidate', choices=['bodyparts3d', 'z-anatomy', 'ecorche'], required=True)
p.add_argument('--source', type=Path, required=True)
p.add_argument('--selection', type=Path)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
a.output.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
records = []
excluded = []
objects = []
reference_points = []


def raw_obj(path):
    positions, faces = [], []
    for line in path.read_text().splitlines():
        bits = line.split()
        if not bits:
            continue
        if bits[0] == 'v':
            positions.append(tuple(float(v) for v in bits[1:4]))
        elif bits[0] == 'f':
            faces.append(tuple(int(v.split('/')[0]) - 1 for v in bits[1:]))
    unique, indices, remap = [], {}, []
    for v in positions:
        if v not in indices:
            indices[v] = len(unique)
            unique.append(v)
        remap.append(indices[v])
    return unique, [tuple(remap[i] for i in f) for f in faces]


def bounds_points(ob):
    return [ob.matrix_world @ Vector(v) for v in ob.bound_box]


if a.candidate == 'z-anatomy':
    with bpy.data.libraries.load(str(a.source), link=False) as (src, dst):
        dst.collections = ['4: Muscular system']
    collection = dst.collections[0]
    bpy.context.scene.collection.children.link(collection)
    bpy.context.view_layer.update()
    muscle_materials = {'Abductor', 'Adductor', 'Biarticular', 'Depressor', 'Diaphragm',
                        'Extension', 'Extension hand/foot', 'Extensor extremities',
                        'External rotation', 'Flexion', 'Flexion fingers',
                        'Flexion hand/foot', 'Internal rotator', 'Levator',
                        'Masticator', 'Orbicularis/Constrictor', 'Superficial', 'Trapezius'}
    supports = {'Epicranial aponeurosis', 'Palmar aponeurosis', 'Plantar aponeurosis',
                'Calcaneal tendon', 'Tendon of extensor digitorum longus',
                'Intermediate tendon of digastric muscle'}
    for ob in collection.all_objects:
        if ob.type != 'MESH':
            excluded.append({'name': ob.name, 'reason': 'not a mesh'})
            continue
        ob.data.calc_loop_triangles()
        materials = {m.name for m in ob.data.materials if m}
        base_name = ob.name[:-2] if ob.name.endswith(('.l', '.r')) else ob.name
        muscle = bool(materials & muscle_materials)
        support = base_name in supports
        if not ob.data.loop_triangles or not (muscle or support) or any(s in ob.name.lower() for s in ['stapedius', 'tensor tympani']):
            excluded.append({'name': ob.name, 'reason': 'annotation, fascia cover, joint tissue, internal throat/ear, or not selected skeletal muscle'})
            continue
        side = 'left' if ob.name.endswith('.l') else 'right' if ob.name.endswith('.r') else 'midline'
        ob['audit_identity'] = ob.name
        ob['audit_side'] = side
        ob['audit_role'] = 'muscle' if muscle else 'supporting tendon/aponeurosis'
        ob['audit_orange'] = side == 'left' and 'pectoralis major muscle' in ob.name.lower()
        ob['audit_source'] = 'Z-Anatomy'
        objects.append(ob)
        reference_points.extend(bounds_points(ob))
elif a.candidate == 'ecorche':
    bpy.ops.import_scene.gltf(filepath=str(a.source))
    bpy.context.view_layer.update()
    for ob in list(bpy.context.scene.objects):
        if ob.type != 'MESH':
            continue
        reference_points.extend(bounds_points(ob))  # Measurement only; bones do not enter render.
        if ob.get('layer') not in {'superficial muscles', 'deep muscles'}:
            excluded.append({'name': ob.name, 'reason': 'skeleton/eyes/cartilage layer excluded'})
            continue
        ob['audit_identity'] = ob.get('name', ob.name)
        ob['audit_side'] = ob.get('side', 'unspecified')
        ob['audit_role'] = 'muscle'
        ob['audit_orange'] = ob.get('fma') in {'FMA45875', 'FMA34691', 'FMA79980'}
        ob['audit_source'] = ob.get('source', 'unspecified')
        objects.append(ob)
else:
    manifest = json.loads(a.selection.read_text())
    ids = manifest['audit_all_muscle_element_ids']
    labels, sides, fmas = {}, {}, {}
    # Prefer the smallest explicit source representation; retain its exact identity.
    for representation in sorted(manifest['audit_all_muscle_sources'], key=lambda r: -len(r['elements'])):
        for element in representation['elements']:
            labels[element['element_id']] = representation['name_en']
            fmas[element['element_id']] = representation['concept_id']
    for selection in manifest['selection_candidates']:
        for component in selection['components']:
            for element in component['elements']:
                labels[element['element_id']] = component['name_en']
                sides[element['element_id']] = selection['side']
    skin, _ = raw_obj(a.source / 'FJ2810.obj')
    reference_points = [Vector(v) for v in skin]
    for element in ids:
        vertices, faces = raw_obj(a.source / (element + '.obj'))
        mesh = bpy.data.meshes.new(element)
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        ob = bpy.data.objects.new(element, mesh)
        bpy.context.collection.objects.link(ob)
        ob['audit_identity'] = labels.get(element, element)
        ob['audit_side'] = sides.get(element, 'see original FMA tables')
        ob['audit_role'] = 'muscle'
        ob['audit_orange'] = element in {'FJ1446M', 'FJ1447M', 'FJ1464M'}
        ob['audit_source'] = 'BodyParts3D'
        if element in fmas:
            ob['fma'] = fmas[element]
        objects.append(ob)

lo = Vector([min(v[i] for v in reference_points) for i in range(3)])
hi = Vector([max(v[i] for v in reference_points) for i in range(3)])
center = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
scale = 1.8 / (hi.z - lo.z)
graph = bpy.context.evaluated_depsgraph_get()
prepared = []
for ob in objects:
    evaluated = ob.evaluated_get(graph)
    mesh = bpy.data.meshes.new_from_object(evaluated, depsgraph=graph)
    mesh.calc_loop_triangles()
    properties = {k: v for k, v in ob.items() if k.startswith('audit_') or k in {'fma', 'layer'}}
    for vertex in mesh.vertices:
        vertex.co = (ob.matrix_world @ vertex.co - center) * scale
        assert all(math.isfinite(c) for c in vertex.co)
    # Source topology is preserved; no automatic decimation/subdivision/normal repair.
    record = {'object': ob.name, **properties, 'vertices': len(mesh.vertices),
              'triangles': len(mesh.loop_triangles),
              'centroid': [sum(v.co[i] for v in mesh.vertices) / len(mesh.vertices) for i in range(3)],
              'source_modifiers': [m.type for m in ob.modifiers]}
    records.append(record)
    prepared.append((ob.name, mesh, properties))
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for name, mesh, props in prepared:
    mesh.materials.clear()
    ob = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(ob)
    for key, value in props.items():
        ob[key] = value
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    ob.hide_render = False
    ob.hide_viewport = False
    ob.hide_set(False)
assert sum(bool(r['audit_orange']) for r in records) == 3, 'Selection must be the three actual left pec components'
metadata = {'candidate': a.candidate, 'blender': bpy.app.version_string,
            'normalization_reference': {'bodyparts3d': 'original skin bounds, skin not rendered',
                                        'z-anatomy': 'selected muscle + original epicranial/tendon extents; no skin mesh in source Skin collection',
                                        'ecorche': 'complete source body bounds; skeleton measured only, not rendered'}[a.candidate],
            'source_bounds': {'min': list(lo), 'max': list(hi)},
            'transform': {'center': list(center), 'uniform_scale': scale, 'reference_height': 1.8},
            'axes': {'+Z': 'superior', '-Y': 'anterior', '+X': 'anatomical left'},
            'geometry_changes': 'world transforms baked, uniform scale/translation; exact-position weld per BodyParts3D OBJ only; smooth face shading. No sculpting, no subdivisions, no invented fillers.',
            'objects': records, 'excluded': excluded,
            'counts': {'objects': len(records), 'vertices': sum(r['vertices'] for r in records),
                       'triangles': sum(r['triangles'] for r in records)},
            'orange_selection': [r['object'] for r in records if r['audit_orange']]}
if a.source.is_file():
    metadata['source_sha256'] = hashlib.sha256(a.source.read_bytes()).hexdigest()
(a.output / 'inventory.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')
bpy.ops.wm.save_as_mainfile(filepath=str(a.output / 'muscles-only.blend'))
print('AUDIT', json.dumps(metadata['counts']), 'bounds', list(lo), list(hi), flush=True)
