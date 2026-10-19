"""Record finite coordinates, collapsed triangles and winding; not medical certification."""
import argparse, json, sys
from pathlib import Path
import bpy
import numpy as np

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--prepared', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
bpy.ops.wm.open_mainfile(filepath=str(a.prepared / 'muscles-only.blend'), use_scripts=False)
rows = []
for ob in bpy.context.scene.objects:
    if ob.type != 'MESH':
        continue
    mesh = ob.data
    mesh.calc_loop_triangles()
    xyz = np.empty(len(mesh.vertices) * 3, dtype=np.float64)
    mesh.vertices.foreach_get('co', xyz)
    xyz = xyz.reshape((-1, 3))
    assert np.isfinite(xyz).all(), ob.name
    indices = np.empty(len(mesh.loop_triangles) * 3, dtype=np.int32)
    mesh.loop_triangles.foreach_get('vertices', indices)
    indices = indices.reshape((-1, 3))
    triangles = xyz[indices]
    cross = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    double_area = np.linalg.norm(cross, axis=1)
    centered = triangles - xyz.mean(axis=0)
    signed_volume = np.einsum('ij,ij->i', centered[:, 0], np.cross(centered[:, 1], centered[:, 2])).sum() / 6
    rows.append({'object': ob.name, 'triangles': len(indices), 'nonfinite_coordinates': 0,
                 'triangles_double_area_le_1e-12_m2': int(np.count_nonzero(double_area <= 1e-12)),
                 'minimum_double_area_m2': float(double_area.min()),
                 'signed_volume_m3': float(signed_volume)})
report = {'scope': 'Prepared scene only, unchanged topology. No exhaustive intersection, watertightness, raycasting, rig or iPhone performance test.',
          'winding_caveat': 'Signed volume is indicative for open/nonmanifold surfaces; negative volume is not proof of a closed inward shell. Source winding is preserved.',
          'objects': rows, 'totals': {'objects': len(rows), 'triangles': sum(r['triangles'] for r in rows),
                                      'nonfinite_coordinates': 0,
                                      'near_collapsed_triangles': sum(r['triangles_double_area_le_1e-12_m2'] for r in rows),
                                      'objects_negative_signed_volume': sum(r['signed_volume_m3'] < -1e-10 for r in rows)}}
a.output.write_text(json.dumps(report, indent=2) + '\n')
print('GEOMETRY', json.dumps(report['totals']), flush=True)
