import type { SetKind, WeightMode } from './training';

export interface SetTargets {
  repsMin: number; repsMax: number; targetWeightKg: number | null;
  targetRir: number | null; restAfterSec: number;
}
export interface SessionExercise {
  id: string; sessionId: string; sourceWorkoutExerciseId: string; sourceCatalogExerciseId: string;
  sortOrder: number; name: string; muscleGroup: string; equipment: string;
  instructions: string; notes: string; weightMode: WeightMode;
  /** Original program position; replacement snapshots share that position. */
  plannedOrder?: number;
}
export interface ExerciseReplacement {
  id: string; sessionId: string; fromExerciseId: string; toExerciseId: string;
  activeSetId: string; remainingSetCount: number; changedAt: string;
}
export interface ExerciseChoice {
  id: string; sessionId: string; exerciseId: string; expectedSetId: string; chosenAt: string;
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
  /** Optional only for legacy in-memory snapshots; SQLite v4 always reads these. */
  selectedExerciseId?: string | null;
  replacements?: ExerciseReplacement[];
  exerciseChoices?: ExerciseChoice[];
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
  const remaining = session.sets.filter(item => !performedIds.has(item.id));
  const nextSet = remaining.find(item => item.sessionExerciseId === session.selectedExerciseId) ?? remaining[0];
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

export function remainingSessionExercises(session: WorkoutSession): { exercise: SessionExercise; sets: SessionSet[] }[] {
  const performed = new Set(session.performances.map(item => item.sessionSetId));
  return session.exercises.map(exercise => ({ exercise,
    sets: session.sets.filter(item => item.sessionExerciseId === exercise.id && !performed.has(item.id)) }))
    .filter(item => item.sets.length > 0)
    .sort((a, b) => (a.exercise.plannedOrder ?? a.exercise.sortOrder) - (b.exercise.plannedOrder ?? b.exercise.sortOrder)
      || a.sets[0]!.sortOrder - b.sets[0]!.sortOrder);
}

/** Follow the retained chain to the initial programmed snapshot, including
 * intermediate alternatives on which no performance was ever recorded. */
export function replacementOrigin(session: WorkoutSession, exerciseId: string): SessionExercise | null {
  const visited = new Set<string>();
  let id = exerciseId;
  while (true) {
    if (visited.has(id)) throw new Error('La provenance de cet exercice est incohérente.');
    visited.add(id);
    const replacement = session.replacements?.find(item => item.toExerciseId === id);
    if (!replacement) break;
    id = replacement.fromExerciseId;
  }
  return id === exerciseId ? null : session.exercises.find(item => item.id === id) ?? null;
}
