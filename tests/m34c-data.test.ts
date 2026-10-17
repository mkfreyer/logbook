import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { test } from 'node:test';
import { EXERCISE_GUIDES, availableAlternatives, exerciseGuide, loadExplanation } from '../src/data/exerciseGuides';
import { EXPORT_TABLES, writePersonalExport } from '../src/data/personalExport';
import { INITIAL_EXERCISES } from '../src/db/exerciseCatalog';
import { DATABASE_VERSION, initializeDatabase } from '../src/db/migrations';
import { ProgramRepository } from '../src/db/repository';
import { TrainingRepository } from '../src/db/trainingRepository';
import { SessionRepository } from '../src/db/sessionRepository';
import { selectSessionStep } from '../src/domain/session';
import { summarizeSession } from '../src/domain/sessionSummary';
import type { ExerciseCatalogItem } from '../src/domain/training';
import { SqliteDatabase } from './helpers/SqliteDatabase';

const catalog: ExerciseCatalogItem[] = INITIAL_EXERCISES.map(item => ({ ...item, instructions: item.instructions ?? '', isCustom: false, createdAt: '', updatedAt: '' }));
const source = catalog[0]!, alternative = catalog[1]!;
for (const item of catalog) test(`offline guide: stable identity, specific content and explicit valid alternatives for ${item.name}`, () => {
  const guide = exerciseGuide(item); assert.ok(guide); assert.ok(guide.description.length); assert.ok(guide.start.length);
  assert.ok(guide.steps.length >= 2); assert.ok(guide.tips.length >= 2 && guide.tips.length <= 4); assert.ok(guide.mistakes.length); assert.ok(guide.load);
  const ids = guide.alternatives.map(link => link.exerciseId); assert.equal(new Set(ids).size, ids.length); assert.ok(!ids.includes(item.id));
  for (const link of guide.alternatives) { assert.ok(catalog.some(target => target.id === link.exerciseId)); assert.ok(link.reason.length > 40); }
});
test('all fifteen initial IDs have a guide without adding any catalog rows or guessing text matches', () => {
  assert.equal(Object.keys(EXERCISE_GUIDES).length, 15); assert.deepEqual(new Set(Object.keys(EXERCISE_GUIDES)), new Set(catalog.map(item => item.id)));
  const links = availableAlternatives({ ...source, name: 'Un nom différent' }, catalog);
  assert.deepEqual(links.map(item => item.exercise.id), [catalog[1]!.id, catalog[2]!.id]);
  assert.ok(!availableAlternatives(catalog[10]!, catalog).length); // Shoulders are not interchangeable merely by muscle group.
  assert.deepEqual(availableAlternatives({ ...source, id: 'unknown' }, catalog), []);
});
test('custom items never receive invented guidance or inferred alternatives, even with a matching name', () => {
  const custom = { ...source, id: 'personal', isCustom: true };
  assert.equal(exerciseGuide(custom), undefined); assert.deepEqual(availableAlternatives(custom, catalog), []);
});
test('missing alternative rows are omitted and duplicate catalog entries cannot duplicate cards', () => {
  assert.deepEqual(availableAlternatives(source, [source]), []);
  const links = availableAlternatives(source, [source, alternative, alternative]); assert.equal(links.length, 1);
  assert.equal(links[0]!.exercise.weightMode, 'per_hand'); assert.equal(links[0]!.exercise.equipment, alternative.equipment);
});
test('all load modes have a clear explanation and missing load is distinguished from zero', () => {
  assert.ok(loadExplanation.total.includes('barre')); assert.ok(loadExplanation.per_hand.includes('ne double pas')); assert.ok(loadExplanation.additional.includes('0 kg'));
});
async function fixture(t: { after(fn: () => void): void }) {
  const directory = mkdtempSync(join(tmpdir(), 'logbook-m34c-')), path = join(directory, 'logbook.db'), db = new SqliteDatabase(path);
  t.after(() => { db.close(); rmSync(directory, { recursive: true, force: true }); }); await initializeDatabase(db);
  let serial = 0, time = Date.parse('2026-10-17T10:00:00Z'); const id = () => `guide-${++serial}`, now = () => new Date(time += 1000).toISOString();
  const programs = new ProgramRepository(db, id, now), training = new TrainingRepository(db, id, now), sessions = new SessionRepository(db, id, now);
  const program = await programs.createProgram({ name: 'Mon programme de test' }), workout = await programs.createWorkout(program.id, { name: 'Séance' });
  const exercise = await training.addWorkoutExercise(workout.id, { exerciseId: source.id });
  const input = { kind: 'top_set' as const, repsMin: 8, repsMax: 10, targetWeightKg: 100, targetRir: 2, restAfterSec: 60 };
  const top = await training.createSet(exercise.id, input);
  await training.createSet(exercise.id, { ...input, kind: 'back_off', loadRule: { basis: 'performed_weight', referenceSetId: top.id, percent: 90 } });
  await training.createSet(exercise.id, { ...input, kind: 'work' }); await training.createSet(exercise.id, { ...input, kind: 'work' });
  const session = await sessions.startOrResume(workout.id);
  return { db, path, id, now, programs, program, workout, training, sessions, session };
}
async function snapshot(db: SqliteDatabase) {
  const tables = await db.getAllAsync<{ name: string }>("SELECT name FROM sqlite_master WHERE type='table' AND name NOT GLOB 'sqlite_*' ORDER BY name");
  return Object.fromEntries(await Promise.all(tables.map(async ({ name }) => [name, await db.getAllAsync(`SELECT rowid AS __rowid, * FROM ${name} ORDER BY rowid`)])));
}
async function planned(training: TrainingRepository, workoutId: string) {
  return Promise.all((await training.listWorkoutExercises(workoutId)).map(async exercise => ({ ...exercise, sets: await training.listSets(exercise.id) })));
}
test('reading every guide on a populated v8 database requires no migration and changes no personal rows', async t => {
  const f = await fixture(t); await f.sessions.skipSet(f.session.id, f.session.sets[2]!.id, 0);
  const before = await snapshot(f.db); for (const item of await f.training.listCatalog()) { exerciseGuide(item); availableAlternatives(item, catalog); }
  await initializeDatabase(f.db); assert.equal(DATABASE_VERSION, 8); assert.deepEqual(await snapshot(f.db), before);
  assert.equal((await f.training.listCatalog()).length, 15); assert.equal((await f.programs.listPrograms()).length, 1);
});
test('replacement preserves performed and skipped series, original targets and the program, then survives reopening', async t => {
  const f = await fixture(t), plannedBefore = await planned(f.training, f.workout.id);
  let s = await f.sessions.skipSet(f.session.id, f.session.sets[2]!.id, 0);
  s = await f.sessions.validateSet(s.id, s.sets[0]!.id, { weightKg: 95, reps: 9, rir: 1 });
  const rest = s.rests[0]!; s = await f.sessions.pauseRest(s.id, rest.id); s = await f.sessions.resumeRest(s.id, rest.id);
  const before = await snapshot(f.db);
  await assert.rejects(f.sessions.replaceExercise(s.id, s.exercises[0]!.id, alternative.id, s.sets[1]!.id), /repos|Reprenez/);
  assert.deepEqual(await snapshot(f.db), before);
  s = await f.sessions.completeRest(s.id, rest.id); const completedRest = s.rests[0]; const performed = s.performances[0];
  const step = selectSessionStep(s); assert.equal(step.phase, 'set'); if (step.phase !== 'set') throw new Error('active set');
  s = await f.sessions.replaceExercise(s.id, step.exercise.id, alternative.id, step.set.id);
  assert.deepEqual(s.performances[0], performed); assert.deepEqual(s.rests[0], completedRest); assert.deepEqual(await planned(f.training, f.workout.id), plannedBefore);
  const passed = s.sets.find(item => item.skippedAt)!; assert.equal(passed.sessionExerciseId, f.session.exercises[0]!.id);
  assert.deepEqual(passed.targets, f.session.sets[2]!.targets);
  const replaced = selectSessionStep(s); assert.equal(replaced.phase, 'set'); if (replaced.phase !== 'set') throw new Error('replacement');
  assert.equal(replaced.exercise.sourceCatalogExerciseId, alternative.id); assert.equal(replaced.exercise.weightMode, 'per_hand');
  assert.equal(replaced.set.targets.targetWeightKg, null); assert.equal(replaced.set.loadRule?.suspended, true);
  assert.deepEqual(replaced.set.originalTargets, f.session.sets[1]!.originalTargets);
  s = await f.sessions.validateSet(s.id, replaced.set.id, { weightKg: 20, reps: 10, rir: null });
  while (selectSessionStep(s).phase !== 'ready_to_finish') {
    const next = selectSessionStep(s);
    if (next.phase === 'rest') s = await f.sessions.completeRest(s.id, next.rest.id);
    else if (next.phase === 'between_sets') s = await f.sessions.advanceAfterSet(s.id, next.performed.id);
    else if (next.phase === 'set') s = await f.sessions.validateSet(s.id, next.set.id, { weightKg: 20, reps: 8, rir: null }, next.set.passageRevision ?? 0);
    else throw new Error('Unexpected session phase');
  }
  s = await f.sessions.finishSession(s.id);
  const reopened = new SqliteDatabase(f.path); t.after(() => reopened.close()); await initializeDatabase(reopened);
  const saved = await new SessionRepository(reopened, f.id, f.now).getSession(s.id); assert.deepEqual(saved, s);
  const summary = summarizeSession(s); assert.ok(summary.exercises.some(item => item.exercise.name === source.name)); assert.ok(summary.exercises.some(item => item.exercise.name === alternative.name));
});
test('renaming a custom exercise keeps its ID and earlier execution snapshot unchanged', async t => {
  const f = await fixture(t), custom = await f.training.createCustomExercise({ name: 'Personnel', muscleGroup: 'Dos', equipment: 'Barre', weightMode: 'total', instructions: 'Repère initial' });
  let captured = await f.sessions.replaceExercise(f.session.id, f.session.exercises[0]!.id, custom.id, f.session.sets[0]!.id);
  captured = await f.sessions.validateSet(captured.id, captured.sets[0]!.id, { weightKg: 20, reps: 8, rir: null });
  const before = await f.sessions.getSession(f.session.id);
  assert.ok(before!.exercises.some(item => item.sourceCatalogExerciseId === custom.id && item.instructions === 'Repère initial'));
  const edited = await f.training.updateCustomExercise(custom.id, { name: 'Personnel renommé', muscleGroup: 'Dos', equipment: 'Haltères', weightMode: 'per_hand', instructions: 'Mes consignes personnelles enrichies' });
  assert.equal(edited.id, custom.id); assert.equal(edited.instructions, 'Mes consignes personnelles enrichies'); assert.equal(exerciseGuide(edited), undefined);
  assert.deepEqual(await f.sessions.getSession(f.session.id), before);
});
test('personal export remains complete schema v8/format 1 and includes custom instructions without writes', async t => {
  const f = await fixture(t); const custom = await f.training.createCustomExercise({ name: 'Personnel', muscleGroup: 'Dos', equipment: 'Poulie', weightMode: 'total', instructions: 'Mes repères de placement' });
  await f.sessions.skipSet(f.session.id, f.session.sets[2]!.id, 0);
  const before = await snapshot(f.db), reader = new SqliteDatabase(f.path); t.after(() => reader.close()); let json = '';
  await writePersonalExport(reader, chunk => { json += chunk; }, { appVersion: '0.1.0' }); const file = JSON.parse(json);
  assert.equal(file.sqliteSchemaVersion, 8); assert.equal(file.formatVersion, 1); assert.equal(file.restorationAvailableInExporter, false);
  assert.equal(file.tables.exercise_catalog.rows.find((item: { id: string }) => item.id === custom.id).instructions, custom.instructions);
  assert.equal(Object.keys(file.tables).length, EXPORT_TABLES.length); assert.deepEqual(await snapshot(f.db), before);
});
