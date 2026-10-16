import { SessionStateError } from '../domain/sessionError';
import type { Database } from './types';
import type { ChangeScope, SessionSet, WorkoutSession } from '../domain/session';
import type { SetTemplateInput } from '../domain/training';
import { percentageWeight } from '../domain/series';
import { cleanSet, writePreparedSet } from './trainingRepository';

export async function hasProgramLink(db: Database, session: WorkoutSession, exerciseId: string, setId?: string): Promise<boolean> {
  const exercise = session.exercises.find(item => item.id === exerciseId);
  if (!exercise || session.replacements?.some(item => item.toExerciseId === exerciseId)) return false;
  const row = await db.getFirstAsync(`SELECT w.id FROM workout_exercises w JOIN workout_templates t ON t.id = w.workout_template_id
    JOIN programs p ON p.id = t.program_id JOIN exercise_catalog c ON c.id = w.exercise_id
    WHERE w.id = ? AND t.id = ? AND p.id = ? AND c.id = ? AND c.weight_mode = ?`,
    exercise.sourceWorkoutExerciseId, session.sourceWorkoutTemplateId, session.sourceProgramId, exercise.sourceCatalogExerciseId, exercise.weightMode);
  if (!row) return false;
  if (!setId) return true;
  const series = session.sets.find(item => item.id === setId);
  return !!series?.sourceSetTemplateId && !!await db.getFirstAsync('SELECT id FROM set_templates WHERE id = ? AND workout_exercise_id = ?', series.sourceSetTemplateId, exercise.sourceWorkoutExerciseId);
}

export async function logAdjustment(db: Database, sessionId: string, setId: string, scope: ChangeScope,
  action: string, payload: unknown, stamp: string, id: () => string) {
  await db.runAsync(`INSERT INTO session_set_adjustments (id, session_id, session_set_id, scope, action, payload, changed_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)`, id(), sessionId, setId, scope, action, JSON.stringify(payload), stamp);
}

/** IDs are execution IDs, not positions or live template references. */
export async function saveExecutionSet(db: Database, session: WorkoutSession, exerciseId: string, setId: string,
  input: SetTemplateInput, scope: ChangeScope, stamp: string, id: () => string, existing?: SessionSet, additionKey?: string) {
  if (scope !== 'session' && scope !== 'program') throw new SessionStateError('Choisissez « Cette séance » ou « Programme ».');
  const clean = cleanSet(input), exercise = session.exercises.find(item => item.id === exerciseId);
  if (!exercise) throw new SessionStateError('Cet exercice est introuvable dans cet entraînement.');
  if (existing && session.performances.some(item => item.sessionSetId === setId)) throw new SessionStateError('Cette série est déjà validée. Ses résultats et ses objectifs sont conservés.');
  if (!existing && session.replacements?.some(item => item.fromExerciseId === exerciseId)) throw new SessionStateError('Choisissez l’exercice de remplacement actuellement présent dans la séance.');
  // Completed exercises may receive an explicit extra set before the workout closes.
  // No already performed row or interval is shifted to insert it.
  const incoming = session.sets.filter(item => item.loadRule?.referenceSetId === setId && !item.loadRule.suspended);
  if (incoming.length && (clean.loadRule || !['work','top_set','custom'].includes(clean.kind) ||
      incoming.some(item => item.kind === 'back_off' && clean.kind !== 'top_set'))) {
    throw new SessionStateError('Cette série sert de référence. Retirez ses liens avant de changer son type ou de la rendre calculée.');
  }
  const reference = clean.loadRule ? session.sets.find(item => item.id === clean.loadRule!.referenceSetId) : null;
  if (clean.loadRule && (!reference || reference.id === setId || reference.sessionExerciseId !== exerciseId || reference.loadRule ||
      !['work','top_set','custom'].includes(reference.kind) || clean.kind === 'back_off' && reference.kind !== 'top_set')) {
    throw new SessionStateError('Choisissez une référence manuelle du même exercice réel (un top set pour un back-off). Les chaînes sont interdites.');
  }
  let sourceId = existing?.sourceSetTemplateId ?? null;
  if (scope === 'program') {
    if (!await hasProgramLink(db, session, exerciseId, existing?.id)) {
      throw new SessionStateError('La série du programme a été supprimée, son exercice remplacé ou son mode de charge modifié. Choisissez « Cette séance » ; aucun modèle inexistant ne sera modifié.');
    }
    let programRule = clean.loadRule;
    if (programRule) {
      if (!reference?.sourceSetTemplateId || !await hasProgramLink(db, session, exerciseId, reference.id)) {
        throw new SessionStateError('La référence n’existe pas dans le programme. Choisissez « Cette séance » ou une autre référence.');
      }
      programRule = { ...programRule, referenceSetId: reference.sourceSetTemplateId };
    }
    sourceId ??= id();
    await writePreparedSet(db, exercise.sourceWorkoutExerciseId, { ...clean, loadRule: programRule }, sourceId, stamp, !!existing);
  }
  const performance = reference && session.performances.find(item => item.sessionSetId === reference.id);
  const baseWeight = clean.loadRule?.basis === 'performed_weight' ? performance?.weightKg ?? null : reference?.targets.targetWeightKg ?? null;
  const targetWeight = clean.loadRule ? percentageWeight(baseWeight, clean.loadRule.percent) : clean.targetWeightKg;
  const target = { repsMin: clean.repsMin, repsMax: clean.repsMax, targetWeightKg: targetWeight, targetRir: clean.targetRir, restAfterSec: clean.restAfterSec };
  if (existing) {
    await db.runAsync(`UPDATE session_sets SET label = ?, kind = ?, notes = ?, reps_min = ?, reps_max = ?, target_weight_kg = ?, target_rir = ?, rest_after_sec = ?, edit_scope = ? WHERE id = ?`,
      clean.label, clean.kind, clean.notes, clean.repsMin, clean.repsMax, targetWeight, clean.targetRir, clean.restAfterSec, scope, setId);
    await db.runAsync('DELETE FROM session_set_load_rules WHERE session_set_id = ?', setId);
  } else {
    const positions = await db.getFirstAsync<{ global: number; series: number }>(`SELECT COALESCE(MAX(sort_order), -1) + 1 AS global,
      COALESCE(MAX(CASE WHEN session_exercise_id = ? THEN series_index END), -1) + 1 AS series FROM session_sets WHERE session_id = ?`, exerciseId, session.id);
    await db.runAsync(`INSERT INTO session_sets (id, session_id, session_exercise_id, legacy_source_set_template_id, source_set_template_id,
      sort_order, series_index, label, kind, notes, original_targets, reps_min, reps_max, target_weight_kg, target_rir, rest_after_sec,
      added_at, addition_scope, addition_key, initial_metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      setId, session.id, exerciseId, sourceId ?? '', sourceId, positions!.global, positions!.series, clean.label, clean.kind, clean.notes,
      JSON.stringify(target), clean.repsMin, clean.repsMax, targetWeight, clean.targetRir, clean.restAfterSec, stamp, scope, additionKey!, JSON.stringify({ label: clean.label, kind: clean.kind, notes: clean.notes }));
  }
  if (clean.loadRule && reference) {
    await db.runAsync(`INSERT INTO session_set_load_rules (session_set_id, session_id, reference_set_id, basis, percent, weight_mode)
      VALUES (?, ?, ?, ?, ?, ?)`, setId, session.id, reference.id, clean.loadRule.basis, clean.loadRule.percent, exercise.weightMode);
  }
  await logAdjustment(db, session.id, setId, scope, existing ? 'edit' : 'add', {
    targets: target, kind: clean.kind, label: clean.label, notes: clean.notes, rule: clean.loadRule,
    referenceWeightKg: clean.loadRule ? baseWeight : null, referencePerformanceId: performance?.id ?? null,
    resolvedWeightKg: targetWeight, sourceSetTemplateId: sourceId,
  }, stamp, id);
}

/** Recalculate only explicit rules, never manual overrides or performed targets. */
export async function resolveDependentRules(db: Database, session: WorkoutSession, referenceId: string,
  basis: 'planned_target' | 'performed_weight', stamp: string, id: () => string) {
  const reference = session.sets.find(item => item.id === referenceId);
  if (!reference) return;
  const performance = session.performances.find(item => item.sessionSetId === referenceId);
  const baseWeight = basis === 'performed_weight' ? performance?.weightKg ?? null : reference.targets.targetWeightKg;
  const done = new Set(session.performances.map(item => item.sessionSetId));
  for (const series of session.sets) {
    const rule = series.loadRule;
    if (!rule || rule.suspended || rule.referenceSetId !== referenceId || rule.basis !== basis || done.has(series.id)) continue;
    const exercise = session.exercises.find(item => item.id === series.sessionExerciseId)!;
    if (series.sessionExerciseId !== reference.sessionExerciseId || exercise.weightMode !== rule.weightMode) continue;
    const result = percentageWeight(baseWeight, rule.percent);
    await db.runAsync('UPDATE session_sets SET target_weight_kg = ? WHERE id = ?', result, series.id);
    await logAdjustment(db, session.id, series.id, 'session', 'resolve', { rule, referenceWeightKg: baseWeight,
      referencePerformanceId: performance?.id ?? null, resolvedWeightKg: result }, stamp, id);
  }
}

export async function suspendRulesFor(db: Database, session: WorkoutSession, setIds: string[], stamp: string, id: () => string) {
  const done = new Set(session.performances.map(item => item.sessionSetId));
  for (const series of session.sets) {
    if (!series.loadRule || done.has(series.id) || (!setIds.includes(series.id) && !setIds.includes(series.loadRule.referenceSetId))) continue;
    await db.runAsync('UPDATE session_set_load_rules SET suspended = 1 WHERE session_set_id = ?', series.id);
    await db.runAsync('UPDATE session_sets SET target_weight_kg = NULL WHERE id = ?', series.id);
    await logAdjustment(db, session.id, series.id, 'session', 'suspend', { rule: series.loadRule,
      reason: 'reference_removed_or_exercise_replaced' }, stamp, id);
  }
}
