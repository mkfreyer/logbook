import type { WeightMode } from './training';

export type HistoryPeriod = '30' | '90' | '365' | 'all';
export const historyPeriods: { id: HistoryPeriod; label: string }[] = [
  { id: '30', label: '30 jours' }, { id: '90', label: '90 jours' },
  { id: '365', label: '1 an' }, { id: 'all', label: 'Tout' },
];
export interface HistoryRange { from?: string; until: string }
export interface HistoryFilter extends HistoryRange { programId?: string }

/** Calendar days in the device timezone, including today. Do not subtract 24h across DST. */
export function historyRange(period: HistoryPeriod, now = new Date()): HistoryRange {
  const until = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
  if (period === 'all') return { until: until.toISOString() };
  const from = new Date(now.getFullYear(), now.getMonth(), now.getDate() - Number(period) + 1);
  return { from: from.toISOString(), until: until.toISOString() };
}
export function previousHistoryRange(period: HistoryPeriod, now = new Date()): HistoryRange | null {
  if (period === 'all') return null;
  const until = new Date(historyRange(period, now).from!);
  const from = new Date(until.getFullYear(), until.getMonth(), until.getDate() - Number(period));
  return { from: from.toISOString(), until: until.toISOString() };
}
export interface HistoryStats {
  sessionCount: number; durationMs: number; performedSetCount: number;
  loggedTonnageKg: number | null; chargedSetCount: number; unchargedSetCount: number;
}
export interface HistorySession {
  id: string; sourceProgramId: string; sourceWorkoutTemplateId: string;
  workoutName: string; programName: string; startedAt: string; finishedAt: string;
  durationMs: number; performedSetCount: number; loggedTonnageKg: number | null;
  chargedSetCount: number; unchargedSetCount: number;
}
export interface HistoryProgram { id: string; name: string; sessionCount: number; deleted: number }
export interface HistoryOverview {
  stats: HistoryStats; previous: HistoryStats | null; programs: HistoryProgram[];
  sessions: HistorySession[]; points: HistorySession[]; page: number; pageCount: number;
}
export interface HistoricalExercise {
  id: string; name: string; muscleGroup: string; equipment: string; instructions: string;
  sessionCount: number;
}
export interface ExercisePerformance {
  id: string; sessionId: string; sessionExerciseId: string; exerciseName: string;
  workoutName: string; programName: string; finishedAt: string; performedAt: string;
  sortOrder: number; seriesIndex: number; label: string; kind: string;
  weightKg: number | null; reps: number; rir: number | null; weightMode: WeightMode;
}
export interface ExerciseVisit {
  sessionId: string; finishedAt: string; workoutName: string; programName: string;
  performances: ExercisePerformance[];
}
export interface ExercisePoint {
  sessionId: string; finishedAt: string; workoutName: string;
  representative: ExercisePerformance | null; loggedTonnageKg: number | null;
}
export interface ExerciseHistory {
  exercise: HistoricalExercise | null; modes: WeightMode[]; mode: WeightMode | null;
  sessionCount: number; lastPerformance: ExercisePerformance | null;
  visits: ExerciseVisit[]; points: ExercisePoint[]; page: number; pageCount: number;
}

/** Same real non-warmup set supplies both kg and reps. Highest kg, then reps,
 * then earliest validation; if all kg are missing, highest reps. One load mode. */
export function representativeSet(rows: ExercisePerformance[]): ExercisePerformance | null {
  const work = rows.filter(row => row.kind !== 'warmup'), charged = work.filter(row => row.weightKg !== null);
  return [...(charged.length ? charged : work)].sort((a, b) =>
    (b.weightKg ?? 0) - (a.weightKg ?? 0) || b.reps - a.reps || a.sortOrder - b.sortOrder)[0] ?? null;
}
export function exercisePoints(rows: ExercisePerformance[]): ExercisePoint[] {
  const visits = new Map<string, ExercisePerformance[]>();
  for (const row of rows) { const group = visits.get(row.sessionId) ?? []; group.push(row); visits.set(row.sessionId, group); }
  return [...visits.values()].map(group => ({ sessionId: group[0]!.sessionId,
    finishedAt: group[0]!.finishedAt, workoutName: group[0]!.workoutName,
    representative: representativeSet(group),
    loggedTonnageKg: group.some(row => row.weightKg !== null)
      ? group.reduce((sum, row) => sum + (row.weightKg === null ? 0 : row.weightKg * row.reps), 0) : null,
  })).sort((a, b) => a.finishedAt.localeCompare(b.finishedAt) || a.sessionId.localeCompare(b.sessionId));
}
