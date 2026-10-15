import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { AccessibilityInfo, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { Gesture, GestureDetector } from 'react-native-gesture-handler';
import Animated, { cancelAnimation, Easing, ReduceMotion, runOnJS, useAnimatedStyle, useSharedValue, withTiming, type SharedValue } from 'react-native-reanimated';
import { colors } from '../ui';
import { clampDrag, canStartPageDrag, directionalDrag, isVerticalIntent, releaseIndex } from './physics';
import { coveredPageOffset } from './presentation';
import { UniverseNavigationContext, UniversePageContext, type PageScrollState, type UniverseId } from './UniverseContext';

export interface UniversePage { id: UniverseId; label: string; content: ReactNode }
const timing = { duration: 260, easing: Easing.out(Easing.cubic), reduceMotion: ReduceMotion.System };
const debugGestures = __DEV__ && process.env.EXPO_PUBLIC_GESTURE_DEBUG === '1';

/** Add Cardio as another page here without introducing a second navigation mechanism. */
export function UniversePager({ pages, selectedId, selectionReceipt, onSelect }: {
  pages: readonly UniversePage[]; selectedId: UniverseId; selectionReceipt?: string; onSelect(id: UniverseId, receipt: string): void;
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
  const reportedUpdate = useSharedValue(false);
  const [trace, setTrace] = useState<string[]>([]);
  const diagnose = useCallback((message: string) => {
    if (!debugGestures) return;
    console.info(`[UniversePager] ${message}`);
    setTrace(lines => [...lines.slice(-5), message]);
  }, []);
  // Native scroll events write to this record on the UI thread, outside React renders.
  const scrollStates = useSharedValue<Record<string, PageScrollState>>({});
  const pagesRef = useRef(pages);
  pagesRef.current = pages;
  const onSelectRef = useRef(onSelect);
  onSelectRef.current = onSelect;
  const selectionSerial = useRef(0);
  const pendingSelections = useRef(new Map<string, UniverseId>());
  const pageIds = useMemo(() => pages.map(page => page.id), [pages]);
  const count = pages.length;

  const commit = useCallback((index: number) => {
    const page = pagesRef.current[index];
    if (!page) return;
    setActiveIndex(index);
    const receipt = String(++selectionSerial.current);
    pendingSelections.current.set(receipt, page.id);
    if (debugGestures) diagnose(`sélection UI #${receipt}: ${page.id}`);
    onSelectRef.current(page.id, receipt);
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
    if (debugGestures) diagnose(`géométrie: hauteur=${Math.round(height)}`);
    cancelAnimation(offset);
    pageHeight.value = height;
    offset.value = -current.value * height;
    busy.value = false;
    dragging.value = false;
  }, [height, pageHeight, offset, busy, dragging, current, diagnose]);

  useEffect(() => {
    // Router echoes may arrive AFTER another UI-thread swipe has completed or
    // started. An acknowledgement must not cancel/reanchor the current track.
    if (selectionReceipt && pendingSelections.current.get(selectionReceipt) === selectedId) {
      for (const receipt of pendingSelections.current.keys()) {
        if (Number(receipt) <= Number(selectionReceipt)) pendingSelections.current.delete(receipt);
      }
      if (debugGestures) diagnose(`route: accusé #${selectionReceipt} ${selectedId} (sans déplacement)`);
      return;
    }
    const index = pagesRef.current.findIndex(page => page.id === selectedId);
    if (index >= 0 && index !== current.value) {
      if (debugGestures) diagnose(`route externe: ${selectedId}, position=${Math.round(offset.value)}`);
      cancelAnimation(offset);
      current.value = index;
      offset.value = -index * pageHeight.value;
      busy.value = false;
      dragging.value = false;
      setActiveIndex(index);
    }
  }, [selectedId, selectionReceipt, current, offset, pageHeight, busy, dragging, diagnose]);

  // UIKit activates this pan itself after the vertical threshold. The native
  // ScrollView waits only for this decision; no manual activation recognizer.
  const pan = useMemo(() => Gesture.Pan().withTestId('universe-pan')
    .activeOffsetY([-12, 12]).failOffsetX([-18, 18]).maxPointers(1)
    .onTouchesDown((event, manager) => {
      if (debugGestures) runOnJS(diagnose)('pan: touch down');
      if (busy.value || event.numberOfTouches !== 1) {
        if (debugGestures) runOnJS(diagnose)('refus: animation / plusieurs doigts');
        manager.fail(); return;
      }
      const touch = event.allTouches[0];
      if (!touch) { manager.fail(); return; }
      direction.value = 0;
      reportedUpdate.value = false;
      touchX.value = touch.absoluteX;
      touchY.value = touch.absoluteY;
      touchHeight.value = pageHeight.value;
      const id = pageIds[current.value];
      const scroll = id ? scrollStates.value[id] : undefined;
      // Home needs no measurement. A newly mounted list starts at y=0.
      // Missing asynchronous layout events must never disable the whole pager.
      initialScrollY.value = scroll?.y ?? 0;
      initialMaxScroll.value = Math.max(0, (scroll?.contentHeight ?? 0) - (scroll?.viewportHeight ?? 0));
    })
    .onBegin(() => { if (debugGestures) runOnJS(diagnose)('pan: began'); })
    .onTouchesMove((event, manager) => {
      const touch = event.allTouches[0];
      if (!touch || event.numberOfTouches !== 1 || busy.value || touchHeight.value !== pageHeight.value) { manager.fail(); return; }
      if (dragging.value) return;
      const dx = touch.absoluteX - touchX.value;
      const dy = touch.absoluteY - touchY.value;
      if (Math.max(Math.abs(dx), Math.abs(dy)) < 12) return;
      if (isVerticalIntent(dx, dy) && canStartPageDrag(current.value, count, dy, initialScrollY.value, initialMaxScroll.value)) {
        direction.value = dy < 0 ? -1 : 1;
        if (debugGestures) runOnJS(diagnose)(`autorisé: ${pageIds[current.value]} y=${Math.round(initialScrollY.value)}`);
      }
      else {
        if (debugGestures) runOnJS(diagnose)(`liste / axe: y=${Math.round(initialScrollY.value)}`);
        manager.fail();
      }
    })
    .onStart(event => {
      dragging.value = true;
      if (debugGestures) runOnJS(diagnose)('pan: ACTIVE');
      // iOS resets translationY at automatic activation. Absolute coordinates
      // retain the full finger movement and do not depend on the moving track.
      if (touchHeight.value === pageHeight.value) offset.value = clampDrag(current.value, directionalDrag(event.absoluteY - touchY.value, direction.value), pageHeight.value, count);
    })
    .onUpdate(event => {
      if (touchHeight.value === pageHeight.value) offset.value = clampDrag(current.value, directionalDrag(event.absoluteY - touchY.value, direction.value), pageHeight.value, count);
      if (debugGestures && !reportedUpdate.value) {
        reportedUpdate.value = true;
        runOnJS(diagnose)('pan: déplacement reçu');
      }
    })
    .onEnd((event, success) => {
      if (success && touchHeight.value === pageHeight.value) settle(releaseIndex(current.value, count, directionalDrag(event.absoluteY - touchY.value, direction.value), event.velocityY, pageHeight.value));
    })
    .onFinalize((_, success) => {
      if (debugGestures) runOnJS(diagnose)(success ? 'pan: terminé' : 'pan: annulé / refusé');
      if (!success && dragging.value) settle(current.value);
      dragging.value = false;
    }), [busy, dragging, current, offset, pageHeight, touchX, touchY, touchHeight, initialScrollY, initialMaxScroll, direction, scrollStates, pageIds, count, settle, reportedUpdate, diagnose]);

  const style = useAnimatedStyle(() => ({ transform: [{ translateY: offset.value }] }));
  const activeId = pages[activeIndex]?.id ?? pages[0]?.id ?? 'home';
  const navigation = useMemo(() => ({ activeId, goTo }), [activeId, goTo]);
  return <UniverseNavigationContext.Provider value={navigation}>
    <GestureDetector gesture={pan}>
      <View testID="universe-viewport" collapsable={false} style={s.viewport}
        onTouchStart={debugGestures ? () => diagnose('vue: toucher reçu') : undefined}
        onLayout={event => { const next = event.nativeEvent.layout.height; if (next > 0) setHeight(next); }}>
        <Animated.View testID="universe-track" style={[s.track, { height: height * count }, style]}>
          {pages.map((page, index) => <UniversePageView key={page.id} page={page} index={index} offset={offset} pan={pan} height={height} active={index === activeIndex} scrollStates={scrollStates} />)}
        </Animated.View>
        {debugGestures && <View pointerEvents="none" style={s.diagnostic}>
          <Text style={s.diagnosticText}>Diagnostic geste · {activeId}</Text>
          <Text style={s.diagnosticText}>{trace.length ? trace.join('\n') : 'Touchez puis glissez sur l’écran.'}</Text>
        </View>}
      </View>
    </GestureDetector>
  </UniverseNavigationContext.Provider>;
}

function UniversePageView({ page, index, offset, pan, height, active, scrollStates }: {
  page: UniversePage; index: number; offset: SharedValue<number>; pan: ReturnType<typeof Gesture.Pan>; height: number; active: boolean;
  scrollStates: SharedValue<Record<string, PageScrollState>>;
}) {
  const value = useMemo(() => ({ id: page.id, pan, scroll: scrollStates }), [page.id, pan, scrollStates]);
  const presentation = useAnimatedStyle(() => ({ transform: [{ translateY: coveredPageOffset(index, offset.value, height) }] }));
  return <UniversePageContext.Provider value={value}>
    <Animated.View testID={`universe-${page.id}`} style={[{ height, width: '100%', flexShrink: 0, zIndex: index, overflow: 'hidden', backgroundColor: colors.background }, presentation]}
      pointerEvents={active ? 'auto' : 'none'} accessibilityElementsHidden={!active}
      importantForAccessibility={active ? 'auto' : 'no-hide-descendants'}>{page.content}</Animated.View>
  </UniversePageContext.Provider>;
}

const s = StyleSheet.create({
  viewport: { flex: 1, overflow: 'hidden', backgroundColor: colors.background },
  track: { position: 'absolute', left: 0, right: 0, top: 0 },
  diagnostic: { position: 'absolute', top: 70, left: 12, right: 12, padding: 10, backgroundColor: '#09121fee', borderRadius: 8, borderWidth: 1, borderColor: colors.cyan },
  diagnosticText: { fontSize: 11, lineHeight: 15, color: colors.text },
});
