import { afterEach, beforeEach, describe, expect, jest, test } from '@jest/globals';
import { act, cleanup, fireEvent, render, waitFor } from '@testing-library/react-native';
import { router } from 'expo-router';
import { Alert, AppState } from 'react-native';
import type { SessionRepository } from '../src/db/sessionRepository';
import type { WorkoutSession } from '../src/domain/session';
import type { ExerciseCatalogItem } from '../src/domain/training';
import { useSessions } from '../src/store/SessionProvider';
import { useTraining } from '../src/store/TrainingProvider';
import { SessionScreen } from '../src/features/sessions/SessionScreen';
import { SessionReplacement } from '../src/features/sessions/SessionReplacement';
import { RemainingExercises } from '../src/features/sessions/RemainingExercises';
import { CompletedSessions } from '../src/features/sessions/CompletedSessions';

const mockFocusCleanups = new Set<() => void>();
const mockFocusEffects = new Set<() => void | (() => void)>();
jest.mock('expo-router', () => {
  const React = require('react') as typeof import('react');
  return { router: { push: jest.fn(), dismissTo: jest.fn(), back: jest.fn(), canGoBack: jest.fn() },
    useFocusEffect: (effect: () => void | (() => void)) => React.useEffect(() => {
      mockFocusEffects.add(effect);
      const blur = effect(); if (!blur) return undefined; mockFocusCleanups.add(blur);
      return () => { mockFocusEffects.delete(effect); mockFocusCleanups.delete(blur); blur(); };
    }, [effect]),
  };
});
jest.mock('../src/store/SessionProvider', () => ({ useSessions: jest.fn() }));
jest.mock('../src/store/TrainingProvider', () => ({ useTraining: jest.fn() }));
jest.mock('@expo/vector-icons', () => ({ Ionicons: () => null }));
jest.mock('react-native-safe-area-context', () => jest.requireActual<{ default: typeof import('react-native-safe-area-context') }>('react-native-safe-area-context/jest/mock').default);

const stamp = '2026-10-14T12:00:00.000Z';
const targets = { repsMin: 8, repsMax: 10, targetWeightKg: 40, targetRir: 2, restAfterSec: 30 };
const exercises = ['Barre', 'Tractions', 'Curl'].map((name, i) => ({ id: `e${i}`, sessionId: 's', sourceWorkoutExerciseId: `we${i}`, sourceCatalogExerciseId: `c${i}`,
  sortOrder: i, plannedOrder: i, name, muscleGroup: 'Dos', equipment: 'Salle', instructions: '', notes: '', weightMode: 'total' as const }));
const sets = [0, 0, 1, 2].map((exerciseIndex, i) => ({ id: `set${i}`, sessionId: 's', sessionExerciseId: `e${exerciseIndex}`, sourceSetTemplateId: `st${i}`,
  sortOrder: i, seriesIndex: i === 1 ? 1 : 0, label: '', kind: 'work' as const, notes: '', targets, originalTargets: targets }));
const initial: WorkoutSession = { id: 's', sourceWorkoutTemplateId: 'w', sourceProgramId: 'p', workoutName: 'Séance réelle', programName: 'Programme personnel', status: 'active',
  startedAt: stamp, finishedAt: null, exercises, sets, performances: [], rests: [], selectedExerciseId: null, replacements: [], exerciseChoices: [] };
const alternative: ExerciseCatalogItem = { id: 'alt', name: 'Mon développé haltères', muscleGroup: 'Pectoraux', equipment: 'Haltères', instructions: '',
  weightMode: 'per_hand', isCustom: true, createdAt: stamp, updatedAt: stamp };
const replacement: WorkoutSession = { ...initial, selectedExerciseId: 'new',
  exercises: [...exercises, { ...exercises[0]!, id: 'new', name: alternative.name, sourceCatalogExerciseId: alternative.id, sortOrder: 3, weightMode: 'per_hand' }],
  sets: sets.map(item => item.sessionExerciseId === 'e0' ? { ...item, sessionExerciseId: 'new', targets: { ...item.targets, targetWeightKg: null } } : item),
  replacements: [{ id: 'r', sessionId: 's', fromExerciseId: 'e0', toExerciseId: 'new', activeSetId: 'set0', remainingSetCount: 2, changedAt: stamp }],
};
const selected: WorkoutSession = { ...initial, selectedExerciseId: 'e2' };
const performance = { id: 'perf', sessionId: 's', sessionSetId: 'set0', sortOrder: 0, weightKg: 40, reps: 8, rir: 2, performedAt: stamp, advancedAt: null };
const rest = { id: 'rest', sessionId: 's', performedSetId: 'perf', plannedSeconds: 30, startedAt: stamp, endedAt: null, chronologicalMs: null, activeMs: null, pauses: [] };
const resting: WorkoutSession = { ...initial, performances: [performance], rests: [rest] };
const completed: WorkoutSession = { ...replacement, status: 'completed', finishedAt: '2026-10-14T13:00:00.000Z',
  performances: sets.map((series, i) => ({ ...performance, id: `perf${i}`, sessionSetId: series.id, sortOrder: i, weightKg: i === 2 ? null : i === 1 ? 20 : i === 3 ? 10 : 40,
    reps: i === 1 ? 10 : 8, rir: i === 2 ? null : i === 1 ? 0 : 2, advancedAt: stamp })),
};
const repository = {
  history: { previousPerformance: jest.fn<() => Promise<null>>() },
  getSession: jest.fn<SessionRepository['getSession']>(), replaceExercise: jest.fn<SessionRepository['replaceExercise']>(),
  chooseNextExercise: jest.fn<SessionRepository['chooseNextExercise']>(), validateSet: jest.fn<SessionRepository['validateSet']>(),
  completeRest: jest.fn<SessionRepository['completeRest']>(), finishSession: jest.fn<SessionRepository['finishSession']>(),
  listCompletedSessions: jest.fn<SessionRepository['listCompletedSessions']>(),
};
const catalog = { listCatalog: jest.fn<() => Promise<ExerciseCatalogItem[]>>() };
function alertButton(name: string) {
  const calls = jest.mocked(Alert.alert).mock.calls, button = calls[calls.length - 1]?.[2]?.find(item => item.text === name);
  expect(button).toBeTruthy(); act(() => button?.onPress?.());
}
function deferred<T>() { let resolve!: (value: T) => void; const promise = new Promise<T>(done => { resolve = done; }); return { promise, resolve }; }
const replacementProps = { sessionId: 's', exerciseId: 'e0', setId: 'set0' };

beforeEach(() => {
  jest.resetAllMocks();
  repository.history.previousPerformance.mockResolvedValue(null); mockFocusCleanups.clear(); mockFocusEffects.clear();
  jest.spyOn(Alert, 'alert').mockImplementation(() => undefined);
  jest.spyOn(AppState, 'addEventListener').mockImplementation(() => ({ remove: jest.fn() }));
  Object.defineProperty(AppState, 'currentState', { value: 'active', writable: true, configurable: true });
  repository.getSession.mockResolvedValue(initial); repository.replaceExercise.mockResolvedValue(replacement); repository.chooseNextExercise.mockResolvedValue(selected);
  repository.validateSet.mockResolvedValue(resting); repository.listCompletedSessions.mockResolvedValue([]);
  catalog.listCatalog.mockResolvedValue([alternative, { ...alternative, id: 'other', name: 'Presse à cuisses', muscleGroup: 'Jambes', isCustom: false }]);
  jest.mocked(useSessions).mockReturnValue(repository as unknown as SessionRepository);
  jest.mocked(useTraining).mockReturnValue(catalog as unknown as ReturnType<typeof useTraining>);
});
afterEach(() => { cleanup(); jest.restoreAllMocks(); });

describe('M2 : remplacement temporaire confirmé', () => {
  test('la recherche inclut les exercices personnalisés et annonce les charges effacées avant toute écriture', async () => {
    const view = render(<SessionReplacement {...replacementProps} />);
    await view.findByText('Exercice personnalisé');
    fireEvent.changeText(view.getByLabelText('Rechercher un remplacement'), 'developpe HALTERES');
    expect(view.queryByText('Presse à cuisses')).toBeNull();
    fireEvent.press(view.getByRole('button', { name: `Remplacer par ${alternative.name}` }));
    expect(Alert.alert).toHaveBeenCalledWith('Remplacer cet exercice ?', expect.stringContaining('charges cibles restantes seront effacées'), expect.any(Array), expect.any(Object));
    expect(repository.replaceExercise).not.toHaveBeenCalled(); alertButton('Annuler');
    expect(repository.replaceExercise).not.toHaveBeenCalled(); expect(router.dismissTo).not.toHaveBeenCalled();
  });
  test('confirmation et double clic ne produisent qu’un remplacement, puis reviennent à la séance', async () => {
    const pending = deferred<WorkoutSession>(); repository.replaceExercise.mockReturnValueOnce(pending.promise);
    const view = render(<SessionReplacement {...replacementProps} />);
    const row = await view.findByRole('button', { name: `Remplacer par ${alternative.name}` });
    fireEvent.press(row); fireEvent.press(row); expect(Alert.alert).toHaveBeenCalledTimes(1);
    alertButton('Remplacer'); alertButton('Remplacer');
    expect(repository.replaceExercise).toHaveBeenCalledTimes(1);
    expect(repository.replaceExercise).toHaveBeenCalledWith('s', 'e0', alternative.id, 'set0');
    expect(router.dismissTo).not.toHaveBeenCalled();
    await act(async () => { pending.resolve(replacement); await pending.promise; });
    expect(router.dismissTo).toHaveBeenCalledWith({ pathname: '/sessions/[sessionId]', params: { sessionId: 's' } });
  });
  test('un échec conserve l’écran et permet une nouvelle confirmation, sans masquer l’erreur', async () => {
    repository.replaceExercise.mockRejectedValueOnce(new Error('Sauvegarde impossible'));
    const view = render(<SessionReplacement {...replacementProps} />);
    fireEvent.press(await view.findByRole('button', { name: `Remplacer par ${alternative.name}` })); alertButton('Remplacer');
    await view.findByText('Sauvegarde impossible'); expect(router.dismissTo).not.toHaveBeenCalled();
    fireEvent.press(view.getByRole('button', { name: `Remplacer par ${alternative.name}` })); alertButton('Remplacer');
    await waitFor(() => expect(router.dismissTo).toHaveBeenCalledTimes(1));
  });
  test('une confirmation tardive après sortie ne modifie aucune série', async () => {
    const view = render(<SessionReplacement {...replacementProps} />);
    fireEvent.press(await view.findByRole('button', { name: `Remplacer par ${alternative.name}` }));
    act(() => mockFocusCleanups.forEach(blur => blur())); alertButton('Remplacer');
    expect(repository.replaceExercise).not.toHaveBeenCalled();
  });
  test('une ancienne route ou un repos actif ne permettent pas de remplacer une série validée', async () => {
    repository.getSession.mockResolvedValue(resting);
    const view = render(<SessionReplacement {...replacementProps} />);
    await view.findByText(/Le repos doit être terminé manuellement/);
    expect(view.queryByLabelText('Rechercher un remplacement')).toBeNull(); expect(repository.replaceExercise).not.toHaveBeenCalled();
  });
  test('retour d’un remplacement : le même identifiant de série n’emporte pas les champs réels de l’ancien exercice', async () => {
    const view = render(<SessionScreen sessionId="s" />);
    fireEvent.changeText(await view.findByLabelText('Charge réelle (kg)'), '80');
    fireEvent.changeText(view.getByLabelText('Répétitions réelles'), '8');
    repository.getSession.mockResolvedValue(replacement);
    act(() => {
      mockFocusCleanups.forEach(blur => blur());
      mockFocusEffects.forEach(effect => effect());
    });
    await view.findByText(alternative.name);
    await waitFor(() => expect(view.getByLabelText('Charge réelle (kg)').props.value).toBe(''));
    expect(view.getByLabelText('Répétitions réelles').props.value).toBe('');
    expect(repository.validateSet).not.toHaveBeenCalled();
  });
});

describe('M2 : exercices restants et repos préservé', () => {
  test('la grille exclut les exercices terminés et conserve les séries encore à faire', async () => {
    repository.getSession.mockResolvedValue({ ...initial, performances: [{ ...performance, sessionSetId: 'set2', advancedAt: stamp }] });
    const view = render(<RemainingExercises sessionId="s" />);
    await view.findByRole('button', { name: 'Choisir Barre' });
    expect(view.queryByRole('button', { name: 'Choisir Tractions' })).toBeNull();
    expect(view.getByRole('button', { name: 'Choisir Curl' })).toBeTruthy();
    expect(view.getByText('2 séries restantes')).toBeTruthy();
  });
  test('choisir un exercice plus loin ouvre la séance sans créer ni valider une performance', async () => {
    const view = render(<RemainingExercises sessionId="s" />);
    fireEvent.press(await view.findByRole('button', { name: 'Choisir Curl' }));
    await waitFor(() => expect(router.dismissTo).toHaveBeenCalledTimes(1));
    expect(repository.chooseNextExercise).toHaveBeenCalledWith('s', 'e2', 'set0');
    expect(repository.validateSet).not.toHaveBeenCalled(); expect(repository.completeRest).not.toHaveBeenCalled();
  });
  test('un choix pendant le repos exige une décision explicite et ne clôture jamais le chronomètre', async () => {
    repository.getSession.mockResolvedValue(resting);
    const view = render(<RemainingExercises sessionId="s" />);
    fireEvent.press(await view.findByRole('button', { name: 'Choisir Curl' }));
    expect(Alert.alert).toHaveBeenCalledWith('Repos encore en cours', expect.stringContaining('Terminez-le manuellement'), expect.any(Array), expect.any(Object));
    alertButton('Annuler'); expect(repository.chooseNextExercise).not.toHaveBeenCalled();
    fireEvent.press(view.getByRole('button', { name: 'Choisir Curl' })); alertButton('Choisir');
    await waitFor(() => expect(router.dismissTo).toHaveBeenCalledTimes(1));
    expect(repository.chooseNextExercise).toHaveBeenCalledWith('s', 'e2', 'set1');
    expect(repository.completeRest).not.toHaveBeenCalled();
  });
  test('un choix enregistré est retrouvé à la réouverture avec une seule série et des champs réels vides', async () => {
    repository.getSession.mockResolvedValue(selected);
    const view = render(<SessionScreen sessionId="s" />);
    await view.findByText('Curl');
    expect(view.queryByText('Barre')).toBeNull(); expect(view.queryByText('Tractions')).toBeNull();
    expect(view.getByLabelText('Charge réelle (kg)').props.value).toBe('');
    expect(view.getByLabelText('Répétitions réelles').props.value).toBe('');
  });
  test('une erreur de sélection conserve la grille et propose une actualisation sans passage prématuré', async () => {
    repository.chooseNextExercise.mockRejectedValueOnce(new Error('La série active a changé'));
    const view = render(<RemainingExercises sessionId="s" />);
    fireEvent.press(await view.findByRole('button', { name: 'Choisir Curl' }));
    await view.findByText('La série active a changé'); expect(router.dismissTo).not.toHaveBeenCalled();
    fireEvent.press(view.getByRole('button', { name: 'Actualiser les exercices' }));
    await waitFor(() => expect(repository.getSession).toHaveBeenCalledTimes(2));
    await view.findByRole('button', { name: 'Choisir Curl' });
  });
});

describe('M2 : bilan réel et accès après fermeture', () => {
  test('le bilan utilise les résultats, exclut le RIR vide et nomme le remplacement effectivement réalisé', async () => {
    repository.getSession.mockResolvedValue(completed);
    const view = render(<SessionScreen sessionId="s" />);
    await view.findByText('Entraînement enregistré');
    expect(view.getByLabelText('Tonnage enregistré').props.children).toBe('600 kg');
    expect(view.getByLabelText('Durée totale').props.children).toBe('1 h 00 min');
    expect(view.getByLabelText('Séries réalisées').props.children).toBe('4');
    expect(view.getByLabelText('RIR moyen').props.children).toBe('1,33');
    expect(view.getByText(alternative.name)).toBeTruthy(); expect(view.getByText('En remplacement de Barre')).toBeTruthy();
    expect(view.queryByText('Barre')).toBeNull(); expect(view.queryByLabelText('Répétitions réelles')).toBeNull();
    fireEvent.press(view.getByRole('button', { name: 'Convention de calcul du tonnage' }));
    expect(view.getByText(/sans supposer deux haltères/)).toBeTruthy();
  });
  test('aucune charge ou aucun RIR donnent des états neutres sans fausses valeurs', async () => {
    repository.getSession.mockResolvedValue({ ...completed, performances: completed.performances.map(item => ({ ...item, weightKg: null, rir: null })) });
    const view = render(<SessionScreen sessionId="s" />);
    await view.findByText('Entraînement enregistré');
    expect(view.getByLabelText('Tonnage enregistré').props.children).toBe('—');
    expect(view.getByLabelText('RIR moyen').props.children).toBe('—'); expect(view.getByText('Aucun RIR renseigné.')).toBeTruthy();
  });
  test('les bilans sauvegardés offrent un accès indépendant du programme source', async () => {
    repository.listCompletedSessions.mockResolvedValue([{ id: 's', workoutName: 'Séance supprimée du programme', programName: 'Programme supprimé', startedAt: stamp, finishedAt: completed.finishedAt, performedSetCount: 4 }]);
    const view = render(<CompletedSessions />);
    fireEvent.press(await view.findByRole('button', { name: 'Voir le bilan Séance supprimée du programme' }));
    expect(router.push).toHaveBeenCalledWith({ pathname: '/sessions/[sessionId]', params: { sessionId: 's' } });
    expect(repository.validateSet).not.toHaveBeenCalled(); expect(repository.finishSession).not.toHaveBeenCalled();
  });
  test('la liste sans entraînement réalisé affiche un état vide', async () => {
    const view = render(<CompletedSessions />); await view.findByText('Votre premier bilan');
    expect(view.queryByText(/kg/)).toBeNull();
  });
  test('un remplacement partiel affiche séparément l’exercice initial réellement fait et son alternative', async () => {
    repository.getSession.mockResolvedValue({ ...completed, sets: completed.sets.map(series => series.id === 'set0' ? { ...series, sessionExerciseId: 'e0' } : series) });
    const view = render(<SessionScreen sessionId="s" />);
    await view.findByText('Entraînement enregistré');
    expect(view.getByText('Barre')).toBeTruthy(); expect(view.getByText(alternative.name)).toBeTruthy();
    expect(view.getByText('40 kg · 8 reps · RIR 2')).toBeTruthy();
    expect(view.getByText('20 kg / haltère · 10 reps · RIR 0')).toBeTruthy();
  });
});

test('le menu secondaire ouvre les trois actions sans transformer la série active en tableau', async () => {
  const view = render(<SessionScreen sessionId="s" />);
  fireEvent.press(await view.findByRole('button', { name: 'Actions de séance' }));
  expect(view.getByRole('button', { name: 'Modifier les objectifs de la série' })).toBeTruthy();
  expect(view.getByRole('button', { name: 'Remplacer cet exercice' })).toBeTruthy();
  fireEvent.press(view.getByRole('button', { name: 'Choisir le prochain exercice' }));
  await waitFor(() => expect(router.push).toHaveBeenCalledWith({ pathname: '/sessions/[sessionId]/exercises', params: { sessionId: 's' } }));
  expect(repository.validateSet).not.toHaveBeenCalled();
});
