import { afterEach, beforeEach, describe, expect, jest, test } from '@jest/globals';
import { act, cleanup, fireEvent, render, waitFor } from '@testing-library/react-native';
import { router } from 'expo-router';
import { Alert, AppState } from 'react-native';
import type { Program, WorkoutTemplate } from '../src/domain/models';
import type { ExerciseCatalogItem, SetTemplate, WorkoutExercise } from '../src/domain/training';
import { parseSetDraft, type SetDraft } from '../src/domain/setDraft';
import { TrainingRepository } from '../src/db/trainingRepository';
import { useLogbook } from '../src/store/LogbookProvider';
import { useTraining } from '../src/store/TrainingProvider';
import { useSessions } from '../src/store/SessionProvider';
import { SetEditor } from '../src/features/training/SetEditor';
import { WorkoutOverview } from '../src/features/training/WorkoutOverview';
import { ExerciseOverview } from '../src/features/training/ExerciseOverview';
import { ExerciseLibrary } from '../src/features/training/ExerciseLibrary';
import { CustomExerciseEditor } from '../src/features/training/CustomExerciseEditor';
import { PlannedExerciseEditor } from '../src/features/training/PlannedExerciseEditor';
import WorkoutsScreen from '../app/programs/[id]/workouts/index';

const mockFocusCleanups = new Set<() => void>();
jest.mock('expo-router', () => {
  const React = require('react') as typeof import('react');
  return { router: { push: jest.fn(), replace: jest.fn(), dismissTo: jest.fn(), back: jest.fn(), canGoBack: jest.fn() },
    useLocalSearchParams: () => ({ id: 'program' }),
    useFocusEffect: (effect: () => void | (() => void)) => React.useEffect(() => {
      const cleanupFocus = effect();
      if (!cleanupFocus) return undefined;
      mockFocusCleanups.add(cleanupFocus);
      return () => { mockFocusCleanups.delete(cleanupFocus); cleanupFocus(); };
    }, [effect]),
  };
});
jest.mock('../src/store/LogbookProvider', () => ({ useLogbook: jest.fn() }));
jest.mock('../src/store/TrainingProvider', () => ({ useTraining: jest.fn() }));
jest.mock('../src/store/SessionProvider', () => ({ useSessions: jest.fn() }));
jest.mock('@expo/vector-icons', () => ({ Ionicons: () => null }));
jest.mock('react-native-safe-area-context', () => jest.requireActual<{ default: typeof import('react-native-safe-area-context') }>('react-native-safe-area-context/jest/mock').default);

const stamp = '2026-10-14T10:00:00Z';
const program: Program = { id: 'program', name: 'Personnel', description: '', sportType: 'musculation', workoutCount: 1, createdAt: stamp, updatedAt: stamp };
const workout: WorkoutTemplate = { id: 'workout', programId: program.id, name: 'Ma séance', notes: 'Mes consignes', sortOrder: 0, createdAt: stamp, updatedAt: stamp };
const catalog: ExerciseCatalogItem = { id: 'catalog', name: 'Développé couché barre', muscleGroup: 'Pectoraux', equipment: 'Barre et banc', instructions: '', weightMode: 'total', isCustom: false, createdAt: stamp, updatedAt: stamp };
const occurrence: WorkoutExercise = { id: 'occurrence', workoutTemplateId: workout.id, exerciseId: catalog.id, exercise: catalog, notes: '', sortOrder: 0, createdAt: stamp, updatedAt: stamp };
const first: SetTemplate = { id: 'first', workoutExerciseId: occurrence.id, sortOrder: 0, label: 'Échauffement', kind: 'warmup', repsMin: 8, repsMax: 8, targetWeightKg: null, targetRir: null, restAfterSec: 60, notes: '', createdAt: stamp, updatedAt: stamp };
const second: SetTemplate = { ...first, id: 'second', sortOrder: 1, label: 'Top set', kind: 'top_set', repsMin: 8, repsMax: 12, targetWeightKg: 42.5, targetRir: 2, restAfterSec: 120 };
const third: SetTemplate = { ...first, id: 'third', sortOrder: 2, label: 'Back-off', kind: 'back_off', restAfterSec: 180 };
const mockStore = { getProgram: jest.fn<(id: string) => Promise<Program | null>>(), getWorkout: jest.fn<(id: string) => Promise<WorkoutTemplate | null>>(), listWorkouts: jest.fn<(id: string) => Promise<WorkoutTemplate[]>>() };
const mockTraining = {
  listWorkoutExercises: jest.fn<TrainingRepository['listWorkoutExercises']>(),
  getWorkoutExercise: jest.fn<TrainingRepository['getWorkoutExercise']>(),
  listSets: jest.fn<TrainingRepository['listSets']>(), getSet: jest.fn<TrainingRepository['getSet']>(),
  createSet: jest.fn<TrainingRepository['createSet']>(), updateSet: jest.fn<TrainingRepository['updateSet']>(), deleteSet: jest.fn<TrainingRepository['deleteSet']>(),
  reorderWorkoutExercises: jest.fn<TrainingRepository['reorderWorkoutExercises']>(), reorderSets: jest.fn<TrainingRepository['reorderSets']>(),
  deleteWorkoutExercise: jest.fn<TrainingRepository['deleteWorkoutExercise']>(),
  listCatalog: jest.fn<TrainingRepository['listCatalog']>(),
  getCatalogExercise: jest.fn<TrainingRepository['getCatalogExercise']>(),
  createCustomExercise: jest.fn<TrainingRepository['createCustomExercise']>(),
  updateCustomExercise: jest.fn<TrainingRepository['updateCustomExercise']>(),
  addWorkoutExercise: jest.fn<TrainingRepository['addWorkoutExercise']>(),
  updateWorkoutExercise: jest.fn<TrainingRepository['updateWorkoutExercise']>(),
};
const mockSessions = { getActiveSession: jest.fn<ReturnType<typeof useSessions>['getActiveSession']>() };
const route = { programId: program.id, workoutId: workout.id, exerciseInstanceId: occurrence.id };
const exerciseDestination = { pathname: '/programs/[id]/workouts/[workoutId]/exercises/[exerciseInstanceId]', params: { id: program.id, workoutId: workout.id, exerciseInstanceId: occurrence.id } };
function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>(done => { resolve = done; });
  return { promise, resolve };
}

beforeEach(() => {
  jest.resetAllMocks();
  jest.spyOn(AppState, 'addEventListener').mockImplementation(() => ({ remove: jest.fn() })); mockFocusCleanups.clear();
  mockStore.getProgram.mockResolvedValue(program); mockStore.getWorkout.mockResolvedValue(workout);
  mockStore.listWorkouts.mockResolvedValue([workout]);
  mockTraining.listWorkoutExercises.mockResolvedValue([occurrence]);
  mockTraining.getWorkoutExercise.mockResolvedValue(occurrence);
  mockTraining.listSets.mockResolvedValue([first, second, third]); mockTraining.getSet.mockResolvedValue(second);
  mockTraining.createSet.mockResolvedValue(first); mockTraining.updateSet.mockResolvedValue(second);
  mockTraining.deleteSet.mockResolvedValue(undefined); mockTraining.deleteWorkoutExercise.mockResolvedValue(undefined);
  mockTraining.reorderSets.mockResolvedValue(undefined); mockTraining.reorderWorkoutExercises.mockResolvedValue(undefined);
  mockTraining.listCatalog.mockResolvedValue([catalog]); mockTraining.getCatalogExercise.mockResolvedValue(catalog);
  mockTraining.createCustomExercise.mockResolvedValue({ ...catalog, isCustom: true }); mockTraining.updateCustomExercise.mockResolvedValue({ ...catalog, isCustom: true });
  mockTraining.addWorkoutExercise.mockResolvedValue(occurrence); mockTraining.updateWorkoutExercise.mockResolvedValue(occurrence);
  jest.mocked(useLogbook).mockReturnValue(mockStore as unknown as ReturnType<typeof useLogbook>);
  jest.mocked(useTraining).mockReturnValue(mockTraining as unknown as TrainingRepository);
  mockSessions.getActiveSession.mockResolvedValue(null);
  jest.mocked(useSessions).mockReturnValue(mockSessions as unknown as ReturnType<typeof useSessions>);
});
afterEach(() => { cleanup(); jest.restoreAllMocks(); });

describe('M3.4A : configuration facultative des charges calculées', () => {
  async function percentageForm() {
    const view = render(<SetEditor mode="create" {...route} />); await view.findByLabelText('Étiquette (facultative)');
    fireEvent.press(view.getByRole('radio', { name: 'Échauffement' }));
    fireEvent.press(view.getByRole('button', { name: 'Charge calculée (facultatif)' }));
    fireEvent.press(view.getByRole('radio', { name: 'Pourcentage d’une série prévue' }));
    return view;
  }
  test('un échauffement choisit sa référence explicitement, montre le calcul et garde son repos individuel', async () => {
    const view = await percentageForm();
    expect(view.getByLabelText('Charge calculée').props.children).toBe('Charge calculée non disponible');
    fireEvent.press(view.getByRole('radio', { name: /Référence : Série 2/ }));
    fireEvent.changeText(view.getByLabelText('Pourcentage de charge'), '50');
    expect(view.getByText('21,25 kg')).toBeTruthy(); fireEvent.changeText(view.getByLabelText('Repos après cette série (s)'), '30');
    fireEvent.press(view.getByRole('button', { name: 'Ajouter la série' }));
    fireEvent.press(view.getByRole('button', { name: 'Ajouter la série' }));
    await waitFor(() => expect(mockTraining.createSet).toHaveBeenCalledWith(occurrence.id, expect.objectContaining({
      kind: 'warmup', restAfterSec: 30, targetWeightKg: null, loadRule: { basis: 'planned_target', referenceSetId: second.id, percent: 50 },
    })));
    expect(mockTraining.createSet).toHaveBeenCalledTimes(1);
  });
  test('M3.4B : une règle réelle se prépare sans utiliser les 42,5 kg prévus comme une performance', async () => {
    const view = await percentageForm();
    fireEvent.press(view.getByRole('radio', { name: 'Pourcentage de la charge réellement effectuée' }));
    fireEvent.press(view.getByRole('radio', { name: /Référence : Série 2/ }));
    fireEvent.changeText(view.getByLabelText('Pourcentage de charge'), '90');
    expect(view.getByText(/En attente de la série de référence/)).toBeTruthy();
    expect(view.getByLabelText('Charge calculée').props.children).toBe('Charge calculée non disponible');
    fireEvent.press(view.getByRole('button', { name: 'Ajouter la série' }));
    await waitFor(() => expect(mockTraining.createSet).toHaveBeenCalledWith(occurrence.id,
      expect.objectContaining({ targetWeightKg: null, loadRule: { basis: 'performed_weight', referenceSetId: second.id, percent: 90 } })));
  });

  test('aucune référence n’est choisie implicitement et une absence de sélection empêche la sauvegarde', async () => {
    const view = await percentageForm(); fireEvent.changeText(view.getByLabelText('Pourcentage de charge'), '50');
    fireEvent.press(view.getByRole('button', { name: 'Ajouter la série' }));
    expect(view.getByText('Choisissez une série de référence avant d’enregistrer.')).toBeTruthy(); expect(mockTraining.createSet).not.toHaveBeenCalled();
  });
  test('une référence sans charge montre un état neutre et ne remplace pas null par zéro', async () => {
    mockTraining.listSets.mockResolvedValue([first, { ...second, targetWeightKg: null }]);
    const view = await percentageForm(); fireEvent.press(view.getByRole('radio', { name: /Référence : Série 2/ }));
    fireEvent.changeText(view.getByLabelText('Pourcentage de charge'), '75');
    expect(view.getByText(/Cette référence n’a pas de charge cible/)).toBeTruthy(); expect(view.queryByText('0 kg')).toBeNull();
    fireEvent.press(view.getByRole('button', { name: 'Ajouter la série' }));
    await waitFor(() => expect(mockTraining.createSet).toHaveBeenCalledWith(occurrence.id, expect.objectContaining({ targetWeightKg: null, loadRule: expect.objectContaining({ percent: 75 }) })));
  });
  test('le remplacement manuel rend le champ éditable et retire la règle du futur enregistrement', async () => {
    const view = await percentageForm(); fireEvent.press(view.getByRole('radio', { name: /Référence : Série 2/ }));
    fireEvent.changeText(view.getByLabelText('Pourcentage de charge'), '50');
    fireEvent.press(view.getByRole('button', { name: 'Remplacer par une charge manuelle' }));
    const input = view.getByLabelText('Charge totale (kg) · facultative'); expect(input.props.editable).toBe(true); expect(input.props.value).toBe('21.25');
    fireEvent.changeText(input, '22,5'); fireEvent.press(view.getByRole('button', { name: 'Ajouter la série' }));
    await waitFor(() => expect(mockTraining.createSet).toHaveBeenCalledWith(occurrence.id, expect.objectContaining({ targetWeightKg: 22.5, loadRule: null })));
  });
  test('le back-off manuel ne nécessite aucun panneau avancé ni pourcentage', async () => {
    const view = render(<SetEditor mode="create" {...route} />); await view.findByLabelText('Étiquette (facultative)');
    fireEvent.press(view.getByRole('radio', { name: 'Back-off' })); expect(view.queryByLabelText('Pourcentage de charge')).toBeNull();
    fireEvent.press(view.getByRole('button', { name: 'Ajouter la série' }));
    await waitFor(() => expect(mockTraining.createSet).toHaveBeenCalledWith(occurrence.id, expect.objectContaining({ kind: 'back_off', loadRule: null })));
  });
  test('un back-off calculé utilise explicitement un top set et conserve son type', async () => {
    const view = render(<SetEditor mode="create" {...route} />); await view.findByLabelText('Étiquette (facultative)');
    fireEvent.press(view.getByRole('radio', { name: 'Back-off' })); fireEvent.press(view.getByRole('button', { name: 'Charge calculée (facultatif)' }));
    fireEvent.press(view.getByRole('radio', { name: 'Pourcentage d’une série prévue' }));
    expect(view.getAllByRole('radio', { name: /Référence :/ })).toHaveLength(1);
    fireEvent.press(view.getByRole('radio', { name: /Référence : Série 2/ })); fireEvent.changeText(view.getByLabelText('Pourcentage de charge'), '90');
    expect(view.getByText('38,25 kg')).toBeTruthy(); fireEvent.press(view.getByRole('button', { name: 'Ajouter la série' }));
    await waitFor(() => expect(mockTraining.createSet).toHaveBeenCalledWith(occurrence.id, expect.objectContaining({ kind: 'back_off', loadRule: expect.objectContaining({ referenceSetId: second.id, percent: 90 }) })));
  });
  test('une référence supprimée est indiquée et peut être remplacée par une cible manuelle vide', async () => {
    mockTraining.getSet.mockResolvedValue({ ...first, loadRule: { basis: 'planned_target', referenceSetId: null, percent: 50 } });
    const view = render(<SetEditor mode="edit" {...route} setId={first.id} />); await view.findByLabelText('Pourcentage de charge');
    expect(view.getByText(/La référence de cette série a été supprimée/)).toBeTruthy();
    fireEvent.press(view.getByRole('button', { name: 'Remplacer par une charge manuelle' }));
    expect(view.getByLabelText('Charge totale (kg) · facultative').props.value).toBe('');
    fireEvent.press(view.getByRole('button', { name: 'Enregistrer les modifications' }));
    await waitFor(() => expect(mockTraining.updateSet).toHaveBeenCalledWith(first.id, expect.objectContaining({ targetWeightKg: null, loadRule: null })));
  });
  test('la confirmation de suppression d’une référence prévient ses séries dépendantes et ne supprime rien sans confirmation', async () => {
    mockTraining.listSets.mockResolvedValue([{ ...first, loadRule: { basis: 'planned_target', referenceSetId: second.id, percent: 50 } }, second]);
    const alert = jest.spyOn(Alert, 'alert'); const view = render(<SetEditor mode="edit" {...route} setId={second.id} />);
    fireEvent.press(await view.findByRole('button', { name: 'Supprimer la série' }));
    expect(alert).toHaveBeenCalledWith('Supprimer la série ?', expect.stringContaining('perdront leur référence'), expect.any(Array), expect.objectContaining({ cancelable: true }));
    act(() => { alert.mock.calls[0]![2]!.find(button => button.text === 'Annuler')?.onPress?.(); });
    expect(mockTraining.deleteSet).not.toHaveBeenCalled();
  });
  test('une règle existante est éditée avec le même ID sans se désactiver en touchant son type déjà sélectionné', async () => {
    const edited = { ...first, targetWeightKg: 21.25, loadRule: { basis: 'planned_target' as const, referenceSetId: second.id, percent: 50 } };
    mockTraining.getSet.mockResolvedValue(edited); mockTraining.listSets.mockResolvedValue([edited, second]);
    const view = render(<SetEditor mode="edit" {...route} setId={first.id} />); await view.findByLabelText('Pourcentage de charge');
    fireEvent.press(view.getByRole('radio', { name: 'Échauffement' })); fireEvent.changeText(view.getByLabelText('Pourcentage de charge'), '75');
    expect(view.getByText('31,875 kg')).toBeTruthy(); fireEvent.press(view.getByRole('button', { name: 'Enregistrer les modifications' }));
    await waitFor(() => expect(mockTraining.updateSet).toHaveBeenCalledWith(first.id, expect.objectContaining({ loadRule: { basis: 'planned_target', referenceSetId: second.id, percent: 75 } })));
  });
  test('les suggestions modifient le nom seulement, sans imposer un type ou un calcul', async () => {
    const view = render(<SetEditor mode="create" {...route} />); await view.findByLabelText('Étiquette (facultative)');
    fireEvent.press(view.getByRole('button', { name: 'Suggestions de noms' })); fireEvent.press(view.getByRole('radio', { name: 'Nom : Top set' }));
    expect(view.getByLabelText('Étiquette (facultative)').props.value).toBe('Top set');
    fireEvent.press(view.getByRole('button', { name: 'Ajouter la série' }));
    await waitFor(() => expect(mockTraining.createSet).toHaveBeenCalledWith(occurrence.id, expect.objectContaining({ label: 'Top set', kind: 'work', loadRule: null })));
  });
});

describe('M1.1 : vue des cibles et séries indépendantes', () => {
  test('ouvrir une séance M0 mène à sa préparation et sa modification reste accessible', async () => {
    const list = render(<WorkoutsScreen />);
    fireEvent.press(await list.findByRole('button', { name: `Ouvrir la séance ${workout.name}` }));
    expect(router.push).toHaveBeenCalledWith({ pathname: '/programs/[id]/workouts/[workoutId]', params: { id: program.id, workoutId: workout.id } });
    list.unmount();
    const view = render(<WorkoutOverview {...route} />);
    fireEvent.press(await view.findByRole('button', { name: 'Modifier la séance' }));
    expect(router.push).toHaveBeenLastCalledWith({ pathname: '/programs/[id]/workouts/[workoutId]/edit', params: { id: program.id, workoutId: workout.id } });
  });
  test('une séance vide propose la bibliothèque sans performances et désactive le démarrage', async () => {
    mockTraining.listWorkoutExercises.mockResolvedValue([]);
    const view = render(<WorkoutOverview {...route} />);
    await view.findByText('Composez votre séance');
    expect(view.getByRole('button', { name: 'Démarrer la séance' }).props.accessibilityState.disabled).toBe(true);
    expect(view.queryByText(/tonnage|durée estimée|dernière performance/i)).toBeNull();
    fireEvent.press(view.getByRole('button', { name: 'Ajouter un exercice' }));
    expect(router.push).toHaveBeenCalledWith({ pathname: '/programs/[id]/workouts/[workoutId]/library', params: { id: program.id, workoutId: workout.id } });
  });

  test('la vue d’ensemble conserve trois repos différents et les valeurs facultatives', async () => {
    const view = render(<WorkoutOverview {...route} />);
    await view.findByText('Repos après cette série : 60 s');
    expect(view.getByText('Repos après cette série : 120 s')).toBeTruthy();
    expect(view.getByText('Repos après cette série : 180 s')).toBeTruthy();
    expect(view.getAllByText(/Charge non définie/)).toHaveLength(2);
    expect(view.getByText(/42,5 kg · RIR 2/)).toBeTruthy();
    fireEvent.press(view.getByRole('button', { name: `Configurer ${catalog.name}` }));
    expect(router.push).toHaveBeenCalledWith(exerciseDestination);
  });

  test('les flèches réorganisent seulement les séries prévues du bon exercice', async () => {
    const pending = deferred<void>(); mockTraining.reorderSets.mockReturnValue(pending.promise);
    const view = render(<ExerciseOverview {...route} />);
    const move = await view.findByRole('button', { name: 'Monter Top set (position 2)' });
    fireEvent.press(move); fireEvent.press(move);
    expect(mockTraining.reorderSets).toHaveBeenCalledTimes(1);
    expect(mockTraining.reorderSets).toHaveBeenCalledWith(occurrence.id, [second.id, first.id, third.id]);
    expect(mockTraining.reorderWorkoutExercises).not.toHaveBeenCalled();
    await act(async () => { pending.resolve(); await pending.promise; });
  });

  test('la création d’une série accepte une plage, une charge décimale et un repos individuel', async () => {
    const view = render(<SetEditor mode="create" {...route} />);
    await view.findByLabelText('Étiquette (facultative)');
    fireEvent.changeText(view.getByLabelText('Étiquette (facultative)'), '  Ma série  ');
    fireEvent.press(view.getByRole('radio', { name: 'Plage min / max' }));
    fireEvent.changeText(view.getByLabelText('Répétitions minimum'), '8');
    fireEvent.changeText(view.getByLabelText('Répétitions maximum'), '12');
    fireEvent.changeText(view.getByLabelText(/Charge totale/), '42,5');
    fireEvent.changeText(view.getByLabelText('RIR cible (facultatif)'), '');
    fireEvent.changeText(view.getByLabelText('Repos après cette série (s)'), '75');
    fireEvent.press(view.getByRole('button', { name: 'Ajouter la série' }));
    await waitFor(() => expect(mockTraining.createSet).toHaveBeenCalledWith(occurrence.id, {
      label: 'Ma série', kind: 'work', repsMin: 8, repsMax: 12, targetWeightKg: 42.5, targetRir: null, restAfterSec: 75, notes: '', loadRule: null,
    }));
    expect(mockTraining.updateSet).not.toHaveBeenCalled();
    await waitFor(() => expect(router.dismissTo).toHaveBeenCalledWith(exerciseDestination));
  });

  test('une modification garde le même identifiant et peut effacer charge/RIR sans changer les autres séries', async () => {
    const view = render(<SetEditor mode="edit" {...route} setId={second.id} />);
    await waitFor(() => expect(view.getByLabelText(/Charge totale/).props.value).toBe('42.5'));
    fireEvent.changeText(view.getByLabelText(/Charge totale/), '');
    fireEvent.changeText(view.getByLabelText('RIR cible (facultatif)'), '');
    fireEvent.changeText(view.getByLabelText('Repos après cette série (s)'), '150');
    fireEvent.press(view.getByRole('button', { name: 'Enregistrer les modifications' }));
    await waitFor(() => expect(mockTraining.updateSet).toHaveBeenCalledWith(second.id, expect.objectContaining({ targetWeightKg: null, targetRir: null, restAfterSec: 150, repsMin: 8, repsMax: 12 })));
    expect(mockTraining.updateSet).toHaveBeenCalledTimes(1);
    expect(mockTraining.createSet).not.toHaveBeenCalled();
  });

  test('les entrées incohérentes sont expliquées sans écrire, et Annuler ne sauvegarde rien', async () => {
    const view = render(<SetEditor mode="create" {...route} />);
    await view.findByLabelText('Repos après cette série (s)');
    fireEvent.changeText(view.getByLabelText('Repos après cette série (s)'), '1,5');
    fireEvent.press(view.getByRole('button', { name: 'Ajouter la série' }));
    expect(view.getByRole('alert')).toBeTruthy();
    expect(mockTraining.createSet).not.toHaveBeenCalled();
    expect(router.dismissTo).not.toHaveBeenCalled();
    fireEvent.press(view.getByRole('button', { name: 'Annuler' }));
    expect(router.dismissTo).toHaveBeenCalledWith(exerciseDestination);
    expect(mockTraining.createSet).not.toHaveBeenCalled();
  });

  test('une erreur de stockage laisse les cibles saisies disponibles pour une nouvelle tentative', async () => {
    mockTraining.createSet.mockRejectedValueOnce(new Error('Stockage indisponible'));
    const view = render(<SetEditor mode="create" {...route} />);
    await view.findByLabelText('Repos après cette série (s)');
    fireEvent.changeText(view.getByLabelText('Repos après cette série (s)'), '135');
    fireEvent.press(view.getByRole('button', { name: 'Ajouter la série' }));
    await view.findByText('Stockage indisponible');
    expect(router.dismissTo).not.toHaveBeenCalled();
    expect(view.getByLabelText('Repos après cette série (s)').props.value).toBe('135');
    fireEvent.press(view.getByRole('button', { name: 'Ajouter la série' }));
    await waitFor(() => expect(router.dismissTo).toHaveBeenCalledTimes(1));
  });

  test('une sauvegarde différée reste unique et ne navigue pas après perte du focus', async () => {
    const pending = deferred<SetTemplate>(); mockTraining.createSet.mockReturnValue(pending.promise);
    const view = render(<SetEditor mode="create" {...route} />);
    const save = await view.findByRole('button', { name: 'Ajouter la série' });
    fireEvent.press(save); fireEvent.press(save);
    expect(mockTraining.createSet).toHaveBeenCalledTimes(1);
    expect(view.getByRole('button', { name: 'Retour' }).props.accessibilityState.disabled).toBe(true);
    act(() => mockFocusCleanups.forEach(blur => blur()));
    await act(async () => { pending.resolve(first); await pending.promise; });
    expect(router.dismissTo).not.toHaveBeenCalled();
  });

  test('un formulaire enregistré reste verrouillé jusqu’à sa sortie pour éviter une seconde création', async () => {
    const view = render(<SetEditor mode="create" {...route} />);
    const button = await view.findByRole('button', { name: 'Ajouter la série' });
    fireEvent.press(button);
    await waitFor(() => expect(router.dismissTo).toHaveBeenCalledTimes(1));
    expect(view.getByRole('button', { name: 'Ajouter la série' }).props.accessibilityState.disabled).toBe(true);
    fireEvent.press(button);
    expect(mockTraining.createSet).toHaveBeenCalledTimes(1);
  });

  test('une série d’un autre exercice ne peut pas être modifiée depuis cette route', async () => {
    mockTraining.getSet.mockResolvedValue({ ...second, workoutExerciseId: 'other-exercise' });
    const view = render(<SetEditor mode="edit" {...route} setId={second.id} />);
    await view.findByText('Cette série ou son exercice n’est pas disponible.');
    expect(view.queryByLabelText('Repos après cette série (s)')).toBeNull();
    expect(mockTraining.updateSet).not.toHaveBeenCalled();
  });

  test('annuler la suppression d’une série ne supprime rien puis confirmer ne cible que cette série', async () => {
    const alert = jest.spyOn(Alert, 'alert').mockImplementation(() => undefined);
    const view = render(<SetEditor mode="edit" {...route} setId={second.id} />);
    fireEvent.press(await view.findByRole('button', { name: 'Supprimer la série' }));
    expect(alert.mock.calls[0]?.[1]).toContain(second.label);
    act(() => alert.mock.calls[0]?.[2]?.find(button => button.text === 'Annuler')?.onPress?.());
    expect(mockTraining.deleteSet).not.toHaveBeenCalled();
    expect(router.dismissTo).not.toHaveBeenCalled();
    fireEvent.press(view.getByRole('button', { name: 'Supprimer la série' }));
    const confirm = alert.mock.calls[1]?.[2]?.find(button => button.text === 'Supprimer')?.onPress;
    act(() => { confirm?.(); confirm?.(); });
    await waitFor(() => expect(router.dismissTo).toHaveBeenCalledWith(exerciseDestination));
    expect(mockTraining.deleteSet).toHaveBeenCalledTimes(1);
    expect(mockTraining.deleteSet).toHaveBeenCalledWith(second.id);
  });
});

describe('M1.1 : bibliothèque et exercices programmés', () => {
  test('la recherche accepte les accents et plusieurs mots, sans ajouter de programme ni d’exercice automatiquement', async () => {
    const squat = { ...catalog, id: 'squat', name: 'Squat barre', muscleGroup: 'Quadriceps' };
    mockTraining.listCatalog.mockResolvedValue([catalog, squat]);
    const view = render(<ExerciseLibrary programId={program.id} workoutId={workout.id} />);
    const search = await view.findByLabelText('Rechercher un exercice');
    expect(view.getByRole('button', { name: 'Ajouter Squat barre' })).toBeTruthy();
    fireEvent.changeText(search, 'developpe pectoraux');
    expect(view.getByRole('button', { name: `Ajouter ${catalog.name}` })).toBeTruthy();
    expect(view.queryByRole('button', { name: 'Ajouter Squat barre' })).toBeNull();
    expect(mockTraining.addWorkoutExercise).not.toHaveBeenCalled();
    fireEvent.press(view.getByRole('button', { name: `Ajouter ${catalog.name}` }));
    await waitFor(() => expect(mockTraining.addWorkoutExercise).toHaveBeenCalledWith(workout.id, { exerciseId: catalog.id }));
    await waitFor(() => expect(router.dismissTo).toHaveBeenCalledWith({ pathname: '/programs/[id]/workouts/[workoutId]', params: { id: program.id, workoutId: workout.id } }));
  });

  test('la création personnalisée conserve la convention de charge et ajoute seulement une référence au catalogue', async () => {
    const view = render(<CustomExerciseEditor programId={program.id} workoutId={workout.id} />);
    const name = await view.findByLabelText('Nom de l’exercice');
    fireEvent.press(view.getByRole('button', { name: 'Créer l’exercice' }));
    expect(mockTraining.createCustomExercise).not.toHaveBeenCalled();
    expect(view.getByRole('alert')).toBeTruthy();
    fireEvent.changeText(name, '  Mon rowing  ');
    fireEvent.changeText(view.getByLabelText('Groupe musculaire'), ' Dos ');
    fireEvent.changeText(view.getByLabelText('Matériel'), ' Haltère ');
    fireEvent.changeText(view.getByLabelText('Consignes (facultatives)'), ' Contrôler la descente ');
    fireEvent.press(view.getByRole('radio', { name: 'Charge par haltère (kg)' }));
    expect(view.getByRole('radio', { name: 'Charge par haltère (kg)' }).props.accessibilityState.checked).toBe(true);
    fireEvent.press(view.getByRole('button', { name: 'Créer l’exercice' }));
    await waitFor(() => expect(mockTraining.createCustomExercise).toHaveBeenCalledWith({ name: 'Mon rowing', muscleGroup: 'Dos', equipment: 'Haltère', instructions: 'Contrôler la descente', weightMode: 'per_hand' }));
    expect(mockTraining.addWorkoutExercise).not.toHaveBeenCalled();
    await waitFor(() => expect(router.replace).toHaveBeenCalledWith({ pathname: '/programs/[id]/workouts/[workoutId]/library', params: { id: program.id, workoutId: workout.id } }));
  });

  test('renommer une référence personnalisée conserve son identifiant et ne réécrit pas les séries', async () => {
    const custom = { ...catalog, id: 'custom', isCustom: true };
    mockTraining.listWorkoutExercises.mockResolvedValue([{ ...occurrence, exerciseId: custom.id, exercise: custom }]);
    const view = render(<CustomExerciseEditor {...route} catalogId={custom.id} />);
    await waitFor(() => expect(view.getByLabelText('Nom de l’exercice').props.value).toBe(custom.name));
    fireEvent.changeText(view.getByLabelText('Nom de l’exercice'), 'Nom corrigé');
    fireEvent.press(view.getByRole('button', { name: 'Enregistrer l’exercice' }));
    await waitFor(() => expect(mockTraining.updateCustomExercise).toHaveBeenCalledWith(custom.id, expect.objectContaining({ name: 'Nom corrigé' })));
    expect(mockTraining.createCustomExercise).not.toHaveBeenCalled();
    expect(mockTraining.updateSet).not.toHaveBeenCalled();
  });

  test('modifier les consignes ou changer un exercice prévu garde son occurrence et les séries', async () => {
    const view = render(<PlannedExerciseEditor {...route} />);
    fireEvent.changeText(await view.findByLabelText('Consignes pour cette séance (facultatives)'), '  Ma consigne  ');
    fireEvent.press(view.getByRole('button', { name: 'Enregistrer les consignes' }));
    await waitFor(() => expect(mockTraining.updateWorkoutExercise).toHaveBeenCalledWith(occurrence.id, { exerciseId: catalog.id, notes: 'Ma consigne' }));
    view.unmount();
    jest.mocked(router.replace).mockClear(); mockTraining.updateWorkoutExercise.mockClear();
    const replacement = { ...catalog, id: 'other-catalog', name: 'Pompes', weightMode: 'additional' as const };
    mockTraining.listCatalog.mockResolvedValue([replacement]);
    const library = render(<ExerciseLibrary {...route} />);
    fireEvent.press(await library.findByRole('button', { name: 'Choisir Pompes' }));
    await waitFor(() => expect(mockTraining.updateWorkoutExercise).toHaveBeenCalledWith(occurrence.id, { exerciseId: replacement.id, notes: occurrence.notes }));
    await waitFor(() => expect(router.dismissTo).toHaveBeenCalledWith(exerciseDestination));
    expect(mockTraining.addWorkoutExercise).not.toHaveBeenCalled();
    expect(mockTraining.updateSet).not.toHaveBeenCalled();
  });

  test('les flèches d’exercice adressent une permutation complète de la bonne séance', async () => {
    const next = { ...occurrence, id: 'next', sortOrder: 1, exercise: { ...catalog, name: 'Pompes' } };
    mockTraining.listWorkoutExercises.mockResolvedValue([occurrence, next]);
    const view = render(<WorkoutOverview {...route} />);
    fireEvent.press(await view.findByRole('button', { name: 'Monter Pompes' }));
    await waitFor(() => expect(mockTraining.reorderWorkoutExercises).toHaveBeenCalledWith(workout.id, [next.id, occurrence.id]));
    expect(mockTraining.reorderSets).not.toHaveBeenCalled();
    await waitFor(() => expect(view.getByRole('button', { name: 'Monter Pompes' }).props.accessibilityState.disabled).toBe(false));
  });

  test('une suppression d’exercice annulée garde tout ; une confirmation cible seulement l’occurrence', async () => {
    const alert = jest.spyOn(Alert, 'alert').mockImplementation(() => undefined);
    const view = render(<ExerciseOverview {...route} />);
    const button = await view.findByRole('button', { name: 'Supprimer cet exercice de la séance' });
    fireEvent.press(button);
    expect(alert.mock.calls[0]?.[1]).toContain('L’exercice restera dans la bibliothèque');
    act(() => alert.mock.calls[0]?.[2]?.find(item => item.text === 'Annuler')?.onPress?.());
    expect(mockTraining.deleteWorkoutExercise).not.toHaveBeenCalled();
    fireEvent.press(button);
    act(() => alert.mock.calls[1]?.[2]?.find(item => item.text === 'Supprimer')?.onPress?.());
    await waitFor(() => expect(mockTraining.deleteWorkoutExercise).toHaveBeenCalledWith(occurrence.id));
    expect(mockTraining.deleteSet).not.toHaveBeenCalled();
    await waitFor(() => expect(router.dismissTo).toHaveBeenCalledWith({ pathname: '/programs/[id]/workouts/[workoutId]', params: { id: program.id, workoutId: workout.id } }));
  });

  test('une route de séance hors programme ne donne accès ni au catalogue ni aux mutations', async () => {
    mockStore.getWorkout.mockResolvedValue({ ...workout, programId: 'another-program' });
    const view = render(<ExerciseLibrary {...route} />);
    await view.findByText('Cette séance n’est plus disponible.');
    expect(view.queryByLabelText('Rechercher un exercice')).toBeNull();
    expect(mockTraining.addWorkoutExercise).not.toHaveBeenCalled();
    expect(mockTraining.listWorkoutExercises).not.toHaveBeenCalled();
  });
});

describe('Saisie française des cibles', () => {
  const draft: SetDraft = { label: '', kind: 'work', repetitionMode: 'exact', repsMin: '8', repsMax: '12', weight: '', rir: '', rest: '90', notes: '' };
  test('répétitions exactes et champs facultatifs vides restent distincts de zéro', () => {
    expect(parseSetDraft(draft)).toMatchObject({ repsMin: 8, repsMax: 8, targetWeightKg: null, targetRir: null });
    expect(parseSetDraft({ ...draft, weight: '0', rir: '0', rest: '0' })).toMatchObject({ targetWeightKg: 0, targetRir: 0, restAfterSec: 0 });
  });
  test.each(['2,5', '2.5'])('charge décimale %s acceptée sans tronquer', weight => {
    expect(parseSetDraft({ ...draft, weight }).targetWeightKg).toBe(2.5);
  });
  test.each(['-5', 'Infinity', 'NaN', '5kg', '1e3', '2,5.5'])('charge invalide %s rejetée', weight => {
    expect(() => parseSetDraft({ ...draft, weight })).toThrow();
  });
  test('plage inversée, RIR impossible et secondes fractionnaires rejetés', () => {
    expect(() => parseSetDraft({ ...draft, repetitionMode: 'range', repsMin: '12', repsMax: '8' })).toThrow(/maximum/);
    expect(() => parseSetDraft({ ...draft, rir: '11' })).toThrow(/RIR/);
    expect(() => parseSetDraft({ ...draft, rest: '2.5' })).toThrow(/entier/);
  });
});
