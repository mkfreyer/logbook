"""Project guides and reject occluded candidate texels on the unmodified mesh."""
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
OUT=ROOT/'docs/m4c/meshy-posterieur-droit-arrondi'
blend=ROOT/'docs/m4c/meshy-deltoides-residu-local/meshy-residu-corrige.blend'
guide=json.loads((OUT/'outline-guides.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(blend),use_scripts=False)
s=bpy.context.scene
camera(s,-135,(-.225,.555,-.055),.36,(1000,1000))
bpy.context.view_layer.update()
assert [list(row) for row in s.camera.matrix_world]==guide['cameraMatrix']
mesh=bpy.data.objects['MESHY_M4C'].data
tree=BVHTree.FromPolygons([v.co[:] for v in mesh.vertices],[p.vertices[:] for p in mesh.polygons],all_triangles=True)
rotation=s.camera.rotation_euler.to_matrix()
direction=rotation@Vector((0,0,-1))
uv=np.load(ROOT/'docs/m4c/meshy-huit-zones/source-uv-binding.npz')['uv_blender'].copy()
uv[:,:,1]=1-uv[:,:,1]
vertices=np.array([[v.co.x,v.co.z,-v.co.y] for v in mesh.vertices])
faces=np.array([p.vertices[:] for p in mesh.polygons])

def capture(pixel):
    origin=s.camera.location+rotation@Vector(((pixel[0]/1000-.5)*.36,(.5-pixel[1]/1000)*.36,0))
    hit=tree.ray_cast(origin,direction)
    assert hit[0] is not None,('Guide leaves model surface',pixel)
    point=np.array([hit[0].x,hit[0].z,-hit[0].y])
    tri=vertices[faces[hit[2]]]
    ab=np.linalg.lstsq(np.column_stack([tri[1]-tri[0],tri[2]-tri[0]]),point-tri[0],rcond=None)[0]
    tex=np.r_[1-ab.sum(),ab]@uv[hit[2]]
    return {'pixel':list(pixel),'point':point.tolist(),'face':hit[2],'uv':tex.tolist()}

curve=[capture(pixel) for pixel in guide['curveRawPixels']]
ratio=np.array([499/555,474/527])
probes=[{'annotationPixel':p,**capture(np.array(p)/ratio+np.array([90,278]))} for p in guide['probes']]
candidates=np.load(OUT/'surface-candidates.npz')
visible=[]
errors=[]
for p in candidates['point']:
    b=Vector((float(p[0]),-float(p[2]),float(p[1])))
    hit=tree.ray_cast(b-direction*3,direction)
    error=(hit[0]-b).length if hit[0] is not None else float('inf')
    errors.append(error)
    # Cover the source's thin overlapping surface layers as well; never paint
    # through the body. Seven samples here are hidden by 0.09..1.55 mm only.
    visible.append(error<=.002)
np.savez_compressed(OUT/'surface-visibility.npz',visible=np.array(visible,bool),hitErrorM=np.array(errors))
(OUT/'projected-outline.json').write_text(json.dumps({
    'sourceBlendSha256':sha(blend.read_bytes()),'curveSurfaceSamples':curve,'probes':probes,
    'visibilityMethod':'Orthographic BVH ray per candidate; 2 mm shallow-layer tolerance for existing surface overlaps, within the local contour only.',
    'candidateCount':len(visible),'visibleCount':sum(visible),
    'sourceGeometryChanged':False},indent=2)+'\n')
print('PROJECTED_CURVE_AND_VISIBILITY',len(curve),sum(visible),flush=True)
