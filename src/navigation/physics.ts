/** Shared by UI-thread gestures and tests. A swipe always changes at most one universe. */
export function isVerticalIntent(dx: number, dy: number): boolean {
  'worklet';
  return Math.abs(dy) >= 12 && Math.abs(dy) > Math.abs(dx) * 1.4;
}

export function canStartPageDrag(index: number, count: number, dy: number, scrollY: number, maxScroll: number): boolean {
  'worklet';
  // Home is an entry point: overflow (small display / larger text) must not
  // silently turn its advertised upward gesture into a scroll-to-bottom task.
  if (dy < 0) return index < count - 1 && (index === 0 || scrollY >= Math.max(0, maxScroll) - 1);
  if (dy > 0) return index > 0 && scrollY <= 1;
  return false;
}

export function clampOffset(offset: number, height: number, count: number): number {
  'worklet';
  return Math.max(-(count - 1) * height, Math.min(0, offset));
}

export function clampDrag(index: number, dy: number, height: number, count: number): number {
  'worklet';
  const position = -index * height + Math.max(-height, Math.min(height, dy));
  return clampOffset(position, height, count);
}

/** Backtracking can cancel a gesture, but cannot claim the opposite list boundary. */
export function directionalDrag(dy: number, direction: number): number {
  'worklet';
  return direction < 0 ? Math.min(0, dy) : Math.max(0, dy);
}

export function releaseIndex(index: number, count: number, dy: number, velocityY: number, height: number): number {
  'worklet';
  if (height <= 0 || Math.abs(dy) < 12) return index;
  const passedDistance = Math.abs(dy) >= height * 0.18;
  const passedVelocity = Math.abs(velocityY) >= 700 && Math.sign(velocityY) === Math.sign(dy);
  if (!passedDistance && !passedVelocity) return index;
  return Math.max(0, Math.min(count - 1, index + (dy < 0 ? 1 : -1)));
}
