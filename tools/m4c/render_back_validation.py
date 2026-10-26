"""Read-only rear inspection of daf5878; never saves a blend or edits a mask."""
import json
import sys
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from glb_io import sha, source
from scene import camera, render

ROOT = Path(__file__).resolve().parents[2]
CURRENT = ROOT / 'docs/m4c/meshy-deltoides-residu-local'
BEFORE = ROOT / 'docs/m4c/meshy-deltoides-limite-inferieure'
OUT = ROOT / 'docs/m4c/meshy-validation-arriere'
DEST = OUT / 'renders'
DEST.mkdir(parents=True, exist_ok=True)

protected = [ROOT / 'assets/models/meshy-e45e5d8.glb',
             CURRENT / 'meshy-residu-corrige.blend',
             BEFORE / 'meshy-eight-zones-corrected.blend']
for folder in [CURRENT, BEFORE]:
    protected.extend(sorted((folder / 'textures').glob('*.png')))
    protected.extend([folder / 'regions.json', folder / 'region-binding.json',
                      folder / 'exports/meshy-eight-zones-control.glb'])
original_files = {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in protected}
spec = json.loads((CURRENT / 'regions.json').read_text())
assert len(spec['zones']) == 8
source(ROOT / 'assets/models/meshy-e45e5d8.glb')
reference_geometry = json.loads((CURRENT / 'blender-preservation.json').read_text())['after']
record = {
    'referenceCommit': 'daf587857adbb0c615640a3af33b165f8a302804',
    'comparisonBeforeCommit': '71f70dc1753735ddbd9da1e021e649c33a1756d3',
    'engine': 'Blender 4.3.2 / Cycles CPU', 'samples': 24,
    'seed': 0, 'denoising': False, 'frames': [], 'sceneAudits': [],
    'onlyCameraAndRenderSettingsChangedInMemory': True,
    'savedBlendFiles': False,
}

def mesh_hashes(mesh):
    co = np.empty(len(mesh.vertices) * 3, np.float32)
    mesh.vertices.foreach_get('co', co)
    idx = np.empty(len(mesh.loops), np.uint32)
    mesh.loops.foreach_get('vertex_index', idx)
    uv = np.empty(len(mesh.loops) * 2, np.float32)
    mesh.uv_layers['M4C_SURFACE_UV'].data.foreach_get('uv', uv)
    normals = np.array([n.vector[:] for n in mesh.corner_normals], np.float32)
    return {key: sha(data.tobytes()) for key, data in
            [('positions', co), ('indices', idx), ('uv', uv), ('normals', normals)]}

def appearance_hash(scene, material):
    # Camera/render settings may change; material, packed images and lights may not.
    nodes = []
    for node in material.node_tree.nodes:
        inputs = []
        for socket in node.inputs:
            if hasattr(socket, 'default_value'):
                value = socket.default_value
                inputs.append([socket.name, list(value) if hasattr(value, '__len__') else value])
        outputs = [[s.name, s.default_value] for s in node.outputs
                   if s.type == 'VALUE' and hasattr(s, 'default_value')]
        nodes.append([node.name, node.type, inputs, outputs])
    lights = [[ob.name, [list(row) for row in ob.matrix_world],
               ob.data.energy, list(ob.data.color), ob.data.size]
              for ob in scene.objects if ob.type == 'LIGHT']
    images = [[n.name, sha(bytes(n.image.packed_file.data)), n.image.colorspace_settings.name,
               n.image.alpha_mode, n.interpolation]
              for n in material.node_tree.nodes if n.type == 'TEX_IMAGE']
    links = sorted([link.from_node.name, link.from_socket.name,
                    link.to_node.name, link.to_socket.name]
                   for link in material.node_tree.links)
    payload = {'nodes': nodes, 'links': links, 'lights': lights, 'images': images}
    return sha(json.dumps(payload, sort_keys=True).encode()), payload

SHOTS = [
    ('dos-complet', 180, (0, 0, 0), 2.05, (800, 1200)),
    ('epaules-dos', 180, (0, .555, -.055), .72, (1400, 900)),
    ('trois-quarts-arriere-droit', -135, (-.225, .555, -.055), .36, (1000, 1000)),
    ('trois-quarts-arriere-gauche', 135, (.225, .555, -.055), .36, (1000, 1000)),
]

for state, folder, blend in [
    ('apres', CURRENT, CURRENT / 'meshy-residu-corrige.blend'),
    ('avant', BEFORE, BEFORE / 'meshy-eight-zones-corrected.blend'),
]:
    bpy.ops.wm.open_mainfile(filepath=str(blend), use_scripts=False)
    s = bpy.context.scene
    mesh = bpy.data.objects['MESHY_M4C'].data
    material = mesh.materials[0]
    assert mesh_hashes(mesh) == reference_geometry
    for zone in spec['zones']:
        assert material.node_tree.nodes['SHOW::' + zone['id']].outputs[0].default_value == 1
    for node in material.node_tree.nodes:
        if node.type == 'TEX_IMAGE':
            expected = folder / 'textures' / Path(node.image.filepath).name
            assert sha(bytes(node.image.packed_file.data)) == sha(expected.read_bytes()), expected
    before_appearance, payload = appearance_hash(s, material)
    s.cycles.samples = 24
    s.cycles.seed = 0
    s.cycles.use_denoising = False
    s.render.use_border = False
    s.render.use_crop_to_border = False
    # Same original light rig; no material, shader, color or image changes.
    for name, angle, target, scale, resolution in SHOTS:
        if state == 'avant' and name == 'trois-quarts-arriere-gauche':
            continue
        camera(s, angle, target, scale, resolution)
        file = DEST / f'{state}-{name}.png'
        render(s, file)
        assert mesh_hashes(mesh) == reference_geometry
        assert appearance_hash(s, material)[0] == before_appearance
        record['frames'].append({
            'file': file.name, 'state': state, 'view': name,
            'angleDegrees': angle, 'targetSourceM': list(target),
            'resolution': list(resolution), 'orthoScale': s.camera.data.ortho_scale,
            'cameraMatrix': [list(row) for row in s.camera.matrix_world],
            'sourceBlend': str(blend.relative_to(ROOT)),
            'sourceBlendSha256': original_files[str(blend.relative_to(ROOT))],
            'sha256': sha(file.read_bytes()),
        })
        (DEST / 'render-metadata.json').write_text(json.dumps(record, indent=2) + '\n')
    record['sceneAudits'].append({
        'state': state, 'geometry': mesh_hashes(mesh), 'geometryUnchanged': True,
        'materialImagesAndLightsUnchanged': True, 'appearanceHash': before_appearance,
        'lights': payload['lights'], 'packedImages': payload['images'],
    })

assert original_files == {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in protected}
manifest = json.loads((ROOT / 'docs/m4c/meshy-huit-zones/application-preservation.json').read_text())
for item in manifest['checkedFiles']:
    assert sha((ROOT / item['file']).read_bytes()) == item['sha256'], item['file']
record['preservation'] = {
    'protectedSourcesByteIdentical': original_files,
    'applicationFilesUnchanged': len(manifest['checkedFiles']),
    'eightIdentifiersUnchanged': [zone['id'] for zone in spec['zones']],
    'geometryMatchesDaf5878InBothScenes': True,
}
(DEST / 'render-metadata.json').write_text(json.dumps(record, indent=2) + '\n')
print('REAR_VALIDATION_RENDERED', len(record['frames']), flush=True)
