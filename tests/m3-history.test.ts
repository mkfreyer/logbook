import assert from 'node:assert/strict';
import { readFileSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { test } from 'node:test';
import { initializeDatabase, DATABASE_VERSION } from '../src/db/migrations';
import { ProgramRepository } from '../src/db/repository';
import { TrainingRepository } from '../src/db/trainingRepository';
import { SessionRepository } from '../src/db/sessionRepository';
import { historyRange, previousHistoryRange, representativeSet, type ExercisePerformance } from '../src/domain/history';
import { selectSessionStep, type ActualSetInput, type WorkoutSession } from '../src/domain/session';
import { chronologicalExerciseBlocks, summarizeSession } from '../src/domain/sessionSummary';
import { SqliteDatabase } from './helpers/SqliteDatabase';

const all = { until: '2030-01-01T00:00:00.000Z' };
async function fixture(path = ':memory:') {
  const db = new SqliteDatabase(path);
  await db.execAsync(readFileSync(new URL('./fixtures/m2-v4.sql', import.meta.url), 'utf8'));
  await initializeDatabase(db);
  let serial = 0, clock = Date.parse('2026-10-15T12:00:00.000Z');
  const id = () => `history-${String(++serial).padStart(6, '0')}`, now = () => new Date(clock).toISOString();
  const programs = new ProgramRepository(db, id, now), training = new TrainingRepository(db, id, now), sessions = new SessionRepository(db, id, now);
  const program = await programs.createProgram({ name: 'Mon programme' });
  const workout = await programs.createWorkout(program.id, { name: 'Haut du corps' });
  const exercise = await training.createCustomExercise({ name: 'Développé barre', muscleGroup: 'Pectoraux', equipment: 'Barre', weightMode: 'total' });
  const occurrence = await training.addWorkoutExercise(workout.id, { exerciseId: exercise.id });
  for (const kind of ['warmup', 'work', 'top_set'] as const) await training.createSet(occurrence.id,
    { kind, repsMin: 99, repsMax: 99, targetWeightKg: 999, targetRir: 9, restAfterSec: 60 });
  const setTime = (iso: string) => { clock = Date.parse(iso); }, advance = (ms: number) => { clock += ms; };
  const actuals: ActualSetInput[] = [{ weightKg: 20, reps: 10, rir: null }, { weightKg: 60, reps: 8, rir: 2 }, { weightKg: 60, reps: 10, rir: 0 }];
  async function complete(workoutId = workout.id, values = actuals) {
    let session = await sessions.startOrResume(workoutId), index = 0;
    while (true) {
      const step = selectSessionStep(session);
      if (step.phase === 'ready_to_finish') { advance(1000); return sessions.finishSession(session.id); }
      if (step.phase === 'set') { advance(1000); session = await sessions.validateSet(session.id, step.set.id, values[index++ % values.length]!); }
      else if (step.phase === 'rest') { advance(75000); session = await sessions.completeRest(session.id, step.rest.id); }
      else throw new Error(`Unexpected ${step.phase}`);
    }
  }
  return { db, programs, training, sessions, program, workout, exercise, occurrence, setTime, advance, complete, actuals };
}

test('empty actual history excludes plans and active sessions; no fictitious tonnage', async t => {
  const f = await fixture(); t.after(() => f.db.close());
  const empty = await f.sessions.history.overview(all);
  assert.deepEqual(empty.stats, { sessionCount: 0, durationMs: 0, performedSetCount: 0, loggedTonnageKg: null, chargedSetCount: 0, unchargedSetCount: 0 });
  assert.deepEqual(empty.sessions, []); assert.deepEqual(empty.points, []); assert.deepEqual(empty.programs, []);
  await f.sessions.startOrResume(f.workout.id);
  assert.equal((await f.sessions.history.overview(all)).stats.sessionCount, 0);
  assert.deepEqual(await f.sessions.history.exercises(all), []);
});
test('SQL overview matches M2 summaries for real durations, results and tonnage, never programmed targets', async t => {
  const f = await fixture(); t.after(() => f.db.close());
  const a = await f.complete(); f.setTime('2026-10-16T12:00:00.000Z'); const b = await f.complete();
  const summary = summarizeSession(a), history = await f.sessions.history.overview(all);
  assert.equal(history.stats.sessionCount, 2); assert.equal(history.stats.performedSetCount, 6);
  assert.equal(history.stats.loggedTonnageKg, summary.loggedTonnageKg! * 2);
  assert.equal(history.stats.durationMs, summary.durationMs * 2); assert.deepEqual(history.sessions.map(row => row.id), [b.id, a.id]);
  assert.deepEqual(history.points.map(row => row.id), [a.id, b.id]);
  assert.equal(summarizeSession(b).meanRir, 1);
});
test('same-name programs stay separate by source ID; deleted plans retain all history and snapshots', async t => {
  const f = await fixture(); t.after(() => f.db.close()); const first = await f.complete();
  const p2 = await f.programs.createProgram({ name: 'Mon programme' });
  const w2 = await f.programs.createWorkout(p2.id, { name: 'Haut du corps' });
  const e2 = await f.training.addWorkoutExercise(w2.id, { exerciseId: f.exercise.id });
  await f.training.createSet(e2.id, { kind: 'work', repsMin: 3, repsMax: 3, restAfterSec: 0 });
  await f.complete(w2.id); await f.programs.deleteProgram(f.program.id);
  const overview = await f.sessions.history.overview(all);
  assert.equal(overview.programs.length, 2); assert.equal(new Set(overview.programs.map(p => p.id)).size, 2);
  const deleted = await f.sessions.history.overview({ ...all, programId: f.program.id });
  assert.equal(deleted.programs[0]!.deleted, 1); assert.equal(deleted.stats.sessionCount, 1);
  assert.equal(deleted.sessions[0]!.id, first.id); assert.equal((await f.sessions.getSession(first.id))!.programName, 'Mon programme');
  assert.equal((await f.sessions.history.exercise(f.exercise.id, all)).sessionCount, 2);
});
test('period boundaries are inclusive/exclusive at ISO timestamps; previous period is independently filtered', async t => {
  const f = await fixture(); t.after(() => f.db.close()); const first = await f.complete();
  f.setTime('2026-10-16T12:00:00.000Z'); const second = await f.complete();
  const boundary = second.finishedAt!;
  const before = await f.sessions.history.overview({ until: boundary });
  assert.deepEqual(before.sessions.map(row => row.id), [first.id]);
  const after = await f.sessions.history.overview({ from: boundary, until: all.until }, 0, { until: boundary });
  assert.deepEqual(after.sessions.map(row => row.id), [second.id]); assert.equal(after.previous!.sessionCount, 1);
});
test('missing loads and RIR remain null; explicit zero is a recorded value', async t => {
  const f = await fixture(); t.after(() => f.db.close());
  await f.complete(f.workout.id, [{ weightKg: null, reps: 10, rir: null }]);
  let overview = await f.sessions.history.overview(all);
  assert.equal(overview.stats.loggedTonnageKg, null); assert.equal(overview.stats.unchargedSetCount, 3);
  const exercise = await f.sessions.history.exercise(f.exercise.id, all);
  assert.equal(exercise.points[0]!.representative!.weightKg, null); assert.equal(exercise.points[0]!.loggedTonnageKg, null);
  assert.equal(exercise.visits[0]!.performances[0]!.rir, null);
  await f.complete(f.workout.id, [{ weightKg: 0, reps: 10, rir: 0 }]);
  overview = await f.sessions.history.overview(all);
  assert.equal(overview.stats.loggedTonnageKg, 0); assert.equal(overview.stats.chargedSetCount, 3);
});
test('representative set excludes warmups, ties by reps, keeps actual correlated kg/reps', async t => {
  const f = await fixture(); t.after(() => f.db.close());
  await f.complete(f.workout.id, [{ weightKg: 200, reps: 20, rir: null }, { weightKg: 80, reps: 4, rir: 1 }, { weightKg: 70, reps: 12, rir: 0 }]);
  const history = await f.sessions.history.exercise(f.exercise.id, all);
  assert.equal(history.points[0]!.representative!.weightKg, 80); assert.equal(history.points[0]!.representative!.reps, 4);
  assert.equal(history.points[0]!.loggedTonnageKg, 5160);
  assert.equal(history.lastPerformance!.weightKg, 70); assert.equal(history.lastPerformance!.reps, 12);
});
test('same catalog identity across programs/renames stays queryable; actual snapshots keep their historical names', async t => {
  const f = await fixture(); t.after(() => f.db.close()); await f.complete();
  await f.training.updateCustomExercise(f.exercise.id, { name: 'Mon développé renommé', muscleGroup: 'Pectoraux', equipment: 'Barre', weightMode: 'total' });
  f.setTime('2026-10-16T12:00:00.000Z'); await f.complete();
  const history = await f.sessions.history.exercise(f.exercise.id, all);
  assert.equal(history.sessionCount, 2); assert.equal(history.exercise!.name, 'Mon développé renommé');
  assert.equal(history.visits[1]!.performances[0]!.exerciseName, 'Développé barre');
  const index = await f.sessions.history.exercises(all);
  assert.equal(index.length, 1); assert.equal(index[0]!.name, 'Mon développé renommé'); assert.equal(index[0]!.sessionCount, 2);
});
test('different catalog IDs and captured load modes are never merged; per-hand tonnage counted once', async t => {
  const f = await fixture(); t.after(() => f.db.close()); await f.complete();
  await f.training.updateCustomExercise(f.exercise.id, { name: 'Développé barre', muscleGroup: 'Pectoraux', equipment: 'Barre', weightMode: 'per_hand' });
  f.setTime('2026-10-16T12:00:00.000Z'); await f.complete(f.workout.id, [{ weightKg: 20, reps: 10, rir: null }]);
  const recent = await f.sessions.history.exercise(f.exercise.id, all);
  assert.deepEqual(recent.modes, ['per_hand', 'total']); assert.equal(recent.mode, 'per_hand');
  assert.equal(recent.points[0]!.loggedTonnageKg, 600); assert.equal(recent.sessionCount, 1);
  const total = await f.sessions.history.exercise(f.exercise.id, all, 'total');
  assert.equal(total.points[0]!.loggedTonnageKg, 1280); assert.equal(total.visits.length, 1);
  const emptyModePeriod = await f.sessions.history.exercise(f.exercise.id, { from: '2026-10-15T00:00:00.000Z', until: '2026-10-16T00:00:00.000Z' }, 'per_hand');
  assert.equal(emptyModePeriod.mode, 'per_hand'); assert.equal(emptyModePeriod.sessionCount, 0);
  assert.deepEqual(emptyModePeriod.visits, []); assert.deepEqual(emptyModePeriod.points, []);
  assert.deepEqual(emptyModePeriod.modes, ['per_hand', 'total']);
  assert.equal((await f.sessions.history.exercise('different-id', all)).exercise, null);
});
test('two actually performed catalog exercises with the same name stay separate in the index and series queries', async t => {
  const f = await fixture(); t.after(() => f.db.close()); await f.complete();
  const other = await f.training.createCustomExercise({ name: f.exercise.name, muscleGroup: 'Pectoraux', equipment: 'Haltères', weightMode: 'per_hand' });
  const workout = await f.programs.createWorkout(f.program.id, { name: 'Autre séance' });
  const occurrence = await f.training.addWorkoutExercise(workout.id, { exerciseId: other.id });
  await f.training.createSet(occurrence.id, { kind: 'work', repsMin: 10, repsMax: 10, restAfterSec: 0 });
  await f.complete(workout.id, [{ weightKg: 12, reps: 10, rir: 3 }]);
  const index = await f.sessions.history.exercises(all); assert.equal(index.length, 2);
  assert.equal((await f.sessions.history.exercise(f.exercise.id, all)).visits[0]!.performances.length, 3);
  const alternate = await f.sessions.history.exercise(other.id, all);
  assert.equal(alternate.visits[0]!.performances.length, 1); assert.equal(alternate.points[0]!.loggedTonnageKg, 120);
});
test('a history snapshot shares the execution queue and cannot straddle a set commit', async t => {
  const f = await fixture(); t.after(() => f.db.close());
  const session = await f.sessions.startOrResume(f.workout.id), step = selectSessionStep(session);
  if (step.phase !== 'set') throw new Error('set');
  const original = f.db.getFirstAsync.bind(f.db);
  let release!: () => void, entered!: () => void;
  const blocked = new Promise<void>(resolve => { release = resolve; }), started = new Promise<void>(resolve => { entered = resolve; });
  let held = false;
  f.db.getFirstAsync = async <T>(sql: string, ...params: (string | number | null)[]) => {
    if (!held && sql.includes('WITH visits')) { held = true; entered(); await blocked; }
    return original<T>(sql, ...params);
  };
  const reading = f.sessions.history.overview(all); await started;
  const writing = f.sessions.validateSet(session.id, step.set.id, { weightKg: 40, reps: 8, rir: 2 });
  await new Promise(resolve => setImmediate(resolve));
  assert.equal((await original<{ count: number }>('SELECT COUNT(*) AS count FROM performed_sets'))!.count, 0);
  release(); assert.equal((await reading).stats.sessionCount, 0); await writing;
  assert.equal((await f.sessions.getSession(session.id))!.performances.length, 1);
});
test('partial replacement splits exact actual identities, preserves performed sets and the original program', async t => {
  const f = await fixture(); t.after(() => f.db.close());
  const replacement = await f.training.createCustomExercise({ name: 'Développé haltères', muscleGroup: 'Pectoraux', equipment: 'Haltères', weightMode: 'per_hand' });
  let session = await f.sessions.startOrResume(f.workout.id), step = selectSessionStep(session);
  assert.equal(step.phase, 'set'); if (step.phase !== 'set') return;
  session = await f.sessions.validateSet(session.id, step.set.id, { weightKg: 40, reps: 10, rir: 2 });
  f.advance(90000); session = await f.sessions.completeRest(session.id, session.rests[0]!.id);
  step = selectSessionStep(session); if (step.phase !== 'set') throw new Error('set');
  session = await f.sessions.replaceExercise(session.id, step.exercise.id, replacement.id, step.set.id);
  // Complete the already active, partially replaced execution.
  session = await f.complete(f.workout.id, [{ weightKg: 20, reps: 10, rir: 1 }]);
  const original = await f.sessions.history.exercise(f.exercise.id, all), actual = await f.sessions.history.exercise(replacement.id, all);
  assert.equal(original.visits[0]!.performances.length, 1); assert.equal(actual.visits[0]!.performances.length, 2);
  assert.equal(actual.points[0]!.loggedTonnageKg, 400);
  assert.equal((await f.training.listWorkoutExercises(f.workout.id))[0]!.exerciseId, f.exercise.id);
  const summary = summarizeSession(session); assert.equal(summary.exercises[1]!.replacedFrom!.sourceCatalogExerciseId, f.exercise.id);
});
test('history reads cannot alter actual results or rest pauses, and v4 initialization preserves every M2 row', async t => {
  const f = await fixture(); t.after(() => f.db.close()); const completed = await f.complete();
  let active = await f.sessions.startOrResume(f.workout.id);
  const step = selectSessionStep(active); if (step.phase !== 'set') throw new Error('set');
  active = await f.sessions.validateSet(active.id, step.set.id, { weightKg: 20, reps: 10, rir: null });
  f.advance(5000); active = await f.sessions.pauseRest(active.id, active.rests[0]!.id);
  const snapshot = async () => {
    const tables = (await f.db.getAllAsync<{ name: string }>("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")).map(row => row.name);
    return Promise.all(tables.map(table => f.db.getAllAsync(`SELECT * FROM ${table} ORDER BY rowid`)));
  };
  const before = await snapshot(); await initializeDatabase(f.db);
  await f.sessions.history.overview(all); await f.sessions.history.exercise(f.exercise.id, all); await f.sessions.history.exercises(all);
  assert.deepEqual(await snapshot(), before); assert.equal(DATABASE_VERSION, 8);
  assert.deepEqual(await f.sessions.getSession(completed.id), completed);
  assert.deepEqual(await f.sessions.getActiveSession(), active);
  assert.deepEqual(await f.db.getAllAsync('PRAGMA foreign_key_check'), []);
});
test('saved history reopens from disk after deleting the original program', async t => {
  const dir = mkdtempSync(join(tmpdir(), 'logbook-history-')); t.after(() => rmSync(dir, { recursive: true, force: true }));
  const file = join(dir, 'logbook.db'), f = await fixture(file), session = await f.complete();
  await f.programs.deleteProgram(f.program.id); f.db.close();
  const db = new SqliteDatabase(file); t.after(() => db.close()); await initializeDatabase(db);
  const repo = new SessionRepository(db, () => 'unused');
  assert.equal((await repo.history.overview(all)).sessions[0]!.id, session.id);
  assert.equal((await repo.history.exercise(f.exercise.id, all)).visits[0]!.performances.length, 3);
});
test('pages cover completed sessions without duplication and chart limit does not truncate totals', async t => {
  const f = await fixture(); t.after(() => f.db.close());
  for (let i = 0; i < 123; i++) { f.setTime(new Date(Date.UTC(2026, 0, i + 1, 12)).toISOString()); await f.complete(); }
  const first = await f.sessions.history.overview(all), allIds: string[] = [];
  assert.equal(first.points.length, 120); assert.equal(first.stats.sessionCount, 123); assert.equal(first.pageCount, 7);
  for (let page = 0; page < first.pageCount; page++) allIds.push(...(await f.sessions.history.overview(all, page)).sessions.map(row => row.id));
  assert.equal(allIds.length, 123); assert.equal(new Set(allIds).size, 123);
  const exercise = await f.sessions.history.exercise(f.exercise.id, all, 'total', 6);
  assert.equal(exercise.visits.length, 3); assert.equal(exercise.points.length, 120); assert.equal(exercise.sessionCount, 123);
  assert.equal((await f.sessions.history.overview(all, 999)).page, 6);
  await assert.rejects(f.sessions.history.overview(all, -1), /Page invalide/);
});
test('a real validation timeline can alternate exercises without regrouping earlier results out of order', () => {
  const a = { id: 'a' }, b = { id: 'b' };
  const summary = { exercises: [{ exercise: a, replacedFrom: null, performances: [{ performance: { sortOrder: 0 } }, { performance: { sortOrder: 2 } }] },
    { exercise: b, replacedFrom: null, performances: [{ performance: { sortOrder: 1 } }] }] } as unknown as ReturnType<typeof summarizeSession>;
  const blocks = chronologicalExerciseBlocks(summary);
  assert.deepEqual(blocks.map(block => block.exercise.id), ['a', 'b', 'a']);
  assert.deepEqual(blocks.flatMap(block => block.performances.map(row => row.performance.sortOrder)), [0, 1, 2]);
  assert.equal(summary.exercises[0]!.performances.length, 2);
});
test('work-set selection handles missing loads, zero, warmup-only and actual ordering ties', () => {
  const row = (id: string, weightKg: number | null, reps: number, kind = 'work', sortOrder = 0) => ({ id, weightKg, reps, kind, sortOrder }) as ExercisePerformance;
  assert.equal(representativeSet([row('warmup', 100, 20, 'warmup')]), null);
  assert.equal(representativeSet([row('a', null, 10), row('b', null, 12)])!.id, 'b');
  assert.equal(representativeSet([row('a', null, 99), row('b', 0, 1)])!.id, 'b');
  assert.equal(representativeSet([row('a', 40, 8, 'work', 3), row('b', 40, 8, 'top_set', 1)])!.id, 'b');
});
test('calendar periods honor local midnight, month/year boundaries and Paris DST changes', () => {
  const previousTZ = process.env.TZ; process.env.TZ = 'Europe/Paris';
  try {
    const range = historyRange('30', new Date('2026-03-29T22:30:00.000Z')); // March 30 locally
    assert.equal(range.from, '2026-02-28T23:00:00.000Z'); assert.equal(range.until, '2026-03-30T22:00:00.000Z');
    assert.notEqual(Date.parse(range.until) - Date.parse(range.from!), 30 * 86400000);
    const fall = historyRange('30', new Date('2026-10-25T23:30:00.000Z'));
    assert.equal(fall.until, '2026-10-26T23:00:00.000Z');
    const year = historyRange('365', new Date('2027-01-01T01:00:00.000Z'));
    assert.equal(new Date(year.from!).getFullYear(), 2026);
    const earlier = previousHistoryRange('30', new Date('2026-03-29T22:30:00.000Z'))!;
    assert.equal(earlier.until, range.from); assert.equal(previousHistoryRange('all'), null);
  } finally { if (previousTZ === undefined) delete process.env.TZ; else process.env.TZ = previousTZ; }
});
