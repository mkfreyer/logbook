import { useContext, useMemo, type ReactNode } from 'react';
import { StyleSheet, type StyleProp, type ViewStyle } from 'react-native';
import { Gesture, GestureDetector } from 'react-native-gesture-handler';
import Animated, { useAnimatedScrollHandler } from 'react-native-reanimated';
import { SafeAreaView } from 'react-native-safe-area-context';
import { colors } from '../ui';
import { UniversePageContext } from './UniverseContext';

const emptyScroll = { y: 0, contentHeight: 0, viewportHeight: 0 };

/** Only universe pages use this tracked scroll view. Forms retain their ordinary Screen. */
export function UniverseScreen({ children, contentContainerStyle, testID }: {
  children: ReactNode; contentContainerStyle?: StyleProp<ViewStyle>; testID?: string;
}) {
  const page = useContext(UniversePageContext);
  if (!page) throw new Error('UniverseScreen nécessite un contexte de page.');
  const { scroll, pan, id } = page;
  const nativeScroll = useMemo(() => Gesture.Native().requireExternalGestureToFail(pan), [pan]);
  const onScroll = useAnimatedScrollHandler(event => {
    scroll.value = { ...scroll.value, [id]: { ...(scroll.value[id] ?? emptyScroll), y: Math.max(0, event.contentOffset.y) } };
  });
  return <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
    <GestureDetector gesture={nativeScroll}>
      <Animated.ScrollView testID={testID} onScroll={onScroll} scrollEventThrottle={16} bounces={false} overScrollMode="never"
        showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled"
        onContentSizeChange={(_, contentHeight) => { scroll.value = { ...scroll.value, [id]: { ...(scroll.value[id] ?? emptyScroll), contentHeight } }; }}
        onLayout={event => { scroll.value = { ...scroll.value, [id]: { ...(scroll.value[id] ?? emptyScroll), viewportHeight: event.nativeEvent.layout.height } }; }}
        contentContainerStyle={[s.content, contentContainerStyle]}>
        {children}
      </Animated.ScrollView>
    </GestureDetector>
  </SafeAreaView>;
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.background },
  content: { padding: 24, gap: 24, flexGrow: 1, paddingBottom: 32, width: '100%', maxWidth: 640, alignSelf: 'center' },
});
