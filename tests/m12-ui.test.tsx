import { afterEach, beforeEach, describe, expect, jest, test } from '@jest/globals';
import { act, cleanup, fireEvent, render, waitFor } from '@testing-library/react-native';
import { router } from 'expo-router';
import { AppState } from 'react-native';
import type { SessionRepository } from '../src/db/sessionRepository';
import type { PerformedSet, RestInterval, SessionExercise, SessionSet, WorkoutSession } from '../src/domain/session';
import { SessionScreen } from '../src/features/sessions/SessionScreen';
import { SessionSetEditor } from '../src/features/sessions/SessionSetEditor';
import { RestTimer } from '../src/features/sessions/RestTimer';
import { parseActualDraft } from '../src/features/sessions/shared';
import { useSessions } from '../src/store/SessionProvider';

const mockFocusCleanups = new Set<() => void>();
jest.mock('expo-router', () => {
  const React = require('react') as typeof import('react');
  return { router: { push: jest.fn(), dismissTo: jest.fn(), back: jest.fn(), canGoBack: jest.fn() },
    useFocusEffect: (effect: () => void | (() => void)) => React.useEffect(() => {
      const cleanupFocus = effect();
      if (!cleanupFocus) return undefined;
      mockFocusCleanups.add(cleanupFocus);
      return () => { mockFocusCleanups.delete(cleanupFocus); cleanupFocus(); };
    }, [effect]),
  };
});
jest.mock('../src/store/SessionProvider', () => ({ useSessions: jest.fn() }));
jest.mock('../src/features/sessions/useRestAlert', () => ({ useRestAlert: () => false }));
jest.mock('@expo/vector-icons', () => ({ Ionicons: () => null }));
jest.mock('react-native-safe-area-context', () => jest.requireActual<{ default: typeof import('react-native-safe-area-context') }>('react-native-safe-area-context/jest/mock').default);

const stamp = '2026-10-14T10:00:00.000Z';
const exercise: SessionExercise = { id: 'exercise', sessionId: 'session', sourceWorkoutExerciseId: 'planned-exercise', sourceCatalogExerciseId: 'catalog', sortOrder: 0,
  name: 'Développé couché', muscleGroup: 'Pectoraux', equipment: 'Barre', instructions: '', notes: '', weightMode: 'total' };
const targets = { repsMin: 8, repsMax: 10, targetWeightKg: 80, targetRir: 2, restAfterSec: 60 };
const first: SessionSet = { id: 'first', sessionId: 'session', sessionExerciseId: 'exercise', sourceSetTemplateId: 'planned-first', sortOrder: 0,
  seriesIndex: 0, label: 'Top set', kind: 'top_set', notes: '', targets, originalTargets: targets };
const second: SessionSet = { ...first, id: 'second', sortOrder: 1, seriesIndex: 1, sourceSetTemplateId: 'planned-second', label: 'Back-off', kind: 'back_off',
  targets: { ...targets, restAfterSec: 120 } };
const third: SessionSet = { ...first, id: 'third', sortOrder: 2, seriesIndex: 2, sourceSetTemplateId: 'planned-third', label: 'Finisher', kind: 'work',
  targets: { ...targets, restAfterSec: 180 } };
const initial: WorkoutSession = { id: 'session', sourceWorkoutTemplateId: 'template', sourceProgramId: 'program', workoutName: 'Ma séance', programName: 'Mon programme',
  status: 'active', startedAt: stamp, finishedAt: null, exercises: [exercise], sets: [first, second, third], performances: [], rests: [] };
const performed: PerformedSet = { id: 'performance', sessionId: 'session', sessionSetId: 'first', sortOrder: 0, weightKg: 72.5, reps: 9, rir: null, performedAt: stamp, advancedAt: null };
const rest: RestInterval = { id: 'rest', sessionId: 'session', performedSetId: performed.id, plannedSeconds: 60, startedAt: stamp,
  endedAt: null, chronologicalMs: null, activeMs: null, pauses: [] };
const resting: WorkoutSession = { ...initial, performances: [performed], rests: [rest] };
const advanced: WorkoutSession = { ...resting, performances: [{ ...performed, advancedAt: stamp }], rests: [{ ...rest, endedAt: stamp, chronologicalMs: 10000, activeMs: 10000 }] };
const allDone: WorkoutSession = { ...initial, performances: [first, second, third].map((series, index) => ({ ...performed, id: `performance-${index}`, sessionSetId: series.id, sortOrder: index, advancedAt: stamp })) };
const mockSessions = {
  history: { previousPerformance: jest.fn<() => Promise<null>>() },
  getSession: jest.fn<SessionRepository['getSession']>(), getActiveSession: jest.fn<SessionRepository['getActiveSession']>(),
  validateSet: jest.fn<SessionRepository['validateSet']>(), pauseRest: jest.fn<SessionRepository['pauseRest']>(),
  resumeRest: jest.fn<SessionRepository['resumeRest']>(), completeRest: jest.fn<SessionRepository['completeRest']>(),
  advanceAfterSet: jest.fn<SessionRepository['advanceAfterSet']>(), finishSession: jest.fn<SessionRepository['finishSession']>(),
  updateSet: jest.fn<SessionRepository['updateSet']>(),
  canUpdateProgram: jest.fn<SessionRepository['canUpdateProgram']>(),
};
function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>(done => { resolve = done; });
  return { promise, resolve };
}
beforeEach(() => {
  jest.resetAllMocks();
  mockSessions.history.previousPerformance.mockResolvedValue(null);
  jest.spyOn(AppState, 'addEventListener').mockImplementation(() => ({ remove: jest.fn() })); mockFocusCleanups.clear();
  Object.defineProperty(AppState, 'currentState', { value: 'active', writable: true, configurable: true });
  mockSessions.getSession.mockResolvedValue(initial); mockSessions.getActiveSession.mockResolvedValue(initial);
  mockSessions.validateSet.mockResolvedValue(resting); mockSessions.completeRest.mockResolvedValue(advanced);
  mockSessions.advanceAfterSet.mockResolvedValue(advanced);
  mockSessions.finishSession.mockResolvedValue({ ...allDone, status: 'completed', finishedAt: stamp });
  mockSessions.updateSet.mockResolvedValue(initial); mockSessions.canUpdateProgram.mockResolvedValue(true);
  mockSessions.pauseRest.mockResolvedValue({ ...resting, rests: [{ ...rest, pauses: [{ id: 'pause', startedAt: stamp, endedAt: null }] }] });
  mockSessions.resumeRest.mockResolvedValue(resting);
  jest.mocked(useSessions).mockReturnValue(mockSessions as unknown as SessionRepository);
});
afterEach(() => { cleanup(); jest.restoreAllMocks(); jest.useRealTimers(); });

describe('M1.2 : une seule série et sauvegarde explicite', () => {
  test('seule la première série est affichée, avec trois champs réels vides et des cibles distinctes', async () => {
    const view = render(<SessionScreen sessionId="session" />);
    await view.findByText(/Top set · 1 \/ 3/);
    expect(view.queryByText(/Back-off|Finisher/)).toBeNull();
    expect(view.getByText('8–10 répétitions · 80 kg · RIR 2')).toBeTruthy();
    for (const label of ['Charge réelle (kg)', 'Répétitions réelles', 'RIR réel']) expect(view.getByLabelText(label).props.value).toBe('');
    fireEvent.press(view.getByRole('button', { name: 'Valider la série' }));
    expect(mockSessions.validateSet).not.toHaveBeenCalled();
    expect(view.getByRole('alert')).toBeTruthy();
  });

  test('la validation sauvegarde les valeurs réellement saisies puis ouvre le repos de la série', async () => {
    jest.useFakeTimers().setSystemTime(new Date(stamp));
    const view = render(<SessionScreen sessionId="session" />);
    fireEvent.changeText(await view.findByLabelText('Charge réelle (kg)'), '72,5');
    fireEvent.changeText(view.getByLabelText('Répétitions réelles'), '9');
    fireEvent.press(view.getByRole('button', { name: 'Valider la série' }));
    await view.findByText('Repos entre les séries');
    expect(mockSessions.validateSet).toHaveBeenCalledWith('session', 'first', { weightKg: 72.5, reps: 9, rir: null }, 0);
    expect(view.queryByLabelText('Répétitions réelles')).toBeNull();
    expect(view.getByText('Repos prévu')).toBeTruthy();
    expect(view.getByRole('button', { name: 'Passer à la série suivante' })).toBeTruthy();
    expect(mockSessions.completeRest).not.toHaveBeenCalled();
  });

  test('charge au poids du corps et RIR peuvent rester vides sans copier les objectifs', async () => {
    const view = render(<SessionScreen sessionId="session" />);
    fireEvent.changeText(await view.findByLabelText('Répétitions réelles'), '12');
    fireEvent.press(view.getByRole('button', { name: 'Valider la série' }));
    await waitFor(() => expect(mockSessions.validateSet).toHaveBeenCalledWith('session', 'first', { weightKg: null, reps: 12, rir: null }, 0));
    await view.findByText('Repos entre les séries');
  });

  test('une erreur conserve les champs, bloque les doubles validations en attente puis permet de réessayer', async () => {
    const pending = deferred<WorkoutSession>(); mockSessions.validateSet.mockReturnValueOnce(pending.promise);
    const view = render(<SessionScreen sessionId="session" />);
    fireEvent.changeText(await view.findByLabelText('Répétitions réelles'), '9');
    const validate = view.getByRole('button', { name: 'Valider la série' });
    fireEvent.press(validate); fireEvent.press(validate);
    expect(mockSessions.validateSet).toHaveBeenCalledTimes(1);
    expect(view.getByRole('button', { name: 'Retour' }).props.accessibilityState.disabled).toBe(true);
    await act(async () => { pending.resolve(initial); await pending.promise; });
    mockSessions.validateSet.mockRejectedValueOnce(new Error('Stockage indisponible'));
    fireEvent.press(view.getByRole('button', { name: 'Valider la série' }));
    await view.findByText('Stockage indisponible');
    expect(view.getByLabelText('Répétitions réelles').props.value).toBe('9');
    expect(router.dismissTo).not.toHaveBeenCalled();
    fireEvent.press(view.getByRole('button', { name: 'Valider la série' }));
    await view.findByText('Repos entre les séries');
  });

  test('la sortie temporaire ne valide aucun champ et ne termine pas la séance', async () => {
    const view = render(<SessionScreen sessionId="session" />);
    fireEvent.changeText(await view.findByLabelText('Répétitions réelles'), '9');
    fireEvent.press(view.getByRole('button', { name: 'Quitter et reprendre plus tard' }));
    expect(router.dismissTo).toHaveBeenCalledWith({ pathname: '/', params: { universe: 'musculation' } });
    expect(mockSessions.validateSet).not.toHaveBeenCalled(); expect(mockSessions.finishSession).not.toHaveBeenCalled();
  });

  test('sans repos, une étape manuelle permet de continuer sans revenir à une liste', async () => {
    mockSessions.getSession.mockResolvedValue({ ...initial, performances: [performed] });
    const view = render(<SessionScreen sessionId="session" />);
    await view.findByText('Série enregistrée');
    expect(view.queryByLabelText('Répétitions réelles')).toBeNull();
    fireEvent.press(view.getByRole('button', { name: 'Passer à la série suivante' }));
    await view.findByText(/Back-off · 2 \/ 3/);
    expect(mockSessions.advanceAfterSet).toHaveBeenCalledWith('session', 'performance');
    expect(view.getByLabelText('Répétitions réelles').props.value).toBe('');
  });

  test('la dernière série propose une fin manuelle et conserve une confirmation véridique', async () => {
    mockSessions.getSession.mockResolvedValue(allDone);
    const view = render(<SessionScreen sessionId="session" />);
    await view.findByText('Toutes les séries sont enregistrées');
    expect(view.queryByText('Repos prévu')).toBeNull();
    expect(mockSessions.finishSession).not.toHaveBeenCalled();
    fireEvent.press(view.getByRole('button', { name: 'Terminer la séance' }));
    await view.findByText('Entraînement enregistré');
    expect(view.getByLabelText('Séries réalisées').props.children).toBe('3');
    expect(mockSessions.finishSession).toHaveBeenCalledTimes(1);
    expect(view.queryByRole('button', { name: 'Terminer la séance' })).toBeNull();
  });

  test('le menu secondaire ne concerne que les objectifs de la série active', async () => {
    const view = render(<SessionScreen sessionId="session" />);
    fireEvent.press(await view.findByRole('button', { name: 'Actions de séance' }));
    fireEvent.press(await view.findByRole('button', { name: 'Modifier les objectifs de la série' }));
    await waitFor(() => expect(router.push).toHaveBeenCalledWith({ pathname: '/sessions/[sessionId]/edit', params: { sessionId: 'session', setId: 'first' } }));
  });
});

describe('M1.2 : repos calculé depuis les horodatages', () => {
  beforeEach(() => {
  jest.spyOn(AppState, 'addEventListener').mockImplementation(() => ({ remove: jest.fn() })); jest.useFakeTimers().setSystemTime(new Date(stamp)); });

  test('le passage anticipé ferme le bon intervalle et affiche la prochaine série avec des champs vides', async () => {
    mockSessions.getSession.mockResolvedValue(resting);
    const view = render(<SessionScreen sessionId="session" />);
    fireEvent.press(await view.findByRole('button', { name: 'Passer à la série suivante' }));
    await view.findByText(/Back-off · 2 \/ 3/);
    expect(mockSessions.completeRest).toHaveBeenCalledWith('session', 'rest');
    expect(view.getByLabelText('Charge réelle (kg)').props.value).toBe('');
  });

  test('l’expiration affiche le dépassement et change le bouton sans progression automatique', () => {
    const complete = jest.fn();
    const view = render(<RestTimer rest={rest} busy={false} onPause={jest.fn()} onResume={jest.fn()} onComplete={complete} />);
    act(() => { jest.advanceTimersByTime(61000); });
    expect(view.getByText('+00:01')).toBeTruthy();
    expect(view.getByRole('button', { name: 'Repos terminé' })).toBeTruthy();
    expect(complete).not.toHaveBeenCalled();
    fireEvent.press(view.getByRole('button', { name: 'Repos terminé' }));
    expect(complete).toHaveBeenCalledTimes(1);
    expect(view.queryByText(/\+15|\+30/)).toBeNull();
  });

  test('une reprise après fermeture recalcule directement le dépassement conservé', async () => {
    jest.setSystemTime(new Date(Date.parse(stamp) + 90000));
    mockSessions.getSession.mockResolvedValue(resting);
    const view = render(<SessionScreen sessionId="session" />);
    await view.findByText('+00:30');
    expect(view.getByLabelText('Repos réel écoulé').props.children).toBe('01:30');
    expect(mockSessions.validateSet).not.toHaveBeenCalled();
    expect(mockSessions.completeRest).not.toHaveBeenCalled();
  });

  test('la pause conservée fige le minuteur mais le repos réel continue et la reprise est explicite', () => {
    jest.setSystemTime(new Date(Date.parse(stamp) + 30000));
    const pause = jest.fn(), resume = jest.fn();
    const view = render(<RestTimer rest={{ ...rest, pauses: [{ id: 'pause', startedAt: new Date(Date.parse(stamp) + 10000).toISOString(), endedAt: null }] }} busy={false} onPause={pause} onResume={resume} onComplete={jest.fn()} />);
    expect(view.getByLabelText('Temps restant').props.children).toBe('00:50');
    act(() => { jest.advanceTimersByTime(10000); });
    expect(view.getByLabelText('Temps restant').props.children).toBe('00:50');
    expect(view.getByLabelText('Repos réel écoulé').props.children).toBe('00:40');
    fireEvent.press(view.getByRole('button', { name: 'Reprendre le minuteur' }));
    expect(resume).toHaveBeenCalledTimes(1); expect(pause).not.toHaveBeenCalled();
  });

  test('pause et reprise utilisent le bon intervalle persistant', async () => {
    mockSessions.getSession.mockResolvedValue(resting);
    const view = render(<SessionScreen sessionId="session" />);
    fireEvent.press(await view.findByRole('button', { name: 'Mettre le minuteur en pause' }));
    fireEvent.press(await view.findByRole('button', { name: 'Reprendre le minuteur' }));
    await view.findByRole('button', { name: 'Mettre le minuteur en pause' });
    expect(mockSessions.pauseRest).toHaveBeenCalledWith('session', 'rest');
    expect(mockSessions.resumeRest).toHaveBeenCalledWith('session', 'rest');
  });

  test('un échec de fin de repos conserve le chronomètre et permet une nouvelle tentative', async () => {
    mockSessions.getSession.mockResolvedValue(resting);
    mockSessions.completeRest.mockRejectedValueOnce(new Error('Impossible d’enregistrer le repos'));
    const view = render(<SessionScreen sessionId="session" />);
    fireEvent.press(await view.findByRole('button', { name: 'Passer à la série suivante' }));
    await view.findByText('Impossible d’enregistrer le repos');
    expect(view.queryByLabelText('Répétitions réelles')).toBeNull();
    fireEvent.press(view.getByRole('button', { name: 'Passer à la série suivante' }));
    await view.findByText(/Back-off · 2 \/ 3/);
  });
});

describe('M1.2 : modification explicite des objectifs', () => {
  test('Cette séance est sélectionnée par défaut, la grille sauvegarde les objectifs sans performances', async () => {
    const view = render(<SessionSetEditor sessionId="session" setId="first" />);
    await waitFor(() => expect(view.getByLabelText('Charge cible (kg)').props.value).toBe('80'));
    expect(view.getByRole('radio', { name: 'Cette séance' }).props.accessibilityState.checked).toBe(true);
    fireEvent.changeText(view.getByLabelText('Charge cible (kg)'), '75,5');
    fireEvent.changeText(view.getByLabelText('Repos cible (s)'), '135');
    fireEvent.press(view.getByRole('button', { name: 'Enregistrer les objectifs' }));
    await waitFor(() => expect(mockSessions.updateSet).toHaveBeenCalledWith('session', 'first', { ...targets, label: 'Top set', kind: 'top_set', notes: '', loadRule: null, targetWeightKg: 75.5, restAfterSec: 135 }, 'session'));
    await waitFor(() => expect(router.dismissTo).toHaveBeenCalledWith({ pathname: '/sessions/[sessionId]', params: { sessionId: 'session' } }));
    expect(mockSessions.validateSet).not.toHaveBeenCalled();
  });

  test('Programme est un choix explicite et transmet sa portée sans toucher aux résultats', async () => {
    const view = render(<SessionSetEditor sessionId="session" setId="first" />);
    await waitFor(() => expect(view.getByRole('radio', { name: 'Programme' }).props.accessibilityState.disabled).toBe(false));
    fireEvent.press(view.getByRole('radio', { name: 'Programme' }));
    fireEvent.changeText(view.getByLabelText('RIR cible'), '');
    fireEvent.press(view.getByRole('button', { name: 'Enregistrer les objectifs' }));
    await waitFor(() => expect(mockSessions.updateSet).toHaveBeenCalledWith('session', 'first', { ...targets, label: 'Top set', kind: 'top_set', notes: '', loadRule: null, targetRir: null }, 'program'));
    await waitFor(() => expect(router.dismissTo).toHaveBeenCalledWith({ pathname: '/sessions/[sessionId]', params: { sessionId: 'session' } }));
    expect(mockSessions.validateSet).not.toHaveBeenCalled();
  });

  test('une erreur ne quitte pas l’éditeur, et Annuler ne sauvegarde pas', async () => {
    mockSessions.updateSet.mockRejectedValueOnce(new Error('La série du programme a été supprimée'));
    const view = render(<SessionSetEditor sessionId="session" setId="first" />);
    await view.findByLabelText('Repos cible (s)');
    fireEvent.changeText(view.getByLabelText('Repos cible (s)'), '90');
    fireEvent.press(view.getByRole('button', { name: 'Enregistrer les objectifs' }));
    await view.findByText('La série du programme a été supprimée');
    expect(router.dismissTo).not.toHaveBeenCalled();
    expect(view.getByLabelText('Repos cible (s)').props.value).toBe('90');
    fireEvent.press(view.getByRole('button', { name: 'Annuler' }));
    expect(mockSessions.updateSet).toHaveBeenCalledTimes(1);
  });

  test('une série déjà validée ou une autre série n’est pas modifiable depuis une route ancienne', async () => {
    mockSessions.getSession.mockResolvedValue(advanced);
    const view = render(<SessionSetEditor sessionId="session" setId="first" />);
    await view.findByText('Cette série n’est pas modifiable : elle est validée, retirée ou la séance est terminée.');
    expect(view.queryByRole('button', { name: 'Enregistrer les objectifs' })).toBeNull();
    expect(mockSessions.updateSet).not.toHaveBeenCalled();
  });

  test('une sauvegarde doublée reste unique, sans navigation tardive après perte du focus', async () => {
    const pending = deferred<WorkoutSession>(); mockSessions.updateSet.mockReturnValue(pending.promise);
    const view = render(<SessionSetEditor sessionId="session" setId="first" />);
    const save = await view.findByRole('button', { name: 'Enregistrer les objectifs' });
    fireEvent.press(save); fireEvent.press(save);
    expect(mockSessions.updateSet).toHaveBeenCalledTimes(1);
    act(() => mockFocusCleanups.forEach(blur => blur()));
    await act(async () => { pending.resolve(initial); await pending.promise; });
    expect(router.dismissTo).not.toHaveBeenCalled();
  });
});

test('les saisies réelles rejettent les conversions partielles et distinguent vide et zéro', () => {
  expect(parseActualDraft({ weight: '', reps: '0', rir: '' })).toEqual({ weightKg: null, reps: 0, rir: null });
  expect(parseActualDraft({ weight: '0', reps: '8', rir: '0' })).toEqual({ weightKg: 0, reps: 8, rir: 0 });
  for (const reps of ['', '8reps', '2.5', '-2']) expect(() => parseActualDraft({ weight: '', reps, rir: '' })).toThrow();
  expect(() => parseActualDraft({ weight: 'Infinity', reps: '8', rir: '' })).toThrow();
  expect(() => parseActualDraft({ weight: '', reps: '8', rir: '11' })).toThrow();
});
