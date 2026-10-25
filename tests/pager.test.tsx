import { afterEach, beforeEach, describe, expect, jest, test } from '@jest/globals';
import { act, cleanup, fireEvent, render } from '@testing-library/react-native';
import { useContext } from 'react';
import { AccessibilityInfo, DeviceEventEmitter, Pressable, StyleSheet, Text } from 'react-native';
import { Gesture, GestureHandlerRootView, PointerType, State, type LegacyGestureStateManager, type GestureTouchEvent } from 'react-native-gesture-handler';
import { fireGestureHandler, getByGestureTestId } from 'react-native-gesture-handler/jest-utils';
import { ReduceMotion, runOnUI, withTiming, type SharedValue } from 'react-native-reanimated';

import { UniversePageContext, useUniverseNavigation, type PageScrollState, type UniverseId } from '../src/navigation/UniverseContext';
import { UniversePager, type UniversePage } from '../src/navigation/UniversePager';
import { UniverseScreen } from '../src/navigation/UniverseScreen';

// Keep the real pager, contexts, scroll view and RNGH event dispatcher. Only the
// UI-thread animation runtime is replaced: shared values survive React renders,
// styles read their latest values, and animations finish synchronously by default.
// Native recognition is explicitly supplied as an input; Jest never runs UIKit.
// These tests exercise configuration, bindings and decisions, not native activation or smoothness.
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
    runOnUI: mockJest.fn(mock.runOnUI),
  };
});
jest.mock('react-native-safe-area-context', () => jest.requireActual<{ default: typeof import('react-native-safe-area-context') }>('react-native-safe-area-context/jest/mock').default);
jest.mock('@expo/vector-icons', () => ({ Ionicons: () => null }));
jest.mock('expo-router', () => ({ router: { push: jest.fn(), replace: jest.fn(), back: jest.fn(), canGoBack: jest.fn() } }));

type Pan = ReturnType<typeof Gesture.Pan>;
type View = Awaited<ReturnType<typeof render>>;
const height = 800;
const pageScrollStates = new Map<UniverseId, SharedValue<Record<string, PageScrollState>>>();

function SamplePage({ id }: { id: UniverseId }) {
  const navigation = useUniverseNavigation();
  const page = useContext(UniversePageContext);
  if (page) pageScrollStates.set(id, page.scroll);
  return <UniverseScreen testID={`scroll-${id}`}>
    <Text>{id}</Text>
    {(['home', 'musculation', 'cardio'] as const).map(target => <Pressable key={target} accessibilityRole="button"
      accessibilityLabel={`${id} vers ${target}`} onPress={() => navigation.goTo(target)}><Text>{target}</Text></Pressable>)}
  </UniverseScreen>;
}

async function setup(selectedId: UniverseId = 'home', ids: UniverseId[] = ['home', 'musculation']) {
  const pages: UniversePage[] = ids.map(id => ({ id, label: id === 'home' ? 'Accueil' : id === 'musculation' ? 'Musculation' : 'Cardio', content: <SamplePage id={id} /> }));
  const onSelect = jest.fn<(id: UniverseId) => void>();
  // Match app/_layout.tsx: RNGH 3 requires its real root context in tests too.
  const view = await render(<UniversePager pages={pages} selectedId={selectedId} onSelect={onSelect} />, { wrapper: GestureHandlerRootView });
  await fireEvent(view.getByTestId('universe-viewport'), 'layout', { nativeEvent: { layout: { height, width: 390, x: 0, y: 0 } } });
  return { view, onSelect, pages, pan: getByGestureTestId('universe-pan') as Pan };
}

async function measure(view: View, id: UniverseId, contentHeight = height, y = 0) {
  const scroll = view.getByTestId(`scroll-${id}`, { includeHiddenElements: true });
  await fireEvent(scroll, 'layout', { nativeEvent: { layout: { height, width: 390, x: 0, y: 0 } } });
  await fireEvent(scroll, 'contentSizeChange', 390, contentHeight);
  await fireEvent.scroll(scroll, { nativeEvent: { contentOffset: { x: 0, y } } });
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

function emitPan(pan: Pan, state: number, dy: number, velocityY = 0, oldState?: number, nativeTranslationY = dy) {
  const event = { handlerTag: pan.handlerTag, state, pointerType: PointerType.TOUCH, numberOfPointers: 1,
    x: 100, y: 400 + dy, absoluteX: 100, absoluteY: 400 + dy,
    translationX: 0, translationY: nativeTranslationY, velocityX: 0, velocityY, ...(oldState === undefined ? {} : { oldState }) };
  DeviceEventEmitter.emit(oldState === undefined ? 'onGestureHandlerEvent' : 'onGestureHandlerStateChange', event);
}

function managerFor(pan: Pan): LegacyGestureStateManager {
  // This fixture deliberately cannot activate the Pan. Only the native recognizer
  // should do that, and its emitted states are separate test inputs below.
  return { handlerTag: pan.handlerTag, begin: jest.fn(), end: jest.fn(), fail: jest.fn(), activate: jest.fn() };
}

async function startDrag(pan: Pan, dy: number) {
  const manager = managerFor(pan);
  await act(() => {
    emitPan(pan, State.BEGAN, 0, 0, State.UNDETERMINED);
    pan.handlers.onTouchesDown?.(touches(pan, 1), manager);
    pan.handlers.onTouchesMove?.(touches(pan, 2, dy), manager);
  });
  expect(manager.activate).not.toHaveBeenCalled();
  expect(manager.fail).not.toHaveBeenCalled();
  // UIKit's successful recognition is an assumption here, not a test result.
  // iOS resets translation on activation; absolute touch coordinates do not reset.
  await act(() => emitPan(pan, State.ACTIVE, dy, 0, State.BEGAN, 0));
  return manager;
}

beforeEach(() => {
  jest.clearAllMocks();
  pageScrollStates.clear();
  jest.spyOn(AccessibilityInfo, 'announceForAccessibility').mockImplementation(() => undefined);
});
afterEach(async () => { await cleanup(); jest.restoreAllMocks(); });

describe('The mounted vertical universe pager', () => {
  test('M3.2 restoration moves both full pages on the same track in either direction, without per-page compensation', async () => {
    const { view, pan, onSelect } = await setup('musculation');
    await startDrag(pan, 20);
    for (const dy of [20, 80, 200, 400, 600]) {
      await act(() => emitPan(pan, State.ACTIVE, dy));
      expect(translation(view)).toBe(-height + dy);
      for (const id of ['home', 'musculation']) {
        const style = StyleSheet.flatten(view.getByTestId(`universe-${id}`, { includeHiddenElements: true }).props.style);
        expect(style.height).toBe(height); expect(style.transform).toBeUndefined();
      }
    }
    await act(() => emitPan(pan, State.END, 600, 0, State.ACTIVE));
    expect(translation(view)).toBe(0); expect(onSelect.mock.calls).toEqual([['home']]);
    await startDrag(pan, -20); await act(() => emitPan(pan, State.ACTIVE, -100));
    expect(translation(view)).toBe(-100);
    await act(() => emitPan(pan, State.CANCELLED, -100, 0, State.ACTIVE));
    expect(translation(view)).toBe(0); expect(onSelect).toHaveBeenCalledTimes(1);
  });

  test('M3.2 route selection and accessible buttons use the original single-id contract', async () => {
    const { view, onSelect, pages } = await setup();
    await view.rerender(<UniversePager pages={pages} selectedId="musculation" onSelect={onSelect} />);
    expect(translation(view)).toBe(-height); expect(onSelect).not.toHaveBeenCalled();
    await fireEvent.press(view.getByRole('button', { name: 'musculation vers home' }));
    expect(translation(view)).toBe(0); expect(onSelect.mock.calls).toEqual([['home']]);
    await view.rerender(<UniversePager pages={pages} selectedId="home" onSelect={onSelect} />);
    await fireEvent.press(view.getByRole('button', { name: 'home vers musculation' }));
    expect(onSelect.mock.calls).toEqual([['home'], ['musculation']]);
    expect(translation(view)).toBe(-height);
  });
  test('optional development diagnostics report received events without intercepting touch input', async () => {
    const { view, pan } = await setup();
    if (process.env.EXPO_PUBLIC_GESTURE_DEBUG !== '1') {
      expect(view.queryByText('Diagnostic geste · home')).toBeNull();
      return;
    }
    const log = jest.spyOn(console, 'info').mockImplementation(() => undefined);
    const heading = view.getByText('Diagnostic geste · home');
    let panel = heading.parent;
    while (panel && panel.props.pointerEvents !== 'none') panel = panel.parent;
    expect(panel).not.toBeNull();
    await fireEvent(view.getByTestId('universe-viewport'), 'touchStart');
    await startDrag(pan, -20);
    await act(() => emitPan(pan, State.ACTIVE, -100));
    expect(log).toHaveBeenCalledWith('[UniversePager] vue: toucher reçu');
    expect(log).toHaveBeenCalledWith('[UniversePager] pan: touch down');
    expect(log).toHaveBeenCalledWith('[UniversePager] pan: ACTIVE');
    expect(log).toHaveBeenCalledWith('[UniversePager] pan: déplacement reçu');
    expect(translation(view)).toBe(-100);
  });

  test('the native recognizer can activate automatically and scroll views wait without a dependency cycle', async () => {
    const nativeGestures: ReturnType<typeof Gesture.Native>[] = [];
    const createNative = Gesture.Native;
    jest.spyOn(Gesture, 'Native').mockImplementation(() => {
      const gesture = createNative();
      nativeGestures.push(gesture);
      return gesture;
    });
    const { pan } = await setup();
    expect(pan.config.manualActivation).not.toBe(true);
    expect(pan.config).toMatchObject({ activeOffsetYStart: -12, activeOffsetYEnd: 12, failOffsetXStart: -18, failOffsetXEnd: 18, maxPointers: 1 });
    expect(pan.config.requireToFail).toBeUndefined();
    expect(pan.config.blocksHandlers).toBeUndefined();
    expect(pan.config.simultaneousWith).toBeUndefined();
    expect(nativeGestures).toHaveLength(2);
    for (const native of nativeGestures) {
      expect(native.config.requireToFail).toEqual([pan]);
      expect(native.config.simultaneousWith).toBeUndefined();
    }
  });

  test.each([0, 150, 400])('Home accepts an upward gesture with overflowing content at scroll offset %i', async y => {
    const { view, onSelect, pan } = await setup();
    await measure(view, 'home', 1200, y);
    await startDrag(pan, -20);
    await act(() => emitPan(pan, State.ACTIVE, -100));
    expect(translation(view)).toBe(-100);
    await act(() => emitPan(pan, State.END, -200, 0, State.ACTIVE));
    expect(translation(view)).toBe(-height);
    expect(onSelect).toHaveBeenCalledWith('musculation');
  });

  test('queued layout patches preserve each page, both dimensions and the latest UI scroll offset', async () => {
    const { view } = await setup();
    const scroll = pageScrollStates.get('home')!;
    expect(scroll).toBe(pageScrollStates.get('musculation'));
    let liveValue = scroll.value;
    let onUIThread = false;
    const queued: (() => void)[] = [];
    // Reanimated reads .value synchronously on JS but queues writes to its UI
    // runtime. Reproduce that distinction, which the stock Jest mock misses.
    Object.defineProperty(scroll, 'value', {
      configurable: true,
      get: () => liveValue,
      set: (next: Record<string, PageScrollState>) => {
        if (onUIThread) liveValue = next;
        else queued.push(() => { liveValue = next; });
      },
    });
    jest.mocked(runOnUI).mockImplementation(worklet => (...args) => {
      queued.push(() => {
        onUIThread = true;
        try { worklet(...args); } finally { onUIThread = false; }
      });
    });
    try {
      for (const [id, contentHeight] of [['home', 1200], ['musculation', 1800]] as const) {
        const scrollView = view.getByTestId(`scroll-${id}`, { includeHiddenElements: true });
        await fireEvent(scrollView, 'layout', { nativeEvent: { layout: { height, width: 390, x: 0, y: 0 } } });
        await fireEvent(scrollView, 'contentSizeChange', 390, contentHeight);
      }
      // A scroll event already executed on UI while the layout patches wait.
      onUIThread = true;
      await fireEvent.scroll(view.getByTestId('scroll-musculation', { includeHiddenElements: true }), {
        nativeEvent: { contentOffset: { x: 0, y: 125 } },
      });
      onUIThread = false;
      expect(queued).toHaveLength(4);
      await act(() => { for (const update of queued) update(); });
      expect(liveValue).toEqual({
        home: { y: 0, contentHeight: 1200, viewportHeight: height },
        musculation: { y: 125, contentHeight: 1800, viewportHeight: height },
      });
    } finally {
      jest.mocked(runOnUI).mockImplementation(worklet => worklet);
    }
  });

  test('accessible buttons select universes with the same vertical track and hide inactive pages', async () => {
    const { view, onSelect } = await setup();
    expect(translation(view)).toBe(0);
    expect(view.getByTestId('universe-musculation', { includeHiddenElements: true }).props.accessibilityElementsHidden).toBe(true);
    expect(view.queryByRole('button', { name: 'musculation vers home' })).toBeNull();

    await fireEvent.press(view.getByRole('button', { name: 'home vers musculation' }));
    expect(onSelect).toHaveBeenCalledWith('musculation');
    expect(translation(view)).toBe(-height);
    expect(withTiming).toHaveBeenLastCalledWith(-height, expect.objectContaining({ reduceMotion: ReduceMotion.System }), expect.any(Function));
    const home = view.getByTestId('universe-home', { includeHiddenElements: true });
    expect(home.props.pointerEvents).toBe('none');
    expect(home.props.accessibilityElementsHidden).toBe(true);
    expect(home.props.importantForAccessibility).toBe('no-hide-descendants');
    expect(AccessibilityInfo.announceForAccessibility).toHaveBeenCalledWith('Musculation');

    await fireEvent.press(view.getByRole('button', { name: 'musculation vers home' }));
    expect(translation(view)).toBe(0);
    expect(onSelect).toHaveBeenLastCalledWith('home');
  });

  test('native ACTIVE events move the track before selection, in both directions without scroll measurements', async () => {
    const { view, onSelect, pan } = await setup();
    await startDrag(pan, -20);
    await act(() => emitPan(pan, State.ACTIVE, -100, 0, undefined, -80));
    expect(translation(view)).toBe(-100);
    expect(onSelect).not.toHaveBeenCalled();
    expect(view.getByRole('button', { name: 'home vers musculation' })).toBeTruthy();

    await act(() => emitPan(pan, State.END, -180, 0, State.ACTIVE, -160));
    expect(translation(view)).toBe(-height);
    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(onSelect).toHaveBeenLastCalledWith('musculation');

    await startDrag(pan, 20);
    await act(() => emitPan(pan, State.ACTIVE, 75, 0, undefined, 55));
    expect(translation(view)).toBe(-height + 75);
    await act(() => emitPan(pan, State.END, 75, 900, State.ACTIVE));
    expect(translation(view)).toBe(0);
    expect(onSelect).toHaveBeenLastCalledWith('home');
  });

  test('a short drag and backtracking restore the origin instead of claiming the opposite direction', async () => {
    const { view, onSelect, pan } = await setup();
    await measure(view, 'home');
    await startDrag(pan, -20);
    await act(() => {
      emitPan(pan, State.ACTIVE, -60);
      emitPan(pan, State.END, -60, 0, State.ACTIVE);
    });
    expect(translation(view)).toBe(0);
    expect(onSelect).not.toHaveBeenCalled();

    await startDrag(pan, -20);
    await act(() => emitPan(pan, State.ACTIVE, -200));
    expect(translation(view)).toBe(-200);
    await act(() => {
      emitPan(pan, State.ACTIVE, 100);
      emitPan(pan, State.END, 100, 1500, State.ACTIVE);
    });
    expect(translation(view)).toBe(0);
    expect(onSelect).not.toHaveBeenCalled();
  });

  test('native cancellation past the release threshold and multiple touches cannot select another universe', async () => {
    const { view, onSelect, pan } = await setup();
    await measure(view, 'home');
    // Supply the direction snapshot, then use RNGH's real state-change dispatcher.
    const directionManager = managerFor(pan);
    await act(() => {
      pan.handlers.onTouchesDown?.(touches(pan, 1), directionManager);
      pan.handlers.onTouchesMove?.(touches(pan, 2, -20), directionManager);
      fireGestureHandler(pan, [
        { state: State.BEGAN, absoluteY: 400 }, { state: State.ACTIVE, absoluteY: 380, translationY: 0 },
        { state: State.ACTIVE, absoluteY: 180, translationY: -200 },
        { state: State.CANCELLED, absoluteY: 180, translationY: -200, velocityY: -1000 },
      ]);
    });
    expect(translation(view)).toBe(0);
    expect(onSelect).not.toHaveBeenCalled();

    const manager = managerFor(pan);
    await act(() => pan.handlers.onTouchesDown?.(touches(pan, 1, 0, 0, 2), manager));
    expect(manager.fail).toHaveBeenCalledTimes(1);
    expect(manager.activate).not.toHaveBeenCalled();
    await startDrag(pan, -20);
    const secondTouch = managerFor(pan);
    await act(() => pan.handlers.onTouchesMove?.(touches(pan, 2, -40, 0, 2), secondTouch));
    expect(secondTouch.fail).toHaveBeenCalledTimes(1);
    await act(() => emitPan(pan, State.CANCELLED, -40, 0, State.ACTIVE));
    expect(translation(view)).toBe(0);
    expect(onSelect).not.toHaveBeenCalled();
  });

  test('a list owns gestures from its interior even if it reaches the edge before the next touch move', async () => {
    const { view, onSelect, pan } = await setup('musculation');
    await measure(view, 'musculation', 1200, 200);
    const manager = managerFor(pan);
    await act(() => pan.handlers.onTouchesDown?.(touches(pan, 1), manager));
    await fireEvent.scroll(view.getByTestId('scroll-musculation'), { nativeEvent: { contentOffset: { x: 0, y: 0 } } });
    await act(() => pan.handlers.onTouchesMove?.(touches(pan, 2, 40), manager));
    expect(manager.fail).toHaveBeenCalledTimes(1);
    expect(manager.activate).not.toHaveBeenCalled();
    expect(onSelect).not.toHaveBeenCalled();
    expect(translation(view)).toBe(-height);

    // A fresh downward gesture at the top is now eligible to return Home.
    await startDrag(pan, 20);
    await act(() => emitPan(pan, State.END, 200, 0, State.ACTIVE));
    expect(onSelect).toHaveBeenLastCalledWith('home');
    expect(translation(view)).toBe(0);
  });

  test('upward intent on the program list releases the pan so the list can scroll normally', async () => {
    const { view, onSelect, pan } = await setup('musculation');
    await measure(view, 'musculation', 1800, 0);
    const manager = managerFor(pan);
    await act(() => {
      pan.handlers.onTouchesDown?.(touches(pan, 1), manager);
      pan.handlers.onTouchesMove?.(touches(pan, 2, -30), manager);
    });
    expect(manager.fail).toHaveBeenCalledTimes(1);
    expect(onSelect).not.toHaveBeenCalled();
    expect(translation(view)).toBe(-height);
    // Native scrolling is an explicit input here, not simulated UIKit arbitration.
    await fireEvent.scroll(view.getByTestId('scroll-musculation'), { nativeEvent: { contentOffset: { x: 0, y: 250 } } });
    expect(pageScrollStates.get('musculation')?.value.musculation?.y).toBe(250);
  });

  test('a third page shares the registry and cannot be reached by reversing a gesture from the wrong list edge', async () => {
    const { view, onSelect, pan } = await setup('musculation', ['home', 'musculation', 'cardio']);
    await measure(view, 'musculation', 1200, 0);
    await startDrag(pan, 20);
    await act(() => emitPan(pan, State.ACTIVE, 150));
    expect(translation(view)).toBe(-height + 150);
    await act(() => {
      emitPan(pan, State.ACTIVE, -250);
      emitPan(pan, State.END, -250, -1500, State.ACTIVE);
    });
    expect(translation(view)).toBe(-height);
    expect(onSelect).not.toHaveBeenCalled();

    await measure(view, 'musculation', 1200, 400);
    await startDrag(pan, -20);
    await act(() => emitPan(pan, State.END, -200, 0, State.ACTIVE));
    expect(translation(view)).toBe(-height * 2);
    expect(onSelect).toHaveBeenCalledWith('cardio');
    expect(view.getByRole('button', { name: 'cardio vers home' })).toBeTruthy();
    expect(view.queryByRole('button', { name: 'musculation vers home' })).toBeNull();
  });

  test('tiny movements preserve taps and horizontal intent releases the list without manual activation', async () => {
    const { view, onSelect, pan } = await setup();
    const tiny = managerFor(pan);
    await act(() => {
      pan.handlers.onTouchesDown?.(touches(pan, 1), tiny);
      pan.handlers.onTouchesMove?.(touches(pan, 2, -10), tiny);
    });
    expect(tiny.activate).not.toHaveBeenCalled();
    expect(tiny.fail).not.toHaveBeenCalled();
    expect(pan.handlers.onTouchesUp).toBeUndefined();

    const horizontal = managerFor(pan);
    await act(() => {
      pan.handlers.onTouchesDown?.(touches(pan, 1), horizontal);
      pan.handlers.onTouchesMove?.(touches(pan, 2, -20, 80), horizontal);
    });
    expect(horizontal.fail).toHaveBeenCalledTimes(1);
    expect(horizontal.activate).not.toHaveBeenCalled();
    expect(onSelect).not.toHaveBeenCalled();
    expect(translation(view)).toBe(0);
  });

  test('settling blocks a second command until completion and resizing reanchors the selected page', async () => {
    const { view, onSelect, pan } = await setup();
    let finish: (() => void) | undefined;
    jest.mocked(withTiming).mockImplementationOnce((value, _configuration, callback) => {
      finish = () => callback?.(true);
      return value;
    });
    await fireEvent.press(view.getByRole('button', { name: 'home vers musculation' }));
    expect(onSelect).not.toHaveBeenCalled();
    await fireEvent.press(view.getByRole('button', { name: 'home vers home' }));
    expect(withTiming).toHaveBeenCalledTimes(1);
    const manager = managerFor(pan);
    await act(() => pan.handlers.onTouchesDown?.(touches(pan, 1), manager));
    expect(manager.fail).toHaveBeenCalledTimes(1);
    await act(() => finish?.());
    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(onSelect).toHaveBeenCalledWith('musculation');

    await fireEvent(view.getByTestId('universe-viewport'), 'layout', { nativeEvent: { layout: { height: 650, width: 500, x: 0, y: 0 } } });
    expect(translation(view)).toBe(-650);
    expect(view.getByTestId('universe-musculation').props.style.height).toBe(650);
    expect(onSelect).toHaveBeenCalledTimes(1);
    await fireEvent.press(view.getByRole('button', { name: 'musculation vers home' }));
    expect(translation(view)).toBe(0);
    expect(onSelect).toHaveBeenLastCalledWith('home');

    // A resize in the middle of a drag invalidates that gesture's old geometry.
    await measure(view, 'home');
    const drag = await startDrag(pan, -20);
    await act(() => emitPan(pan, State.ACTIVE, -90));
    expect(translation(view)).toBe(-90);
    await fireEvent(view.getByTestId('universe-viewport'), 'layout', { nativeEvent: { layout: { height: 700, width: 500, x: 0, y: 0 } } });
    await act(() => {
      emitPan(pan, State.ACTIVE, -250);
      pan.handlers.onTouchesMove?.(touches(pan, 2, -250), drag);
      emitPan(pan, State.END, -250, -1500, State.ACTIVE);
    });
    expect(drag.fail).toHaveBeenCalledTimes(1);
    expect(translation(view)).toBe(0);
    expect(onSelect).toHaveBeenCalledTimes(2);
  });
});
