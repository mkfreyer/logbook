"""Update informational Blender texts after renders; preserve recorded render input SHA."""
import argparse,json,sys
from pathlib import Path
import bpy,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mesh_io import sha,load_glb
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prepared',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.prepared.resolve();new=root/'correction'
file=new/'renders/meshy-masques.blend';metadata=new/'renders/after-metadata.json';render=json.loads(metadata.read_text())
before=sha(file.read_bytes());assert before==render['input_blend_sha256'] and 'postprocess' not in render
bpy.ops.wm.open_mainfile(filepath=str(file),use_scripts=False)
_,_,v,ix=load_glb(root/'source.glb');mesh=next(o.data for o in bpy.data.scenes['00_NEUTRE'].objects if o.type=='MESH')
assert np.array_equal(np.array([p.co[:] for p in mesh.vertices],dtype='<f4'),v)
assert np.array_equal(np.array([p.vertices[:] for p in mesh.polygons],dtype='<u4'),ix)
for name,path in [('REGIONS.json',new/'regions/regions.json'),('CORRECTION_GUIDE.md',new/'README.md'),('MANUAL_REVIEW.json',new/'manual-review.json')]:
 text=bpy.data.texts.get(name) or bpy.data.texts.new(name);text.clear();text.write(path.read_text())
bpy.ops.wm.save_as_mainfile(filepath=str(file),compress=True)
render['postprocess']={'script_sha256':sha(Path(__file__).read_bytes()),'render_input_blend_sha256':before,'final_blend_sha256':sha(file.read_bytes()),'operation':'Update informational region metadata and correction guide texts only; no material, geometry or scene changes.'}
metadata.write_text(json.dumps(render,ensure_ascii=False,indent=2)+'\n')
print('CORRECTION_TEXTS_UPDATED',render['postprocess']['final_blend_sha256'])
