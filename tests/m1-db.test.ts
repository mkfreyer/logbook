import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { DatabaseSync } from 'node:sqlite';
import { test } from 'node:test';
import { INITIAL_EXERCISES } from '../src/db/exerciseCatalog';
import { DATABASE_VERSION, initializeDatabase } from '../src/db/migrations';
import { ProgramRepository } from '../src/db/repository';
import { TrainingNotFoundError, TrainingRepository, TrainingValidationError } from '../src/db/trainingRepository';
import type { Database } from '../src/db/types';
import type { CatalogExerciseInput, SetTemplateInput } from '../src/domain/training';

/** Real SQLite, portable on Windows and Linux with our supported Node version. */
class SQLiteTestAdapter implements Database {
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

const m0Schema = `
  CREATE TABLE programs (
    id TEXT PRIMARY KEY NOT NULL, name TEXT NOT NULL CHECK(length(trim(name)) BETWEEN 1 AND 80),
    description TEXT NOT NULL DEFAULT '' CHECK(length(description) <= 1000),
    sport_type TEXT NOT NULL DEFAULT 'musculation' CHECK(sport_type = 'musculation'),
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
  );
  CREATE TABLE workout_templates (
    id TEXT PRIMARY KEY NOT NULL, program_id TEXT NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
    name TEXT NOT NULL CHECK(length(trim(name)) BETWEEN 1 AND 80), notes TEXT NOT NULL DEFAULT '' CHECK(length(notes) <= 1000),
    sort_order INTEGER NOT NULL CHECK(sort_order >= 0), created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
    UNIQUE(program_id, sort_order)
  );
  CREATE INDEX programs_updated_at ON programs(updated_at DESC, created_at DESC, id);
  CREATE INDEX workouts_program_order ON workout_templates(program_id, sort_order, id);
  PRAGMA user_version = 1;
`;

const customInput: CatalogExerciseInput = { name: 'Mon exercice personnel', muscleGroup: 'Dos', equipment: 'Poulie', weightMode: 'total', instructions: 'Ma consigne.' };
const setInput: SetTemplateInput = { kind: 'work', repsMin: 8, repsMax: 12, restAfterSec: 90 };

function repositories(db: Database) {
  let id = 0, tick = 0;
  const uuid = () => `training-test-${++id}`;
  const now = () => new Date(Date.UTC(2026, 9, 14, 12, 0, tick++)).toISOString();
  return { programs: new ProgramRepository(db, uuid, now), training: new TrainingRepository(db, uuid, now) };
}

async function fixture(filename = ':memory:') {
  const db = new SQLiteTestAdapter(filename); await initializeDatabase(db);
  const repos = repositories(db);
  const program = await repos.programs.createProgram({ name: 'Mon programme' });
  const workout = await repos.programs.createWorkout(program.id, { name: 'Séance A' });
  const catalog = await repos.training.listCatalog();
  const exercise = await repos.training.addWorkoutExercise(workout.id, { exerciseId: catalog[0]!.id });
  return { db, ...repos, program, workout, catalog, exercise };
}

test('V2 adds a real exercise library without creating user programs, workouts, series or performances', async t => {
  const db = new SQLiteTestAdapter(); t.after(() => db.close());
  await initializeDatabase(db);
  const { programs, training } = repositories(db);
  const library = await training.listCatalog();
  assert.equal(library.length, INITIAL_EXERCISES.length);
  assert.equal(new Set(library.map(item => item.id)).size, library.length);
  assert.ok(library.every(item => !item.isCustom && item.instructions && item.muscleGroup && item.equipment));
  assert.ok(library.some(item => item.weightMode === 'per_hand'));
  assert.ok(library.some(item => item.weightMode === 'additional'));
  assert.deepEqual(await programs.listPrograms(), []);
  for (const table of ['workout_templates', 'workout_exercises', 'set_templates']) assert.deepEqual(await db.getAllAsync(`SELECT * FROM ${table}`), []);
  assert.equal((await db.getFirstAsync<{ user_version: number }>('PRAGMA user_version'))?.user_version, DATABASE_VERSION);
  assert.deepEqual(await db.getAllAsync('PRAGMA foreign_key_check'), []);
});

test('migration from populated M0 preserves the exact schema and every existing record', async t => {
  const db = new SQLiteTestAdapter(); t.after(() => db.close());
  await db.execAsync('PRAGMA foreign_keys = ON;'); await db.execAsync(m0Schema);
  const { programs, training } = repositories(db);
  const kept = await programs.createProgram({ name: 'Programme M0', description: 'Ne pas modifier' });
  const first = await programs.createWorkout(kept.id, { name: 'Séance M0 A', notes: 'Mes notes' });
  const second = await programs.createWorkout(kept.id, { name: 'Séance M0 B' });
  const programBefore = await programs.getProgram(kept.id);
  const schemaBefore = await db.getAllAsync("SELECT name, sql FROM sqlite_master WHERE name IN ('programs', 'workout_templates', 'programs_updated_at', 'workouts_program_order') ORDER BY name");
  await initializeDatabase(db);
  assert.deepEqual(await programs.getProgram(kept.id), programBefore);
  assert.deepEqual(await programs.listWorkouts(kept.id), [first, second]);
  assert.deepEqual(await db.getAllAsync("SELECT name, sql FROM sqlite_master WHERE name IN ('programs', 'workout_templates', 'programs_updated_at', 'workouts_program_order') ORDER BY name"), schemaBefore);
  assert.deepEqual(await training.listWorkoutExercises(first.id), []);
  const planned = await training.addWorkoutExercise(first.id, { exerciseId: INITIAL_EXERCISES[0]!.id });
  await training.createSet(planned.id, setInput);
  await initializeDatabase(db); await initializeDatabase(db);
  assert.deepEqual(await programs.getProgram(kept.id), programBefore);
  assert.equal((await training.listSets(planned.id)).length, 1);
  assert.equal((await training.listCatalog()).length, INITIAL_EXERCISES.length);
});

test('failed V2 catalogue insertion rolls back all new tables and preserves populated M0 version 1', async t => {
  class FailingMigrationAdapter extends SQLiteTestAdapter {
    inserts = 0;
    override async runAsync(sql: string, ...params: (string | number | null)[]) {
      if (sql.includes('INSERT INTO exercise_catalog') && ++this.inserts === 3) throw new Error('storage failure');
      return super.runAsync(sql, ...params);
    }
  }
  const db = new FailingMigrationAdapter(); t.after(() => db.close()); await db.execAsync(m0Schema);
  const { programs } = repositories(db);
  const program = await programs.createProgram({ name: 'Conserver après erreur' });
  const workout = await programs.createWorkout(program.id, { name: 'Séance conservée' });
  await assert.rejects(initializeDatabase(db), /storage failure/);
  assert.equal((await db.getFirstAsync<{ user_version: number }>('PRAGMA user_version'))?.user_version, 1);
  assert.deepEqual(await programs.getWorkout(workout.id), workout);
  assert.deepEqual(await programs.listPrograms(), [{ ...program, workoutCount: 1 }]);
  for (const table of ['exercise_catalog', 'workout_exercises', 'set_templates']) {
    assert.equal(await db.getFirstAsync("SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?", table), null);
  }
  await initializeDatabase(db);
  assert.equal((await db.getFirstAsync<{ user_version: number }>('PRAGMA user_version'))?.user_version, 2);
});

test('library search ignores accents and case, matches equipment and never executes SQL-looking terms', async t => {
  const { db, training } = await fixture(); t.after(() => db.close());
  const found = await training.listCatalog('DEVELOPPE COUCHE');
  assert.equal(found.length, 1); assert.equal(found[0]!.name, 'Développé couché barre');
  assert.ok((await training.listCatalog('epaules HALTERES')).every(item => item.muscleGroup === 'Épaules'));
  assert.ok((await training.listCatalog('poulie')).length >= 2);
  assert.deepEqual(await training.listCatalog("'); DELETE FROM exercise_catalog; --"), []);
  assert.equal((await training.listCatalog()).length, INITIAL_EXERCISES.length);
});

test('custom exercise creation and editing preserve catalog identity and existing occurrences', async t => {
  const { db, training, workout } = await fixture(); t.after(() => db.close());
  const custom = await training.createCustomExercise({ ...customInput, name: " Mon rowing d'Alice " });
  assert.equal(custom.name, "Mon rowing d'Alice"); assert.equal(custom.isCustom, true);
  const first = await training.addWorkoutExercise(workout.id, { exerciseId: custom.id });
  const second = await training.addWorkoutExercise(workout.id, { exerciseId: custom.id });
  const renamed = await training.updateCustomExercise(custom.id, { ...customInput, name: 'Mon rowing renommé', weightMode: 'per_hand' });
  assert.equal(renamed.id, custom.id); assert.equal(renamed.createdAt, custom.createdAt);
  assert.notEqual(renamed.updatedAt, custom.updatedAt);
  assert.deepEqual((await training.listWorkoutExercises(workout.id)).filter(item => item.exerciseId === custom.id).map(item => item.id), [first.id, second.id]);
  assert.deepEqual((await training.getWorkoutExercise(first.id)).exercise, renamed);
  await initializeDatabase(db);
  assert.deepEqual(await training.getCatalogExercise(custom.id), renamed);
  await assert.rejects(training.updateCustomExercise(INITIAL_EXERCISES[0]!.id, customInput), TrainingValidationError);
});

test('exercise occurrences can be added, edited and repeated without altering the library or their sets', async t => {
  const { db, training, exercise, workout, catalog } = await fixture(); t.after(() => db.close());
  const second = await training.addWorkoutExercise(workout.id, { exerciseId: exercise.exerciseId, notes: 'Deuxième occurrence' });
  assert.notEqual(second.id, exercise.id); assert.equal(second.exerciseId, exercise.exerciseId);
  const plannedSet = await training.createSet(exercise.id, setInput);
  const edited = await training.updateWorkoutExercise(exercise.id, { exerciseId: catalog[1]!.id, notes: ' Consigne personnelle ' });
  assert.equal(edited.id, exercise.id); assert.equal(edited.sortOrder, exercise.sortOrder);
  assert.equal(edited.createdAt, exercise.createdAt); assert.equal(edited.notes, 'Consigne personnelle');
  assert.deepEqual(await training.getSet(plannedSet.id), plannedSet);
  assert.deepEqual((await training.listWorkoutExercises(workout.id)).map(item => item.id), [exercise.id, second.id]);
  assert.deepEqual(await training.getCatalogExercise(exercise.exerciseId), exercise.exercise);
});

test('each series persists its own label, type, reps range, optional weight/RIR and individual rest', async t => {
  const { db, training, exercise } = await fixture(); t.after(() => db.close());
  const warmup = await training.createSet(exercise.id, { kind: 'warmup', label: 'Échauffement', repsMin: 15, repsMax: 15, restAfterSec: 45 });
  const top = await training.createSet(exercise.id, { kind: 'top_set', label: 'Mon top set', repsMin: 6, repsMax: 8, targetWeightKg: 42.5, targetRir: 2, restAfterSec: 180, notes: 'Contrôler la descente' });
  const backoff = await training.createSet(exercise.id, { kind: 'back_off', repsMin: 10, repsMax: 12, targetWeightKg: 35, targetRir: 0, restAfterSec: 0 });
  assert.deepEqual((await training.listSets(exercise.id)).map(item => item.restAfterSec), [45, 180, 0]);
  assert.equal(warmup.targetRir, null); assert.equal(warmup.targetWeightKg, null);
  assert.equal(backoff.targetRir, 0); assert.equal(top.targetWeightKg, 42.5);
  const edited = await training.updateSet(top.id, { kind: 'custom', label: ' Ma série ', repsMin: 8, repsMax: 10, targetWeightKg: null, targetRir: null, restAfterSec: 120 });
  assert.equal(edited.id, top.id); assert.equal(edited.createdAt, top.createdAt); assert.equal(edited.sortOrder, top.sortOrder);
  assert.equal(edited.label, 'Ma série'); assert.equal(edited.targetRir, null); assert.equal(edited.targetWeightKg, null);
  assert.deepEqual(await training.getSet(warmup.id), warmup); assert.deepEqual(await training.getSet(backoff.id), backoff);
  assert.deepEqual((await training.listSets(exercise.id)).map(item => item.restAfterSec), [45, 120, 0]);
});

test('invalid catalog and numeric series inputs fail without creating or partially changing data', async t => {
  const { db, training, exercise } = await fixture(); t.after(() => db.close());
  const before = await training.listCatalog();
  for (const input of [{ ...customInput, name: '' }, { ...customInput, name: 'a'.repeat(81) },
    { ...customInput, muscleGroup: '' }, { ...customInput, equipment: '' },
    { ...customInput, instructions: 'a'.repeat(1001) }, { ...customInput, weightMode: 'invalid' }]) {
    await assert.rejects(training.createCustomExercise(input as CatalogExerciseInput), TrainingValidationError);
  }
  assert.deepEqual(await training.listCatalog(), before);
  const original = await training.createSet(exercise.id, setInput);
  const invalid = [ { repsMin: -1 }, { repsMin: 1.5 }, { repsMin: Number.NaN }, { repsMax: 7 },
    { targetWeightKg: -1 }, { targetWeightKg: Number.POSITIVE_INFINITY }, { targetWeightKg: Number.NaN },
    { targetRir: -1 }, { targetRir: 11 }, { targetRir: 1.5 }, { restAfterSec: -1 }, { restAfterSec: 90.5 },
    { restAfterSec: 86401 }, { label: 'a'.repeat(81) }, { notes: 'a'.repeat(1001) }, { kind: 'invalid' } ];
  for (const overrides of invalid) {
    const input = { ...setInput, ...overrides } as SetTemplateInput;
    await assert.rejects(training.createSet(exercise.id, input), TrainingValidationError);
    await assert.rejects(training.updateSet(original.id, input), TrainingValidationError);
    assert.deepEqual(await training.getSet(original.id), original);
  }
  assert.deepEqual(await training.listSets(exercise.id), [original]);
  const zero = await training.createSet(exercise.id, { ...setInput, repsMin: 0, repsMax: 0, targetWeightKg: 0, targetRir: 10, restAfterSec: 86400 });
  assert.equal(zero.targetWeightKg, 0); assert.equal(zero.restAfterSec, 86400);
});

test('database constraints independently reject invalid targets, missing parents and referenced catalogue deletion', async t => {
  const { db, training, exercise } = await fixture(); t.after(() => db.close());
  const planned = await training.createSet(exercise.id, setInput);
  for (const update of ['reps_min = -1', 'reps_max = 1', 'reps_min = 2.5', 'target_weight_kg = -1', 'target_rir = 11', 'target_rir = 1.5', 'rest_after_sec = -1', 'rest_after_sec = 86401', 'kind = \'invalid\'']) {
    await assert.rejects(db.runAsync(`UPDATE set_templates SET ${update} WHERE id = ?`, planned.id), /CHECK/);
  }
  await assert.rejects(db.runAsync('UPDATE set_templates SET workout_exercise_id = ? WHERE id = ?', 'missing', planned.id), /FOREIGN KEY/);
  await assert.rejects(db.runAsync('UPDATE workout_exercises SET workout_template_id = ? WHERE id = ?', 'missing', exercise.id), /FOREIGN KEY/);
  await assert.rejects(db.runAsync('DELETE FROM exercise_catalog WHERE id = ?', exercise.exerciseId), /FOREIGN KEY/);
  assert.deepEqual(await training.getSet(planned.id), planned);
  assert.deepEqual(await db.getAllAsync('PRAGMA foreign_key_check'), []);
});

test('reordering exercise occurrences is an atomic scoped permutation with stable IDs and attached sets', async t => {
  const { db, training, programs, workout, exercise } = await fixture(); t.after(() => db.close());
  const second = await training.addWorkoutExercise(workout.id, { exerciseId: INITIAL_EXERCISES[1]!.id });
  const third = await training.addWorkoutExercise(workout.id, { exerciseId: INITIAL_EXERCISES[2]!.id });
  const plannedSet = await training.createSet(exercise.id, setInput);
  const independentWorkout = await programs.createWorkout(workout.programId, { name: 'Autre séance' });
  const independent = await training.addWorkoutExercise(independentWorkout.id, { exerciseId: exercise.exerciseId });
  await training.reorderWorkoutExercises(workout.id, [third.id, exercise.id, second.id]);
  assert.deepEqual((await training.listWorkoutExercises(workout.id)).map(item => [item.id, item.sortOrder]), [[third.id, 0], [exercise.id, 1], [second.id, 2]]);
  assert.deepEqual(await training.getSet(plannedSet.id), plannedSet);
  assert.deepEqual(await training.getWorkoutExercise(independent.id), independent);
  const before = await training.listWorkoutExercises(workout.id);
  for (const ids of [[third.id, exercise.id], [third.id, exercise.id, exercise.id], [third.id, exercise.id, independent.id], [third.id, exercise.id, 'missing']]) {
    await assert.rejects(training.reorderWorkoutExercises(workout.id, ids), TrainingValidationError);
    assert.deepEqual(await training.listWorkoutExercises(workout.id), before);
  }
});

test('reordering series moves each individual interval with its series and preserves other exercises', async t => {
  const { db, training, workout, exercise } = await fixture(); t.after(() => db.close());
  const first = await training.createSet(exercise.id, { ...setInput, restAfterSec: 45 });
  const middle = await training.createSet(exercise.id, { ...setInput, restAfterSec: 120 });
  const last = await training.createSet(exercise.id, { ...setInput, restAfterSec: 0 });
  const other = await training.addWorkoutExercise(workout.id, { exerciseId: exercise.exerciseId });
  const otherSet = await training.createSet(other.id, setInput);
  await training.reorderSets(exercise.id, [last.id, first.id, middle.id]);
  assert.deepEqual((await training.listSets(exercise.id)).map(item => [item.id, item.restAfterSec, item.sortOrder]), [[last.id, 0, 0], [first.id, 45, 1], [middle.id, 120, 2]]);
  assert.deepEqual(await training.getSet(otherSet.id), otherSet);
  const before = await training.listSets(exercise.id);
  for (const ids of [[last.id], [last.id, first.id, first.id], [last.id, first.id, otherSet.id]]) {
    await assert.rejects(training.reorderSets(exercise.id, ids), TrainingValidationError);
    assert.deepEqual(await training.listSets(exercise.id), before);
  }
});

test('storage failure halfway through a reorder rolls back positions and timestamps for exercises and series', async t => {
  const { db, training, workout, exercise } = await fixture(); t.after(() => db.close());
  const second = await training.addWorkoutExercise(workout.id, { exerciseId: exercise.exerciseId });
  const firstSet = await training.createSet(exercise.id, setInput);
  const secondSet = await training.createSet(exercise.id, setInput);
  const exercisesBefore = await training.listWorkoutExercises(workout.id), setsBefore = await training.listSets(exercise.id);
  await db.execAsync(`CREATE TRIGGER reject_exercise_reorder BEFORE UPDATE ON workout_exercises
    WHEN NEW.sort_order = 1 AND OLD.sort_order > 1 BEGIN SELECT RAISE(ABORT, 'exercise reorder failed'); END;`);
  await assert.rejects(training.reorderWorkoutExercises(workout.id, [second.id, exercise.id]), /exercise reorder failed/);
  assert.deepEqual(await training.listWorkoutExercises(workout.id), exercisesBefore);
  await db.execAsync(`CREATE TRIGGER reject_set_reorder BEFORE UPDATE ON set_templates
    WHEN NEW.sort_order = 1 AND OLD.sort_order > 1 BEGIN SELECT RAISE(ABORT, 'set reorder failed'); END;`);
  await assert.rejects(training.reorderSets(exercise.id, [secondSet.id, firstSet.id]), /set reorder failed/);
  assert.deepEqual(await training.listSets(exercise.id), setsBefore);
});

test('Expo exclusive transaction path receives all reorder queries instead of the outer connection', async t => {
  const { db, training, exercise } = await fixture(); t.after(() => db.close());
  const first = await training.createSet(exercise.id, setInput), second = await training.createSet(exercise.id, setInput);
  let exclusiveCalls = 0, transactionQueries = 0;
  const outer: Database = {
    execAsync: sql => db.execAsync(sql), runAsync: () => { throw new Error('outer write used'); },
    getFirstAsync: () => { throw new Error('outer read used'); }, getAllAsync: () => { throw new Error('outer list used'); },
    withTransactionAsync: () => { throw new Error('ordinary transaction used'); },
    withExclusiveTransactionAsync: async task => {
      exclusiveCalls++;
      const transaction: Database = {
        execAsync: sql => db.execAsync(sql),
        runAsync: (sql, ...params) => { transactionQueries++; return db.runAsync(sql, ...params); },
        getFirstAsync: (sql, ...params) => { transactionQueries++; return db.getFirstAsync(sql, ...params); },
        getAllAsync: (sql, ...params) => { transactionQueries++; return db.getAllAsync(sql, ...params); },
        withTransactionAsync: task => db.withTransactionAsync(task),
      };
      await db.withTransactionAsync(() => task(transaction));
    },
  };
  const exclusiveRepo = new TrainingRepository(outer, () => 'unused');
  await exclusiveRepo.reorderSets(exercise.id, [second.id, first.id]);
  assert.equal(exclusiveCalls, 1); assert.equal(transactionQueries, 5);
  assert.deepEqual((await training.listSets(exercise.id)).map(item => item.id), [second.id, first.id]);
});

test('concurrent additions are serialized, have unique positions, and the write queue recovers after an error', async t => {
  const { db, training, workout, exercise } = await fixture(); t.after(() => db.close());
  await Promise.all(Array.from({ length: 8 }, () => training.addWorkoutExercise(workout.id, { exerciseId: exercise.exerciseId })));
  const exercises = await training.listWorkoutExercises(workout.id);
  assert.deepEqual(exercises.map(item => item.sortOrder), Array.from({ length: 9 }, (_, i) => i));
  assert.equal(new Set(exercises.map(item => item.id)).size, 9);
  await Promise.all(Array.from({ length: 8 }, (_, i) => training.createSet(exercise.id, { ...setInput, restAfterSec: 30 + i })));
  assert.deepEqual((await training.listSets(exercise.id)).map(item => item.sortOrder), Array.from({ length: 8 }, (_, i) => i));
  await assert.rejects(training.reorderSets(exercise.id, ['missing']), TrainingValidationError);
  const added = await training.createSet(exercise.id, setInput); assert.equal(added.sortOrder, 8);
});

test('deleting one set or one exercise preserves sibling data and ordering, and cascades only its planned sets', async t => {
  const { db, training, workout, exercise } = await fixture(); t.after(() => db.close());
  const first = await training.createSet(exercise.id, setInput);
  const middle = await training.createSet(exercise.id, { ...setInput, restAfterSec: 120 });
  const last = await training.createSet(exercise.id, { ...setInput, restAfterSec: 30 });
  const other = await training.addWorkoutExercise(workout.id, { exerciseId: exercise.exerciseId });
  const independent = await training.createSet(other.id, { ...setInput, notes: 'À conserver' });
  await training.deleteSet(middle.id);
  assert.deepEqual(await training.listSets(exercise.id), [first, last]);
  const appended = await training.createSet(exercise.id, setInput); assert.equal(appended.sortOrder, 3);
  await training.deleteWorkoutExercise(exercise.id);
  for (const id of [first.id, last.id, appended.id]) await assert.rejects(training.getSet(id), TrainingNotFoundError);
  assert.deepEqual(await training.getWorkoutExercise(other.id), other);
  assert.deepEqual(await training.getSet(independent.id), independent);
  assert.deepEqual(await training.listWorkoutExercises(workout.id), [other]);
  assert.deepEqual(await training.getCatalogExercise(exercise.exerciseId), exercise.exercise);
  await assert.rejects(training.deleteSet(middle.id), TrainingNotFoundError);
  await assert.rejects(training.deleteWorkoutExercise(exercise.id), TrainingNotFoundError);
});

test('M0 workout and program deletions cascade preparation only and retain catalog and unrelated user data', async t => {
  const { db, training, programs, program, workout, exercise } = await fixture(); t.after(() => db.close());
  const custom = await training.createCustomExercise(customInput);
  await training.createSet(exercise.id, setInput);
  const deletedCustomOccurrence = await training.addWorkoutExercise(workout.id, { exerciseId: custom.id });
  await training.createSet(deletedCustomOccurrence.id, setInput);
  const keptProgram = await programs.createProgram({ name: 'Conserver' });
  const keptWorkout = await programs.createWorkout(keptProgram.id, { name: 'Conserver' });
  const keptExercise = await training.addWorkoutExercise(keptWorkout.id, { exerciseId: custom.id });
  const keptSet = await training.createSet(keptExercise.id, { ...setInput, targetWeightKg: 37.5 });
  const secondWorkout = await programs.createWorkout(program.id, { name: 'Autre préparation supprimée' });
  const secondExercise = await training.addWorkoutExercise(secondWorkout.id, { exerciseId: exercise.exerciseId });
  const secondSet = await training.createSet(secondExercise.id, setInput);
  await programs.deleteWorkout(workout.id);
  await assert.rejects(training.getWorkoutExercise(exercise.id), TrainingNotFoundError);
  assert.deepEqual(await training.getSet(secondSet.id), secondSet);
  await programs.deleteProgram(program.id);
  await assert.rejects(training.getSet(secondSet.id), TrainingNotFoundError);
  assert.deepEqual(await training.getWorkoutExercise(keptExercise.id), keptExercise);
  assert.deepEqual(await training.getSet(keptSet.id), keptSet);
  assert.deepEqual(await training.getCatalogExercise(custom.id), custom);
  assert.equal((await training.listCatalog()).length, INITIAL_EXERCISES.length + 1);
  assert.deepEqual(await programs.listPrograms(), [{ ...keptProgram, workoutCount: 1 }]);
  assert.deepEqual(await db.getAllAsync('PRAGMA foreign_key_check'), []);
});

test('storage errors roll back cascading exercise deletion and leave its sets available for retry', async t => {
  const { db, training, exercise } = await fixture(); t.after(() => db.close());
  const first = await training.createSet(exercise.id, setInput), second = await training.createSet(exercise.id, setInput);
  await db.execAsync(`CREATE TRIGGER reject_set_deletion BEFORE DELETE ON set_templates
    WHEN OLD.sort_order = 1 BEGIN SELECT RAISE(ABORT, 'delete failed'); END;`);
  await assert.rejects(training.deleteWorkoutExercise(exercise.id), /delete failed/);
  assert.deepEqual(await training.getWorkoutExercise(exercise.id), exercise);
  assert.deepEqual(await training.listSets(exercise.id), [first, second]);
  await db.execAsync('DROP TRIGGER reject_set_deletion;');
  await training.deleteWorkoutExercise(exercise.id);
  await assert.rejects(training.getWorkoutExercise(exercise.id), TrainingNotFoundError);
});

test('missing and SQL-looking identifiers are rejected without affecting existing plans', async t => {
  const { db, training, exercise, workout } = await fixture(); t.after(() => db.close());
  const planned = await training.createSet(exercise.id, setInput);
  for (const id of ['missing', "' OR 1=1 --"]) {
    await assert.rejects(training.getCatalogExercise(id), TrainingNotFoundError);
    await assert.rejects(training.getWorkoutExercise(id), TrainingNotFoundError);
    await assert.rejects(training.getSet(id), TrainingNotFoundError);
    await assert.rejects(training.listWorkoutExercises(id), TrainingNotFoundError);
    await assert.rejects(training.listSets(id), TrainingNotFoundError);
    await assert.rejects(training.addWorkoutExercise(id, { exerciseId: exercise.exerciseId }), TrainingNotFoundError);
    await assert.rejects(training.addWorkoutExercise(workout.id, { exerciseId: id }), TrainingNotFoundError);
    await assert.rejects(training.createSet(id, setInput), TrainingNotFoundError);
    await assert.rejects(training.updateSet(id, setInput), TrainingNotFoundError);
    await assert.rejects(training.deleteSet(id), TrainingNotFoundError);
    await assert.rejects(training.deleteWorkoutExercise(id), TrainingNotFoundError);
    await assert.rejects(training.reorderWorkoutExercises(id, []), TrainingNotFoundError);
    await assert.rejects(training.reorderSets(id, []), TrainingNotFoundError);
  }
  assert.deepEqual(await training.getWorkoutExercise(exercise.id), exercise);
  assert.deepEqual(await training.listSets(exercise.id), [planned]);
});

test('custom exercise, edited/reordered targets and deletions survive actual database close and reopen', async t => {
  const directory = mkdtempSync(join(tmpdir(), 'logbook-m11-')); t.after(() => rmSync(directory, { recursive: true, force: true }));
  const filename = join(directory, 'logbook.db');
  const { db, programs, training, workout, exercise } = await fixture(filename);
  const custom = await training.createCustomExercise(customInput);
  const second = await training.addWorkoutExercise(workout.id, { exerciseId: custom.id, notes: 'Ma consigne' });
  const firstSet = await training.createSet(second.id, setInput);
  const deleted = await training.createSet(second.id, setInput);
  const lastSet = await training.createSet(second.id, { ...setInput, kind: 'back_off', targetWeightKg: 12.5, targetRir: 2, restAfterSec: 30 });
  await training.deleteSet(deleted.id);
  await training.updateSet(firstSet.id, { ...setInput, label: 'Ma série enregistrée', restAfterSec: 180 });
  await training.reorderSets(second.id, [lastSet.id, firstSet.id]);
  await training.reorderWorkoutExercises(workout.id, [second.id, exercise.id]);
  const programsBefore = await programs.listPrograms(), exercisesBefore = await training.listWorkoutExercises(workout.id), setsBefore = await training.listSets(second.id);
  db.close();
  const reopened = new SQLiteTestAdapter(filename); t.after(() => reopened.close()); await initializeDatabase(reopened);
  const again = repositories(reopened);
  assert.deepEqual(await again.programs.listPrograms(), programsBefore);
  assert.deepEqual(await again.training.listWorkoutExercises(workout.id), exercisesBefore);
  assert.deepEqual(await again.training.listSets(second.id), setsBefore);
  assert.deepEqual(await again.training.getCatalogExercise(custom.id), custom);
  await assert.rejects(again.training.getSet(deleted.id), TrainingNotFoundError);
  assert.deepEqual(await reopened.getAllAsync('PRAGMA foreign_key_check'), []);
});
