import { afterEach, beforeEach, expect, jest, test } from '@jest/globals';
import { act, cleanup, render, waitFor } from '@testing-library/react-native';
import { AppState, Text } from 'react-native';
import type { WorkoutSession } from '../src/domain/session';
import { SessionProvider } from '../src/store/SessionProvider';

const mockPlayer = { seekTo: jest.fn<() => Promise<void>>().mockResolvedValue(undefined), play: jest.fn() };
const mockAudioMode = jest.fn<() => Promise<void>>().mockResolvedValue(undefined);
let mockChange: () => void;
const mockRepository = {
  getActiveSession: jest.fn<() => Promise<WorkoutSession | null>>(),
  subscribe: jest.fn((listener: () => void) => { mockChange = listener; return jest.fn(); }),
};
const mockDatabase = {};
jest.mock('expo-sqlite', () => ({ useSQLiteContext: () => mockDatabase }));
jest.mock('expo-crypto', () => ({ randomUUID: () => 'unused' }));
jest.mock('../src/store/PreferencesProvider', () => ({ usePreferences: () => ({ soundEnabled: true }) }));
jest.mock('../src/db/sessionRepository', () => ({ SessionRepository: class { constructor() { return mockRepository; } } }));
jest.mock('expo-audio', () => ({ useAudioPlayer: () => mockPlayer, setAudioModeAsync: () => mockAudioMode() }));

const stamp = '2026-10-14T12:00:00.000Z', start = Date.parse(stamp);
const targets = { repsMin: 8, repsMax: 8, targetWeightKg: null, targetRir: null, restAfterSec: 1 };
const session: WorkoutSession = {
  id: 's', sourceWorkoutTemplateId: 'w', sourceProgramId: 'p', workoutName: 'Séance', programName: 'Programme',
  status: 'active', startedAt: stamp, finishedAt: null, selectedExerciseId: null,
  exercises: [0, 1].map(index => ({ id: `e${index}`, sessionId: 's', sourceWorkoutExerciseId: `we${index}`, sourceCatalogExerciseId: `c${index}`,
    sortOrder: index, name: `Exercice ${index}`, muscleGroup: 'Dos', equipment: 'Salle', instructions: '', notes: '', weightMode: 'total' })),
  sets: [0, 0, 1].map((exercise, index) => ({ id: `set${index}`, sessionId: 's', sessionExerciseId: `e${exercise}`, sourceSetTemplateId: `st${index}`,
    sortOrder: index, seriesIndex: index === 1 ? 1 : 0, label: '', kind: 'work', notes: '', targets, originalTargets: targets })),
  performances: [{ id: 'performed', sessionId: 's', sessionSetId: 'set0', sortOrder: 0, weightKg: null, reps: 8, rir: null, performedAt: stamp, advancedAt: null }],
  rests: [{ id: 'rest', sessionId: 's', performedSetId: 'performed', plannedSeconds: 1, startedAt: stamp, endedAt: null, chronologicalMs: null, activeMs: null, pauses: [] }],
};

beforeEach(() => {
  jest.clearAllMocks(); jest.useFakeTimers(); jest.setSystemTime(start);
  Object.defineProperty(AppState, 'currentState', { value: 'active', writable: true, configurable: true });
  jest.spyOn(AppState, 'addEventListener').mockImplementation(() => ({ remove: jest.fn() }));
  mockRepository.getActiveSession.mockResolvedValue(session);
});
afterEach(() => { cleanup(); jest.restoreAllMocks(); jest.useRealTimers(); });

test('choosing another exercise exactly at expiry keeps the same rest observation and sounds once, without ending rest', async () => {
  render(<SessionProvider><Text>Grille des exercices restants</Text></SessionProvider>);
  await waitFor(() => expect(mockRepository.subscribe).toHaveBeenCalledTimes(1));
  await act(async () => { await Promise.resolve(); });
  await act(async () => { jest.advanceTimersByTime(800); });
  expect(mockPlayer.play).not.toHaveBeenCalled();
  // The saved choice returns a new snapshot of an unchanged interval between clock ticks.
  // Replacing the interval object here used to reset the alert's deadline observation.
  jest.setSystemTime(start + 1000);
  mockRepository.getActiveSession.mockResolvedValue({ ...session, selectedExerciseId: 'e1', rests: [{ ...session.rests[0]!, pauses: [] }] });
  await act(async () => { mockChange(); await Promise.resolve(); });
  await act(async () => { jest.advanceTimersByTime(250); });
  expect(mockPlayer.play).toHaveBeenCalledTimes(1);
  await act(async () => { jest.advanceTimersByTime(3000); });
  expect(mockPlayer.play).toHaveBeenCalledTimes(1);
  expect(session.rests[0]!.endedAt).toBeNull(); expect(session.performances.length).toBe(1);
});
