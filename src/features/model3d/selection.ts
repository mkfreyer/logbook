/** Stable M4C codes; anatomical left/right, independent of camera orientation. */
export const MUSCLES = [
  { code: 1, id: 'pectoralis.left', name: 'Grand pectoral gauche' },
  { code: 2, id: 'pectoralis.right', name: 'Grand pectoral droit' },
  { code: 3, id: 'deltoid.left.anterior', name: 'Deltoïde antérieur gauche' },
  { code: 4, id: 'deltoid.left.lateral', name: 'Deltoïde moyen gauche' },
  { code: 5, id: 'deltoid.left.posterior', name: 'Deltoïde postérieur gauche' },
  { code: 6, id: 'deltoid.right.anterior', name: 'Deltoïde antérieur droit' },
  { code: 7, id: 'deltoid.right.lateral', name: 'Deltoïde moyen droit' },
  { code: 8, id: 'deltoid.right.posterior', name: 'Deltoïde postérieur droit' },
] as const;
export type MuscleId = typeof MUSCLES[number]['id'];
export const SELECTION_COLOR = '#ff932b';
export function muscleById(id: unknown) { return MUSCLES.find(muscle => muscle.id === id) ?? null; }
export function sampleMuscle(uv: { x: number; y: number } | undefined, pixels: Uint8Array, width: number, height: number) {
  if (!uv || !Number.isFinite(uv.x) || !Number.isFinite(uv.y) || uv.x < 0 || uv.x > 1 || uv.y < 0 || uv.y > 1) return null;
  const x = Math.min(width - 1, Math.floor(uv.x * width)), y = Math.min(height - 1, Math.floor(uv.y * height));
  return MUSCLES.find(m => m.code === pixels[y * width + x]) ?? null;
}
/** CSS-pixel slop and time limit apply to the entire gesture, including return trips. */
export class SelectionTap {
  private pointers = new Set<number>();
  private candidate: { id: number; x: number; y: number; time: number } | null = null;
  down(id: number, x: number, y: number, time: number) {
    this.pointers.add(id);
    this.candidate = this.pointers.size === 1 ? { id, x, y, time } : null;
  }
  move(id: number, x: number, y: number) {
    if (this.candidate?.id === id && Math.hypot(x - this.candidate.x, y - this.candidate.y) > 8) this.candidate = null;
  }
  up(id: number, x: number, y: number, time: number) {
    this.move(id, x, y);
    const candidate = this.candidate;
    this.candidate = null; this.pointers.delete(id);
    return !!candidate && candidate.id === id && time >= candidate.time && time - candidate.time <= 350 && this.pointers.size === 0;
  }
  cancel(id: number) { this.pointers.delete(id); this.candidate = null; }
  clear() { this.pointers.clear(); this.candidate = null; }
}
