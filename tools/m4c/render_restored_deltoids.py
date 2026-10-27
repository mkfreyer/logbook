"""Four confirmation renders of exact 06fa665. Never edits masks or geometry."""
import json,sys
from pathlib import Path
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/m4c'))
from scene import camera,render
from glb_io import sha
BASE=ROOT/'docs/m4c/meshy-posterieurs-harmonises';OUT=ROOT/'docs/m4c/restauration-06fa665';DEST=OUT/'renders'
bpy.ops.wm.open_mainfile(filepath=str(BASE/'meshy-posterieurs-harmonises.blend'),use_scripts=False)
s=bpy.context.scene;mesh=bpy.data.objects['MESHY_M4C'].data
before={}
for name,prop,count,dtype in [('positions','co',3,np.float32),('indices','vertex_index',1,np.uint32)]:
 array=np.empty((len(mesh.vertices) if name=='positions' else len(mesh.loops))*count,dtype);(mesh.vertices if name=='positions' else mesh.loops).foreach_get(prop,array);before[name]=sha(array.tobytes())
reference=json.loads((BASE/'blender-preservation.json').read_text())['after'];assert all(before[k]==reference[k] for k in before)
s.cycles.samples=16;s.cycles.seed=0;s.cycles.use_denoising=False
# The saved master already has all eight SHOW switches on and the validated palette.
meta={'sourceCommit':'06fa665','sourceBlendSha256':sha((BASE/'meshy-posterieurs-harmonises.blend').read_bytes()),'maskEdits':False,'geometryEdits':False,'engine':'Blender 4.3.2 Cycles CPU','samples':16,'frames':[]}
for name,angle in [('face',0),('dos',180),('trois-quarts-gauche',135),('trois-quarts-droit',-135)]:
 camera(s,angle,(0,.555,-.055),.75,(1100,820));render(s,DEST/(name+'.png'))
 meta['frames'].append({'file':name+'.png','cameraMatrix':[list(row) for row in s.camera.matrix_world],'sha256':sha((DEST/(name+'.png')).read_bytes())});(DEST/'render-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
print('RESTORED_REFERENCE_RENDERED',len(meta['frames']),flush=True)
