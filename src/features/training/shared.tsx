import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect } from 'expo-router';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import type { SetTemplate, WeightMode } from '../../domain/training';
import { formatSeriesTitle, type SeriesDisplay } from '../../domain/series';
import { useSeriesDisplay } from '../../store/SeriesDisplayProvider';
import { colors } from '../../ui';
import { messageFor } from '../programs/shared';

export interface TrainingRoute { programId?: string; workoutId?: string; exerciseInstanceId?: string }

export function seriesTitle(series: SetTemplate, index: number, display?: SeriesDisplay): string {
  return formatSeriesTitle(series, index, display);
}

export function repetitionTarget(series: SetTemplate): string {
  return `${series.repsMin === series.repsMax ? series.repsMin : `${series.repsMin}–${series.repsMax}`} reps`;
}

export function weightTarget(series: SetTemplate, mode: WeightMode): string {
  if (series.targetWeightKg === null) return 'Charge non définie';
  const weight = series.targetWeightKg.toLocaleString('fr-FR', { maximumSignificantDigits: 21 });
  return `${weight} kg${mode === 'per_hand' ? ' / haltère' : mode === 'additional' ? ' ajoutés' : ''}`;
}

export function SetTargetSummary({ series, mode, index, compact = false }: {
  series: SetTemplate; mode: WeightMode; index: number; compact?: boolean;
}) {
  const display = useSeriesDisplay();
  return <View style={trainingStyles.setSummary}>
    <Text style={compact ? trainingStyles.compactTitle : trainingStyles.title}>{seriesTitle(series, index, display)}</Text>
    <Text style={trainingStyles.body}>{repetitionTarget(series)} · {weightTarget(series, mode)}{series.targetRir !== null ? ` · RIR ${series.targetRir}` : ''}</Text>
    <Text style={trainingStyles.meta}>{series.restAfterSec === 0 ? 'Aucun repos prévu après cette série' : `Repos après cette série : ${series.restAfterSec} s`}</Text>
    {series.loadRule && <Text style={trainingStyles.hint}>{series.loadRule.percent} % d’une référence prévue{series.targetWeightKg === null ? ' · charge à définir' : ''}</Text>}
    {!compact && series.notes ? <Text style={trainingStyles.body}>{series.notes}</Text> : null}
  </View>;
}

/** Each mutation is locked synchronously and never navigates after leaving the screen. */
export function useScreenOperation() {
  const lock = useRef(false);
  const mounted = useRef(true);
  const focused = useRef(false);
  const completedNavigation = useRef(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  useFocusEffect(useCallback(() => {
    focused.current = true;
    // A pushed editor/session can return to this mounted screen. Only release a
    // completed navigation, never an in-flight write that still owns the lock.
    if (completedNavigation.current) {
      completedNavigation.current = false;
      lock.current = false;
      setBusy(false);
    }
    return () => { focused.current = false; };
  }, []));
  const run = async (operation: () => Promise<unknown>, onSuccess?: () => void, leavesScreen = false) => {
    if (lock.current || !mounted.current || !focused.current) return;
    lock.current = true; setBusy(true); setError(null);
    let succeeded = false;
    try {
      await operation();
      if (mounted.current && focused.current) {
        completedNavigation.current = leavesScreen;
        onSuccess?.(); succeeded = true;
      }
    } catch (failure: unknown) {
      if (mounted.current && focused.current) setError(messageFor(failure));
    } finally {
      // Retain the success lock until navigation removes or blurs this screen.
      // Reordering stays on the screen and unlocks for the next action.
      if (!succeeded || !leavesScreen) {
        lock.current = false;
        if (mounted.current) setBusy(false);
      }
    }
  };
  return { busy, error, setError, run, lock };
}

export function OrderControls({ label, first, last, disabled, onUp, onDown }: {
  label: string; first: boolean; last: boolean; disabled: boolean; onUp(): void; onDown(): void;
}) {
  return <View style={trainingStyles.orderControls}>
    <Pressable accessibilityRole="button" accessibilityLabel={`Monter ${label}`} disabled={first || disabled}
      accessibilityState={{ disabled: first || disabled }} onPress={onUp}
      style={({ pressed }) => [trainingStyles.orderButton, (first || disabled) && trainingStyles.disabled, pressed && trainingStyles.pressed]}>
      <Ionicons name="arrow-up" color={colors.cyan} size={18} />
    </Pressable>
    <Pressable accessibilityRole="button" accessibilityLabel={`Descendre ${label}`} disabled={last || disabled}
      accessibilityState={{ disabled: last || disabled }} onPress={onDown}
      style={({ pressed }) => [trainingStyles.orderButton, (last || disabled) && trainingStyles.disabled, pressed && trainingStyles.pressed]}>
      <Ionicons name="arrow-down" color={colors.cyan} size={18} />
    </Pressable>
  </View>;
}

export function swappedIds(items: { id: string }[], index: number, delta: -1 | 1): string[] {
  const ids = items.map(item => item.id);
  const destination = index + delta;
  const current = ids[index]; const other = ids[destination];
  if (current === undefined || other === undefined) return ids;
  ids[index] = other; ids[destination] = current;
  return ids;
}

export const trainingStyles = StyleSheet.create({
  sections: { gap: 18 }, cards: { gap: 12 }, row: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  grow: { flex: 1, minWidth: 0 }, title: { color: colors.text, fontWeight: '600', fontSize: 17, lineHeight: 24 },
  compactTitle: { color: colors.text, fontWeight: '500', fontSize: 14, lineHeight: 21 },
  body: { color: colors.muted, fontSize: 13, lineHeight: 20 },
  meta: { color: colors.cyan, fontSize: 12, lineHeight: 19 },
  eyebrow: { color: colors.cyan, fontSize: 11, fontWeight: '700', letterSpacing: 1.6 },
  icon: { width: 48, height: 48, backgroundColor: '#123e65', borderWidth: 1, borderColor: '#236293', borderRadius: 14, alignItems: 'center', justifyContent: 'center' },
  setSummary: { gap: 3, flex: 1, minWidth: 0 },
  sets: { gap: 10, borderTopWidth: 1, borderTopColor: colors.border, paddingTop: 12 },
  orderControls: { flexDirection: 'row', gap: 6, justifyContent: 'flex-end' },
  orderButton: { minWidth: 44, minHeight: 44, alignItems: 'center', justifyContent: 'center', borderRadius: 12, backgroundColor: colors.surfaceRaised, borderWidth: 1, borderColor: colors.border },
  disabled: { opacity: 0.35 }, pressed: { opacity: 0.7 },
  hint: { color: colors.muted, fontSize: 12, lineHeight: 19 },
});
