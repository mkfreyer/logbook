import { useFocusEffect } from 'expo-router';
import { useCallback, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import type { ActualSetInput, SessionSet, WorkoutSession } from '../../domain/session';
import { formatSeriesTitle, type SeriesDisplay } from '../../domain/series';
import { useSessions } from '../../store/SessionProvider';
import { Card, colors } from '../../ui';
import { messageFor } from '../programs/shared';

export function useSessionData(sessionId?: string) {
  const repository = useSessions();
  const [session, setSession] = useState<WorkoutSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [revision, setRevision] = useState(0);
  const active = useRef(false), generation = useRef(0);
  useFocusEffect(useCallback(() => {
    active.current = true;
    const request = ++generation.current;
    setLoading(true); setError(null);
    void (sessionId ? repository.getSession(sessionId) : Promise.resolve(null))
      .then(value => { if (active.current && request === generation.current) setSession(value); })
      .catch(failure => { if (active.current && request === generation.current) setError(messageFor(failure)); })
      .finally(() => { if (active.current && request === generation.current) setLoading(false); });
    return () => { active.current = false; generation.current++; };
  }, [repository, sessionId, revision]));
  const accept = (value: WorkoutSession) => {
    if (!active.current) return;
    generation.current++; setSession(value); setLoading(false); setError(null);
  };
  return { repository, session, loading, error, accept, retry: () => setRevision(value => value + 1) };
}

export function sessionSeriesTitle(series: SessionSet, display?: SeriesDisplay): string {
  return formatSeriesTitle(series, series.seriesIndex, display);
}

export function parseActualDraft(draft: { weight: string; reps: string; rir: string }): ActualSetInput {
  const parse = (raw: string, label: string, optional = false, decimal = false) => {
    const text = raw.trim();
    if (!text && optional) return null;
    if (!(decimal ? /^\d+(?:[.,]\d+)?$/ : /^\d+$/).test(text)) throw new Error(`${label} : indiquez un nombre ${decimal ? '' : 'entier '}positif ou nul${optional ? ', ou laissez vide' : ''}.`);
    const value = Number(text.replace(',', '.'));
    if (!Number.isFinite(value) || (!decimal && !Number.isSafeInteger(value))) throw new Error(`${label} : cette valeur est trop grande.`);
    return value;
  };
  const weightKg = parse(draft.weight, 'Charge réelle', true, true);
  const reps = parse(draft.reps, 'Répétitions réelles')!;
  const rir = parse(draft.rir, 'RIR réel', true);
  if (rir !== null && rir > 10) throw new Error('Le RIR réel doit être compris entre 0 et 10.');
  return { weightKg, reps, rir };
}

export function NumericInput({ label, value, onChange, decimal = false, disabled = false, placeholder = '—' }: {
  label: string; value: string; onChange(value: string): void; decimal?: boolean; disabled?: boolean; placeholder?: string;
}) {
  return <TextInput accessibilityLabel={label} value={value} onChangeText={onChange}
    keyboardType={decimal ? 'decimal-pad' : 'number-pad'} editable={!disabled} selectionColor={colors.cyan}
    placeholder={placeholder} placeholderTextColor={colors.muted} maxLength={16} style={sessionStyles.input} />;
}

export function NumericCard(props: Parameters<typeof NumericInput>[0] & { caption?: string }) {
  return <Card style={sessionStyles.numberCard}><Text style={sessionStyles.smallLabel}>{props.caption ?? props.label}</Text><NumericInput {...props} /></Card>;
}

export function Choice({ label, selected, disabled, onPress }: { label: string; selected: boolean; disabled: boolean; onPress(): void }) {
  return <Pressable accessibilityRole="radio" accessibilityLabel={label} accessibilityState={{ checked: selected, disabled }}
    disabled={disabled} onPress={onPress} style={[sessionStyles.choice, selected && sessionStyles.selected]}>
    <View style={[sessionStyles.radio, selected && sessionStyles.radioSelected]} />
    <Text style={sessionStyles.choiceText}>{label}</Text>
  </Pressable>;
}

export const sessionStyles = StyleSheet.create({
  sections: { gap: 20 }, row: { flexDirection: 'row', gap: 12, alignItems: 'center' },
  eyebrow: { color: colors.cyan, fontSize: 11, fontWeight: '700', letterSpacing: 1.5 },
  title: { color: colors.text, fontSize: 24, fontWeight: '700', lineHeight: 31 },
  subtitle: { color: colors.text, fontSize: 18, fontWeight: '600', lineHeight: 25 },
  body: { color: colors.muted, fontSize: 14, lineHeight: 21 },
  help: { color: colors.muted, fontSize: 12, lineHeight: 18 },
  center: { textAlign: 'center' },
  numberCard: { flex: 1, minWidth: 0, padding: 12, gap: 6, minHeight: 108 },
  smallLabel: { color: colors.muted, fontSize: 12, lineHeight: 18 },
  input: { color: colors.text, fontSize: 24, minHeight: 46, minWidth: 0, flexGrow: 1, paddingVertical: 4 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12 }, gridCell: { width: '47%', flexGrow: 1 },
  choices: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  choice: { minHeight: 48, paddingHorizontal: 12, paddingVertical: 12, borderRadius: 14, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.surface, flexDirection: 'row', alignItems: 'center', gap: 8 },
  selected: { borderColor: colors.blue, backgroundColor: '#10365a' }, choiceText: { color: colors.text, fontSize: 14, fontWeight: '500' },
  radio: { width: 16, height: 16, borderRadius: 8, borderWidth: 1, borderColor: colors.muted },
  radioSelected: { backgroundColor: colors.blue, borderColor: colors.cyan, borderWidth: 3 },
});
