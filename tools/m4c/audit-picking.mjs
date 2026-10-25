/** Standalone data/raycast audit. No changes to the Logbook viewer or UI. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { inflateSync } from 'node:zlib';
import { createHash } from 'node:crypto';
import * as THREE from 'three';
import { sampleId, resolveOriginalSurfaceHit } from './surface-lookup.mjs';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const out = path.join(root, 'docs/m4c/meshy-huit-zones');
const json = file => JSON.parse(fs.readFileSync(path.join(out, file), 'utf8'));
const spec = json('regions.json'), binding = json('region-binding.json');
function readGLB(file) {
  const raw = fs.readFileSync(file), length = raw.readUInt32LE(12), doc = JSON.parse(raw.toString('utf8', 20, 20 + length));
  const binary = raw.subarray(28 + length), primitive = doc.meshes[0].primitives[0];
  function accessor(index) {
    const a = doc.accessors[index], v = doc.bufferViews[a.bufferView], width = { SCALAR: 1, VEC2: 2, VEC3: 3 }[a.type];
    const Constructor = { 5123: Uint16Array, 5125: Uint32Array, 5126: Float32Array }[a.componentType];
    return new Constructor(raw.buffer, binary.byteOffset + (v.byteOffset ?? 0) + (a.byteOffset ?? 0), a.count * width);
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(accessor(primitive.attributes.POSITION), 3));
  geometry.setAttribute('normal', new THREE.BufferAttribute(accessor(primitive.attributes.NORMAL), 3));
  if (primitive.attributes.TEXCOORD_0 !== undefined) geometry.setAttribute('uv', new THREE.BufferAttribute(accessor(primitive.attributes.TEXCOORD_0), 2));
  geometry.setIndex(new THREE.BufferAttribute(accessor(primitive.indices), 1));
  const mesh = new THREE.Mesh(geometry, new THREE.MeshBasicMaterial({ side: THREE.DoubleSide })); mesh.updateMatrixWorld();
  return { raw, geometry, mesh, positions: geometry.attributes.position.array, indices: geometry.index.array };
}
function decodeL8(file) {
  const b = fs.readFileSync(file); assert.equal(b.subarray(1, 4).toString(), 'PNG');
  let width, height; const chunks = [];
  for (let at = 8; at < b.length;) {
    const length = b.readUInt32BE(at), kind = b.toString('ascii', at + 4, at + 8), data = b.subarray(at + 8, at + 8 + length);
    if (kind === 'IHDR') { width = data.readUInt32BE(0); height = data.readUInt32BE(4); assert.equal(data[8], 8); assert.equal(data[9], 0); assert.equal(data[12], 0); }
    if (kind === 'IDAT') chunks.push(data); at += length + 12;
  }
  const raw = inflateSync(Buffer.concat(chunks)), pixels = new Uint8Array(width * height);
  const paeth = (a, b, c) => { const p = a + b - c, pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c); return pa <= pb && pa <= pc ? a : pb <= pc ? b : c; };
  for (let y = 0; y < height; y++) {
    const filter = raw[y * (width + 1)];
    for (let x = 0; x < width; x++) {
      const at = y * width + x, a = x ? pixels[at - 1] : 0, b = y ? pixels[at - width] : 0, c = x && y ? pixels[at - width - 1] : 0;
      const predictor = [0, a, b, Math.floor((a + b) / 2), paeth(a, b, c)][filter]; assert.notEqual(predictor, undefined);
      pixels[at] = (raw[y * (width + 1) + x + 1] + predictor) & 255;
    }
  }
  return { pixels, width, height };
}
const typedFile = (file, Constructor) => { const b = fs.readFileSync(path.join(out, file)); return new Constructor(Uint8Array.from(b).buffer); };
const original = readGLB(path.join(root, 'assets/models/meshy-e45e5d8.glb'));
const control = readGLB(path.join(out, 'exports/meshy-eight-zones-control.glb'));
const data = { ...decodeL8(path.join(out, spec.atlas.file)), assetId: binding.assetId, sourceSha256: createHash('sha256').update(original.raw).digest('hex'), requiredSha256: binding.sourceSha256,
  positions: original.positions, indices: original.indices, regions: spec.zones,
  boundFaces: typedFile(binding.boundFaces, Uint32Array), cornerUV: typedFile(binding.cornerUV, Float32Array) };
const hitData = hit => ({ assetId: binding.assetId, coordinateSpace: 'mesh-local', faceIndex: hit.faceIndex, point: { x: hit.point.x, y: hit.point.y, z: hit.point.z } });
const results = [];
for (const witness of json('picking-witnesses.json')) {
  const p = new THREE.Vector3(witness.point.x, witness.point.y, witness.point.z), normal = new THREE.Vector3(...witness.normal).normalize();
  const ray = new THREE.Raycaster(p.clone().addScaledVector(normal, .025), normal.clone().negate(), 0, .1);
  const a = ray.intersectObject(original.mesh)[0], b = ray.intersectObject(control.mesh)[0]; assert.ok(a && b);
  const fromOriginal = resolveOriginalSurfaceHit(hitData(a), data), fromExport = sampleId(b.uv, data.pixels, data.width, data.height, spec.zones);
  assert.equal(fromOriginal, witness.expectedId); assert.equal(fromExport, witness.expectedId);
  assert.ok(a.point.distanceTo(b.point) < 1e-7);
  assert.equal(Math.sign(p.x), witness.expectedId.includes('.left') ? 1 : -1);
  results.push({ expectedId: witness.expectedId, original: fromOriginal, exportedUV: fromExport, pointDeltaM: a.point.distanceTo(b.point) });
}
// Verify that two IDs can coexist within the SAME original source triangle.
let crossing;
for (let slot = 0; slot < data.boundFaces.length && !crossing; slot++) {
  const values = new Map(), face = data.boundFaces[slot];
  for (let u = 1; u < 10 && !crossing; u++) for (let v = 1; v < 10 - u; v++) {
    const weights = [u / 10, v / 10, 1 - (u + v) / 10], point = [0, 0, 0];
    for (let c = 0; c < 3; c++) for (let k = 0; k < 3; k++) point[k] += weights[c] * data.positions[data.indices[face * 3 + c] * 3 + k];
    const hit = { assetId: binding.assetId, coordinateSpace: 'mesh-local', faceIndex: face, point: { x: point[0], y: point[1], z: point[2] } };
    const id = resolveOriginalSurfaceHit(hit, data);
    if (id?.startsWith('deltoid.')) values.set(id, hit);
    if (values.size > 1) { crossing = { sourceFace: face, hits: [...values].map(([id, hit]) => ({ id, hit })) }; break; }
  }
}
assert.ok(crossing, 'No inter-fascicle boundary inside a source triangle');
const validHit = crossing.hits[0].hit;
assert.equal(resolveOriginalSurfaceHit({ ...validHit, assetId: 'other' }, data), null);
assert.equal(resolveOriginalSurfaceHit(validHit, { ...data, sourceSha256: 'other' }), null);
assert.equal(resolveOriginalSurfaceHit({ ...validHit, faceIndex: -1 }, data), null);
assert.equal(resolveOriginalSurfaceHit({ ...validHit, point: { x: NaN, y: 0, z: 0 } }, data), null);
assert.equal(resolveOriginalSurfaceHit({ ...validHit, point: { x: 20, y: 20, z: 20 } }, data), null);
const report = { status: 'passed', engine: 'Three.js 0.186.1 CPU Raycaster, no application UI', originalWithoutUV: true, sourceAndExportRaycasts: results, boundaryCrossesOriginalTriangle: crossing, invalidOrMismatchedAssetsRejected: true, actualIPhonePerformanceMeasured: false };
fs.writeFileSync(path.join(out, 'picking-audit.json'), JSON.stringify(report, null, 2) + '\n');
original.geometry.dispose(); control.geometry.dispose(); original.mesh.material.dispose(); control.mesh.material.dispose();
console.log('Eight real Three.js raycasts on source and export passed; IDs resolved without UI integration.');
