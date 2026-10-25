import { afterEach, expect, jest, test } from '@jest/globals';
import { act, cleanup, renderHook } from '@testing-library/react-native';
import { useScreenOperation } from '../src/features/training/shared';

let mockFocus: () => void | (() => void);
let mockBlur: void | (() => void);
jest.mock('expo-router', () => ({ useFocusEffect: (callback: () => void | (() => void)) => {
  const React = require('react');
  mockFocus = callback;
  React.useEffect(() => { mockBlur = callback(); return () => mockBlur?.(); }, [callback]);
} }));
afterEach(cleanup);

test('retour après ouverture de la séance : la configuration redevient utilisable', async () => {
  const { result } = await renderHook(useScreenOperation);
  const save = jest.fn<() => Promise<void>>().mockResolvedValue(undefined), navigate = jest.fn();
  await act(async () => { await result.current.run(save, navigate, true); });
  expect(result.current.busy).toBe(true);
  await act(async () => { await result.current.run(save, navigate, true); });
  expect(save).toHaveBeenCalledTimes(1);
  await act(() => { mockBlur?.(); mockBlur = mockFocus(); });
  expect(result.current.busy).toBe(false); expect(result.current.lock.current).toBe(false);
  await act(async () => { await result.current.run(save, navigate, true); });
  expect(save).toHaveBeenCalledTimes(2);
});

test('un retour pendant une écriture ne libère pas prématurément le verrou', async () => {
  const { result } = await renderHook(useScreenOperation);
  let resolve!: () => void;
  const save = jest.fn(() => new Promise<void>(done => { resolve = done; }));
  let operation!: Promise<void>;
  await act(() => { operation = result.current.run(save); });
  await act(() => { mockBlur?.(); mockBlur = mockFocus(); });
  await act(async () => { await result.current.run(save); });
  expect(save).toHaveBeenCalledTimes(1); expect(result.current.busy).toBe(true);
  await act(async () => { resolve(); await operation; });
  expect(result.current.busy).toBe(false);
});
