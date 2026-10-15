import type { PerformedSet, SessionExercise, SessionSet, WorkoutSession } from './session';
import { replacementOrigin } from './session';
import type { WeightMode } from './training';

export interface ExerciseSummary {
  exercise: SessionExercise;
  performances: { performance: PerformedSet; series: SessionSet }[];
  replacedFrom: SessionExercise | null;
}
export interface SessionSummary {
  durationMs: number; performedSetCount: number; loggedTonnageKg: number | null;
  chargedSetCount: number; unchargedSetCount: number; meanRir: number | null; rirSetCount: number;
  tonnageByMode: Record<WeightMode, number>; exercises: ExerciseSummary[];
}

/** Split returns to a previous exercise into separate consecutive blocks, so a
 * historical detail follows actual validation order even after M2 free choices. */
export function chronologicalExerciseBlocks(summary: SessionSummary): ExerciseSummary[] {
  const ordered = summary.exercises.flatMap(group => group.performances.map(item => ({ group, item })))
    .sort((a, b) => a.item.performance.sortOrder - b.item.performance.sortOrder);
  const blocks: ExerciseSummary[] = [];
  for (const { group, item } of ordered) {
    const previous = blocks.at(-1);
    if (previous?.exercise.id === group.exercise.id) previous.performances.push(item);
    else blocks.push({ exercise: group.exercise, replacedFrom: group.replacedFrom, performances: [item] });
  }
  return blocks;
}

/** Tonnage is the sum of recorded kg × reps, including warm-ups. Per-hand kg are
 * counted once (no assumed number of hands); additional kg exclude body weight.
 * A missing weight is excluded, never imputed. This is not total displaced mass. */
export function summarizeSession(session: WorkoutSession): SessionSummary {
  if (session.status !== 'completed' || !session.finishedAt) throw new Error('Le bilan est disponible après la fin de la séance.');
  const durationMs = Date.parse(session.finishedAt) - Date.parse(session.startedAt);
  if (!Number.isFinite(durationMs) || durationMs < 0) throw new Error('Les horaires de cette séance sont incohérents.');
  const tonnageByMode: Record<WeightMode, number> = { total: 0, per_hand: 0, additional: 0 };
  const groups = new Map<string, ExerciseSummary>();
  let rirTotal = 0, rirSetCount = 0, chargedSetCount = 0;
  // Actual chronological order, not the program's positions or grid order.
  for (const performance of [...session.performances].sort((a, b) => a.sortOrder - b.sortOrder)) {
    const series = session.sets.find(item => item.id === performance.sessionSetId);
    const exercise = series && session.exercises.find(item => item.id === series.sessionExerciseId);
    if (!series || !exercise) throw new Error('Les résultats de cette séance sont incomplets. Réessayez.');
    let group = groups.get(exercise.id);
    if (!group) {
      group = { exercise, performances: [], replacedFrom: replacementOrigin(session, exercise.id) };
      groups.set(exercise.id, group);
    }
    group.performances.push({ performance, series });
    if (performance.weightKg !== null) {
      tonnageByMode[exercise.weightMode] += performance.weightKg * performance.reps;
      chargedSetCount++;
    }
    if (performance.rir !== null) { rirTotal += performance.rir; rirSetCount++; }
  }
  const loggedTonnageKg = chargedSetCount ? Object.values(tonnageByMode).reduce((sum, value) => sum + value, 0) : null;
  if (loggedTonnageKg !== null && !Number.isFinite(loggedTonnageKg)) throw new Error('Ces charges dépassent la plage de calcul du bilan.');
  return { durationMs, performedSetCount: session.performances.length, loggedTonnageKg,
    chargedSetCount, unchargedSetCount: session.performances.length - chargedSetCount,
    meanRir: rirSetCount ? rirTotal / rirSetCount : null, rirSetCount, tonnageByMode, exercises: [...groups.values()] };
}

export function formatSessionDuration(ms: number): string {
  const seconds = Math.max(0, Math.floor(ms / 1000)), hours = Math.floor(seconds / 3600);
  const minutes = Math.floor(seconds % 3600 / 60), rest = seconds % 60;
  return hours ? `${hours} h ${minutes.toString().padStart(2, '0')} min`
    : minutes ? `${minutes} min ${rest.toString().padStart(2, '0')} s` : `${rest} s`;
}
