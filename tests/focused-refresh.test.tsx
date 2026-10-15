import { afterEach, beforeEach, expect, jest, test } from '@jest/globals';
import { act, cleanup, fireEvent, render } from '@testing-library/react-native';
import { useCallback } from 'react';
import { AppState, Text, View } from 'react-native';
import ProgramScreen from '../app/programs/[id]/index';
import WorkoutsScreen from '../app/programs/[id]/workouts/index';
import { NotFoundError } from '../src/db/repository';
import { TrainingNotFoundError, type TrainingRepository } from '../src/db/trainingRepository';
import type { HistoryRepository } from '../src/db/historyRepository';
import type { HistoryOverview as Overview } from '../src/domain/history';
import type { Program, WorkoutTemplate } from '../src/domain/models';
import type { ExerciseCatalogItem, SetTemplate, WorkoutExercise } from '../src/domain/training';
import { LoadState, RefreshNotice, useFocusedData } from '../src/features/programs/shared';
import { WorkoutOverview } from '../src/features/training/WorkoutOverview';
import { ExerciseOverview } from '../src/features/training/ExerciseOverview';
import { SetEditor } from '../src/features/training/SetEditor';
import { HistoryOverview } from '../src/features/history/HistoryOverview';
import { useLogbook } from '../src/store/LogbookProvider';
import { useTraining } from '../src/store/TrainingProvider';

let mockFocused = true;
let mockParams = { id: 'a' };
jest.mock('expo-router', () => {
  const React = require('react') as typeof import('react');
  return {
    router: { push: jest.fn(), replace: jest.fn(), back: jest.fn(), dismissTo: jest.fn(), canGoBack: () => true },
    useLocalSearchParams: () => mockParams,
    useFocusEffect: (effect: () => void | (() => void)) => React.useEffect(() => {
      if (mockFocused) return effect();
    }, [effect, mockFocused]),
  };
});
jest.mock('../src/store/LogbookProvider', () => ({ useLogbook: jest.fn() }));
jest.mock('../src/store/TrainingProvider', () => ({ useTraining: jest.fn() }));
jest.mock('../src/store/SessionProvider', () => ({ useSessions: () => mockSessions }));
jest.mock('../src/features/sessions/ResumeSessionCard', () => ({ useActiveSession: () => ({ data: null, loading: false, error: null }) }));
jest.mock('@expo/vector-icons', () => ({ Ionicons: () => null }));
jest.mock('react-native-safe-area-context', () => jest.requireActual<{ default: typeof import('react-native-safe-area-context') }>('react-native-safe-area-context/jest/mock').default);

const stamp = '2026-10-16T12:00:00.000Z';
const program: Program = { id: 'a', name: 'Programme A', description: '', sportType: 'musculation', workoutCount: 1, createdAt: stamp, updatedAt: stamp };
const workout: WorkoutTemplate = { id: 'w', programId: 'a', name: 'Séance A', notes: '', sortOrder: 0, createdAt: stamp, updatedAt: stamp };
const catalog: ExerciseCatalogItem = { id: 'bar', name: 'Développé barre', muscleGroup: 'Pectoraux', equipment: 'Barre', weightMode: 'total', instructions: '', isCustom: false, createdAt: stamp, updatedAt: stamp };
const exercise: WorkoutExercise = { id: 'we', workoutTemplateId: 'w', exerciseId: 'bar', exercise: catalog, sortOrder: 0, notes: '', createdAt: stamp, updatedAt: stamp };
const series: SetTemplate = { id: 'set', workoutExerciseId: 'we', sortOrder: 0, kind: 'work', label: '', notes: '', repsMin: 8, repsMax: 8, targetWeightKg: 60, targetRir: 2, restAfterSec: 60, createdAt: stamp, updatedAt: stamp };
const store = {
  getProgram: jest.fn<(id: string) => Promise<Program | null>>(),
  getWorkout: jest.fn<(id: string) => Promise<WorkoutTemplate | null>>(),
  listWorkouts: jest.fn<(id: string) => Promise<WorkoutTemplate[]>>(),
  deleteProgram: jest.fn(),
};
const training = {
  listWorkoutExercises: jest.fn<TrainingRepository['listWorkoutExercises']>(),
  getWorkoutExercise: jest.fn<TrainingRepository['getWorkoutExercise']>(),
  listSets: jest.fn<TrainingRepository['listSets']>(), getSet: jest.fn<TrainingRepository['getSet']>(),
  reorderWorkoutExercises: jest.fn<TrainingRepository['reorderWorkoutExercises']>(),
};
const mockSessions = { history: { overview: jest.fn<HistoryRepository['overview']>() } };
const emptyOverview: Overview = { stats: { sessionCount: 0, durationMs: 0, performedSetCount: 0, loggedTonnageKg: null, chargedSetCount: 0, unchargedSetCount: 0 }, previous: null, programs: [], sessions: [], points: [], page: 0, pageCount: 0 };
function deferred<T>() {
  let resolve!: (value: T) => void, reject!: (error: Error) => void;
  const promise = new Promise<T>((done, fail) => { resolve = done; reject = fail; });
  return { promise, resolve, reject };
}
function refocus(rerender: () => void) {
  mockFocused = false; rerender(); mockFocused = true; rerender();
}
const readItem = jest.fn<(id: string) => Promise<string | null>>();
const renderSnapshot = jest.fn<(id: string, value: string | null) => void>();
function Harness({ id = 'a' }: { id?: string }) {
  const result = useFocusedData(useCallback(() => readItem(id), [id]));
  renderSnapshot(id, result.data);
  return <View><RefreshNotice {...result} />{result.loading || result.error || result.data === null
    ? <LoadState loading={result.loading} error={result.error} retry={result.retry} />
    : <Text>{result.data}</Text>}</View>;
}
beforeEach(() => {
  jest.resetAllMocks(); mockFocused = true; mockParams = { id: 'a' };
  jest.spyOn(AppState, 'addEventListener').mockImplementation(() => ({ remove: jest.fn() }));
  store.getProgram.mockResolvedValue(program); store.getWorkout.mockResolvedValue(workout); store.listWorkouts.mockResolvedValue([workout]);
  training.listWorkoutExercises.mockResolvedValue([exercise]); training.listSets.mockResolvedValue([series]);
  training.getWorkoutExercise.mockResolvedValue(exercise); training.getSet.mockResolvedValue(series);
  jest.mocked(useLogbook).mockReturnValue(store as unknown as ReturnType<typeof useLogbook>);
  jest.mocked(useTraining).mockReturnValue(training as unknown as TrainingRepository);
  readItem.mockResolvedValue('Résultat A');
  mockSessions.history.overview.mockResolvedValue(emptyOverview);
});
afterEach(() => { cleanup(); jest.useRealTimers(); jest.restoreAllMocks(); });

test('first program load shows a contained loading card without invented name or session count', async () => {
  const pending = deferred<Program | null>(); store.getProgram.mockReturnValueOnce(pending.promise);
  const view = render(<ProgramScreen />);
  expect(view.getByText('Votre programme')).toBeTruthy(); expect(view.getByRole('progressbar', { name: 'Chargement' })).toBeTruthy();
  expect(view.queryByText('Programme A')).toBeNull(); expect(view.queryByRole('button', { name: 'Voir les séances' })).toBeNull();
  await act(async () => { pending.resolve(program); await pending.promise; });
  expect(view.getByText('Programme A')).toBeTruthy(); expect(view.queryByText('Chargement…')).toBeNull();
});
test('return from a program editor retains content and mounted buttons until the renamed program arrives', async () => {
  const view = render(<ProgramScreen />); await view.findByText('Programme A');
  const button = view.getByRole('button', { name: 'Voir les séances' });
  const pending = deferred<Program | null>(); store.getProgram.mockReturnValueOnce(pending.promise);
  refocus(() => view.rerender(<ProgramScreen />));
  expect(view.getByText('Programme A')).toBeTruthy(); expect(view.getByRole('button', { name: 'Voir les séances' })).toBe(button);
  expect(view.queryByText('Chargement…')).toBeNull(); expect(store.getProgram).toHaveBeenCalledTimes(2);
  await act(async () => { pending.resolve({ ...program, name: 'Programme modifié', workoutCount: 2 }); await pending.promise; });
  expect(view.getByText('Programme modifié')).toBeTruthy(); expect(view.queryByText('Programme A')).toBeNull(); expect(view.getByText('2')).toBeTruthy();
});
test('workout list keeps its cards on return and reflects additions, edits and deletions only after the read', async () => {
  const view = render(<WorkoutsScreen />); await view.findByText('Séance A');
  const pending = deferred<WorkoutTemplate[]>(); store.listWorkouts.mockReturnValueOnce(pending.promise);
  refocus(() => view.rerender(<WorkoutsScreen />)); await act(async () => {});
  expect(view.getByRole('button', { name: 'Ouvrir la séance Séance A' })).toBeTruthy(); expect(view.queryByText('Chargement…')).toBeNull();
  await act(async () => { pending.resolve([{ ...workout, id: 'w2', name: 'Séance B' }]); await pending.promise; });
  expect(view.queryByText('Séance A')).toBeNull(); expect(view.getByText('Séance B')).toBeTruthy();
  store.listWorkouts.mockResolvedValueOnce([]); refocus(() => view.rerender(<WorkoutsScreen />));
  await view.findByText('Votre programme prend forme'); expect(view.queryByText('Séance B')).toBeNull();
});
test('program A is never rendered under the identifier of program B, including before the new read resolves', async () => {
  const view = render(<ProgramScreen />); await view.findByText('Programme A');
  const pending = deferred<Program | null>(); store.getProgram.mockReturnValueOnce(pending.promise);
  mockParams = { id: 'b' }; view.rerender(<ProgramScreen />);
  expect(view.queryByText('Programme A')).toBeNull(); expect(view.getByText('Chargement…')).toBeTruthy();
  await act(async () => { pending.resolve({ ...program, id: 'b', name: 'Programme B' }); await pending.promise; });
  expect(view.getByText('Programme B')).toBeTruthy();
});
test.each(['resolve', 'reject'] as const)('late %s from an old identity cannot replace the current snapshot or its status', async outcome => {
  const older = deferred<string | null>(); readItem.mockReturnValueOnce(older.promise).mockResolvedValueOnce('Résultat B');
  const view = render(<Harness />); view.rerender(<Harness id="b" />); await view.findByText('Résultat B');
  await act(async () => { if (outcome === 'resolve') older.resolve('Ancien A'); else older.reject(new Error('Ancien échec A')); });
  expect(view.getByText('Résultat B')).toBeTruthy(); expect(view.queryByText('Ancien A')).toBeNull();
  expect(renderSnapshot.mock.calls.some(([id, value]) => id === 'b' && value !== null && value !== 'Résultat B')).toBe(false);
  expect(view.queryByRole('button', { name: 'Données non à jour, réessayer' })).toBeNull();
});
test('overlapping reads across rapid refocus ignore the older response even for the same identifier', async () => {
  const view = render(<Harness />); await view.findByText('Résultat A');
  const older = deferred<string | null>(), newest = deferred<string | null>();
  readItem.mockReturnValueOnce(older.promise).mockReturnValueOnce(newest.promise);
  refocus(() => view.rerender(<Harness />)); refocus(() => view.rerender(<Harness />));
  expect(view.getByText('Résultat A')).toBeTruthy(); expect(view.queryByText('Chargement…')).toBeNull();
  await act(async () => { newest.resolve('Récent'); await newest.promise; });
  await act(async () => { older.resolve('Dépassé'); await older.promise; });
  expect(view.getByText('Récent')).toBeTruthy(); expect(view.queryByText('Dépassé')).toBeNull();
});
test('refresh errors retain a valid program; rapid retries keep content and the warning until success', async () => {
  const view = render(<ProgramScreen />); await view.findByText('Programme A');
  store.getProgram.mockRejectedValueOnce(new Error('Lecture impossible')); refocus(() => view.rerender(<ProgramScreen />));
  await view.findByText('Données non à jour · Réessayer'); expect(view.getByText('Programme A')).toBeTruthy();
  expect(view.queryByText('Chargement impossible')).toBeNull();
  const pending = deferred<Program | null>(); store.getProgram.mockReturnValueOnce(pending.promise);
  const retry = view.getByRole('button', { name: 'Données non à jour, réessayer' }); fireEvent.press(retry); fireEvent.press(retry);
  expect(store.getProgram).toHaveBeenCalledTimes(3); expect(view.getByText('Données non à jour · Réessayer')).toBeTruthy();
  expect(view.getByRole('button', { name: 'Voir les séances' })).toBeTruthy(); expect(view.queryByText('Chargement…')).toBeNull();
  await act(async () => { pending.resolve(program); await pending.promise; });
  expect(view.queryByText('Données non à jour · Réessayer')).toBeNull();
});
test('first-load failure offers a real error and retry without pretending the program exists', async () => {
  store.getProgram.mockRejectedValueOnce(new Error('Lecture initiale impossible'));
  const view = render(<ProgramScreen />); await view.findByText('Lecture initiale impossible');
  expect(view.queryByRole('button', { name: 'Voir les séances' })).toBeNull();
  fireEvent.press(view.getByRole('button', { name: 'Réessayer' })); await view.findByText('Programme A');
});
test('confirmed deletion evicts the snapshot and a subsequent storage failure never resurrects it', async () => {
  const view = render(<ProgramScreen />); await view.findByText('Programme A');
  store.getProgram.mockResolvedValueOnce(null); refocus(() => view.rerender(<ProgramScreen />)); await view.findByText('Introuvable');
  expect(view.queryByText('Programme A')).toBeNull(); expect(view.queryByRole('button', { name: 'Modifier le programme' })).toBeNull();
  store.getProgram.mockRejectedValueOnce(new Error('Lecture impossible')); refocus(() => view.rerender(<ProgramScreen />));
  await view.findByText('Chargement impossible'); expect(view.queryByText('Programme A')).toBeNull();
});
test.each([new NotFoundError('program'), new TrainingNotFoundError('exercise')])('typed absence %s is not treated as an ordinary stale-data error', async failure => {
  const view = render(<Harness />); await view.findByText('Résultat A');
  readItem.mockRejectedValueOnce(failure); refocus(() => view.rerender(<Harness />)); await view.findByText('Introuvable');
  expect(view.queryByText('Résultat A')).toBeNull(); expect(view.queryByText('Données non à jour · Réessayer')).toBeNull();
});
test('a confirmed empty workout list remains a valid result when its refresh fails', async () => {
  store.listWorkouts.mockResolvedValue([]); const view = render(<WorkoutsScreen />); await view.findByText('Votre programme prend forme');
  store.listWorkouts.mockRejectedValueOnce(new Error('Lecture impossible')); refocus(() => view.rerender(<WorkoutsScreen />));
  await view.findByText('Données non à jour · Réessayer'); expect(view.getByText('Votre programme prend forme')).toBeTruthy();
  expect(view.getByRole('button', { name: 'Ajouter une séance' })).toBeTruthy();
});
test('workout configuration uses the real plan hook and keeps targets and primary actions mounted while refreshing sets', async () => {
  const view = render(<WorkoutOverview programId="a" workoutId="w" />); await view.findByText('Repos après cette série : 60 s');
  const finish = view.getByRole('button', { name: 'Terminer la configuration' });
  const pending = deferred<SetTemplate[]>(); training.listSets.mockReturnValueOnce(pending.promise);
  refocus(() => view.rerender(<WorkoutOverview programId="a" workoutId="w" />)); await act(async () => {});
  expect(view.getByRole('button', { name: 'Terminer la configuration' })).toBe(finish);
  expect(view.getByRole('button', { name: 'Démarrer la séance' })).toBeTruthy(); expect(view.getByText('Repos après cette série : 60 s')).toBeTruthy();
  expect(view.queryByText('Chargement…')).toBeNull();
  await act(async () => { pending.resolve([{ ...series, restAfterSec: 120 }]); await pending.promise; });
  expect(view.getByText('Repos après cette série : 120 s')).toBeTruthy(); expect(view.queryByText('Repos après cette série : 60 s')).toBeNull();
});
test('changing the plan to a different program cannot show the old workout or accept mismatched ownership', async () => {
  const view = render(<WorkoutOverview programId="a" workoutId="w" />); await view.findByText('1. Développé barre');
  store.getProgram.mockResolvedValueOnce({ ...program, id: 'b', name: 'Programme B' });
  view.rerender(<WorkoutOverview programId="b" workoutId="w" />); expect(view.queryByText('1. Développé barre')).toBeNull();
  await view.findByText('Introuvable'); expect(view.queryByRole('button', { name: 'Démarrer la séance' })).toBeNull();
});
test('a deleted exercise removes the configuration and its actions after a plan refresh', async () => {
  const view = render(<ExerciseOverview programId="a" workoutId="w" exerciseInstanceId="we" />); await view.findByText('Repos après cette série : 60 s');
  training.listWorkoutExercises.mockResolvedValueOnce([]);
  refocus(() => view.rerender(<ExerciseOverview programId="a" workoutId="w" exerciseInstanceId="we" />)); await view.findByText('Introuvable');
  expect(view.queryByRole('button', { name: 'Terminer' })).toBeNull(); expect(view.queryByText('Repos après cette série : 60 s')).toBeNull();
});
test('reordering cannot reuse the previous order while refreshed configuration is still pending', async () => {
  training.listWorkoutExercises.mockResolvedValue([exercise, { ...exercise, id: 'we2', exercise: { ...catalog, id: 'curl', name: 'Curl' } }]);
  training.listSets.mockImplementation(async id => [{ ...series, id: `set-${id}`, workoutExerciseId: id }]);
  training.reorderWorkoutExercises.mockResolvedValue(undefined);
  const view = render(<WorkoutOverview programId="a" workoutId="w" />); await view.findByText('2. Curl');
  const pending = deferred<SetTemplate[]>(); training.listSets.mockReturnValueOnce(pending.promise);
  refocus(() => view.rerender(<WorkoutOverview programId="a" workoutId="w" />)); await act(async () => {});
  fireEvent.press(view.getByRole('button', { name: 'Descendre Développé barre' }));
  expect(training.reorderWorkoutExercises).not.toHaveBeenCalled(); expect(view.getByText('2. Curl')).toBeTruthy();
  await act(async () => { pending.resolve([series]); await pending.promise; });
  await act(async () => { fireEvent.press(view.getByRole('button', { name: 'Descendre Développé barre' })); });
  expect(training.reorderWorkoutExercises).toHaveBeenCalledWith('w', ['we2', 'we']);
});
test('a series form keeps the same field and its unsaved text while reading and on refresh failure', async () => {
  const props = { mode: 'edit' as const, programId: 'a', workoutId: 'w', exerciseInstanceId: 'we', setId: 'set' };
  const view = render(<SetEditor {...props} />); const field = await view.findByLabelText('Étiquette (facultative)');
  fireEvent.changeText(field, 'Mon repère non enregistré');
  const pending = deferred<SetTemplate>(); training.getSet.mockReturnValueOnce(pending.promise);
  refocus(() => view.rerender(<SetEditor {...props} />)); await act(async () => {});
  expect(view.getByLabelText('Étiquette (facultative)')).toBe(field); expect(field.props.value).toBe('Mon repère non enregistré');
  await act(async () => { pending.reject(new Error('Lecture impossible')); });
  expect(view.getByText('Données non à jour · Réessayer')).toBeTruthy(); expect(field.props.value).toBe('Mon repère non enregistré');
});
test('a history return later the same day refreshes once without discarding content just because the Date object changed', async () => {
  jest.useFakeTimers(); jest.setSystemTime(new Date(2026, 9, 16, 12));
  const view = render(<HistoryOverview />); await act(async () => {});
  const title = view.getByText('Votre histoire commence ici');
  const pending = deferred<Overview>(); mockSessions.history.overview.mockReturnValueOnce(pending.promise);
  jest.setSystemTime(new Date(2026, 9, 16, 12, 1));
  refocus(() => view.rerender(<HistoryOverview />));
  expect(view.getByText('Votre histoire commence ici')).toBe(title); expect(view.queryByText('Chargement…')).toBeNull();
  expect(mockSessions.history.overview).toHaveBeenCalledTimes(2);
  await act(async () => { pending.resolve(emptyOverview); await pending.promise; });
});
test('foreground still refreshes history silently within the same day', async () => {
  jest.useFakeTimers(); jest.setSystemTime(new Date(2026, 9, 16, 12));
  const view = render(<HistoryOverview />); await act(async () => {});
  const pending = deferred<Overview>(); mockSessions.history.overview.mockReturnValueOnce(pending.promise);
  jest.setSystemTime(new Date(2026, 9, 16, 12, 1));
  const listeners = jest.mocked(AppState.addEventListener).mock.calls.map(call => call[1]);
  act(() => listeners.forEach(listener => listener('active')));
  expect(view.getByText('Votre histoire commence ici')).toBeTruthy(); expect(view.queryByText('Chargement…')).toBeNull();
  expect(mockSessions.history.overview).toHaveBeenCalledTimes(2);
  await act(async () => { pending.resolve(emptyOverview); await pending.promise; });
});
