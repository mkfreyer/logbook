import assert from 'node:assert/strict';
import { readFileSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { test } from 'node:test';
import { DATABASE_VERSION, initializeDatabase } from '../src/db/migrations';
import type { Program, WorkoutTemplate } from '../src/domain/models';
import { ProgramRepository } from '../src/db/repository';
import { TrainingRepository } from '../src/db/trainingRepository';
import { SessionRepository } from '../src/db/sessionRepository';
import { PreferencesRepository } from '../src/db/preferencesRepository';
import { EXPORT_TABLES, EXPORT_PAGE_SIZE, writePersonalExport, type PersonalExportError } from '../src/data/personalExport';
import { selectSessionStep, type WorkoutSession } from '../src/domain/session';
import { SqliteDatabase } from './helpers/SqliteDatabase';

type Row = Record<string, string | number | null>;
interface ExportFile { format: string; formatVersion: number; sqliteSchemaVersion: number; createdAt: string;
  rowidField: string; preferenceDefaults: { restSoundEnabled: boolean }; restorationAvailableInExporter: boolean;
  tables: Record<string, { columns: string[]; rows: Row[]; rowCount: number }> }
async function fixture(t: { after(callback: () => void): void }, legacy = false) {
  const directory = mkdtempSync(join(tmpdir(), 'logbook-m33-')), path = join(directory, 'logbook.db');
  const db = new SqliteDatabase(path); t.after(() => { db.close(); rmSync(directory, { recursive: true, force: true }); });
  if (legacy) {
    await db.execAsync(readFileSync(new URL('./fixtures/m33-populated-v5.sql', import.meta.url), 'utf8'));
    await db.execAsync('DROP TABLE app_preferences; PRAGMA user_version = 4;');
  } else await initializeDatabase(db);
  let serial = 100000, clock = Date.parse('2026-10-15T12:00:00.000Z');
  const id = () => `id-${--serial}`, now = () => new Date(clock).toISOString(), advance = (ms: number) => { clock += ms; };
  const programs = new ProgramRepository(db, id, now), training = new TrainingRepository(db, id, now), sessions = new SessionRepository(db, id, now), preferences = new PreferencesRepository(db, now);
  if (legacy) {
    const saved = JSON.parse(readFileSync(new URL('./fixtures/m33-populated-snapshots.json', import.meta.url), 'utf8')) as {
      program: Program; workout: WorkoutTemplate; completed: WorkoutSession; active: WorkoutSession;
    };
    return { db, path, programs, training, sessions, preferences, ...saved };
  }
  const program = await programs.createProgram({ name: 'Mes vrais repères de test', description: 'Texte "cité"\navec accents 🏋️' });
  const workout = await programs.createWorkout(program.id, { name: 'Haut du corps' });
  const catalog = [];
  for (const [index, name] of ['Barre', 'Tractions', 'Haltères'].entries()) catalog.push(await training.createCustomExercise({ name, muscleGroup: 'Dos', equipment: 'Salle', weightMode: index === 0 ? 'total' : index === 1 ? 'additional' : 'per_hand' }));
  for (const item of catalog.slice(0, 2)) {
    const planned = await training.addWorkoutExercise(workout.id, { exerciseId: item.id });
    for (let i = 0; i < 2; i++) await training.createSet(planned.id, { kind: 'work', repsMin: 99, repsMax: 99, targetWeightKg: 999, targetRir: 7, restAfterSec: 30 });
  }
  let session = await sessions.startOrResume(workout.id);
  session = await sessions.validateSet(session.id, session.sets[0]!.id, { weightKg: 40, reps: 8, rir: 0 });
  const restId = session.rests[0]!.id; advance(3000); await sessions.pauseRest(session.id, restId);
  advance(2000); await sessions.resumeRest(session.id, restId); advance(5000); session = await sessions.completeRest(session.id, restId);
  let step = selectSessionStep(session); if (step.phase !== 'set') throw new Error('set');
  session = await sessions.replaceExercise(session.id, step.exercise.id, catalog[2]!.id, step.set.id);
  const replacement = session.selectedExerciseId!, other = session.exercises[1]!.id;
  for (const choice of [other, replacement, other]) {
    step = selectSessionStep(session); if (step.phase !== 'set') throw new Error('set');
    session = await sessions.chooseNextExercise(session.id, choice, step.set.id);
  }
  while (selectSessionStep(session).phase !== 'ready_to_finish') {
    const next = selectSessionStep(session); advance(1000);
    if (next.phase === 'set') session = await sessions.validateSet(session.id, next.set.id, { weightKg: next.exercise.weightMode === 'additional' ? null : 15, reps: 10, rir: null });
    else if (next.phase === 'rest') session = await sessions.completeRest(session.id, next.rest.id);
    else throw new Error('phase');
  }
  const completed = await sessions.finishSession(session.id);
  advance(60000); let active = await sessions.startOrResume(workout.id);
  active = await sessions.validateSet(active.id, active.sets[0]!.id, { weightKg: null, reps: 10, rir: null });
  advance(5000); active = await sessions.pauseRest(active.id, active.rests[0]!.id);
  const occurrence = (await training.listWorkoutExercises(workout.id))[0]!;
  const reference = (await training.listSets(occurrence.id))[0]!;
  await training.createSet(occurrence.id, { kind: 'warmup', repsMin: 5, repsMax: 5, restAfterSec: 20,
    loadRule: { basis: 'planned_target', referenceSetId: reference.id, percent: 50 } });
  return { db, path, programs, training, sessions, preferences, completed, active, program, workout };
}
async function snapshot(db: SqliteDatabase, excludePreferences = false) {
  const result: Record<string, Row[]> = {};
  for (const [table] of EXPORT_TABLES) if (!(excludePreferences && ['app_preferences', 'set_load_rules'].includes(table))) {
    const columns = excludePreferences && table === 'session_sets'
      ? (await db.getAllAsync<{ name: string }>('PRAGMA table_info(session_sets)')).map(item => item.name).filter(name => name !== 'load_rule_snapshot').join(',') : '*';
    result[table] = await db.getAllAsync(`SELECT rowid AS __rowid, ${columns} FROM ${table} ORDER BY rowid`);
  }
  return result;
}
async function exportFile(path: string, onChunk?: (text: string) => void | Promise<void>, signal?: AbortSignal) {
  const reader = new SqliteDatabase(path); let text = '';
  try {
    await writePersonalExport(reader, async chunk => { text += chunk; await onChunk?.(chunk); }, { appVersion: '0.1.0', createdAt: '2026-10-15T12:00:00.000Z', signal });
    return JSON.parse(text) as ExportFile;
  } finally { reader.close(); }
}

test('v4 to current migration preserves every M0–M3.2 value, including a paused active rest; preference table starts empty', async t => {
  const f = await fixture(t, true), before = await snapshot(f.db, true);
  await initializeDatabase(f.db);
  assert.deepEqual(await snapshot(f.db, true), before); assert.deepEqual(await f.db.getAllAsync('SELECT * FROM app_preferences'), []);
  assert.equal((await f.db.getFirstAsync<{ user_version: number }>('PRAGMA user_version'))!.user_version, DATABASE_VERSION);
  assert.deepEqual(await f.sessions.getSession(f.active.id), f.active); assert.deepEqual(await f.sessions.getSession(f.completed.id), f.completed);
  assert.deepEqual(await f.db.getAllAsync('PRAGMA foreign_key_check'), []);
});
test('failed preference migration rolls back its schema and leaves version 4 data untouched', async t => {
  const f = await fixture(t, true), before = await snapshot(f.db, true), original = f.db.execAsync.bind(f.db);
  f.db.execAsync = async sql => { if (sql.includes('CREATE TABLE app_preferences')) throw new Error('storage full'); return original(sql); };
  await assert.rejects(initializeDatabase(f.db), /storage full/); assert.deepEqual(await snapshot(f.db, true), before);
  assert.equal((await f.db.getFirstAsync<{ user_version: number }>('PRAGMA user_version'))!.user_version, 4);
  assert.equal(await f.db.getFirstAsync("SELECT name FROM sqlite_master WHERE name='app_preferences'"), null);
});
test('sound defaults to existing behavior and persists false/true across independent connections', async t => {
  const f = await fixture(t); assert.deepEqual(await f.preferences.getPreferences(), { restSoundEnabled: true });
  await f.preferences.setRestSoundEnabled(false);
  const db = new SqliteDatabase(f.path); t.after(() => db.close()); const preferences = new PreferencesRepository(db);
  assert.deepEqual(await preferences.getPreferences(), { restSoundEnabled: false });
  await preferences.setRestSoundEnabled(true); assert.deepEqual(await f.preferences.getPreferences(), { restSoundEnabled: true });
});
test('failed preference writes preserve the saved value and recover; malformed known values are not treated as true', async t => {
  const f = await fixture(t); await f.preferences.setRestSoundEnabled(false); const original = f.db.runAsync.bind(f.db);
  f.db.runAsync = async () => { throw new Error('storage full'); };
  await assert.rejects(f.preferences.setRestSoundEnabled(true), /storage full/); assert.equal((await f.preferences.getPreferences()).restSoundEnabled, false);
  f.db.runAsync = original; await f.preferences.setRestSoundEnabled(true);
  await f.db.runAsync("UPDATE app_preferences SET value_json = '\"invalid\"'"); await assert.rejects(f.preferences.getPreferences());
  await assert.rejects(f.preferences.setRestSoundEnabled('false' as unknown as boolean));
});
test('rapid preference requests serialize real SQLite writes and persist the latest intent without touching other data', async t => {
  const f = await fixture(t), before = await snapshot(f.db, true), original = f.db.runAsync.bind(f.db);
  let inFlight = 0, maxInFlight = 0;
  f.db.runAsync = async (sql, ...args) => {
    inFlight++; maxInFlight = Math.max(maxInFlight, inFlight);
    try { await new Promise(resolve => setTimeout(resolve, 2)); return await original(sql, ...args); }
    finally { inFlight--; }
  };
  await Promise.all([false, true, false, true, false].map(value => f.preferences.setRestSoundEnabled(value)));
  assert.equal(maxInFlight, 1);
  const reader = new SqliteDatabase(f.path); t.after(() => reader.close());
  assert.equal((await new PreferencesRepository(reader).getPreferences()).restSoundEnabled, false);
  assert.deepEqual(await snapshot(f.db, true), before);
});
test('a failed queued preference write does not block the last intent or corrupt application data', async t => {
  const f = await fixture(t), before = await snapshot(f.db, true), original = f.db.runAsync.bind(f.db); let writes = 0;
  f.db.runAsync = async (sql, ...args) => {
    if (++writes === 2) throw new Error('storage full');
    return original(sql, ...args);
  };
  const results = await Promise.allSettled([false, true, false].map(value => f.preferences.setRestSoundEnabled(value)));
  assert.deepEqual(results.map(result => result.status), ['fulfilled', 'rejected', 'fulfilled']);
  assert.equal((await f.preferences.getPreferences()).restSoundEnabled, false);
  assert.deepEqual(await snapshot(f.db, true), before);
});
test('complete JSON export preserves all table values, IDs, null/zero, targets, pauses, active/completed sessions and tied journal order', async t => {
  const f = await fixture(t); await f.preferences.setRestSoundEnabled(false); const before = await snapshot(f.db);
  const file = await exportFile(f.path);
  assert.equal(file.format, 'logbook.personal-data'); assert.equal(file.formatVersion, 1); assert.equal(file.sqliteSchemaVersion, DATABASE_VERSION);
  assert.equal(file.rowidField, '__rowid'); assert.equal(file.restorationAvailableInExporter, false); assert.equal(file.preferenceDefaults.restSoundEnabled, true);
  for (const [table] of EXPORT_TABLES) {
    assert.deepEqual(file.tables[table]!.rows, before[table]); assert.equal(file.tables[table]!.rowCount, before[table]!.length);
    assert.ok(file.tables[table]!.rows.length > 0, `fixture should exercise ${table}`);
  }
  assert.deepEqual(await snapshot(f.db), before);
  assert.equal(file.tables.performed_sets!.rows[0]!.rir, 0); assert.ok(file.tables.performed_sets!.rows.some(row => row.weight_kg === null));
  const choices = file.tables.session_exercise_choices!.rows;
  assert.equal(new Set(choices.map(row => row.chosen_at)).size, 1);
  assert.notDeepEqual(choices.map(row => row.id), choices.map(row => row.id).sort());
});
test('a fresh application exports an honest empty logbook with catalog references and preference defaults', async t => {
  const directory = mkdtempSync(join(tmpdir(), 'logbook-empty-')), path = join(directory, 'logbook.db'), db = new SqliteDatabase(path);
  t.after(() => { db.close(); rmSync(directory, { recursive: true, force: true }); }); await initializeDatabase(db);
  const file = await exportFile(path);
  for (const [table] of EXPORT_TABLES) assert.equal(file.tables[table]!.rowCount, table === 'exercise_catalog' ? 15 : 0);
});
test('a WAL snapshot stays coherent while another connection creates a program, changes a preference and validates a set', async t => {
  const f = await fixture(t); await f.preferences.setRestSoundEnabled(false); const before = await snapshot(f.db); let written = false;
  const file = await exportFile(f.path, async () => {
    if (written) return; written = true;
    const program = await f.programs.createProgram({ name: 'Créé pendant l’export' }); await f.programs.createWorkout(program.id, { name: 'Nouvelle séance' });
    await f.preferences.setRestSoundEnabled(true);
    const phase = selectSessionStep(f.active); if (phase.phase !== 'rest') throw new Error('rest');
    const resumed = await f.sessions.completeRest(f.active.id, phase.rest.id), next = selectSessionStep(resumed);
    if (next.phase !== 'set') throw new Error('set');
    await f.sessions.validateSet(resumed.id, next.set.id, { weightKg: 20, reps: 8, rir: 2 });
  });
  for (const [table] of EXPORT_TABLES) assert.deepEqual(file.tables[table]!.rows, before[table], table);
  assert.equal((await f.preferences.getPreferences()).restSoundEnabled, true);
  assert.equal((await f.sessions.getSession(f.active.id))!.performances.length, 2);
  assert.equal((await f.programs.listPrograms()).length, 2);
});
test('export keeps historical snapshots after deletion of their program', async t => {
  const f = await fixture(t); await f.programs.deleteProgram(f.program.id);
  const file = await exportFile(f.path); assert.equal(file.tables.programs!.rowCount, 0);
  assert.equal(file.tables.workout_sessions!.rowCount, 2); assert.equal(file.tables.performed_sets!.rowCount, 5);
  assert.equal(file.tables.workout_sessions!.rows[0]!.source_program_id, f.program.id);
});
test('cancelled export and sink failure release the snapshot and never modify application rows', async t => {
  const f = await fixture(t), before = await snapshot(f.db), controller = new AbortController();
  await assert.rejects(exportFile(f.path, () => controller.abort(), controller.signal), (error: PersonalExportError) => error.code === 'cancelled');
  await assert.rejects(exportFile(f.path, () => { throw new Error('disk full'); }), /disk full/);
  assert.deepEqual(await snapshot(f.db), before);
  await f.programs.createProgram({ name: 'Toujours modifiable' });
  assert.equal((await f.programs.listPrograms()).length, 2);
});
test('export rejects unknown schema/tables and relational corruption without producing a claimed backup', async t => {
  const f = await fixture(t); await f.db.execAsync('PRAGMA user_version = 99;');
  await assert.rejects(exportFile(f.path), (error: PersonalExportError) => error.code === 'incompatible');
  await f.db.execAsync(`PRAGMA user_version = ${DATABASE_VERSION}; CREATE TABLE sqlitex_user_data (id TEXT);`);
  await assert.rejects(exportFile(f.path), (error: PersonalExportError) => error.code === 'incompatible');
  await f.db.execAsync('DROP TABLE sqlitex_user_data; PRAGMA foreign_keys = OFF;');
  await f.db.runAsync("INSERT INTO workout_templates VALUES ('orphan','missing','Orpheline','',999,'2026','2026')");
  await assert.rejects(exportFile(f.path), (error: PersonalExportError) => error.code === 'integrity');
});
test('multi-year export uses bounded pages rather than loading all performances at once', async t => {
  const f = await fixture(t);
  await f.db.withTransactionAsync(async () => {
    await f.db.runAsync(`WITH RECURSIVE n(i) AS (VALUES(1) UNION ALL SELECT i+1 FROM n WHERE i<1500)
      INSERT INTO workout_sessions (id,source_workout_template_id,source_program_id,workout_name,program_name,status,started_at,finished_at)
      SELECT 'bulk-'||i,source_workout_template_id,source_program_id,workout_name,program_name,'completed',
        strftime('%Y-%m-%dT10:00:00.000Z','2021-01-01','+'||i||' days'),strftime('%Y-%m-%dT11:00:00.000Z','2021-01-01','+'||i||' days')
      FROM n CROSS JOIN workout_sessions WHERE id=?`, f.completed.id);
    await f.db.runAsync(`INSERT INTO session_exercises SELECT s.id||'-'||e.id,s.id,e.source_workout_exercise_id,e.source_catalog_exercise_id,
      e.sort_order,e.name,e.muscle_group,e.equipment,e.instructions,e.notes,e.weight_mode,e.planned_order
      FROM workout_sessions s CROSS JOIN session_exercises e WHERE s.id LIKE 'bulk-%' AND e.session_id=?`, f.completed.id);
    // Explicit column names keep the fixture independent of physical column order.
    const columns = (await f.db.getAllAsync<{ name: string }>('PRAGMA table_info(session_sets)')).map(row => row.name);
    const expression = columns.map(column => column === 'id' ? "s.id||'-'||t.id" : column === 'session_id' ? 's.id' : column === 'session_exercise_id' ? "s.id||'-'||t.session_exercise_id" : `t.${column}`);
    await f.db.runAsync(`INSERT INTO session_sets (${columns.join(',')}) SELECT ${expression.join(',')} FROM workout_sessions s CROSS JOIN session_sets t WHERE s.id LIKE 'bulk-%' AND t.session_id=?`, f.completed.id);
    await f.db.runAsync(`INSERT INTO performed_sets SELECT s.id||'-'||p.id,s.id,s.id||'-'||p.session_set_id,p.sort_order,p.weight_kg,p.reps,p.rir,p.performed_at,p.advanced_at
      FROM workout_sessions s CROSS JOIN performed_sets p WHERE s.id LIKE 'bulk-%' AND p.session_id=?`, f.completed.id);
  });
  const reader = new SqliteDatabase(f.path); t.after(() => reader.close());
  const original = reader.getAllAsync.bind(reader); let maxRows = 0, pages = 0;
  reader.getAllAsync = async <T>(sql: string, ...params: (string | number | null)[]) => {
    const rows = await original<T>(sql, ...params);
    if (sql.includes('rowid AS __rowid')) { pages++; maxRows = Math.max(maxRows, rows.length); }
    return rows;
  };
  let text = ''; const result = await writePersonalExport(reader, chunk => { text += chunk; }, { appVersion: '0.1.0' });
  const file = JSON.parse(text) as ExportFile;
  assert.equal(file.tables.workout_sessions!.rowCount, 1502); assert.equal(file.tables.performed_sets!.rowCount, 6005);
  assert.ok(result.totalRows > 15000); assert.ok(pages > 50); assert.equal(maxRows, EXPORT_PAGE_SIZE);
  assert.deepEqual(await f.db.getAllAsync('PRAGMA foreign_key_check'), []);
});
