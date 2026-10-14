import { afterEach, beforeEach, describe, expect, jest, test } from '@jest/globals';
import { act, cleanup, fireEvent, render, waitFor } from '@testing-library/react-native';
import { router } from 'expo-router';

import HomeScreen from '../app/index';
import ProgramsScreen from '../app/programs';
import type { Program, ProgramInput, WorkoutInput, WorkoutTemplate } from '../src/domain/models';
import { ProgramEditor } from '../src/features/programs/ProgramEditor';
import { WorkoutEditor } from '../src/features/programs/WorkoutEditor';
import { useLogbook } from '../src/store/LogbookProvider';

const mockFocusCleanups = new Set<() => void>();

jest.mock('expo-router', () => {
  const React = require('react') as typeof import('react');
  return {
    router: { push: jest.fn(), replace: jest.fn(), back: jest.fn(), canGoBack: jest.fn() },
    useFocusEffect: (effect: () => void | (() => void)) => React.useEffect(() => {
      const cleanupFocus = effect();
      if (typeof cleanupFocus !== 'function') return undefined;
      mockFocusCleanups.add(cleanupFocus);
      return () => { mockFocusCleanups.delete(cleanupFocus); cleanupFocus(); };
    }, [effect]),
  };
});
jest.mock('../src/store/LogbookProvider', () => ({ useLogbook: jest.fn() }));
jest.mock('@expo/vector-icons', () => ({ Ionicons: () => null }));
jest.mock('react-native-safe-area-context', () => jest.requireActual<{ default: typeof import('react-native-safe-area-context') }>('react-native-safe-area-context/jest/mock').default);

const program: Program = {
  id: 'program-local', name: 'Mon organisation', description: 'Deux jours par semaine',
  sportType: 'musculation', createdAt: '2026-10-14T10:00:00.000Z',
  updatedAt: '2026-10-14T10:00:00.000Z', workoutCount: 0,
};
const workout: WorkoutTemplate = {
  id: 'workout-local', programId: program.id, name: 'Ma séance', notes: 'À mon rythme',
  sortOrder: 0, createdAt: program.createdAt, updatedAt: program.updatedAt,
};
const mockStore = {
  programs: [] as Program[], loading: false, error: null as string | null,
  refresh: jest.fn<() => Promise<void>>(),
  getProgram: jest.fn<(id: string) => Promise<Program | null>>(),
  getWorkout: jest.fn<(id: string) => Promise<WorkoutTemplate | null>>(),
  listWorkouts: jest.fn<(id: string) => Promise<WorkoutTemplate[]>>(),
  createProgram: jest.fn<(input: ProgramInput) => Promise<Program>>(),
  updateProgram: jest.fn<(id: string, input: ProgramInput) => Promise<Program>>(),
  createWorkout: jest.fn<(id: string, input: WorkoutInput) => Promise<WorkoutTemplate>>(),
  updateWorkout: jest.fn<(id: string, input: WorkoutInput) => Promise<WorkoutTemplate>>(),
};

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}

beforeEach(() => {
  jest.resetAllMocks();
  mockFocusCleanups.clear();
  mockStore.programs = [];
  mockStore.loading = false;
  mockStore.error = null;
  mockStore.refresh.mockResolvedValue(undefined);
  mockStore.getProgram.mockResolvedValue(program);
  mockStore.getWorkout.mockResolvedValue(workout);
  mockStore.listWorkouts.mockResolvedValue([]);
  mockStore.createProgram.mockResolvedValue(program);
  mockStore.updateProgram.mockResolvedValue(program);
  mockStore.createWorkout.mockResolvedValue(workout);
  mockStore.updateWorkout.mockResolvedValue(workout);
  jest.mocked(router.canGoBack).mockReturnValue(false);
  jest.mocked(useLogbook).mockReturnValue(mockStore);
});
afterEach(() => { cleanup(); mockFocusCleanups.clear(); });

describe('M0 : états vides et organisation locale', () => {
  test('une première ouverture invite à créer sans programmes ni performances fictifs', () => {
    const home = render(<HomeScreen />);
    expect(home.getByText('Créer mon premier programme')).toBeTruthy();
    expect(home.getByText('Votre progression apparaîtra ici après vos premiers entraînements.')).toBeTruthy();
    expect(home.queryByText(/Prise de muscle|Alex|\+12\s*%|124\s*350/)).toBeNull();
    fireEvent.press(home.getByRole('button', { name: 'Créer mon premier programme' }));
    expect(router.push).toHaveBeenCalledWith('/programs/new');
    home.unmount();

    const list = render(<ProgramsScreen />);
    expect(list.getByText('Un programme à votre image')).toBeTruthy();
    expect(list.queryByRole('button', { name: /Ouvrir le programme/ })).toBeNull();
    expect(mockStore.createProgram).not.toHaveBeenCalled();
  });

  test('la création de programme exige un nom puis sauvegarde les champs nettoyés', async () => {
    const view = render(<ProgramEditor mode="create" />);
    const name = await view.findByLabelText('Nom du programme');
    fireEvent.changeText(name, '   ');
    fireEvent.press(view.getByRole('button', { name: 'Créer le programme' }));
    expect(view.getByText('Donnez un nom à votre programme.')).toBeTruthy();
    expect(mockStore.createProgram).not.toHaveBeenCalled();

    fireEvent.changeText(name, '  Mon organisation  ');
    fireEvent.changeText(view.getByLabelText('Description (facultative)'), '  Deux jours par semaine  ');
    fireEvent.press(view.getByRole('button', { name: 'Créer le programme' }));
    await waitFor(() => expect(mockStore.createProgram).toHaveBeenCalledWith({ name: 'Mon organisation', description: 'Deux jours par semaine' }));
    await waitFor(() => expect(router.replace).toHaveBeenCalledWith({ pathname: '/programs/[id]', params: { id: program.id } }));
  });

  test('la modification charge le programme et conserve son identité', async () => {
    jest.mocked(router.canGoBack).mockReturnValue(true);
    const view = render(<ProgramEditor mode="edit" id={program.id} />);
    await waitFor(() => expect(view.getByLabelText('Nom du programme').props.value).toBe(program.name));
    expect(view.getByLabelText('Description (facultative)').props.value).toBe(program.description);
    fireEvent.changeText(view.getByLabelText('Nom du programme'), 'Nouveau nom');
    fireEvent.press(view.getByRole('button', { name: 'Enregistrer les modifications' }));
    await waitFor(() => expect(mockStore.updateProgram).toHaveBeenCalledWith(program.id, { name: 'Nouveau nom', description: program.description }));
    await waitFor(() => expect(router.back).toHaveBeenCalledTimes(1));
    expect(mockStore.createProgram).not.toHaveBeenCalled();
  });

  test('la création de séance exige un nom et retourne aux séances du bon programme', async () => {
    const view = render(<WorkoutEditor mode="create" programId={program.id} />);
    const name = await view.findByLabelText('Nom de la séance');
    fireEvent.press(view.getByRole('button', { name: 'Ajouter la séance' }));
    expect(view.getByText('Donnez un nom à votre séance.')).toBeTruthy();
    expect(mockStore.createWorkout).not.toHaveBeenCalled();

    fireEvent.changeText(name, '  Ma séance  ');
    fireEvent.changeText(view.getByLabelText('Notes (facultatives)'), '  À mon rythme  ');
    fireEvent.press(view.getByRole('button', { name: 'Ajouter la séance' }));
    await waitFor(() => expect(mockStore.createWorkout).toHaveBeenCalledWith(program.id, { name: 'Ma séance', notes: 'À mon rythme' }));
    await waitFor(() => expect(router.replace).toHaveBeenCalledWith({ pathname: '/programs/[id]/workouts', params: { id: program.id } }));
  });

  test('la modification de séance conserve son identité et ses notes', async () => {
    jest.mocked(router.canGoBack).mockReturnValue(true);
    const view = render(<WorkoutEditor mode="edit" programId={program.id} workoutId={workout.id} />);
    await waitFor(() => expect(view.getByLabelText('Nom de la séance').props.value).toBe(workout.name));
    fireEvent.changeText(view.getByLabelText('Notes (facultatives)'), '  Nouvelle consigne  ');
    fireEvent.press(view.getByRole('button', { name: 'Enregistrer les modifications' }));
    await waitFor(() => expect(mockStore.updateWorkout).toHaveBeenCalledWith(workout.id, { name: workout.name, notes: 'Nouvelle consigne' }));
    await waitFor(() => expect(router.back).toHaveBeenCalledTimes(1));
    expect(mockStore.createWorkout).not.toHaveBeenCalled();
  });

  test('une création différée reste unique et ne navigue plus après perte du focus', async () => {
    const pending = deferred<Program>();
    mockStore.createProgram.mockReturnValue(pending.promise);
    const view = render(<ProgramEditor mode="create" />);
    fireEvent.changeText(await view.findByLabelText('Nom du programme'), 'Mon organisation');
    const save = view.getByRole('button', { name: 'Créer le programme' });
    fireEvent.press(save);
    fireEvent.press(save);
    expect(mockStore.createProgram).toHaveBeenCalledTimes(1);
    expect(view.getByRole('button', { name: 'Créer le programme' }).props.accessibilityState.disabled).toBe(true);
    expect(view.getByRole('button', { name: 'Retour' }).props.accessibilityState.disabled).toBe(true);

    act(() => { mockFocusCleanups.forEach((blur) => blur()); });
    await act(async () => { pending.resolve(program); await pending.promise; });
    expect(router.replace).not.toHaveBeenCalled();
    expect(router.back).not.toHaveBeenCalled();
  });

  test('une édition de séance différée reste unique et ne navigue plus après perte du focus', async () => {
    const pending = deferred<WorkoutTemplate>();
    mockStore.updateWorkout.mockReturnValue(pending.promise);
    const view = render(<WorkoutEditor mode="edit" programId={program.id} workoutId={workout.id} />);
    await waitFor(() => expect(view.getByLabelText('Nom de la séance').props.value).toBe(workout.name));
    const save = view.getByRole('button', { name: 'Enregistrer les modifications' });
    fireEvent.press(save);
    fireEvent.press(save);
    expect(mockStore.updateWorkout).toHaveBeenCalledTimes(1);
    expect(view.getByRole('button', { name: 'Enregistrer les modifications' }).props.accessibilityState.disabled).toBe(true);

    act(() => { mockFocusCleanups.forEach((blur) => blur()); });
    await act(async () => { pending.resolve(workout); await pending.promise; });
    expect(router.replace).not.toHaveBeenCalled();
    expect(router.back).not.toHaveBeenCalled();
  });

  test('une séance appartenant à un autre programme ne peut pas être modifiée', async () => {
    mockStore.getWorkout.mockResolvedValue({ ...workout, programId: 'other-program' });
    const view = render(<WorkoutEditor mode="edit" programId={program.id} workoutId={workout.id} />);
    expect(await view.findByText('Cette séance ou son programme n’est pas disponible.')).toBeTruthy();
    expect(view.queryByLabelText('Nom de la séance')).toBeNull();
    expect(mockStore.updateWorkout).not.toHaveBeenCalled();
  });
});
