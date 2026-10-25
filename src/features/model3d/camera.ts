/** Geometric camera limits; no device-specific or invented performance values. */
export const MIN_POLAR_ANGLE = Math.PI / 4;
export const MAX_POLAR_ANGLE = 3 * Math.PI / 4;
export const VIEW_FOV_DEGREES = 36;
export type ModelSize = { x: number; y: number; z: number };
export function cameraFraming(size: ModelSize, aspect: number) {
  if (![size.x, size.y, size.z, aspect].every(value => Number.isFinite(value) && value > 0)) {
    throw new Error('Dimensions de visualisation invalides.');
  }
  const tanHalfFov = Math.tan(VIEW_FOV_DEGREES * Math.PI / 360);
  const horizontalRadius = Math.hypot(size.x, size.z) / 2;
  const fitDistance = (Math.max(size.y / (2 * tanHalfFov), horizontalRadius / (tanHalfFov * aspect)) + horizontalRadius) * 1.1;
  // With target.x/z fixed, the camera stays outside the enclosing vertical cylinder,
  // even at the allowed elevation limits and when the target moves vertically.
  const minDistance = (horizontalRadius + size.y * 0.05) / Math.sin(MIN_POLAR_ANGLE);
  return { fitDistance, minDistance, maxDistance: fitDistance * 1.8, near: size.y * 0.005, far: fitDistance * 6 + size.y * 3 };
}
