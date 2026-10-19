"""Add a reversible premium-volume variant to the validated B+ Blender source."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.dont_write_bytecode = True
from generate_bplus import deform, digest


def positions_hash(key):
    return hashlib.sha256(b''.join(struct.pack('<3f', *v.co) for v in key.data)).hexdigest()


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
        raise ValueError('Expected the exact user-validated B+ source')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    with bpy.data.libraries.load(str(args.blend), link=False) as (source, target):
        target.objects = ['GEO-body_male_realistic', 'GEO-body_male_realistic.eye.L', 'GEO-body_male_realistic.eye.R']
        target.texts = list(source.texts)
    for obj in target.objects:
        bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.update()
    body = target.objects[0]
    source_key = body.data.shape_keys.key_blocks[settings['source_shape_key']]
    if positions_hash(source_key) != settings['source_shape_key_sha256']:
        raise ValueError('The validated B+ shape has changed')
    preserved = {key.name: {'sha256': positions_hash(key), 'value': key.value}
                 for key in body.data.shape_keys.key_blocks}
    variant = body.shape_key_add(name=settings['variant_shape_key'], from_mix=False)
    variant.relative_key = source_key
    center = Vector(settings['normalization']['center'])
    scale = settings['normalization']['scale']
    inverse = body.matrix_world.to_3x3().inverted()
    distances = []
    for original, key in zip(source_key.data, variant.data):
        point = (body.matrix_world @ original.co - center) * scale
        delta, _ = deform(point, settings['regions'])
        key.co = original.co + inverse @ (delta / scale)
        distances.append(delta.length)
    variant.value = 1.0
    for name, record in preserved.items():
        key = body.data.shape_keys.key_blocks[name]
        assert positions_hash(key) == record['sha256'] and key.value == record['value']
    body['variant'] = settings['variant']
    body['variant_source'] = 'User-validated B+ moderate athletic v1'
    text = bpy.data.texts.new('B+ V2 provenance and settings')
    text.write(json.dumps(settings, indent=2))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output), compress=True)
    report = {'source_sha256': digest(args.blend), 'settings_sha256': digest(args.settings),
              'variant_sha256': digest(args.output), 'settings': settings,
              'method': 'additional symmetric volume fields on shape key relative to unchanged validated B+; before original Multires 3',
              'source_shape_key': source_key.name, 'variant_shape_key': variant.name,
              'variant_relative_key': variant.relative_key.name, 'preserved_shape_keys': preserved,
              'shape_key_sha256': positions_hash(variant),
              'vertices': len(body.data.vertices), 'faces': len(body.data.polygons),
              'maximum_additional_cage_displacement_at_height_1_8': max(distances),
              'changed_vertices_above_1e_6': sum(d > 1e-6 for d in distances),
              'new_vertices': 0, 'new_faces': 0, 'application_integrated': False}
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'settings'}, indent=2))


if __name__ == '__main__':
    main()
