#!/usr/bin/env python3
"""Verify M4A S1/S2/S3 artifacts, common render protocol and historical preservation."""
import ast,hashlib,json,re,subprocess
from pathlib import Path
from PIL import Image
repo=Path(__file__).resolve().parents[2];root=repo/'docs/m4a/stylized'
baseline='b905fb0498c8085837e978282421c48fef791a26'
scripts=['build_stylized_anatomy.py','render_stylized_anatomy.py','check_stylized_anatomy.py',
         'audit_stylized_review.py','make_stylized_sheets.py','validate_stylized_delivery.py']

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def git(*args):return subprocess.check_output(['git',*args],cwd=repo).decode().strip()

historical=git('ls-tree','-r','--name-only',baseline,'docs/m4a','tools/m4a').splitlines()
for name in historical:assert git('rev-parse',baseline+':'+name)==git('hash-object',name),name
for name in scripts:ast.parse((repo/'tools/m4a'/name).read_text())
protocols=[];summaries={};input_hashes=set();views={'front','three-quarter','back','side','selection'}
review=read(root/'review-validation.json')
for v in ['s1','s2','s3']:
    folder=root/v;c=read(folder/'construction.json');g=read(folder/'geometry-check.json');r=read(folder/'render-metadata.json')
    assert c['generator_sha256']==sha(repo/'tools/m4a/build_stylized_anatomy.py')
    assert c['L1_L2_L3_assets_read'] is False and c['skeleton_organs_face_muscles_read_into_output'] is False
    assert c['license']=='CC-BY-SA-4.0';input_hashes.add(c['source_sha256'])
    assert c['counts']['triangles']==g['visible_triangles'] and c['counts']['triangles']<=112000
    assert c['counts']['visible_objects']==g['visible_objects']
    assert g['source_blend_sha256']==r['source_sha256']==sha(folder/'model.blend')
    assert all(x['nonfinite_coordinates']==x['near_degenerate_triangles']==x['loose_vertices']==0 for x in g['objects'])
    if v=='s1':assert g['all_union_faces_used_exactly_once'] and g['continuous_source']['nonmanifold_edges']==0
    if v=='s2':assert g['nonmanifold_visible_edges']==0
    if v=='s3':assert g['nonmanifold_visible_edges']==1522
    assert r['protocol']['renderer_sha256']==sha(repo/'tools/m4a/render_stylized_anatomy.py')
    assert r['protocol']['resolution']==[720,1152] and r['protocol']['samples']==96
    assert r['protocol']['AI_generated_images'] is False and r['protocol']['license']=='CC-BY-SA-4.0'
    assert len(r['frames'])==5 and {f['view'] for f in r['frames']}==views
    assert r['orange_zones']==['pectoralis.left','pectoralis.right']
    expected={o['object'] for o in c['objects'] if o['zone'] in r['orange_zones']}
    assert len(expected)==(6 if v=='s3' else 2)
    for frame in r['frames']:
        file=folder/frame['path'];assert sha(file)==frame['sha256']
        with Image.open(file) as im:assert im.size==(720,1152);im.verify()
        assert set(frame['orange_objects'])==(expected if frame['view']=='selection' else set())
    assert sha(folder/'scene-review.blend')==r['review_scene']['sha256']
    assert review[v]['source_review_geometry_normals_semantics_identical']
    protocols.append(r['protocol']);summaries[v]={'triangles':g['visible_triangles'],
       'objects':g['visible_objects'],'selectable_objects':c['counts']['selectable_objects'],
       'zone_ids':c['counts']['selectable_zone_ids'],
       'nonmanifold_edges':g.get('nonmanifold_visible_edges',g.get('continuous_source',{}).get('nonmanifold_edges'))}
assert len(input_hashes)==1 and protocols[0]==protocols[1]==protocols[2]
assert len({r['geometry_signature_sha256'] for r in review.values()})==3
sheets=read(root/'sheets-metadata.json');assert len(sheets['sources'])==15 and not sheets['anatomy_repainted']
for source in sheets['sources']:assert sha(root/source['file'])==source['sha256']
assert len(list(root.rglob('*.png')))==22
for p in root.glob('*.png'):
    with Image.open(p) as im:im.verify()
assert not list(root.rglob('*.blend1')) and not list(root.rglob('*.part'))
for name in ['CC-BY-SA-4.0.txt','Ecorche-LICENSE.md','Ecorche-ATTRIBUTION.md']:
    assert (root/'licenses'/name).read_bytes()==(repo/'docs/m4a/ecorche/licenses'/name).read_bytes()
for p in [repo/'docs/M4A_S1_S2_S3.md',root/'README.md',root/'ATTRIBUTION.md']:
    for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        if not target.startswith(('http:','https:','#')):
            resolved=(p.parent/target.split('#')[0]).resolve()
            assert resolved.exists() or resolved in {root/'manifest.json',root/'validation.json'},(p,target)
report={'baseline':baseline,'historical_files_verified_unchanged':len(historical),'variants':summaries,
        'input_anatomical_source_same':True,'three_different_geometry_signatures':True,
        'source_review_geometry_normals_zone_semantics_identical':True,
        'common_blender_protocol':True,'blender_pngs_verified':15,'comparison_sheets_verified':7,
        'orange_is_real_3d_objects':True,'licenses_and_attribution_preserved':True,
        'application_integration':False,'M4B':False,'mobile_benchmark':False,
        'limitations':['S1 closed union retains three components and residual tunnels; regions provisional.',
        'S2/S3 overlapping anatomical masses are not a final surface partition.',
        'S3 retains 1522 nonmanifold edges; cleanup required.',
        'No exhaustive intersection, rig, medical or iPhone performance validation.']}
(root/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
files=list(root.rglob('*'))+[repo/'docs/M4A_S1_S2_S3.md']+[repo/'tools/m4a'/name for name in scripts]
manifest=[{'path':str(p.relative_to(repo)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(files) if p.is_file() and p!=root/'manifest.json']
(root/'manifest.json').write_text(json.dumps({'algorithm':'SHA-256','license_for_derived_assets':'CC-BY-SA-4.0','files':manifest},indent=2)+'\n')
print(json.dumps(report,indent=2))
