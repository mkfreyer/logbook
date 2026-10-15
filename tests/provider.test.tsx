import { afterEach, beforeEach, describe, expect, jest, test } from '@jest/globals';
import { act, cleanup, render, waitFor } from '@testing-library/react-native';
import { Text } from 'react-native';
import { LogbookProvider, useLogbook } from '../src/store/LogbookProvider';
import type { Program } from '../src/domain/models';

const first: Program = {
  id: 'first', name: 'Premier', description: '', sportType: 'musculation',
  createdAt: '2026-10-14T10:00:00Z', updatedAt: '2026-10-14T10:00:00Z', workoutCount: 2,
};
const second: Program = { ...first, id: 'second', name: 'Second', workoutCount: 1 };
const mockRepository = {
  listPrograms: jest.fn<() => Promise<Program[]>>(),
  deleteProgram: jest.fn<(id: string) => Promise<void>>(),
  deleteWorkout: jest.fn<(id: string) => Promise<void>>(),
};
const mockDatabase = {};
jest.mock('expo-sqlite', () => ({ useSQLiteContext: () => mockDatabase }));
jest.mock('expo-crypto', () => ({ randomUUID: () => 'unused-id' }));
jest.mock('../src/db/repository', () => ({
  ...jest.requireActual<typeof import('../src/db/repository')>('../src/db/repository'),
  ProgramRepository: class { constructor() { return mockRepository; } },
}));

let store: ReturnType<typeof useLogbook>;
function Consumer() {
  store = useLogbook();
  return <Text>{store.programs.map(program => `${program.id}:${program.workoutCount}`).join(',')}</Text>;
}
async function setup() {
  const view = render(<LogbookProvider><Consumer /></LogbookProvider>);
  await waitFor(() => expect(store.loading).toBe(false));
  return view;
}

beforeEach(() => {
  jest.resetAllMocks();
  mockRepository.listPrograms.mockResolvedValue([first, second]);
  mockRepository.deleteProgram.mockResolvedValue(undefined);
  mockRepository.deleteWorkout.mockResolvedValue(undefined);
});
afterEach(cleanup);

describe('LogbookProvider : suppressions et actualisation', () => {
  test('distingue une liste vide confirmée d’une première lecture en échec', async () => {
    mockRepository.listPrograms.mockRejectedValueOnce(new Error('initial read failure'));
    await setup(); expect(store.hasLoaded).toBe(false); expect(store.error).not.toBeNull();
    mockRepository.listPrograms.mockResolvedValue([]);
    await act(async () => store.refresh()); expect(store.hasLoaded).toBe(true); expect(store.programs).toEqual([]);
    mockRepository.listPrograms.mockRejectedValueOnce(new Error('refresh failure'));
    await act(async () => store.refresh()); expect(store.hasLoaded).toBe(true); expect(store.programs).toEqual([]); expect(store.error).not.toBeNull();
  });

  test('deleteProgram supprime la carte et publie la liste actualisée avant de terminer', async () => {
    await setup();
    mockRepository.listPrograms.mockResolvedValue([second]);
    await act(async () => store.deleteProgram(first.id));
    expect(mockRepository.deleteProgram).toHaveBeenCalledWith(first.id);
    expect(mockRepository.deleteWorkout).not.toHaveBeenCalled();
    expect(mockRepository.listPrograms).toHaveBeenCalledTimes(2);
    expect(store.programs).toEqual([second]);
    expect(store.error).toBeNull();
  });

  test('deleteWorkout actualise les comptes sans retirer ni modifier les autres programmes', async () => {
    await setup();
    const updated = { ...first, workoutCount: 1 };
    mockRepository.listPrograms.mockResolvedValue([updated, second]);
    await act(async () => store.deleteWorkout('planned-workout'));
    expect(mockRepository.deleteWorkout).toHaveBeenCalledWith('planned-workout');
    expect(mockRepository.deleteProgram).not.toHaveBeenCalled();
    expect(store.programs).toEqual([updated, second]);
    expect(mockRepository.listPrograms).toHaveBeenCalledTimes(2);
  });

  test.each(['deleteProgram', 'deleteWorkout'] as const)('%s propage une erreur de stockage sans retirer de donnée affichée', async operation => {
    await setup();
    mockRepository[operation].mockRejectedValueOnce(new Error('storage failure'));
    await act(async () => {
      await expect(store[operation]('first')).rejects.toThrow('storage failure');
    });
    expect(store.programs).toEqual([first, second]);
    expect(mockRepository.listPrograms).toHaveBeenCalledTimes(1);
  });

  test('une erreur de relecture après suppression ne réaffiche pas le programme supprimé et peut être réessayée', async () => {
    await setup();
    mockRepository.listPrograms.mockRejectedValueOnce(new Error('read failure'));
    await act(async () => store.deleteProgram(first.id));
    expect(store.programs).toEqual([second]);
    expect(store.error).toBe('Impossible de lire vos programmes. Réessayez.');
    mockRepository.listPrograms.mockResolvedValue([second]);
    await act(async () => store.refresh());
    expect(store.programs).toEqual([second]);
    expect(store.error).toBeNull();
    expect(mockRepository.deleteProgram).toHaveBeenCalledTimes(1);
  });

  test('une lecture ancienne terminée après la suppression ne peut pas réintroduire le programme', async () => {
    await setup();
    let finishOldRead!: (value: Program[]) => void;
    mockRepository.listPrograms.mockReturnValueOnce(new Promise(resolve => { finishOldRead = resolve; }));
    let oldRead!: Promise<void>;
    act(() => { oldRead = store.refresh(); });
    mockRepository.listPrograms.mockResolvedValue([second]);
    await act(async () => store.deleteProgram(first.id));
    await act(async () => { finishOldRead([first, second]); await oldRead; });
    expect(store.programs).toEqual([second]);
  });
});
