"""Exact assembly of the approved groin body and the existing foot proposal.

No sculpting, vertex edits, smoothing, normal recalculation or topology changes.
"""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import bpy


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--body', type=Path, required=True)
    parser.add_argument('--feet', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=True)
    body, feet = args.body.resolve(), args.feet.resolve()
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    body_meta = json.loads((body.parent/'finition.json').read_text())
    foot_meta = json.loads((feet.parent/'finition.json').read_text())
    assert sha(body) == body_meta['master_sha256']
    assert sha(feet) == foot_meta['master_sha256']
    ids = set(foot_meta['changed_objects'])
    assert ids == {'m2_c001.left', 'm2_c001.right'}
    bpy.ops.wm.open_mainfile(filepath=str(body), use_scripts=False)
    source = bpy.data.scenes[body_meta['scene']]
    existing_materials = {m.name: m for m in bpy.data.materials}
    original_feet = {o['asset_id']: o for o in source.objects if o.get('asset_id') in ids}
    with bpy.data.libraries.load(str(feet), link=False) as (available, requested):
        names = ['PIEDS__'+key for key in sorted(ids)]
        assert all(name in available.objects for name in names)
        requested.objects = names
    imported = requested.objects
    assert {o['asset_id'] for o in imported} == ids
    scene = bpy.data.scenes.new('27_PIEDS_AINE_VALIDEE')
    scene.use_fake_user = True
    scene.world = source.world
    scene.camera = source.camera
    for ob in source.objects:
        if ob.get('asset_id') not in ids:
            scene.collection.objects.link(ob)
    for ob in imported:
        # Appending brings duplicate neutral materials. Reuse the identical
        # canonical body material; never rebuild normals or mesh data.
        original = original_feet[ob['asset_id']]
        assert len(original.material_slots) == len(ob.material_slots)
        for index, slot in enumerate(ob.material_slots):
            target = original.material_slots[index].material
            assert target.name in existing_materials
            slot.material = target
        scene.collection.objects.link(ob)
    bpy.context.window.scene = scene
    meta = {
        **foot_meta,
        'baseline_commit': '41896cc1d606295b9ea8286e5569a6a964c20fb2',
        'baseline_master': os.path.relpath(body, root),
        'baseline_glb': os.path.relpath(body.parent/'ecorche-aine-homogene.glb', root),
        'baseline_blend_sha256': sha(body),
        'source_scene': source.name,
        'donor_commit': '8a8b95ed31aeddff47bd038ac09183273009edf3',
        'donor_master': os.path.relpath(feet, root),
        'donor_scene': foot_meta['scene'],
        'donor_blend_sha256': sha(feet),
        'scene': scene.name,
        'master': 'ecorche-pieds-aine-validee.blend',
        'export_file': 'ecorche-pieds-aine-validee.glb',
        'method': 'Exact datablock assembly: body and groin from 41896cc; two existing foot objects from 8a8b95e. No new geometry or shading edits.',
        'export_modifications': 'Exact assembly: 297 body objects including groin unchanged from 41896cc; two foot objects unchanged from 8a8b95e, including normals and topology. No new sculpting.',
        'builder_sha256': sha(Path(__file__)),
        'new_geometry_edits': False,
    }
    meta.pop('master_sha256', None)
    bpy.data.texts.new('ASSEMBLAGE_PIEDS_AINE.json').write(json.dumps(meta, indent=2))
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(root/meta['master']), compress=True)
    meta['master_sha256'] = sha(root/meta['master'])
    (root/'finition.json').write_text(json.dumps(meta, indent=2)+'\n')
    print('ASSEMBLED', meta['master_sha256'], flush=True)


if __name__ == '__main__':
    main()
