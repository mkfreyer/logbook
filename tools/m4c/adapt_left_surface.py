"""Reflect geometric guide points, then project on actual left shoulder triangles.

This never reflects texture pixels and never deforms or moves the mannequin.
"""
import json,sys
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/m4c'))
from scene import camera
from glb_io import sha
OUT=ROOT/'docs/m4c/meshy-posterieurs-harmonises'
BASE=ROOT/'docs/m4c/meshy-posterieur-droit-bord-inferieur'
guide=json.loads((OUT/'right-reference-outline.json').read_text())
blend=BASE/'meshy-posterieur-droit-bord-inferieur.blend'
bpy.ops.wm.open_mainfile(filepath=str(blend),use_scripts=False)
s=bpy.context.scene;mesh=bpy.data.objects['MESHY_M4C'].data
vertices=[v.co[:] for v in mesh.vertices];faces=[p.vertices[:] for p in mesh.polygons]
tree=BVHTree.FromPolygons(vertices,faces,all_triangles=True)
left_indices=[i for i,f in enumerate(faces) if all(mesh.vertices[k].co.x>.10 and .42<mesh.vertices[k].co.z<.68 for k in f)]
left_faces=[faces[i] for i in left_indices]
left_tree=BVHTree.FromPolygons(vertices,left_faces,all_triangles=True)
camera(s,-135,(-.225,.555,-.055),.36,(1000,1000));bpy.context.view_layer.update()
assert [list(r) for r in s.camera.matrix_world]==guide['cameraRight']
rotation=s.camera.rotation_euler.to_matrix();direction=rotation@Vector((0,0,-1));samples=[]
cam_left=np.array(guide['cameraLeft'])
for pixel in guide['rightCurveRawPixels']:
    origin=s.camera.location+rotation@Vector(((pixel[0]/1000-.5)*.36,(.5-pixel[1]/1000)*.36,0))
    hit=tree.ray_cast(origin,direction);assert hit[0] is not None
    reflected=Vector((-hit[0].x,hit[0].y,hit[0].z))
    target=left_tree.find_nearest(reflected);assert target[0] is not None and target[3]<.02
    left=np.array(target[0]);q=(left-cam_left[:3,3])@cam_left[:3,:3]
    raw=np.array([(q[0]/.36+.5)*1000,(.5-q[1]/.36)*1000])
    samples.append({'rightPointGLB':[hit[0].x,hit[0].z,-hit[0].y],
        'reflectedPointGLB':[reflected.x,reflected.z,-reflected.y],
        'leftPointGLB':[target[0].x,target[0].z,-target[0].y],
        'leftSourceFace':int(left_indices[target[2]]),'projectionDistanceM':target[3],
        'leftReferencePixel':[1000-raw[0],raw[1]]})
distances=np.array([r['projectionDistanceM'] for r in samples])
(OUT/'surface-adaptation.json').write_text(json.dumps({'referenceCommit':'977f68a',
    'sourceBlendSha256':sha(blend.read_bytes()),'cameraLeft':guide['cameraLeft'],
    'method':'Mirror object-space guide points, nearest projection on real left-shoulder surface; no UV pixel reflection.',
    'meanProjectionDistanceM':float(distances.mean()),'maxProjectionDistanceM':float(distances.max()),
    'samples':samples,'geometryChanged':False},indent=2)+'\n')
print('ADAPTED_LEFT_CURVE',len(samples),distances.mean(),distances.max(),flush=True)
