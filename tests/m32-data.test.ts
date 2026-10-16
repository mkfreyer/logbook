import assert from 'node:assert/strict';
import { readFileSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { test } from 'node:test';
import { DATABASE_VERSION, initializeDatabase } from '../src/db/migrations';
import { ProgramRepository } from '../src/db/repository';
import { SessionRepository } from '../src/db/sessionRepository';
import { TrainingRepository } from '../src/db/trainingRepository';
import { localDayKey, localWeek } from '../src/domain/activity';
import { selectSessionStep, type ActualSetInput, type WorkoutSession } from '../src/domain/session';
import { SqliteDatabase } from './helpers/SqliteDatabase';

async function fixture(path = ':memory:') {
  const db = new SqliteDatabase(path); await db.execAsync(readFileSync(new URL('./fixtures/m2-v4.sql', import.meta.url), 'utf8'));
  await initializeDatabase(db);
  let serial = 0, clock = Date.parse('2026-10-15T12:00:00.000Z');
  const id = () => `m32-${++serial}`, now = () => new Date(clock).toISOString();
  const programs = new ProgramRepository(db, id, now), training = new TrainingRepository(db, id, now), sessions = new SessionRepository(db, id, now);
  const program = await programs.createProgram({ name: 'Mon programme' }), workout = await programs.createWorkout(program.id, { name: 'Ma séance' });
  const exercise = await training.createCustomExercise({ name: 'Barre', muscleGroup: 'Pectoraux', equipment: 'Barre', weightMode: 'total' });
  const planned = await training.addWorkoutExercise(workout.id, { exerciseId: exercise.id });
  const templates = [];
  for (const kind of ['warmup', 'work', 'top_set'] as const) templates.push(await training.createSet(planned.id, { kind, repsMin: 99, repsMax: 99, targetWeightKg: 999, restAfterSec: 0 }));
  const values = [{ weightKg: 20, reps: 15, rir: null }, { weightKg: 60, reps: 10, rir: 2 }, { weightKg: 70, reps: 5, rir: 0 }];
  const setTime = (date: string) => { clock = Date.parse(date); };
  async function complete(finishedAt: string, actuals: ActualSetInput[] = values, workoutId = workout.id) {
    setTime(new Date(Date.parse(finishedAt) - 1000).toISOString());
    let session = await sessions.startOrResume(workoutId), index = 0;
    while (selectSessionStep(session).phase !== 'ready_to_finish') {
      const step = selectSessionStep(session);
      if (step.phase === 'set') session = await sessions.validateSet(session.id, step.set.id, actuals[index++ % actuals.length]!);
      else if (step.phase === 'between_sets') session = await sessions.advanceAfterSet(session.id, step.performed.id);
      else if (step.phase === 'rest') session = await sessions.completeRest(session.id, step.rest.id);
      else throw new Error('Unexpected phase');
    }
    setTime(finishedAt); return sessions.finishSession(session.id);
  }
  async function start() { setTime('2026-10-20T12:00:00.000Z'); return sessions.startOrResume(workout.id); }
  const previous = (session: WorkoutSession, index = 1) => sessions.history.previousPerformance(session.id, session.sets[index]!.id);
  return { db, programs, training, sessions, program, workout, exercise, planned, templates, values, setTime, complete, start, previous };
}

test('a first use and an unfinished session cannot supply a previous performance', async t => {
  const f = await fixture(); t.after(() => f.db.close()); let active = await f.start();
  assert.equal(await f.previous(active), null);
  active = await f.sessions.validateSet(active.id, active.sets[0]!.id, f.values[0]!);
  assert.equal(await f.previous(active, 0), null); assert.equal(await f.previous(active), null);
});
test('previous work set is the exact type and position, across programs and after program deletion', async t => {
  const f = await fixture(); t.after(() => f.db.close());
  const completed = await f.complete('2026-10-15T12:00:00.000Z'); await f.programs.deleteProgram(f.program.id);
  const program = await f.programs.createProgram({ name: 'Autre programme' });
  const workout = await f.programs.createWorkout(program.id, { name: 'Autre séance' });
  const occurrence = await f.training.addWorkoutExercise(workout.id, { exerciseId: f.exercise.id });
  for (const kind of ['warmup', 'work'] as const) await f.training.createSet(occurrence.id, { kind, repsMin: 8, repsMax: 8, restAfterSec: 0 });
  f.setTime('2026-10-16T12:00:00.000Z'); const active = await f.sessions.startOrResume(workout.id);
  const previous = await f.previous(active);
  assert.equal(previous!.comparison, 'same_series'); assert.equal(previous!.performance.sessionId, completed.id);
  assert.equal(previous!.performance.weightKg, 60); assert.equal(previous!.performance.reps, 10); assert.equal(previous!.performance.rir, 2);
  assert.notEqual(previous!.performance.weightKg, active.sets[1]!.targets.targetWeightKg);
});
test('fallbacks distinguish same type at another position and another non-warmup type', async t => {
  const f = await fixture(); t.after(() => f.db.close()); await f.complete('2026-10-15T12:00:00.000Z');
  await f.training.createSet(f.planned.id, { kind: 'work', repsMin: 3, repsMax: 3, restAfterSec: 0 });
  await f.training.createSet(f.planned.id, { kind: 'custom', label: 'Finisher', repsMin: 3, repsMax: 3, restAfterSec: 0 });
  const active = await f.start(), sameType = await f.previous(active, 3), fallback = await f.previous(active, 4);
  assert.equal(sameType!.comparison, 'same_type'); assert.equal(sameType!.performance.weightKg, 60);
  assert.equal(fallback!.comparison, 'exercise'); assert.equal(fallback!.performance.kind, 'top_set'); assert.equal(fallback!.performance.weightKg, 70);
});
test('comparability takes priority over a more recent differently positioned or typed result', async t => {
  const f = await fixture(); t.after(() => f.db.close()); const first = await f.complete('2026-10-15T12:00:00.000Z');
  await f.training.updateSet(f.templates[1]!.id, { ...f.templates[1]!, kind: 'back_off' });
  await f.complete('2026-10-16T12:00:00.000Z', [{ weightKg: 100, reps: 2, rir: 1 }]);
  await f.training.updateSet(f.templates[1]!.id, { ...f.templates[1]!, kind: 'work' });
  const previous = await f.previous(await f.start());
  assert.equal(previous!.performance.sessionId, first.id); assert.equal(previous!.performance.weightKg, 60); assert.equal(previous!.comparison, 'same_series');
});
test('working sets never use warmups; warmups never pretend to be comparable to work', async t => {
  const f = await fixture(); t.after(() => f.db.close());
  await f.training.updateSet(f.templates[1]!.id, { ...f.templates[1]!, kind: 'warmup' });
  await f.training.updateSet(f.templates[2]!.id, { ...f.templates[2]!, kind: 'warmup' });
  await f.complete('2026-10-15T12:00:00.000Z');
  await f.training.updateSet(f.templates[1]!.id, { ...f.templates[1]!, kind: 'work' });
  const active = await f.start(); assert.equal(await f.previous(active), null);
  assert.equal((await f.previous(active, 0))!.performance.kind, 'warmup');
});
test('same catalog ID with a new load mode never reuses an incompatible result', async t => {
  const f = await fixture(); t.after(() => f.db.close()); await f.complete('2026-10-15T12:00:00.000Z');
  await f.training.updateCustomExercise(f.exercise.id, { ...f.exercise, weightMode: 'per_hand' });
  const active = await f.start(); assert.equal(await f.previous(active), null);
});
test('a temporary replacement uses its actual identity rather than the original bar exercise', async t => {
  const f = await fixture(); t.after(() => f.db.close()); await f.complete('2026-10-15T12:00:00.000Z');
  const alternate = await f.training.createCustomExercise({ name: 'Haltères', muscleGroup: 'Pectoraux', equipment: 'Haltères', weightMode: 'total' });
  let active = await f.start();
  active = await f.sessions.replaceExercise(active.id, active.exercises[0]!.id, alternate.id, active.sets[0]!.id);
  assert.equal(await f.previous(active), null);
  const completed = await f.complete('2026-10-20T12:01:00.000Z', [{ weightKg: 15, reps: 12, rir: 1 }]);
  active = await f.sessions.startOrResume(f.workout.id);
  assert.equal((await f.previous(active))!.performance.weightKg, 60);
  active = await f.sessions.replaceExercise(active.id, active.exercises[0]!.id, alternate.id, active.sets[0]!.id);
  assert.equal((await f.previous(active))!.performance.sessionId, completed.id);
  assert.equal((await f.previous(active))!.performance.weightKg, 15);
});
test('missing charge and RIR stay null; explicit zero is preserved', async t => {
  const f = await fixture(); t.after(() => f.db.close());
  await f.complete('2026-10-15T12:00:00.000Z', [{ weightKg: null, reps: 12, rir: null }, { weightKg: 0, reps: 8, rir: 0 }, { weightKg: null, reps: 10, rir: null }]);
  const active = await f.start(), work = await f.previous(active), top = await f.previous(active, 2);
  assert.equal(work!.performance.weightKg, 0); assert.equal(work!.performance.rir, 0);
  assert.equal(top!.performance.weightKg, null); assert.equal(top!.performance.rir, null);
});
test('renaming an exercise keeps its history key and old recorded labels', async t => {
  const f = await fixture(); t.after(() => f.db.close()); await f.complete('2026-10-15T12:00:00.000Z');
  const renamed = await f.training.updateCustomExercise(f.exercise.id, { ...f.exercise, name: 'Mon développé' });
  assert.equal(renamed.id, f.exercise.id); const previous = await f.previous(await f.start());
  assert.equal(previous!.performance.exerciseName, 'Barre'); assert.equal(previous!.performance.weightKg, 60);
});
test('weekly activity counts only local Monday–Sunday completions, including a midnight crossing', async t => {
  const old = process.env.TZ; process.env.TZ = 'Europe/Paris';
  const f = await fixture(); t.after(() => f.db.close());
  try {
    for (const time of ['2026-10-25T22:59:59.000Z', '2026-10-25T23:00:00.000Z', '2026-10-28T23:30:00.000Z', '2026-11-01T22:59:59.000Z', '2026-11-01T23:00:00.000Z']) await f.complete(time);
    const stats = await f.sessions.history.homeActivity(new Date('2026-10-29T10:00:00.000Z'));
    assert.equal(stats.sessionCount, 3); assert.equal(stats.totalCompleted, 5);
    assert.deepEqual(stats.days.map(day => day.count), [1, 0, 0, 1, 0, 0, 1]);
    assert.equal(stats.days[3]!.today, true);
  } finally { if (old === undefined) delete process.env.TZ; else process.env.TZ = old; }
});
test('empty and active-only weeks contain no completed sessions', async t => {
  const f = await fixture(); t.after(() => f.db.close()); await f.start();
  const stats = await f.sessions.history.homeActivity(new Date('2026-10-20T12:00:00.000Z'));
  assert.equal(stats.sessionCount, 0); assert.equal(stats.totalCompleted, 0); assert.equal(stats.days.length, 7);
  assert.ok(stats.days.every(day => day.count === 0));
});
test('week calendar handles DST and a timezone change without UTC day slicing', async t => {
  const old = process.env.TZ; const f = await fixture(); t.after(() => f.db.close());
  try {
    process.env.TZ = 'Europe/Paris';
    const spring = localWeek(new Date('2026-03-29T12:00:00.000Z')), autumn = localWeek(new Date('2026-10-25T12:00:00.000Z'));
    assert.equal((Date.parse(spring.until) - Date.parse(spring.from)) / 3600000, 167);
    assert.equal((Date.parse(autumn.until) - Date.parse(autumn.from)) / 3600000, 169);
    await f.complete('2026-10-25T23:30:00.000Z');
    const now = new Date('2026-10-26T12:00:00.000Z');
    assert.equal((await f.sessions.history.homeActivity(now)).sessionCount, 1);
    process.env.TZ = 'America/Los_Angeles';
    assert.equal((await f.sessions.history.homeActivity(now)).sessionCount, 0);
    assert.equal(localDayKey(new Date('2026-10-25T23:30:00.000Z')), '2026-10-25');
  } finally { if (old === undefined) delete process.env.TZ; else process.env.TZ = old; }
});
test('completion observers fire after a real finish only, never on validations or duplicate finish', async t => {
  const f = await fixture(); t.after(() => f.db.close()); let calls = 0;
  const unsubscribe = f.sessions.subscribeCompleted(() => { calls++; });
  const session = await f.complete('2026-10-15T12:00:00.000Z'); assert.equal(calls, 1);
  await f.sessions.finishSession(session.id); assert.equal(calls, 1);
  const active = await f.start(); await f.sessions.validateSet(active.id, active.sets[0]!.id, f.values[0]!);
  assert.equal(calls, 1); await assert.rejects(f.sessions.finishSession(active.id)); assert.equal(calls, 1); unsubscribe();
});
test('M3.1 SQLite rows survive readings, reopening, and a personalized reference update without history rewriting', async t => {
  const dir = mkdtempSync(join(tmpdir(), 'logbook-m32-')); t.after(() => rmSync(dir, { recursive: true, force: true }));
  const path = join(dir, 'logbook.db'), f = await fixture(path); const completed = await f.complete('2026-10-15T12:00:00.000Z'); const active = await f.start();
  const dump = async () => {
    const tables = await f.db.getAllAsync<{ name: string }>("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name");
    return Promise.all(tables.map(row => f.db.getAllAsync(`SELECT * FROM ${row.name} ORDER BY rowid`)));
  };
  const before = await dump(); await initializeDatabase(f.db); await f.previous(active); await f.sessions.history.homeActivity();
  assert.deepEqual(await dump(), before); assert.equal(DATABASE_VERSION, 7);
  const renamed = await f.training.updateCustomExercise(f.exercise.id, { ...f.exercise, name: 'Renommé après les réalisations' });
  assert.equal(renamed.id, f.exercise.id); f.db.close();
  const db = new SqliteDatabase(path); t.after(() => db.close()); await initializeDatabase(db);
  const sessions = new SessionRepository(db, () => 'unused');
  assert.deepEqual(await sessions.getSession(completed.id), completed); assert.deepEqual(await sessions.getActiveSession(), active);
  assert.equal((await sessions.history.previousPerformance(active.id, active.sets[1]!.id))!.performance.weightKg, 60);
  assert.deepEqual(await db.getAllAsync('PRAGMA foreign_key_check'), []);
});
