import type { SetKind, WeightMode } from './training';

export interface LoadRuleSnapshot {
  basis: 'planned_target' | 'performed_weight'; referenceSetTemplateId: string | null; percent: number;
  referenceWeightKg: number | null; resolvedWeightKg: number | null; weightMode: WeightMode;
}

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
export type ChangeScope = 'session' | 'program';
export interface SessionLoadRule {
  basis: 'planned_target' | 'performed_weight'; referenceSetId: string; percent: number;
  weightMode: WeightMode; suspended: boolean;
}
export interface SetAdjustment {
  id: string; setId: string; scope: ChangeScope; action: string; payload: Record<string, unknown>; changedAt: string;
}
export interface SetPassage {
  id: string; sessionId: string; setId: string; action: 'skip' | 'reintegrate'; revision: number; changedAt: string;
}
export interface SessionSet {
  id: string; sessionId: string; sessionExerciseId: string; sourceSetTemplateId: string | null;
  sortOrder: number; seriesIndex: number; label: string; kind: SetKind; notes: string;
  /** Immutable targets captured when the workout started. */
  originalTargets: SetTargets;
  /** Targets for this execution; only unperformed sets can be changed. */
  targets: SetTargets;
  /** Immutable provenance, never reevaluated using a live program/performance. */
  loadRuleSnapshot?: LoadRuleSnapshot | null;
  loadRule?: SessionLoadRule;
  addition?: { key: string; scope: ChangeScope; addedAt: string };
  editScope?: ChangeScope;
  /** Derived from the append-only passage journal, never a performance. */
  skippedAt?: string;
  passageRevision?: number;
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
  personalNote?: string;
  exerciseNotes?: Record<string, string>;
  adjustments?: SetAdjustment[];
  passages?: SetPassage[];
}
export type SessionStep =
  | { phase: 'set'; set: SessionSet; exercise: SessionExercise }
  | { phase: 'rest'; rest: RestInterval; performed: PerformedSet; nextSet: SessionSet | null; exercise: SessionExercise }
  | { phase: 'between_sets'; performed: PerformedSet; nextSet: SessionSet | null; exercise: SessionExercise }
  | { phase: 'ready_to_finish' }
  | { phase: 'completed' };

/** Progress counts actual results separately from skipped and remaining series. */
export function remainingSessionSets(session: WorkoutSession): SessionSet[] {
  const done = new Set(session.performances.map(item => item.sessionSetId));
  return session.sets.filter(item => !item.skippedAt && !done.has(item.id));
}
export function sessionProgress(session: WorkoutSession) {
  const skipped = session.sets.filter(item => !!item.skippedAt).length;
  return { performed: session.performances.length, skipped, remaining: remainingSessionSets(session).length, total: session.sets.length };
}
export function sessionProgressLabel(session: WorkoutSession): string {
  const p = sessionProgress(session);
  return p.skipped ? `${p.performed} série${p.performed > 1 ? 's' : ''} réalisée${p.performed > 1 ? 's' : ''} · ${p.skipped} passée${p.skipped > 1 ? 's' : ''} · ${p.remaining} restante${p.remaining > 1 ? 's' : ''}`
    : `${p.performed} / ${p.total} séries validées`;
}
export const PASSED_REFERENCE_MESSAGE = 'La série de référence est passée. Utilisez « Réintégrer la série » ou choisissez une charge manuelle.';

/** A pending rest/advance remains visible even after the last remaining series
 * is skipped. Only the existing manual actions may close that transition. */
export function selectSessionStep(session: WorkoutSession): SessionStep {
  if (session.status === 'completed') return { phase: 'completed' };
  const remaining = remainingSessionSets(session);
  const nextSet = remaining.find(item => item.sessionExerciseId === session.selectedExerciseId) ?? remaining[0] ?? null;
  const pending = session.performances.find(item => item.advancedAt === null);
  const exerciseId = nextSet?.sessionExerciseId ?? session.sets.find(item => item.id === pending?.sessionSetId)?.sessionExerciseId;
  const exercise = session.exercises.find(item => item.id === exerciseId);
  if (pending) {
    if (!exercise) throw new Error('Exercice de la séance introuvable.');
    const rest = session.rests.find(item => item.performedSetId === pending.id && item.endedAt === null);
    if (rest) return { phase: 'rest', rest, performed: pending, nextSet, exercise };
    return { phase: 'between_sets', performed: pending, nextSet, exercise };
  }
  if (!nextSet) return { phase: 'ready_to_finish' };
  if (!exercise) throw new Error('Exercice de la séance introuvable.');
  return { phase: 'set', set: nextSet, exercise };
}

export function remainingSessionExercises(session: WorkoutSession): { exercise: SessionExercise; sets: SessionSet[] }[] {
  const remaining = remainingSessionSets(session);
  return session.exercises.map(exercise => ({ exercise, sets: remaining.filter(item => item.sessionExerciseId === exercise.id) }))
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
