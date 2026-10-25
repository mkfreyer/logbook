import { afterEach, beforeEach, expect, jest, test } from '@jest/globals';
import { act, cleanup, fireEvent, render, waitFor } from '@testing-library/react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { Alert } from 'react-native';
import { INITIAL_EXERCISES } from '../src/db/exerciseCatalog';
import { EXERCISE_GUIDES } from '../src/data/exerciseGuides';
import type { TrainingRepository } from '../src/db/trainingRepository';
import { TrainingNotFoundError } from '../src/db/trainingRepository';
import type { SessionRepository } from '../src/db/sessionRepository';
import type { WorkoutSession } from '../src/domain/session';
import type { ExerciseCatalogItem } from '../src/domain/training';
import { ExerciseDetail } from '../src/features/exercises/ExerciseDetail';
import { ExerciseCatalog } from '../src/features/exercises/ExerciseCatalog';
import { SessionScreen } from '../src/features/sessions/SessionScreen';
import { SessionReplacement } from '../src/features/sessions/SessionReplacement';
import { useTraining } from '../src/store/TrainingProvider';
import { useSessions } from '../src/store/SessionProvider';
import ExerciseDetailRoute from '../app/exercises/[exerciseId]';
import ReplaceRoute from '../app/sessions/[sessionId]/replace';

const mockEffects = new Set<() => void | (() => void)>(), mockBlurs = new Set<() => void>();
jest.mock('expo-router', () => {
  const React = require('react') as typeof import('react');
  return { router: { push: jest.fn(), dismissTo: jest.fn(), back: jest.fn(), canGoBack: jest.fn(), replace: jest.fn() }, useLocalSearchParams: jest.fn(),
    useFocusEffect: (effect: () => void | (() => void)) => React.useEffect(() => {
      mockEffects.add(effect); const blur = effect(); if (blur) mockBlurs.add(blur);
      return () => { mockEffects.delete(effect); if (blur) { mockBlurs.delete(blur); blur(); } };
    }, [effect]) };
});
jest.mock('../src/store/TrainingProvider', () => ({ useTraining: jest.fn() }));
jest.mock('../src/store/SessionProvider', () => ({ useSessions: jest.fn() }));
jest.mock('@expo/vector-icons', () => ({ Ionicons: () => null }));
jest.mock('react-native-safe-area-context', () => jest.requireActual<{ default: typeof import('react-native-safe-area-context') }>('react-native-safe-area-context/jest/mock').default);

const stamp = '2026-10-17T10:00:00.000Z';
const catalog: ExerciseCatalogItem[] = INITIAL_EXERCISES.map(item => ({ ...item, instructions: item.instructions ?? '', isCustom: false, createdAt: stamp, updatedAt: stamp }));
const source = catalog[0]!, alternative = catalog[1]!;
const custom: ExerciseCatalogItem = { ...source, id: 'custom', name: 'Mon mouvement', isCustom: true, instructions: '' };
const exercise = { id: 'se', sessionId: 's', sourceWorkoutExerciseId: 'we', sourceCatalogExerciseId: source.id, name: source.name, muscleGroup: source.muscleGroup,
  equipment: source.equipment, instructions: source.instructions, weightMode: source.weightMode, sortOrder: 0, plannedOrder: 0, notes: '' };
const targets = { repsMin: 8, repsMax: 10, targetWeightKg: 80, targetRir: 2, restAfterSec: 60 };
const set = { id: 'set', sessionId: 's', sessionExerciseId: 'se', sourceSetTemplateId: 'st', sortOrder: 0, seriesIndex: 0, label: '', kind: 'work' as const,
  notes: '', targets, originalTargets: targets };
const session: WorkoutSession = { id: 's', sourceProgramId: 'p', sourceWorkoutTemplateId: 'w', programName: 'Programme', workoutName: 'Séance', status: 'active',
  startedAt: stamp, finishedAt: null, exercises: [exercise], sets: [set], performances: [], rests: [] };
const context = { sessionId: 's', exerciseId: 'se', setId: 'set' };
const training = { getCatalogExercise: jest.fn<TrainingRepository['getCatalogExercise']>(), listCatalog: jest.fn<TrainingRepository['listCatalog']>() };
const sessions = { history: { previousPerformance: jest.fn<() => Promise<null>>() }, validateSet: jest.fn<SessionRepository['validateSet']>(), getSession: jest.fn<SessionRepository['getSession']>(), replaceExercise: jest.fn<SessionRepository['replaceExercise']>() };
function deferred<T>() { let resolve!: (value: T) => void; const promise = new Promise<T>(done => { resolve = done; }); return { promise, resolve }; }
async function pressAlert(name: string) { const button = jest.mocked(Alert.alert).mock.lastCall?.[2]?.find(item => item.text === name); expect(button).toBeTruthy(); await act(() => button?.onPress?.()); }
async function requestReplacement(view: Awaited<ReturnType<typeof render>>) {
  await fireEvent.press(await view.findByRole('button', { name: 'Remplacer pour cette séance' }));
  await waitFor(() => expect(Alert.alert).toHaveBeenCalled());
}

beforeEach(() => {
  jest.resetAllMocks(); mockEffects.clear(); mockBlurs.clear();
  jest.spyOn(Alert, 'alert').mockImplementation(() => undefined);
  training.getCatalogExercise.mockImplementation(async id => [...catalog, custom].find(item => item.id === id)!);
  sessions.history.previousPerformance.mockResolvedValue(null);
  training.listCatalog.mockResolvedValue([...catalog, custom]); sessions.getSession.mockResolvedValue(session); sessions.replaceExercise.mockResolvedValue(session);
  jest.mocked(useTraining).mockReturnValue(training as unknown as TrainingRepository);
  jest.mocked(useSessions).mockReturnValue(sessions as unknown as SessionRepository);
});
afterEach(async () => { await cleanup(); jest.restoreAllMocks(); });

test('the three accessible tabs show specific offline content and retain existing instructions', async () => {
  const view = await render(<ExerciseDetail exerciseId={source.id} />); await view.findByText(source.instructions);
  expect(view.getByRole('tab', { name: 'Description', selected: true })).toBeTruthy();
  expect(view.getByText(EXERCISE_GUIDES[source.id]!.start)).toBeTruthy();
  await fireEvent.press(view.getByRole('tab', { name: 'Conseils' })); expect(view.getByText(`1. ${EXERCISE_GUIDES[source.id]!.tips[0]}`)).toBeTruthy();
  expect(view.getByText(EXERCISE_GUIDES[source.id]!.load)).toBeTruthy();
  await fireEvent.press(view.getByRole('tab', { name: 'Alternatives' })); await view.findByRole('button', { name: `Fiche de ${alternative.name}` });
  expect(view.getByText('Charge par haltère (kg)')).toBeTruthy(); expect(view.queryByRole('button', { name: 'Remplacer pour cette séance' })).toBeNull();
  expect(sessions.getSession).not.toHaveBeenCalled();
});
test('custom sheet has honest empty advice/alternatives and keeps edit access with a stable ID', async () => {
  const view = await render(<ExerciseDetail exerciseId={custom.id} />); await view.findByText('Aucune instruction renseignée pour cet exercice.');
  await fireEvent.press(view.getByRole('tab', { name: 'Conseils' })); expect(view.getByText('Aucun conseil spécifique renseigné')).toBeTruthy();
  await fireEvent.press(view.getByRole('tab', { name: 'Alternatives' })); await view.findByText('Aucune alternative renseignée');
  await fireEvent.press(view.getByRole('button', { name: 'Modifier mon exercice personnalisé' }));
  expect(router.push).toHaveBeenCalledWith({ pathname: '/exercises/[exerciseId]/edit', params: { exerciseId: custom.id } });
});
test('optional help explains targets, RIR, series, units and skip without a blocking dialog', async () => {
  const view = await render(<ExerciseDetail exerciseId={source.id} initialTab="advice" />); await view.findByRole('button', { name: 'Comprendre les termes d’entraînement' });
  expect(view.queryByText('Passer ou supprimer ?')).toBeNull(); await fireEvent.press(view.getByRole('button', { name: 'Comprendre les termes d’entraînement' }));
  for (const title of ['Cible et résultat', 'RIR', 'Types de séries', 'Comment noter la charge ?', 'Passer ou supprimer ?']) expect(view.getByText(title)).toBeTruthy();
  await fireEvent.press(view.getByRole('button', { name: 'Fermer l’aide entraînement' })); expect(view.queryByText('Passer ou supprimer ?')).toBeNull();
  expect(Alert.alert).not.toHaveBeenCalled(); expect(sessions.replaceExercise).not.toHaveBeenCalled();
});
test('an unavailable alternative is omitted rather than manufactured', async () => {
  training.listCatalog.mockResolvedValue([source]);
  const view = await render(<ExerciseDetail exerciseId={source.id} initialTab="alternatives" />); await view.findByText('Aucune alternative renseignée');
  expect(view.queryByText(alternative.name)).toBeNull();
});
test('opening an alternative from the global library only consults its sheet', async () => {
  const view = await render(<ExerciseDetail exerciseId={source.id} initialTab="alternatives" />);
  await fireEvent.press(await view.findByRole('button', { name: `Fiche de ${alternative.name}` }));
  expect(router.push).toHaveBeenCalledWith({ pathname: '/exercises/[exerciseId]', params: { exerciseId: alternative.id } });
  expect(sessions.replaceExercise).not.toHaveBeenCalled(); expect(sessions.getSession).not.toHaveBeenCalled();
});
test('accent insensitive multiword catalog search still opens only a sheet', async () => {
  const view = await render(<ExerciseCatalog />); await view.findByRole('button', { name: `Fiche de ${source.name}` });
  await fireEvent.changeText(view.getByLabelText('Rechercher dans la bibliothèque'), 'DEVELOPPE INCLINE');
  expect(view.queryByRole('button', { name: `Fiche de ${source.name}` })).toBeNull();
  await fireEvent.press(view.getByRole('button', { name: `Fiche de ${alternative.name}` })); expect(router.push).toHaveBeenCalledWith({ pathname: '/exercises/[exerciseId]', params: { exerciseId: alternative.id } });
});
test('replacement search opens current alternatives or a target sheet with the full origin context', async () => {
  const view = await render(<SessionReplacement {...context} />);
  await fireEvent.press(await view.findByRole('button', { name: 'Fiche et alternatives de l’exercice' }));
  expect(router.push).toHaveBeenLastCalledWith({ pathname: '/exercises/[exerciseId]', params: { exerciseId: source.id, tab: 'alternatives', replacementSessionId: 's', replacementExerciseId: 'se', replacementSetId: 'set' } });
  await fireEvent.press(view.getByRole('button', { name: `Fiche de ${custom.name}` }));
  expect(router.push).toHaveBeenLastCalledWith({ pathname: '/exercises/[exerciseId]', params: { exerciseId: custom.id, replacementSessionId: 's', replacementExerciseId: 'se', replacementSetId: 'set' } });
  expect(sessions.replaceExercise).not.toHaveBeenCalled();
});
test('context survives navigation from current alternatives to their sheet', async () => {
  const view = await render(<ExerciseDetail exerciseId={source.id} initialTab="alternatives" replacementContext={context} />);
  await fireEvent.press(await view.findByRole('button', { name: `Fiche de ${alternative.name}` }));
  expect(router.push).toHaveBeenCalledWith({ pathname: '/exercises/[exerciseId]', params: { exerciseId: alternative.id, replacementSessionId: 's', replacementExerciseId: 'se', replacementSetId: 'set' } });
});
test('cancelled replacement never writes, even if an old confirmation callback is replayed', async () => {
  const view = await render(<ExerciseDetail exerciseId={alternative.id} replacementContext={context} />); await requestReplacement(view);
  await pressAlert('Annuler'); await pressAlert('Remplacer'); await act(async () => {});
  expect(sessions.replaceExercise).not.toHaveBeenCalled(); expect(router.dismissTo).not.toHaveBeenCalled();
});
test('confirmed replacement shares the existing repository and prevents repeated taps/decisions', async () => {
  const pending = deferred<WorkoutSession>(); sessions.replaceExercise.mockReturnValueOnce(pending.promise);
  const view = await render(<ExerciseDetail exerciseId={alternative.id} replacementContext={context} />);
  const button = await view.findByRole('button', { name: 'Remplacer pour cette séance' }); await fireEvent.press(button); await fireEvent.press(button);
  await waitFor(() => expect(Alert.alert).toHaveBeenCalledTimes(1));
  expect(jest.mocked(Alert.alert).mock.lastCall![1]).toContain('charges cibles restantes seront effacées');
  await pressAlert('Remplacer'); await pressAlert('Remplacer'); await waitFor(() => expect(sessions.replaceExercise).toHaveBeenCalledTimes(1));
  expect(sessions.replaceExercise).toHaveBeenCalledWith('s', 'se', alternative.id, 'set'); expect(router.dismissTo).not.toHaveBeenCalled();
  await act(async () => { pending.resolve(session); await pending.promise; });
  expect(router.dismissTo).toHaveBeenCalledWith({ pathname: '/sessions/[sessionId]', params: { sessionId: 's' } });
});
const invalidSessions: [string, WorkoutSession | null][] = [
  ['completed session', { ...session, status: 'completed' as const, finishedAt: stamp }],
  ['missing session', null],
  ['changed active set', { ...session, sets: [{ ...set, id: 'different' }] }],
  ['skipped series', { ...session, sets: [{ ...set, skippedAt: stamp, passageRevision: 1 }] }],
];
for (const [name, value] of invalidSessions) test(`invalid replacement context: ${name}`, async () => {
  sessions.getSession.mockResolvedValue(value);
  const view = await render(<ExerciseDetail exerciseId={alternative.id} replacementContext={context} />);
  await view.findByText(/Ce remplacement n’est plus disponible/); expect(view.queryByRole('button', { name: 'Remplacer pour cette séance' })).toBeNull();
  expect(view.getByRole('button', { name: 'Revenir à la séance' })).toBeTruthy(); expect(sessions.replaceExercise).not.toHaveBeenCalled();
});
test('a context changed while the alert is open cannot mutate the session', async () => {
  const view = await render(<ExerciseDetail exerciseId={alternative.id} replacementContext={context} />); await requestReplacement(view);
  sessions.getSession.mockResolvedValue({ ...session, status: 'completed', finishedAt: stamp }); await pressAlert('Remplacer');
  await view.findByText('La série active a changé. Revenez à la séance avant de remplacer son exercice.'); expect(sessions.replaceExercise).not.toHaveBeenCalled();
});
test('a completed performance with a running rest blocks replacement without closing the rest', async () => {
  const performance = { id: 'perf', sessionId: 's', sessionSetId: 'set', performedAt: stamp, sortOrder: 0, weightKg: 70, reps: 8, rir: 2, advancedAt: null };
  sessions.getSession.mockResolvedValue({ ...session, sets: [set, { ...set, id: 'next', sortOrder: 1 }], performances: [performance], rests: [{ id: 'rest', sessionId: 's', performedSetId: 'perf', plannedSeconds: 60, startedAt: stamp, endedAt: null, chronologicalMs: null, activeMs: null, pauses: [] }] });
  const view = await render(<ExerciseDetail exerciseId={alternative.id} replacementContext={context} />);
  await view.findByText(/Ce remplacement n’est plus disponible/); expect(sessions.replaceExercise).not.toHaveBeenCalled();
});
test('a repository failure preserves the sheet and offers retry and return', async () => {
  sessions.replaceExercise.mockRejectedValueOnce(new Error('Écriture impossible'));
  const view = await render(<ExerciseDetail exerciseId={alternative.id} replacementContext={context} />); await requestReplacement(view); await pressAlert('Remplacer');
  await view.findByText('Écriture impossible'); expect(router.dismissTo).not.toHaveBeenCalled(); expect(view.getByRole('button', { name: 'Actualiser le remplacement' })).toBeTruthy();
});
test('a late confirmation after leaving the sheet is ignored', async () => {
  const view = await render(<ExerciseDetail exerciseId={alternative.id} replacementContext={context} />); await requestReplacement(view);
  await act(() => mockBlurs.forEach(blur => blur())); await pressAlert('Remplacer'); await act(async () => {}); expect(sessions.replaceExercise).not.toHaveBeenCalled();
});
test('refocus silently preserves sheet content and selected tab while SQLite is pending', async () => {
  const view = await render(<ExerciseDetail exerciseId={source.id} />); await view.findByText(source.instructions);
  await fireEvent.press(view.getByRole('tab', { name: 'Conseils' })); const pending = deferred<ExerciseCatalogItem>(); training.getCatalogExercise.mockReturnValueOnce(pending.promise);
  await act(() => { mockBlurs.forEach(blur => blur()); mockEffects.forEach(effect => effect()); });
  expect(view.getByRole('tab', { name: 'Conseils', selected: true })).toBeTruthy(); expect(view.queryByText('Chargement…')).toBeNull();
  expect(view.getByText(EXERCISE_GUIDES[source.id]!.load)).toBeTruthy(); await act(async () => { pending.resolve(source); await pending.promise; });
});
test('a changed exercise ID never renders the former exercise or its guide as the new one', async () => {
  const view = await render(<ExerciseDetail exerciseId={source.id} />); await view.findByText(source.instructions);
  const pending = deferred<ExerciseCatalogItem>(); training.getCatalogExercise.mockReturnValueOnce(pending.promise);
  await view.rerender(<ExerciseDetail exerciseId={alternative.id} />); expect(view.queryByText(source.instructions)).toBeNull();
  await act(async () => { pending.resolve(alternative); await pending.promise; }); expect(view.getByText(alternative.instructions)).toBeTruthy();
});
test('Expo Router restores replacement context from a full sheet URL', async () => {
  jest.mocked(useLocalSearchParams).mockReturnValue({ exerciseId: alternative.id, replacementSessionId: 's', replacementExerciseId: 'se', replacementSetId: 'set' });
  const view = await render(<ExerciseDetailRoute />); await view.findByRole('button', { name: 'Remplacer pour cette séance' }); expect(sessions.getSession).toHaveBeenCalledWith('s');
});
test('a missing catalog exercise is a real not-found state and cannot offer replacement', async () => {
  training.getCatalogExercise.mockRejectedValueOnce(new TrainingNotFoundError('catalog'));
  const view = await render(<ExerciseDetail exerciseId="unavailable" replacementContext={context} />);
  await view.findByText('Introuvable'); expect(view.queryByRole('button', { name: 'Remplacer pour cette séance' })).toBeNull();
  expect(sessions.getSession).not.toHaveBeenCalled();
});
test('custom exercise editing carries the training context without modifying the session', async () => {
  const view = await render(<ExerciseDetail exerciseId={custom.id} replacementContext={context} />);
  await fireEvent.press(await view.findByRole('button', { name: 'Modifier mon exercice personnalisé' }));
  expect(router.push).toHaveBeenCalledWith({ pathname: '/exercises/[exerciseId]/edit', params: { exerciseId: custom.id, replacementSessionId: 's', replacementExerciseId: 'se', replacementSetId: 'set' } });
  expect(sessions.replaceExercise).not.toHaveBeenCalled();
});
test('a context becoming invalid during preflight is rejected before opening a confirmation', async () => {
  const view = await render(<ExerciseDetail exerciseId={alternative.id} replacementContext={context} />);
  const button = await view.findByRole('button', { name: 'Remplacer pour cette séance' });
  sessions.getSession.mockResolvedValue({ ...session, sets: [{ ...set, skippedAt: stamp, passageRevision: 1 }] }); await fireEvent.press(button);
  await view.findByText(/Ce remplacement n’est plus disponible. Revenez à la séance/);
  expect(Alert.alert).not.toHaveBeenCalled(); expect(sessions.replaceExercise).not.toHaveBeenCalled();
});
test('changing replacement-route identifiers ignores a delayed preflight from the former context', async () => {
  jest.mocked(useLocalSearchParams).mockReturnValue({ sessionId: 's', exerciseId: 'se', setId: 'set' });
  const view = await render(<ReplaceRoute />); const button = await view.findByRole('button', { name: `Remplacer par ${alternative.name}` });
  const pending = deferred<WorkoutSession | null>(); sessions.getSession.mockReturnValueOnce(pending.promise); await fireEvent.press(button);
  jest.mocked(useLocalSearchParams).mockReturnValue({ sessionId: 's', exerciseId: 'se', setId: 'other-set' }); await view.rerender(<ReplaceRoute />);
  await view.findByText(/Revenez à la série active pour remplacer/);
  await act(async () => { pending.resolve(session); await pending.promise; });
  expect(Alert.alert).not.toHaveBeenCalled(); expect(sessions.replaceExercise).not.toHaveBeenCalled();
});

for (const replace of [false, true]) test(`direct sheet → tabs → alternative → ${replace ? 'confirmed replacement' : 'back without replacement'} preserves training correctly`, async () => {
  const trainingView = await render(<SessionScreen sessionId="s" />);
  await fireEvent.changeText(await trainingView.findByLabelText('Charge réelle (kg)'), '62,5');
  await fireEvent.changeText(trainingView.getByLabelText('Répétitions réelles'), '9'); await fireEvent.changeText(trainingView.getByLabelText('RIR réel'), '2');
  await fireEvent.press(trainingView.getByRole('button', { name: `Voir la fiche de ${source.name}` }));
  await waitFor(() => expect(router.push).toHaveBeenCalledWith({ pathname: '/exercises/[exerciseId]', params: { exerciseId: source.id, replacementSessionId: 's', replacementExerciseId: 'se', replacementSetId: 'set' } }));
  await act(() => mockBlurs.forEach(blur => blur()));
  const sheet = await render(<ExerciseDetail exerciseId={source.id} replacementContext={context} />);
  await sheet.findByRole('tab', { name: 'Description', selected: true });
  await fireEvent.press(sheet.getByRole('tab', { name: 'Conseils' })); expect(sheet.getByText(EXERCISE_GUIDES[source.id]!.load)).toBeTruthy();
  await fireEvent.press(sheet.getByRole('tab', { name: 'Alternatives' }));
  await fireEvent.press(await sheet.findByRole('button', { name: `Fiche de ${alternative.name}` }));
  expect(router.push).toHaveBeenLastCalledWith({ pathname: '/exercises/[exerciseId]', params: { exerciseId: alternative.id, replacementSessionId: 's', replacementExerciseId: 'se', replacementSetId: 'set' } });
  await act(() => mockBlurs.forEach(blur => blur()));
  const target = await render(<ExerciseDetail exerciseId={alternative.id} replacementContext={context} />);
  await target.findByRole('button', { name: 'Remplacer pour cette séance' });
  if (replace) {
    await requestReplacement(target); expect(sessions.replaceExercise).not.toHaveBeenCalled();
    const updated: WorkoutSession = { ...session, exercises: [{ ...exercise, id: 'replaced', sourceCatalogExerciseId: alternative.id, name: alternative.name, weightMode: 'per_hand' }],
      sets: [{ ...set, sessionExerciseId: 'replaced', targets: { ...targets, targetWeightKg: null } }] };
    sessions.replaceExercise.mockImplementationOnce(async () => { sessions.getSession.mockResolvedValue(updated); return updated; }); await pressAlert('Remplacer');
    await waitFor(() => expect(sessions.replaceExercise).toHaveBeenCalledWith('s', 'se', alternative.id, 'set'));
    await waitFor(() => expect(router.dismissTo).toHaveBeenCalledWith({ pathname: '/sessions/[sessionId]', params: { sessionId: 's' } }));
  } else {
    await fireEvent.press(target.getByRole('button', { name: 'Revenir à la séance' }));
    expect(router.dismissTo).toHaveBeenCalledWith({ pathname: '/sessions/[sessionId]', params: { sessionId: 's' } });
    expect(sessions.replaceExercise).not.toHaveBeenCalled();
  }
  await target.unmount(); await sheet.unmount(); await act(() => mockEffects.forEach(effect => effect()));
  await trainingView.findByRole('button', { name: `Voir la fiche de ${replace ? alternative.name : source.name}` });
  expect(trainingView.getByLabelText('Charge réelle (kg)').props.value).toBe(replace ? '' : '62,5');
  expect(trainingView.getByLabelText('Répétitions réelles').props.value).toBe(replace ? '' : '9');
  expect(trainingView.getByLabelText('RIR réel').props.value).toBe(replace ? '' : '2');
  expect(sessions.validateSet).not.toHaveBeenCalled();
});
