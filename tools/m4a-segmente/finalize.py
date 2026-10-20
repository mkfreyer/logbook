"""Check the finished review package and write its SHA-256 manifest."""
from pathlib import Path
import hashlib,json,re,subprocess
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/m4a/segmente'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
proof=json.loads((OUT/'verification.json').read_text())
assert proof['glb_sha256']==sha(OUT/'pilote-haut-corps.glb')
assert proof['blend_sha256']==sha(OUT/'pilote-haut-corps.blend')
frames=json.loads((OUT/'render-metadata.json').read_text())['frames'];assert len(frames)==18
expected={m+'.'+s for m in ['pectoralis','deltoid','biceps','triceps'] for s in ['left','right']}
assert {f['selected'] for f in frames if f['selected']}==expected
for f in frames:
    with Image.open(OUT/'renders'/f['file']) as im:assert im.size==(780,1000)
assert len(proof['first_hit_selection_probes'])==8
validation=json.loads((OUT/'gltf-validation.json').read_text());assert validation['issues']['numErrors']==0 and validation['issues']['numWarnings']==0
for doc in [ROOT/'docs/M4A_PILOTE_SEGMENTE.md',OUT/'README.md',OUT/'LICENCE.md',OUT/'ARCHIVES.md']:
    for target in re.findall(r'\]\(([^)]+)\)',doc.read_text()):
        if '://' not in target and not target.startswith('#'):assert (doc.parent/target).exists(),(doc,target)
changed=subprocess.check_output(['git','diff','--name-only','7c2aa5c'],cwd=ROOT,text=True).splitlines()
changed+=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
assert all(p=='docs/M4A_PILOTE_SEGMENTE.md' or p.startswith(('docs/m4a/segmente/','tools/m4a-segmente/')) for p in changed)
files=[ROOT/'docs/M4A_PILOTE_SEGMENTE.md']+list(OUT.rglob('*'))+list((ROOT/'tools/m4a-segmente').rglob('*'))
records=[]
for p in sorted(files):
    if not p.is_file() or p.name=='manifest.json' or p.suffix in ['.pyc','.blend1','.blend2'] or '__pycache__' in p.parts or p.name.startswith('preview-'):continue
    records.append(dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=sha(p)))
(OUT/'manifest.json').write_text(json.dumps(dict(schema=1,base_commit='7c2aa5c',source_sha256='9fab861a65407e69b9401bec077bf7b40f58d36404e80bad9db6147f24320a14',render_count=18,selection_count=8,application_changed=False,files=records),indent=2)+'\n')
print('PACKAGE_VERIFIED',len(records),'files; 18 renders; 8 selections; app unchanged')
