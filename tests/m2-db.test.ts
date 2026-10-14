import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { test } from 'node:test';
import { initializeDatabase, DATABASE_VERSION } from '../src/db/migrations';
import { ProgramRepository } from '../src/db/repository';
import { TrainingRepository } from '../src/db/trainingRepository';
import { SessionRepository } from '../src/db/sessionRepository';
import { remainingSessionExercises, selectSessionStep, type WorkoutSession } from '../src/domain/session';
import { summarizeSession } from '../src/domain/sessionSummary';
import { calculateRestTiming } from '../src/domain/restTimer';
import { SqliteDatabase } from './helpers/SqliteDatabase';

async function fixture(path = ':memory:', rest = 0) {
  const db = new SqliteDatabase(path); await initializeDatabase(db);
  let serial = 0, clock = Date.UTC(2026, 9, 14, 12);
  const id = () => `m2-${++serial}`, now = () => new Date(clock).toISOString();
  const programs = new ProgramRepository(db, id, now), training = new TrainingRepository(db, id, now), repository = new SessionRepository(db, id, now);
  const program = await programs.createProgram({ name: 'Mon programme' });
  const workout = await programs.createWorkout(program.id, { name: 'Ma séance' });
  const catalog = [], exercises = [];
  for (const [i, name] of ['Barre', 'Tractions', 'Élévations', 'Curl'].entries()) {
    const item = await training.createCustomExercise({ name, muscleGroup: 'Dos', equipment: 'Salle', weightMode: i === 2 ? 'per_hand' : i === 1 ? 'additional' : 'total' });
    catalog.push(item);
    const exercise = await training.addWorkoutExercise(workout.id, { exerciseId: item.id }); exercises.push(exercise);
    for (let j = 0; j < 2; j++) await training.createSet(exercise.id, { kind: 'work', repsMin: 8, repsMax: 10, targetWeightKg: 40, targetRir: 2, restAfterSec: rest });
  }
  const alternative = await training.createCustomExercise({ name: 'Haltères', muscleGroup: 'Pectoraux', equipment: 'Haltères', weightMode: 'per_hand' });
  return { db, programs, training, repository, program, workout, catalog, exercises, alternative, now, advance: (ms: number) => { clock += ms; } };
}
function active(session: WorkoutSession) {
  const step = selectSessionStep(session); assert.equal(step.phase, 'set');
  if (step.phase !== 'set') throw new Error('Expected active series'); return step;
}
async function advance(repository: SessionRepository, session: WorkoutSession): Promise<WorkoutSession> {
  const step = selectSessionStep(session);
  if (step.phase === 'rest') return repository.completeRest(session.id, step.rest.id);
  if (step.phase === 'between_sets') return repository.advanceAfterSet(session.id, step.performed.id);
  return session;
}
async function plans(db: SqliteDatabase) {
  const result: Record<string, unknown> = {};
  for (const table of ['programs', 'workout_templates', 'workout_exercises', 'set_templates']) result[table] = await db.getAllAsync(`SELECT * FROM ${table} ORDER BY id`);
  return result;
}

test('temporary replacement creates exact exercise identity, clears incompatible targets and leaves the program unchanged', async t => {
  const f = await fixture(); t.after(() => f.db.close()); const before = await plans(f.db);
  const initial = await f.repository.startOrResume(f.workout.id), step = active(initial);
  const changed = await f.repository.replaceExercise(initial.id, step.exercise.id, f.alternative.id, step.set.id);
  const next = active(changed);
  assert.notEqual(next.exercise.id, step.exercise.id); assert.equal(next.exercise.name, 'Haltères');
  assert.equal(next.exercise.sourceCatalogExerciseId, f.alternative.id); assert.equal(next.exercise.weightMode, 'per_hand');
  assert.equal(next.exercise.plannedOrder, 0); assert.equal(next.set.id, step.set.id);
  assert.equal(next.set.targets.targetWeightKg, null); assert.deepEqual(next.set.originalTargets, step.set.originalTargets);
  assert.equal(next.set.targets.restAfterSec, step.set.targets.restAfterSec); assert.equal(changed.performances.length, 0);
  assert.deepEqual(await plans(f.db), before); assert.equal(changed.replacements!.length, 1);
  assert.deepEqual(await f.repository.replaceExercise(initial.id, step.exercise.id, f.alternative.id, step.set.id), changed);
  assert.equal((await f.repository.getSession(initial.id))!.exercises.length, 5);
});

test('partial replacement never reassigns validated series; remaining results refer to the actual replacement', async t => {
  const f = await fixture(); t.after(() => f.db.close());
  let session = await f.repository.startOrResume(f.workout.id); const first = active(session);
  session = await f.repository.validateSet(session.id, first.set.id, { weightKg: 50, reps: 8, rir: 2 });
  session = await advance(f.repository, session); const second = active(session), performance = structuredClone(session.performances[0]);
  session = await f.repository.replaceExercise(session.id, second.exercise.id, f.alternative.id, second.set.id);
  assert.deepEqual(session.performances[0], performance);
  assert.equal(session.sets.find(item => item.id === first.set.id)!.sessionExerciseId, first.exercise.id);
  assert.notEqual(active(session).exercise.id, first.exercise.id);
  session = await f.repository.validateSet(session.id, second.set.id, { weightKg: 20, reps: 9, rir: 1 });
  const actual = session.sets.find(item => item.id === session.performances[1]!.sessionSetId)!;
  assert.equal(session.exercises.find(item => item.id === actual.sessionExerciseId)!.name, 'Haltères');
  assert.deepEqual(await f.db.getAllAsync('PRAGMA foreign_key_check'), []);
});

test('choosing a later exercise persists, finishes its remaining series then returns to the earliest unfinished program exercise', async t => {
  const f = await fixture(); t.after(() => f.db.close()); const before = await plans(f.db);
  let session = await f.repository.startOrResume(f.workout.id);
  const chosen = session.exercises[2]!, original = active(session);
  session = await f.repository.chooseNextExercise(session.id, chosen.id, original.set.id);
  assert.equal(active(session).exercise.id, chosen.id); assert.equal(session.exerciseChoices!.length, 1);
  assert.equal(session.performances.length, 0); assert.equal(remainingSessionExercises(session).length, 4);
  assert.deepEqual(await f.repository.chooseNextExercise(session.id, chosen.id, original.set.id), session);
  session = await f.repository.validateSet(session.id, active(session).set.id, { weightKg: 5, reps: 12, rir: 0 });
  session = await advance(f.repository, session); assert.equal(active(session).exercise.id, chosen.id);
  session = await f.repository.validateSet(session.id, active(session).set.id, { weightKg: 5, reps: 10, rir: null });
  session = await advance(f.repository, session); assert.equal(active(session).exercise.id, original.exercise.id);
  assert.equal(session.selectedExerciseId, null); assert.deepEqual(await plans(f.db), before);
  while (selectSessionStep(session).phase !== 'ready_to_finish') {
    const step = active(session); session = await f.repository.validateSet(session.id, step.set.id, { weightKg: null, reps: 8, rir: null });
    session = await advance(f.repository, session);
  }
  assert.equal(session.performances.length, 8); assert.equal(new Set(session.performances.map(item => item.sessionSetId)).size, 8);
  assert.deepEqual(session.performances.map(item => item.sortOrder), [0, 1, 2, 3, 4, 5, 6, 7]);
  const order = session.performances.map(item => session.sets.find(series => series.id === item.sessionSetId)!.sessionExerciseId);
  assert.deepEqual(order, [chosen.id, chosen.id, original.exercise.id, original.exercise.id, session.exercises[1]!.id, session.exercises[1]!.id, session.exercises[3]!.id, session.exercises[3]!.id]);
});

test('a choice during paused rest never closes or alters that interval; its real duration is saved only by explicit completion', async t => {
  const f = await fixture(':memory:', 60); t.after(() => f.db.close());
  let session = await f.repository.startOrResume(f.workout.id);
  session = await f.repository.validateSet(session.id, active(session).set.id, { weightKg: 40, reps: 8, rir: null });
  const rest = session.rests[0]!; f.advance(10000); session = await f.repository.pauseRest(session.id, rest.id);
  const savedRest = structuredClone(session.rests[0]); f.advance(20000);
  const pending = selectSessionStep(session); assert.equal(pending.phase, 'rest'); if (pending.phase !== 'rest') throw new Error('rest');
  session = await f.repository.chooseNextExercise(session.id, session.exercises[3]!.id, pending.nextSet.id);
  assert.deepEqual(session.rests[0], savedRest); assert.equal(selectSessionStep(session).phase, 'rest');
  assert.equal(calculateRestTiming(session.rests[0]!, Date.parse(f.now())).chronologicalMs, 30000);
  session = await f.repository.completeRest(session.id, rest.id);
  assert.equal(session.rests[0]!.chronologicalMs, 30000); assert.equal(session.rests[0]!.activeMs, 10000);
  assert.equal(active(session).exercise.id, session.exercises[3]!.id);
});

test('a chosen final program exercise still opens its own rest if earlier series remain', async t => {
  const f = await fixture(':memory:', 17); t.after(() => f.db.close());
  let session = await f.repository.startOrResume(f.workout.id);
  session = await f.repository.chooseNextExercise(session.id, session.exercises[3]!.id, active(session).set.id);
  session = await f.repository.validateSet(session.id, active(session).set.id, { weightKg: 10, reps: 8, rir: null });
  session = await advance(f.repository, session);
  session = await f.repository.validateSet(session.id, active(session).set.id, { weightKg: 10, reps: 8, rir: null });
  assert.equal(selectSessionStep(session).phase, 'rest'); assert.equal(session.rests[1]!.plannedSeconds, 17);
  session = await advance(f.repository, session); assert.equal(active(session).exercise.plannedOrder, 0);
});

test('exceptional choice and partial replacement survive close/reopen; finished summary remains after program deletion', async t => {
  const directory = mkdtempSync(join(tmpdir(), 'logbook-m2-')); t.after(() => rmSync(directory, { force: true, recursive: true }));
  const path = join(directory, 'db.sqlite'), f = await fixture(path);
  let session = await f.repository.startOrResume(f.workout.id);
  session = await f.repository.chooseNextExercise(session.id, session.exercises[2]!.id, active(session).set.id);
  const step = active(session);
  session = await f.repository.replaceExercise(session.id, step.exercise.id, f.alternative.id, step.set.id);
  const id = session.id; f.db.close();
  const db = new SqliteDatabase(path); t.after(() => db.close()); await initializeDatabase(db);
  let serial = 0; const repository = new SessionRepository(db, () => `reopen-${++serial}`, f.now);
  assert.deepEqual(await repository.getActiveSession(), session);
  while (selectSessionStep(session).phase !== 'ready_to_finish') {
    session = await repository.validateSet(id, active(session).set.id, { weightKg: 10, reps: 5, rir: 2 });
    session = await advance(repository, session);
  }
  f.advance(3700000); session = await repository.finishSession(id);
  const summary = summarizeSession(session);
  assert.equal(summary.durationMs, 3700000); assert.equal(summary.performedSetCount, 8); assert.equal(summary.loggedTonnageKg, 400);
  const programs = new ProgramRepository(db, () => 'unused', f.now); await programs.deleteProgram(f.program.id);
  assert.deepEqual(summarizeSession((await repository.getSession(id))!), summary);
  assert.equal((await repository.listCompletedSessions())[0]!.id, id);
  const nextDb = new SqliteDatabase(path); t.after(() => nextDb.close()); await initializeDatabase(nextDb);
  const nextRepository = new SessionRepository(nextDb, () => 'unused');
  assert.deepEqual(summarizeSession((await nextRepository.getSession(id))!), summary);
  assert.equal(summary.exercises[0]!.exercise.name, 'Haltères');
  assert.equal(summary.exercises[0]!.replacedFrom?.name, 'Élévations');
});

test('replacement or choice transaction failure rolls back every moved series, target, event and selected exercise', async t => {
  const f = await fixture(); t.after(() => f.db.close());
  const session = await f.repository.startOrResume(f.workout.id), step = active(session), before = await plans(f.db);
  await f.db.execAsync(`CREATE TRIGGER fail_replacement BEFORE INSERT ON session_exercise_replacements BEGIN SELECT RAISE(ABORT,'replacement failed'); END;`);
  await assert.rejects(f.repository.replaceExercise(session.id, step.exercise.id, f.alternative.id, step.set.id), /replacement failed/);
  assert.deepEqual(await f.repository.getSession(session.id), session); assert.deepEqual(await plans(f.db), before);
  await f.db.execAsync(`CREATE TRIGGER fail_choice BEFORE UPDATE OF selected_exercise_id ON workout_sessions BEGIN SELECT RAISE(ABORT,'choice failed'); END;`);
  await assert.rejects(f.repository.chooseNextExercise(session.id, session.exercises[2]!.id, step.set.id), /choice failed/);
  assert.deepEqual(await f.repository.getSession(session.id), session);
});

test('stale rapid choices and foreign or finished exercises are rejected without changing performed data', async t => {
  const f = await fixture(); t.after(() => f.db.close());
  let session = await f.repository.startOrResume(f.workout.id); const step = active(session);
  session = await f.repository.chooseNextExercise(session.id, session.exercises[2]!.id, step.set.id);
  await assert.rejects(f.repository.chooseNextExercise(session.id, session.exercises[3]!.id, step.set.id), /changé/);
  await assert.rejects(f.repository.replaceExercise(session.id, step.exercise.id, f.alternative.id, step.set.id), /active/);
  await assert.rejects(f.repository.chooseNextExercise(session.id, 'foreign', active(session).set.id), /plus de série/);
  await assert.rejects(f.db.runAsync("UPDATE workout_sessions SET selected_exercise_id = 'foreign' WHERE id = ?", session.id), /another session/);
  assert.deepEqual(await f.repository.getSession(session.id), session);
});

test('replacement chains keep every snapshot and reject rewriting performed exercise identity', async t => {
  const f = await fixture(); t.after(() => f.db.close());
  let session = await f.repository.startOrResume(f.workout.id); const first = active(session);
  session = await f.repository.replaceExercise(session.id, first.exercise.id, f.alternative.id, first.set.id);
  const second = active(session);
  session = await f.repository.replaceExercise(session.id, second.exercise.id, first.exercise.sourceCatalogExerciseId, second.set.id);
  assert.equal(session.replacements!.length, 2); assert.equal(active(session).exercise.name, first.exercise.name);
  assert.equal(active(session).set.targets.targetWeightKg, null); assert.equal(session.exercises.length, 6);
  session = await f.repository.validateSet(session.id, active(session).set.id, { weightKg: 30, reps: 8, rir: 2 });
  await assert.rejects(f.db.runAsync('UPDATE session_exercises SET name = ? WHERE id = ?', 'other', first.exercise.id), /immutable/);
  await assert.rejects(f.db.runAsync('UPDATE session_sets SET session_exercise_id = ? WHERE id = ?', first.exercise.id, first.set.id), /immutable/);
});

test('another execution of the template restores its original exercise and charges', async t => {
  const f = await fixture(); t.after(() => f.db.close());
  let session = await f.repository.startOrResume(f.workout.id), first = active(session);
  session = await f.repository.replaceExercise(session.id, first.exercise.id, f.alternative.id, first.set.id);
  while (selectSessionStep(session).phase !== 'ready_to_finish') {
    session = await f.repository.validateSet(session.id, active(session).set.id, { weightKg: null, reps: 8, rir: null });
    session = await advance(f.repository, session);
  }
  await f.repository.finishSession(session.id);
  const next = await f.repository.startOrResume(f.workout.id);
  assert.equal(active(next).exercise.name, first.exercise.name); assert.equal(active(next).set.targets.targetWeightKg, 40);
  assert.deepEqual(next.replacements, []); assert.deepEqual(next.exerciseChoices, []);
});

async function legacyV3(db: SqliteDatabase) {
  await db.execAsync(readFileSync(new URL('./fixtures/m12-v3.sql', import.meta.url), 'utf8'));
  const start = '2026-10-14T12:00:00.000Z', finish = '2026-10-14T13:00:00.000Z';
  await db.runAsync('INSERT INTO programs (id,name,created_at,updated_at) VALUES (?,?,?,?)', 'p', 'Programme M0', start, start);
  await db.runAsync('INSERT INTO workout_templates (id,program_id,name,sort_order,created_at,updated_at) VALUES (?,?,?,?,?,?)', 'w', 'p', 'Séance M0', 0, start, start);
  await db.runAsync(`INSERT INTO exercise_catalog (id,name,muscle_group,equipment,instructions,weight_mode,is_custom,created_at,updated_at)
    VALUES ('c','Barre M1.1','Dos','Barre','Consigne','total',1,?,?)`, start, start);
  await db.runAsync(`INSERT INTO workout_exercises (id,workout_template_id,exercise_id,sort_order,created_at,updated_at) VALUES ('we','w','c',0,?,?)`, start, start);
  for (let i = 0; i < 2; i++) await db.runAsync(`INSERT INTO set_templates (id,workout_exercise_id,sort_order,kind,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec,created_at,updated_at)
    VALUES (?,'we',?,'work',8,12,40,2,20,?,?)`, `template${i}`, i, start, start);
  for (const [id, status, started, ended] of [['done', 'completed', start, finish], ['active', 'active', '2026-10-14T14:00:00.000Z', null]] as const) {
    await db.runAsync(`INSERT INTO workout_sessions (id,source_workout_template_id,source_program_id,workout_name,program_name,status,started_at,finished_at)
      VALUES (?,'w','p','Séance M0','Programme M0',?,?,?)`, id, status, started, ended);
    await db.runAsync(`INSERT INTO session_exercises (id,session_id,source_workout_exercise_id,source_catalog_exercise_id,sort_order,name,muscle_group,equipment,instructions,notes,weight_mode)
      VALUES (?,?,'we','c',0,'Barre réalisée','Dos','Barre','Consigne','','total')`, `ex-${id}`, id);
    for (let i = 0; i < 2; i++) await db.runAsync(`INSERT INTO session_sets (id,session_id,session_exercise_id,source_set_template_id,sort_order,series_index,label,kind,notes,original_targets,reps_min,reps_max,target_weight_kg,target_rir,rest_after_sec)
      VALUES (?,?,?,?,?,?,'','work','',?,8,12,40,2,20)`, `${id}-${i}`, id, `ex-${id}`, `template${i}`, i, i,
      JSON.stringify({ repsMin: 8, repsMax: 12, targetWeightKg: 40, targetRir: 2, restAfterSec: 20 }));
    await db.runAsync(`INSERT INTO performed_sets (id,session_id,session_set_id,sort_order,weight_kg,reps,rir,performed_at,advanced_at)
      VALUES (?,?,?,0,40,8,2,?,?)`, `perf-${id}`, id, `${id}-0`, started, id === 'done' ? finish : null);
    await db.runAsync(`INSERT INTO rest_intervals (id,session_id,performed_set_id,planned_seconds,started_at,ended_at,chronological_ms,active_ms)
      VALUES (?,?,?,20,?,?,?,?)`, `rest-${id}`, id, `perf-${id}`, started, ended, id === 'done' ? 3600000 : null, id === 'done' ? 3590000 : null);
    await db.runAsync(`INSERT INTO rest_pauses (id,rest_interval_id,started_at,ended_at) VALUES (?,?,?,?)`, `pause-${id}`, `rest-${id}`, started,
      id === 'done' ? '2026-10-14T12:00:10.000Z' : null);
    if (id === 'done') await db.runAsync(`INSERT INTO performed_sets (id,session_id,session_set_id,sort_order,weight_kg,reps,rir,performed_at,advanced_at)
      VALUES ('last','done','done-1',1,NULL,10,NULL,?,?)`, finish, finish);
  }
}
async function legacyRecords(db: SqliteDatabase) {
  const result: Record<string, { columns: string; rows: unknown[] }> = {};
  for (const table of ['programs', 'workout_templates', 'exercise_catalog', 'workout_exercises', 'set_templates',
    'workout_sessions', 'session_exercises', 'session_sets', 'performed_sets', 'rest_intervals', 'rest_pauses']) {
    const fields = await db.getAllAsync<{ name: string }>(`PRAGMA table_info(${table})`);
    const columns = fields.map(item => item.name).join(',');
    result[table] = { columns, rows: await db.getAllAsync(`SELECT ${columns} FROM ${table} ORDER BY id`) };
  }
  return result;
}

test('V4 preserves every released M1.2 record, running pause, completed summary and program target during migration', async t => {
  const db = new SqliteDatabase(); t.after(() => db.close()); await legacyV3(db);
  const before = await legacyRecords(db); await initializeDatabase(db); await initializeDatabase(db);
  for (const [table, data] of Object.entries(before)) assert.deepEqual(await db.getAllAsync(`SELECT ${data.columns} FROM ${table} ORDER BY id`), data.rows);
  assert.equal((await db.getFirstAsync<{ user_version: number }>('PRAGMA user_version'))!.user_version, DATABASE_VERSION);
  const repository = new SessionRepository(db, () => 'unused');
  const session = (await repository.getActiveSession())!;
  assert.equal(session.id, 'active'); assert.equal(session.selectedExerciseId, null); assert.deepEqual(session.exerciseChoices, []);
  assert.equal(selectSessionStep(session).phase, 'rest'); assert.equal(session.rests[0]!.pauses[0]!.endedAt, null);
  assert.equal(calculateRestTiming(session.rests[0]!, Date.parse('2026-10-14T15:00:00.000Z')).activeMs, 0);
  const summary = summarizeSession((await repository.getSession('done'))!);
  assert.equal(summary.performedSetCount, 2); assert.equal(summary.durationMs, 3600000); assert.equal(summary.loggedTonnageKg, 320); assert.equal(summary.meanRir, 2);
  assert.equal((await repository.listCompletedSessions())[0]!.id, 'done');
  assert.deepEqual(await db.getAllAsync('PRAGMA foreign_key_check'), []);
});

test('failed V4 migration rolls back added columns/tables and preserves the filled V3 including all pauses', async t => {
  const db = new SqliteDatabase(); t.after(() => db.close()); await legacyV3(db); const before = await legacyRecords(db);
  const facade = {
    execAsync: async (sql: string) => { await db.execAsync(sql); if (sql.includes('CREATE TABLE session_exercise_choices')) throw new Error('migration error'); },
    runAsync: db.runAsync.bind(db), getFirstAsync: db.getFirstAsync.bind(db), getAllAsync: db.getAllAsync.bind(db), withTransactionAsync: db.withTransactionAsync.bind(db),
  };
  await assert.rejects(initializeDatabase(facade), /migration error/);
  assert.deepEqual(await legacyRecords(db), before);
  assert.equal((await db.getFirstAsync<{ user_version: number }>('PRAGMA user_version'))!.user_version, 3);
  assert.equal(await db.getFirstAsync("SELECT name FROM sqlite_master WHERE name = 'session_exercise_choices'"), null);
});

test('snapshot reads cannot straddle a replacement: no old exercise list paired with new series assignments', async t => {
  const f = await fixture(); t.after(() => f.db.close());
  const session = await f.repository.startOrResume(f.workout.id), step = active(session);
  let release!: () => void, entered!: () => void, first = true, writeEntered = false;
  const held = new Promise<void>(done => { release = done; }), reading = new Promise<void>(done => { entered = done; });
  const facade = {
    execAsync: f.db.execAsync.bind(f.db), runAsync: f.db.runAsync.bind(f.db), getFirstAsync: f.db.getFirstAsync.bind(f.db),
    getAllAsync: async <T>(sql: string, ...args: (string | number | null)[]) => {
      const rows = await f.db.getAllAsync<T>(sql, ...args);
      if (first && sql.includes('FROM session_exercises')) { first = false; entered(); await held; }
      return rows;
    },
    withTransactionAsync: async (task: () => Promise<void>) => { writeEntered = true; await f.db.withTransactionAsync(task); },
  };
  let id = 0; const repository = new SessionRepository(facade, () => `read-${++id}`, f.now);
  const read = repository.getSession(session.id); await reading;
  const write = repository.replaceExercise(session.id, step.exercise.id, f.alternative.id, step.set.id);
  await new Promise<void>(resolve => setImmediate(resolve)); assert.equal(writeEntered, false);
  release(); assert.deepEqual(await read, session);
  const updated = await write; assert.equal(active(updated).exercise.name, f.alternative.name);
  assert.deepEqual(await repository.getSession(session.id), updated);
});

test('temporary alternative targets cannot be written into the original program; this-session editing remains possible', async t => {
  const f = await fixture(); t.after(() => f.db.close());
  let session = await f.repository.startOrResume(f.workout.id), step = active(session); const before = await plans(f.db);
  session = await f.repository.replaceExercise(session.id, step.exercise.id, f.alternative.id, step.set.id); step = active(session);
  const changes = { ...step.set.targets, targetWeightKg: 18, restAfterSec: 70 };
  await assert.rejects(f.repository.updateSetTargets(session.id, step.set.id, changes, 'program'), /remplacé/);
  assert.deepEqual(await f.repository.getSession(session.id), session); assert.deepEqual(await plans(f.db), before);
  session = await f.repository.updateSetTargets(session.id, step.set.id, changes, 'session');
  assert.deepEqual(active(session).set.targets, changes); assert.deepEqual(await plans(f.db), before);
});

test('Expo exclusive-connection path keeps replacement/choice mutations scoped and atomic even with foreign keys off', async t => {
  const f = await fixture(); t.after(() => f.db.close()); let session = await f.repository.startOrResume(f.workout.id);
  let transactions = 0;
  const unsupported = async () => { throw new Error('outer connection used during exclusive transaction'); };
  const facade = {
    execAsync: unsupported, runAsync: unsupported, getFirstAsync: unsupported, getAllAsync: unsupported, withTransactionAsync: unsupported,
    withExclusiveTransactionAsync: async (task: (db: SqliteDatabase) => Promise<void>) => {
      transactions++; await f.db.execAsync('PRAGMA foreign_keys = OFF');
      await f.db.withTransactionAsync(() => task(f.db)); await f.db.execAsync('PRAGMA foreign_keys = ON');
    },
  };
  let id = 0; const repository = new SessionRepository(facade, () => `exclusive-m2-${++id}`, f.now);
  session = await repository.chooseNextExercise(session.id, session.exercises[2]!.id, active(session).set.id);
  let step = active(session); session = await repository.replaceExercise(session.id, step.exercise.id, f.alternative.id, step.set.id);
  step = active(session); session = await repository.validateSet(session.id, step.set.id, { weightKg: 10, reps: 8, rir: 1 });
  assert.equal(transactions, 3); assert.equal(session.performances.length, 1);
  assert.deepEqual(await f.db.getAllAsync('PRAGMA foreign_key_check'), []);
});

test('changing catalog weight mode while a session is active cannot copy its old-unit targets into future programming', async t => {
  const f = await fixture(); t.after(() => f.db.close());
  const session = await f.repository.startOrResume(f.workout.id), step = active(session);
  const catalog = await f.training.getCatalogExercise(step.exercise.sourceCatalogExerciseId);
  await f.training.updateCustomExercise(catalog.id, { ...catalog, weightMode: 'per_hand' });
  const before = await plans(f.db);
  await assert.rejects(f.repository.updateSetTargets(session.id, step.set.id, { ...step.set.targets, targetWeightKg: 45 }, 'program'), /mode de charge/);
  assert.deepEqual(await plans(f.db), before); assert.deepEqual(await f.repository.getSession(session.id), session);
});
