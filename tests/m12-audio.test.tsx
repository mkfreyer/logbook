import { afterEach, beforeEach, expect, jest, test } from '@jest/globals';
import { act, cleanup, renderHook } from '@testing-library/react-native';
import { AppState, type AppStateStatus } from 'react-native';
import { useRestAlert } from '../src/features/sessions/useRestAlert';
import type { RestInterval } from '../src/domain/session';

const mockPlayer = { seekTo: jest.fn<() => Promise<void>>().mockResolvedValue(undefined), play: jest.fn() };
const mockAudioMode = jest.fn<(...args: unknown[]) => Promise<void>>().mockResolvedValue(undefined);
jest.mock('expo-audio', () => ({ useAudioPlayer: () => mockPlayer, setAudioModeAsync: (...args: unknown[]) => mockAudioMode(...args) }));
const start = Date.parse('2026-10-14T10:00:00Z');
const rest: RestInterval = { id: 'r1', sessionId: 's1', performedSetId: 'p1', plannedSeconds: 2,
  startedAt: new Date(start).toISOString(), endedAt: null, chronologicalMs: null, activeMs: null, pauses: [] };
let onAppState: (state: AppStateStatus) => void;

beforeEach(() => {
  jest.useFakeTimers(); jest.setSystemTime(start); jest.clearAllMocks();
  Object.defineProperty(AppState, 'currentState', { value: 'active', writable: true, configurable: true });
  jest.spyOn(AppState, 'addEventListener').mockImplementation((_event, handler) => {
    onAppState = handler; return { remove: jest.fn() };
  });
  mockAudioMode.mockResolvedValue(undefined);
});
afterEach(async () => { await cleanup(); jest.restoreAllMocks(); jest.useRealTimers(); });
async function advance(ms: number) { await act(async () => { jest.advanceTimersByTime(ms); }); }
async function appState(state: AppStateStatus) { await act(() => { AppState.currentState = state; onAppState(state); }); }

test('échéance au premier plan : une alerte, sans modifier le repos', async () => {
  await renderHook(() => useRestAlert(rest, true));
  await advance(1800); expect(mockPlayer.play).not.toHaveBeenCalled();
  await advance(400); expect(mockPlayer.play).toHaveBeenCalledTimes(1);
  await advance(5000); expect(mockPlayer.play).toHaveBeenCalledTimes(1);
  expect(mockAudioMode).toHaveBeenCalledWith(expect.objectContaining({ shouldPlayInBackground: false, allowsRecording: false }));
  expect(rest.endedAt).toBeNull();
});
test('échéance en arrière-plan : aucune sonnerie tardive au retour', async () => {
  await renderHook(() => useRestAlert(rest, true));
  await advance(1000); await appState('background'); await advance(3000);
  await appState('active'); await advance(2000);
  expect(mockPlayer.play).not.toHaveBeenCalled();
});
test('un repos déjà dépassé à la réouverture ne rejoue pas l’alerte', async () => {
  jest.setSystemTime(start + 10000); await renderHook(() => useRestAlert(rest, true));
  await advance(1000); expect(mockPlayer.play).not.toHaveBeenCalled();
});
test('un écran quitté n’émet pas de son', async () => {
  const view = await renderHook((props: { enabled: boolean }) => useRestAlert(rest, props.enabled), { initialProps: { enabled: true } });
  await view.rerender({ enabled: false }); await advance(3000);
  expect(mockPlayer.play).not.toHaveBeenCalled();
});
test('un échec audio est signalé sans empêcher le minuteur', async () => {
  mockAudioMode.mockRejectedValueOnce(new Error('audio unavailable'));
  const view = await renderHook(() => useRestAlert(rest, true));
  await advance(2200); expect(view.result.current).toBe(true);
  expect(mockPlayer.play).not.toHaveBeenCalled(); expect(rest.endedAt).toBeNull();
});
