import { createContext, useContext } from 'react';
import type { Gesture } from 'react-native-gesture-handler';
import type { SharedValue } from 'react-native-reanimated';

export type UniverseId = 'home' | 'musculation' | 'cardio';

export interface UniverseNavigation {
  activeId: UniverseId;
  goTo(id: UniverseId): void;
}
export const UniverseNavigationContext = createContext<UniverseNavigation | null>(null);

export interface PageScrollState {
  y: number;
  contentHeight: number;
  viewportHeight: number;
}
export const UniversePageContext = createContext<{
  id: UniverseId;
  // RNGH 3's root PanGesture is the new hook API, not this builder API.
  pan: ReturnType<typeof Gesture.Pan>;
  scroll: SharedValue<Record<string, PageScrollState>>;
} | null>(null);

export function useUniverseNavigation() {
  const context = useContext(UniverseNavigationContext);
  if (!context) throw new Error('Un univers doit être affiché dans UniversePager.');
  return context;
}

export function useUniverseIsActive() {
  const page = useContext(UniversePageContext);
  return useUniverseNavigation().activeId === page?.id;
}
