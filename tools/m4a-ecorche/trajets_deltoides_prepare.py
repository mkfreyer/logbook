"""Extract the unchanged 0ab3d83 shoulder and its original orthographic camera."""
import argparse, hashlib, json, sys
from pathlib import Path
import bpy, numpy as np

p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.output.mkdir(parents=True,exist_ok=True)
assert hashlib.sha256(a.baseline.read_bytes()).hexdigest()=='f8b6a232a18335221af3cafc62b37837fedc1caaf9bc6cb48e1cb583f222d9ab'
bpy.ops.wm.open_mainfile(filepath=str(a.baseline.resolve()),use_scripts=False)
s=bpy.data.scenes['16_COMBINAISON_P4_P5'];bpy.context.window.scene=s;s.view_layers[0].update()
ob=s.objects['P4P5__deltoid.right'];g=bpy.context.evaluated_depsgraph_get();ev=ob.evaluated_get(g);m=ev.to_mesh()
v=np.array([ob.matrix_world@x.co for x in m.vertices]);f=np.array([x.vertices[:]for x in m.polygons],np.int32)
cam=s.objects['P4P5_epaule-droite'];basis=np.array(cam.matrix_world.to_3x3());origin=np.array(cam.location)
np.savez_compressed(a.output/'source.npz',v=v,f=f,basis=basis,cam=origin)
print('PREPARED',len(v),len(f),flush=True)
