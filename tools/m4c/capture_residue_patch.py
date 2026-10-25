"""Read-only ray sampling of the small annotated right-deltoid residue."""
import sys,json
from pathlib import Path
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'tools/m4c'));from scene import camera
bpy.ops.wm.open_mainfile(filepath=str(root/'docs/m4c/meshy-deltoides-limite-inferieure/meshy-eight-zones-corrected.blend'),use_scripts=False)
s=bpy.context.scene;o=bpy.data.objects['MESHY_M4C'];camera(s,-45,(-.225,.555,-.055),.29,(640,640))
bpy.context.view_layer.update()
tree=BVHTree.FromPolygons([v.co[:] for v in o.data.vertices],[p.vertices[:] for p in o.data.polygons],all_triangles=True);rot=s.camera.rotation_euler.to_matrix();direction=rot@Vector((0,0,-1));rows=[]
for y in range(430,482,2):
 for x in range(198,246,2):
  hit=tree.ray_cast(s.camera.location+rot@Vector(((x/640-.5)*.29,(.5-y/640)*.29,0)),direction)
  if hit[0]:
   p=hit[0];rows.append({'pixel':[x,y],'point':[p.x,p.z,-p.y],'face':hit[2]})
out=root/'docs/m4c/meshy-deltoides-residu-local'
(out/'surface-samples.json').write_text(json.dumps(rows,indent=2)+'\n')
(out/'patch-guides.json').write_text(json.dumps({'referenceCommit':'71f70dc','anatomicalSide':'right','camera_matrix':[list(row) for row in s.camera.matrix_world],'frameSize':[640,640],'orthoScale':.29,'boundaryYX':[[442,215],[448,217],[454,220],[460,224],[466,228],[472,230],[476,232]],'onlyTransition':[8,0],'visibilityDistanceM':.003,'supportBoxM':{'min':[-.267,.480,-.124],'max':[-.231,.504,-.078]}},indent=2)+'\n')
