"""File costs and byte-level protection of the validated application baseline."""
import hashlib,json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[2];out=root/'docs/m4c/meshy-huit-zones';base='11d56d0f0aaf2a4dd621438fcd09f41f9bca4256'
files=subprocess.check_output(['git','ls-tree','-r','--name-only',base],cwd=root,text=True).splitlines()
protected=[p for p in files if p.startswith(('app/','src/','assets/','tools/m4b/','.github/')) or p in ['app.json','package.json','package-lock.json','tsconfig.json','metro.config.js','babel.config.js','.nvmrc']]
checks=[]
for p in protected:
    before=subprocess.check_output(['git','show',f'{base}:{p}'],cwd=root);after=(root/p).read_bytes();assert before==after,p
    checks.append({'file':p,'sha256':hashlib.sha256(after).hexdigest()})
(out/'application-preservation.json').write_text(json.dumps({'baseCommit':base,'allExistingProtectedFilesBitIdentical':True,'checkedFiles':checks,'SQLiteSchemaVersion':8,'applicationOrViewerIntegrationPerformed':False,'userConfirmedM4BSDK58OnIPhone':True,'M4CIPhoneTestPerformed':False},indent=2)+'\n')
e=json.loads((out/'exports/export-report.json').read_text())
report={'baseCommit':base,'sourceSha256':e['source_sha256'],'sourceGlbBytes':1993204,'controlGlbBytes':e['glb_bytes'],'additionalControlGlbBytes':e['glb_bytes']-1993204,'trianglesBefore':110588,'trianglesAfter':e['triangles_after'],'sourceAndBlenderVertices':55288,'exportVertices':e['export_vertices'],'UVSeamDuplicates':e['uv_seam_duplicates'],'UVSeamDuplicatesPercent':round(100*e['uv_seam_duplicates']/55288,3),'sourceBindingBytes':e['source_binding_bytes'],'idAtlasResolution':[2048,2048],'idPngBytes':(out/'textures/muscle-ids.png').stat().st_size,'allExternalTexturePngBytes':sum(p.stat().st_size for p in (out/'textures').glob('*.png')),'estimatedGPUMemoryBytes':{'idAtlasIfExplicitR8NoMipmaps':2048**2,'idAtlasIfRGBA8NoMipmaps':2048**2*4,'colorTextureRGBA8WithMipmapsApprox':round(2048**2*4*4/3),'sourceGeometryBuffers':55288*24+331764*2,'controlGeometryBuffers':e['export_vertices']*32+331764*2},'drawCallsForSingleMeshPrimitive':1,'extraCostInExistingApplication':0,'actualIPhoneM4CPerformanceMeasured':False,'protectedApplicationFilesChecked':len(checks),'files':{str(p.relative_to(out)):p.stat().st_size for p in sorted(out.rglob('*')) if p.is_file() and p.name!='delivery-metrics.json'}}
(out/'delivery-metrics.json').write_text(json.dumps(report,indent=2)+'\n');print('Application files unchanged:',len(checks),'extra GLB bytes:',report['additionalControlGlbBytes'],'ID PNG bytes:',report['idPngBytes'])
