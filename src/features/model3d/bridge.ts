import { muscleById, type MuscleId } from './selection';
/** A surface intersection is technical geometry, never an anatomical muscle ID. */
export type SurfaceHit = {
  assetId: 'meshy-e45e5d8';
  coordinateSpace: 'mesh-local';
  point: { x: number; y: number; z: number };
  faceIndex: number;
  uv?: { x: number; y: number };
};
export type ViewerCommand = 'overview' | 'front' | 'reset-selection' | 'dispose';
export type ViewerEvent =
  | { version: 1; type: 'ready'; triangles: number; geometryBytes: number }
  | { version: 1; type: 'error'; message: string }
  | { version: 1; type: 'surface-hit'; hit: SurfaceHit }
  | { version: 1; type: 'selection'; muscleId: MuscleId | null };
const record = (value: unknown): value is Record<string, unknown> => !!value && typeof value === 'object' && !Array.isArray(value);
const finite = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value);
export function parseViewerEvent(text: string): ViewerEvent | null {
  if (text.length > 4096) return null;
  let value: unknown;
  try { value = JSON.parse(text); } catch { return null; }
  if (!record(value) || value.version !== 1) return null;
  if (value.type === 'ready' && value.triangles === 110588 && finite(value.geometryBytes) && value.geometryBytes > 0) {
    return { version: 1, type: 'ready', triangles: value.triangles, geometryBytes: value.geometryBytes };
  }
  if (value.type === 'error' && typeof value.message === 'string') {
    return { version: 1, type: 'error', message: value.message.slice(0, 240) };
  }
  if (value.type === 'selection') {
    if (value.muscleId === null) return { version: 1, type: 'selection', muscleId: null };
    const muscle = muscleById(value.muscleId);
    return muscle ? { version: 1, type: 'selection', muscleId: muscle.id } : null;
  }
  if (value.type !== 'surface-hit' || !record(value.hit)) return null;
  const hit = value.hit;
  if (hit.assetId !== 'meshy-e45e5d8' || hit.coordinateSpace !== 'mesh-local' || !record(hit.point)
    || ![hit.point.x, hit.point.y, hit.point.z].every(finite) || !Number.isInteger(hit.faceIndex)
    || (hit.faceIndex as number) < 0 || (hit.faceIndex as number) >= 110588) return null;
  const result: SurfaceHit = { assetId: hit.assetId, coordinateSpace: hit.coordinateSpace,
    point: { x: hit.point.x as number, y: hit.point.y as number, z: hit.point.z as number }, faceIndex: hit.faceIndex as number };
  if (record(hit.uv) && finite(hit.uv.x) && finite(hit.uv.y)) result.uv = { x: hit.uv.x, y: hit.uv.y };
  return { version: 1, type: 'surface-hit', hit: result };
}
export function commandScript(command: ViewerCommand): string {
  return `window.LogbookModelViewer && window.LogbookModelViewer.command(${JSON.stringify(command)}); true;`;
}
