import { afterEach, beforeEach, expect, jest, test } from '@jest/globals';
import { act, cleanup, render, waitFor } from '@testing-library/react-native';
import { AppState, Text } from 'react-native';
import type { WorkoutSession } from '../src/domain/session';
import { SessionProvider, useSessions } from '../src/store/SessionProvider';
import { useRestAlert } from '../src/features/sessions/useRestAlert';

const mockDatabase = {};
const mockUnsubscribe = jest.fn();
let mockChange: () => void;
const mockRepository = {
  getActiveSession: jest.fn<() => Promise<WorkoutSession | null>>(),
  subscribe: jest.fn((listener: () => void) => { mockChange = listener; return mockUnsubscribe; }),
};
jest.mock('expo-sqlite', () => ({ useSQLiteContext: () => mockDatabase }));
jest.mock('expo-crypto', () => ({ randomUUID: () => 'uuid' }));
jest.mock('../src/store/PreferencesProvider', () => ({ usePreferences: () => ({ soundEnabled: true }) }));
jest.mock('../src/db/sessionRepository', () => ({ SessionRepository: class { constructor() { return mockRepository; } } }));
jest.mock('../src/features/sessions/useRestAlert', () => ({ useRestAlert: jest.fn(() => false) }));
const stamp = '2026-10-14T12:00:00.000Z';
const targets = { repsMin: 8, repsMax: 8, targetWeightKg: null, targetRir: null, restAfterSec: 60 };
const resting: WorkoutSession = {
  id: 'session', sourceWorkoutTemplateId: 'deleted-template', sourceProgramId: 'deleted-program',
  workoutName: 'Ma séance', programName: 'Mon programme', status: 'active', startedAt: stamp, finishedAt: null,
  exercises: [{ id: 'exercise', sessionId: 'session', sourceWorkoutExerciseId: 'source', sourceCatalogExerciseId: 'catalog',
    sortOrder: 0, name: 'Pompes', muscleGroup: 'Pectoraux', equipment: 'Poids du corps', instructions: '', notes: '', weightMode: 'additional' }],
  sets: [0, 1].map(index => ({ id: `set${index}`, sessionId: 'session', sessionExerciseId: 'exercise', sourceSetTemplateId: `source${index}`,
    sortOrder: index, seriesIndex: index, label: '', kind: 'work', notes: '', targets, originalTargets: targets })),
  performances: [{ id: 'performed', sessionId: 'session', sessionSetId: 'set0', sortOrder: 0, weightKg: null, reps: 8,
    rir: null, performedAt: stamp, advancedAt: null }],
  rests: [{ id: 'rest', sessionId: 'session', performedSetId: 'performed', plannedSeconds: 60, startedAt: stamp,
    endedAt: null, chronologicalMs: null, activeMs: null, pauses: [] }],
};
function OtherScreen() {
  const repository = useSessions();
  expect(repository).toBe(mockRepository);
  return <Text>Liste des programmes</Text>;
}
beforeEach(() => {
  jest.clearAllMocks();
  jest.spyOn(AppState, 'addEventListener').mockImplementation(() => ({ remove: jest.fn() }));
  mockRepository.getActiveSession.mockResolvedValue(null);
});
afterEach(() => { cleanup(); jest.restoreAllMocks(); });

test('l’observateur audio reste actif sur un autre écran et suit les repos sauvegardés', async () => {
  const view = render(<SessionProvider><OtherScreen /></SessionProvider>);
  expect(view.getByText('Liste des programmes')).toBeTruthy();
  await waitFor(() => expect(mockRepository.subscribe).toHaveBeenCalledTimes(1));
  mockRepository.getActiveSession.mockResolvedValue(resting);
  act(() => mockChange());
  await waitFor(() => expect(useRestAlert).toHaveBeenLastCalledWith(resting.rests[0], true));
  mockRepository.getActiveSession.mockResolvedValue(null);
  act(() => mockChange());
  await waitFor(() => expect(useRestAlert).toHaveBeenLastCalledWith(null, true));
  expect(view.getByText('Liste des programmes')).toBeTruthy();
});

test('une lecture impossible ne bloque pas le reste de l’application et un changement peut réessayer', async () => {
  mockRepository.getActiveSession.mockRejectedValueOnce(new Error('read failure'));
  const view = render(<SessionProvider><OtherScreen /></SessionProvider>);
  await waitFor(() => expect(mockRepository.getActiveSession).toHaveBeenCalledTimes(1));
  expect(view.getByText('Liste des programmes')).toBeTruthy();
  mockRepository.getActiveSession.mockResolvedValue(resting); act(() => mockChange());
  await waitFor(() => expect(useRestAlert).toHaveBeenLastCalledWith(resting.rests[0], true));
  view.unmount(); expect(mockUnsubscribe).toHaveBeenCalledTimes(1);
});
