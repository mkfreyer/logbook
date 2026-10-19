"""Verify published BP3D sources, render provenance, geometry reports and scope.

Passing this check establishes traceability, not visual acceptance. Both delivered
constructions are explicitly rejected as final premium bases in the report.
"""
import argparse,hashlib,json,subprocess,zipfile
from pathlib import Path
from PIL import Image
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path);a=p.parse_args()
repo=Path(__file__).resolve().parents[2];root=repo/'docs/m4a/bp3d-fitness'
def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=repo).decode().strip()
groups=read(root/'groups.json')['groups'];audit=read(repo/'docs/m4a/bodyparts3d/selection-candidate.json')
verified={r['id']:r for r in audit['selection_candidates']}
assert len(groups)==30 and [r['zone_id'] for r in groups]==list(range(1,31))
ids=set()
for r in groups:
 for src in r['sources']:assert src==verified[src['id']]
 elements={e for src in r['sources'] for e in src['element_ids']};assert set(r['element_ids'])==elements
 if not elements:assert r['family'] in ['dorsaux','abdominaux'] and r['source_status']!='verified_BP3D'
 ids|=elements
assert len(ids)==74 and len({r['family'] for r in groups})==15
protocols=[];source_records=[];counts={}
for variant in ['soft','defined']:
 folder=root/variant;c=read(folder/'construction.json');g=read(folder/'geometry-check.json');m=read(folder/'renders/render-metadata.json')
 assert c['generator_sha256']==sha(repo/'tools/m4a/build_bp3d_fitness.py')
 assert c['source_head_sha256']==sha(repo/'docs/m4a/bplus-power/power/model.blend')
 assert m['protocol']['renderer_sha256']==sha(repo/'tools/m4a/render_bp3d_fitness.py')
 assert sha(folder/'model.blend')==g['source_sha256']==m['source_sha256']
 assert c['source_archive_sha256']=='40665852c49f218326590e204db91064a1ecfc3c6f8cbd7bbbcaac62c7cd409e'
 assert len(c['source_records'])==75 and {r['element_id'] for r in c['source_records']}==ids|{'FJ2810'}
 assert len(c['authored_complements'])==4 and c['license_for_derived_models_and_renders']=='CC-BY-SA-4.0'
 assert c['counts']['objects']==3 and c['counts']['region_ids_available']==list(range(31))
 assert g['review_scene_geometry_and_labels_unchanged']
 assert sha(folder/'renders/scene-review.blend')==g['review_scene_sha256']==m['review_scene']['sha256']
 assert sum(o['triangles'] for o in g['objects'])==c['counts']['visible_triangles']
 for o in g['objects']:
  assert o['components']==1 and o['coordinates_finite'] and o['boundary_edges']==o['nonmanifold_edges']==o['near_degenerate_triangles']==0
 body=next(o for o in g['objects'] if o['role']=='body');assert body['region_ids']==list(range(31))
 # Remaining handles/intersections are measured defects, never treated as approval.
 assert [f['view'] for f in m['frames']]==['front','three-quarter','back','selection']
 for f in m['frames']:
  path=folder/'renders'/f['path'];assert sha(path)==f['sha256']
  assert Image.open(path).size==(720,1152)
  assert f['selection_enabled']==(f['view']=='selection')
 assert m['selection']['selected_id']==1 and m['selection']['logical_regions']==['pectoraux.left']
 assert m['protocol']['AI_generated_images'] is False and m['protocol']['geometry_changed_by_renderer'] is False
 protocols.append(m['protocol']);source_records.append(c['source_records']);counts[variant]=c['counts']
assert protocols[0]==protocols[1] and source_records[0]==source_records[1]
archive_verified=False
if a.archive:
 assert sha(a.archive)=='40665852c49f218326590e204db91064a1ecfc3c6f8cbd7bbbcaac62c7cd409e'
 with zipfile.ZipFile(a.archive) as z:
  assert z.testzip() is None
  entries={Path(n).stem:n for n in z.namelist() if n.endswith('.obj')}
  for r in source_records[0]:assert hashlib.sha256(z.read(entries[r['element_id']])).hexdigest()==r['sha256']
 archive_verified=True
manifest=read(root/'comparisons/manifest.json');assert len(manifest['images'])==6
for item in manifest['images']:
 path=root/'comparisons'/item['path'];assert sha(path)==item['sha256'];assert Image.open(path).size==(item['width'],item['height'])
report=(repo/'docs/M4A_BP3D_RECONSTRUCTION.md').read_text();assert 'ne retenir ni D1 ni D2' in report
baseline='d4ca080485e778587ae15c337e02b8f975d03f73'
allowed={'docs/M4A.md','docs/M4A_REPRISE_ENVIRONNEMENT.md','docs/M4A_BP3D_RECONSTRUCTION.md'}|{'tools/m4a/'+n for n in ['build_bp3d_fitness.py','render_bp3d_fitness.py','check_bp3d_fitness.py','compose_bp3d_fitness.py','validate_bp3d_fitness.py']}
changed=set(git('diff','--name-only',baseline).splitlines())|set(git('ls-files','--others','--exclude-standard').splitlines())
for name in changed:assert name in allowed or name.startswith('docs/m4a/bp3d-fitness/'),name
# Historical source/model/render/tool files may be added beside, but never changed.
old_paths=git('ls-tree','-r','--name-only',baseline,'docs/m4a','tools/m4a').splitlines()
for name in changed&set(old_paths):assert git('hash-object',name)==git('rev-parse',baseline+':'+name),name
result={'baseline':baseline,'fitness_families':15,'provisional_lateral_zones':30,'muscle_source_OBJ':74,'archive_and_source_sha_verified':archive_verified,'actual_Blender_frames':8,'common_protocol_verified':True,'review_geometry_and_zone_labels_unchanged':True,'historical_assets_and_tools_unchanged':True,'application_SQLite_M4B_unchanged':True,'counts':counts,'visual_verdict':'Neither D1 nor D2 meets the premium target; stop before integration.'}
(root/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
