import type { Database } from './types';
import type { ExerciseCatalogItem, WeightMode, SetTemplateInput } from '../domain/training';
import { selectSessionStep, remainingSessionSets, type ActualSetInput, type PerformedSet, type RestInterval, type RestPause,
  type SessionExercise, type SessionSet, type SetTargets, type WorkoutSession, type ExerciseReplacement, type ExerciseChoice } from '../domain/session';
import { calculateRestTiming } from '../domain/restTimer';
import { HistoryRepository } from './historyRepository';
import { readPlannedSets } from './plannedSets';
import { hasProgramLink, logAdjustment, saveExecutionSet, resolveDependentRules, suspendRulesFor } from './sessionSetOperations';
import type { ChangeScope, SessionLoadRule, SetAdjustment, SetPassage } from '../domain/session';
import type { LoadRuleSnapshot } from '../domain/session';

import { SessionStateError } from '../domain/sessionError';
export { SessionStateError } from '../domain/sessionError';

const sessionColumns = `id, source_workout_template_id AS sourceWorkoutTemplateId,
  source_program_id AS sourceProgramId, workout_name AS workoutName, program_name AS programName,
  status, started_at AS startedAt, finished_at AS finishedAt, selected_exercise_id AS selectedExerciseId`;
const targetColumns = `reps_min AS repsMin, reps_max AS repsMax, target_weight_kg AS targetWeightKg,
  target_rir AS targetRir, rest_after_sec AS restAfterSec`;
type SessionRow = Omit<WorkoutSession, 'exercises' | 'sets' | 'performances' | 'rests' | 'replacements' | 'exerciseChoices'>;
export type CompletedSessionEntry = Pick<WorkoutSession, 'id' | 'workoutName' | 'programName' | 'startedAt' | 'finishedAt'> & { performedSetCount: number };
type AdditionColumns = { additionKey: string | null; additionScope: ChangeScope | null; addedAt: string | null; editScope: ChangeScope | null };
type SetRow = Omit<SessionSet, 'targets' | 'originalTargets'> & SetTargets & AdditionColumns & { originalTargetsJson: string; loadRuleJson: string | null };
type ExerciseSource = {
  id: string; exerciseId: string; name: string; muscleGroup: string; equipment: string;
  instructions: string; notes: string; weightMode: WeightMode;
};

function integer(value: number, name: string, max = Number.MAX_SAFE_INTEGER): number {
  if (!Number.isSafeInteger(value) || value < 0 || value > max) throw new SessionStateError(`${name} : indiquez un entier entre 0 et ${max}.`);
  return value;
}
function weight(value: number | null): number | null {
  if (value !== null && (typeof value !== 'number' || !Number.isFinite(value) || value < 0)) {
    throw new SessionStateError('Indiquez une charge positive ou nulle, ou laissez le champ vide.');
  }
  return value;
}
function targets(input: SetTargets): SetTargets {
  const repsMin = integer(input.repsMin, 'Répétitions minimales');
  const repsMax = integer(input.repsMax, 'Répétitions maximales');
  if (repsMax < repsMin) throw new SessionStateError('Le maximum doit être supérieur ou égal au minimum.');
  return { repsMin, repsMax, targetWeightKg: weight(input.targetWeightKg),
    targetRir: input.targetRir === null ? null : integer(input.targetRir, 'RIR', 10),
    restAfterSec: integer(input.restAfterSec, 'Repos', 86400) };
}
function actual(input: ActualSetInput): ActualSetInput {
  return { weightKg: weight(input.weightKg), reps: integer(input.reps, 'Répétitions'),
    rir: input.rir === null ? null : integer(input.rir, 'RIR', 10) };
}

/** No execution has a cascading dependency on a preparation. All multi-row writes
 * are atomic, and return their committed snapshot. The exclusive Expo connection
 * prevents unrelated M0/M1.1 writes from being captured by our transaction.
 * Expo does not enable foreign keys on that connection: every inserted parent and
 * ownership is checked here, and this repository never deletes records. */
export class SessionRepository {
  private pendingWrite: Promise<void> = Promise.resolve();
  private readonly listeners = new Set<() => void>();
  private readonly completionListeners = new Set<() => void>();
  readonly history = new HistoryRepository(operation => this.read(() => operation(this.db)));
  constructor(private readonly db: Database, private readonly idFactory: () => string,
    private readonly now: () => string = () => new Date().toISOString()) {}

  /** Subscribers reread committed data; no clock or workout state lives in this event. */
  subscribe(listener: () => void): () => void {
    this.listeners.add(listener);
    return () => { this.listeners.delete(listener); };
  }

  subscribeCompleted(listener: () => void): () => void {
    this.completionListeners.add(listener);
    return () => { this.completionListeners.delete(listener); };
  }

  private write<T>(operation: (db: Database) => Promise<T>, completed?: () => boolean): Promise<T> {
    const result = this.pendingWrite.then(async () => {
      let value!: T;
      const task = async (db: Database) => { value = await operation(db); };
      if (this.db.withExclusiveTransactionAsync) await this.db.withExclusiveTransactionAsync(task);
      else await this.db.withTransactionAsync(() => task(this.db));
      // Observation must never turn an already committed save into a reported failure.
      for (const listener of this.listeners) { try { listener(); } catch { /* Observer owns its retry. */ } }
      if (completed?.()) for (const listener of this.completionListeners) { try { listener(); } catch { /* Observer owns its retry. */ } }
      return value;
    });
    this.pendingWrite = result.then(() => undefined, () => undefined);
    return result;
  }

  /** A multi-query snapshot must not straddle a replacement transaction. Sharing
   * the queue with writes keeps its exercise identities, series and cursor coherent. */
  private read<T>(operation: () => Promise<T>): Promise<T> {
    const result = this.pendingWrite.then(operation);
    this.pendingWrite = result.then(() => undefined, () => undefined);
    return result;
  }

  private stamp(session: WorkoutSession, extra: string[] = []): string {
    // Retain causal timestamp ordering even if the phone clock was moved backwards.
    return [this.now(), session.startedAt, session.finishedAt ?? session.startedAt, ...(session.adjustments ?? []).map(item => item.changedAt), ...(session.passages ?? []).map(item => item.changedAt), ...session.performances.map(item => item.advancedAt ?? item.performedAt),
      ...session.rests.flatMap(item => [item.endedAt ?? item.startedAt, ...item.pauses.map(pause => pause.endedAt ?? pause.startedAt)]),
      ...(session.replacements ?? []).map(item => item.changedAt), ...(session.exerciseChoices ?? []).map(item => item.chosenAt), ...extra].sort().at(-1)!;
  }

  private async readSession(db: Database, id: string): Promise<WorkoutSession | null> {
    const session = await db.getFirstAsync<SessionRow>(`SELECT ${sessionColumns} FROM workout_sessions WHERE id = ?`, id);
    if (!session) return null;
    const exercises = await db.getAllAsync<SessionExercise>(`SELECT id, session_id AS sessionId,
      source_workout_exercise_id AS sourceWorkoutExerciseId, source_catalog_exercise_id AS sourceCatalogExerciseId,
      sort_order AS sortOrder, planned_order AS plannedOrder, name, muscle_group AS muscleGroup, equipment, instructions, notes, weight_mode AS weightMode
      FROM session_exercises WHERE session_id = ? ORDER BY sort_order, id`, id);
    const rows = await db.getAllAsync<SetRow>(`SELECT id, session_id AS sessionId, session_exercise_id AS sessionExerciseId,
      source_set_template_id AS sourceSetTemplateId, sort_order AS sortOrder, series_index AS seriesIndex,
      addition_key AS additionKey, addition_scope AS additionScope, added_at AS addedAt, edit_scope AS editScope,
      label, kind, notes, original_targets AS originalTargetsJson, load_rule_snapshot AS loadRuleJson, ${targetColumns}
      FROM session_sets WHERE session_id = ? AND removed_at IS NULL ORDER BY sort_order, id`, id);
    const sets: SessionSet[] = rows.map(({ originalTargetsJson, loadRuleJson, additionKey, additionScope, addedAt, editScope, repsMin, repsMax, targetWeightKg, targetRir, restAfterSec, ...row }) =>
      ({ ...row, originalTargets: JSON.parse(originalTargetsJson) as SetTargets,
        ...(loadRuleJson ? { loadRuleSnapshot: JSON.parse(loadRuleJson) as LoadRuleSnapshot } : {}),
        ...(additionKey ? { addition: { key: additionKey, scope: additionScope!, addedAt: addedAt! } } : {}),
        ...(editScope ? { editScope } : {}),
        targets: { repsMin, repsMax, targetWeightKg, targetRir, restAfterSec } }));
    // Additional sets belong to their exercise; immutable global capture positions
    // and performed order are not renumbered to insert them.
    const exerciseOrder = new Map(exercises.map(e => [e.id, e.plannedOrder ?? e.sortOrder]));
    sets.sort((a,b) => exerciseOrder.get(a.sessionExerciseId)! - exerciseOrder.get(b.sessionExerciseId)!
      || a.seriesIndex - b.seriesIndex || a.sortOrder - b.sortOrder);
    const rules = await db.getAllAsync<Omit<SessionLoadRule, 'suspended'> & { setId: string; suspended: number }>(`SELECT session_set_id AS setId,
      reference_set_id AS referenceSetId, basis, percent, weight_mode AS weightMode, suspended FROM session_set_load_rules WHERE session_id = ?`, id);
    for (const { setId, suspended, ...rule } of rules) { const series = sets.find(item => item.id === setId); if (series) series.loadRule = { ...rule, suspended: !!suspended }; }
    const performances = await db.getAllAsync<PerformedSet>(`SELECT id, session_id AS sessionId, session_set_id AS sessionSetId,
      sort_order AS sortOrder, weight_kg AS weightKg, reps, rir, performed_at AS performedAt, advanced_at AS advancedAt
      FROM performed_sets WHERE session_id = ? ORDER BY sort_order, id`, id);
    const intervals = await db.getAllAsync<Omit<RestInterval, 'pauses'>>(`SELECT id, session_id AS sessionId,
      performed_set_id AS performedSetId, planned_seconds AS plannedSeconds, started_at AS startedAt, ended_at AS endedAt,
      chronological_ms AS chronologicalMs, active_ms AS activeMs FROM rest_intervals WHERE session_id = ? ORDER BY started_at, id`, id);
    const pauses = await db.getAllAsync<RestPause & { restId: string }>(`SELECT p.id, p.rest_interval_id AS restId,
      p.started_at AS startedAt, p.ended_at AS endedAt FROM rest_pauses p JOIN rest_intervals r ON r.id = p.rest_interval_id
      WHERE r.session_id = ? ORDER BY p.started_at, p.id`, id);
    const rests = intervals.map(interval => ({ ...interval, pauses: pauses.filter(pause => pause.restId === interval.id)
      .map(({ restId: _restId, ...pause }) => pause) }));
    const replacements = await db.getAllAsync<ExerciseReplacement>(`SELECT id, session_id AS sessionId,
      from_exercise_id AS fromExerciseId, to_exercise_id AS toExerciseId, active_set_id AS activeSetId,
      remaining_set_count AS remainingSetCount, changed_at AS changedAt FROM session_exercise_replacements
      WHERE session_id = ? ORDER BY changed_at, rowid`, id);
    const exerciseChoices = await db.getAllAsync<ExerciseChoice>(`SELECT id, session_id AS sessionId,
      exercise_id AS exerciseId, expected_set_id AS expectedSetId, chosen_at AS chosenAt FROM session_exercise_choices
      WHERE session_id = ? ORDER BY chosen_at, rowid`, id);
    const notes = await db.getAllAsync<{ exerciseId: string | null; body: string }>('SELECT session_exercise_id AS exerciseId, body FROM session_personal_notes WHERE session_id = ?', id);
    const adjustments = await db.getAllAsync<Omit<SetAdjustment, 'payload'> & { payload: string }>(`SELECT id, session_set_id AS setId,
      scope, action, payload, changed_at AS changedAt FROM session_set_adjustments WHERE session_id = ? ORDER BY changed_at, rowid`, id);
    const passages = await db.getAllAsync<SetPassage>(`SELECT id, session_id AS sessionId, session_set_id AS setId,
      action, revision, changed_at AS changedAt FROM session_set_passages WHERE session_id = ? ORDER BY rowid`, id);
    const byId = new Map(sets.map(series => [series.id, series]));
    for (const passage of passages) {
      const series = byId.get(passage.setId);
      if (!series) continue; // A withdrawn addition retains its journal in the export.
      series.passageRevision = passage.revision;
      if (passage.action === 'skip') series.skippedAt = passage.changedAt;
      else delete series.skippedAt;
    }
    return { ...session, exercises, sets, performances, rests, replacements, exerciseChoices,
      ...(passages.length ? { passages } : {}),
      ...(notes.some(n => !n.exerciseId) ? { personalNote: notes.find(n => !n.exerciseId)!.body } : {}),
      ...(notes.some(n => n.exerciseId) ? { exerciseNotes: Object.fromEntries(notes.filter(n => n.exerciseId).map(n => [n.exerciseId!, n.body])) } : {}),
      ...(adjustments.length ? { adjustments: adjustments.map(a => ({ ...a, payload: JSON.parse(a.payload) as Record<string, unknown> })) } : {}) };
  }

  private async requireSession(db: Database, id: string, activeOnly = true): Promise<WorkoutSession> {
    const session = await this.readSession(db, id);
    if (!session) throw new SessionStateError('Cet entraînement est introuvable.');
    if (activeOnly && session.status !== 'active') throw new SessionStateError('Cet entraînement est déjà terminé.');
    return session;
  }
  async getSession(id: string): Promise<WorkoutSession | null> {
    return this.read(() => this.readSession(this.db, id));
  }
  async getActiveSession(): Promise<WorkoutSession | null> {
    return this.read(async () => {
      const row = await this.db.getFirstAsync<{ id: string }>("SELECT id FROM workout_sessions WHERE status = 'active'");
      return row ? this.readSession(this.db, row.id) : null;
    });
  }

  async listCompletedSessions(): Promise<CompletedSessionEntry[]> {
    return this.read(() => this.db.getAllAsync<CompletedSessionEntry>(`SELECT s.id, s.workout_name AS workoutName,
      s.program_name AS programName, s.started_at AS startedAt, s.finished_at AS finishedAt,
      (SELECT COUNT(*) FROM performed_sets WHERE session_id = s.id) AS performedSetCount
      FROM workout_sessions s WHERE s.status = 'completed' ORDER BY s.finished_at DESC, s.id`));
  }

  startOrResume(workoutId: string): Promise<WorkoutSession> {
    return this.write(async db => {
      const existing = await db.getFirstAsync<{ id: string }>("SELECT id FROM workout_sessions WHERE status = 'active'");
      if (existing) return this.requireSession(db, existing.id);
      const source = await db.getFirstAsync<{ id: string; programId: string; name: string; programName: string }>(
        `SELECT w.id, w.program_id AS programId, w.name, p.name AS programName
         FROM workout_templates w JOIN programs p ON p.id = w.program_id WHERE w.id = ?`, workoutId);
      if (!source) throw new SessionStateError('Cette séance programmée est introuvable.');
      const sourceExercises = await db.getAllAsync<ExerciseSource>(`SELECT w.id, w.exercise_id AS exerciseId,
        e.name, e.muscle_group AS muscleGroup, e.equipment, e.instructions, w.notes, e.weight_mode AS weightMode
        FROM workout_exercises w JOIN exercise_catalog e ON e.id = w.exercise_id
        WHERE w.workout_template_id = ? ORDER BY w.sort_order, w.id`, workoutId);
      if (!sourceExercises.length) throw new SessionStateError('Ajoutez un exercice et ses séries avant de démarrer.');
      const id = this.idFactory(), stamp = this.now();
      await db.runAsync(`INSERT INTO workout_sessions (id, source_workout_template_id, source_program_id, workout_name,
        program_name, status, started_at) VALUES (?, ?, ?, ?, ?, 'active', ?)`, id, source.id, source.programId, source.name, source.programName, stamp);
      let globalOrder = 0;
      for (const [exerciseOrder, exercise] of sourceExercises.entries()) {
        const series = await readPlannedSets(db, exercise.id);
        if (!series.length) throw new SessionStateError(`Ajoutez au moins une série à « ${exercise.name} » avant de démarrer.`);
        const exerciseId = this.idFactory();
        await db.runAsync(`INSERT INTO session_exercises (id, session_id, source_workout_exercise_id,
          source_catalog_exercise_id, sort_order, planned_order, name, muscle_group, equipment, instructions, notes, weight_mode)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`, exerciseId, id, exercise.id, exercise.exerciseId,
        exerciseOrder, exerciseOrder, exercise.name, exercise.muscleGroup, exercise.equipment, exercise.instructions, exercise.notes, exercise.weightMode);
        const seriesIds = new Map(series.map(item => [item.id, this.idFactory()]));
        for (const [seriesIndex, seriesSource] of series.entries()) {
          const clean = targets(seriesSource);
          const rule = seriesSource.loadRule;
          const loadRuleSnapshot: LoadRuleSnapshot | null = rule ? { basis: rule.basis,
            referenceSetTemplateId: rule.referenceSetId, percent: rule.percent,
            referenceWeightKg: rule.basis === 'planned_target' ? series.find(item => item.id === rule.referenceSetId)?.targetWeightKg ?? null : null,
            resolvedWeightKg: clean.targetWeightKg, weightMode: exercise.weightMode } : null;
          await db.runAsync(`INSERT INTO session_sets (id, session_id, session_exercise_id, legacy_source_set_template_id, source_set_template_id,
            sort_order, series_index, label, kind, notes, original_targets, reps_min, reps_max, target_weight_kg, target_rir, rest_after_sec, load_rule_snapshot, initial_metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`, seriesIds.get(seriesSource.id)!, id, exerciseId, seriesSource.id, seriesSource.id,
          globalOrder++, seriesIndex, seriesSource.label, seriesSource.kind, seriesSource.notes, JSON.stringify(clean),
          clean.repsMin, clean.repsMax, clean.targetWeightKg, clean.targetRir, clean.restAfterSec, loadRuleSnapshot ? JSON.stringify(loadRuleSnapshot) : null, JSON.stringify({ label: seriesSource.label, kind: seriesSource.kind, notes: seriesSource.notes }));
        }
        for (const seriesSource of series) {
          const rule = seriesSource.loadRule, referenceId = rule?.referenceSetId ? seriesIds.get(rule.referenceSetId) : null;
          if (rule && referenceId) await db.runAsync(`INSERT INTO session_set_load_rules (session_set_id, session_id, reference_set_id, basis, percent, weight_mode)
            VALUES (?, ?, ?, ?, ?, ?)`, seriesIds.get(seriesSource.id)!, id, referenceId, rule.basis, rule.percent, exercise.weightMode);
        }
      }
      return this.requireSession(db, id);
    });
  }

  validateSet(sessionId: string, setId: string, input: ActualSetInput, expectedPassageRevision = 0): Promise<WorkoutSession> {
    return this.write(async db => {
      const clean = actual(input), session = await this.requireSession(db, sessionId);
      const series = session.sets.find(item => item.id === setId);
      if (series?.skippedAt) throw new SessionStateError('Réintégrer la série avant de la valider.');
      integer(expectedPassageRevision, 'Version de la série');
      if ((series?.passageRevision ?? 0) !== expectedPassageRevision) throw new SessionStateError('Le statut de cette série a changé. Actualisez avant de valider sa performance.');
      // Idempotence is scoped to this exact immutable series, never the next one.
      if (session.performances.some(item => item.sessionSetId === setId)) return session;
      const step = selectSessionStep(session);
      if (step.phase !== 'set' || step.set.id !== setId) throw new SessionStateError('Cette série n’est pas la série active. Reprenez votre entraînement.');
      const stamp = this.stamp(session), performedId = this.idFactory();
      const remaining = remainingSessionSets(session).filter(item => item.id !== setId);
      const hasNext = remaining.length > 0;
      await db.runAsync(`INSERT INTO performed_sets (id, session_id, session_set_id, sort_order, weight_kg, reps, rir, performed_at, advanced_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`, performedId, sessionId, setId, session.performances.length,
      clean.weightKg, clean.reps, clean.rir, stamp, hasNext ? null : stamp);
      await resolveDependentRules(db, { ...session, performances: [...session.performances, {
        id: performedId, sessionId, sessionSetId: setId, sortOrder: session.performances.length,
        ...clean, performedAt: stamp, advancedAt: hasNext ? null : stamp,
      }] }, setId, 'performed_weight', stamp, this.idFactory);
      // A declared per-series interval is used as-is, also at an exercise boundary.
      // There is no invented transition duration and no rest after the final series.
      if (hasNext && step.set.targets.restAfterSec > 0) {
        await db.runAsync(`INSERT INTO rest_intervals (id, session_id, performed_set_id, planned_seconds, started_at)
          VALUES (?, ?, ?, ?, ?)`, this.idFactory(), sessionId, performedId, step.set.targets.restAfterSec, stamp);
      }
      // An explicit choice holds through this exercise only. Then resume original
      // program order among all unfinished series, including temporarily skipped ones.
      if (session.selectedExerciseId && !remaining.some(item => item.sessionExerciseId === session.selectedExerciseId)) {
        await db.runAsync('UPDATE workout_sessions SET selected_exercise_id = NULL WHERE id = ?', sessionId);
      }
      return this.requireSession(db, sessionId);
    });
  }

  pauseRest(sessionId: string, restId: string): Promise<WorkoutSession> {
    return this.write(async db => {
      const session = await this.requireSession(db, sessionId), rest = this.requireRest(session, restId);
      if (rest.pauses.some(item => item.endedAt === null)) return session;
      await db.runAsync('INSERT INTO rest_pauses (id, rest_interval_id, started_at) VALUES (?, ?, ?)', this.idFactory(), restId, this.stamp(session));
      return this.requireSession(db, sessionId);
    });
  }
  resumeRest(sessionId: string, restId: string): Promise<WorkoutSession> {
    return this.write(async db => {
      const session = await this.requireSession(db, sessionId); this.requireRest(session, restId);
      await db.runAsync('UPDATE rest_pauses SET ended_at = ? WHERE rest_interval_id = ? AND ended_at IS NULL', this.stamp(session), restId);
      return this.requireSession(db, sessionId);
    });
  }
  private requireRest(session: WorkoutSession, restId: string): RestInterval {
    const step = selectSessionStep(session);
    if (step.phase !== 'rest' || step.rest.id !== restId) throw new SessionStateError('Ce repos n’est plus actif. Reprenez votre entraînement.');
    return step.rest;
  }
  completeRest(sessionId: string, restId: string): Promise<WorkoutSession> {
    return this.write(async db => {
      const session = await this.requireSession(db, sessionId);
      if (session.rests.some(item => item.id === restId && item.endedAt !== null)) return session;
      const rest = this.requireRest(session, restId), stamp = this.stamp(session);
      const timing = calculateRestTiming(rest, Date.parse(stamp));
      await db.runAsync('UPDATE rest_pauses SET ended_at = ? WHERE rest_interval_id = ? AND ended_at IS NULL', stamp, restId);
      await db.runAsync('UPDATE rest_intervals SET ended_at = ?, chronological_ms = ?, active_ms = ? WHERE id = ?',
        stamp, timing.chronologicalMs, timing.activeMs, restId);
      await db.runAsync('UPDATE performed_sets SET advanced_at = ? WHERE id = ?', stamp, rest.performedSetId);
      return this.requireSession(db, sessionId);
    });
  }
  advanceAfterSet(sessionId: string, performedSetId: string): Promise<WorkoutSession> {
    return this.write(async db => {
      const session = await this.requireSession(db, sessionId);
      if (session.performances.some(item => item.id === performedSetId && item.advancedAt !== null)) return session;
      const step = selectSessionStep(session);
      if (step.phase !== 'between_sets' || step.performed.id !== performedSetId) throw new SessionStateError('Validez d’abord la série ou terminez son repos.');
      await db.runAsync('UPDATE performed_sets SET advanced_at = ? WHERE id = ?', this.stamp(session), performedSetId);
      return this.requireSession(db, sessionId);
    });
  }

  /** A choice changes only the next unperformed series. An active rest and its
   * pauses are left open until the user explicitly completes it. */
  chooseNextExercise(sessionId: string, exerciseId: string, expectedSetId: string): Promise<WorkoutSession> {
    return this.write(async db => {
      const session = await this.requireSession(db, sessionId);
      if (session.selectedExerciseId === exerciseId) return session;
      const step = selectSessionStep(session);
      const next = step.phase === 'set' ? step.set : step.phase === 'rest' || step.phase === 'between_sets' ? step.nextSet : null;
      if (!next || next.id !== expectedSetId) throw new SessionStateError('La série active a changé. Actualisez les exercices restants.');
      if (!session.exercises.some(item => item.id === exerciseId) ||
          !remainingSessionSets(session).some(item => item.sessionExerciseId === exerciseId)) {
        throw new SessionStateError('Cet exercice n’a plus de série à effectuer dans cet entraînement.');
      }
      await db.runAsync(`INSERT INTO session_exercise_choices (id, session_id, exercise_id, expected_set_id, chosen_at)
        VALUES (?, ?, ?, ?, ?)`, this.idFactory(), sessionId, exerciseId, next.id, this.stamp(session));
      await db.runAsync('UPDATE workout_sessions SET selected_exercise_id = ? WHERE id = ?', exerciseId, sessionId);
      return this.requireSession(db, sessionId);
    });
  }

  /** Split only unperformed series into a new immutable exercise snapshot.
   * Prior performances keep their original series, exercise and unit. */
  replaceExercise(sessionId: string, fromExerciseId: string, catalogId: string, expectedSetId: string): Promise<WorkoutSession> {
    return this.write(async db => {
      const session = await this.requireSession(db, sessionId);
      const previous = (session.replacements ?? []).find(item => item.fromExerciseId === fromExerciseId);
      if (previous && previous.activeSetId === expectedSetId &&
          session.exercises.find(item => item.id === previous.toExerciseId)?.sourceCatalogExerciseId === catalogId) return session;
      if (previous) throw new SessionStateError('Cet exercice a déjà été remplacé. Les séries réintégrées conservent l’exercice initial ; réalisez-les ou utilisez « Passer cette série ».');
      const step = selectSessionStep(session);
      if (step.phase !== 'set' || step.set.id !== expectedSetId || step.exercise.id !== fromExerciseId) {
        throw new SessionStateError('Reprenez la série active avant de remplacer son exercice. Un repos doit être terminé manuellement.');
      }
      if (catalogId === step.exercise.sourceCatalogExerciseId) throw new SessionStateError('Choisissez un exercice différent.');
      const catalog = await db.getFirstAsync<ExerciseCatalogItem>(`SELECT id, name, muscle_group AS muscleGroup,
        equipment, instructions, weight_mode AS weightMode FROM exercise_catalog WHERE id = ?`, catalogId);
      if (!catalog) throw new SessionStateError('Cet exercice n’est plus dans la bibliothèque.');
      const remaining = remainingSessionSets(session).filter(item => item.sessionExerciseId === fromExerciseId);
      if (!remaining.length) throw new SessionStateError('Cet exercice est déjà terminé.');
      const id = this.idFactory(), stamp = this.stamp(session);
      const order = Math.max(...session.exercises.map(item => item.sortOrder)) + 1;
      await db.runAsync(`INSERT INTO session_exercises (id, session_id, source_workout_exercise_id,
        source_catalog_exercise_id, sort_order, planned_order, name, muscle_group, equipment, instructions, notes, weight_mode)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`, id, sessionId, step.exercise.sourceWorkoutExerciseId,
      catalog.id, order, step.exercise.plannedOrder ?? step.exercise.sortOrder, catalog.name,
      catalog.muscleGroup, catalog.equipment, catalog.instructions, step.exercise.notes, catalog.weightMode);
      await suspendRulesFor(db, session, remaining.map(item => item.id), stamp, this.idFactory);
      for (const series of remaining) {
        await db.runAsync(`UPDATE session_sets SET session_exercise_id = ?, target_weight_kg = NULL
          WHERE id = ? AND session_id = ? AND NOT EXISTS (SELECT 1 FROM performed_sets WHERE session_set_id = session_sets.id)`,
        id, series.id, sessionId);
      }
      await db.runAsync(`INSERT INTO session_exercise_replacements (id, session_id, from_exercise_id,
        to_exercise_id, active_set_id, remaining_set_count, changed_at) VALUES (?, ?, ?, ?, ?, ?, ?)`,
      this.idFactory(), sessionId, fromExerciseId, id, expectedSetId, remaining.length, stamp);
      await db.runAsync('UPDATE workout_sessions SET selected_exercise_id = ? WHERE id = ?', id, sessionId);
      return this.requireSession(db, sessionId);
    });
  }

  /** Kept for the original manual editor/API; all paths use the same guards. */
  updateSetTargets(sessionId: string, setId: string, input: SetTargets, scope: ChangeScope): Promise<WorkoutSession> {
    return this.write(async db => {
      const session = await this.requireSession(db, sessionId), series = session.sets.find(item => item.id === setId);
      if (!series) throw new SessionStateError('Cette série est introuvable.');
      await saveExecutionSet(db, session, series.sessionExerciseId, setId, { ...targets(input), label: series.label, kind: series.kind, notes: series.notes }, scope, this.stamp(session), this.idFactory, series);
      await resolveDependentRules(db, await this.requireSession(db, sessionId), setId, 'planned_target', this.stamp(session), this.idFactory);
      return this.requireSession(db, sessionId);
    });
  }

  canUpdateProgram(sessionId: string, exerciseId: string, setId?: string): Promise<boolean> {
    return this.read(async () => hasProgramLink(this.db, await this.requireSession(this.db, sessionId), exerciseId, setId));
  }

  addSet(sessionId: string, exerciseId: string, input: SetTemplateInput, scope: ChangeScope, additionKey: string): Promise<WorkoutSession> {
    return this.write(async db => {
      const session = await this.requireSession(db, sessionId);
      if (typeof additionKey !== 'string' || !additionKey.trim() || additionKey.length > 100) throw new SessionStateError('Identifiant d’ajout invalide.');
      // The persisted token survives uncertain responses/retries, including a removed
      // extra series: the same intent can never silently append another one.
      if (await db.getFirstAsync('SELECT id FROM session_sets WHERE session_id = ? AND addition_key = ?', sessionId, additionKey)) return session;
      await saveExecutionSet(db, session, exerciseId, this.idFactory(), input, scope, this.stamp(session), this.idFactory, undefined, additionKey);
      return this.requireSession(db, sessionId);
    });
  }

  updateSet(sessionId: string, setId: string, input: SetTemplateInput, scope: ChangeScope): Promise<WorkoutSession> {
    return this.write(async db => {
      const session = await this.requireSession(db, sessionId), series = session.sets.find(item => item.id === setId);
      if (!series) throw new SessionStateError('Cette série est introuvable.');
      const stamp = this.stamp(session);
      await saveExecutionSet(db, session, series.sessionExerciseId, setId, input, scope, stamp, this.idFactory, series);
      await resolveDependentRules(db, await this.requireSession(db, sessionId), setId, 'planned_target', stamp, this.idFactory);
      return this.requireSession(db, sessionId);
    });
  }

  deleteAddedSet(sessionId: string, setId: string): Promise<WorkoutSession> {
    return this.write(async db => {
      const session = await this.requireSession(db, sessionId), series = session.sets.find(item => item.id === setId);
      if (!series) return session;
      if (series.skippedAt) throw new SessionStateError('Réintégrer la série avant de retirer cet ajout.');
      if (!series.addition || session.performances.some(item => item.sessionSetId === setId)) throw new SessionStateError('Seule une série ajoutée non validée peut être retirée.');
      if (session.rests.some(item => item.endedAt === null) && remainingSessionSets(session).length <= 1) throw new SessionStateError('Terminez explicitement le repos avant de retirer la dernière série restante.');
      const stamp = this.stamp(session);
      await suspendRulesFor(db, session, [setId], stamp, this.idFactory);
      await logAdjustment(db, sessionId, setId, 'session', 'delete', { programPreserved: true }, stamp, this.idFactory);
      // Retain provenance/log foreign keys. Only the execution's remaining list is
      // affected; a prior Program addition is preserved for future workouts.
      await db.runAsync('UPDATE session_sets SET removed_at = ? WHERE id = ?', stamp, setId);
      if (session.selectedExerciseId === series.sessionExerciseId && !session.sets.some(item => item.id !== setId && item.sessionExerciseId === series.sessionExerciseId && !item.skippedAt && !session.performances.some(p => p.sessionSetId === item.id))) {
        await db.runAsync('UPDATE workout_sessions SET selected_exercise_id = NULL WHERE id = ?', sessionId);
      }
      return this.requireSession(db, sessionId);
    });
  }

  skipSet(sessionId: string, setId: string, expectedRevision: number): Promise<WorkoutSession> {
    return this.changeSetPassage(sessionId, setId, expectedRevision, 'skip');
  }

  reintegrateSet(sessionId: string, setId: string, expectedRevision: number): Promise<WorkoutSession> {
    return this.changeSetPassage(sessionId, setId, expectedRevision, 'reintegrate');
  }

  private changeSetPassage(sessionId: string, setId: string, expectedRevision: number, action: SetPassage['action']): Promise<WorkoutSession> {
    return this.write(async db => {
      const session = await this.requireSession(db, sessionId), series = session.sets.find(item => item.id === setId);
      if (!series) throw new SessionStateError('Cette série est introuvable ou a été retirée.');
      if (session.performances.some(item => item.sessionSetId === setId)) throw new SessionStateError('Cette série est déjà réalisée. Sa performance reste conservée.');
      integer(expectedRevision, 'Version de la série');
      const revision = series.passageRevision ?? 0, skipped = !!series.skippedAt, requested = action === 'skip';
      if (revision !== expectedRevision) {
        // Repeating the same intent is harmless; a response from an earlier
        // skip/reintegration cycle must never overwrite a more recent decision.
        if (revision === expectedRevision + 1 && skipped === requested) return session;
        throw new SessionStateError('Le statut de cette série a changé. Actualisez avant de réessayer.');
      }
      if (skipped === requested) return session;
      await db.runAsync(`INSERT INTO session_set_passages (id, session_id, session_set_id, action, revision, changed_at)
        VALUES (?, ?, ?, ?, ?, ?)`, this.idFactory(), sessionId, setId, action, revision + 1, this.stamp(session));
      // The rest and pending manual advance belong to the previous performance.
      // Neither is closed or edited by this operation.
      if (requested && session.selectedExerciseId === series.sessionExerciseId &&
          !remainingSessionSets(session).some(item => item.id !== setId && item.sessionExerciseId === series.sessionExerciseId)) {
        await db.runAsync('UPDATE workout_sessions SET selected_exercise_id = NULL WHERE id = ?', sessionId);
      }
      return this.requireSession(db, sessionId);
    });
  }

  savePersonalNote(sessionId: string, body: string, exerciseId: string | null = null): Promise<WorkoutSession> {
    return this.write(async db => {
      const session = await this.requireSession(db, sessionId, false);
      if (typeof body !== 'string' || body.length > 4000) throw new SessionStateError('La note doit contenir au maximum 4 000 caractères.');
      if (exerciseId !== null && !session.exercises.some(item => item.id === exerciseId)) throw new SessionStateError('Cet exercice n’appartient pas à cet entraînement.');
      const noteId = exerciseId === null ? `session:${sessionId}` : `exercise:${exerciseId}`;
      await db.runAsync(`INSERT INTO session_personal_notes (id, session_id, session_exercise_id, body, updated_at) VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET body = excluded.body, updated_at = excluded.updated_at`, noteId, sessionId, exerciseId, body.trim(), this.stamp(session));
      return this.requireSession(db, sessionId, false);
    });
  }

  finishSession(sessionId: string): Promise<WorkoutSession> {
    let changed = false;
    return this.write(async db => {
      const session = await this.requireSession(db, sessionId, false);
      if (session.status === 'completed') return session;
      if (selectSessionStep(session).phase !== 'ready_to_finish' || !session.performances.length) {
        throw new SessionStateError('Réalisez ou passez toutes les séries avant de terminer la séance, avec au moins une performance réelle.');
      }
      await db.runAsync("UPDATE workout_sessions SET status = 'completed', finished_at = ? WHERE id = ?", this.stamp(session), sessionId);
      changed = true;
      return this.requireSession(db, sessionId, false);
    }, () => changed);
  }
}
