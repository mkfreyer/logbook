import { afterEach, beforeEach, describe, expect, jest, test } from '@jest/globals';
import { act, cleanup, fireEvent, render, waitFor } from '@testing-library/react-native';
import { router } from 'expo-router';
import { Alert, type AlertButton } from 'react-native';

import ProgramScreen from '../app/programs/[id]/index';
import HomeScreen from '../src/features/home/HomeScreen';
import ProgramsScreen from '../src/features/programs/ProgramsScreen';
import type { Program, ProgramInput, WorkoutInput, WorkoutTemplate } from '../src/domain/models';
import { ProgramEditor } from '../src/features/programs/ProgramEditor';
import { WorkoutEditor } from '../src/features/programs/WorkoutEditor';
import { useLogbook } from '../src/store/LogbookProvider';

const mockFocusCleanups = new Set<() => void>();
const mockGoTo = jest.fn();

jest.mock('expo-router', () => {
  const React = require('react') as typeof import('react');
  return {
    router: { push: jest.fn(), replace: jest.fn(), back: jest.fn(), canGoBack: jest.fn(), dismissTo: jest.fn() },
    useLocalSearchParams: () => ({ id: 'program-local' }),
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
jest.mock('@expo/vector-icons/Ionicons', () => ({ __esModule: true, default: () => null }));
jest.mock('../src/navigation/UniverseScreen', () => ({ UniverseScreen: ({ children }: { children: import('react').ReactNode }) => children }));
jest.mock('../src/navigation/UniverseContext', () => ({ useUniverseIsActive: () => true, useUniverseNavigation: () => ({ goTo: mockGoTo }) }));
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
  deleteProgram: jest.fn<(id: string) => Promise<void>>(),
  deleteWorkout: jest.fn<(id: string) => Promise<void>>(),
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
  mockStore.deleteProgram.mockResolvedValue(undefined);
  mockStore.deleteWorkout.mockResolvedValue(undefined);
  jest.mocked(router.canGoBack).mockReturnValue(false);
  jest.mocked(useLogbook).mockReturnValue(mockStore);
});
afterEach(() => { cleanup(); mockFocusCleanups.clear(); jest.restoreAllMocks(); });

describe('M0 : états vides et organisation locale', () => {
  test('une première ouverture invite à créer sans programmes ni performances fictifs', () => {
    const home = render(<HomeScreen />);
    expect(home.getByText('Créer mon premier programme')).toBeTruthy();
    expect(home.getByText('Après vos premières séances')).toBeTruthy();
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

  test('les boutons entre univers utilisent le pager, et Cardio reste indisponible', () => {
    mockStore.programs = [program];
    const home = render(<HomeScreen />);
    expect(home.getByText(program.name)).toBeTruthy();
    expect(home.getByText('0 séance prévue · à votre rythme')).toBeTruthy();
    fireEvent.press(home.getByRole('button', { name: 'Musculation' }));
    expect(mockGoTo).toHaveBeenCalledWith('musculation');
    expect(router.push).not.toHaveBeenCalled();
    expect(home.getByRole('button', { name: 'Cardio, à venir' }).props.accessibilityState.disabled).toBe(true);
    home.unmount();

    const list = render(<ProgramsScreen />);
    expect(list.queryByRole('button', { name: 'Retour' })).toBeNull();
    fireEvent.press(list.getByRole('button', { name: 'Accueil' }));
    expect(mockGoTo).toHaveBeenLastCalledWith('home');
    expect(router.back).not.toHaveBeenCalled();
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

describe('M0 : suppressions confirmées', () => {
  let alert: jest.SpiedFunction<typeof Alert.alert>;
  beforeEach(() => { alert = jest.spyOn(Alert, 'alert').mockImplementation(() => undefined); });

  function choice(text: string): AlertButton {
    const button = alert.mock.calls.at(-1)?.[2]?.find(item => item.text === text);
    expect(button).toBeDefined();
    return button!;
  }
  function screen(kind: 'programme' | 'séance') {
    return render(kind === 'programme' ? <ProgramScreen /> : <WorkoutEditor mode="edit" programId={program.id} workoutId={workout.id} />);
  }
  function pressHandler(button: ReturnType<ReturnType<typeof render>['getByRole']>): () => void {
    let node: typeof button | null = button;
    while (node) {
      if (typeof node.props.onPress === 'function') return node.props.onPress as () => void;
      node = node.parent;
    }
    throw new Error('No press handler found');
  }

  test.each(['programme', 'séance'] as const)('annuler la confirmation du %s ne supprime ni ne navigue', async kind => {
    const view = screen(kind);
    const label = kind === 'programme' ? 'Supprimer le programme' : 'Supprimer la séance';
    const button = await view.findByRole('button', { name: label });
    expect(view.getByRole('button', { name: 'Retour' })).toBeTruthy();
    fireEvent.press(button);
    expect(alert).toHaveBeenCalledTimes(1);
    const [title, message] = alert.mock.calls[0]!;
    expect(title).toContain(label);
    expect(message).toContain(kind === 'programme' ? program.name : workout.name);
    expect(message).toContain(kind === 'programme' ? 'toutes ses séances planifiées' : 'Les autres séances seront conservées');
    expect(choice('Annuler').style).toBe('cancel');
    expect(choice('Supprimer').style).toBe('destructive');
    act(() => choice('Annuler').onPress?.());
    expect(mockStore.deleteProgram).not.toHaveBeenCalled();
    expect(mockStore.deleteWorkout).not.toHaveBeenCalled();
    expect(router.dismissTo).not.toHaveBeenCalled();
    expect(router.back).not.toHaveBeenCalled();
    expect(view.getByRole('button', { name: label }).props.accessibilityState.disabled).toBe(false);
    // Even a stale callback from the cancelled dialog cannot delete.
    act(() => choice('Supprimer').onPress?.());
    expect(mockStore.deleteProgram).not.toHaveBeenCalled();
    expect(mockStore.deleteWorkout).not.toHaveBeenCalled();
  });

  test('la suppression du programme est unique et attend le stockage avant le retour à Musculation', async () => {
    const pending = deferred<void>();
    mockStore.deleteProgram.mockReturnValue(pending.promise);
    const view = screen('programme');
    const button = await view.findByRole('button', { name: 'Supprimer le programme' });
    // Bypass the React disabled render to exercise the synchronous double-click lock.
    const press = pressHandler(button);
    act(() => { press(); press(); });
    expect(alert).toHaveBeenCalledTimes(1);
    expect(mockStore.deleteProgram).not.toHaveBeenCalled();
    const remove = choice('Supprimer').onPress;
    act(() => { remove?.(); remove?.(); });
    expect(mockStore.deleteProgram).toHaveBeenCalledTimes(1);
    expect(mockStore.deleteProgram).toHaveBeenCalledWith(program.id);
    expect(view.getByRole('button', { name: 'Retour' }).props.accessibilityState.disabled).toBe(true);
    expect(view.getByRole('button', { name: 'Modifier le programme' }).props.accessibilityState.disabled).toBe(true);
    expect(router.dismissTo).not.toHaveBeenCalled();
    await act(async () => { pending.resolve(); await pending.promise; });
    expect(router.dismissTo).toHaveBeenCalledTimes(1);
    expect(router.dismissTo).toHaveBeenCalledWith({ pathname: '/', params: { universe: 'musculation' } });
    expect(mockStore.deleteWorkout).not.toHaveBeenCalled();
  });

  test('la suppression de séance attend le stockage et bloque une sauvegarde concurrente', async () => {
    const pending = deferred<void>();
    mockStore.deleteWorkout.mockReturnValue(pending.promise);
    const view = screen('séance');
    const removeButton = await view.findByRole('button', { name: 'Supprimer la séance' });
    const savePress = pressHandler(view.getByRole('button', { name: 'Enregistrer les modifications' }));
    fireEvent.changeText(view.getByLabelText('Nom de la séance'), 'Nom non enregistré');
    fireEvent.press(removeButton);
    expect(alert.mock.calls[0]?.[1]).toContain(workout.name);
    act(() => savePress());
    expect(mockStore.updateWorkout).not.toHaveBeenCalled();
    const remove = choice('Supprimer').onPress;
    act(() => { remove?.(); remove?.(); savePress(); });
    expect(mockStore.deleteWorkout).toHaveBeenCalledTimes(1);
    expect(mockStore.deleteWorkout).toHaveBeenCalledWith(workout.id);
    expect(mockStore.updateWorkout).not.toHaveBeenCalled();
    expect(router.dismissTo).not.toHaveBeenCalled();
    await act(async () => { pending.resolve(); await pending.promise; });
    expect(router.dismissTo).toHaveBeenCalledWith({ pathname: '/programs/[id]/workouts', params: { id: program.id } });
    expect(mockStore.deleteProgram).not.toHaveBeenCalled();
  });

  test.each(['programme', 'séance'] as const)('une erreur de suppression du %s laisse l’écran ouvert et permet une nouvelle tentative', async kind => {
    const remove = kind === 'programme' ? mockStore.deleteProgram : mockStore.deleteWorkout;
    remove.mockRejectedValueOnce(new Error('SQLite unavailable'));
    const view = screen(kind);
    const label = kind === 'programme' ? 'Supprimer le programme' : 'Supprimer la séance';
    fireEvent.press(await view.findByRole('button', { name: label }));
    act(() => choice('Supprimer').onPress?.());
    expect(await view.findByText(kind === 'programme' ? 'Impossible de supprimer ce programme. Réessayez.' : 'Impossible de supprimer cette séance. Réessayez.')).toBeTruthy();
    expect(router.dismissTo).not.toHaveBeenCalled();
    expect(router.back).not.toHaveBeenCalled();
    expect(view.getByRole('button', { name: label }).props.accessibilityState.disabled).toBe(false);
    if (kind === 'séance') expect(view.getByLabelText('Nom de la séance').props.value).toBe(workout.name);
    fireEvent.press(view.getByRole('button', { name: label }));
    act(() => choice('Supprimer').onPress?.());
    await waitFor(() => expect(router.dismissTo).toHaveBeenCalledTimes(1));
    expect(remove).toHaveBeenCalledTimes(2);
  });

  test('une sauvegarde de séance en cours empêche même l’ouverture de la confirmation de suppression', async () => {
    const pending = deferred<WorkoutTemplate>();
    mockStore.updateWorkout.mockReturnValue(pending.promise);
    const view = screen('séance');
    const removeButton = await view.findByRole('button', { name: 'Supprimer la séance' });
    const deletePress = pressHandler(removeButton);
    fireEvent.press(view.getByRole('button', { name: 'Enregistrer les modifications' }));
    act(() => deletePress());
    expect(alert).not.toHaveBeenCalled();
    expect(mockStore.deleteWorkout).not.toHaveBeenCalled();
    await act(async () => { pending.resolve(workout); await pending.promise; });
  });

  test('une confirmation quittée et une suppression terminée après perte du focus ne redirigent pas', async () => {
    const view = screen('programme');
    fireEvent.press(await view.findByRole('button', { name: 'Supprimer le programme' }));
    const confirm = choice('Supprimer').onPress;
    act(() => mockFocusCleanups.forEach(blur => blur()));
    act(() => confirm?.());
    expect(mockStore.deleteProgram).not.toHaveBeenCalled();
    view.unmount();

    const pending = deferred<void>();
    mockStore.deleteWorkout.mockReturnValue(pending.promise);
    const editor = screen('séance');
    fireEvent.press(await editor.findByRole('button', { name: 'Supprimer la séance' }));
    act(() => choice('Supprimer').onPress?.());
    expect(mockStore.deleteWorkout).toHaveBeenCalledTimes(1);
    act(() => mockFocusCleanups.forEach(blur => blur()));
    editor.unmount();
    await act(async () => { pending.resolve(); await pending.promise; });
    expect(router.dismissTo).not.toHaveBeenCalled();
  });

  test('la suppression est absente lors de la création ou pour une séance d’un autre programme', async () => {
    const create = render(<WorkoutEditor mode="create" programId={program.id} />);
    await create.findByLabelText('Nom de la séance');
    expect(create.queryByRole('button', { name: 'Supprimer la séance' })).toBeNull();
    create.unmount();
    mockStore.getWorkout.mockResolvedValue({ ...workout, programId: 'other-program' });
    const invalid = screen('séance');
    await invalid.findByText('Cette séance ou son programme n’est pas disponible.');
    expect(invalid.queryByRole('button', { name: 'Supprimer la séance' })).toBeNull();
    expect(mockStore.deleteWorkout).not.toHaveBeenCalled();
  });
});
