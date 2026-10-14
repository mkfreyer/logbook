import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { DatabaseSync } from 'node:sqlite';
import { test } from 'node:test';
import { DATABASE_VERSION, initializeDatabase } from '../src/db/migrations';
import { NotFoundError, ProgramRepository, ValidationError } from '../src/db/repository';
import type { Database } from '../src/db/types';

/** Uses the real SQLite engine, with the same async contract as Expo SQLite. */
class SQLiteTestAdapter implements Database {
  readonly connection: DatabaseSync;

  constructor(filename = ':memory:') {
    this.connection = new DatabaseSync(filename);
  }

  async execAsync(sql: string): Promise<void> {
    this.connection.exec(sql);
  }

  async runAsync(sql: string, ...params: (string | number | null)[]) {
    const result = this.connection.prepare(sql).run(...params);
    return { changes: Number(result.changes) };
  }

  async getFirstAsync<T>(sql: string, ...params: (string | number | null)[]): Promise<T | null> {
    const row = this.connection.prepare(sql).get(...params);
    return row ? { ...row } as T : null;
  }

  async getAllAsync<T>(sql: string, ...params: (string | number | null)[]): Promise<T[]> {
    return this.connection.prepare(sql).all(...params).map((row) => ({ ...row }) as T);
  }

  async withTransactionAsync(task: () => Promise<void>): Promise<void> {
    this.connection.exec('BEGIN IMMEDIATE');
    try {
      await task();
      this.connection.exec('COMMIT');
    } catch (error) {
      this.connection.exec('ROLLBACK');
      throw error;
    }
  }

  close(): void {
    this.connection.close();
  }
}

async function fixture(filename = ':memory:') {
  const db = new SQLiteTestAdapter(filename);
  await initializeDatabase(db);
  let nextId = 0;
  let nextTime = 0;
  const repository = new ProgramRepository(
    db,
    () => `test-id-${++nextId}`,
    () => new Date(Date.UTC(2026, 9, 14, 0, 0, nextTime++)).toISOString(),
  );
  return { db, repository };
}

test('a fresh database is versioned, has foreign keys enabled, and has no sample programs', async (t) => {
  const { db, repository } = await fixture();
  t.after(() => db.close());
  assert.deepEqual(await repository.listPrograms(), []);
  assert.equal((await db.getFirstAsync<{ user_version: number }>('PRAGMA user_version'))?.user_version, DATABASE_VERSION);
  assert.equal((await db.getFirstAsync<{ foreign_keys: number }>('PRAGMA foreign_keys'))?.foreign_keys, 1);
  assert.deepEqual(await db.getAllAsync('SELECT * FROM workout_templates'), []);
});

test('programs and workout plans can be created, read and edited without changing identity or order', async (t) => {
  const { db, repository } = await fixture();
  t.after(() => db.close());
  const program = await repository.createProgram({ name: '  Mon programme  ', description: '  Trois jours  ' });
  assert.equal(program.name, 'Mon programme');
  assert.equal(program.description, 'Trois jours');
  assert.equal(program.sportType, 'musculation');
  assert.equal(program.workoutCount, 0);
  const first = await repository.createWorkout(program.id, { name: ' Séance A ', notes: ' À mon rythme ' });
  const second = await repository.createWorkout(program.id, { name: 'Séance B' });
  assert.equal(first.name, 'Séance A');
  assert.equal(first.notes, 'À mon rythme');
  assert.equal(second.notes, '');
  assert.deepEqual((await repository.listWorkouts(program.id)).map((workout) => workout.sortOrder), [0, 1]);
  assert.equal((await repository.getProgram(program.id)).workoutCount, 2);

  const editedProgram = await repository.updateProgram(program.id, { name: 'Mon nouveau nom', description: 'Quatre jours' });
  const editedWorkout = await repository.updateWorkout(first.id, { name: 'Séance du lundi', notes: 'Matin' });
  assert.equal(editedProgram.id, program.id);
  assert.equal(editedProgram.createdAt, program.createdAt);
  assert.notEqual(editedProgram.updatedAt, program.updatedAt);
  assert.equal(editedProgram.description, 'Quatre jours');
  assert.equal(editedWorkout.id, first.id);
  assert.equal(editedWorkout.createdAt, first.createdAt);
  assert.notEqual(editedWorkout.updatedAt, first.updatedAt);
  assert.equal(editedWorkout.programId, program.id);
  assert.equal(editedWorkout.sortOrder, first.sortOrder);
  assert.equal(editedWorkout.notes, 'Matin');
  assert.deepEqual((await repository.listWorkouts(program.id)).map((workout) => workout.name), ['Séance du lundi', 'Séance B']);
});

test('saved programs and edited workouts survive closing and reopening the database', async (t) => {
  const directory = mkdtempSync(join(tmpdir(), 'logbook-db-test-'));
  t.after(() => rmSync(directory, { recursive: true, force: true }));
  const filename = join(directory, 'logbook.sqlite');
  const { db, repository } = await fixture(filename);
  let originalClosed = false;
  t.after(() => { if (!originalClosed) db.close(); });
  const program = await repository.createProgram({ name: 'Programme personnel' });
  const workout = await repository.createWorkout(program.id, { name: 'Lundi' });
  const edited = await repository.updateWorkout(workout.id, { name: 'Mercredi', notes: 'Objectif personnel' });
  db.close();
  originalClosed = true;

  const reopened = new SQLiteTestAdapter(filename);
  t.after(() => reopened.close());
  await initializeDatabase(reopened);
  const reopenedRepository = new ProgramRepository(reopened, () => 'unused');
  assert.deepEqual(await reopenedRepository.getWorkout(workout.id), edited);
  assert.deepEqual(await reopenedRepository.listPrograms(), [{ ...program, workoutCount: 1 }]);
  assert.equal((await reopened.getFirstAsync<{ foreign_keys: number }>('PRAGMA foreign_keys'))?.foreign_keys, 1);
});

test('bound parameters preserve quotes and SQL-looking content without executing it', async (t) => {
  const { db, repository } = await fixture();
  t.after(() => db.close());
  const sqlLookingName = "L'entraînement'); DROP TABLE programs; --";
  const program = await repository.createProgram({ name: sqlLookingName, description: "'); DELETE FROM programs; --" });
  const workout = await repository.createWorkout(program.id, { name: sqlLookingName, notes: "' OR 1=1 --" });
  assert.equal((await repository.getProgram(program.id)).name, sqlLookingName);
  assert.equal((await repository.getWorkout(workout.id)).notes, "' OR 1=1 --");
  assert.equal((await repository.listPrograms()).length, 1);
  await assert.rejects(repository.getProgram("' OR 1=1 --"), NotFoundError);
  await assert.rejects(repository.getWorkout("' OR 1=1 --"), NotFoundError);
});

test('names are required and length limits reject invalid input without partial writes', async (t) => {
  const { db, repository } = await fixture();
  t.after(() => db.close());
  await assert.rejects(repository.createProgram({ name: '   ' }), ValidationError);
  await assert.rejects(repository.createProgram({ name: 'a'.repeat(81) }), ValidationError);
  await assert.rejects(repository.createProgram({ name: 'Valide', description: 'a'.repeat(1001) }), ValidationError);
  assert.deepEqual(await repository.listPrograms(), []);
  const program = await repository.createProgram({ name: 'a'.repeat(80), description: 'b'.repeat(1000) });
  await assert.rejects(repository.createWorkout(program.id, { name: '\n\t' }), ValidationError);
  await assert.rejects(repository.createWorkout(program.id, { name: 'a'.repeat(81) }), ValidationError);
  await assert.rejects(repository.createWorkout(program.id, { name: 'Valide', notes: 'a'.repeat(1001) }), ValidationError);
  const workout = await repository.createWorkout(program.id, { name: 'a'.repeat(80), notes: 'b'.repeat(1000) });
  await assert.rejects(repository.updateProgram(program.id, { name: '' }), ValidationError);
  await assert.rejects(repository.updateWorkout(workout.id, { name: 'Valide', notes: 'a'.repeat(1001) }), ValidationError);
  assert.deepEqual(await repository.getProgram(program.id), { ...program, workoutCount: 1 });
  assert.deepEqual(await repository.getWorkout(workout.id), workout);
});

test('missing parent programs and missing records fail clearly', async (t) => {
  const { db, repository } = await fixture();
  t.after(() => db.close());
  await assert.rejects(repository.getProgram('missing'), NotFoundError);
  await assert.rejects(repository.updateProgram('missing', { name: 'Nom' }), NotFoundError);
  await assert.rejects(repository.listWorkouts('missing'), NotFoundError);
  await assert.rejects(repository.createWorkout('missing', { name: 'Séance' }), NotFoundError);
  await assert.rejects(repository.getWorkout('missing'), NotFoundError);
  await assert.rejects(repository.updateWorkout('missing', { name: 'Séance' }), NotFoundError);
  assert.deepEqual(await repository.listPrograms(), []);
  assert.deepEqual(await db.getAllAsync('SELECT * FROM workout_templates'), []);
});

test('database foreign keys reject orphan workouts independently of repository validation', async (t) => {
  const { db } = await fixture();
  t.after(() => db.close());
  await assert.rejects(db.runAsync(
    `INSERT INTO workout_templates (id, program_id, name, notes, sort_order, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, ?)`,
    'orphan', 'absent', 'Séance', '', 0, '2026-10-14T00:00:00Z', '2026-10-14T00:00:00Z',
  ), /FOREIGN KEY/);
});

test('deleting a program cascades only its planned workouts and preserves other records', async (t) => {
  const { db, repository } = await fixture();
  t.after(() => db.close());
  const removed = await repository.createProgram({ name: 'À supprimer' });
  const kept = await repository.createProgram({ name: 'À conserver', description: 'Personnel' });
  const first = await repository.createWorkout(removed.id, { name: 'A' });
  const second = await repository.createWorkout(removed.id, { name: 'B' });
  const keptWorkout = await repository.createWorkout(kept.id, { name: 'Intacte', notes: 'À conserver' });
  const keptProgram = await repository.getProgram(kept.id);

  await repository.deleteProgram(removed.id);
  await assert.rejects(repository.getProgram(removed.id), NotFoundError);
  await assert.rejects(repository.getWorkout(first.id), NotFoundError);
  await assert.rejects(repository.getWorkout(second.id), NotFoundError);
  assert.deepEqual(await repository.listPrograms(), [keptProgram]);
  assert.deepEqual(await repository.listWorkouts(kept.id), [keptWorkout]);
  assert.deepEqual(await db.getAllAsync('PRAGMA foreign_key_check'), []);
  assert.equal((await db.getFirstAsync<{ user_version: number }>('PRAGMA user_version'))?.user_version, DATABASE_VERSION);
});

test('deleting a middle workout preserves sibling identities, notes, timestamps and order', async (t) => {
  const { db, repository } = await fixture();
  t.after(() => db.close());
  const program = await repository.createProgram({ name: 'Trois séances' });
  const other = await repository.createProgram({ name: 'Autre programme' });
  const first = await repository.createWorkout(program.id, { name: 'A', notes: 'Première' });
  const middle = await repository.createWorkout(program.id, { name: 'B' });
  const last = await repository.createWorkout(program.id, { name: 'C', notes: 'Dernière' });
  const independent = await repository.createWorkout(other.id, { name: 'Indépendante' });
  const otherBefore = await repository.getProgram(other.id);

  await repository.deleteWorkout(middle.id);
  assert.deepEqual(await repository.listWorkouts(program.id), [first, last]);
  assert.deepEqual(await repository.getProgram(program.id), { ...program, workoutCount: 2 });
  assert.deepEqual(await repository.getProgram(other.id), otherBefore);
  assert.deepEqual(await repository.getWorkout(independent.id), independent);
  const appended = await repository.createWorkout(program.id, { name: 'D' });
  assert.equal(appended.sortOrder, 3);
  assert.deepEqual(await repository.listWorkouts(program.id), [first, last, appended]);

  await repository.deleteWorkout(first.id);
  await repository.deleteWorkout(last.id);
  await repository.deleteWorkout(appended.id);
  assert.deepEqual(await repository.listWorkouts(program.id), []);
  assert.equal((await repository.getProgram(program.id)).workoutCount, 0);
  assert.deepEqual(await repository.getWorkout(independent.id), independent);
});

test('missing, repeated and SQL-looking delete identifiers never remove unrelated data', async (t) => {
  const { db, repository } = await fixture();
  t.after(() => db.close());
  const program = await repository.createProgram({ name: 'Intact' });
  const workout = await repository.createWorkout(program.id, { name: 'Intacte' });
  await assert.rejects(repository.deleteProgram("' OR 1=1 --"), NotFoundError);
  await assert.rejects(repository.deleteWorkout("' OR 1=1 --"), NotFoundError);
  await assert.rejects(repository.deleteProgram('missing'), NotFoundError);
  await assert.rejects(repository.deleteWorkout('missing'), NotFoundError);
  assert.deepEqual(await repository.getWorkout(workout.id), workout);
  assert.deepEqual(await repository.getProgram(program.id), { ...program, workoutCount: 1 });

  await repository.deleteWorkout(workout.id);
  await assert.rejects(repository.deleteWorkout(workout.id), NotFoundError);
  assert.deepEqual(await repository.getProgram(program.id), program);
  await repository.deleteProgram(program.id);
  await assert.rejects(repository.deleteProgram(program.id), NotFoundError);
  assert.deepEqual(await repository.listPrograms(), []);
});

test('a SQLite failure rolls back both the program deletion and its cascading children', async (t) => {
  const { db, repository } = await fixture();
  t.after(() => db.close());
  const program = await repository.createProgram({ name: 'Conserver si erreur' });
  const first = await repository.createWorkout(program.id, { name: 'A' });
  const second = await repository.createWorkout(program.id, { name: 'B' });
  await db.execAsync(`CREATE TRIGGER reject_workout_deletion BEFORE DELETE ON workout_templates
    WHEN OLD.sort_order = 1 BEGIN SELECT RAISE(ABORT, 'simulated storage failure'); END;`);
  await assert.rejects(repository.deleteProgram(program.id), /simulated storage failure/);
  assert.deepEqual(await repository.getProgram(program.id), { ...program, workoutCount: 2 });
  assert.deepEqual(await repository.listWorkouts(program.id), [first, second]);
  await assert.rejects(repository.deleteWorkout(second.id), /simulated storage failure/);
  assert.deepEqual(await repository.listWorkouts(program.id), [first, second]);
});

test('deletions persist across database closure without changing retained preparations', async (t) => {
  const directory = mkdtempSync(join(tmpdir(), 'logbook-delete-'));
  t.after(() => rmSync(directory, { recursive: true, force: true }));
  const filename = join(directory, 'logbook.db');
  const first = await fixture(filename);
  const program = await first.repository.createProgram({ name: 'Programme restant' });
  const removedProgram = await first.repository.createProgram({ name: 'Programme supprimé' });
  const kept = await first.repository.createWorkout(program.id, { name: 'Restante', notes: 'Notes' });
  const removed = await first.repository.createWorkout(program.id, { name: 'Supprimée' });
  await first.repository.createWorkout(removedProgram.id, { name: 'Cascade' });
  await first.repository.deleteProgram(removedProgram.id);
  await first.repository.deleteWorkout(removed.id);
  first.db.close();

  const reopened = await fixture(filename);
  t.after(() => reopened.db.close());
  assert.deepEqual(await reopened.repository.listPrograms(), [{ ...program, workoutCount: 1 }]);
  assert.deepEqual(await reopened.repository.listWorkouts(program.id), [kept]);
  await assert.rejects(reopened.repository.getWorkout(removed.id), NotFoundError);
  await assert.rejects(reopened.repository.getProgram(removedProgram.id), NotFoundError);
});

test('concurrent workout creations use distinct stable positions within each program', async (t) => {
  const { db, repository } = await fixture();
  t.after(() => db.close());
  const firstProgram = await repository.createProgram({ name: 'Premier' });
  const secondProgram = await repository.createProgram({ name: 'Second' });
  await Promise.all(Array.from({ length: 12 }, (_, index) =>
    repository.createWorkout(firstProgram.id, { name: `Séance ${index + 1}` }),
  ));
  const independent = await repository.createWorkout(secondProgram.id, { name: 'Séance indépendante' });
  assert.equal(independent.sortOrder, 0);
  const workouts = await repository.listWorkouts(firstProgram.id);
  assert.deepEqual(workouts.map((workout) => workout.sortOrder), Array.from({ length: 12 }, (_, index) => index));
  assert.equal(new Set(workouts.map((workout) => workout.id)).size, 12);
  assert.equal((await repository.getProgram(firstProgram.id)).workoutCount, 12);
  assert.equal((await repository.getProgram(secondProgram.id)).workoutCount, 1);
});

test('program list has stable ordering and puts a newly edited program first', async (t) => {
  const { db, repository } = await fixture();
  t.after(() => db.close());
  const first = await repository.createProgram({ name: 'Premier' });
  const second = await repository.createProgram({ name: 'Second' });
  assert.deepEqual((await repository.listPrograms()).map((program) => program.id), [second.id, first.id]);
  await repository.updateProgram(first.id, { name: 'Premier modifié' });
  assert.deepEqual((await repository.listPrograms()).map((program) => program.id), [first.id, second.id]);
});

test('re-running the versioned migration preserves existing user data', async (t) => {
  const { db, repository } = await fixture();
  t.after(() => db.close());
  const program = await repository.createProgram({ name: 'À conserver', description: 'Personnel' });
  const workout = await repository.createWorkout(program.id, { name: 'À conserver aussi', notes: 'Notes' });
  await initializeDatabase(db);
  await initializeDatabase(db);
  assert.deepEqual(await repository.getProgram(program.id), { ...program, workoutCount: 1 });
  assert.deepEqual(await repository.getWorkout(workout.id), workout);
});

test('a migration failure rolls back schema changes and keeps the version unchanged', async (t) => {
  const db = new SQLiteTestAdapter();
  t.after(() => db.close());
  await db.execAsync('CREATE TABLE workout_templates (existing TEXT);');
  await assert.rejects(initializeDatabase(db), /already exists/);
  assert.equal((await db.getFirstAsync<{ user_version: number }>('PRAGMA user_version'))?.user_version, 0);
  assert.equal(await db.getFirstAsync("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'programs'"), null);
  assert.notEqual(await db.getFirstAsync("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'workout_templates'"), null);
});

test('a newer database version fails safely without deleting or downgrading user data', async (t) => {
  const { db, repository } = await fixture();
  t.after(() => db.close());
  const program = await repository.createProgram({ name: 'Données futures' });
  await db.execAsync('PRAGMA user_version = 99;');
  await assert.rejects(initializeDatabase(db), /version plus récente/);
  assert.equal((await db.getFirstAsync<{ user_version: number }>('PRAGMA user_version'))?.user_version, 99);
  assert.deepEqual(await repository.getProgram(program.id), program);
});
