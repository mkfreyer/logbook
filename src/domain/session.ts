import type { SetKind, WeightMode } from './training';

export interface SetTargets {
  repsMin: number; repsMax: number; targetWeightKg: number | null;
  targetRir: number | null; restAfterSec: number;
}
export interface SessionExercise {
  id: string; sessionId: string; sourceWorkoutExerciseId: string; sourceCatalogExerciseId: string;
  sortOrder: number; name: string; muscleGroup: string; equipment: string;
  instructions: string; notes: string; weightMode: WeightMode;
}
export interface SessionSet {
  id: string; sessionId: string; sessionExerciseId: string; sourceSetTemplateId: string;
  sortOrder: number; seriesIndex: number; label: string; kind: SetKind; notes: string;
  /** Immutable targets captured when the workout started. */
  originalTargets: SetTargets;
  /** Targets for this execution; only unperformed sets can be changed. */
  targets: SetTargets;
}
export interface ActualSetInput { weightKg: number | null; reps: number; rir: number | null }
export interface PerformedSet extends ActualSetInput {
  id: string; sessionId: string; sessionSetId: string; sortOrder: number;
  performedAt: string; advancedAt: string | null;
}
export interface RestPause { id: string; startedAt: string; endedAt: string | null }
export interface RestInterval {
  id: string; sessionId: string; performedSetId: string; plannedSeconds: number;
  startedAt: string; endedAt: string | null;
  /** Frozen on completion. Chronological time includes pauses; active time excludes them. */
  chronologicalMs: number | null; activeMs: number | null; pauses: RestPause[];
}
export interface WorkoutSession {
  id: string; sourceWorkoutTemplateId: string; sourceProgramId: string;
  workoutName: string; programName: string; status: 'active' | 'completed';
  startedAt: string; finishedAt: string | null;
  exercises: SessionExercise[]; sets: SessionSet[]; performances: PerformedSet[]; rests: RestInterval[];
}
export type SessionStep =
  | { phase: 'set'; set: SessionSet; exercise: SessionExercise }
  | { phase: 'rest'; rest: RestInterval; performed: PerformedSet; nextSet: SessionSet; exercise: SessionExercise }
  | { phase: 'between_sets'; performed: PerformedSet; nextSet: SessionSet; exercise: SessionExercise }
  | { phase: 'ready_to_finish' }
  | { phase: 'completed' };

/** Progress is derived from persisted records, never a screen-local series counter. */
export function selectSessionStep(session: WorkoutSession): SessionStep {
  if (session.status === 'completed') return { phase: 'completed' };
  const performedIds = new Set(session.performances.map(item => item.sessionSetId));
  const nextSet = session.sets.find(item => !performedIds.has(item.id));
  if (!nextSet) return { phase: 'ready_to_finish' };
  const exercise = session.exercises.find(item => item.id === nextSet.sessionExerciseId);
  if (!exercise) throw new Error('Exercice de la séance introuvable.');
  const pending = session.performances.find(item => item.advancedAt === null);
  if (pending) {
    const rest = session.rests.find(item => item.performedSetId === pending.id && item.endedAt === null);
    if (rest) return { phase: 'rest', rest, performed: pending, nextSet, exercise };
    return { phase: 'between_sets', performed: pending, nextSet, exercise };
  }
  return { phase: 'set', set: nextSet, exercise };
}
