"""Verify identical geometry in source and review scenes, including custom normals."""
import argparse, hashlib, json, sys
from pathlib import Path
import bpy
import numpy as np

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root', type=Path, required=True)
a = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
a.root = a.root.resolve()


def signature():
    digest = hashlib.sha256()
    for ob in sorted([o for o in bpy.context.scene.objects if o.type == 'MESH'], key=lambda o: o.name):
        digest.update(ob.name.encode() + b'\0')
        for collection, prop, dtype, length in [(ob.data.vertices, 'co', '<f4', 3),
                                              (ob.data.loops, 'vertex_index', '<i4', 1),
                                              (ob.data.polygons, 'loop_total', '<i4', 1),
                                              (ob.data.corner_normals, 'vector', '<f4', 3)]:
            values = np.empty(len(collection)*length, dtype=dtype)
            collection.foreach_get(prop, values)
            digest.update(values.tobytes())
        for name in ['logbook_surface_zone', 'logbook_source_face', 'logbook_source_vertex']:
            attr = ob.data.attributes.get(name)
            if attr:
                values = np.empty(len(attr.data), dtype='<i4')
                attr.data.foreach_get('value', values)
                digest.update(name.encode() + values.tobytes())
    return digest.hexdigest()


report = {}
for variant in ['l2', 'l3']:
    folder = a.root / variant
    source = folder / 'logbook-original.blend' if variant == 'l3' else a.root.parent / 'original/defined/logbook-original.blend'
    bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
    before = signature()
    bpy.ops.wm.open_mainfile(filepath=str(folder / 'scene-review.blend'), use_scripts=False)
    after = signature()
    assert before == after
    scene = bpy.context.scene
    assert len([o for o in scene.objects if o.type == 'LIGHT']) == 4
    assert len([o for o in scene.objects if o.type == 'CAMERA']) == 1
    assert (scene.render.resolution_x, scene.render.resolution_y) == (800, 1280)
    assert bpy.data.objects['LB.Construction.closed-surface'].hide_render
    visible = [o for o in scene.objects if o.type == 'MESH' and o.get('logbook_render')]
    assert len(visible) == 23 and sum(bool(o.get('logbook_selectable')) for o in visible) == 22
    for ob in visible:
        node = ob.data.materials[0].node_tree.nodes['Principled BSDF']
        assert max(abs(float(x)-y) for x,y in zip(node.inputs['Base Color'].default_value, [.17,.245,.38,1])) < 1e-6
        assert abs(node.inputs['Transmission Weight'].default_value - .035) < 1e-6
        assert abs(node.inputs['Subsurface Weight'].default_value - .05) < 1e-6
    report[variant] = {'source_review_geometry_normals_attributes_identical': True,
                       'geometry_signature_sha256': before, 'studio_lights': 4,
                       'neutral_material_restored': True, 'construction_hidden': True}
(a.root / 'review-validation.json').write_text(json.dumps(report, indent=2) + '\n')
print('L3_REVIEW', json.dumps(report), flush=True)
