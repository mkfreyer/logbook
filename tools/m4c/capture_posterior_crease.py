"""Capture surface crease landmarks and annotated-view probes on 8b723d9."""
import sys,json
from pathlib import Path
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'tools/m4c'))
from scene import camera
bpy.ops.wm.open_mainfile(filepath=str(root/'docs/m4c/meshy-huit-zones/meshy-eight-zones.blend'),use_scripts=False)
s=bpy.context.scene;o=bpy.data.objects['MESHY_M4C'];tree=BVHTree.FromPolygons([v.co[:] for v in o.data.vertices],[p.vertices[:] for p in o.data.polygons],all_triangles=True)
result={}
for side,sign in [('right',-1),('left',1)]:
 camera(s,sign*45,(sign*.225,.555,-.055),.29,(640,640));rotation=s.camera.rotation_euler.to_matrix();direction=rotation@Vector((0,0,-1));records=[]
 for px,py in [(215,465),(225,466),(240,495),(255,522),(267,545)]:
  if side=='left':px=640-px
  origin=s.camera.location+rotation@Vector(((px/640-.5)*.29,(.5-py/640)*.29,0))
  hit=tree.ray_cast(origin,direction);assert hit[0],(side,px,py)
  p=hit[0];records.append({'pixel':[px,py],'pointGLB':[p.x,p.z,-p.y],'sourceFace':hit[2]})
 result[side]=records
path=root/'docs/m4c/meshy-deltoides-limite-inferieure/crease-landmarks.json';path.write_text(json.dumps({'referenceCommit':'8b723d9','cameraSource':'deltoide-droit-avant / deltoide-gauche-avant; original cameras retained','role':'Proposed superficial deltoid/upper-arm crease; source geometry is stylized, no definitive triceps ID assigned.','sides':result},indent=2)+'\n')
probes=[]
for side,sign in [('right',-1),('left',1)]:
 camera(s,sign*45,(sign*.225,.555,-.055),.29,(640,640));rotation=s.camera.rotation_euler.to_matrix();direction=rotation@Vector((0,0,-1))
 for px,py in [(220,490),(235,510)]:
  if side=='left':px=640-px
  hit=tree.ray_cast(s.camera.location+rotation@Vector(((px/640-.5)*.29,(.5-py/640)*.29,0)),direction);assert hit[0]
  q=hit[0];probes.append({'side':side,'referencePixel':[px,py],'pointGLB':[q.x,q.z,-q.y],'sourceFace':hit[2]})
(root/'docs/m4c/meshy-deltoides-limite-inferieure/annotated-surface-probes.json').write_text(json.dumps(probes,indent=2)+'\n')
print('CREASE_AND_INTERIOR_PROBES_CAPTURED',flush=True)
