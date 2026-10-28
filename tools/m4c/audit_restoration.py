"""Byte-for-byte restoration audit; no anatomical processing or resource writes."""
import argparse,base64,hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--interactive',action='store_true');args=p.parse_args()
base='docs/m4c/meshy-posterieurs-harmonises'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def digest(data):return hashlib.sha256(data).hexdigest()
def equal(reference,path):
 old=git('show',reference+':'+path);current=(ROOT/path).read_bytes();assert old==current,path
 return {'sha256':digest(current),'bytes':len(current),'byteIdentical':True}
paths=git('ls-tree','-r','--name-only','06fa665','--',base).decode().splitlines();assert paths
files={path:equal('06fa665',path) for path in paths}
master=equal('06fa665','assets/models/meshy-e45e5d8.glb');assert master['sha256']=='421e593cad17f60d1c0c5e67707729fb88bbf69026795e22011ecc7d90b38959'
zones=json.loads((ROOT/base/'regions.json').read_text())['zones'];assert len(zones)==8 and {z['code'] for z in zones}==set(range(1,9))
report={'status':'passed','m4cReference':'06fa665b676ea697e862ae3491fa1af6f827199d','allM4CReferenceFolderFiles':files,'eightMasks':{z['id']:files[base+'/textures/'+z['id']+'.png'] for z in zones},'muscleIDs':{z['id']:z['code'] for z in zones},'meshyMaster':master,'anatomicalEditsPerformed':False}
if args.interactive:
 runtime=['assets/models/meshy-m4d-uv.glb','src/features/model3d/generated/selectionData.ts','src/features/model3d/generated/viewerBundle.ts','tools/m4d/build-selection.mjs','tests/muscle-selection.test.ts']
 report['m4dReference']='268ea3e80f45ff0eefa72c4575425fbae66a44fb';report['runtimeAndSourceBindings']={path:equal('268ea3e',path) for path in runtime}
 application=git('ls-tree','-r','--name-only','268ea3e','--','src','app','assets','app.json','package.json','package-lock.json','tsconfig.json').decode().splitlines()
 report['allApplicationFilesEqual268ea3e']={path:equal('268ea3e',path) for path in application}
 code=(ROOT/'src/features/model3d/generated/selectionData.ts').read_text();png=base64.b64decode(json.loads(re.search(r'muscleAtlasBase64 = ("[^"]*");',code).group(1)));assert png==(ROOT/base/'textures/muscle-ids.png').read_bytes()
 report['runtimeAtlasEquals06fa665']=True;report['sqliteV8AndDependenciesUnchanged']=True
 output=ROOT/'docs/m4d/selection-restauree/verification.json'
else:output=ROOT/'docs/m4c/restauration-06fa665/verification.json'
output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':'passed','referenceFolderFilesIdentical':len(files),'eightMasksIdentical':True,'interactiveResourcesIdentical':args.interactive,'output':str(output.relative_to(ROOT))}))
