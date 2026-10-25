/** Real WebGL integration in Chromium; this is NOT an iPhone performance test. */
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';
import { buildViewerDocument } from '../../src/features/model3d/document';
import { MODEL } from '../../src/features/model3d/model';

async function main() {
const artifactDir = process.env.M4B_ARTIFACT_DIR ?? '/tmp/logbook-m4b-validation';
await mkdir(artifactDir, { recursive: true });
const glb = await readFile('assets/models/meshy-e45e5d8.glb');
const html = buildViewerDocument(glb.toString('base64'));
const server = createServer((request, response) => {
  response.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' });
  response.end(request.url === '/invalid' ? buildViewerDocument('Z2xURg==') : html);
});
await new Promise<void>(resolve => server.listen(0, '127.0.0.1', resolve));
const address = server.address(); assert.ok(address && typeof address !== 'string');
const origin = `http://127.0.0.1:${address.port}`;
const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH ?? '/usr/bin/chromium', headless: true,
  args: ['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--disable-dev-shm-usage'] }).catch(error => { server.close(); throw error; });
const context = await browser.newContext({ viewport: { width: 390, height: 540 }, deviceScaleFactor: 2, hasTouch: true, isMobile: true });
const requests: string[] = [], errors: string[] = [];
await context.route('**/*', async route => {
  const url = route.request().url(); requests.push(url);
  if (!url.startsWith(`${origin}/`)) { await route.abort(); return; }
  await route.continue();
});
await context.addInitScript({ content: "window.messages=[]; window.ReactNativeWebView={postMessage:function(text){window.messages.push(JSON.parse(text));}};" });
const page = await context.newPage();
page.on('pageerror', error => errors.push(error.message));
const snapshot = () => page.evaluate(() => window.LogbookModelViewer!.snapshot());
const command = (value: 'overview' | 'front' | 'dispose') => page.evaluate(value => window.LogbookModelViewer!.command(value), value);
const ready = async () => {
  await page.waitForFunction(() => window.LogbookModelViewer?.snapshot().loaded === true && (window.LogbookModelViewer?.snapshot().renderCount as number) > 0, null, { timeout: 30000 });
  await page.waitForTimeout(500);
};
const cdp = await context.newCDPSession(page);
type Point = { x: number; y: number; id: number };
async function touch(start: Point[], end: Point[], steps = 12) {
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: start });
  for (let i = 1; i <= steps; i++) {
    const points = start.map((p, k) => ({ ...p, x: p.x + (end[k]!.x - p.x) * i / steps, y: p.y + (end[k]!.y - p.y) * i / steps }));
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: points });
    await page.waitForTimeout(12);
  }
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  await page.waitForTimeout(500);
}
const results: Record<string, unknown> = { device: 'Chromium desktop, SwiftShader software WebGL; emulated touch viewport 390×540, not an iPhone', asset: MODEL };
try {
  await page.goto(origin); await ready();
  const initial = await snapshot();
  assert.equal(initial.triangles, MODEL.triangles); assert.equal(initial.renderedTriangles, MODEL.triangles);
  assert.equal(initial.geometries, 1); // Renderer may also allocate an internal framebuffer texture.
  await writeFile(path.join(artifactDir, 'initial-snapshot.json'), JSON.stringify(initial, null, 2));
  assert.ok((initial.geometryBytes as number) > 0);
  await page.screenshot({ path: path.join(artifactDir, 'vue-generale.png') });
  await context.setOffline(true); results.offlineAfterLoad = true;
  // Actual camera projection of the rendered model's eight bounding corners.
  const fit = await page.evaluate(() => {
    const s = window.LogbookModelViewer!.snapshot();
    const b = s.projectedBounds as { min: { x: number; y: number; z: number }; max: { x: number; y: number; z: number } };
    const distance = s.distance as number, tan = Math.tan(36 * Math.PI / 360), aspect = innerWidth / innerHeight;
    return { vertical: Math.max(Math.abs(b.min.y), Math.abs(b.max.y)) / ((distance - b.max.z) * tan),
      horizontal: Math.max(Math.abs(b.min.x), Math.abs(b.max.x)) / ((distance - b.max.z) * tan * aspect) };
  });
  assert.ok(fit.vertical < 1 && fit.horizontal < 1, JSON.stringify(fit));
  results.initial = initial; results.overviewFits = fit;
  await touch([{ x: 100, y: 270, id: 0 }], [{ x: 300, y: 285, id: 0 }]);
  const rotated = await snapshot(); assert.ok(Math.abs(rotated.azimuth as number) > 0.3);
  assert.ok((rotated.polarAngle as number) >= Math.PI / 4 && (rotated.polarAngle as number) <= 3 * Math.PI / 4);
  await page.screenshot({ path: path.join(artifactDir, 'rotation.png') });
  let previousAzimuth = rotated.azimuth as number;
  let turn = Math.abs(previousAzimuth);
  for (let i = 0; i < 5; i++) {
    await touch([{ x: 100, y: 270, id: 0 }], [{ x: 300, y: 270, id: 0 }]);
    const angle = (await snapshot()).azimuth as number;
    let delta = angle - previousAzimuth;
    while (delta > Math.PI) delta -= 2 * Math.PI;
    while (delta < -Math.PI) delta += 2 * Math.PI;
    turn += Math.abs(delta); previousAzimuth = angle;
    if (i === 0) await page.screenshot({ path: path.join(artifactDir, 'vue-dos.png') });
  }
  assert.ok(turn > 2 * Math.PI); results.touchRotationSweepRadians = turn;

  await command('overview'); await page.waitForTimeout(400);
  const beforeZoom = await snapshot();
  await touch([{ x: 140, y: 250, id: 1 }, { x: 250, y: 250, id: 2 }], [{ x: 70, y: 250, id: 1 }, { x: 320, y: 250, id: 2 }]);
  const zoomed = await snapshot(); assert.ok((zoomed.distance as number) < (beforeZoom.distance as number) * 0.9);
  for (let i = 0; i < 3; i++) await touch([{ x: 170, y: 250, id: 1 }, { x: 220, y: 250, id: 2 }], [{ x: 20, y: 250, id: 1 }, { x: 370, y: 250, id: 2 }], 8);
  const clamped = await snapshot(); assert.ok((clamped.distance as number) >= (clamped.minDistance as number) - 1e-6);
  await touch([{ x: 100, y: 380, id: 1 }, { x: 280, y: 380, id: 2 }], [{ x: 100, y: 70, id: 1 }, { x: 280, y: 70, id: 2 }]);
  const panned = await snapshot(); assert.ok(Math.abs((panned.target as number[])[1]!) > 0.02);
  assert.ok(Math.abs((panned.target as number[])[0]!) < 1e-8 && Math.abs((panned.target as number[])[2]!) < 1e-8);
  await page.screenshot({ path: path.join(artifactDir, 'zoom.png') });
  const preFront = await snapshot(); await command('front'); await page.waitForTimeout(250);
  const front = await snapshot(); assert.ok(Math.abs(front.azimuth as number) < 1e-6);
  assert.ok(Math.abs((front.distance as number) - (preFront.distance as number)) < 1e-5);
  await touch([{ x: 40, y: 250, id: 1 }, { x: 350, y: 250, id: 2 }], [{ x: 180, y: 250, id: 1 }, { x: 210, y: 250, id: 2 }]);
  const zoomedOut = await snapshot(); assert.ok((zoomedOut.distance as number) > (front.distance as number));
  assert.ok((zoomedOut.distance as number) <= (zoomedOut.maxDistance as number) + 1e-6);
  await command('overview'); await page.waitForTimeout(500);
  const reset = await snapshot();
  assert.ok(Math.abs((reset.distance as number) - (initial.distance as number)) < 1e-5);
  assert.deepEqual(reset.target, [0, 0, 0]); assert.ok(Math.abs(reset.azimuth as number) < 1e-6);
  // A real raycast yields geometry only; there is no invented anatomical selection.
  await touch([{ x: 195, y: 190, id: 3 }], [{ x: 195, y: 190, id: 3 }], 1);
  const events = await page.evaluate(() => (window as unknown as { messages: Array<{ type: string; hit?: unknown }> }).messages);
  assert.ok(events.some(event => event.type === 'surface-hit'));
  assert.ok(!JSON.stringify(events).includes('muscleId'));
  await page.waitForTimeout(700); const idle = await snapshot(); await page.waitForTimeout(200);
  assert.equal((await snapshot()).renderCount, idle.renderCount);
  results.touch = { rotation: true, pinchIn: true, pinchOut: true, zoomLimits: true, verticalPan: true, front: true, overview: true, realRaycast: true, idleRenderStops: true };
  await context.setOffline(false);
  const cycles: unknown[] = [];
  for (let i = 0; i < 5; i++) {
    await command('dispose'); const released = await snapshot();
    assert.equal(released.disposed, true); assert.equal(released.geometries, 0);
    assert.equal(await page.locator('canvas').count(), 0);
    cycles.push({ geometriesAfterDispose: released.geometries, contextLost: released.contextLost });
    await page.goto(origin); await ready();
  }
  results.openCloseCycles = cycles;
  await page.setViewportSize({ width: 320, height: 460 });
  await command('overview'); await page.waitForTimeout(400);
  const narrow = await snapshot(); assert.equal(narrow.loaded, true);
  await command('dispose'); await page.goto(`${origin}/invalid`);
  await page.waitForFunction(() => (window as unknown as { messages: Array<{ type: string }> }).messages.some(event => event.type === 'error'));
  results.invalidModelReportsError = true;
  assert.deepEqual(errors, []); assert.ok(requests.every(url => url.startsWith(`${origin}/`)));
  results.externalRequests = 0; results.errors = errors; results.status = 'passed';
  await writeFile(path.join(artifactDir, 'browser-results.json'), JSON.stringify(results, null, 2) + '\n');
  console.log('Real WebGL + touch + model identity + lifecycle: passed. iPhone validation remains pending.');
} finally { await browser.close(); server.close(); }

}
void main().catch(error => { console.error(error); process.exitCode = 1; });
