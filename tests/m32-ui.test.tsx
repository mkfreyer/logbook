import { afterEach, beforeEach, expect, jest, test } from '@jest/globals';
import { act, cleanup, fireEvent, render, waitFor } from '@testing-library/react-native';
import { router } from 'expo-router';
import { AppState, Text, View } from 'react-native';
import { useSessions } from '../src/store/SessionProvider';
import { useTraining } from '../src/store/TrainingProvider';
import type { SessionRepository } from '../src/db/sessionRepository';
import type { HistoryRepository } from '../src/db/historyRepository';
import type { TrainingRepository } from '../src/db/trainingRepository';
import type { WorkoutSession } from '../src/domain/session';
import { localWeek } from '../src/domain/activity';
import type { HomeActivity, PreviousPerformance } from '../src/domain/activity';
import type { ExerciseCatalogItem } from '../src/domain/training';
import { SessionScreen } from '../src/features/sessions/SessionScreen';
import { PreviousPerformanceCard } from '../src/features/sessions/PreviousPerformanceCard';
import { useHomeActivity } from '../src/features/home/useHomeActivity';
import { HomeActivityCards } from '../src/features/home/HomeActivityCards';
import { ExerciseDetail } from '../src/features/exercises/ExerciseDetail';
import { ExerciseCatalog } from '../src/features/exercises/ExerciseCatalog';
import { CatalogExerciseEditor } from '../src/features/exercises/CatalogExerciseEditor';
import { ExerciseLibrary } from '../src/features/training/ExerciseLibrary';
import { useWorkoutPlan } from '../src/features/training/useWorkoutPlan';

const mockFocusCleanups = new Set<() => void>();
jest.mock('expo-router', () => {
  const React = require('react') as typeof import('react');
  return { router: { push: jest.fn(), replace: jest.fn(), dismissTo: jest.fn(), back: jest.fn(), canGoBack: jest.fn() },
    useFocusEffect: (effect: () => void | (() => void)) => React.useEffect(() => {
      const close = effect(); if (!close) return;
      mockFocusCleanups.add(close); return () => { mockFocusCleanups.delete(close); close(); };
    }, [effect]) };
});
jest.mock('../src/store/SessionProvider', () => ({ useSessions: jest.fn() }));
jest.mock('../src/store/TrainingProvider', () => ({ useTraining: jest.fn() }));
jest.mock('../src/features/training/useWorkoutPlan', () => ({ useWorkoutPlan: jest.fn() }));
jest.mock('@expo/vector-icons', () => ({ Ionicons: () => null }));
jest.mock('react-native-safe-area-context', () => jest.requireActual<{ default: typeof import('react-native-safe-area-context') }>('react-native-safe-area-context/jest/mock').default);

const stamp = '2026-10-15T12:00:00.000Z';
const exercise = { id: 'e', sessionId: 's', sourceWorkoutExerciseId: 'we', sourceCatalogExerciseId: 'bar', sortOrder: 0, plannedOrder: 0,
  name: 'Développé barre', muscleGroup: 'Pectoraux', equipment: 'Barre', instructions: '', notes: '', weightMode: 'total' as const };
const targets = { repsMin: 8, repsMax: 10, targetWeightKg: 80, targetRir: 2, restAfterSec: 60 };
const series = { id: 'set', sessionId: 's', sessionExerciseId: 'e', sourceSetTemplateId: 'st', sortOrder: 0, seriesIndex: 0, kind: 'work' as const,
  label: '', notes: '', originalTargets: targets, targets };
const session: WorkoutSession = { id: 's', sourceProgramId: 'p', sourceWorkoutTemplateId: 'w', programName: 'Mon programme', workoutName: 'Ma séance', status: 'active',
  startedAt: stamp, finishedAt: null, exercises: [exercise], sets: [series], performances: [], rests: [] };
const previous: PreviousPerformance = { comparison: 'same_series', performance: { id: 'old', sessionId: 'completed', sessionExerciseId: 'old-ex', exerciseName: exercise.name,
  workoutName: 'Autre séance', programName: 'Programme supprimé', finishedAt: '2026-10-10T12:00:00.000Z', performedAt: '2026-10-10T11:00:00.000Z',
  seriesIndex: 0, sortOrder: 2, label: '', kind: 'work', weightKg: 60, reps: 10, rir: 2, weightMode: 'total' } };
const custom: ExerciseCatalogItem = { id: 'custom', name: 'Mon développé', muscleGroup: 'Pectoraux', equipment: 'Haltères', instructions: 'Mon repère personnel.',
  weightMode: 'per_hand', isCustom: true, createdAt: stamp, updatedAt: stamp };
const history = { previousPerformance: jest.fn<HistoryRepository['previousPerformance']>(), homeActivity: jest.fn<HistoryRepository['homeActivity']>() };
const completions = new Set<() => void>();
const repo = { history, subscribeCompleted: jest.fn<SessionRepository['subscribeCompleted']>(), getSession: jest.fn<SessionRepository['getSession']>(), validateSet: jest.fn<SessionRepository['validateSet']>() };
const training = { listCatalog: jest.fn<TrainingRepository['listCatalog']>(), getCatalogExercise: jest.fn<TrainingRepository['getCatalogExercise']>(),
  addWorkoutExercise: jest.fn<TrainingRepository['addWorkoutExercise']>(),
  createCustomExercise: jest.fn<TrainingRepository['createCustomExercise']>(), updateCustomExercise: jest.fn<TrainingRepository['updateCustomExercise']>() };
function activity(count = 2, total = 7): HomeActivity {
  const days = localWeek(new Date()).days; days[0]!.count = count;
  return { sessionCount: count, totalCompleted: total, days };
}
function HomeHarness({ enabled = true }: { enabled?: boolean }) {
  const state = useHomeActivity(enabled);
  return <View><Text testID="local-date">{state.now.toString()}</Text><HomeActivityCards activity={state} /></View>;
}
function deferred<T>() {
  let resolve!: (value: T) => void, reject!: (error: Error) => void;
  const promise = new Promise<T>((done, fail) => { resolve = done; reject = fail; });
  return { promise, resolve, reject };
}

beforeEach(() => {
  jest.resetAllMocks(); completions.clear(); mockFocusCleanups.clear();
  jest.spyOn(AppState, 'addEventListener').mockImplementation(() => ({ remove: jest.fn() }));
  history.previousPerformance.mockResolvedValue(previous); history.homeActivity.mockImplementation(async () => activity());
  repo.getSession.mockResolvedValue(session); repo.validateSet.mockResolvedValue(session);
  repo.subscribeCompleted.mockImplementation(listener => { completions.add(listener); return () => { completions.delete(listener); }; });
  training.listCatalog.mockResolvedValue([custom, { ...custom, id: 'bar', name: 'Développé barre', equipment: 'Barre', isCustom: false }]);
  training.getCatalogExercise.mockResolvedValue(custom); training.createCustomExercise.mockResolvedValue(custom); training.updateCustomExercise.mockResolvedValue({ ...custom, name: 'Renommé' });
  training.addWorkoutExercise.mockResolvedValue({ id: 'occ', workoutTemplateId: 'w', exerciseId: 'custom', sortOrder: 0, notes: '', exercise: custom, createdAt: stamp, updatedAt: stamp });
  jest.mocked(useWorkoutPlan).mockReturnValue({ loading: false, error: null, retry: jest.fn(), training,
    data: { program: { id: 'p' }, workout: { id: 'w', name: 'Ma séance' }, exercise: null } } as unknown as ReturnType<typeof useWorkoutPlan>);
  jest.mocked(useSessions).mockReturnValue(repo as unknown as SessionRepository);
  jest.mocked(useTraining).mockReturnValue(training as unknown as TrainingRepository);
});
afterEach(() => { cleanup(); jest.useRealTimers(); jest.restoreAllMocks(); });

test('a single active series shows the previous real result without filling any actual field', async () => {
  const view = render(<SessionScreen sessionId="s" />); await view.findByText('60 kg × 10 répétitions · RIR 2');
  expect(view.getByText(/Même type et position de série/)).toBeTruthy();
  for (const label of ['Charge réelle (kg)', 'Répétitions réelles', 'RIR réel']) expect(view.getByLabelText(label).props.value).toBe('');
  expect(view.getAllByLabelText('Répétitions réelles')).toHaveLength(1); expect(view.getByRole('button', { name: 'Valider la série' })).toBeTruthy();
  expect(repo.validateSet).not.toHaveBeenCalled(); expect(history.previousPerformance).toHaveBeenCalledWith('s', 'set');
});
test('reading the previous result never replaces a partially typed current result', async () => {
  const pending = deferred<PreviousPerformance | null>(); history.previousPerformance.mockReturnValue(pending.promise);
  const view = render(<SessionScreen sessionId="s" />); const input = await view.findByLabelText('Charge réelle (kg)');
  fireEvent.changeText(input, '65'); fireEvent.changeText(view.getByLabelText('Répétitions réelles'), '8');
  await act(async () => { pending.resolve(previous); await pending.promise; });
  expect(view.getByLabelText('Charge réelle (kg)').props.value).toBe('65'); expect(view.getByLabelText('Répétitions réelles').props.value).toBe('8');
});
test('less exact comparison is labeled and missing kg/RIR are never turned into zero', async () => {
  history.previousPerformance.mockResolvedValue({ comparison: 'exercise', performance: { ...previous.performance, weightKg: null, rir: null, kind: 'back_off' } });
  const view = render(<PreviousPerformanceCard sessionId="s" series={series} exercise={exercise} />);
  await view.findByText('Charge non renseignée × 10 répétitions'); expect(view.getByText(/Dernière performance de cet exercice · autre type/)).toBeTruthy();
  expect(view.queryByText(/RIR 0|0 kg/)).toBeNull();
});
test('per-hand load and explicit zero RIR retain their captured meaning', async () => {
  history.previousPerformance.mockResolvedValue({ comparison: 'same_type', performance: { ...previous.performance, weightMode: 'per_hand', weightKg: 20, rir: 0 } });
  const view = render(<PreviousPerformanceCard sessionId="s" series={series} exercise={exercise} />);
  await view.findByText('20 kg / haltère × 10 répétitions · RIR 0'); expect(view.getByText(/Même type · autre position/)).toBeTruthy();
});
test('no prior comparison gives a neutral message and lookup failure offers retry', async () => {
  history.previousPerformance.mockRejectedValueOnce(new Error('Stockage inaccessible'));
  const view = render(<PreviousPerformanceCard sessionId="s" series={series} exercise={exercise} />);
  fireEvent.press(await view.findByRole('button', { name: 'Réessayer la dernière performance' }));
  await view.findByText('DERNIÈRE FOIS'); history.previousPerformance.mockResolvedValue(null);
  view.rerender(<PreviousPerformanceCard sessionId="s" series={{ ...series, id: 'new' }} exercise={exercise} />);
  await view.findByText('Pas encore de série comparable enregistrée.'); expect(view.queryByText('DERNIÈRE FOIS')).toBeNull();
});
test('replacement with the same set ID discards a late result from the original exercise', async () => {
  const pending = deferred<PreviousPerformance | null>(); history.previousPerformance.mockReturnValueOnce(pending.promise).mockResolvedValue(null);
  const view = render(<PreviousPerformanceCard sessionId="s" series={series} exercise={exercise} />);
  view.rerender(<PreviousPerformanceCard sessionId="s" series={series} exercise={{ ...exercise, id: 'alt', sourceCatalogExerciseId: 'dumbbell', weightMode: 'per_hand' }} />);
  await view.findByText('Pas encore de série comparable enregistrée.');
  await act(async () => { pending.resolve(previous); await pending.promise; });
  expect(view.queryByText(/60 kg/)).toBeNull(); expect(history.previousPerformance).toHaveBeenCalledTimes(2);
});
test('a lookup error after switching exercise exposes retry instead of stale results or endless loading', async () => {
  const view = render(<PreviousPerformanceCard sessionId="s" series={series} exercise={exercise} />);
  await view.findByText(/60 kg/); history.previousPerformance.mockRejectedValueOnce(new Error('Lecture impossible'));
  view.rerender(<PreviousPerformanceCard sessionId="s" series={series} exercise={{ ...exercise, sourceCatalogExerciseId: 'alternate' }} />);
  await view.findByRole('button', { name: 'Réessayer la dernière performance' }); expect(view.queryByText(/60 kg/)).toBeNull();
});
test('home shows actual weekly count/day markers and a neutral progression link', async () => {
  const view = render(<HomeHarness />); await view.findByText('séances terminées');
  expect(view.getByLabelText('Séances terminées cette semaine').props.children).toBe(2);
  expect(view.getByLabelText('Séances terminées cette semaine').props.accessibilityValue.text).toBe('2');
  expect(view.getAllByLabelText(/ : .*séance/)).toHaveLength(7); expect(view.queryByText(/\+\d+%/)).toBeNull();
  fireEvent.press(view.getByRole('button', { name: 'Consulter ma progression par exercice' })); expect(router.push).toHaveBeenCalledWith('/history/exercises');
});
test('first home load has a discreet placeholder without claiming zero sessions or fabricated day counts', async () => {
  const pending = deferred<HomeActivity>(); history.homeActivity.mockReturnValueOnce(pending.promise);
  const view = render(<HomeHarness />);
  expect(view.getByText('Chargement…')).toBeTruthy();
  expect(view.getByLabelText('Séances terminées cette semaine').props.accessibilityValue.text).toBe('Chargement');
  expect(view.queryByText('Aucune séance cette semaine.')).toBeNull(); expect(view.queryAllByLabelText(/ : .*séance/)).toHaveLength(0);
  await act(async () => { pending.resolve(activity()); await pending.promise; });
  expect(view.queryByText('Chargement…')).toBeNull(); expect(view.getAllByLabelText(/ : .*séance/)).toHaveLength(7);
});
test('returning to Home keeps the valid count, caption and seven markers throughout a deferred read', async () => {
  const view = render(<HomeHarness />); await view.findByText('séances terminées');
  const markers = view.getAllByLabelText(/ : .*séance/).map(day => day.props.accessibilityLabel);
  const pending = deferred<HomeActivity>(); history.homeActivity.mockReturnValueOnce(pending.promise);
  view.rerender(<HomeHarness enabled={false} />); view.rerender(<HomeHarness />);
  expect(history.homeActivity).toHaveBeenCalledTimes(2);
  expect(view.getByLabelText('Séances terminées cette semaine').props.children).toBe(2);
  expect(view.getByText('séances terminées')).toBeTruthy();
  expect(view.getAllByLabelText(/ : .*séance/).map(day => day.props.accessibilityLabel)).toEqual(markers);
  expect(view.queryByText(/Actualisation|Chargement|Lecture en cours/)).toBeNull(); expect(view.queryByText('…')).toBeNull();
  await act(async () => { pending.resolve(activity(3)); await pending.promise; });
  expect(view.getByLabelText('Séances terminées cette semaine').props.children).toBe(3);
});
test('a known empty week and first-session caption also stay stable on foreground refresh', async () => {
  history.homeActivity.mockResolvedValueOnce(activity(0, 0));
  const view = render(<HomeHarness />); await view.findByText('Après votre première séance terminée.');
  const pending = deferred<HomeActivity>(); history.homeActivity.mockReturnValueOnce(pending.promise);
  const listener = jest.mocked(AppState.addEventListener).mock.calls[0]![1];
  act(() => listener('background')); act(() => listener('active'));
  expect(view.getByText('Après votre première séance terminée.')).toBeTruthy(); expect(view.getByText('Aucune séance cette semaine.')).toBeTruthy();
  expect(view.getByLabelText('Séances terminées cette semaine').props.children).toBe(0); expect(view.getAllByLabelText(/ : .*séance/)).toHaveLength(7);
  await act(async () => { pending.resolve(activity(1, 1)); await pending.promise; });
  expect(view.getByLabelText('Séances terminées cette semaine').props.children).toBe(1);
});
test('rapid refreshes accept only the newest result and ignore late failures without flashing loading', async () => {
  const view = render(<HomeHarness />); await view.findByText('séances terminées');
  const older = deferred<HomeActivity>(), failing = deferred<HomeActivity>(), newest = deferred<HomeActivity>();
  history.homeActivity.mockReturnValueOnce(older.promise).mockReturnValueOnce(failing.promise).mockReturnValueOnce(newest.promise);
  act(() => completions.forEach(listener => listener()));
  act(() => completions.forEach(listener => listener()));
  act(() => completions.forEach(listener => listener()));
  expect(view.getByLabelText('Séances terminées cette semaine').props.children).toBe(2); expect(view.queryByText('…')).toBeNull();
  await act(async () => { newest.resolve(activity(5)); await newest.promise; });
  await act(async () => { older.resolve(activity(1)); failing.reject(new Error('Ancienne lecture en échec')); });
  expect(view.getByLabelText('Séances terminées cette semaine').props.children).toBe(5);
  expect(view.queryByRole('button', { name: 'Actualiser les statistiques' })).toBeNull(); expect(history.homeActivity).toHaveBeenCalledTimes(4);
});
test('refresh failure preserves valid statistics and retry keeps the stale notice until a successful replacement', async () => {
  const view = render(<HomeHarness />); await view.findByText('séances terminées');
  history.homeActivity.mockRejectedValueOnce(new Error('Lecture impossible'));
  act(() => completions.forEach(listener => listener())); await view.findByText('Données non à jour · Réessayer');
  expect(view.getByLabelText('Séances terminées cette semaine').props.children).toBe(2); expect(view.getAllByLabelText(/ : .*séance/)).toHaveLength(7);
  const pending = deferred<HomeActivity>(); history.homeActivity.mockReturnValueOnce(pending.promise);
  const retry = view.getByRole('button', { name: 'Actualiser les statistiques' }); fireEvent.press(retry); fireEvent.press(retry);
  expect(history.homeActivity).toHaveBeenCalledTimes(3); expect(view.getByText('Données non à jour · Réessayer')).toBeTruthy();
  expect(view.getByLabelText('Séances terminées cette semaine').props.children).toBe(2); expect(view.queryByText('…')).toBeNull();
  await act(async () => { pending.resolve(activity(4)); await pending.promise; });
  expect(view.getByLabelText('Séances terminées cette semaine').props.children).toBe(4); expect(view.queryByText('Données non à jour · Réessayer')).toBeNull();
});
test('an older success cannot clear the newest failure or replace the last valid statistics', async () => {
  const view = render(<HomeHarness />); await view.findByText('séances terminées');
  const older = deferred<HomeActivity>(), latest = deferred<HomeActivity>();
  history.homeActivity.mockReturnValueOnce(older.promise).mockReturnValueOnce(latest.promise);
  act(() => completions.forEach(listener => listener())); act(() => completions.forEach(listener => listener()));
  await act(async () => { latest.reject(new Error('Lecture récente impossible')); });
  await act(async () => { older.resolve(activity(9)); await older.promise; });
  expect(view.getByLabelText('Séances terminées cette semaine').props.children).toBe(2);
  expect(view.getByText('Données non à jour · Réessayer')).toBeTruthy();
});
test('Sunday midnight dates the cached week instead of calling its count current while Monday is loading', async () => {
  jest.useFakeTimers(); jest.setSystemTime(new Date(2026, 9, 18, 23, 59, 59));
  const view = render(<HomeHarness />); await act(async () => {});
  const pending = deferred<HomeActivity>(); history.homeActivity.mockReturnValueOnce(pending.promise);
  await act(async () => { jest.advanceTimersByTime(1000); });
  expect(history.homeActivity.mock.lastCall![0]!.getDay()).toBe(1);
  expect(view.queryByLabelText('Séances terminées cette semaine')).toBeNull(); expect(view.getByText('Semaine du 12/10')).toBeTruthy();
  expect(view.getByLabelText('Séances terminées la semaine du 2026-10-12').props.children).toBe(2);
  expect(view.getAllByLabelText(/ : .*séance/)).toHaveLength(7); expect(view.queryAllByLabelText(/aujourd’hui/)).toHaveLength(0);
  await act(async () => { pending.resolve(activity(0)); await pending.promise; });
  expect(view.getByLabelText('Séances terminées cette semaine').props.children).toBe(0);
  expect(view.queryByText('Semaine du 12/10')).toBeNull(); expect(view.getByLabelText('2026-10-19 : 0 séance terminée, aujourd’hui')).toBeTruthy();
});
test('a week-change read failure retains explicitly dated data and retries the new week', async () => {
  jest.useFakeTimers(); jest.setSystemTime(new Date(2026, 9, 18, 23, 59, 59));
  const view = render(<HomeHarness />); await act(async () => {});
  history.homeActivity.mockRejectedValueOnce(new Error('Lecture impossible'));
  await act(async () => { jest.advanceTimersByTime(1000); });
  expect(view.getByText('Données non à jour · Réessayer')).toBeTruthy();
  expect(view.getByLabelText('Séances terminées la semaine du 2026-10-12').props.children).toBe(2);
  expect(view.queryByText('Cette semaine')).toBeNull();
  fireEvent.press(view.getByRole('button', { name: 'Actualiser les statistiques' })); await act(async () => {});
  expect(view.getByText('Cette semaine')).toBeTruthy(); expect(view.queryByText('Données non à jour · Réessayer')).toBeNull();
});
test('a new day in the same week updates today without hiding cached counts or markers', async () => {
  jest.useFakeTimers(); jest.setSystemTime(new Date(2026, 9, 15, 23, 59, 59));
  const view = render(<HomeHarness />); await act(async () => {});
  expect(view.getByLabelText('2026-10-15 : 0 séance terminée, aujourd’hui')).toBeTruthy();
  const pending = deferred<HomeActivity>(); history.homeActivity.mockReturnValueOnce(pending.promise);
  await act(async () => { jest.advanceTimersByTime(1000); });
  expect(view.getByLabelText('2026-10-16 : 0 séance terminée, aujourd’hui')).toBeTruthy();
  expect(view.getByLabelText('Séances terminées cette semaine').props.children).toBe(2); expect(view.getAllByLabelText(/ : .*séance/)).toHaveLength(7);
  expect(view.queryByText(/Lecture en cours|Chargement/)).toBeNull();
  await act(async () => { pending.resolve(activity()); await pending.promise; });
});
test('a hidden Home returning weeks later labels the saved period before its new read completes', async () => {
  jest.useFakeTimers(); jest.setSystemTime(new Date(2026, 9, 15, 12));
  const view = render(<HomeHarness />); await act(async () => {}); view.rerender(<HomeHarness enabled={false} />);
  jest.setSystemTime(new Date(2026, 10, 2, 12));
  const pending = deferred<HomeActivity>(); history.homeActivity.mockReturnValueOnce(pending.promise);
  view.rerender(<HomeHarness />);
  expect(view.queryByText('Cette semaine')).toBeNull(); expect(view.getByText('Semaine du 12/10')).toBeTruthy();
  expect(view.queryAllByLabelText(/aujourd’hui/)).toHaveLength(0);
  await act(async () => { pending.resolve(activity(1)); await pending.promise; });
  expect(view.getByLabelText('Séances terminées cette semaine').props.children).toBe(1);
});
test('a read crossing midnight cannot call Sunday statistics current even before the midnight callback runs', async () => {
  jest.useFakeTimers(); jest.setSystemTime(new Date(2026, 9, 18, 23, 59, 59));
  const sundayData = activity(), pending = deferred<HomeActivity>(); history.homeActivity.mockReturnValueOnce(pending.promise);
  const view = render(<HomeHarness />);
  // A suspended JS timer may run later than the SQLite response on resume.
  jest.setSystemTime(new Date(2026, 9, 19, 0, 0, 1));
  await act(async () => { pending.resolve(sundayData); await pending.promise; });
  expect(history.homeActivity).toHaveBeenCalledTimes(1); expect(view.queryByText('Cette semaine')).toBeNull();
  expect(view.getByLabelText('Séances terminées la semaine du 2026-10-12').props.children).toBe(2);
});
test('empty home is truthful and storage failure never masquerades as an empty week', async () => {
  history.homeActivity.mockRejectedValueOnce(new Error('Lecture impossible'));
  const view = render(<HomeHarness />); fireEvent.press(await view.findByRole('button', { name: 'Actualiser les statistiques' }));
  await view.findByText('séances terminées'); history.homeActivity.mockResolvedValue(activity(0, 0));
  act(() => completions.forEach(listener => listener()));
  await view.findByText('Après votre première séance terminée.'); expect(view.getByText('Aucune séance cette semaine.')).toBeTruthy();
  expect(view.getByLabelText('Séances terminées cette semaine').props.children).toBe(0);
});
test('a committed finish refreshes Home, while ordinary timer time causes no SQLite polling', async () => {
  jest.useFakeTimers(); jest.setSystemTime(new Date(2026, 9, 15, 12));
  const view = render(<HomeHarness />); await act(async () => {}); expect(history.homeActivity).toHaveBeenCalledTimes(1);
  await act(async () => { jest.advanceTimersByTime(5000); }); expect(history.homeActivity).toHaveBeenCalledTimes(1);
  history.homeActivity.mockResolvedValue(activity(3)); act(() => completions.forEach(listener => listener()));
  await act(async () => {}); expect(view.getByLabelText('Séances terminées cette semaine').props.children).toBe(3);
  expect(history.homeActivity).toHaveBeenCalledTimes(2);
});
test('hidden Home performs no statistics reads and unsubscribes when leaving the universe', async () => {
  const view = render(<HomeHarness enabled={false} />); expect(history.homeActivity).not.toHaveBeenCalled(); expect(completions.size).toBe(0);
  view.rerender(<HomeHarness />); await view.findByText('séances terminées'); expect(completions.size).toBe(1);
  view.rerender(<HomeHarness enabled={false} />); const count = history.homeActivity.mock.calls.length;
  act(() => completions.forEach(listener => listener())); expect(history.homeActivity.mock.calls.length).toBe(count); expect(completions.size).toBe(0);
});
test('local Sunday midnight and foreground return recalculate the date and week', async () => {
  jest.useFakeTimers(); jest.setSystemTime(new Date(2026, 9, 18, 23, 59, 59));
  render(<HomeHarness />); await act(async () => {});
  await act(async () => { jest.advanceTimersByTime(1200); });
  expect(history.homeActivity).toHaveBeenCalledTimes(2); expect(history.homeActivity.mock.lastCall![0]!.getDay()).toBe(1);
  const listener = jest.mocked(AppState.addEventListener).mock.calls[0]![1];
  act(() => listener('background')); await act(async () => { jest.advanceTimersByTime(86400000); }); expect(history.homeActivity).toHaveBeenCalledTimes(2);
  act(() => listener('active')); await act(async () => {}); expect(history.homeActivity).toHaveBeenCalledTimes(3);
});
test('late reads after Home is hidden cannot replace a newer visible result', async () => {
  const pending = deferred<HomeActivity>(); history.homeActivity.mockReturnValueOnce(pending.promise).mockResolvedValue(activity(3));
  const view = render(<HomeHarness />); view.rerender(<HomeHarness enabled={false} />); view.rerender(<HomeHarness />);
  await view.findByText('séances terminées'); await act(async () => { pending.resolve(activity(1)); await pending.promise; });
  expect(view.getByLabelText('Séances terminées cette semaine').props.children).toBe(3);
});
test('catalog supports multi-word search without accents and opens a stable exercise reference', async () => {
  const view = render(<ExerciseCatalog />); await view.findByText('Mon développé');
  fireEvent.changeText(view.getByLabelText('Rechercher dans la bibliothèque'), 'developpe HALTERES');
  expect(view.queryByText('Développé barre')).toBeNull(); fireEvent.press(view.getByRole('button', { name: 'Fiche de Mon développé' }));
  expect(router.push).toHaveBeenCalledWith({ pathname: '/exercises/[exerciseId]', params: { exerciseId: 'custom' } });
  expect(training.createCustomExercise).not.toHaveBeenCalled();
});
test('custom exercise detail shows real instructions, load mode, history and edit access', async () => {
  const view = render(<ExerciseDetail exerciseId="custom" />); await view.findByText('Mon repère personnel.');
  expect(view.getByText('Charge par haltère (kg)')).toBeTruthy(); fireEvent.press(view.getByRole('button', { name: 'Voir mes performances' }));
  expect(router.push).toHaveBeenCalledWith({ pathname: '/history/exercises/[exerciseId]', params: { exerciseId: 'custom' } });
  fireEvent.press(view.getByRole('button', { name: 'Modifier mon exercice personnalisé' }));
  expect(router.push).toHaveBeenLastCalledWith({ pathname: '/exercises/[exerciseId]/edit', params: { exerciseId: 'custom' } });
});
test('catalog entry without instructions has an honest empty state and no edit/fictional advice', async () => {
  training.getCatalogExercise.mockResolvedValue({ ...custom, instructions: '', isCustom: false });
  const view = render(<ExerciseDetail exerciseId="custom" />); await view.findByText('Aucune instruction renseignée pour cet exercice.');
  expect(view.queryByRole('button', { name: 'Modifier mon exercice personnalisé' })).toBeNull(); expect(view.queryByText('Conseils')).toBeNull();
});
test('personalized edit keeps its stable ID, saves before returning, and prevents duplicate saves', async () => {
  const pending = deferred<ExerciseCatalogItem>(); training.updateCustomExercise.mockReturnValue(pending.promise);
  const view = render(<CatalogExerciseEditor exerciseId="custom" />); const field = await view.findByLabelText('Nom de l’exercice');
  await waitFor(() => expect(field.props.value).toBe('Mon développé')); fireEvent.changeText(field, 'Renommé');
  fireEvent.press(view.getByRole('button', { name: 'Enregistrer l’exercice' })); fireEvent.press(view.getByRole('button', { name: 'Enregistrer l’exercice' }));
  expect(training.updateCustomExercise).toHaveBeenCalledTimes(1); expect(training.updateCustomExercise).toHaveBeenCalledWith('custom', expect.objectContaining({ name: 'Renommé' }));
  expect(router.dismissTo).not.toHaveBeenCalled(); await act(async () => { pending.resolve({ ...custom, name: 'Renommé' }); await pending.promise; });
  expect(router.dismissTo).toHaveBeenCalledWith({ pathname: '/exercises/[exerciseId]', params: { exerciseId: 'custom' } });
});
test('save errors stay on the personalized form and allow correction', async () => {
  training.updateCustomExercise.mockRejectedValueOnce(new Error('Sauvegarde impossible'));
  const view = render(<CatalogExerciseEditor exerciseId="custom" />); await view.findByLabelText('Nom de l’exercice');
  fireEvent.press(view.getByRole('button', { name: 'Enregistrer l’exercice' })); await view.findByText('Sauvegarde impossible'); expect(router.dismissTo).not.toHaveBeenCalled();
  fireEvent.press(view.getByRole('button', { name: 'Enregistrer l’exercice' })); await waitFor(() => expect(router.dismissTo).toHaveBeenCalledTimes(1));
});
test('standalone creation adds only a catalog reference and opens its real detail after success', async () => {
  const view = render(<CatalogExerciseEditor />); await view.findByLabelText('Nom de l’exercice');
  fireEvent.changeText(view.getByLabelText('Nom de l’exercice'), 'Mon exercice'); fireEvent.changeText(view.getByLabelText('Groupe musculaire'), 'Dos'); fireEvent.changeText(view.getByLabelText('Matériel'), 'Poulie');
  fireEvent.press(view.getByRole('button', { name: 'Créer l’exercice' }));
  await waitFor(() => expect(router.replace).toHaveBeenCalledWith({ pathname: '/exercises/[exerciseId]', params: { exerciseId: 'custom' } }));
  expect(training.createCustomExercise).toHaveBeenCalledTimes(1); expect(training.updateCustomExercise).not.toHaveBeenCalled();
});
test('configuration library info opens the detail without adding; the existing add action remains direct', async () => {
  const view = render(<ExerciseLibrary programId="p" workoutId="w" />);
  fireEvent.press(await view.findByRole('button', { name: 'Fiche de Mon développé' }));
  expect(router.push).toHaveBeenCalledWith({ pathname: '/exercises/[exerciseId]', params: { exerciseId: 'custom' } });
  expect(training.addWorkoutExercise).not.toHaveBeenCalled();
  fireEvent.press(view.getByRole('button', { name: 'Ajouter Mon développé' }));
  await waitFor(() => expect(router.dismissTo).toHaveBeenCalledWith({ pathname: '/programs/[id]/workouts/[workoutId]', params: { id: 'p', workoutId: 'w' } }));
  expect(training.addWorkoutExercise).toHaveBeenCalledWith('w', { exerciseId: 'custom' });
});
test('a direct edit route cannot modify a predefined catalog reference', async () => {
  training.getCatalogExercise.mockResolvedValue({ ...custom, isCustom: false });
  const view = render(<CatalogExerciseEditor exerciseId="custom" />);
  await view.findByText('Seuls vos exercices personnalisés peuvent être modifiés.');
  expect(view.queryByRole('button', { name: 'Enregistrer l’exercice' })).toBeNull(); expect(training.updateCustomExercise).not.toHaveBeenCalled();
});
