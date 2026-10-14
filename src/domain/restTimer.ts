import type { RestInterval } from './session';

export interface RestTiming {
  chronologicalMs: number; activeMs: number; pausedMs: number;
  remainingMs: number; overtimeMs: number; expired: boolean; isPaused: boolean; progress: number;
}
/** Calendar time keeps passing during pause/background. Countdown time excludes saved pauses.
 * Backgrounding alone is never a pause. A timer repaint is not a source of truth. */
export function calculateRestTiming(rest: RestInterval, nowMs = Date.now()): RestTiming {
  const start = Date.parse(rest.startedAt);
  const end = Math.max(start, rest.endedAt ? Date.parse(rest.endedAt) : nowMs);
  const chronologicalMs = rest.chronologicalMs ?? Math.max(0, end - start);
  const pausedMs = Math.min(chronologicalMs, rest.pauses.reduce((sum, pause) =>
    sum + Math.max(0, Math.min(end, pause.endedAt ? Date.parse(pause.endedAt) : end) - Math.max(start, Date.parse(pause.startedAt))), 0));
  const activeMs = rest.activeMs ?? Math.max(0, chronologicalMs - pausedMs);
  const targetMs = rest.plannedSeconds * 1000;
  return { chronologicalMs, activeMs, pausedMs, remainingMs: Math.max(0, targetMs - activeMs),
    overtimeMs: Math.max(0, activeMs - targetMs), expired: activeMs >= targetMs,
    isPaused: rest.endedAt === null && rest.pauses.some(item => item.endedAt === null),
    progress: targetMs > 0 ? Math.min(1, activeMs / targetMs) : 1 };
}

export function formatDuration(milliseconds: number): string {
  const seconds = Math.max(0, Math.floor(milliseconds / 1000));
  return `${Math.floor(seconds / 60).toString().padStart(2, '0')}:${(seconds % 60).toString().padStart(2, '0')}`;
}
