"""Derive an editable, modestly athletic shape key from the genuine B source cage."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

import bpy
from mathutils import Vector


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def smoothstep(value):
    value = min(1.0, max(0.0, value))
    return value * value * (3.0 - 2.0 * value)


def influence(point, region):
    center, radii = region['center'], region['radii']
    radius = math.sqrt(sum(((point[i] - center[i]) / radii[i]) ** 2 for i in range(3)))
    if radius >= 2.5:
        return 0.0
    low, low_full, high_full, high = region['z_support']
    support = smoothstep((point.z - low) / (low_full - low))
    support *= smoothstep((high - point.z) / (high - high_full))
    return math.exp(-radius * radius) * smoothstep((2.5 - radius) / 0.5) * support


def deform(point, regions):
    sign = 1.0 if point.x >= 0 else -1.0
    local = Vector((abs(point.x), point.y, point.z))
    delta = Vector((0, 0, 0))
    weights = {}
    for region in regions:
        weight = influence(local, region)
        move = Vector(region['delta'])
        move.y += region.get('radial_y', 0) * (local.y - region['center'][1])
        if 'arm_radial_scale' in region:
            # Smooth expansion perpendicular to the native upper-arm axis in A-pose.
            axis_x = 0.249 + 0.39 * (1.31 - local.z)
            radial = (local.x - axis_x) * 0.9317
            move.x += radial * 0.9317 * region['arm_radial_scale']
            move.z += radial * 0.3634 * region['arm_radial_scale']
            move.y += (local.y - 0.028) * region['arm_radial_scale']
        delta += move * weight
        weights[region['name']] = weight
    # Keep the center seam continuous; bilateral masks do not identify muscles.
    delta.x *= sign * smoothstep(abs(point.x) / 0.04)
    return delta, weights


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--blend', type=Path, required=True)
    parser.add_argument('--settings', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    if args.output.exists():
        raise ValueError('Refusing to overwrite an existing variant')
    settings = json.loads(args.settings.read_text())
    if digest(args.blend) != settings['source_blend_sha256']:
        raise ValueError('Source B file does not match the inspected official bundle')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    names = ['GEO-body_male_realistic', 'GEO-body_male_realistic.eye.L', 'GEO-body_male_realistic.eye.R']
    with bpy.data.libraries.load(str(args.blend), link=False) as (source, target):
        target.objects = names
        target.texts = list(source.texts)
    for obj in target.objects:
        bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.update()
    body = target.objects[0]
    basis = body.shape_key_add(name='B original — unchanged basis', from_mix=False)
    variant = body.shape_key_add(name='B+ moderate athletic', from_mix=False)
    normalization = settings['normalization']
    center = Vector(normalization['center'])
    scale = normalization['scale']
    inverse = body.matrix_world.to_3x3().inverted()
    distances = []
    region_max = {region['name']: 0.0 for region in settings['regions']}
    for vertex, original, key in zip(body.data.vertices, basis.data, variant.data):
        point = (body.matrix_world @ original.co - center) * scale
        delta, weights = deform(point, settings['regions'])
        key.co = original.co + inverse @ (delta / scale)
        distances.append(delta.length)
        for name, weight in weights.items():
            region_max[name] = max(region_max[name], weight)
        assert all(math.isfinite(c) for c in key.co)
        assert vertex.co == original.co
    variant.value = 1.0
    body['variant'] = settings['variant']
    body['license'] = 'CC0; source Dan Ulrich / Blender Studio Human Base Meshes v1.4.1'
    body['shape_key_is_not_muscle_segmentation'] = True
    text = bpy.data.texts.new('B+ provenance and settings')
    text.write(json.dumps(settings, indent=2))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output), compress=True)
    report = {'source_sha256': digest(args.blend), 'settings_sha256': digest(args.settings),
              'variant_sha256': digest(args.output), 'settings': settings,
              'method': 'symmetric smooth additive volume fields on original cage shape key before original Multires 3',
              'vertices': len(body.data.vertices), 'faces': len(body.data.polygons),
              'maximum_cage_displacement_at_normalized_height_1_8': max(distances),
              'mean_cage_displacement_at_normalized_height_1_8': sum(distances) / len(distances),
              'changed_vertices_above_1e_6': sum(d > 1e-6 for d in distances),
              'region_max_influence': region_max, 'original_basis_preserved': True,
              'shape_key_sha256': hashlib.sha256(b''.join(struct.pack('<3f', *v.co) for v in variant.data)).hexdigest(),
              'application_integrated': False}
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'settings'}, indent=2))


if __name__ == '__main__':
    main()
