"""Replace inherited triangle-editing texts with the painted-mask guide; no scene edits."""
import argparse,json,sys
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mesh_io import sha
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prepared',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.prepared.resolve();out=root/'texture-poc'
meta=json.loads((out/'build.json').read_text());file=out/'meshy-painted-mask.blend';before=sha(file.read_bytes())
assert before==meta['blend_sha256'] and not meta.get('documentation_postprocess')
bpy.ops.wm.open_mainfile(filepath=str(file),use_scripts=False)
keep={'LICENCE_ET_PROVENANCE.md','PAINTED_CONTOUR.svg','TEXTURE_POC.json'}
for text in list(bpy.data.texts):
 if text.name not in keep:bpy.data.texts.remove(text)
bpy.data.texts.new('LIRE_MASQUE_PEINT.md').write((out/'README.md').read_text())
bpy.ops.wm.save_as_mainfile(filepath=str(file),compress=True)
meta['blend_sha256']=sha(file.read_bytes());meta['documentation_postprocess']={'script_sha256':sha(Path(__file__).read_bytes()),'input_blend_sha256':before,'final_blend_sha256':meta['blend_sha256'],'operation':'Informational texts only: remove inherited triangle-editing guides and embed current painted-mask guide. No geometry, UV, texture, material or camera edits.'}
(out/'build.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
print('TEXTURE_GUIDE_EMBEDDED',meta['blend_sha256'])
