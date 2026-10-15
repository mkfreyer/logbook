import { afterEach, beforeEach, expect, jest, test } from '@jest/globals';
import { act, cleanup, fireEvent, render, waitFor } from '@testing-library/react-native';
import { router } from 'expo-router';
import { AppState } from 'react-native';
import type { SessionRepository } from '../src/db/sessionRepository';
import type { HistoryRepository } from '../src/db/historyRepository';
import type { ExerciseHistory as ExerciseData, HistoryOverview as Overview } from '../src/domain/history';
import type { WorkoutSession } from '../src/domain/session';
import { useSessions } from '../src/store/SessionProvider';
import { HistoryOverview } from '../src/features/history/HistoryOverview';
import { ExerciseHistory, ExerciseHistoryIndex } from '../src/features/history/ExerciseHistory';
import { SessionHistory } from '../src/features/history/SessionHistory';
import { ProgressChart } from '../src/features/history/ProgressChart';

jest.mock('expo-router', () => {
  const React = require('react') as typeof import('react');
  return { router: { push: jest.fn(), back: jest.fn(), replace: jest.fn(), dismissTo: jest.fn(), canGoBack: jest.fn() },
    useFocusEffect: (effect: () => void | (() => void)) => React.useEffect(effect, [effect]) };
});
jest.mock('../src/store/SessionProvider', () => ({ useSessions: jest.fn() }));
jest.mock('@expo/vector-icons', () => ({ Ionicons: () => null }));
jest.mock('react-native-safe-area-context', () => jest.requireActual<{ default: typeof import('react-native-safe-area-context') }>('react-native-safe-area-context/jest/mock').default);
const history = { overview: jest.fn<HistoryRepository['overview']>(), exercises: jest.fn<HistoryRepository['exercises']>(), exercise: jest.fn<HistoryRepository['exercise']>() };
const repo = { history, getSession: jest.fn<SessionRepository['getSession']>(), validateSet: jest.fn(), finishSession: jest.fn() };
const empty: Overview = { stats: { sessionCount: 0, durationMs: 0, performedSetCount: 0, loggedTonnageKg: null, chargedSetCount: 0, unchargedSetCount: 0 }, previous: null, programs: [], sessions: [], points: [], page: 0, pageCount: 0 };
const entry = { id: 's1', sourceProgramId: 'p1', sourceWorkoutTemplateId: 'w1', workoutName: 'Haut du corps', programName: 'Mon programme',
  startedAt: '2026-10-01T12:00:00.000Z', finishedAt: '2026-10-01T13:00:00.000Z', durationMs: 3600000, performedSetCount: 2, loggedTonnageKg: 800, chargedSetCount: 2, unchargedSetCount: 0 };
const overview: Overview = { ...empty, stats: { ...empty.stats, sessionCount: 2, durationMs: 7200000, performedSetCount: 4, loggedTonnageKg: 1600, chargedSetCount: 4 },
  sessions: [entry], points: [entry, { ...entry, id: 's2', finishedAt: '2026-10-02T13:00:00.000Z' }], pageCount: 1,
  programs: [{ id: 'p1', name: 'Mon programme', sessionCount: 1, deleted: 1 }, { id: 'p2', name: 'Mon programme', sessionCount: 1, deleted: 0 }] };
const actual = { id: 'perf', sessionId: 's1', sessionExerciseId: 'actual-e', exerciseName: 'Développé haltères', workoutName: entry.workoutName,
  programName: entry.programName, finishedAt: entry.finishedAt, performedAt: entry.finishedAt, sortOrder: 0, seriesIndex: 1, label: 'Top set', kind: 'top_set', weightKg: 20, reps: 10, rir: null, weightMode: 'per_hand' as const };
const exerciseData: ExerciseData = { exercise: { id: 'catalog-alt', name: actual.exerciseName, muscleGroup: 'Pectoraux', equipment: 'Haltères', instructions: '', sessionCount: 2 },
  modes: ['per_hand', 'total'], mode: 'per_hand', sessionCount: 2, lastPerformance: actual,
  visits: [{ sessionId: 's1', finishedAt: entry.finishedAt, workoutName: entry.workoutName, programName: entry.programName, performances: [actual] }],
  points: [{ sessionId: 's1', finishedAt: entry.finishedAt, workoutName: entry.workoutName, representative: actual, loggedTonnageKg: 200 },
    { sessionId: 's2', finishedAt: '2026-10-02T13:00:00.000Z', workoutName: entry.workoutName, representative: { ...actual, weightKg: 22, reps: 8 }, loggedTonnageKg: 176 }], page: 0, pageCount: 1 };
const targets = { repsMin: 99, repsMax: 99, targetWeightKg: 999, targetRir: 9, restAfterSec: 60 };
const completed: WorkoutSession = { id: 's1', sourceWorkoutTemplateId: 'w1', sourceProgramId: 'deleted', workoutName: entry.workoutName, programName: entry.programName, status: 'completed',
  startedAt: entry.startedAt, finishedAt: entry.finishedAt,
  exercises: [{ id: 'actual-e', sessionId: 's1', sourceWorkoutExerciseId: 'we', sourceCatalogExerciseId: 'catalog-alt', sortOrder: 0, name: actual.exerciseName, muscleGroup: 'Pectoraux', equipment: 'Haltères', instructions: '', notes: '', weightMode: 'per_hand' }],
  sets: [{ id: 'set', sessionId: 's1', sessionExerciseId: 'actual-e', sourceSetTemplateId: 'st', sortOrder: 0, seriesIndex: 1, label: 'Top set', kind: 'top_set', notes: '', targets, originalTargets: targets }],
  performances: [{ id: 'perf', sessionId: 's1', sessionSetId: 'set', sortOrder: 0, weightKg: 20, reps: 10, rir: null, performedAt: actual.performedAt, advancedAt: actual.performedAt }],
  rests: [{ id: 'rest', sessionId: 's1', performedSetId: 'perf', plannedSeconds: 60, startedAt: actual.performedAt, endedAt: entry.finishedAt,
    chronologicalMs: 90000, activeMs: 70000, pauses: [{ id: 'pause', startedAt: actual.performedAt, endedAt: entry.finishedAt }] }] };

beforeEach(() => {
  jest.resetAllMocks(); jest.spyOn(AppState, 'addEventListener').mockImplementation(() => ({ remove: jest.fn() }));
  history.overview.mockResolvedValue(empty); history.exercises.mockResolvedValue([]); history.exercise.mockResolvedValue(exerciseData);
  repo.getSession.mockResolvedValue(completed); jest.mocked(useSessions).mockReturnValue(repo as unknown as SessionRepository);
  jest.mocked(router.canGoBack).mockReturnValue(true);
});
afterEach(() => { cleanup(); jest.restoreAllMocks(); });

test('empty history has an honest invitation, period expansion and access to programs without fake metrics', async () => {
  const view = render(<HistoryOverview />); await view.findByText('Votre histoire commence ici');
  expect(view.queryByLabelText('Tonnage enregistré')).toBeNull();
  fireEvent.press(view.getByRole('button', { name: 'Voir toute la période' }));
  await waitFor(() => expect(history.overview).toHaveBeenLastCalledWith(expect.not.objectContaining({ from: expect.anything() }), 0, null));
  fireEvent.press(view.getByRole('button', { name: 'Voir mes programmes' }));
  expect(router.dismissTo).toHaveBeenCalledWith({ pathname: '/', params: { universe: 'musculation' } });
});
test('general history exposes actual totals and two same-name programs route by stable ID', async () => {
  history.overview.mockResolvedValue(overview);
  const view = render(<HistoryOverview />); await view.findByLabelText('Entraînements');
  expect(view.getByLabelText('Entraînements').props.children).toBe('2');
  expect(view.getByLabelText('Tonnage enregistré').props.children).toBe('1 600 kg');
  const programs = view.getAllByRole('button', { name: 'Historique du programme Mon programme, 1 séances' });
  fireEvent.press(programs[1]!);
  expect(router.push).toHaveBeenCalledWith({ pathname: '/history/programs/[programId]', params: { programId: 'p2', name: 'Mon programme', period: '30' } });
  fireEvent.press(view.getByRole('button', { name: /Consulter Haut du corps/ }));
  expect(router.push).toHaveBeenLastCalledWith({ pathname: '/history/sessions/[sessionId]', params: { sessionId: 's1' } });
});
test('period and page changes query SQLite with the selected scope and reset page on period change', async () => {
  history.overview.mockResolvedValue({ ...overview, pageCount: 3 });
  const view = render(<HistoryOverview programId="p1" programName="Mon programme" />);
  fireEvent.press(await view.findByRole('button', { name: 'Suivante' }));
  await waitFor(() => expect(history.overview).toHaveBeenLastCalledWith(expect.objectContaining({ programId: 'p1' }), 1, expect.anything()));
  fireEvent.press(view.getByRole('radio', { name: '90 jours' }));
  await waitFor(() => expect(history.overview).toHaveBeenLastCalledWith(expect.objectContaining({ programId: 'p1', from: expect.any(String) }), 0, expect.anything()));
});
test('program history marks deletion and compares actual prior period without fictitious improvement', async () => {
  history.overview.mockResolvedValue({ ...overview, programs: [overview.programs[0]!], previous: { ...empty.stats, sessionCount: 1, performedSetCount: 3 } });
  const view = render(<HistoryOverview programId="p1" />);
  await view.findByText('Programme supprimé · ses entraînements restent conservés.');
  expect(view.getByText('1 séances · 3 séries · —')).toBeTruthy(); expect(view.queryByText(/\+\d+%/)).toBeNull();
  fireEvent.press(view.getByRole('radio', { name: 'Séries' })); await view.findByText('Séries par séance');
});
test('storage errors expose retry and do not show stale totals as current', async () => {
  history.overview.mockRejectedValue(new Error('Lecture impossible'));
  const view = render(<HistoryOverview />); await view.findByText('Lecture impossible');
  history.overview.mockResolvedValue(overview); fireEvent.press(view.getByRole('button', { name: 'Réessayer' }));
  await view.findByLabelText('Entraînements'); expect(view.queryByText('Lecture impossible')).toBeNull();
});
test('exercise index searches real identities without accents and opens exact exercise', async () => {
  history.exercises.mockResolvedValue([exerciseData.exercise!, { ...exerciseData.exercise!, id: 'other', name: 'Tractions' }]);
  const view = render(<ExerciseHistoryIndex />); await view.findByText('Tractions');
  fireEvent.changeText(view.getByLabelText('Rechercher dans mes performances'), 'developpe');
  expect(view.queryByText('Tractions')).toBeNull();
  fireEvent.press(view.getByRole('button', { name: 'Performances de Développé haltères' }));
  expect(router.push).toHaveBeenCalledWith({ pathname: '/history/exercises/[exerciseId]', params: { exerciseId: 'catalog-alt' } });
});
test('exercise history groups dates outside a four-column table and offers separate captured load modes', async () => {
  const view = render(<ExerciseHistory exerciseId="catalog-alt" />); await view.findByText('Top set');
  expect(view.getByText('Série')).toBeTruthy(); expect(view.getByText('Kg')).toBeTruthy(); expect(view.getByText('Reps')).toBeTruthy(); expect(view.getByText('RIR')).toBeTruthy();
  expect(view.queryByText('Date')).toBeNull(); expect(view.getByText('—')).toBeTruthy();
  fireEvent.press(view.getByRole('radio', { name: 'Charge totale (kg)' }));
  await waitFor(() => expect(history.exercise).toHaveBeenLastCalledWith('catalog-alt', expect.anything(), 'total', 0));
  expect(repo.validateSet).not.toHaveBeenCalled();
});
test('exercise graph switches correlated reps and logged tonnage; prior values never become actual input', async () => {
  const view = render(<ExerciseHistory exerciseId="catalog-alt" initialMode="per_hand" />); await view.findByText('Top set');
  fireEvent.press(view.getByRole('radio', { name: 'Répétitions' })); expect(view.getByText('Répétitions de travail')).toBeTruthy();
  fireEvent.press(view.getByRole('radio', { name: 'Tonnage' })); expect(view.getByText('Tonnage enregistré')).toBeTruthy();
  fireEvent.press(view.getByRole('button', { name: 'Consulter cette séance' }));
  expect(router.push).toHaveBeenCalledWith({ pathname: '/history/sessions/[sessionId]', params: { sessionId: 's1' } });
  expect(view.queryByLabelText('Charge réelle (kg)')).toBeNull();
});
test('an empty period preserves its load mode and offers an explicit change instead of substituting incompatible values', async () => {
  history.exercise.mockResolvedValue({ ...exerciseData, mode: 'per_hand', sessionCount: 0, visits: [], points: [], lastPerformance: null });
  const view = render(<ExerciseHistory exerciseId="catalog-alt" initialMode="per_hand" />);
  await view.findByText('Aucune série sur cette période');
  expect(view.getByRole('radio', { name: 'Charge par haltère (kg)' }).props.accessibilityState.checked).toBe(true);
  expect(view.queryByText('Top set')).toBeNull();
  fireEvent.press(view.getByRole('radio', { name: 'Charge totale (kg)' }));
  await waitFor(() => expect(history.exercise).toHaveBeenLastCalledWith('catalog-alt', expect.anything(), 'total', 0));
});
test('historical detail shares M2 math, expands preserved rests, links exact performed exercise, stays read-only', async () => {
  const view = render(<SessionHistory sessionId="s1" />); await view.findByText('Entraînement enregistré');
  expect(view.getByLabelText('Tonnage enregistré').props.children).toBe('200 kg');
  expect(view.getByLabelText('RIR moyen').props.children).toBe('—');
  fireEvent.press(view.getByRole('button', { name: 'Repos de la série réalisée 1' }));
  expect(view.getByText('Repos prévu : 60 s · Repos réel : 1 min 30 s')).toBeTruthy();
  expect(view.getByText(/Minuteur actif : 1 min 10 s/)).toBeTruthy();
  fireEvent.press(view.getByRole('button', { name: 'Historique : Développé haltères' }));
  expect(router.push).toHaveBeenCalledWith({ pathname: '/history/exercises/[exerciseId]', params: { exerciseId: 'catalog-alt', mode: 'per_hand' } });
  fireEvent.press(view.getByRole('button', { name: 'Retour à l’historique' })); expect(router.back).toHaveBeenCalledTimes(1);
  expect(view.queryByRole('button', { name: 'Valider la série' })).toBeNull(); expect(repo.validateSet).not.toHaveBeenCalled(); expect(repo.finishSession).not.toHaveBeenCalled();
});
test('an active workout cannot expose execution controls through the historical route', async () => {
  repo.getSession.mockResolvedValue({ ...completed, status: 'active', finishedAt: null });
  const view = render(<SessionHistory sessionId="s1" />);
  await view.findByText('Cet entraînement n’est pas terminé ou n’est plus disponible.');
  expect(view.queryByLabelText('Répétitions réelles')).toBeNull(); expect(repo.validateSet).not.toHaveBeenCalled();
});
test('chart announces insufficient and missing data without showing a missing weight as zero', () => {
  const view = render(<ProgressChart title="Charge" unit="kg" points={[{ id: 'missing', date: entry.finishedAt, value: null, label: '' }]} />);
  expect(view.getByText(/Aucun relevé disponible/)).toBeTruthy(); expect(view.queryByTestId('history-chart')).toBeNull();
  view.rerender(<ProgressChart title="Charge" unit="kg" points={[{ id: 'zero', date: entry.finishedAt, value: 0, label: '' }]} />);
  expect(view.getByText(/Un relevé : 0 kg/)).toBeTruthy();
});
test('chart touch and accessible controls select only real dated observations', () => {
  const points = [{ id: 'one', date: '2026-10-01T12:00:00.000Z', value: 50, label: 'Première' }, { id: 'two', date: '2026-10-10T12:00:00.000Z', value: 60, label: 'Deuxième' }];
  const view = render(<ProgressChart title="Charge" unit="kg" points={points} />);
  expect(view.getByText(/60 kg · Deuxième/)).toBeTruthy();
  fireEvent.press(view.getByRole('button', { name: 'Relevé précédent : Charge' })); expect(view.getByText(/50 kg · Première/)).toBeTruthy();
  fireEvent(view.getByTestId('history-chart'), 'touchEnd', { nativeEvent: { locationX: 297 } });
  expect(view.getByText(/60 kg · Deuxième/)).toBeTruthy();
});
test('returning to foreground refreshes the local calendar scope and history', async () => {
  const view = render(<HistoryOverview />); await view.findByText('Votre histoire commence ici');
  const before = history.overview.mock.calls.length;
  const listeners = jest.mocked(AppState.addEventListener).mock.calls.map(call => call[1]);
  act(() => listeners.forEach(listener => listener('active')));
  await waitFor(() => expect(history.overview.mock.calls.length).toBeGreaterThan(before));
});
