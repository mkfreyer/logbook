import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { AccessibilityInfo, StyleSheet, View, useWindowDimensions } from 'react-native';
import { Gesture, GestureDetector } from 'react-native-gesture-handler';
import Animated, { cancelAnimation, Easing, ReduceMotion, runOnJS, useAnimatedStyle, useSharedValue, withTiming, type SharedValue } from 'react-native-reanimated';
import { colors } from '../ui';
import { clampDrag, canStartPageDrag, directionalDrag, isVerticalIntent, releaseIndex } from './physics';
import { UniverseNavigationContext, UniversePageContext, type PageScrollState, type UniverseId } from './UniverseContext';

export interface UniversePage { id: UniverseId; label: string; content: ReactNode }
const timing = { duration: 260, easing: Easing.out(Easing.cubic), reduceMotion: ReduceMotion.System };

/** Add Cardio as another page here without introducing a second navigation mechanism. */
export function UniversePager({ pages, selectedId, onSelect }: {
  pages: readonly UniversePage[]; selectedId: UniverseId; onSelect(id: UniverseId): void;
}) {
  const { height: windowHeight } = useWindowDimensions();
  const initialIndex = Math.max(0, pages.findIndex(page => page.id === selectedId));
  const [activeIndex, setActiveIndex] = useState(initialIndex);
  const [height, setHeight] = useState(windowHeight);
  const current = useSharedValue(initialIndex);
  const pageHeight = useSharedValue(height);
  const offset = useSharedValue(-initialIndex * height);
  const busy = useSharedValue(false);
  const dragging = useSharedValue(false);
  const touchX = useSharedValue(0);
  const touchY = useSharedValue(0);
  const initialScrollY = useSharedValue(0);
  const initialMaxScroll = useSharedValue(0);
  const direction = useSharedValue(0);
  const touchHeight = useSharedValue(height);
  // Native scroll events write to this record on the UI thread, outside React renders.
  const scrollStates = useSharedValue<Record<string, PageScrollState>>({});
  const pagesRef = useRef(pages);
  pagesRef.current = pages;
  const onSelectRef = useRef(onSelect);
  onSelectRef.current = onSelect;
  const pageIds = useMemo(() => pages.map(page => page.id), [pages]);
  const count = pages.length;

  const commit = useCallback((index: number) => {
    const page = pagesRef.current[index];
    if (!page) return;
    setActiveIndex(index);
    onSelectRef.current(page.id);
    AccessibilityInfo.announceForAccessibility(page.label);
  }, []);

  const settle = useCallback((index: number) => {
    'worklet';
    busy.value = true;
    offset.value = withTiming(-index * pageHeight.value, timing, finished => {
      if (finished) {
        const changed = current.value !== index;
        current.value = index;
        busy.value = false;
        if (changed) runOnJS(commit)(index);
      }
    });
  }, [busy, offset, pageHeight, current, commit]);

  const goTo = useCallback((id: UniverseId) => {
    const index = pagesRef.current.findIndex(page => page.id === id);
    if (index < 0 || busy.value || dragging.value) return;
    settle(index);
  }, [busy, dragging, settle]);

  useEffect(() => {
    cancelAnimation(offset);
    pageHeight.value = height;
    offset.value = -current.value * height;
    busy.value = false;
    dragging.value = false;
  }, [height, pageHeight, offset, busy, dragging, current]);

  useEffect(() => {
    const index = pagesRef.current.findIndex(page => page.id === selectedId);
    if (index >= 0 && index !== current.value) {
      cancelAnimation(offset);
      current.value = index;
      offset.value = -index * pageHeight.value;
      busy.value = false;
      dragging.value = false;
      setActiveIndex(index);
    }
  }, [selectedId, current, offset, pageHeight, busy, dragging]);

  const pan = useMemo(() => Gesture.Pan().withTestId('universe-pan').manualActivation(true).maxPointers(1)
    .onTouchesDown((event, manager) => {
      if (busy.value || event.numberOfTouches !== 1) { manager.fail(); return; }
      const touch = event.allTouches[0];
      if (!touch) { manager.fail(); return; }
      touchX.value = touch.absoluteX;
      touchY.value = touch.absoluteY;
      touchHeight.value = pageHeight.value;
      const id = pageIds[current.value];
      const scroll = id ? scrollStates.value[id] : undefined;
      if (!scroll || scroll.viewportHeight <= 0) { manager.fail(); return; }
      initialScrollY.value = scroll?.y ?? 0;
      initialMaxScroll.value = Math.max(0, (scroll?.contentHeight ?? 0) - (scroll?.viewportHeight ?? 0));
    })
    .onTouchesMove((event, manager) => {
      const touch = event.allTouches[0];
      if (!touch || event.numberOfTouches !== 1 || busy.value || touchHeight.value !== pageHeight.value) { manager.fail(); return; }
      if (dragging.value) return;
      const dx = touch.absoluteX - touchX.value;
      const dy = touch.absoluteY - touchY.value;
      if (Math.max(Math.abs(dx), Math.abs(dy)) < 12) return;
      if (isVerticalIntent(dx, dy) && canStartPageDrag(current.value, count, dy, initialScrollY.value, initialMaxScroll.value)) {
        direction.value = dy < 0 ? -1 : 1;
        manager.activate();
      }
      else manager.fail();
    })
    .onTouchesUp((_, manager) => { if (!dragging.value) manager.fail(); })
    .onStart(() => { dragging.value = true; })
    .onUpdate(event => { if (touchHeight.value === pageHeight.value) offset.value = clampDrag(current.value, directionalDrag(event.translationY, direction.value), pageHeight.value, count); })
    .onEnd((event, success) => { if (success && touchHeight.value === pageHeight.value) settle(releaseIndex(current.value, count, directionalDrag(event.translationY, direction.value), event.velocityY, pageHeight.value)); })
    .onFinalize((_, success) => {
      if (!success && dragging.value) settle(current.value);
      dragging.value = false;
    }), [busy, dragging, current, offset, pageHeight, touchX, touchY, touchHeight, initialScrollY, initialMaxScroll, direction, scrollStates, pageIds, count, settle]);

  const style = useAnimatedStyle(() => ({ transform: [{ translateY: offset.value }] }));
  const activeId = pages[activeIndex]?.id ?? pages[0]?.id ?? 'home';
  const navigation = useMemo(() => ({ activeId, goTo }), [activeId, goTo]);
  return <UniverseNavigationContext.Provider value={navigation}>
    <GestureDetector gesture={pan}>
      <View testID="universe-viewport" style={s.viewport} onLayout={event => { const next = event.nativeEvent.layout.height; if (next > 0) setHeight(next); }}>
        <Animated.View testID="universe-track" style={[s.track, { height: height * count }, style]}>
          {pages.map((page, index) => <UniversePageView key={page.id} page={page} pan={pan} height={height} active={index === activeIndex} scrollStates={scrollStates} />)}
        </Animated.View>
      </View>
    </GestureDetector>
  </UniverseNavigationContext.Provider>;
}

function UniversePageView({ page, pan, height, active, scrollStates }: {
  page: UniversePage; pan: ReturnType<typeof Gesture.Pan>; height: number; active: boolean;
  scrollStates: SharedValue<Record<string, PageScrollState>>;
}) {
  const value = useMemo(() => ({ id: page.id, pan, scroll: scrollStates }), [page.id, pan, scrollStates]);
  return <UniversePageContext.Provider value={value}>
    <View testID={`universe-${page.id}`} style={{ height, width: '100%' }} pointerEvents={active ? 'auto' : 'none'}
      accessibilityElementsHidden={!active} importantForAccessibility={active ? 'auto' : 'no-hide-descendants'}>{page.content}</View>
  </UniversePageContext.Provider>;
}

const s = StyleSheet.create({
  viewport: { flex: 1, overflow: 'hidden', backgroundColor: colors.background },
  track: { position: 'absolute', left: 0, right: 0, top: 0 },
});
