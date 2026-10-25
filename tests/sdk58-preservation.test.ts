import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { test } from 'node:test';
import { writePersonalExport } from '../src/data/personalExport';
import { INITIAL_EXERCISES } from '../src/db/exerciseCatalog';
import { DATABASE_VERSION, initializeDatabase } from '../src/db/migrations';
import { ProgramRepository } from '../src/db/repository';
import { SessionRepository } from '../src/db/sessionRepository';
import { TrainingRepository } from '../src/db/trainingRepository';
import { selectSessionStep } from '../src/domain/session';
import { SqliteDatabase } from './helpers/SqliteDatabase';

// Uses an on-disk fixture only. Never opens the developer's or phone's database.
test('SDK upgrade reopens populated v8 without changing schema, personal rows, active rest or export', async t => {
  const directory = mkdtempSync(join(tmpdir(), 'logbook-sdk58-'));
  const path = join(directory, 'logbook.db');
  const original = new SqliteDatabase(path);
  let originalClosed = false;
  let reopened: SqliteDatabase | undefined;
  // Close both handles before removing the fixture, including on Windows.
  t.after(() => { reopened?.close(); if (!originalClosed) original.close(); rmSync(directory, { recursive: true, force: true }); });
  await initializeDatabase(original);
  let serial = 0, time = Date.parse('2026-10-25T10:00:00Z');
  const id = () => `upgrade-${++serial}`, now = () => new Date(time += 1000).toISOString();
  const programs = new ProgramRepository(original, id, now);
  const training = new TrainingRepository(original, id, now);
  const sessions = new SessionRepository(original, id, now);
  const program = await programs.createProgram({ name: 'Programme conservé' });
  const workout = await programs.createWorkout(program.id, { name: 'Séance conservée' });
  const exercise = await training.addWorkoutExercise(workout.id, { exerciseId: INITIAL_EXERCISES[0]!.id });
  await training.createSet(exercise.id, { kind: 'work', repsMin: 8, repsMax: 10, targetWeightKg: 50, targetRir: 2, restAfterSec: 60 });
  let completed = await sessions.startOrResume(workout.id);
  completed = await sessions.validateSet(completed.id, completed.sets[0]!.id, { weightKg: 50, reps: 9, rir: 2 });
  for (let guard = 0; selectSessionStep(completed).phase !== 'ready_to_finish'; guard++) {
    assert.ok(guard < 5);
    const step = selectSessionStep(completed);
    if (step.phase === 'rest') completed = await sessions.completeRest(completed.id, step.rest.id);
    else if (step.phase === 'between_sets') completed = await sessions.advanceAfterSet(completed.id, step.performed.id);
    else assert.fail(`Unexpected fixture phase ${step.phase}`);
  }
  completed = await sessions.finishSession(completed.id);
  // Add a second set: the following session must resume into its paused rest.
  await training.createSet(exercise.id, { kind: 'work', repsMin: 8, repsMax: 10, targetWeightKg: 50, targetRir: 2, restAfterSec: 60 });
  let active = await sessions.startOrResume(workout.id);
  active = await sessions.validateSet(active.id, active.sets[0]!.id, { weightKg: 52, reps: 8, rir: 1 });
  active = await sessions.pauseRest(active.id, active.rests[0]!.id);
  await original.runAsync('INSERT INTO app_preferences (key, value_json, updated_at) VALUES (?, ?, ?)', 'upgrade-preservation', '{"enabled":true}', now());

  async function snapshot(db: SqliteDatabase) {
    const schema = await db.getAllAsync<{ name: string; type: string; sql: string | null }>(
      "SELECT name, type, sql FROM sqlite_master WHERE name NOT GLOB 'sqlite_*' ORDER BY name");
    const rows = Object.fromEntries(await Promise.all(schema.filter(item => item.type === 'table').map(async item =>
      [item.name, await db.getAllAsync(`SELECT rowid, * FROM ${item.name} ORDER BY rowid`)])));
    let exported = '';
    const reader = new SqliteDatabase(path);
    try {
      await writePersonalExport(reader, chunk => { exported += chunk; }, { appVersion: '0.1.0', createdAt: '2026-10-25T12:00:00Z' });
    } finally { reader.close(); }
    return { schema, rows, exported: JSON.parse(exported) };
  }
  const before = await snapshot(original);
  original.close(); originalClosed = true;
  reopened = new SqliteDatabase(path);
  await initializeDatabase(reopened);
  const restored = new SessionRepository(reopened, id, now);
  assert.equal(DATABASE_VERSION, 8);
  assert.deepEqual(await reopened.getFirstAsync('PRAGMA user_version'), { user_version: 8 });
  assert.deepEqual(await restored.getActiveSession(), active);
  assert.deepEqual(await restored.startOrResume(workout.id), active);
  assert.deepEqual(await restored.getSession(completed.id), completed);
  assert.equal((await restored.listCompletedSessions()).length, 1);
  assert.deepEqual(await snapshot(reopened), before);
});
