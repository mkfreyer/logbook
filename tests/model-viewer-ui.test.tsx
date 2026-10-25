/** Native screen/bridge/lifecycle contracts only; real 3D is tested in test-browser.ts. */
import { afterEach, beforeEach, expect, jest, test } from '@jest/globals';
import { act, cleanup, fireEvent, render, waitFor } from '@testing-library/react-native';
import { AppState, type AppStateStatus } from 'react-native';
import { ModelViewerScreen } from '../src/features/model3d/ModelViewerScreen';
import { loadModelBase64 } from '../src/features/model3d/loadModel';
import type { WebViewProps } from 'react-native-webview';

let mockFocused = true;
let mockProps: WebViewProps;
let mockAppChange: (state: AppStateStatus) => void;
const mockInject = jest.fn();
const appStateDescriptor = Object.getOwnPropertyDescriptor(AppState, 'currentState');
jest.mock('expo-router', () => {
  const React = require('react') as typeof import('react');
  return { router: { back: jest.fn(), replace: jest.fn(), canGoBack: () => true },
    useFocusEffect: (effect: () => void | (() => void)) => React.useEffect(() => { if (mockFocused) return effect(); }, [effect, mockFocused]) };
});
jest.mock('react-native-webview', () => {
  const React = require('react') as typeof import('react');
  const { View } = require('react-native') as typeof import('react-native');
  return { WebView: React.forwardRef((_props: WebViewProps, ref) => {
    mockProps = _props; React.useImperativeHandle(ref, () => ({ injectJavaScript: mockInject }));
    return React.createElement(View, { testID: 'model-webview' });
  }) };
});
jest.mock('../src/features/model3d/loadModel', () => ({ loadModelBase64: jest.fn() }));
jest.mock('../src/features/model3d/generated/viewerBundle', () => ({ viewerBundle: '/* UI contract test, not a renderer */' }));
jest.mock('@expo/vector-icons', () => ({ Ionicons: () => null }));
jest.mock('react-native-safe-area-context', () => jest.requireActual<{ default: typeof import('react-native-safe-area-context') }>('react-native-safe-area-context/jest/mock').default);
function message(value: unknown) {
  act(() => mockProps.onMessage?.({ nativeEvent: { data: JSON.stringify(value) } } as Parameters<NonNullable<WebViewProps['onMessage']>>[0]));
}
const ready = { version: 1, type: 'ready', triangles: 110588, geometryBytes: 1990584 };
beforeEach(() => {
  jest.clearAllMocks(); mockFocused = true;
  Object.defineProperty(AppState, 'currentState', { value: 'active', writable: true, configurable: true });
  jest.spyOn(AppState, 'addEventListener').mockImplementation((_event, callback) => { mockAppChange = callback; return { remove: jest.fn() }; });
  jest.mocked(loadModelBase64).mockResolvedValue('AAAA');
});
afterEach(() => { cleanup(); jest.restoreAllMocks(); jest.useRealTimers(); if (appStateDescriptor) Object.defineProperty(AppState, 'currentState', appStateDescriptor); });

test('controls wait for the validated model, then send only camera commands', async () => {
  const view = render(<ModelViewerScreen />); await view.findByTestId('model-webview');
  expect(view.getByRole('button', { name: 'Vue générale' }).props.accessibilityState.disabled).toBe(true);
  message({ ...ready, triangles: 97424 });
  expect(view.getByRole('button', { name: 'Vue générale' }).props.accessibilityState.disabled).toBe(true);
  message(ready);
  await waitFor(() => expect(view.getByRole('button', { name: 'Vue générale' }).props.accessibilityState.disabled).toBe(false));
  fireEvent.press(view.getByRole('button', { name: 'Vue générale' })); expect(mockInject).toHaveBeenLastCalledWith(expect.stringContaining('command("overview")'));
  fireEvent.press(view.getByRole('button', { name: 'Face' })); expect(mockInject).toHaveBeenLastCalledWith(expect.stringContaining('command("front")'));
  expect(mockProps.onShouldStartLoadWithRequest?.({ url: 'https://example.com' } as never)).toBe(false);
  expect(mockProps.onShouldStartLoadWithRequest?.({ url: 'about:blank' } as never)).toBe(true);
  expect(view.queryByText(/tonnage|séries|pectoraux|deltoïde/i)).toBeNull();
});

test('background releases the WebView and ignores events from its previous generation', async () => {
  const view = render(<ModelViewerScreen />); await view.findByTestId('model-webview'); message(ready);
  const previous = mockProps.onMessage;
  act(() => mockAppChange('background'));
  expect(view.queryByTestId('model-webview')).toBeNull();
  expect(mockInject).toHaveBeenCalledWith(expect.stringContaining('command("dispose")'));
  act(() => mockAppChange('active')); await view.findByTestId('model-webview');
  act(() => previous?.({ nativeEvent: { data: JSON.stringify(ready) } } as never));
  expect(view.getByRole('button', { name: 'Face' }).props.accessibilityState.disabled).toBe(true);
  message(ready); await waitFor(() => expect(view.getByRole('button', { name: 'Face' }).props.accessibilityState.disabled).toBe(false));
  act(() => mockAppChange('active')); message(ready);
  expect(view.getByRole('button', { name: 'Face' }).props.accessibilityState.disabled).toBe(false);
  expect(loadModelBase64).toHaveBeenCalledTimes(1);
});

test('blur removes the rendering surface; focus creates a new one', async () => {
  const view = render(<ModelViewerScreen />); await view.findByTestId('model-webview'); message(ready);
  mockFocused = false; view.rerender(<ModelViewerScreen />);
  expect(view.queryByTestId('model-webview')).toBeNull();
  mockFocused = true; view.rerender(<ModelViewerScreen />); await view.findByTestId('model-webview');
  expect(view.getByRole('button', { name: 'Face' }).props.accessibilityState.disabled).toBe(true);
});

test('a local asset failure has a retry instead of a false ready state', async () => {
  jest.mocked(loadModelBase64).mockRejectedValueOnce(new Error('file missing'));
  const view = render(<ModelViewerScreen />); await view.findByText('Le mannequin local n’a pas pu être chargé.');
  expect(view.queryByTestId('model-webview')).toBeNull();
  fireEvent.press(view.getByRole('button', { name: 'Réessayer' })); await view.findByTestId('model-webview');
  message(ready); await waitFor(() => expect(view.queryByRole('button', { name: 'Réessayer' })).toBeNull());
});

test('a stopped content process releases the surface and offers a clean retry', async () => {
  const view = render(<ModelViewerScreen />); await view.findByTestId('model-webview'); message(ready);
  const stale = mockProps.onMessage;
  act(() => mockProps.onContentProcessDidTerminate?.({ nativeEvent: {} } as never));
  act(() => stale?.({ nativeEvent: { data: JSON.stringify(ready) } } as never));
  await view.findByText('Le rendu 3D a été interrompu. Réessayez.'); expect(view.queryByTestId('model-webview')).toBeNull();
  fireEvent.press(view.getByRole('button', { name: 'Réessayer' })); await view.findByTestId('model-webview'); message(ready);
  await waitFor(() => expect(view.getByRole('button', { name: 'Face' }).props.accessibilityState.disabled).toBe(false));
});
