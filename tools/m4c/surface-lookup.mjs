/** Offline preparation only. Not imported by Logbook or its viewer.
 * IDs are atlas values. Face indices only accelerate lookup on the SHA-bound
 * original asset; they are never anatomical identifiers.
 */
export function sampleId(uv, pixels, width, height, regions) {
  if (!uv || !Number.isFinite(uv.x) || !Number.isFinite(uv.y)) return null;
  const x = Math.max(0, Math.min(width - 1, Math.floor(uv.x * width)));
  const y = Math.max(0, Math.min(height - 1, Math.floor(uv.y * height)));
  const code = pixels[y * width + x];
  return regions.find(region => region.code === code)?.id ?? null;
}
export function barycentric(point, a, b, c) {
  const sub = (u, v) => u.map((value, index) => value - v[index]);
  const dot = (u, v) => u.reduce((sum, value, index) => sum + value * v[index], 0);
  const v0 = sub(b, a), v1 = sub(c, a), v2 = sub(point, a);
  const d00 = dot(v0, v0), d01 = dot(v0, v1), d11 = dot(v1, v1), d20 = dot(v2, v0), d21 = dot(v2, v1);
  const denominator = d00 * d11 - d01 * d01;
  if (Math.abs(denominator) < 1e-20) return null;
  const y = (d11 * d20 - d01 * d21) / denominator, z = (d00 * d21 - d01 * d20) / denominator;
  const weights = [1 - y - z, y, z];
  if (weights.some(value => !Number.isFinite(value) || value < -0.002 || value > 1.002)) return null;
  // A hit on the wrong plane must not borrow this face's UV.
  const rebuilt = a.map((_, k) => weights[0] * a[k] + weights[1] * b[k] + weights[2] * c[k]);
  if (Math.hypot(...sub(point, rebuilt)) > 1e-5) return null;
  return weights;
}
export function resolveOriginalSurfaceHit(hit, data) {
  if (hit?.assetId !== data.assetId || hit.coordinateSpace !== 'mesh-local'
      || data.sourceSha256 !== data.requiredSha256 || !Number.isInteger(hit.faceIndex)) return null;
  const face = hit.faceIndex;
  if (face < 0 || face >= data.indices.length / 3) return null;
  // Current e45e5d8 has no UV. Never trust a supplied UV from another asset.
  let lo = 0, hi = data.boundFaces.length - 1, slot = -1;
  while (lo <= hi) {
    const mid = (lo + hi) >>> 1, value = data.boundFaces[mid];
    if (value === face) { slot = mid; break; }
    if (value < face) lo = mid + 1; else hi = mid - 1;
  }
  if (slot < 0) return null;
  const vertices = [0, 1, 2].map(corner => {
    const index = data.indices[face * 3 + corner] * 3;
    return Array.from(data.positions.subarray(index, index + 3));
  });
  const point = [hit.point?.x, hit.point?.y, hit.point?.z];
  if (!point.every(Number.isFinite)) return null;
  const w = barycentric(point, ...vertices);
  if (!w) return null;
  const uv = { x: 0, y: 0 };
  for (let i = 0; i < 3; i++) {
    uv.x += w[i] * data.cornerUV[slot * 6 + i * 2];
    uv.y += w[i] * data.cornerUV[slot * 6 + i * 2 + 1];
  }
  return sampleId(uv, data.pixels, data.width, data.height, data.regions);
}
