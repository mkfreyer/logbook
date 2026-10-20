"""Embed the license and editing/export guide after rendering, without mesh edits."""
import argparse,json,sys
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mesh_io import sha
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prepared',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.prepared.resolve()
file=root/'renders/meshy-masques.blend';meta=json.loads((root/'renders/render-metadata.json').read_text())
assert sha(file.read_bytes())==meta['blend_sha256'];before=meta['blend_sha256']
bpy.ops.wm.open_mainfile(filepath=str(file),use_scripts=False)
for name in ['LICENCE_ET_PROVENANCE.md','RAYCAST_ET_EXPORT.md']:
 text=bpy.data.texts.get(name) or bpy.data.texts.new(name);text.clear();text.write((root/name).read_text())
bpy.ops.wm.save_as_mainfile(filepath=str(file),compress=True)
meta['license_and_guide_postprocess']={'script_sha256':sha(Path(__file__).read_bytes()),'input_blend_sha256':before,'embedded_texts':['LICENCE_ET_PROVENANCE.md','RAYCAST_ET_EXPORT.md'],'geometry_operation':False}
meta['blend_sha256']=sha(file.read_bytes());(root/'renders/render-metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
print('MESHY_DOCUMENTS_EMBEDDED',meta['blend_sha256'],flush=True)
