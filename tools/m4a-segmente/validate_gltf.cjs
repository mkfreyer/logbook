// Optional Khronos glTF Validator check. Pass its installed module path in argv[2].
const fs = require('fs');
const path = require('path');
const validator = require(process.argv[2] || 'gltf-validator');
const root = path.resolve(__dirname, '../..');
const out = path.join(root, 'docs/m4a/segmente');
validator.validateBytes(new Uint8Array(fs.readFileSync(path.join(out,'pilote-haut-corps.glb'))), { uri: 'pilote-haut-corps.glb', maxIssues: 1000 }).then(report => {
  fs.writeFileSync(path.join(out, 'gltf-validation.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ errors: report.issues.numErrors, warnings: report.issues.numWarnings, infos: report.issues.numInfos, truncated: report.issues.truncated }));
  if (report.issues.numErrors) process.exitCode = 1;
});
