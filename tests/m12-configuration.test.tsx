import { afterEach, beforeEach, describe, expect, jest, test } from '@jest/globals';
import { act, cleanup, fireEvent, render, waitFor } from '@testing-library/react-native';
import { router } from 'expo-router';
import { AppState } from 'react-native';

import WorkoutsScreen from '../app/programs/[id]/workouts/index';
import type { WorkoutSession } from '../src/domain/session';
import type { PlannedExercise } from '../src/domain/training';
import { WorkoutOverview } from '../src/features/training/WorkoutOverview';
import { ExerciseOverview } from '../src/features/training/ExerciseOverview';
import { ResumeSessionCard } from '../src/features/sessions/ResumeSessionCard';
import { useWorkoutPlan } from '../src/features/training/useWorkoutPlan';
import { useLogbook } from '../src/store/LogbookProvider';
import { useSessions } from '../src/store/SessionProvider';

const mockFocusCleanups = new Set<() => void>();
let mockParams: { id: string; configuredWorkoutId?: string } = { id: 'program' };
jest.mock('expo-router', () => {
  const React = require('react') as typeof import('react');
  return {
    router: { push: jest.fn(), replace: jest.fn(), dismissTo: jest.fn(), back: jest.fn(), canGoBack: jest.fn() },
    useLocalSearchParams: () => mockParams,
    useFocusEffect: (effect: () => void | (() => void)) => React.useEffect(() => {
      const blur = effect();
      if (!blur) return undefined;
      mockFocusCleanups.add(blur);
      return () => { mockFocusCleanups.delete(blur); blur(); };
    }, [effect]),
  };
});
jest.mock('../src/store/LogbookProvider', () => ({ useLogbook: jest.fn() }));
jest.mock('../src/store/SessionProvider', () => ({ useSessions: jest.fn() }));
jest.mock('../src/features/training/useWorkoutPlan', () => ({ useWorkoutPlan: jest.fn() }));
jest.mock('@expo/vector-icons', () => ({ Ionicons: () => null }));
jest.mock('react-native-safe-area-context', () => jest.requireActual<{ default: typeof import('react-native-safe-area-context') }>('react-native-safe-area-context/jest/mock').default);

const stamp = '2026-10-14T10:00:00.000Z';
const program = { id: 'program', name: 'Programme personnel', description: '', sportType: 'musculation' as const, workoutCount: 1, createdAt: stamp, updatedAt: stamp };
const workout = { id: 'workout', programId: program.id, name: 'Séance personnelle', notes: '', sortOrder: 0, createdAt: stamp, updatedAt: stamp };
const exercise: PlannedExercise = {
  id: 'occurrence', workoutTemplateId: workout.id, exerciseId: 'catalog', sortOrder: 0, notes: '', createdAt: stamp, updatedAt: stamp,
  exercise: { id: 'catalog', name: 'Pompes', muscleGroup: 'Pectoraux', equipment: 'Poids du corps', instructions: '', weightMode: 'additional', isCustom: false, createdAt: stamp, updatedAt: stamp },
  sets: [0, 1].map(index => ({ id: `set-${index}`, workoutExerciseId: 'occurrence', sortOrder: index, label: '', kind: 'work', repsMin: 8, repsMax: 12, targetWeightKg: null, targetRir: null, restAfterSec: 60, notes: '', createdAt: stamp, updatedAt: stamp })),
};
const session: WorkoutSession = {
  id: 'actual-session', sourceWorkoutTemplateId: workout.id, sourceProgramId: program.id,
  workoutName: workout.name, programName: program.name, status: 'active', startedAt: stamp, finishedAt: null,
  exercises: [], sets: [], performances: [], rests: [],
};
const route = { programId: program.id, workoutId: workout.id, exerciseInstanceId: exercise.id };
const overviewRoute = { pathname: '/programs/[id]/workouts/[workoutId]', params: { id: program.id, workoutId: workout.id } };
const liveRoute = { pathname: '/sessions/[sessionId]', params: { sessionId: session.id } };
const mockSessions = {
  getActiveSession: jest.fn<ReturnType<typeof useSessions>['getActiveSession']>(),
  startOrResume: jest.fn<ReturnType<typeof useSessions>['startOrResume']>(),
};
const mockTraining = {
  reorderSets: jest.fn<() => Promise<void>>(), reorderWorkoutExercises: jest.fn<() => Promise<void>>(), deleteWorkoutExercise: jest.fn<() => Promise<void>>(),
};
const mockRetry = jest.fn();
const plan = () => ({ data: { program, workout, exercises: [exercise], exercise }, loading: false, error: null, retry: mockRetry, training: mockTraining }) as unknown as ReturnType<typeof useWorkoutPlan>;
function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: Error) => void;
  const promise = new Promise<T>((done, fail) => { resolve = done; reject = fail; });
  return { promise, resolve, reject };
}

beforeEach(() => {
  jest.resetAllMocks();
  jest.spyOn(AppState, 'addEventListener').mockImplementation(() => ({ remove: jest.fn() })); mockFocusCleanups.clear(); mockParams = { id: program.id };
  mockSessions.getActiveSession.mockResolvedValue(null); mockSessions.startOrResume.mockResolvedValue(session);
  mockTraining.reorderSets.mockResolvedValue(undefined); mockTraining.reorderWorkoutExercises.mockResolvedValue(undefined);
  jest.mocked(useSessions).mockReturnValue(mockSessions as unknown as ReturnType<typeof useSessions>);
  jest.mocked(useWorkoutPlan).mockReturnValue(plan());
  jest.mocked(useLogbook).mockReturnValue({ getProgram: jest.fn<() => Promise<typeof program>>().mockResolvedValue(program), listWorkouts: jest.fn<() => Promise<typeof workout[]>>().mockResolvedValue([workout]) } as unknown as ReturnType<typeof useLogbook>);
});
afterEach(async () => { await cleanup(); jest.restoreAllMocks(); });

describe('M1.2 : terminer la configuration sans créer une réalisation', () => {
  test('Terminer conserve la flèche et rejoint exactement la vue de séance, sans écriture', async () => {
    const view = await render(<ExerciseOverview {...route} />);
    expect(view.getByRole('button', { name: 'Retour' })).toBeTruthy();
    await fireEvent.press(view.getByRole('button', { name: 'Terminer' }));
    expect(router.dismissTo).toHaveBeenCalledWith(overviewRoute);
    expect(mockSessions.startOrResume).not.toHaveBeenCalled();
    expect(mockTraining.reorderSets).not.toHaveBeenCalled();
  });

  test('une sauvegarde en cours ou en erreur bloque Terminer ; une nouvelle tentative réussie le réactive', async () => {
    const pending = deferred<void>(); mockTraining.reorderSets.mockReturnValueOnce(pending.promise);
    const view = await render(<ExerciseOverview {...route} />);
    await fireEvent.press(view.getByRole('button', { name: 'Monter Série 2 (position 2)' }));
    expect(view.getByRole('button', { name: 'Terminer' }).props.accessibilityState.disabled).toBe(true);
    await fireEvent.press(view.getByRole('button', { name: 'Terminer' }));
    expect(router.dismissTo).not.toHaveBeenCalled();
    await act(async () => { pending.reject(new Error('Écriture impossible')); await pending.promise.catch(() => undefined); });
    expect(view.getByText('Écriture impossible')).toBeTruthy();
    await fireEvent.press(view.getByRole('button', { name: 'Terminer' }));
    expect(router.dismissTo).not.toHaveBeenCalled();
    await fireEvent.press(view.getByRole('button', { name: 'Monter Série 2 (position 2)' }));
    await waitFor(() => expect(view.getByRole('button', { name: 'Terminer' }).props.accessibilityState.disabled).toBe(false));
    await fireEvent.press(view.getByRole('button', { name: 'Terminer' }));
    expect(router.dismissTo).toHaveBeenCalledWith(overviewRoute);
  });

  test('Terminer la configuration revient aux séances avec une confirmation vérifiée, sans démarrage', async () => {
    const view = await render(<WorkoutOverview {...route} />);
    await waitFor(() => expect(view.getByRole('button', { name: 'Démarrer la séance' }).props.accessibilityState.disabled).toBe(false));
    await fireEvent.press(view.getByRole('button', { name: 'Terminer la configuration' }));
    expect(router.dismissTo).toHaveBeenCalledWith({ pathname: '/programs/[id]/workouts', params: { id: program.id, configuredWorkoutId: workout.id } });
    expect(mockSessions.startOrResume).not.toHaveBeenCalled();
    await view.unmount();
    mockParams = { id: program.id, configuredWorkoutId: workout.id };
    const list = await render(<WorkoutsScreen />);
    await list.findByText('Configuration enregistrée');
    expect(list.getByText(`${workout.name} · vos modifications sont sauvegardées.`)).toBeTruthy();
    expect(mockSessions.startOrResume).not.toHaveBeenCalled();
  });

  test('un identifiant étranger ne produit aucune confirmation de configuration', async () => {
    mockParams = { id: program.id, configuredWorkoutId: 'another-workout' };
    const view = await render(<WorkoutsScreen />);
    await view.findByRole('button', { name: `Ouvrir la séance ${workout.name}` });
    expect(view.queryByText('Configuration enregistrée')).toBeNull();
  });
});

describe('M1.2 : entrée et reprise d’un entraînement', () => {
  test('aucun départ pour une séance vide ou un exercice sans série', async () => {
    jest.mocked(useWorkoutPlan).mockReturnValue({ ...plan(), data: { program, workout, exercises: [{ ...exercise, sets: [] }], exercise } });
    const view = await render(<WorkoutOverview {...route} />);
    await waitFor(() => expect(mockSessions.getActiveSession).toHaveBeenCalledTimes(1));
    await fireEvent.press(view.getByRole('button', { name: 'Démarrer la séance' }));
    expect(mockSessions.startOrResume).not.toHaveBeenCalled();
    expect(view.getByText(/configurez les séries de chaque exercice/)).toBeTruthy();
  });

  test('le démarrage attend SQLite et résiste au double clic avant d’ouvrir la série active', async () => {
    const pending = deferred<WorkoutSession>(); mockSessions.startOrResume.mockReturnValue(pending.promise);
    const view = await render(<WorkoutOverview {...route} />);
    await waitFor(() => expect(view.getByRole('button', { name: 'Démarrer la séance' }).props.accessibilityState.disabled).toBe(false));
    await fireEvent.press(view.getByRole('button', { name: 'Démarrer la séance' }));
    await fireEvent.press(view.getByRole('button', { name: 'Démarrer la séance' }));
    expect(mockSessions.startOrResume).toHaveBeenCalledTimes(1);
    expect(mockSessions.startOrResume).toHaveBeenCalledWith(workout.id);
    expect(router.push).not.toHaveBeenCalled();
    await act(async () => { pending.resolve(session); await pending.promise; });
    expect(router.push).toHaveBeenCalledWith(liveRoute);
  });

  test('un échec de démarrage reste visible sans navigation et peut être retenté', async () => {
    mockSessions.startOrResume.mockRejectedValueOnce(new Error('Stockage indisponible'));
    const view = await render(<WorkoutOverview {...route} />);
    await waitFor(() => expect(view.getByRole('button', { name: 'Démarrer la séance' }).props.accessibilityState.disabled).toBe(false));
    await fireEvent.press(view.getByRole('button', { name: 'Démarrer la séance' }));
    await view.findByText('Stockage indisponible');
    expect(router.push).not.toHaveBeenCalled();
    expect(view.getByRole('button', { name: 'Terminer la configuration' }).props.accessibilityState.disabled).toBe(true);
    await fireEvent.press(view.getByRole('button', { name: 'Démarrer la séance' }));
    await waitFor(() => expect(router.push).toHaveBeenCalledWith(liveRoute));
  });

  test('une séance existante est nommée et proposée explicitement à la reprise', async () => {
    const existing = { ...session, sourceWorkoutTemplateId: 'other-template', workoutName: 'Séance déjà commencée' };
    mockSessions.getActiveSession.mockResolvedValue(existing); mockSessions.startOrResume.mockResolvedValue(existing);
    const view = await render(<WorkoutOverview {...route} />);
    const resume = await view.findByRole('button', { name: 'Reprendre la séance en cours' });
    expect(view.getByText(/Séance déjà commencée.*déjà en cours/)).toBeTruthy();
    expect(view.queryByRole('button', { name: 'Démarrer la séance' })).toBeNull();
    await fireEvent.press(resume);
    await waitFor(() => expect(router.push).toHaveBeenCalledWith(liveRoute));
  });

  test('une session concurrente différente ne fait pas quitter la configuration sans proposer sa reprise', async () => {
    const existing = { ...session, sourceWorkoutTemplateId: 'other-template', workoutName: 'Séance en cours ailleurs' };
    const view = await render(<WorkoutOverview {...route} />);
    await waitFor(() => expect(view.getByRole('button', { name: 'Démarrer la séance' }).props.accessibilityState.disabled).toBe(false));
    mockSessions.startOrResume.mockResolvedValue(existing); mockSessions.getActiveSession.mockResolvedValue(existing);
    await fireEvent.press(view.getByRole('button', { name: 'Démarrer la séance' }));
    await view.findByRole('button', { name: 'Reprendre la séance en cours' });
    expect(router.push).not.toHaveBeenCalled();
    await fireEvent.press(view.getByRole('button', { name: 'Reprendre la séance en cours' }));
    await waitFor(() => expect(router.push).toHaveBeenCalledWith(liveRoute));
  });

  test('un départ sauvegardé après fermeture de la page ne déclenche pas une navigation tardive', async () => {
    const pending = deferred<WorkoutSession>(); mockSessions.startOrResume.mockReturnValue(pending.promise);
    const view = await render(<WorkoutOverview {...route} />);
    await waitFor(() => expect(view.getByRole('button', { name: 'Démarrer la séance' }).props.accessibilityState.disabled).toBe(false));
    await fireEvent.press(view.getByRole('button', { name: 'Démarrer la séance' }));
    await act(() => mockFocusCleanups.forEach(blur => blur()));
    await act(async () => { pending.resolve(session); await pending.promise; });
    expect(router.push).not.toHaveBeenCalled();
  });

  test('la carte permet de reprendre même si le programme source a été supprimé', async () => {
    mockSessions.getActiveSession.mockResolvedValue({ ...session, sourceProgramId: 'deleted-program', sourceWorkoutTemplateId: 'deleted-template' });
    const view = await render(<ResumeSessionCard />);
    await fireEvent.press(await view.findByRole('button', { name: 'Reprendre la séance' }));
    expect(router.push).toHaveBeenCalledWith(liveRoute);
    expect(mockSessions.startOrResume).not.toHaveBeenCalled();
    expect(useLogbook).not.toHaveBeenCalled();
  });

  test('le retour au premier plan recharge la session et retire une carte devenue terminée', async () => {
    const foreground = new Set<(state: import('react-native').AppStateStatus) => void>();
    jest.spyOn(AppState, 'addEventListener').mockImplementation((_event, listener) => {
      foreground.add(listener);
      return { remove: () => { foreground.delete(listener); } };
    });
    mockSessions.getActiveSession.mockResolvedValue(session);
    const view = await render(<ResumeSessionCard />);
    await view.findByRole('button', { name: 'Reprendre la séance' });
    mockSessions.getActiveSession.mockResolvedValue(null);
    expect(foreground.size).toBeGreaterThan(0);
    await act(() => foreground.forEach(listener => listener('active')));
    await waitFor(() => expect(mockSessions.getActiveSession).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(view.queryByRole('button', { name: 'Reprendre la séance' })).toBeNull());
  });
});
