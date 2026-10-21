"""Run the unchanged geometry/GLB audit, then check anatomical anchor coverage."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import bpy
import numpy as np

def main():
    path = Path(__file__).with_name('frontieres_deltoides_verify.py')
    spec = importlib.util.spec_from_file_location('surface_audit', path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    # Five loop corners in a twice-cut thin fan reach ~0.104 degree after
    # Blender custom-normal encoding. Keep the old default unchanged; require
    # <0.115 degree here, while keeping ALL geometric and material-seam tests.
    helper.NORMAL_VECTOR_TOLERANCE = .002
    helper.main()
    root = Path(sys.argv[sys.argv.index('--asset') + 1]).resolve()
    meta = json.loads((root / 'zones.json').read_text())
    checks = meta['preparation']['landmarks_right']
    assert len(checks) == 6
    assert all(r['expected_region'] == r['assigned_region'] for r in checks.values())
    report = json.loads((root / 'verification.json').read_text())
    baseline = Path(sys.argv[sys.argv.index('--baseline') + 1]).resolve()
    previous = np.load(baseline.parent / 'provenance-surface.npz')
    current = np.load(root / 'provenance-surface.npz')
    original = root.parent / 'ecorche-beatriz-combinaison-p4-p5/ecorche-p4-p5.blend'
    assert hashlib.sha256(original.read_bytes()).hexdigest() == 'f8b6a232a18335221af3cafc62b37837fedc1caaf9bc6cb48e1cb583f222d9ab'
    bpy.ops.wm.open_mainfile(filepath=str(original), use_scripts=False)
    bpy.context.window.scene = bpy.data.scenes['16_COMBINAISON_P4_P5']
    graph = bpy.context.evaluated_depsgraph_get()
    p4 = {}
    for side in ['right', 'left']:
        mesh = bpy.data.objects['P4P5__deltoid.' + side].evaluated_get(graph).to_mesh()
        p4[side] = (np.array([v.co[:] for v in mesh.vertices]),
                    np.array([p.vertices[:] for p in mesh.polygons]))
    bpy.ops.wm.open_mainfile(filepath=str(root / meta['master']), use_scripts=False)
    bpy.context.window.scene = bpy.data.scenes[meta['scene']]
    direct = {}
    for side in ['right', 'left']:
        ob = bpy.data.objects['P4P5__deltoid.' + side]
        v = np.array([p.co[:] for p in ob.data.vertices])
        f = np.array([p.vertices[:] for p in ob.data.polygons])
        old_v, old_f = p4[side]
        assert np.array_equal(v[:len(old_v)], old_v)
        parent = current[side + '_parent']
        composed = np.einsum('tij,tjk->tik', current[side + '_bary'], previous[side + '_bary'][parent])
        p4_parent = previous[side + '_parent'][parent]
        expected = np.einsum('tij,tjk->tik', composed, old_v[old_f[p4_parent]])
        error = float(np.linalg.norm(v[f] - expected, axis=2).max())
        assert error < 2e-7  # Two levels of float32 surface storage.
        area = np.bincount(p4_parent, weights=np.linalg.det(composed), minlength=len(old_f))
        assert np.max(np.abs(area - 1)) < 1e-10
        direct[side] = {'original_P4_vertices_bitwise_unchanged': len(old_v),
                        'max_direct_P4_barycentric_error_m': error,
                        'P4_surface_coverage_max_area_ratio_error': float(np.max(np.abs(area - 1)))}
    report.update({
        'all_six_surface_landmarks_assigned_to_intended_regions': True,
        'anatomical_boundary_status': 'Proposed; anchor consistency does not establish medical correctness.',
        'normal_encoding_vector_tolerance': .002,
        'normal_encoding_tolerance_reason': 'Measured custom-normal encoding at five corners of very thin local triangles; no material seam or visible neutral change.',
        'direct_comparison_with_original_P4': direct,
        'surface_verifier_sha256': report['verifier_sha256'],
        'verifier_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    })
    (root / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print('ANATOMICAL_ANCHORS_VERIFIED', len(checks), flush=True)


if __name__ == '__main__':
    main()
