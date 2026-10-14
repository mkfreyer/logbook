import { afterEach, beforeEach, describe, expect, jest, test } from '@jest/globals';
import { act, cleanup, fireEvent, render } from '@testing-library/react-native';
import { AccessibilityInfo, DeviceEventEmitter, Pressable, StyleSheet, Text } from 'react-native';
import { Gesture, PointerType, State, type GestureStateManager, type GestureTouchEvent } from 'react-native-gesture-handler';
import { fireGestureHandler, getByGestureTestId } from 'react-native-gesture-handler/jest-utils';
import { ReduceMotion, withTiming } from 'react-native-reanimated';

import { useUniverseNavigation, type UniverseId } from '../src/navigation/UniverseContext';
import { UniversePager, type UniversePage } from '../src/navigation/UniversePager';
import { UniverseScreen } from '../src/navigation/UniverseScreen';

// Keep the real pager, contexts, scroll view and RNGH event dispatcher. Only the
// UI-thread animation runtime is replaced: shared values survive React renders,
// styles read their latest values, and animations finish synchronously by default.
// These tests exercise bindings and decisions; they cannot prove native smoothness.
jest.mock('react-native-reanimated', () => {
  const React = require('react') as typeof import('react');
  const mock = require('react-native-reanimated/mock') as typeof import('react-native-reanimated');
  const { jest: mockJest } = require('@jest/globals') as typeof import('@jest/globals');
  return {
    ...mock,
    useSharedValue: <T,>(initial: T) => React.useRef({ value: initial }).current,
    useAnimatedStyle: (factory: () => { transform: unknown }) => ({ get transform() { return factory().transform; } }),
    useAnimatedScrollHandler: (callback: (event: unknown) => void) => (event: { nativeEvent?: unknown }) => callback(event.nativeEvent ?? event),
    withTiming: mockJest.fn(mock.withTiming),
  };
});
jest.mock('react-native-safe-area-context', () => jest.requireActual<{ default: typeof import('react-native-safe-area-context') }>('react-native-safe-area-context/jest/mock').default);
jest.mock('@expo/vector-icons', () => ({ Ionicons: () => null }));
jest.mock('expo-router', () => ({ router: { push: jest.fn(), replace: jest.fn(), back: jest.fn(), canGoBack: jest.fn() } }));

type Pan = ReturnType<typeof Gesture.Pan>;
type View = ReturnType<typeof render>;
const height = 800;

function SamplePage({ id }: { id: UniverseId }) {
  const navigation = useUniverseNavigation();
  return <UniverseScreen testID={`scroll-${id}`}>
    <Text>{id}</Text>
    {(['home', 'musculation', 'cardio'] as const).map(target => <Pressable key={target} accessibilityRole="button"
      accessibilityLabel={`${id} vers ${target}`} onPress={() => navigation.goTo(target)}><Text>{target}</Text></Pressable>)}
  </UniverseScreen>;
}

function setup(selectedId: UniverseId = 'home', ids: UniverseId[] = ['home', 'musculation']) {
  const pages: UniversePage[] = ids.map(id => ({ id, label: id === 'home' ? 'Accueil' : id === 'musculation' ? 'Musculation' : 'Cardio', content: <SamplePage id={id} /> }));
  const onSelect = jest.fn<(id: UniverseId) => void>();
  const view = render(<UniversePager pages={pages} selectedId={selectedId} onSelect={onSelect} />);
  fireEvent(view.getByTestId('universe-viewport'), 'layout', { nativeEvent: { layout: { height, width: 390, x: 0, y: 0 } } });
  return { view, onSelect, pages, pan: getByGestureTestId('universe-pan') as Pan };
}

function measure(view: View, id: UniverseId, contentHeight = height, y = 0) {
  const scroll = view.getByTestId(`scroll-${id}`, { includeHiddenElements: true });
  fireEvent(scroll, 'layout', { nativeEvent: { layout: { height, width: 390, x: 0, y: 0 } } });
  fireEvent(scroll, 'contentSizeChange', 390, contentHeight);
  fireEvent.scroll(scroll, { nativeEvent: { contentOffset: { x: 0, y } } });
}

function translation(view: View): number {
  const style = StyleSheet.flatten(view.getByTestId('universe-track').props.style);
  const value = style.transform.find((entry: { translateY?: number }) => entry.translateY !== undefined).translateY as number;
  // Both signed zeros represent the same physical position.
  return value === 0 ? 0 : value;
}

function touches(pan: Pan, eventType: GestureTouchEvent['eventType'], dy = 0, dx = 0, count = 1): GestureTouchEvent {
  const allTouches = Array.from({ length: count }, (_, id) => ({ id, x: 100 + dx + id * 20, y: 400 + dy, absoluteX: 100 + dx + id * 20, absoluteY: 400 + dy }));
  return { handlerTag: pan.handlerTag, state: State.BEGAN, pointerType: PointerType.TOUCH, eventType, numberOfTouches: count, allTouches, changedTouches: allTouches };
}

function emitPan(pan: Pan, state: number, dy: number, velocityY = 0, oldState?: number) {
  const event = { handlerTag: pan.handlerTag, state, pointerType: PointerType.TOUCH, numberOfPointers: 1,
    x: 100, y: 400 + dy, absoluteX: 100, absoluteY: 400 + dy,
    translationX: 0, translationY: dy, velocityX: 0, velocityY, ...(oldState === undefined ? {} : { oldState }) };
  DeviceEventEmitter.emit(oldState === undefined ? 'onGestureHandlerEvent' : 'onGestureHandlerStateChange', event);
}

function managerFor(pan: Pan): GestureStateManager {
  return {
    handlerTag: pan.handlerTag,
    begin: jest.fn(), end: jest.fn(), fail: jest.fn(),
    activate: jest.fn(() => {
      emitPan(pan, State.BEGAN, 0, 0, State.UNDETERMINED);
      emitPan(pan, State.ACTIVE, 0, 0, State.BEGAN);
    }),
  };
}

function startDrag(pan: Pan, dy: number) {
  const manager = managerFor(pan);
  act(() => {
    pan.handlers.onTouchesDown?.(touches(pan, 1), manager);
    pan.handlers.onTouchesMove?.(touches(pan, 2, dy), manager);
  });
  expect(manager.activate).toHaveBeenCalledTimes(1);
  expect(manager.fail).not.toHaveBeenCalled();
  return manager;
}

beforeEach(() => {
  jest.clearAllMocks();
  jest.spyOn(AccessibilityInfo, 'announceForAccessibility').mockImplementation(() => undefined);
});
afterEach(() => { cleanup(); jest.restoreAllMocks(); });

describe('The mounted vertical universe pager', () => {
  test('accessible buttons select universes with the same vertical track and hide inactive pages', () => {
    const { view, onSelect } = setup();
    expect(translation(view)).toBe(0);
    expect(view.getByTestId('universe-musculation', { includeHiddenElements: true }).props.accessibilityElementsHidden).toBe(true);
    expect(view.queryByRole('button', { name: 'musculation vers home' })).toBeNull();

    fireEvent.press(view.getByRole('button', { name: 'home vers musculation' }));
    expect(onSelect).toHaveBeenCalledWith('musculation');
    expect(translation(view)).toBe(-height);
    expect(withTiming).toHaveBeenLastCalledWith(-height, expect.objectContaining({ reduceMotion: ReduceMotion.System }), expect.any(Function));
    const home = view.getByTestId('universe-home', { includeHiddenElements: true });
    expect(home.props.pointerEvents).toBe('none');
    expect(home.props.accessibilityElementsHidden).toBe(true);
    expect(home.props.importantForAccessibility).toBe('no-hide-descendants');
    expect(AccessibilityInfo.announceForAccessibility).toHaveBeenCalledWith('Musculation');

    fireEvent.press(view.getByRole('button', { name: 'musculation vers home' }));
    expect(translation(view)).toBe(0);
    expect(onSelect).toHaveBeenLastCalledWith('home');
  });

  test('the real gesture binding moves the track before selection, then commits in both directions', () => {
    const { view, onSelect, pan } = setup();
    measure(view, 'home');
    measure(view, 'musculation');
    startDrag(pan, -20);
    act(() => emitPan(pan, State.ACTIVE, -100));
    expect(translation(view)).toBe(-100);
    expect(onSelect).not.toHaveBeenCalled();
    expect(view.getByRole('button', { name: 'home vers musculation' })).toBeTruthy();

    act(() => emitPan(pan, State.END, -180, 0, State.ACTIVE));
    expect(translation(view)).toBe(-height);
    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(onSelect).toHaveBeenLastCalledWith('musculation');

    startDrag(pan, 20);
    act(() => emitPan(pan, State.ACTIVE, 75));
    expect(translation(view)).toBe(-height + 75);
    act(() => emitPan(pan, State.END, 75, 900, State.ACTIVE));
    expect(translation(view)).toBe(0);
    expect(onSelect).toHaveBeenLastCalledWith('home');
  });

  test('a short drag and backtracking restore the origin instead of claiming the opposite direction', () => {
    const { view, onSelect, pan } = setup();
    measure(view, 'home');
    startDrag(pan, -20);
    act(() => {
      emitPan(pan, State.ACTIVE, -60);
      emitPan(pan, State.END, -60, 0, State.ACTIVE);
    });
    expect(translation(view)).toBe(0);
    expect(onSelect).not.toHaveBeenCalled();

    startDrag(pan, -20);
    act(() => emitPan(pan, State.ACTIVE, -200));
    expect(translation(view)).toBe(-200);
    act(() => {
      emitPan(pan, State.ACTIVE, 100);
      emitPan(pan, State.END, 100, 1500, State.ACTIVE);
    });
    expect(translation(view)).toBe(0);
    expect(onSelect).not.toHaveBeenCalled();
  });

  test('native cancellation past the release threshold and multiple touches cannot select another universe', () => {
    const { view, onSelect, pan } = setup();
    measure(view, 'home');
    // Supply the direction snapshot, then use RNGH's real state-change dispatcher.
    const directionManager = managerFor(pan);
    act(() => {
      pan.handlers.onTouchesDown?.(touches(pan, 1), directionManager);
      pan.handlers.onTouchesMove?.(touches(pan, 2, -20), { ...directionManager, activate: jest.fn() });
      fireGestureHandler(pan, [
        { state: State.BEGAN }, { state: State.ACTIVE },
        { state: State.ACTIVE, translationY: -220 },
        { state: State.CANCELLED, translationY: -220, velocityY: -1000 },
      ]);
    });
    expect(translation(view)).toBe(0);
    expect(onSelect).not.toHaveBeenCalled();

    const manager = managerFor(pan);
    act(() => pan.handlers.onTouchesDown?.(touches(pan, 1, 0, 0, 2), manager));
    expect(manager.fail).toHaveBeenCalledTimes(1);
    expect(manager.activate).not.toHaveBeenCalled();
    startDrag(pan, -20);
    const secondTouch = managerFor(pan);
    act(() => pan.handlers.onTouchesMove?.(touches(pan, 2, -40, 0, 2), secondTouch));
    expect(secondTouch.fail).toHaveBeenCalledTimes(1);
    act(() => emitPan(pan, State.CANCELLED, -40, 0, State.ACTIVE));
    expect(translation(view)).toBe(0);
    expect(onSelect).not.toHaveBeenCalled();
  });

  test('a list owns gestures from its interior even if it reaches the edge before the next touch move', () => {
    const { view, onSelect, pan } = setup('musculation');
    measure(view, 'musculation', 1200, 200);
    const manager = managerFor(pan);
    act(() => pan.handlers.onTouchesDown?.(touches(pan, 1), manager));
    fireEvent.scroll(view.getByTestId('scroll-musculation'), { nativeEvent: { contentOffset: { x: 0, y: 0 } } });
    act(() => pan.handlers.onTouchesMove?.(touches(pan, 2, 40), manager));
    expect(manager.fail).toHaveBeenCalledTimes(1);
    expect(manager.activate).not.toHaveBeenCalled();
    expect(onSelect).not.toHaveBeenCalled();
    expect(translation(view)).toBe(-height);

    // A fresh downward gesture at the top is now eligible to return Home.
    startDrag(pan, 20);
    act(() => emitPan(pan, State.END, 200, 0, State.ACTIVE));
    expect(onSelect).toHaveBeenLastCalledWith('home');
    expect(translation(view)).toBe(0);
  });

  test('a third page shares the registry and cannot be reached by reversing a gesture from the wrong list edge', () => {
    const { view, onSelect, pan } = setup('musculation', ['home', 'musculation', 'cardio']);
    measure(view, 'musculation', 1200, 0);
    startDrag(pan, 20);
    act(() => emitPan(pan, State.ACTIVE, 150));
    expect(translation(view)).toBe(-height + 150);
    act(() => {
      emitPan(pan, State.ACTIVE, -250);
      emitPan(pan, State.END, -250, -1500, State.ACTIVE);
    });
    expect(translation(view)).toBe(-height);
    expect(onSelect).not.toHaveBeenCalled();

    measure(view, 'musculation', 1200, 400);
    startDrag(pan, -20);
    act(() => emitPan(pan, State.END, -200, 0, State.ACTIVE));
    expect(translation(view)).toBe(-height * 2);
    expect(onSelect).toHaveBeenCalledWith('cardio');
    expect(view.getByRole('button', { name: 'cardio vers home' })).toBeTruthy();
    expect(view.queryByRole('button', { name: 'musculation vers home' })).toBeNull();
  });

  test('unmeasured pages, tiny drags and horizontal intent fail without taking control of the list', () => {
    const { view, onSelect, pan } = setup();
    const unmeasured = managerFor(pan);
    act(() => pan.handlers.onTouchesDown?.(touches(pan, 1), unmeasured));
    expect(unmeasured.fail).toHaveBeenCalledTimes(1);
    measure(view, 'home');

    const tiny = managerFor(pan);
    act(() => {
      pan.handlers.onTouchesDown?.(touches(pan, 1), tiny);
      pan.handlers.onTouchesMove?.(touches(pan, 2, -10), tiny);
    });
    expect(tiny.activate).not.toHaveBeenCalled();
    expect(tiny.fail).not.toHaveBeenCalled();
    act(() => pan.handlers.onTouchesUp?.(touches(pan, 3, -10), tiny));
    expect(tiny.fail).toHaveBeenCalledTimes(1);

    const horizontal = managerFor(pan);
    act(() => {
      pan.handlers.onTouchesDown?.(touches(pan, 1), horizontal);
      pan.handlers.onTouchesMove?.(touches(pan, 2, -20, 80), horizontal);
    });
    expect(horizontal.fail).toHaveBeenCalledTimes(1);
    expect(horizontal.activate).not.toHaveBeenCalled();
    expect(onSelect).not.toHaveBeenCalled();
    expect(translation(view)).toBe(0);
  });

  test('settling blocks a second command until completion and resizing reanchors the selected page', () => {
    const { view, onSelect, pan } = setup();
    let finish: (() => void) | undefined;
    jest.mocked(withTiming).mockImplementationOnce((value, _configuration, callback) => {
      finish = () => callback?.(true);
      return value;
    });
    fireEvent.press(view.getByRole('button', { name: 'home vers musculation' }));
    expect(onSelect).not.toHaveBeenCalled();
    fireEvent.press(view.getByRole('button', { name: 'home vers home' }));
    expect(withTiming).toHaveBeenCalledTimes(1);
    const manager = managerFor(pan);
    act(() => pan.handlers.onTouchesDown?.(touches(pan, 1), manager));
    expect(manager.fail).toHaveBeenCalledTimes(1);
    act(() => finish?.());
    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(onSelect).toHaveBeenCalledWith('musculation');

    fireEvent(view.getByTestId('universe-viewport'), 'layout', { nativeEvent: { layout: { height: 650, width: 500, x: 0, y: 0 } } });
    expect(translation(view)).toBe(-650);
    expect(view.getByTestId('universe-musculation').props.style.height).toBe(650);
    expect(onSelect).toHaveBeenCalledTimes(1);
    fireEvent.press(view.getByRole('button', { name: 'musculation vers home' }));
    expect(translation(view)).toBe(0);
    expect(onSelect).toHaveBeenLastCalledWith('home');

    // A resize in the middle of a drag invalidates that gesture's old geometry.
    measure(view, 'home');
    const drag = startDrag(pan, -20);
    act(() => emitPan(pan, State.ACTIVE, -90));
    expect(translation(view)).toBe(-90);
    fireEvent(view.getByTestId('universe-viewport'), 'layout', { nativeEvent: { layout: { height: 700, width: 500, x: 0, y: 0 } } });
    act(() => {
      emitPan(pan, State.ACTIVE, -250);
      pan.handlers.onTouchesMove?.(touches(pan, 2, -250), drag);
      emitPan(pan, State.END, -250, -1500, State.ACTIVE);
    });
    expect(drag.fail).toHaveBeenCalledTimes(1);
    expect(translation(view)).toBe(0);
    expect(onSelect).toHaveBeenCalledTimes(2);
  });
});
