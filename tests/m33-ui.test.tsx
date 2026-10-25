import { afterEach, beforeEach, expect, jest, test } from '@jest/globals';
import { act, cleanup, fireEvent, render, waitFor } from '@testing-library/react-native';
import { AppState, Text } from 'react-native';
import { router } from 'expo-router';
import type { WorkoutSession } from '../src/domain/session';
import { PreferencesProvider } from '../src/store/PreferencesProvider';
import { SessionProvider } from '../src/store/SessionProvider';
import { SettingsScreen } from '../src/features/settings/SettingsScreen';
import { exportPersonalData } from '../src/data/exportPersonalData';
import { PersonalExportError } from '../src/data/personalExport';

let mockStored: string | null = null;
const mockRead = jest.fn<() => Promise<{ value: string } | null>>();
const mockWrite = jest.fn<(sql: string, key: string, value: string) => Promise<void>>();
const mockDatabase = { getFirstAsync: mockRead, runAsync: mockWrite };
const mockPlayer = { seekTo: jest.fn<() => Promise<void>>(), play: jest.fn() };
const mockAudioMode = jest.fn<(options: unknown) => Promise<void>>();
const mockSessionRepository = { getActiveSession: jest.fn<() => Promise<WorkoutSession | null>>(),
  subscribe: jest.fn<(listener: () => void) => () => void>() };
let mockRefresh: () => void;
const mockFocusCleanups = new Set<() => void>();
jest.mock('expo-router', () => {
  const React = require('react') as typeof import('react');
  return { router: { back: jest.fn(), replace: jest.fn(), canGoBack: jest.fn() },
    useFocusEffect: (effect: () => void | (() => void)) => React.useEffect(() => {
      const close = effect(); if (!close) return;
      mockFocusCleanups.add(close); return () => { mockFocusCleanups.delete(close); close(); };
    }, [effect]) };
});
jest.mock('expo-sqlite', () => ({ useSQLiteContext: () => mockDatabase }));
jest.mock('expo-crypto', () => ({ randomUUID: () => 'unused' }));
jest.mock('expo-audio', () => ({ useAudioPlayer: () => mockPlayer, setAudioModeAsync: (value: unknown) => mockAudioMode(value) }));
jest.mock('../src/db/sessionRepository', () => ({ SessionRepository: class { constructor() { return mockSessionRepository; } } }));
jest.mock('../src/data/exportPersonalData', () => ({ exportPersonalData: jest.fn(), cleanupPersonalExportCache: jest.fn() }));
jest.mock('@expo/vector-icons', () => ({ Ionicons: () => null }));
jest.mock('react-native-safe-area-context', () => jest.requireActual<{ default: typeof import('react-native-safe-area-context') }>('react-native-safe-area-context/jest/mock').default);

const stamp = '2026-10-15T12:00:00.000Z', start = Date.parse(stamp);
const targets = { repsMin: 8, repsMax: 8, targetWeightKg: null, targetRir: null, restAfterSec: 2 };
const session: WorkoutSession = {
  id: 's', sourceWorkoutTemplateId: 'w', sourceProgramId: 'p', workoutName: 'Séance', programName: 'Programme',
  status: 'active', startedAt: stamp, finishedAt: null, selectedExerciseId: null,
  exercises: [{ id: 'e', sessionId: 's', sourceWorkoutExerciseId: 'we', sourceCatalogExerciseId: 'catalog', sortOrder: 0,
    name: 'Exercice', muscleGroup: 'Dos', equipment: 'Salle', instructions: '', notes: '', weightMode: 'total' }],
  sets: [0, 1].map(index => ({ id: `set${index}`, sessionId: 's', sessionExerciseId: 'e', sourceSetTemplateId: `st${index}`,
    sortOrder: index, seriesIndex: index, label: '', kind: 'work', notes: '', targets, originalTargets: targets })),
  performances: [{ id: 'performed', sessionId: 's', sessionSetId: 'set0', sortOrder: 0, weightKg: null, reps: 8, rir: null, performedAt: stamp, advancedAt: null }],
  rests: [{ id: 'rest', sessionId: 's', performedSetId: 'performed', plannedSeconds: 2, startedAt: stamp, endedAt: null,
    chronologicalMs: null, activeMs: null, pauses: [] }],
};
function Screen({ sound = false }: { sound?: boolean }) {
  return <PreferencesProvider>{sound ? <SessionProvider><SettingsScreen /></SessionProvider> : <SettingsScreen />}</PreferencesProvider>;
}
function deferred<T>() { let resolve!: (value: T) => void; const promise = new Promise<T>(done => { resolve = done; }); return { promise, resolve }; }
async function loaded(view: Awaited<ReturnType<typeof render>>) {
  await waitFor(() => expect(view.getByLabelText('Son de fin de repos').props.disabled).toBe(false));
}
async function advance(ms: number) { await act(async () => { jest.advanceTimersByTime(ms); }); }
beforeEach(() => {
  jest.clearAllMocks(); mockFocusCleanups.clear(); mockStored = null;
  mockRead.mockImplementation(async () => mockStored === null ? null : { value: mockStored });
  mockWrite.mockImplementation(async (_sql, _key, value) => { mockStored = value; });
  mockPlayer.seekTo.mockResolvedValue(undefined); mockAudioMode.mockResolvedValue(undefined);
  mockSessionRepository.getActiveSession.mockResolvedValue(session);
  mockSessionRepository.subscribe.mockImplementation(listener => { mockRefresh = listener; return jest.fn(); });
  jest.mocked(exportPersonalData).mockResolvedValue(undefined);
  jest.mocked(router.canGoBack).mockReturnValue(true);
  Object.defineProperty(AppState, 'currentState', { value: 'active', writable: true, configurable: true });
  jest.spyOn(AppState, 'addEventListener').mockImplementation(() => ({ remove: jest.fn() }));
});
afterEach(async () => { await cleanup(); jest.restoreAllMocks(); jest.useRealTimers(); });

test('settings show real units, local-data risks and unavailable restoration, without exporting on mount', async () => {
  const view = await render(<Screen />); await loaded(view);
  expect(view.getByText('Kilogrammes · kg')).toBeTruthy(); expect(view.getByText('Version 0.1.0')).toBeTruthy();
  expect(view.getByText(/Supprimer Logbook, Expo Go ou son stockage/)).toBeTruthy();
  expect(view.getByText(/La restauration n’est pas encore disponible/)).toBeTruthy();
  expect(view.queryByRole('button', { name: 'Restaurer mes données' })).toBeNull();
  expect(view.getAllByRole('switch')).toHaveLength(1); expect(exportPersonalData).not.toHaveBeenCalled();
  await fireEvent.press(view.getByRole('button', { name: 'Retour' })); expect(router.back).toHaveBeenCalledTimes(1);
});
test('changing the switch displays the intent immediately and persists it across provider remount', async () => {
  let view = await render(<Screen />); await loaded(view);
  expect(view.getByLabelText('Son de fin de repos').props.value).toBe(true);
  await fireEvent(view.getByLabelText('Son de fin de repos'), 'valueChange', false);
  await waitFor(() => expect(view.getByLabelText('Son de fin de repos').props.value).toBe(false));
  await waitFor(() => expect(mockStored).toBe('false')); await view.unmount();
  view = await render(<Screen />); await loaded(view); expect(view.getByLabelText('Son de fin de repos').props.value).toBe(false);
});
test('a delayed SQLite write must not disable, revert or relayout the native switch while the latest intent is displayed', async () => {
  const pending = deferred<void>();
  mockWrite.mockImplementation(async (_sql, _key, value) => { await pending.promise; mockStored = value; });
  const view = await render(<Screen />); await loaded(view);
  await fireEvent(view.getByLabelText('Son de fin de repos'), 'valueChange', false);
  expect(view.getByLabelText('Son de fin de repos').props.value).toBe(false);
  expect(view.getByLabelText('Son de fin de repos').props.disabled).toBe(false);
  expect(view.queryByText('Enregistrement…')).toBeNull();
  await act(async () => { pending.resolve(); });
  expect(mockStored).toBe('false');
});
test('rapid alternating taps stay responsive while ordered completions cannot overwrite the latest visible intent', async () => {
  const jobs: { value: string; finish(): void }[] = [];
  mockWrite.mockImplementation((_sql, _key, value) => new Promise(resolve => {
    jobs.push({ value, finish: () => { mockStored = value; resolve(); } });
  }));
  const view = await render(<Screen />); await loaded(view);
  const control = view.getByLabelText('Son de fin de repos');
  await act(() => { for (const value of [false, true, false, true, false]) control.props.onChange({ nativeEvent: { value: value } }); });
  expect(view.getByLabelText('Son de fin de repos').props.value).toBe(false);
  expect(view.getByLabelText('Son de fin de repos').props.disabled).toBe(false);
  for (let i = 0; i < 5; i++) {
    await waitFor(() => expect(jobs).toHaveLength(i + 1));
    expect(jobs[i]!.value).toBe(i % 2 ? 'true' : 'false');
    await act(async () => { jobs[i]!.finish(); });
    expect(view.getByLabelText('Son de fin de repos').props.value).toBe(false);
    expect(view.getByLabelText('Son de fin de repos').props.disabled).toBe(false);
    expect(view.queryByText('Enregistrement…')).toBeNull();
  }
  expect(mockWrite).toHaveBeenCalledTimes(5); expect(mockStored).toBe('false');
  await view.unmount(); const reopened = await render(<Screen />); await loaded(reopened);
  expect(reopened.getByLabelText('Son de fin de repos').props.value).toBe(false);
});
test('an older failed intent cannot roll back a later queued choice or disable its switch', async () => {
  const pending = deferred<void>();
  mockWrite.mockImplementationOnce(async () => { await pending.promise; throw new Error('Première écriture échouée'); });
  const view = await render(<Screen />); await loaded(view); const control = view.getByLabelText('Son de fin de repos');
  await act(() => { control.props.onChange({ nativeEvent: { value: false } }); control.props.onChange({ nativeEvent: { value: true } }); });
  await act(async () => { pending.resolve(); });
  await waitFor(() => expect(mockStored).toBe('true'));
  expect(view.getByLabelText('Son de fin de repos').props.value).toBe(true);
  expect(view.getByLabelText('Son de fin de repos').props.disabled).toBe(false);
  expect(view.queryByText(/Le réglage n’a pas pu être lu ou enregistré/)).toBeNull();
});
test('a failed latest write rolls back to the last actual commit, not the initial default, and retry reads SQLite', async () => {
  const view = await render(<Screen />); await loaded(view);
  await fireEvent(view.getByLabelText('Son de fin de repos'), 'valueChange', false);
  await waitFor(() => expect(mockStored).toBe('false'));
  mockWrite.mockRejectedValueOnce(new Error('Stockage saturé'));
  await fireEvent(view.getByLabelText('Son de fin de repos'), 'valueChange', true);
  await view.findByText(/Le réglage n’a pas pu être lu ou enregistré/);
  expect(view.getByLabelText('Son de fin de repos').props.value).toBe(false);
  expect(mockStored).toBe('false');
  await fireEvent.press(view.getByText('Réessayer le réglage sonore')); await loaded(view);
  expect(view.getByLabelText('Son de fin de repos').props.value).toBe(false);
});
test('leaving settings does not cancel a pending preference commit in the app-level provider', async () => {
  const pending = deferred<void>();
  mockWrite.mockImplementation(async (_sql, _key, value) => { await pending.promise; mockStored = value; });
  const view = await render(<PreferencesProvider><SettingsScreen /></PreferencesProvider>); await loaded(view);
  await fireEvent(view.getByLabelText('Son de fin de repos'), 'valueChange', false);
  await view.rerender(<PreferencesProvider><Text>Accueil</Text></PreferencesProvider>);
  await act(async () => { pending.resolve(); }); expect(mockStored).toBe('false');
  await view.rerender(<PreferencesProvider><SettingsScreen /></PreferencesProvider>); await loaded(view);
  expect(view.getByLabelText('Son de fin de repos').props.value).toBe(false);
});
test('the actual global rest observer plays once with the persisted preference and respects silent mode configuration', async () => {
  jest.useFakeTimers(); jest.setSystemTime(start);
  const view = await render(<Screen sound />); await loaded(view); await advance(2100);
  expect(mockPlayer.play).toHaveBeenCalledTimes(1);
  expect(mockAudioMode).toHaveBeenCalledWith(expect.objectContaining({ playsInSilentMode: false, shouldPlayInBackground: false }));
  await advance(5000); expect(mockPlayer.play).toHaveBeenCalledTimes(1);
  expect(session.rests[0]!.endedAt).toBeNull(); expect(session.performances).toHaveLength(1);
});
test('disabling sound really mutes the active interval, including after reopening settings and the observer', async () => {
  jest.useFakeTimers(); jest.setSystemTime(start);
  let view = await render(<Screen sound />); await loaded(view);
  await fireEvent(view.getByLabelText('Son de fin de repos'), 'valueChange', false);
  await waitFor(() => expect(mockStored).toBe('false')); await view.unmount();
  view = await render(<Screen sound />); await loaded(view); await advance(3000);
  expect(mockPlayer.play).not.toHaveBeenCalled(); expect(mockAudioMode).not.toHaveBeenCalled();
});
test('turning sound back on after expiry does not play a late alarm; the next interval can alert normally', async () => {
  jest.useFakeTimers(); jest.setSystemTime(start); mockStored = 'false';
  const view = await render(<Screen sound />); await loaded(view); await advance(3000);
  await fireEvent(view.getByLabelText('Son de fin de repos'), 'valueChange', true); await loaded(view); await advance(1000);
  expect(mockPlayer.play).not.toHaveBeenCalled();
  mockSessionRepository.getActiveSession.mockResolvedValue({ ...session, rests: [{ ...session.rests[0]!, id: 'next-rest', startedAt: new Date().toISOString() }] });
  await act(async () => { mockRefresh(); }); await advance(2200); expect(mockPlayer.play).toHaveBeenCalledTimes(1);
});
test('pending or failed preference saves are muted, block duplicate writes and remain visible until retry', async () => {
  jest.useFakeTimers(); jest.setSystemTime(start);
  const pending = deferred<void>(); mockWrite.mockImplementation(async () => { await pending.promise; throw new Error('Stockage indisponible'); });
  const view = await render(<Screen sound />); await loaded(view);
  const control = view.getByLabelText('Son de fin de repos');
  await act(() => { control.props.onChange({ nativeEvent: { value: false } }); control.props.onChange({ nativeEvent: { value: false } }); });
  await advance(2200); expect(mockWrite).toHaveBeenCalledTimes(1); expect(mockPlayer.play).not.toHaveBeenCalled();
  await act(async () => { pending.resolve(); });
  expect(view.getByText(/Le réglage n’a pas pu être lu ou enregistré/)).toBeTruthy();
  expect(view.getByLabelText('Son de fin de repos').props.value).toBe(true);
  expect(view.getByLabelText('Son de fin de repos').props.disabled).toBe(true);
  await fireEvent.press(view.getByText('Réessayer le réglage sonore')); await loaded(view);
  expect(view.getByLabelText('Son de fin de repos').props.value).toBe(true); expect(router.back).not.toHaveBeenCalled();
});
test('a failed preference read cannot be mistaken for permission to sound, and retry reads the saved value', async () => {
  jest.useFakeTimers(); jest.setSystemTime(start); mockStored = 'false'; mockRead.mockRejectedValueOnce(new Error('Lecture impossible'));
  const view = await render(<Screen sound />); await view.findByText(/Le réglage n’a pas pu être lu ou enregistré/);
  await advance(2500); expect(mockPlayer.play).not.toHaveBeenCalled();
  await fireEvent.press(view.getByText('Réessayer le réglage sonore')); await loaded(view);
  expect(view.getByLabelText('Son de fin de repos').props.value).toBe(false);
});
test('export is explicit, blocks double presses and navigation, and never claims the sheet saved a file', async () => {
  const pending = deferred<void>(); jest.mocked(exportPersonalData).mockReturnValue(pending.promise);
  const view = await render(<Screen />); await loaded(view);
  const button = view.getByRole('button', { name: 'Exporter mes données' });
  await act(() => { button.props.onClick({ nativeEvent: {}, target: null, currentTarget: null }); button.props.onClick({ nativeEvent: {}, target: null, currentTarget: null }); });
  expect(exportPersonalData).toHaveBeenCalledTimes(1); await fireEvent.press(view.getByRole('button', { name: 'Retour' }));
  expect(router.back).not.toHaveBeenCalled();
  await act(async () => { jest.mocked(exportPersonalData).mock.calls[0]![0]!.onPhase?.('sharing'); });
  expect(view.queryByRole('button', { name: 'Annuler l’export' })).toBeNull();
  await act(async () => { pending.resolve(); });
  expect(view.getByText(/Feuille de partage fermée. Vérifiez votre fichier/)).toBeTruthy();
  expect(view.queryByText('Sauvegarde enregistrée')).toBeNull(); expect(view.getByRole('button', { name: 'Exporter mes données' })).toBeEnabled();
});
test('cancel during preparation aborts the signal, stays on settings and allows a subsequent export', async () => {
  jest.mocked(exportPersonalData).mockImplementation(options => new Promise((_resolve, reject) => {
    options!.signal!.addEventListener('abort', () => reject(new PersonalExportError('cancelled', 'Export annulé. Vos données sont conservées.')), { once: true });
  }));
  const view = await render(<Screen />); await loaded(view); await fireEvent.press(view.getByText('Exporter mes données'));
  const signal = jest.mocked(exportPersonalData).mock.calls[0]![0]!.signal!;
  await fireEvent.press(view.getByText('Annuler l’export')); await view.findByText('Export annulé. Vos données sont conservées.');
  expect(signal.aborted).toBe(true); expect(router.back).not.toHaveBeenCalled();
  jest.mocked(exportPersonalData).mockResolvedValue(undefined); await fireEvent.press(view.getByText('Exporter mes données'));
  await view.findByText(/Feuille de partage fermée/); expect(exportPersonalData).toHaveBeenCalledTimes(2);
});
test('export errors remain visible without leaving settings and retries clear stale errors', async () => {
  jest.mocked(exportPersonalData).mockRejectedValueOnce(new PersonalExportError('io', 'Impossible de préparer le fichier.'));
  const view = await render(<Screen />); await loaded(view); await fireEvent.press(view.getByText('Exporter mes données'));
  await view.findByText('Impossible de préparer le fichier.'); expect(router.back).not.toHaveBeenCalled();
  await fireEvent.press(view.getByText('Exporter mes données')); await view.findByText(/Feuille de partage fermée/);
  expect(view.queryByText('Impossible de préparer le fichier.')).toBeNull();
});
test('leaving settings during preparation aborts, but a native sharing-sheet blur does not cancel the export', async () => {
  const pending = deferred<void>(); jest.mocked(exportPersonalData).mockReturnValue(pending.promise);
  let view = await render(<Screen />); await loaded(view); await fireEvent.press(view.getByText('Exporter mes données'));
  let signal = jest.mocked(exportPersonalData).mock.calls[0]![0]!.signal!;
  await act(() => { for (const close of mockFocusCleanups) close(); }); expect(signal.aborted).toBe(true);
  await act(async () => { pending.resolve(); }); await view.unmount();
  const next = deferred<void>(); jest.mocked(exportPersonalData).mockReturnValue(next.promise);
  view = await render(<Screen />); await loaded(view); await fireEvent.press(view.getByText('Exporter mes données'));
  signal = jest.mocked(exportPersonalData).mock.calls[1]![0]!.signal!;
  await act(async () => { jest.mocked(exportPersonalData).mock.calls[1]![0]!.onPhase?.('sharing'); });
  await act(() => { for (const close of mockFocusCleanups) close(); }); expect(signal.aborted).toBe(false);
  await act(async () => { next.resolve(); });
  expect(mockWrite).not.toHaveBeenCalled();
});
