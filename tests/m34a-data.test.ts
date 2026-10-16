import assert from 'node:assert/strict';
import { readFileSync, mkdtempSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { test } from 'node:test';
import { initializeDatabase } from '../src/db/migrations';
import { ProgramRepository } from '../src/db/repository';
import { TrainingRepository } from '../src/db/trainingRepository';
import { SessionRepository } from '../src/db/sessionRepository';
import { PreferencesRepository } from '../src/db/preferencesRepository';
import { percentageWeight, parseLoadPercentage, formatSeriesTitle } from '../src/domain/series';
import type { SetTemplateInput, WeightMode } from '../src/domain/training';
import type { WorkoutSession } from '../src/domain/session';
import { selectSessionStep } from '../src/domain/session';
import { summarizeSession } from '../src/domain/sessionSummary';
import { EXPORT_TABLES, writePersonalExport } from '../src/data/personalExport';
import { SqliteDatabase } from './helpers/SqliteDatabase';
import type { Database } from '../src/db/types';

const manual: SetTemplateInput = { kind: 'top_set', label: 'Principale', repsMin: 8, repsMax: 10, targetWeightKg: 80, targetRir: 2, restAfterSec: 60 };
const rule = (id: string | null, percent = 50) => ({ basis: 'planned_target' as const, referenceSetId: id, percent });
async function fixture(t: { after(close: () => void): void }, mode: WeightMode = 'total') {
  const dir = mkdtempSync(join(tmpdir(), 'logbook-m34a-')), path = join(dir, 'logbook.db'), db = new SqliteDatabase(path);
  t.after(() => { db.close(); rmSync(dir, { recursive: true, force: true }); }); await initializeDatabase(db);
  let serial = 0, time = Date.parse('2026-10-16T12:00:00Z');
  const id = () => `m34a-${++serial}`, now = () => new Date(time++).toISOString();
  const programs = new ProgramRepository(db, id, now), training = new TrainingRepository(db, id, now), sessions = new SessionRepository(db, id, now);
  const program = await programs.createProgram({ name: 'Mon programme de test' }), workout = await programs.createWorkout(program.id, { name: 'Séance' });
  const catalog = await training.createCustomExercise({ name: 'Ma référence', muscleGroup: 'Dos', equipment: 'Salle', weightMode: mode });
  const exercise = await training.addWorkoutExercise(workout.id, { exerciseId: catalog.id });
  return { db, path, id, programs, training, sessions, program, workout, exercise };
}
async function legacy(t: { after(close: () => void): void }) {
  const db = new SqliteDatabase(); t.after(() => db.close());
  await db.execAsync(readFileSync(new URL('./fixtures/m33-populated-v5.sql', import.meta.url), 'utf8'));
  return db;
}
async function capture(db: SqliteDatabase) {
  const tables = await db.getAllAsync<{ name: string }>("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name");
  return Promise.all(tables.map(async table => {
    const columns = (await db.getAllAsync<{ name: string }>(`PRAGMA table_info(${table.name})`)).map(item => item.name);
    return { name: table.name, columns, rows: await db.getAllAsync(`SELECT ${columns.join(',')} FROM ${table.name} ORDER BY rowid`) };
  }));
}
test('decimal percentages are precise proposals without equipment rounding, null is not zero', () => {
  assert.equal(percentageWeight(80, 50), 40); assert.equal(percentageWeight(100, 90), 90);
  assert.equal(percentageWeight(83.25, 12.5), 10.40625); assert.equal(percentageWeight(0.1, 30), 0.03);
  assert.equal(percentageWeight(null, 50), null); assert.equal(percentageWeight(0, 50), 0);
  assert.equal(parseLoadPercentage('75,5'), 75.5);
  for (const input of ['0', '-2', '101', 'NaN', '50kg', '']) assert.throws(() => parseLoadPercentage(input));
  assert.throws(() => percentageWeight(Number.MIN_VALUE, 1));
});
test('series display modes preserve names/types and provide an understandable missing-name fallback', () => {
  const named = { label: 'Ma série', kind: 'work' as const };
  assert.equal(formatSeriesTitle(named, 2, 'number'), 'Série 3'); assert.equal(formatSeriesTitle(named, 2, 'name'), 'Ma série');
  assert.equal(formatSeriesTitle(named, 2, 'both'), 'Série 3 · Ma série');
  assert.equal(formatSeriesTitle({ ...named, label: '' }, 2, 'name'), 'Série 3');
  assert.equal(formatSeriesTitle({ label: '', kind: 'warmup' }, 0, 'name'), 'Échauffement');
});
for (const mode of ['total', 'per_hand', 'additional'] as const) test(`calculated warmup/back-off persist, follow manual targets and respect ${mode}`, async t => {
  const f = await fixture(t, mode), base = await f.training.createSet(f.exercise.id, manual);
  const warmup = await f.training.createSet(f.exercise.id, { ...manual, kind: 'warmup', restAfterSec: 30, loadRule: rule(base.id) });
  const back = await f.training.createSet(f.exercise.id, { ...manual, kind: 'back_off', loadRule: rule(base.id, 90) });
  assert.equal(warmup.targetWeightKg, 40); assert.equal(back.targetWeightKg, 72); assert.equal(warmup.restAfterSec, 30);
  assert.equal((await f.db.getFirstAsync<{ target_weight_kg: number | null }>('SELECT target_weight_kg FROM set_templates WHERE id=?', warmup.id))!.target_weight_kg, null);
  await f.training.updateSet(base.id, { ...manual, targetWeightKg: 100 });
  assert.equal((await f.training.getSet(back.id)).targetWeightKg, 90);
  const reopened = new SqliteDatabase(f.path); t.after(() => reopened.close());
  assert.deepEqual((await new TrainingRepository(reopened, f.id).getSet(warmup.id)).loadRule, rule(base.id));
  const session = await f.sessions.startOrResume(f.workout.id);
  assert.equal(session.sets[1]!.targets.targetWeightKg, 50); assert.equal(session.sets[1]!.loadRuleSnapshot!.weightMode, mode);
  assert.equal(session.performances.length, 0);
});
test('ordinary, optional warmup, top set, custom and manual back-off remain independent', async t => {
  const f = await fixture(t);
  for (const kind of ['work', 'warmup', 'top_set', 'back_off', 'custom'] as const) {
    const set = await f.training.createSet(f.exercise.id, { ...manual, kind, label: `${kind} personnel`, targetWeightKg: null });
    assert.equal(set.kind, kind); assert.equal(set.loadRule, null); assert.equal(set.targetWeightKg, null);
    const edited = await f.training.updateSet(set.id, { ...manual, kind, label: 'Renommée', restAfterSec: 120 });
    assert.equal(edited.id, set.id); assert.equal(edited.restAfterSec, 120);
  }
});
test('missing reference weight stays null, explicit zero stays zero, deleting a reference never keeps a stale computed weight', async t => {
  const f = await fixture(t), base = await f.training.createSet(f.exercise.id, { ...manual, targetWeightKg: null });
  const warm = await f.training.createSet(f.exercise.id, { ...manual, kind: 'warmup', loadRule: rule(base.id) }); assert.equal(warm.targetWeightKg, null);
  await f.training.updateSet(base.id, { ...manual, targetWeightKg: 0 }); assert.equal((await f.training.getSet(warm.id)).targetWeightKg, 0);
  await f.training.deleteSet(base.id); const missing = await f.training.getSet(warm.id);
  assert.equal(missing.targetWeightKg, null); assert.equal(missing.loadRule!.referenceSetId, null);
  const overridden = await f.training.updateSet(warm.id, { ...manual, kind: 'warmup', targetWeightKg: 23.75, loadRule: null });
  assert.equal(overridden.targetWeightKg, 23.75); assert.equal(overridden.loadRule, null);
});
test('self references, cross-exercise references, calculated chains, wrong top sets and invalid percentages are rejected atomically', async t => {
  const f = await fixture(t), base = await f.training.createSet(f.exercise.id, manual);
  const warm = await f.training.createSet(f.exercise.id, { ...manual, kind: 'warmup', loadRule: rule(base.id) });
  const other = await f.training.addWorkoutExercise(f.workout.id, { exerciseId: f.exercise.exerciseId });
  const wrong = await f.training.createSet(other.id, manual), work = await f.training.createSet(f.exercise.id, { ...manual, kind: 'work' });
  const before = await capture(f.db);
  for (const ref of [warm.id, wrong.id, 'missing']) await assert.rejects(f.training.createSet(f.exercise.id, { ...manual, kind: 'warmup', loadRule: rule(ref) }));
  await assert.rejects(f.training.updateSet(warm.id, { ...manual, kind: 'warmup', loadRule: rule(warm.id) }));
  await assert.rejects(f.training.createSet(f.exercise.id, { ...manual, kind: 'back_off', loadRule: rule(work.id) }));
  await assert.rejects(f.training.updateSet(base.id, { ...manual, kind: 'warmup', loadRule: rule(work.id) }));
  for (const percent of [0, -1, 101, NaN]) await assert.rejects(f.training.createSet(f.exercise.id, { ...manual, kind: 'warmup', loadRule: rule(base.id, percent) }));
  assert.deepEqual(await capture(f.db), before);
  await assert.rejects(f.db.runAsync('UPDATE set_templates SET kind=\'warmup\' WHERE id=?', base.id));
  assert.deepEqual(await capture(f.db), before);
});
test('reference identity survives reordering and failed writes restore the complete old rule', async t => {
  const f = await fixture(t), base = await f.training.createSet(f.exercise.id, manual);
  const warm = await f.training.createSet(f.exercise.id, { ...manual, kind: 'warmup', loadRule: rule(base.id) });
  await f.training.reorderSets(f.exercise.id, [warm.id, base.id]);
  assert.equal((await f.training.getSet(warm.id)).loadRule!.referenceSetId, base.id);
  const before = await capture(f.db), run = f.db.runAsync.bind(f.db);
  f.db.runAsync = async (sql, ...args) => { if (sql.includes('INSERT INTO set_load_rules')) throw new Error('disk full'); return run(sql, ...args); };
  await assert.rejects(f.training.updateSet(warm.id, { ...manual, kind: 'warmup', loadRule: rule(base.id, 75) }), /disk full/);
  assert.deepEqual(await capture(f.db), before);
});
test('session snapshots freeze the planned calculation and no real performance is invented or rewritten', async t => {
  const f = await fixture(t), base = await f.training.createSet(f.exercise.id, manual);
  const warm = await f.training.createSet(f.exercise.id, { ...manual, kind: 'warmup', restAfterSec: 0, loadRule: rule(base.id) });
  await f.training.reorderSets(f.exercise.id, [warm.id, base.id]);
  let session = await f.sessions.startOrResume(f.workout.id);
  const captured = session.sets[0]!; assert.equal(captured.targets.targetWeightKg, 40); assert.equal(session.performances.length, 0);
  await f.training.updateSet(base.id, { ...manual, targetWeightKg: 100 });
  session = (await f.sessions.getSession(session.id))!; assert.deepEqual(session.sets[0], captured);
  session = await f.sessions.validateSet(session.id, captured.id, { weightKg: 32.5, reps: 5, rir: null });
  assert.equal(session.performances[0]!.weightKg, 32.5); assert.equal(session.rests.length, 0);
  await assert.rejects(f.db.runAsync('UPDATE session_sets SET load_rule_snapshot=NULL WHERE id=?', captured.id));
  session = await f.sessions.advanceAfterSet(session.id, session.performances[0]!.id);
  session = await f.sessions.validateSet(session.id, session.sets[1]!.id, { weightKg: 80, reps: 8, rir: 2 });
  session = await f.sessions.finishSession(session.id); const before = summarizeSession(session);
  assert.equal(before.loggedTonnageKg, 802.5);
  await f.programs.deleteProgram(f.program.id);
  assert.deepEqual(await f.sessions.getSession(session.id), session); assert.deepEqual(summarizeSession((await f.sessions.getSession(session.id))!), before);
  assert.equal((await f.db.getAllAsync('PRAGMA foreign_key_check')).length, 0);
});
test('existing live manual edits keep session-only scope and explicitly replace a future rule in program scope', async t => {
  const f = await fixture(t), base = await f.training.createSet(f.exercise.id, manual);
  const warm = await f.training.createSet(f.exercise.id, { ...manual, kind: 'warmup', loadRule: rule(base.id) });
  await f.training.reorderSets(f.exercise.id, [warm.id, base.id]); let session = await f.sessions.startOrResume(f.workout.id);
  const first = session.sets[0]!, input = { ...first.targets, targetWeightKg: 35 };
  session = await f.sessions.updateSetTargets(session.id, first.id, input, 'session');
  assert.equal((await f.training.getSet(warm.id)).targetWeightKg, 40); assert.deepEqual(session.sets[0]!.originalTargets, first.originalTargets);
  session = await f.sessions.updateSetTargets(session.id, first.id, input, 'program');
  assert.equal((await f.training.getSet(warm.id)).loadRule, null); assert.equal((await f.training.getSet(warm.id)).targetWeightKg, 35);
  assert.deepEqual(session.sets[0]!.loadRuleSnapshot, first.loadRuleSnapshot); assert.equal(session.performances.length, 0);
});
test('v5 migration preserves every old column, ID, preference, completed workout and active paused rest', async t => {
  const db = await legacy(t), before = await capture(db);
  await initializeDatabase(db); await initializeDatabase(db);
  for (const table of before) assert.deepEqual(await db.getAllAsync(`SELECT ${table.columns.join(',')} FROM ${table.name} ORDER BY rowid`), table.rows, table.name);
  assert.deepEqual(await db.getAllAsync('SELECT * FROM set_load_rules'), []);
  assert.deepEqual(await db.getAllAsync('SELECT load_rule_snapshot FROM session_sets WHERE load_rule_snapshot IS NOT NULL'), []);
  assert.equal((await db.getFirstAsync<{user_version:number}>('PRAGMA user_version'))!.user_version, 6);
  const saved = JSON.parse(readFileSync(new URL('./fixtures/m33-populated-snapshots.json', import.meta.url), 'utf8')) as {active:WorkoutSession;completed:WorkoutSession};
  const sessions = new SessionRepository(db, () => 'unused');
  assert.deepEqual(await sessions.getActiveSession(), saved.active); assert.deepEqual(await sessions.getSession(saved.completed.id), saved.completed);
  const preferences = new PreferencesRepository(db); assert.equal((await preferences.getPreferences()).restSoundEnabled, false); assert.equal(await preferences.getSeriesDisplay(), 'name');
  assert.deepEqual(await db.getAllAsync('PRAGMA foreign_key_check'), []);
});
test('failed v6 migration rolls back schema and all v5 data and can be retried', async t => {
  const db = await legacy(t), before = await capture(db), exec = db.execAsync.bind(db);
  db.execAsync = async sql => { await exec(sql); if (sql.includes('CREATE TABLE set_load_rules')) throw new Error('migration disk full'); };
  await assert.rejects(initializeDatabase(db), /migration disk full/); assert.deepEqual(await capture(db), before);
  assert.equal((await db.getFirstAsync<{user_version:number}>('PRAGMA user_version'))!.user_version, 5);
  db.execAsync = exec; await initializeDatabase(db);
});
test('display preference persists independently of sound, including rapid writes and errors', async t => {
  const f = await fixture(t), preferences = new PreferencesRepository(f.db);
  await preferences.setRestSoundEnabled(false);
  await Promise.all(['number', 'both', 'name', 'both'].map(mode => preferences.setSeriesDisplay(mode as 'both')));
  const read = new SqliteDatabase(f.path); t.after(() => read.close()); const reopened = new PreferencesRepository(read);
  assert.equal(await reopened.getSeriesDisplay(), 'both'); assert.equal((await reopened.getPreferences()).restSoundEnabled, false);
  await assert.rejects(preferences.setSeriesDisplay('invalid' as 'both')); assert.equal(await preferences.getSeriesDisplay(), 'both');
});
test('personal export includes complete calculation relationships, frozen provenance and the display preference without changing data', async t => {
  const f = await fixture(t), base = await f.training.createSet(f.exercise.id, manual);
  await f.training.createSet(f.exercise.id, { ...manual, kind: 'back_off', loadRule: rule(base.id, 90) });
  const session = await f.sessions.startOrResume(f.workout.id); await new PreferencesRepository(f.db).setSeriesDisplay('both');
  const before = await capture(f.db), reader = new SqliteDatabase(f.path); t.after(() => reader.close()); let json = '';
  await writePersonalExport(reader, value => { json += value; }, { appVersion: '0.1.0' });
  const file = JSON.parse(json); assert.equal(file.formatVersion, 1); assert.equal(file.sqliteSchemaVersion, 6);
  assert.equal(Object.keys(file.tables).length, EXPORT_TABLES.length); assert.equal(file.tables.set_load_rules.rows[0].reference_set_id, base.id);
  assert.equal(JSON.parse(file.tables.session_sets.rows[1].load_rule_snapshot).resolvedWeightKg, 72);
  assert.equal(file.tables.app_preferences.rows[0].value_json, '"both"'); assert.equal(file.preferenceDefaults.seriesDisplay, 'name');
  assert.equal(file.tables.performed_sets.rowCount, 0); assert.deepEqual(await capture(f.db), before);
  assert.equal(selectSessionStep(session).phase, 'set');
});
test('Expo-style exclusive connections atomically write and capture rules even when their FK pragma is off', async t => {
  const f = await fixture(t); let transactions = 0;
  const exclusive = Object.create(f.db) as Database;
  exclusive.withExclusiveTransactionAsync = async operation => {
    const transaction = new SqliteDatabase(f.path); transactions++;
    try { await transaction.withTransactionAsync(() => operation(transaction)); } finally { transaction.close(); }
  };
  const training = new TrainingRepository(exclusive, f.id), sessions = new SessionRepository(exclusive, f.id);
  const base = await training.createSet(f.exercise.id, manual), warm = await training.createSet(f.exercise.id, { ...manual, kind: 'warmup', loadRule: rule(base.id) });
  assert.equal(warm.targetWeightKg, 40); const session = await sessions.startOrResume(f.workout.id);
  assert.equal(session.sets[1]!.loadRuleSnapshot!.resolvedWeightKg, 40); assert.equal(transactions, 3);
  assert.deepEqual(await f.db.getAllAsync('PRAGMA foreign_key_check'), []);
});
