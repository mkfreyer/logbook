import assert from 'node:assert/strict';
import { test } from 'node:test';
import type { WorkoutSession } from '../src/domain/session';
import { formatSessionDuration, summarizeSession } from '../src/domain/sessionSummary';

function session(): WorkoutSession {
  const targets = { repsMin: 8, repsMax: 12, targetWeightKg: 999, targetRir: 10, restAfterSec: 60 };
  const exercises = ['total', 'per_hand', 'additional', 'total'].map((mode, index) => ({
    id: `e${index}`, sessionId: 's', sourceWorkoutExerciseId: `source${index}`, sourceCatalogExerciseId: `c${index}`,
    sortOrder: index, name: `Exercice ${index}`, muscleGroup: 'Dos', equipment: 'Salle', instructions: '', notes: '',
    weightMode: mode as 'total' | 'per_hand' | 'additional',
  }));
  const sets = exercises.map((exercise, index) => ({ id: `set${index}`, sessionId: 's', sessionExerciseId: exercise.id,
    sourceSetTemplateId: `planned${index}`, sortOrder: index, seriesIndex: 0, label: '', kind: index === 0 ? 'warmup' as const : 'work' as const,
    notes: '', targets, originalTargets: targets }));
  const performances = [
    { id: 'p2', sessionId: 's', sessionSetId: 'set2', sortOrder: 0, weightKg: null, reps: 12, rir: null, performedAt: '2026-10-14T12:10:00Z', advancedAt: '2026-10-14T12:11:00Z' },
    { id: 'p1', sessionId: 's', sessionSetId: 'set1', sortOrder: 1, weightKg: 10, reps: 8, rir: 0, performedAt: '2026-10-14T12:12:00Z', advancedAt: '2026-10-14T12:13:00Z' },
    { id: 'p0', sessionId: 's', sessionSetId: 'set0', sortOrder: 2, weightKg: 40, reps: 5, rir: 3, performedAt: '2026-10-14T12:14:00Z', advancedAt: '2026-10-14T12:15:00Z' },
  ];
  return { id: 's', sourceWorkoutTemplateId: 'w', sourceProgramId: 'program', workoutName: 'Séance', programName: 'Programme',
    status: 'completed', startedAt: '2026-10-14T12:00:00Z', finishedAt: '2026-10-14T14:03:04Z', exercises, sets, performances, rests: [] };
}

test('summary counts only actual sets, chronological duration including absences, logged kg and provided RIR', () => {
  const summary = summarizeSession(session());
  assert.equal(summary.durationMs, 7384000); assert.equal(summary.performedSetCount, 3);
  assert.equal(summary.loggedTonnageKg, 280); assert.equal(summary.chargedSetCount, 2); assert.equal(summary.unchargedSetCount, 1);
  assert.equal(summary.meanRir, 1.5); assert.equal(summary.rirSetCount, 2);
  assert.deepEqual(summary.tonnageByMode, { total: 200, per_hand: 80, additional: 0 });
  assert.deepEqual(summary.exercises.map(item => item.exercise.id), ['e2', 'e1', 'e0']);
  assert.equal(summary.exercises.some(item => item.exercise.id === 'e3'), false);
});
test('missing weight and RIR remain neutral; provided zero is not missing', () => {
  const value = session(); value.performances = value.performances.map(item => ({ ...item, weightKg: null, rir: null }));
  let summary = summarizeSession(value);
  assert.equal(summary.loggedTonnageKg, null); assert.equal(summary.meanRir, null); assert.equal(summary.rirSetCount, 0);
  value.performances[0] = { ...value.performances[0]!, weightKg: 0, rir: 0 };
  summary = summarizeSession(value);
  assert.equal(summary.loggedTonnageKg, 0); assert.equal(summary.meanRir, 0); assert.equal(summary.chargedSetCount, 1);
});
test('additional weight never invents body mass, per-hand weight is not silently doubled, and warm-ups are included', () => {
  const value = session(); value.performances[0]!.weightKg = 5;
  const summary = summarizeSession(value);
  assert.equal(summary.tonnageByMode.additional, 60); assert.equal(summary.tonnageByMode.per_hand, 80);
  assert.equal(summary.loggedTonnageKg, 340);
});
test('summary uses the actual replacement name and unit, retaining its source without merging identities', () => {
  const value = session(); value.exercises[1]!.name = 'Haltères utilisés';
  value.replacements = [{ id: 'r', sessionId: 's', fromExerciseId: 'e3', toExerciseId: 'e1', activeSetId: 'set1', remainingSetCount: 1, changedAt: value.startedAt }];
  const summary = summarizeSession(value);
  assert.equal(summary.exercises[1]!.exercise.name, 'Haltères utilisés'); assert.equal(summary.exercises[1]!.replacedFrom?.name, 'Exercice 3');
  assert.equal(summary.exercises.some(item => item.exercise.id === 'e3'), false);
});
test('an unfinished session has no final summary; incomplete provenance is reported instead of inventing results', () => {
  const value = session(); value.status = 'active'; value.finishedAt = null;
  assert.throws(() => summarizeSession(value), /après la fin/);
  value.status = 'completed'; value.finishedAt = '2026-10-14T14:00:00Z'; value.sets = [];
  assert.throws(() => summarizeSession(value), /incomplets/);
});
test('chronological duration formats seconds, minutes and long absences clearly', () => {
  assert.equal(formatSessionDuration(9000), '9 s'); assert.equal(formatSessionDuration(61000), '1 min 01 s');
  assert.equal(formatSessionDuration(7384000), '2 h 03 min');
});

test('a chain of temporary alternatives keeps initial program provenance while only performed alternatives appear in the summary', () => {
  const value = session();
  value.replacements = [
    { id: 'r0', sessionId: 's', fromExerciseId: 'e3', toExerciseId: 'e2', activeSetId: 'set2', remainingSetCount: 1, changedAt: value.startedAt },
    { id: 'r1', sessionId: 's', fromExerciseId: 'e2', toExerciseId: 'e1', activeSetId: 'set1', remainingSetCount: 1, changedAt: value.startedAt },
  ];
  const summary = summarizeSession(value);
  assert.equal(summary.exercises.find(item => item.exercise.id === 'e1')!.replacedFrom!.id, 'e3');
  assert.equal(summary.exercises.some(item => item.exercise.id === 'e3'), false);
});

test('invalid times and overflowing arithmetic are reported rather than displayed as fabricated zero or infinite metrics', () => {
  const value = session(); value.finishedAt = 'invalid'; assert.throws(() => summarizeSession(value), /horaires/);
  value.finishedAt = '2026-10-14T11:00:00Z'; assert.throws(() => summarizeSession(value), /horaires/);
  value.finishedAt = '2026-10-14T14:00:00Z'; value.performances[0]!.weightKg = Number.MAX_VALUE;
  assert.throws(() => summarizeSession(value), /plage de calcul/);
});
