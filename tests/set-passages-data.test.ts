import assert from 'node:assert/strict';
import { readFileSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { test } from 'node:test';
import { initializeDatabase, DATABASE_VERSION } from '../src/db/migrations';
import { ProgramRepository } from '../src/db/repository';
import { TrainingRepository } from '../src/db/trainingRepository';
import { SessionRepository } from '../src/db/sessionRepository';
import type { Database } from '../src/db/types';
import { remainingSessionSets, remainingSessionExercises, selectSessionStep, sessionProgress, sessionProgressLabel, type WorkoutSession } from '../src/domain/session';
import { summarizeSession } from '../src/domain/sessionSummary';
import { EXPORT_TABLES, writePersonalExport } from '../src/data/personalExport';
import { SqliteDatabase } from './helpers/SqliteDatabase';

async function fixture(t: { after(fn: () => void): void }, rest = 60) {
  const dir = mkdtempSync(join(tmpdir(), 'logbook-passages-')), path = join(dir, 'logbook.db'), db = new SqliteDatabase(path);
  t.after(() => { db.close(); rmSync(dir, { recursive: true, force: true }); }); await initializeDatabase(db);
  let serial = 0, clock = Date.parse('2026-10-17T10:00:00Z');
  const id = () => `passage-${++serial}`, now = () => new Date(clock += 1000).toISOString();
  const programs = new ProgramRepository(db, id, now), training = new TrainingRepository(db, id, now), sessions = new SessionRepository(db, id, now);
  const program = await programs.createProgram({ name: 'Carnet de test' }), workout = await programs.createWorkout(program.id, { name: 'Séance' });
  const catalog = await training.createCustomExercise({ name: 'Barre', muscleGroup: 'Dos', equipment: 'Barre', weightMode: 'total' });
  const ex = await training.addWorkoutExercise(workout.id, { exerciseId: catalog.id });
  const input = { kind: 'top_set' as const, label: 'Top', repsMin: 8, repsMax: 10, targetWeightKg: 100, targetRir: 2, restAfterSec: rest, notes: 'Consigne' };
  const top = await training.createSet(ex.id, input);
  await training.createSet(ex.id, { ...input, kind: 'back_off', label: 'Back', loadRule: { basis: 'performed_weight', referenceSetId: top.id, percent: 90 } });
  await training.createSet(ex.id, { ...input, kind: 'warmup', label: 'Chauffe', loadRule: { basis: 'planned_target', referenceSetId: top.id, percent: 50 } });
  const other = await training.addWorkoutExercise(workout.id, { exerciseId: (await training.listCatalog()).find(e => e.id !== catalog.id)!.id });
  await training.createSet(other.id, { ...input, kind: 'work', targetWeightKg: null });
  const session = await sessions.startOrResume(workout.id);
  return { db, path, id, now, programs, training, sessions, program, workout, ex, top, input, session };
}
async function snapshot(db: SqliteDatabase, names?: string[]) {
  const tables = names ?? (await db.getAllAsync<{ name: string }>("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")).map(t => t.name);
  return Object.fromEntries(await Promise.all(tables.map(async name => [name, await db.getAllAsync(`SELECT rowid AS __rowid, * FROM ${name} ORDER BY rowid`)])));
}
const preparation = (db: SqliteDatabase) => snapshot(db, ['programs', 'workout_templates', 'workout_exercises', 'exercise_catalog', 'set_templates', 'set_load_rules', 'set_actual_load_rules', 'app_preferences']);
const actual = { weightKg: 95, reps: 10, rir: 0 };

test('skipping a planned series changes only execution status, not goals, program, performance or rest', async t => {
  const f = await fixture(t), before = await preparation(f.db), first = f.session.sets[0]!;
  const s = await f.sessions.skipSet(f.session.id, first.id, 0);
  assert.ok(s.sets[0]!.skippedAt); assert.deepEqual(s.sets[0]!.targets, first.targets); assert.deepEqual(s.sets[0]!.originalTargets, first.originalTargets);
  assert.deepEqual(s.performances, []); assert.deepEqual(s.rests, []); assert.deepEqual(await preparation(f.db), before);
  assert.equal(remainingSessionSets(s).length, 3); assert.equal(selectSessionStep(s).phase, 'set');
  assert.deepEqual(sessionProgress(s), { performed: 0, skipped: 1, remaining: 3, total: 4 });
});
for (const scope of ['session', 'program'] as const) test(`an added ${scope} series can be skipped without changing its source model`, async t => {
  const f = await fixture(t); let s = await f.sessions.addSet(f.session.id, f.session.exercises[0]!.id, f.input, scope, scope);
  const extra = s.sets.find(item => item.addition)!, before = await preparation(f.db);
  s = await f.sessions.skipSet(s.id, extra.id, 0); assert.ok(s.sets.find(item => item.id === extra.id)!.skippedAt);
  assert.equal(s.sets.length, 5); assert.deepEqual(await preparation(f.db), before);
});
test('reintegration preserves adjusted targets, name, type, notes, frozen goals and rule provenance', async t => {
  const f = await fixture(t), id = f.session.sets[1]!.id;
  let s = await f.sessions.updateSet(f.session.id, id, { ...f.input, kind: 'custom', label: 'Libre', repsMin: 6, repsMax: 9, targetWeightKg: 82.5, targetRir: null, restAfterSec: 123, notes: 'Ajustement légitime' }, 'session');
  const before = s.sets.find(item => item.id === id)!;
  s = await f.sessions.skipSet(s.id, id, 0); s = await f.sessions.reintegrateSet(s.id, id, 1);
  const { passageRevision, ...restored } = s.sets.find(item => item.id === id)!;
  assert.equal(passageRevision, 2); assert.deepEqual(restored, before); assert.ok(remainingSessionSets(s).some(item => item.id === id));
});
test('a reintegrated reference is manually performed and resolves the actual-dependent target normally', async t => {
  const f = await fixture(t), first = f.session.sets[0]!;
  let s = await f.sessions.skipSet(f.session.id, first.id, 0);
  assert.equal(s.sets[1]!.targets.targetWeightKg, null); assert.equal(s.sets[2]!.targets.targetWeightKg, 50);
  await assert.rejects(f.sessions.validateSet(s.id, first.id, actual, s.sets.find(item => item.id === first.id)?.passageRevision ?? 0), /Réintégrer la série/);
  s = await f.sessions.reintegrateSet(s.id, first.id, 1); const step = selectSessionStep(s);
  assert.equal(step.phase, 'set'); if (step.phase !== 'set') throw new Error('set'); assert.equal(step.set.id, first.id);
  s = await f.sessions.validateSet(s.id, first.id, actual, s.sets.find(item => item.id === first.id)?.passageRevision ?? 0); assert.equal(s.sets[1]!.targets.targetWeightKg, 85.5);
  assert.deepEqual(s.performances.map(p => p.weightKg), [95]);
});
test('a performed series cannot be skipped or reintegrated and SQLite refuses performance insertion on a skipped set', async t => {
  const f = await fixture(t); let s = await f.sessions.validateSet(f.session.id, f.session.sets[0]!.id, actual);
  const before = structuredClone(s.performances), next = s.sets[1]!;
  await assert.rejects(f.sessions.skipSet(s.id, s.sets[0]!.id, 0), /déjà réalisée/);
  await assert.rejects(f.sessions.reintegrateSet(s.id, s.sets[0]!.id, 0), /déjà réalisée/);
  s = await f.sessions.skipSet(s.id, next.id, 0);
  await assert.rejects(f.db.runAsync(`INSERT INTO performed_sets (id,session_id,session_set_id,sort_order,weight_kg,reps,rir,performed_at,advanced_at) VALUES ('forbidden',?,?,50,50,8,0,?,?)`, s.id, next.id, f.now(), f.now()), /Reintegrate/);
  assert.deepEqual(s.performances, before);
});
test('all series may be skipped, but finishing still requires at least one real performance', async t => {
  const f = await fixture(t); let s = f.session;
  for (const series of f.session.sets) s = await f.sessions.skipSet(s.id, series.id, 0);
  assert.equal(selectSessionStep(s).phase, 'ready_to_finish'); assert.deepEqual(s.performances, []); assert.deepEqual(s.rests, []);
  await assert.rejects(f.sessions.finishSession(s.id), /au moins une performance réelle/);
  s = await f.sessions.reintegrateSet(s.id, s.sets[0]!.id, 1); s = await f.sessions.validateSet(s.id, s.sets[0]!.id, actual, s.sets[0]!.passageRevision ?? 0);
  assert.equal(s.rests.length, 0); s = await f.sessions.finishSession(s.id);
  assert.equal(s.status, 'completed'); assert.equal(s.performances.length, 1); assert.equal(sessionProgress(s).skipped, 3);
  assert.match(sessionProgressLabel(s), /1 série réalisée · 3 passées · 0 restante/);
  assert.equal(summarizeSession(s).loggedTonnageKg, 950); assert.equal(summarizeSession(s).meanRir, 0);
});
test('rapid duplicate intents affect one exact series and stale callbacks cannot overwrite a later reintegration', async t => {
  const f = await fixture(t), id = f.session.sets[0]!.id;
  const skipped = await Promise.all([0, 0, 0].map(revision => f.sessions.skipSet(f.session.id, id, revision)));
  assert.ok(skipped.every(s => sessionProgress(s).skipped === 1)); assert.equal(skipped[2]!.passages!.length, 1);
  const restored = await Promise.all([1, 1].map(revision => f.sessions.reintegrateSet(f.session.id, id, revision)));
  assert.equal(restored[1]!.passages!.length, 2); assert.equal(sessionProgress(restored[1]!).skipped, 0);
  await assert.rejects(f.sessions.skipSet(f.session.id, id, 0), /statut.*changé/);
  await f.sessions.skipSet(f.session.id, id, 2); await assert.rejects(f.sessions.reintegrateSet(f.session.id, id, 1), /statut.*changé/);
});
test('concurrent validation/skip requests commit one coherent outcome without skipping the following series', async t => {
  const f = await fixture(t), id = f.session.sets[0]!.id;
  const results = await Promise.allSettled([f.sessions.skipSet(f.session.id, id, 0), f.sessions.validateSet(f.session.id, id, actual)]);
  assert.deepEqual(results.map(r => r.status), ['fulfilled', 'rejected']);
  let s = (await f.sessions.getSession(f.session.id))!; assert.equal(s.performances.length, 0); assert.equal(sessionProgress(s).skipped, 1);
  s = await f.sessions.reintegrateSet(s.id, id, 1);
  const second = await Promise.allSettled([f.sessions.validateSet(s.id, id, actual, s.sets.find(item => item.id === id)?.passageRevision ?? 0), f.sessions.skipSet(s.id, id, 2)]);
  assert.deepEqual(second.map(r => r.status), ['fulfilled', 'rejected']);
  s = (await f.sessions.getSession(s.id))!; assert.equal(s.performances.length, 1); assert.equal(sessionProgress(s).skipped, 0);
});
test('SQLite statuses, goals and revisions survive reopening, then allow reintegration and execution', async t => {
  const f = await fixture(t); const saved = await f.sessions.skipSet(f.session.id, f.session.sets[0]!.id, 0);
  const db = new SqliteDatabase(f.path); t.after(() => db.close()); const resumed = new SessionRepository(db, f.id, f.now);
  assert.deepEqual(await resumed.getActiveSession(), saved);
  let s = await resumed.reintegrateSet(saved.id, saved.sets[0]!.id, 1); s = await resumed.validateSet(s.id, s.sets[0]!.id, actual, s.sets[0]!.passageRevision ?? 0);
  assert.equal(s.performances.length, 1); assert.equal(s.passages!.length, 2);
});
test('skipping and reintegrating another exercise respects the explicitly selected current exercise', async t => {
  const f = await fixture(t), other = f.session.exercises[1]!, first = f.session.sets[0]!;
  let s = await f.sessions.chooseNextExercise(f.session.id, other.id, first.id);
  s = await f.sessions.skipSet(s.id, first.id, 0); s = await f.sessions.reintegrateSet(s.id, first.id, 1);
  const step = selectSessionStep(s); if (step.phase !== 'set') throw new Error('set');
  assert.equal(step.exercise.id, other.id); assert.equal(s.exerciseChoices!.length, 1); assert.ok(remainingSessionExercises(s).some(e => e.exercise.id === first.sessionExerciseId));
});
test('skipping the last remaining series preserves an open paused rest until explicit manual completion', async t => {
  const f = await fixture(t); let s = await f.sessions.validateSet(f.session.id, f.session.sets[0]!.id, actual);
  s = await f.sessions.pauseRest(s.id, s.rests[0]!.id); const before = structuredClone({ rests: s.rests, performances: s.performances });
  for (const series of s.sets.slice(1)) s = await f.sessions.skipSet(s.id, series.id, 0);
  const step = selectSessionStep(s); assert.equal(step.phase, 'rest'); if (step.phase !== 'rest') throw new Error('rest');
  assert.equal(step.nextSet, null); assert.deepEqual(s.rests, before.rests); assert.deepEqual(s.performances, before.performances);
  await assert.rejects(f.sessions.finishSession(s.id)); s = await f.sessions.completeRest(s.id, step.rest.id);
  assert.equal(selectSessionStep(s).phase, 'ready_to_finish'); assert.ok(s.rests[0]!.endedAt); assert.ok(s.rests[0]!.pauses[0]!.endedAt);
  const completed = await f.sessions.finishSession(s.id); assert.equal(completed.performances.length, 1);
});
test('reintegration during rest restores a next series without resetting or ending its interval or pauses', async t => {
  const f = await fixture(t); let s = await f.sessions.validateSet(f.session.id, f.session.sets[0]!.id, actual);
  s = await f.sessions.pauseRest(s.id, s.rests[0]!.id); const before = structuredClone(s.rests);
  for (const series of s.sets.slice(1)) s = await f.sessions.skipSet(s.id, series.id, 0);
  s = await f.sessions.reintegrateSet(s.id, s.sets[1]!.id, 1);
  const step = selectSessionStep(s); if (step.phase !== 'rest') throw new Error('rest');
  assert.equal(step.nextSet!.id, s.sets[1]!.id); assert.deepEqual(s.rests, before);
});
test('a zero-rest pending transition also remains manual when every following series is skipped', async t => {
  const f = await fixture(t, 0); let s = await f.sessions.validateSet(f.session.id, f.session.sets[0]!.id, actual);
  const before = structuredClone(s.performances);
  for (const series of s.sets.slice(1)) s = await f.sessions.skipSet(s.id, series.id, 0);
  const step = selectSessionStep(s); if (step.phase !== 'between_sets') throw new Error('between');
  assert.equal(step.nextSet, null); assert.deepEqual(s.performances, before); assert.deepEqual(s.rests, []);
  s = await f.sessions.advanceAfterSet(s.id, step.performed.id); assert.equal(selectSessionStep(s).phase, 'ready_to_finish');
});
test('passing an actual reference leaves the dependent unresolved and preserves explicitly planned calculations and manual overrides', async t => {
  const f = await fixture(t); let s = await f.sessions.skipSet(f.session.id, f.session.sets[0]!.id, 0);
  assert.equal(s.sets[1]!.targets.targetWeightKg, null); assert.equal(s.sets[2]!.targets.targetWeightKg, 50);
  s = await f.sessions.updateSet(s.id, s.sets[1]!.id, { ...f.input, kind: 'back_off', targetWeightKg: 82, loadRule: null }, 'session');
  s = await f.sessions.reintegrateSet(s.id, s.sets[0]!.id, 1); s = await f.sessions.validateSet(s.id, s.sets[0]!.id, actual, s.sets[0]!.passageRevision ?? 0);
  assert.equal(s.sets[1]!.targets.targetWeightKg, 82); assert.equal(s.sets[2]!.targets.targetWeightKg, 50);
});
test('a skipped dependent retains a legitimate resolved proposal when reintegrated after its reference is performed', async t => {
  const f = await fixture(t); let s = await f.sessions.skipSet(f.session.id, f.session.sets[1]!.id, 0);
  s = await f.sessions.validateSet(s.id, s.sets[0]!.id, actual, s.sets[0]!.passageRevision ?? 0); assert.equal(s.sets[1]!.targets.targetWeightKg, 85.5);
  s = await f.sessions.reintegrateSet(s.id, s.sets[1]!.id, 1); assert.equal(s.sets[1]!.targets.targetWeightKg, 85.5); assert.equal(s.performances.length, 1);
});
test('replacement affects remaining series only; skipped originals keep their identity and targets after reintegration', async t => {
  const f = await fixture(t); let s = await f.sessions.skipSet(f.session.id, f.session.sets[0]!.id, 0);
  s = await f.sessions.skipSet(s.id, s.sets[2]!.id, 0); const before = structuredClone(s.sets[2]!);
  const replacement = (await f.training.listCatalog()).find(item => item.id !== s.exercises[0]!.sourceCatalogExerciseId)!;
  s = await f.sessions.replaceExercise(s.id, s.exercises[0]!.id, replacement.id, s.sets[1]!.id);
  assert.equal(s.sets.find(item => item.id === before.id)!.sessionExerciseId, before.sessionExerciseId);
  assert.deepEqual(s.sets.find(item => item.id === before.id)!.targets, before.targets);
  s = await f.sessions.reintegrateSet(s.id, before.id, 1); assert.ok(remainingSessionExercises(s).some(item => item.exercise.id === before.sessionExerciseId));
});
test('withdrawal of an added series remains distinct and requires reintegration before withdrawal', async t => {
  const f = await fixture(t); let s = await f.sessions.addSet(f.session.id, f.session.exercises[0]!.id, f.input, 'program', 'extra');
  const extra = s.sets.find(i => i.addition)!; s = await f.sessions.skipSet(s.id, extra.id, 0);
  await assert.rejects(f.sessions.deleteAddedSet(s.id, extra.id), /Réintégrer la série/);
  await assert.rejects(f.sessions.updateSet(s.id, extra.id, f.input, 'program'), /Réintégrer la série/);
  s = await f.sessions.reintegrateSet(s.id, extra.id, 1); s = await f.sessions.deleteAddedSet(s.id, extra.id);
  assert.equal(sessionProgress(s).skipped, 0); assert.equal(s.sets.length, 4); assert.equal(s.passages!.length, 2);
  assert.equal((await f.training.listSets(f.ex.id)).length, 4);
});
test('completed history retains skips and real statistics even after the program is deleted, with no status edits allowed', async t => {
  const f = await fixture(t); let s = f.session;
  for (const series of s.sets.slice(1)) s = await f.sessions.skipSet(s.id, series.id, 0);
  s = await f.sessions.validateSet(s.id, s.sets[0]!.id, actual, s.sets[0]!.passageRevision ?? 0); s = await f.sessions.finishSession(s.id);
  const before = structuredClone(s); assert.equal(summarizeSession(s).performedSetCount, 1); assert.equal(summarizeSession(s).loggedTonnageKg, 950);
  await assert.rejects(f.sessions.reintegrateSet(s.id, s.sets[1]!.id, 1), /déjà terminé/);
  await assert.rejects(f.sessions.skipSet(s.id, s.sets[1]!.id, 1), /déjà terminé/);
  await f.programs.deleteProgram(f.program.id); assert.deepEqual(await f.sessions.getSession(s.id), before);
  assert.equal((await f.sessions.listCompletedSessions())[0]!.performedSetCount, 1);
});
test('a failed selected-exercise write rolls back the passage and keeps a safe retry', async t => {
  const f = await fixture(t); let s = await f.sessions.chooseNextExercise(f.session.id, f.session.exercises[1]!.id, f.session.sets[0]!.id);
  const id = s.sets[3]!.id;
  await f.db.execAsync("CREATE TRIGGER fail_selection BEFORE UPDATE OF selected_exercise_id ON workout_sessions WHEN NEW.selected_exercise_id IS NULL BEGIN SELECT RAISE(ABORT,'storage full'); END;");
  await assert.rejects(f.sessions.skipSet(s.id, id, 0), /storage full/); assert.deepEqual(await f.sessions.getSession(s.id), s);
  await f.db.execAsync('DROP TRIGGER fail_selection'); s = await f.sessions.skipSet(s.id, id, 0); assert.equal(s.passages!.length, 1);
});
test('a populated released v7 database migrates without modifying any prior row, preference, note, goal, result or paused rest', async t => {
  const db = new SqliteDatabase(); t.after(() => db.close()); await db.execAsync(readFileSync(new URL('./fixtures/m34b-populated-v7.sql', import.meta.url), 'utf8'));
  const before = await snapshot(db), saved = JSON.parse(readFileSync(new URL('./fixtures/m34b-populated-v7-snapshots.json', import.meta.url), 'utf8'));
  await initializeDatabase(db); await initializeDatabase(db); assert.deepEqual(await snapshot(db, Object.keys(before)), before);
  const sessions = new SessionRepository(db, () => 'unused'); assert.deepEqual(await sessions.getActiveSession(), saved.active); assert.deepEqual(await sessions.getSession(saved.completed.id), saved.completed);
  assert.equal((await db.getFirstAsync<{ user_version: number }>('PRAGMA user_version'))!.user_version, DATABASE_VERSION);
  assert.deepEqual(await db.getAllAsync('SELECT * FROM session_set_passages'), []); assert.deepEqual(await db.getAllAsync('PRAGMA foreign_key_check'), []);
});
test('failed v8 migration rolls back schema and preserves v7 for a later retry', async t => {
  const db = new SqliteDatabase(); t.after(() => db.close()); await db.execAsync(readFileSync(new URL('./fixtures/m34b-populated-v7.sql', import.meta.url), 'utf8'));
  const before = await snapshot(db), exec = db.execAsync.bind(db);
  db.execAsync = async sql => { await exec(sql); if (sql.includes('CREATE TABLE session_set_passages')) throw new Error('disk full'); };
  await assert.rejects(initializeDatabase(db), /disk full/); assert.deepEqual(await snapshot(db), before);
  assert.equal((await db.getFirstAsync<{ user_version: number }>('PRAGMA user_version'))!.user_version, 7);
  db.execAsync = exec; await initializeDatabase(db);
});
test('export preserves skip/reintegration revisions and goals without any write and remains coherent during another connection change', async t => {
  const f = await fixture(t); let s = await f.sessions.skipSet(f.session.id, f.session.sets[0]!.id, 0);
  s = await f.sessions.reintegrateSet(s.id, s.sets[0]!.id, 1); s = await f.sessions.skipSet(s.id, s.sets[0]!.id, 2);
  const before = await snapshot(f.db), reader = new SqliteDatabase(f.path); t.after(() => reader.close()); let json = '';
  await writePersonalExport(reader, chunk => { json += chunk; }, { appVersion: '0.1.0' }); const file = JSON.parse(json);
  assert.equal(file.sqliteSchemaVersion, 8); assert.equal(file.restorationAvailableInExporter, false); assert.equal(EXPORT_TABLES.length, 20);
  assert.deepEqual(file.tables.session_set_passages.rows.map((r: any) => [r.action, r.revision]), [['skip', 1], ['reintegrate', 2], ['skip', 3]]);
  assert.deepEqual(await snapshot(f.db), before);
  const reader2 = new SqliteDatabase(f.path); t.after(() => reader2.close()); let second = '', changed = false;
  await writePersonalExport(reader2, async chunk => { second += chunk; if (!changed) { changed = true; await f.sessions.reintegrateSet(s.id, s.sets[0]!.id, 3); } }, { appVersion: '0.1.0' });
  assert.equal(JSON.parse(second).tables.session_set_passages.rowCount, 3); assert.equal((await f.sessions.getSession(s.id))!.passages!.length, 4);
});
test('SQLite guards and export integrity refuse a fabricated skip on an already performed series', async t => {
  const f = await fixture(t), s = await f.sessions.validateSet(f.session.id, f.session.sets[0]!.id, actual);
  await assert.rejects(f.db.runAsync("INSERT INTO session_set_passages VALUES ('bad',?,?,'skip',1,?)", s.id, s.sets[0]!.id, f.now()), /Invalid series passage/);
  await f.db.execAsync('DROP TRIGGER validate_set_passage'); await f.db.runAsync("INSERT INTO session_set_passages VALUES ('bad',?,?,'skip',1,?)", s.id, s.sets[0]!.id, f.now());
  const reader = new SqliteDatabase(f.path); t.after(() => reader.close());
  await assert.rejects(writePersonalExport(reader, () => {}, { appVersion: '0.1.0' }), /statut d’une série/);
});
test('exclusive Expo connections with FK off still validate exact ownership and sequential passage revisions', async t => {
  const f = await fixture(t), exclusive = Object.create(f.db) as Database;
  exclusive.withExclusiveTransactionAsync = async task => {
    const db = new SqliteDatabase(f.path); await db.execAsync('PRAGMA foreign_keys=OFF'); assert.equal((await db.getFirstAsync<{ foreign_keys: number }>('PRAGMA foreign_keys'))!.foreign_keys, 0);
    try { await db.withTransactionAsync(() => task(db)); } finally { db.close(); }
  };
  const sessions = new SessionRepository(exclusive, f.id, f.now);
  await assert.rejects(sessions.skipSet(f.session.id, 'wrong-series', 0));
  await assert.rejects(sessions.skipSet(f.session.id, f.session.sets[0]!.id, 50), /statut.*changé/);
  let s = await sessions.skipSet(f.session.id, f.session.sets[0]!.id, 0); s = await sessions.reintegrateSet(s.id, s.sets[0]!.id, 1);
  assert.equal(s.passages!.length, 2); assert.deepEqual(await f.db.getAllAsync('PRAGMA foreign_key_check'), []);
});


test('a delayed validation from before skipping is rejected even after that same series is reintegrated', async t => {
  const f = await fixture(t), id = f.session.sets[0]!.id;
  let s = await f.sessions.skipSet(f.session.id, id, 0); s = await f.sessions.reintegrateSet(s.id, id, 1);
  await assert.rejects(f.sessions.validateSet(s.id, id, actual, 0), /statut.*changé/); assert.equal((await f.sessions.getSession(s.id))!.performances.length, 0);
  s = await f.sessions.validateSet(s.id, id, actual, 2); assert.equal(s.performances.length, 1);
});
