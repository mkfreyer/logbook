import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { cameraFraming, MIN_POLAR_ANGLE, VIEW_FOV_DEGREES } from '../src/features/model3d/camera';
import { commandScript, parseViewerEvent } from '../src/features/model3d/bridge';
import { MODEL } from '../src/features/model3d/model';
import { buildViewerDocument } from '../src/features/model3d/document';

test('the preserved M4A master remains byte-identical, with its original unsegmented mesh', () => {
  const bytes = readFileSync(new URL('../assets/models/meshy-e45e5d8.glb', import.meta.url));
  assert.equal(bytes.length, MODEL.bytes);
  assert.equal(createHash('sha256').update(bytes).digest('hex'), MODEL.sha256);
  assert.equal(bytes.readUInt32LE(0), 0x46546c67); assert.equal(bytes.readUInt32LE(4), 2);
  const json = JSON.parse(bytes.subarray(20, 20 + bytes.readUInt32LE(12)).toString());
  assert.equal(json.meshes.length, 1); assert.equal(json.nodes.length, 1);
  assert.equal((json.textures ?? []).length, 0);
  assert.equal(json.meshes[0].primitives.length, 1);
  assert.equal(json.accessors[json.meshes[0].primitives[0].indices].count / 3, 110588);
  assert.match(json.asset.copyright, /Meshy.*CC BY 4.0/);
});

test('overview fits head, feet and width across narrow and wide viewports', () => {
  for (const aspect of [0.4, 0.6, 1, 2]) {
    const size = { x: 0.76, y: 1.9, z: 0.33 }, frame = cameraFraming(size, aspect);
    const tan = Math.tan(VIEW_FOV_DEGREES * Math.PI / 360);
    const frontDistance = frame.fitDistance - size.z / 2;
    assert.ok((size.y / 2) / (frontDistance * tan) < 1);
    assert.ok((size.x / 2) / (frontDistance * tan * aspect) < 1);
    assert.ok(frame.minDistance < frame.fitDistance && frame.fitDistance < frame.maxDistance);
    assert.ok(frame.minDistance * Math.sin(MIN_POLAR_ANGLE) > Math.hypot(size.x, size.z) / 2);
    assert.ok(frame.near > 0 && frame.far > frame.maxDistance + size.y);
  }
  assert.throws(() => cameraFraming({ x: 1, y: 2, z: 1 }, 0));
  assert.throws(() => cameraFraming({ x: NaN, y: 2, z: 1 }, 1));
});

test('bridge validates technical surface hits, without inventing muscle identifiers', () => {
  const hit = { assetId: MODEL.id, coordinateSpace: 'mesh-local', point: { x: 0.1, y: 0.5, z: 0.12 }, faceIndex: 42 };
  assert.deepEqual(parseViewerEvent(JSON.stringify({ version: 1, type: 'surface-hit', hit })), { version: 1, type: 'surface-hit', hit });
  for (const invalid of [null, {}, { version: 2, type: 'ready' }, { version: 1, type: 'ready', triangles: 97424, geometryBytes: 1000 },
    { version: 1, type: 'surface-hit', hit: { ...hit, assetId: 'deltoid.left.anterior' } },
    { version: 1, type: 'surface-hit', hit: { ...hit, faceIndex: -1 } },
    { version: 1, type: 'surface-hit', hit: { ...hit, faceIndex: 110588 } },
    { version: 1, type: 'surface-hit', hit: { ...hit, point: { x: null, y: 0, z: 0 } } }]) {
    assert.equal(parseViewerEvent(JSON.stringify(invalid)), null);
  }
  assert.equal(parseViewerEvent('not json'), null); assert.equal(parseViewerEvent('x'.repeat(4097)), null);
  assert.match(commandScript('overview'), /command\("overview"\)/);
});

test('HTML contains only bundled code/data and forbids external connections', () => {
  const html = buildViewerDocument('Z2xURg==');
  assert.match(html, /connect-src 'none'/); assert.match(html, /model-data/);
  assert.doesNotMatch(html, /<script[^>]+src=/i);
  assert.throws(() => buildViewerDocument('</script>'));
});
