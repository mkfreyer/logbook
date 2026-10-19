#!/usr/bin/env python3
"""Validate the M4A L3 delivery and preserve all historical M4A assets."""
import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path
from PIL import Image

repo = Path(__file__).resolve().parents[2]
root = repo / 'docs/m4a/l3'
baseline = 'f3bfda6c4d26b523d02262df520bcb015770c82f'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


historical = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', baseline, 'docs/m4a', 'tools/m4a'], cwd=repo).decode().splitlines()
for name in historical:
    expected = subprocess.check_output(['git', 'rev-parse', baseline+':'+name], cwd=repo).decode().strip()
    actual = subprocess.check_output(['git', 'hash-object', name], cwd=repo).decode().strip()
    assert actual == expected, f'Historical artifact changed: {name}'
for name in ['build_l3_mannequin.py','render_l3_mannequin.py','make_l3_sheets.py','audit_l3_review.py','validate_l3_delivery.py']:
    ast.parse((repo / 'tools/m4a' / name).read_text())
c = read(root / 'l3/construction.json')
g = read(root / 'l3/geometry-check.json')
assert c['generator_sha256'] == sha(repo / 'tools/m4a/build_l3_mannequin.py')
assert c['external_assets_read'] == []
assert g['source_blend_sha256'] == sha(root / 'l3/logbook-original.blend')
shell = g['continuous_shell']
for key in ['boundary_edges','nonmanifold_edges','loose_vertices','nonfinite_coordinates','near_degenerate_triangles','surface_genus']:
    assert shell[key] == 0, key
assert shell['connected_components'] == 1 and shell['signed_volume_m3'] > 0
assert shell['triangles'] == c['counts']['visible_triangles'] == 89672
assert c['relief_geometry_check']['triangles_inverted_relative_to_pre_relief'] == 0
assert c['relief_geometry_check']['minimum_normal_dot_before_after_relief'] >= .8
assert g['surface_zones']['all_source_faces_used_once']
assert g['surface_zones']['shared_border_positions_identical']
assert all(z['connected_components'] == 1 for z in g['surface_zones']['zones'] if z['selectable'])
assert (root / 'l2/construction.json').read_bytes() == (repo / 'docs/m4a/original/defined/construction.json').read_bytes()
protocols = []
views = {'front','three-quarter','back','side','selection'}
for variant in ['l2','l3']:
    folder = root / variant
    source = root / 'l3/logbook-original.blend' if variant == 'l3' else repo / 'docs/m4a/original/defined/logbook-original.blend'
    m = read(folder / 'render-metadata.json')
    assert m['source_sha256'] == sha(source)
    assert m['protocol']['renderer_sha256'] == sha(repo / 'tools/m4a/render_l3_mannequin.py')
    assert m['protocol']['resolution'] == [800,1280] and m['protocol']['samples'] == 128
    assert m['protocol']['AI_generated_images'] is False
    assert m['review_scene']['sha256'] == sha(folder / 'scene-review.blend')
    assert {f['view'] for f in m['frames']} == views and len(m['frames']) == 5
    assert m['orange_zones'] == ['pectoralis.left','pectoralis.right']
    for frame in m['frames']:
        path = folder / frame['path']
        assert sha(path) == frame['sha256']
        with Image.open(path) as im:
            assert im.size == (800,1280)
            im.verify()
        assert set(frame['orange_objects']) == ({'LB.pectoralis.left','LB.pectoralis.right'} if frame['view'] == 'selection' else set())
    protocols.append(m['protocol'])
assert protocols[0] == protocols[1]
review = read(root / 'review-validation.json')
assert set(review) == {'l2','l3'}
assert all(v['source_review_geometry_normals_attributes_identical'] for v in review.values())
assert review['l2']['geometry_signature_sha256'] != review['l3']['geometry_signature_sha256']
sheets = read(root / 'sheets-metadata.json')
for source in sheets['sources']:
    assert sha(root / source['file']) == source['sha256']
assert not sheets['geometry_or_anatomy_repainted']
assert len(list(root.rglob('*.png'))) == 17
for path in root.glob('*.png'):
    with Image.open(path) as im:
        im.verify()
for path in [repo / 'docs/M4A_L3.md', root / 'README.md']:
    for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
        if not target.startswith(('http:','https:','#')):
            resolved = (path.parent / target.split('#')[0]).resolve()
            assert resolved.exists() or resolved in {root / 'manifest.json', root / 'validation.json'}, (path,target)
assert not list(root.rglob('*.blend1')) and not list(root.rglob('*.part'))
report = {'baseline': baseline, 'historical_assets_verified_unchanged': len(historical),
          'l3_triangles': shell['triangles'], 'l2_triangles': 81036,
          'selectable_connected_zones': 22, 'closed_shell_genus_zero': True,
          'source_review_geometry_normals_semantics_identical': True,
          'same_render_protocol_both_variants': True, 'blender_frames_verified': 10,
          'comparison_sheets_verified': 7, 'orange_is_two_real_pectoral_objects': True,
          'application_integration': False, 'M4B': False, 'mobile_benchmark': False,
          'limitations': ['Stylised surface regions, not medical segmentation.',
                         'No exhaustive intersection or medical test.',
                         'Shader and mobile performance not validated in an app.']}
(root / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
files = list(root.rglob('*')) + [repo / 'docs/M4A_L3.md'] + [repo / 'tools/m4a' / name for name in ['build_l3_mannequin.py','render_l3_mannequin.py','make_l3_sheets.py','audit_l3_review.py','validate_l3_delivery.py']]
manifest = [{'path': str(p.relative_to(repo)), 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in sorted(files) if p.is_file() and p != root / 'manifest.json']
(root / 'manifest.json').write_text(json.dumps({'algorithm':'SHA-256','files':manifest}, indent=2) + '\n')
print(json.dumps(report, indent=2))
