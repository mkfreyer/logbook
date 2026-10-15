import { useFocusEffect } from 'expo-router';
import { useCallback, useState } from 'react';
import { AppState, Pressable, StyleSheet, Text, View } from 'react-native';
import { historyPeriods, type HistoryPeriod } from '../../domain/history';
import { Button, Card, colors } from '../../ui';
import { sessionStyles as s } from '../sessions/shared';

export const historyNumber = (value: number) => value.toLocaleString('fr-FR', { maximumFractionDigits: 2 });
export const historyDate = (date: string) => new Date(date).toLocaleString('fr-FR', { dateStyle: 'medium', timeStyle: 'short' });
export const historyWeight = (value: number | null) => value === null ? '—' : `${historyNumber(value)} kg`;

/** Refresh calendar filters at focus, foreground and local midnight, not on timer ticks. */
export function useHistoryClock() {
  const [now, setNow] = useState(() => new Date());
  useFocusEffect(useCallback(() => {
    let timer: ReturnType<typeof setTimeout>;
    const update = () => {
      clearTimeout(timer);
      const date = new Date(); setNow(date);
      timer = setTimeout(update, new Date(date.getFullYear(), date.getMonth(), date.getDate() + 1).getTime() - date.getTime() + 50);
    };
    update();
    const subscription = AppState.addEventListener('change', state => { if (state === 'active') update(); });
    return () => { clearTimeout(timer); subscription.remove(); };
  }, []));
  return now;
}

/** Same calendar bounds keep the snapshot; foreground still requests fresh rows. */
export function useHistoryForegroundRefresh(retry: () => void) {
  useFocusEffect(useCallback(() => {
    const subscription = AppState.addEventListener('change', state => { if (state === 'active') retry(); });
    return () => subscription.remove();
  }, [retry]));
}
export function PeriodPicker({ value, onChange }: { value: HistoryPeriod; onChange(value: HistoryPeriod): void }) {
  return <View accessibilityRole="radiogroup" accessibilityLabel="Période" style={h.tabs}>
    {historyPeriods.map(item => <HistoryTab key={item.id} label={item.label} selected={value === item.id} onPress={() => onChange(item.id)} />)}
  </View>;
}
export function HistoryTab({ label, selected, onPress }: { label: string; selected: boolean; onPress(): void }) {
  return <Pressable accessibilityRole="radio" accessibilityLabel={label} accessibilityState={{ checked: selected }} onPress={onPress}
    style={[h.tab, selected && h.selected]}><Text style={[s.help, { color: selected ? colors.text : colors.muted }]}>{label}</Text></Pressable>;
}
export function HistoryMetric({ label, value }: { label: string; value: string }) {
  return <Card style={h.metric}><Text style={s.help}>{label}</Text><Text accessibilityLabel={label} style={h.value}>{value}</Text></Card>;
}
export function HistoryPagination({ page, count, onChange }: { page: number; count: number; onChange(page: number): void }) {
  if (count <= 1) return null;
  return <View style={{ gap: 8 }}><Text style={[s.help, s.center]}>Page {page + 1} sur {count}</Text>
    <View style={s.row}><View style={{ flex: 1 }}><Button label="Précédente" variant="secondary" disabled={page === 0} onPress={() => onChange(page - 1)} /></View>
      <View style={{ flex: 1 }}><Button label="Suivante" variant="secondary" disabled={page + 1 >= count} onPress={() => onChange(page + 1)} /></View></View></View>;
}
export const h = StyleSheet.create({
  tabs: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  tab: { minHeight: 44, minWidth: 60, paddingHorizontal: 11, paddingVertical: 12, borderRadius: 12, borderWidth: 1, borderColor: colors.border, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.surface },
  selected: { borderColor: colors.blue, backgroundColor: '#12436c' },
  metrics: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  metric: { width: '47%', flexGrow: 1, gap: 8, padding: 14 },
  value: { color: colors.text, fontSize: 22, fontWeight: '600', fontVariant: ['tabular-nums'] },
  tableRow: { flexDirection: 'row', gap: 6, alignItems: 'center', paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: colors.border },
  seriesCell: { flex: 1.5 }, cell: { flex: 1, textAlign: 'right' },
});
