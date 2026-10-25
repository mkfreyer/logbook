"""Run source-surface checks and verify preservation against dbba75e."""
import argparse,json,sys
from pathlib import Path
import bpy,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from assemble_head import sha
from check_head_assembly import main as source_checks,triangle_keys
source_checks()
p=argparse.ArgumentParser();p.add_argument('--asset',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.asset.resolve()
meta=json.loads((root/'assemblage.json').read_text());report=json.loads((root/'verification.json').read_text())
before,after=[bpy.data.scenes[meta[k]] for k in ['scene_before','scene_after']]
a0,a1=[next(o for o in s.objects if o.type=='MESH') for s in [before,after]]
v0,v=[np.array([x.co[:] for x in o.data.vertices]) for o in [a0,a1]]
f0,f=[np.array([x.vertices[:] for x in o.data.polygons],np.int32) for o in [a0,a1]]
nbv=meta['protected_body_vertices'];nbf=meta['retained_body_triangles_after_cut']
assert np.array_equal(v0[:nbv],v[:nbv]) and np.array_equal(f0[:nbf],f[:nbf])
plane=np.array(meta['head_cut_plane_normal']);offset=meta['head_cut_plane_offset_m']
protected=(v0[f0]@plane>offset+1e-6).all(1)
protected_new=(v[f]@plane>offset+1e-6).all(1)
assert np.array_equal(triangle_keys(v0[f0[protected]]),triangle_keys(v[f[protected_new]]))
n0,n=[np.array([x.vector[:] for x in o.data.corner_normals]).reshape(-1,3,3) for o in [a0,a1]]
normal_error=float(np.linalg.norm(n[:nbf]-n0[:nbf],axis=2).max())
assert normal_error<.001
assert np.array_equal(v0.min(0),v.min(0)) and np.array_equal(v0.max(0),v.max(0))
report.update({'reference_commit':'dbba75e','protected_body_mesh_vertices':nbv,'protected_body_mesh_vertices_moved':0,
 'body_triangle_connectivity_identical':True,'upper_head_original_whole_triangles_preserved':int(protected.sum()),
 'upper_face_and_hair_surface_exact':True,'global_bounds_exact':True,
 'protected_body_corner_normal_error_max':normal_error,
 'triangles_before':len(f0),'triangles_after':len(f),'triangle_delta':len(f)-len(f0),
 'topology_change_scope':meta['topology_change_scope'],'local_z_range_m':meta['local_z_range_m'],
 'local_verifier_sha256':sha(Path(__file__))})
(root/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
print('LOCAL_VERIFIED',json.dumps(report),flush=True)
