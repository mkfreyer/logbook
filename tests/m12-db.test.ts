import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { DatabaseSync } from 'node:sqlite';
import { test } from 'node:test';
import { DATABASE_VERSION, initializeDatabase } from '../src/db/migrations';
import { INITIAL_EXERCISES, CATALOG_CREATED_AT } from '../src/db/exerciseCatalog';
import { ProgramRepository } from '../src/db/repository';
import { TrainingRepository } from '../src/db/trainingRepository';
import { SessionRepository, SessionStateError } from '../src/db/sessionRepository';
import type { Database } from '../src/db/types';
import { calculateRestTiming, formatDuration } from '../src/domain/restTimer';
import { selectSessionStep, type WorkoutSession } from '../src/domain/session';

class SQLiteAdapter implements Database {
  readonly connection: DatabaseSync;
  constructor(filename = ':memory:') { this.connection = new DatabaseSync(filename); }
  async execAsync(sql: string) { this.connection.exec(sql); }
  async runAsync(sql: string, ...params: (string | number | null)[]) {
    return { changes: Number(this.connection.prepare(sql).run(...params).changes) };
  }
  async getFirstAsync<T>(sql: string, ...params: (string | number | null)[]): Promise<T | null> {
    const row = this.connection.prepare(sql).get(...params); return row ? { ...row } as T : null;
  }
  async getAllAsync<T>(sql: string, ...params: (string | number | null)[]): Promise<T[]> {
    return this.connection.prepare(sql).all(...params).map(row => ({ ...row }) as T);
  }
  async withTransactionAsync(task: () => Promise<void>) {
    this.connection.exec('BEGIN IMMEDIATE');
    try { await task(); this.connection.exec('COMMIT'); }
    catch (error) { this.connection.exec('ROLLBACK'); throw error; }
  }
  close() { this.connection.close(); }
}

/** Frozen schema of the released M1.1, independent of the new initializer. */
const releasedV2Schema = `
  CREATE TABLE programs (
    id TEXT PRIMARY KEY NOT NULL,
    name TEXT NOT NULL CHECK(length(trim(name)) BETWEEN 1 AND 80),
    description TEXT NOT NULL DEFAULT '' CHECK(length(description) <= 1000),
    sport_type TEXT NOT NULL DEFAULT 'musculation' CHECK(sport_type = 'musculation'),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
  );

  CREATE TABLE workout_templates (
    id TEXT PRIMARY KEY NOT NULL,
    program_id TEXT NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
    name TEXT NOT NULL CHECK(length(trim(name)) BETWEEN 1 AND 80),
    notes TEXT NOT NULL DEFAULT '' CHECK(length(notes) <= 1000),
    sort_order INTEGER NOT NULL CHECK(sort_order >= 0),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(program_id, sort_order)
  );

  CREATE INDEX programs_updated_at ON programs(updated_at DESC, created_at DESC, id);
  CREATE INDEX workouts_program_order ON workout_templates(program_id, sort_order, id);

  CREATE TABLE exercise_catalog (
    id TEXT PRIMARY KEY NOT NULL,
    name TEXT NOT NULL CHECK(length(trim(name)) BETWEEN 1 AND 80),
    muscle_group TEXT NOT NULL CHECK(length(trim(muscle_group)) BETWEEN 1 AND 80),
    equipment TEXT NOT NULL CHECK(length(trim(equipment)) BETWEEN 1 AND 80),
    instructions TEXT NOT NULL DEFAULT '' CHECK(length(instructions) <= 1000),
    weight_mode TEXT NOT NULL CHECK(weight_mode IN ('total', 'per_hand', 'additional')),
    is_custom INTEGER NOT NULL CHECK(is_custom IN (0, 1)),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
  );

  CREATE TABLE workout_exercises (
    id TEXT PRIMARY KEY NOT NULL,
    workout_template_id TEXT NOT NULL REFERENCES workout_templates(id) ON DELETE CASCADE,
    exercise_id TEXT NOT NULL REFERENCES exercise_catalog(id) ON DELETE RESTRICT,
    sort_order INTEGER NOT NULL CHECK(typeof(sort_order) = 'integer' AND sort_order >= 0),
    notes TEXT NOT NULL DEFAULT '' CHECK(length(notes) <= 1000),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(workout_template_id, sort_order)
  );

  CREATE TABLE set_templates (
    id TEXT PRIMARY KEY NOT NULL,
    workout_exercise_id TEXT NOT NULL REFERENCES workout_exercises(id) ON DELETE CASCADE,
    sort_order INTEGER NOT NULL CHECK(typeof(sort_order) = 'integer' AND sort_order >= 0),
    label TEXT NOT NULL DEFAULT '' CHECK(length(label) <= 80),
    kind TEXT NOT NULL CHECK(kind IN ('work', 'warmup', 'top_set', 'back_off', 'custom')),
    reps_min INTEGER NOT NULL CHECK(typeof(reps_min) = 'integer' AND reps_min >= 0),
    reps_max INTEGER NOT NULL CHECK(typeof(reps_max) = 'integer' AND reps_max >= reps_min),
    target_weight_kg REAL CHECK(target_weight_kg IS NULL OR (typeof(target_weight_kg) IN ('real', 'integer') AND target_weight_kg >= 0 AND target_weight_kg <= 1.7976931348623157e308)),
    target_rir INTEGER CHECK(target_rir IS NULL OR (typeof(target_rir) = 'integer' AND target_rir BETWEEN 0 AND 10)),
    rest_after_sec INTEGER NOT NULL CHECK(typeof(rest_after_sec) = 'integer' AND rest_after_sec BETWEEN 0 AND 86400),
    notes TEXT NOT NULL DEFAULT '' CHECK(length(notes) <= 1000),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(workout_exercise_id, sort_order)
  );

  CREATE INDEX exercises_workout_order ON workout_exercises(workout_template_id, sort_order, id);
  CREATE INDEX sets_exercise_order ON set_templates(workout_exercise_id, sort_order, id);

PRAGMA user_version = 2;`;

async function createV2(db: Database) {
  await db.execAsync('PRAGMA foreign_keys = ON;');
  await db.execAsync(releasedV2Schema);
  for (const exercise of INITIAL_EXERCISES) await db.runAsync(
    `INSERT INTO exercise_catalog (id,name,muscle_group,equipment,instructions,weight_mode,is_custom,created_at,updated_at)
     VALUES (?,?,?,?,?,?,0,?,?)`, exercise.id, exercise.name, exercise.muscleGroup, exercise.equipment,
    exercise.instructions ?? '', exercise.weightMode, CATALOG_CREATED_AT, CATALOG_CREATED_AT);
}

function repos(db: Database, prefix = 'm12') {
  let id = 0, nowMs = Date.UTC(2026, 9, 14, 12);
  const uuid = () => `${prefix}-${++id}`, now = () => new Date(nowMs).toISOString();
  return { programs: new ProgramRepository(db, uuid, now), training: new TrainingRepository(db, uuid, now),
    sessions: new SessionRepository(db, uuid, now), advance: (ms: number) => { nowMs += ms; },
    nowMs: () => nowMs, now };
}
async function fixture(rests = [60, 120, 180, 240], filename = ':memory:', v2 = false) {
  const db = new SQLiteAdapter(filename);
  if (v2) await createV2(db); else await initializeDatabase(db);
  const repositories = repos(db);
  const program = await repositories.programs.createProgram({ name: 'Programme conservé', description: 'Mes données M0' });
  const workout = await repositories.programs.createWorkout(program.id, { name: 'Ma séance', notes: 'Mes notes M0' });
  const custom = await repositories.training.createCustomExercise({ name: 'Mon exercice', muscleGroup: 'Dos', equipment: 'Poids du corps', weightMode: 'additional' });
  const exercise = await repositories.training.addWorkoutExercise(workout.id, { exerciseId: custom.id, notes: 'Ma consigne' });
  for (const [index, restAfterSec] of rests.entries()) await repositories.training.createSet(exercise.id,
    { kind: index === 0 ? 'warmup' : 'work', label: index === 0 ? 'Mise en route' : '', repsMin: 8, repsMax: 12,
      targetWeightKg: 42.5, targetRir: 2, restAfterSec });
  return { db, ...repositories, program, workout, exercise, custom };
}
const performed = { weightKg: 35, reps: 9, rir: 1 };
function active(session: WorkoutSession) {
  const step = selectSessionStep(session); assert.equal(step.phase, 'set');
  if (step.phase !== 'set') throw new Error('Expected active series');
  return step.set;
}
function resting(session: WorkoutSession) {
  const step = selectSessionStep(session); assert.equal(step.phase, 'rest');
  if (step.phase !== 'rest') throw new Error('Expected active rest');
  return step.rest;
}
async function preparation(db: Database) {
  const snapshot: Record<string, unknown[]> = {};
  for (const table of ['programs', 'workout_templates', 'exercise_catalog', 'workout_exercises', 'set_templates']) {
    snapshot[table] = await db.getAllAsync(`SELECT * FROM ${table} ORDER BY id`);
  }
  return snapshot;
}

test('V3 migrates populated released M1.1 without touching any preparation record or its schema', async t => {
  const f = await fixture([60, 120, 180], ':memory:', true); t.after(() => f.db.close());
  const before = await preparation(f.db);
  const schema = await f.db.getAllAsync("SELECT name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY name");
  await initializeDatabase(f.db); await initializeDatabase(f.db);
  assert.deepEqual(await preparation(f.db), before);
  for (const row of schema as { name: string; sql: string }[]) {
    assert.deepEqual(await f.db.getFirstAsync('SELECT name,sql FROM sqlite_master WHERE name = ?', row.name), row);
  }
  assert.equal((await f.db.getFirstAsync<{ user_version: number }>('PRAGMA user_version'))!.user_version, DATABASE_VERSION);
  for (const table of ['workout_sessions', 'session_exercises', 'session_sets', 'performed_sets', 'rest_intervals', 'rest_pauses']) {
    assert.deepEqual(await f.db.getAllAsync(`SELECT * FROM ${table}`), []);
  }
  assert.equal(await f.sessions.getActiveSession(), null);
  assert.deepEqual(await f.db.getAllAsync('PRAGMA foreign_key_check'), []);
});

test('migration storage failure rolls back all new execution tables and keeps the populated V2 usable', async t => {
  const f = await fixture([60], ':memory:', true); t.after(() => f.db.close());
  const before = await preparation(f.db);
  const failing: Database = {
    execAsync: async sql => {
      if (sql.includes('CREATE TABLE workout_sessions')) { await f.db.execAsync(sql); throw new Error('migration storage failure'); }
      await f.db.execAsync(sql);
    },
    runAsync: (sql, ...params) => f.db.runAsync(sql, ...params),
    getFirstAsync: (sql, ...params) => f.db.getFirstAsync(sql, ...params),
    getAllAsync: (sql, ...params) => f.db.getAllAsync(sql, ...params),
    withTransactionAsync: task => f.db.withTransactionAsync(task),
  };
  await assert.rejects(initializeDatabase(failing), /migration storage failure/);
  assert.equal((await f.db.getFirstAsync<{ user_version: number }>('PRAGMA user_version'))!.user_version, 2);
  assert.deepEqual(await preparation(f.db), before);
  assert.equal(await f.db.getFirstAsync("SELECT name FROM sqlite_master WHERE name = 'workout_sessions'"), null);
  await initializeDatabase(f.db);
  assert.equal((await f.sessions.startOrResume(f.workout.id)).sets.length, 1);
});

test('start atomically snapshots names, exercise order and individual targets without recording performances', async t => {
  const f = await fixture(); t.after(() => f.db.close());
  const last = await f.training.addWorkoutExercise(f.workout.id, { exerciseId: INITIAL_EXERCISES[0]!.id });
  await f.training.createSet(last.id, { kind: 'custom', label: 'Fin', repsMin: 3, repsMax: 3, restAfterSec: 0 });
  await f.training.reorderWorkoutExercises(f.workout.id, [last.id, f.exercise.id]);
  const before = await preparation(f.db), session = await f.sessions.startOrResume(f.workout.id);
  assert.equal(session.status, 'active'); assert.equal(session.startedAt, f.now());
  assert.equal(session.workoutName, f.workout.name); assert.equal(session.programName, f.program.name);
  assert.deepEqual(session.exercises.map(item => item.sourceWorkoutExerciseId), [last.id, f.exercise.id]);
  assert.deepEqual(session.sets.map(item => item.targets.restAfterSec), [0, 60, 120, 180, 240]);
  assert.ok(session.sets.every(item => item.id !== item.sourceSetTemplateId));
  assert.deepEqual(session.performances, []); assert.deepEqual(session.rests, []);
  assert.deepEqual(await preparation(f.db), before);
  assert.equal(active(session).label, 'Fin');
  await f.training.updateCustomExercise(f.custom.id, { name: 'Nouveau nom', muscleGroup: 'Bras', equipment: 'Haltère', weightMode: 'total' });
  await f.training.updateSet(session.sets[0]!.sourceSetTemplateId, { kind: 'work', repsMin: 20, repsMax: 20, targetWeightKg: 50, restAfterSec: 25 });
  assert.deepEqual(await f.sessions.getSession(session.id), session);
});

test('incomplete preparations roll back their entire snapshot and starting twice resumes one active session', async t => {
  const f = await fixture([]); t.after(() => f.db.close());
  await assert.rejects(f.sessions.startOrResume(f.workout.id), /au moins une série/);
  assert.equal(await f.sessions.getActiveSession(), null);
  assert.deepEqual(await f.db.getAllAsync('SELECT * FROM session_exercises'), []);
  await f.training.createSet(f.exercise.id, { kind: 'work', repsMin: 8, repsMax: 8, restAfterSec: 30 });
  const [one, two] = await Promise.all([f.sessions.startOrResume(f.workout.id), f.sessions.startOrResume(f.workout.id)]);
  assert.deepEqual(one, two);
  assert.deepEqual(await f.sessions.startOrResume('another-or-deleted-workout'), one);
  assert.equal((await f.db.getAllAsync('SELECT * FROM workout_sessions')).length, 1);
  await assert.rejects(f.db.runAsync(`INSERT INTO workout_sessions
    (id,source_workout_template_id,source_program_id,workout_name,program_name,status,started_at)
    VALUES ('duplicate','w','p','W','P','active',?)`, f.now()), /UNIQUE/);
});

test('actual values require explicit input and duplicate validation cannot replace a performance or create another rest', async t => {
  const f = await fixture(); t.after(() => f.db.close());
  const session = await f.sessions.startOrResume(f.workout.id), set = active(session);
  await assert.rejects(f.sessions.validateSet(session.id, set.id, { ...performed, reps: Number.NaN }), SessionStateError);
  for (const invalid of [{ reps: -1 }, { reps: 2.5 }, { weightKg: -1 }, { weightKg: Infinity }, { rir: 11 }, { rir: 1.5 }]) {
    await assert.rejects(f.sessions.validateSet(session.id, set.id, { ...performed, ...invalid }), SessionStateError);
  }
  f.advance(4000);
  const [first, duplicate] = await Promise.all([
    f.sessions.validateSet(session.id, set.id, { weightKg: null, reps: 0, rir: null }),
    f.sessions.validateSet(session.id, set.id, performed),
  ]);
  assert.deepEqual(first, duplicate);
  assert.equal(first.performances.length, 1); assert.equal(first.rests.length, 1);
  assert.deepEqual({ weightKg: first.performances[0]!.weightKg, reps: first.performances[0]!.reps, rir: first.performances[0]!.rir },
    { weightKg: null, reps: 0, rir: null });
  assert.equal(first.performances[0]!.performedAt, f.now());
  assert.equal(first.sets[0]!.targets.targetWeightKg, 42.5);
  await assert.rejects(f.sessions.validateSet(session.id, session.sets[1]!.id, performed), /pas la série active/);
});

test('three different individual rests are retained, early exit works, overtime never advances, and final series has no rest', async t => {
  const f = await fixture(); t.after(() => f.db.close());
  let session = await f.sessions.startOrResume(f.workout.id);
  const chronological = [10000, 125000, 181000];
  for (let index = 0; index < 3; index++) {
    session = await f.sessions.validateSet(session.id, active(session).id, performed);
    const rest = resting(session); assert.equal(rest.plannedSeconds, [60, 120, 180][index]);
    f.advance(chronological[index]!);
    const timing = calculateRestTiming(rest, f.nowMs());
    assert.equal(timing.expired, index > 0);
    assert.equal(timing.overtimeMs, index === 0 ? 0 : index === 1 ? 5000 : 1000);
    assert.equal(selectSessionStep((await f.sessions.getSession(session.id))!).phase, 'rest');
    session = await f.sessions.completeRest(session.id, rest.id);
    assert.equal(session.rests[index]!.chronologicalMs, chronological[index]);
    assert.equal(session.rests[index]!.activeMs, chronological[index]);
    assert.equal(selectSessionStep(session).phase, 'set');
    assert.deepEqual(await f.sessions.completeRest(session.id, rest.id), session);
  }
  session = await f.sessions.validateSet(session.id, active(session).id, performed);
  assert.equal(session.rests.length, 3); assert.equal(selectSessionStep(session).phase, 'ready_to_finish');
  assert.equal(session.status, 'active'); assert.equal(session.finishedAt, null);
});

test('zero rest leaves a manual next action and explicitly configured rest applies at exercise boundaries without a default', async t => {
  const f = await fixture([0, 73]); t.after(() => f.db.close());
  const other = await f.training.addWorkoutExercise(f.workout.id, { exerciseId: INITIAL_EXERCISES[0]!.id });
  await f.training.createSet(other.id, { kind: 'work', repsMin: 8, repsMax: 8, restAfterSec: 300 });
  let session = await f.sessions.startOrResume(f.workout.id);
  session = await f.sessions.validateSet(session.id, active(session).id, performed);
  const between = selectSessionStep(session); assert.equal(between.phase, 'between_sets');
  assert.equal(session.rests.length, 0);
  if (between.phase !== 'between_sets') throw new Error();
  session = await f.sessions.advanceAfterSet(session.id, between.performed.id);
  assert.deepEqual(await f.sessions.advanceAfterSet(session.id, between.performed.id), session);
  session = await f.sessions.validateSet(session.id, active(session).id, performed);
  const rest = resting(session); assert.equal(rest.plannedSeconds, 73);
  const step = selectSessionStep(session);
  if (step.phase !== 'rest') throw new Error();
  assert.equal(step.exercise.sourceWorkoutExerciseId, other.id);
  session = await f.sessions.completeRest(session.id, rest.id);
  session = await f.sessions.validateSet(session.id, active(session).id, performed);
  assert.equal(session.rests.length, 1); assert.equal(selectSessionStep(session).phase, 'ready_to_finish');
});

test('pauses persist each interval; chronological rest includes pauses while active countdown excludes them', async t => {
  const f = await fixture(); t.after(() => f.db.close());
  let session = await f.sessions.startOrResume(f.workout.id);
  session = await f.sessions.validateSet(session.id, active(session).id, performed);
  const restId = resting(session).id;
  f.advance(10000); session = await f.sessions.pauseRest(session.id, restId);
  assert.deepEqual(await f.sessions.pauseRest(session.id, restId), session);
  f.advance(30000);
  let timing = calculateRestTiming(resting(session), f.nowMs());
  assert.equal(timing.chronologicalMs, 40000); assert.equal(timing.activeMs, 10000);
  assert.equal(timing.remainingMs, 50000); assert.equal(timing.isPaused, true);
  session = await f.sessions.resumeRest(session.id, restId);
  assert.deepEqual(await f.sessions.resumeRest(session.id, restId), session);
  f.advance(20000); session = await f.sessions.pauseRest(session.id, restId);
  f.advance(5000); session = await f.sessions.completeRest(session.id, restId);
  const rest = session.rests[0]!; timing = calculateRestTiming(rest, f.nowMs() + 900000);
  assert.equal(rest.pauses.length, 2); assert.ok(rest.pauses.every(item => item.endedAt !== null));
  assert.equal(rest.chronologicalMs, 65000); assert.equal(rest.activeMs, 30000);
  assert.equal(timing.chronologicalMs, 65000); assert.equal(timing.activeMs, 30000); assert.equal(timing.isPaused, false);
  assert.equal(formatDuration(timing.activeMs), '00:30');
});

test('closing SQLite during a running or paused rest reconstructs elapsed time and the active series without duplicates', async t => {
  const directory = mkdtempSync(join(tmpdir(), 'logbook-m12-')); t.after(() => rmSync(directory, { recursive: true, force: true }));
  const path = join(directory, 'logbook.db'), f = await fixture([60, 120], path);
  let session = await f.sessions.startOrResume(f.workout.id);
  session = await f.sessions.validateSet(session.id, active(session).id, performed);
  const rest = resting(session), startMs = Date.parse(rest.startedAt); f.db.close();
  const again = new SQLiteAdapter(path); await initializeDatabase(again);
  const laterRepo = new SessionRepository(again, () => 'pause-after-reopen', () => new Date(startMs + 90000).toISOString());
  session = (await laterRepo.getActiveSession())!;
  assert.deepEqual(resting(session), rest);
  assert.equal(calculateRestTiming(resting(session), startMs + 90000).overtimeMs, 30000);
  session = await laterRepo.pauseRest(session.id, rest.id); again.close();
  const finalDb = new SQLiteAdapter(path); t.after(() => finalDb.close()); await initializeDatabase(finalDb);
  const finalRepo = new SessionRepository(finalDb, () => 'later-id', () => new Date(startMs + 240000).toISOString());
  session = (await finalRepo.getActiveSession())!;
  const timing = calculateRestTiming(resting(session), startMs + 240000);
  assert.equal(timing.isPaused, true); assert.equal(timing.activeMs, 90000); assert.equal(timing.chronologicalMs, 240000);
  session = await finalRepo.completeRest(session.id, rest.id);
  assert.equal(session.performances.length, 1); assert.equal(active(session).seriesIndex, 1);
  assert.deepEqual(await finalRepo.startOrResume(f.workout.id), session);
  assert.equal(session.rests[0]!.activeMs, 90000); assert.equal(session.rests[0]!.chronologicalMs, 240000);
});

test('Cette séance modifies only unperformed execution targets and keeps the original snapshot and every preparation', async t => {
  const f = await fixture(); t.after(() => f.db.close());
  const before = await preparation(f.db);
  let session = await f.sessions.startOrResume(f.workout.id);
  const set = active(session), original = set.originalTargets;
  session = await f.sessions.updateSetTargets(session.id, set.id, { ...set.targets, targetWeightKg: null, targetRir: 0, repsMin: 5, repsMax: 7, restAfterSec: 33 }, 'session');
  assert.equal(active(session).targets.restAfterSec, 33); assert.equal(active(session).targets.targetRir, 0);
  assert.deepEqual(active(session).originalTargets, original);
  assert.deepEqual(await preparation(f.db), before);
  session = await f.sessions.validateSet(session.id, set.id, performed);
  assert.equal(resting(session).plannedSeconds, 33);
  const immutable = structuredClone(session);
  await assert.rejects(f.sessions.updateSetTargets(session.id, set.id, original, 'program'), SessionStateError);
  assert.deepEqual(await f.sessions.getSession(session.id), immutable);
});

test('Programme updates the active objective and the future template, without rewriting original targets or past performance', async t => {
  const f = await fixture([0, 0]); t.after(() => f.db.close());
  let session = await f.sessions.startOrResume(f.workout.id);
  session = await f.sessions.validateSet(session.id, active(session).id, performed);
  const first = structuredClone(session.performances[0]!);
  const step = selectSessionStep(session); assert.equal(step.phase, 'between_sets');
  if (step.phase !== 'between_sets') throw new Error('Expected next');
  session = await f.sessions.advanceAfterSet(session.id, step.performed.id);
  const set = active(session), original = set.originalTargets;
  const changed = { ...set.targets, repsMin: 6, repsMax: 6, targetWeightKg: 22.5, restAfterSec: 18 };
  session = await f.sessions.updateSetTargets(session.id, set.id, changed, 'program');
  assert.deepEqual(active(session).targets, changed); assert.deepEqual(active(session).originalTargets, original);
  assert.deepEqual(session.performances[0], { ...first, advancedAt: f.now() });
  const template = await f.training.getSet(set.sourceSetTemplateId);
  assert.equal(template.repsMin, 6); assert.equal(template.targetWeightKg, 22.5);
  session = await f.sessions.validateSet(session.id, set.id, { weightKg: 20, reps: 5, rir: null });
  session = await f.sessions.finishSession(session.id);
  const finished = structuredClone(session);
  const next = await f.sessions.startOrResume(f.workout.id);
  assert.notEqual(next.id, session.id); assert.equal(next.performances.length, 0);
  assert.deepEqual(next.sets[1]!.originalTargets, changed);
  await f.training.updateSet(template.id, { ...template, targetWeightKg: 99 });
  assert.deepEqual(await f.sessions.getSession(session.id), finished);
});

test('deleting a program preserves active and completed execution data, and the active snapshot can still finish', async t => {
  const f = await fixture([20, 0]); t.after(() => f.db.close());
  let session = await f.sessions.startOrResume(f.workout.id);
  session = await f.sessions.validateSet(session.id, active(session).id, performed);
  const snapshot = structuredClone(session);
  await f.programs.deleteProgram(f.program.id);
  assert.deepEqual(await f.sessions.getActiveSession(), snapshot);
  assert.equal((await f.db.getFirstAsync<{ count: number }>('SELECT COUNT(*) AS count FROM set_templates'))!.count, 0);
  session = await f.sessions.completeRest(session.id, resting(session).id);
  session = await f.sessions.validateSet(session.id, active(session).id, performed);
  f.advance(25000); session = await f.sessions.finishSession(session.id);
  assert.equal(session.status, 'completed'); assert.equal(session.finishedAt, f.now());
  assert.equal(session.performances.length, 2); assert.equal(session.rests.length, 1);
  assert.equal(await f.sessions.getActiveSession(), null);
  assert.deepEqual(await f.sessions.finishSession(session.id), session);
  assert.deepEqual(await f.db.getAllAsync('PRAGMA foreign_key_check'), []);
});

test('a deleted or replaced template cannot receive Programme edits but This session remains usable', async t => {
  const f = await fixture(); t.after(() => f.db.close());
  let session = await f.sessions.startOrResume(f.workout.id);
  const set = active(session), changed = { ...set.targets, restAfterSec: 8 };
  const alternative = INITIAL_EXERCISES[0]!;
  await f.training.updateWorkoutExercise(f.exercise.id, { exerciseId: alternative.id });
  await assert.rejects(f.sessions.updateSetTargets(session.id, set.id, changed, 'program'), /remplacé/);
  assert.deepEqual(await f.sessions.getSession(session.id), session);
  session = await f.sessions.updateSetTargets(session.id, set.id, changed, 'session');
  await f.training.deleteSet(set.sourceSetTemplateId);
  await assert.rejects(f.sessions.updateSetTargets(session.id, set.id, { ...changed, restAfterSec: 10 }, 'program'), /supprimée/);
  assert.deepEqual(await f.sessions.getSession(session.id), session);
});

test('SQLite independently protects original targets, validated objectives, actual performances and the single active session', async t => {
  const f = await fixture(); t.after(() => f.db.close());
  let session = await f.sessions.startOrResume(f.workout.id);
  const set = active(session);
  await assert.rejects(f.db.runAsync("UPDATE workout_sessions SET status = 'completed', finished_at = NULL WHERE id = ?", session.id), /CHECK/);
  await assert.rejects(f.db.runAsync('UPDATE session_sets SET original_targets = ? WHERE id = ?', '{}', set.id), /immutable/);
  await assert.rejects(f.db.runAsync(`INSERT INTO workout_sessions (id,source_workout_template_id,source_program_id,workout_name,program_name,status,started_at)
    VALUES ('other',?,?,?,?, 'active',?)`, f.workout.id, f.program.id, 'other', 'other', f.now()), /UNIQUE/);
  session = await f.sessions.validateSet(session.id, set.id, performed);
  await assert.rejects(f.db.runAsync('UPDATE performed_sets SET reps = 15 WHERE id = ?', session.performances[0]!.id), /immutable/);
  await assert.rejects(f.db.runAsync('UPDATE session_sets SET reps_min = 1 WHERE id = ?', set.id), /immutable/);
  await assert.rejects(f.db.runAsync(`INSERT INTO session_sets (id,session_id,session_exercise_id,source_set_template_id,sort_order,series_index,label,kind,notes,original_targets,reps_min,reps_max,rest_after_sec)
    VALUES ('orphan',?,'missing','source',500,0,'','work','','{}',1,1,0)`, session.id), /FOREIGN KEY/);
  assert.deepEqual(await f.db.getAllAsync('PRAGMA foreign_key_check'), []);
});

test('failure starting a rest rolls back its performance and allows retry without duplicates', async t => {
  const f = await fixture(); t.after(() => f.db.close());
  const session = await f.sessions.startOrResume(f.workout.id), set = active(session);
  await f.db.execAsync(`CREATE TRIGGER fail_rest BEFORE INSERT ON rest_intervals BEGIN SELECT RAISE(ABORT,'rest failure'); END;`);
  await assert.rejects(f.sessions.validateSet(session.id, set.id, performed), /rest failure/);
  assert.deepEqual(await f.sessions.getSession(session.id), session);
  await f.db.execAsync('DROP TRIGGER fail_rest');
  const saved = await f.sessions.validateSet(session.id, set.id, performed);
  assert.equal(saved.performances.length, 1); assert.equal(saved.rests.length, 1);
});

test('failure closing a paused rest rolls back pause end and advancement, and preserves retry', async t => {
  const f = await fixture(); t.after(() => f.db.close());
  let session = await f.sessions.startOrResume(f.workout.id);
  session = await f.sessions.validateSet(session.id, active(session).id, performed);
  const restId = resting(session).id;
  f.advance(1000); session = await f.sessions.pauseRest(session.id, restId); f.advance(5000);
  await f.db.execAsync(`CREATE TRIGGER fail_end BEFORE UPDATE OF ended_at ON rest_intervals BEGIN SELECT RAISE(ABORT,'end failure'); END;`);
  await assert.rejects(f.sessions.completeRest(session.id, restId), /end failure/);
  assert.deepEqual(await f.sessions.getSession(session.id), session);
  await f.db.execAsync('DROP TRIGGER fail_end');
  session = await f.sessions.completeRest(session.id, restId);
  assert.equal(session.rests[0]!.chronologicalMs, 6000); assert.equal(session.rests[0]!.activeMs, 1000);
});

test('Programme and execution objective updates commit together or both roll back', async t => {
  const f = await fixture(); t.after(() => f.db.close());
  const session = await f.sessions.startOrResume(f.workout.id), set = active(session);
  const template = await f.training.getSet(set.sourceSetTemplateId);
  await f.db.execAsync(`CREATE TRIGGER fail_targets BEFORE UPDATE OF reps_min ON session_sets BEGIN SELECT RAISE(ABORT,'targets failure'); END;`);
  await assert.rejects(f.sessions.updateSetTargets(session.id, set.id, { ...set.targets, repsMin: 3 }, 'program'), /targets failure/);
  assert.deepEqual(await f.training.getSet(set.sourceSetTemplateId), template);
  assert.deepEqual(await f.sessions.getSession(session.id), session);
});

test('invalid targets, premature completion and out-of-order validation never alter execution or preparation', async t => {
  const f = await fixture(); t.after(() => f.db.close());
  const session = await f.sessions.startOrResume(f.workout.id), set = active(session), before = await preparation(f.db);
  await assert.rejects(f.sessions.finishSession(session.id), SessionStateError);
  await assert.rejects(f.sessions.validateSet(session.id, session.sets[1]!.id, performed), SessionStateError);
  for (const change of [{ repsMax: 1 }, { targetWeightKg: -1 }, { targetRir: 11 }, { restAfterSec: 1.5 }]) {
    await assert.rejects(f.sessions.updateSetTargets(session.id, set.id, { ...set.targets, ...change }, 'program'), SessionStateError);
  }
  assert.deepEqual(await f.sessions.getSession(session.id), session); assert.deepEqual(await preparation(f.db), before);
});

test('exclusive Expo path uses only the transaction connection, with no ambient writes or assumed foreign keys', async t => {
  const f = await fixture(); t.after(() => f.db.close());
  let transactions = 0;
  const unsupported = async () => { throw new Error('outer query inside transaction'); };
  const facade: Database = {
    execAsync: unsupported, runAsync: unsupported, getFirstAsync: unsupported, getAllAsync: unsupported, withTransactionAsync: unsupported,
    withExclusiveTransactionAsync: async task => {
      transactions++; await f.db.execAsync('PRAGMA foreign_keys = OFF');
      await f.db.withTransactionAsync(() => task(f.db));
      await f.db.execAsync('PRAGMA foreign_keys = ON');
    },
  };
  let serial = 0;
  const repository = new SessionRepository(facade, () => `exclusive-${++serial}`, f.now);
  let session = await repository.startOrResume(f.workout.id);
  session = await repository.validateSet(session.id, active(session).id, performed);
  session = await repository.pauseRest(session.id, resting(session).id);
  session = await repository.completeRest(session.id, resting(session).id);
  assert.equal(transactions, 4); assert.equal(active(session).seriesIndex, 1);
  assert.deepEqual(await f.db.getAllAsync('PRAGMA foreign_key_check'), []);
});

test('committed change observers can refresh a foreground alarm and cannot turn a saved write into a failure', async t => {
  const f = await fixture([0]); t.after(() => f.db.close());
  let observed = 0;
  const stop = f.sessions.subscribe(() => { observed++; });
  f.sessions.subscribe(() => { throw new Error('observer failure'); });
  const session = await f.sessions.startOrResume(f.workout.id);
  assert.equal(observed, 1); stop();
  const saved = await f.sessions.validateSet(session.id, active(session).id, performed);
  assert.equal(saved.performances.length, 1); assert.equal(observed, 1);
});
