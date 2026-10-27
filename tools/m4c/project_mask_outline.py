"""Read-only projection of a guide and local candidate visibility on source Meshy."""
import argparse
import json
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4c'))
from scene import camera
from glb_io import sha
parser=argparse.ArgumentParser()
parser.add_argument('--asset-dir',type=Path,required=True)
parser.add_argument('--base-blend',type=Path,required=True)
parser.add_argument('--guide',default='lower-contour-guides.json')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
out=args.asset_dir.resolve();blend=args.base_blend.resolve()
guide=json.loads((out/args.guide).read_text())
bpy.ops.wm.open_mainfile(filepath=str(blend),use_scripts=False)
s=bpy.context.scene
camera(s,guide['angleDegrees'],guide['targetSourceM'],guide['orthoScale'],tuple(guide['referenceResolution']))
bpy.context.view_layer.update()
assert [list(row) for row in s.camera.matrix_world]==guide['cameraMatrix']
mesh=bpy.data.objects['MESHY_M4C'].data
tree=BVHTree.FromPolygons([v.co[:] for v in mesh.vertices],[p.vertices[:] for p in mesh.polygons],all_triangles=True)
rotation=s.camera.rotation_euler.to_matrix();direction=rotation@Vector((0,0,-1))
uv=np.load(ROOT/'docs/m4c/meshy-huit-zones/source-uv-binding.npz')['uv_blender'].copy();uv[:,:,1]=1-uv[:,:,1]
vertices=np.array([[v.co.x,v.co.z,-v.co.y] for v in mesh.vertices])
faces=np.array([p.vertices[:] for p in mesh.polygons])

def capture(pixel):
    origin=s.camera.location+rotation@Vector(((pixel[0]/1000-.5)*.36,(.5-pixel[1]/1000)*.36,0))
    hit=tree.ray_cast(origin,direction)
    assert hit[0] is not None,('Guide leaves surface',pixel)
    point=np.array([hit[0].x,hit[0].z,-hit[0].y]);tri=vertices[faces[hit[2]]]
    ab=np.linalg.lstsq(np.column_stack([tri[1]-tri[0],tri[2]-tri[0]]),point-tri[0],rcond=None)[0]
    return {'pixel':list(pixel),'point':point.tolist(),'face':hit[2],
            'uv':(np.r_[1-ab.sum(),ab]@uv[hit[2]]).tolist()}

curve=[capture(p) for p in guide['curveRawPixels']]
ratio=np.array(guide['annotationScale']);origin=np.array(guide['cropOrigin'])
probes=[{'annotationPixel':p,**capture(np.array(p)/ratio+origin)} for p in guide['probes']]
candidate=np.load(out/'surface-candidates.npz');visible=[];errors=[]
for p in candidate['point']:
    b=Vector((float(p[0]),-float(p[2]),float(p[1])))
    hit=tree.ray_cast(b-direction*3,direction)
    error=(hit[0]-b).length if hit[0] is not None else float('inf')
    errors.append(error);visible.append(error<=.002)
np.savez_compressed(out/'surface-visibility.npz',visible=np.array(visible,bool),hitErrorM=np.array(errors))
(out/'projected-outline.json').write_text(json.dumps({
    'sourceBlendSha256':sha(blend.read_bytes()),'curveSurfaceSamples':curve,'probes':probes,
    'visibilityMethod':'Orthographic BVH ray per candidate, 2mm local depth tolerance for existing thin overlapping layers.',
    'candidateCount':len(visible),'visibleCount':sum(visible),'sourceGeometryChanged':False},indent=2)+'\n')
print('PROJECTED_LOWER_CONTOUR',len(curve),sum(visible),flush=True)
