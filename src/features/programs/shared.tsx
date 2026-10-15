import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect } from 'expo-router';
import { useCallback, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import { NotFoundError } from '../../db/repository';
import { TrainingNotFoundError } from '../../db/trainingRepository';
import { Button, Card, colors, EmptyState } from '../../ui';

export function routeId(value: string | string[] | undefined): string | undefined {
  return typeof value === 'string' && value.length > 0 ? value : undefined;
}

export function messageFor(error: unknown): string {
  return error instanceof Error ? error.message : 'Une erreur est survenue. Réessayez.';
}

/** One local snapshot, scoped to a memoized reader (including its route IDs).
 * Returning to the same screen refreshes silently; a different reader hides the
 * old snapshot during render, before the focus effect can start its new read. */
export function useFocusedData<T>(load: () => Promise<T>) {
  const [state, setState] = useState({ reader: load, data: null as T | null,
    reading: true, settled: false, error: null as string | null });
  const [revision, setRevision] = useState(0);
  const reading = useRef(false);

  useFocusEffect(
    useCallback(() => {
      let active = true;
      reading.current = true;
      setState(current => current.reader === load ? { ...current, reading: true }
        : { reader: load, data: null, reading: true, settled: false, error: null });
      void (async () => {
        try {
          const result = await load();
          // null is an authoritative missing result, not a failed refresh: it
          // must evict the previous item, even if the following retry fails.
          if (active) setState({ reader: load, data: result, reading: false, settled: true, error: null });
        } catch (failure: unknown) {
          if (active) {
            if (failure instanceof NotFoundError || failure instanceof TrainingNotFoundError) {
              setState({ reader: load, data: null, reading: false, settled: true, error: null });
            } else setState(current => current.reader === load
              ? { ...current, reading: false, settled: true, error: messageFor(failure) } : current);
          }
        } finally {
          if (active) reading.current = false;
        }
      })();
      return () => { active = false; reading.current = false; };
    }, [load, revision]),
  );

  const retry = useCallback(() => {
    if (reading.current) return;
    reading.current = true;
    setRevision(value => value + 1);
  }, []);
  const matches = state.reader === load;
  const data = matches ? state.data : null;
  const error = matches ? state.error : null;
  return { data, loading: !matches || state.reading && !state.settled,
    refreshing: matches && state.reading && state.settled,
    // Existing LoadState guards receive only blocking errors. A successful
    // empty list is valid data too; it must not become an error screen.
    error: data == null ? error : null, refreshError: data != null ? error : null, retry };
}

/** Kept separate from LoadState so existing content and scroll views stay mounted. */
export function RefreshNotice({ refreshError, retry, refreshing = false }: {
  refreshError?: string | null; retry(): void; refreshing?: boolean;
}) {
  if (!refreshError) return null;
  return <Pressable accessibilityRole="button" accessibilityLabel="Données non à jour, réessayer"
    accessibilityState={{ disabled: refreshing }} disabled={refreshing} onPress={retry} style={styles.refreshNotice}>
    <Text style={styles.noticeText}>Données non à jour · Réessayer</Text>
  </Pressable>;
}

export function LoadState({ loading, error, retry, missing }: {
  loading: boolean;
  error: string | null;
  retry: () => void;
  missing?: string;
}) {
  if (loading) {
    return <Card><View style={styles.loading} accessible accessibilityRole="progressbar" accessibilityLabel="Chargement">
      <ActivityIndicator color={colors.blue} size="small" />
      <Text style={styles.muted}>Chargement…</Text>
    </View></Card>;
  }
  return <Card>
    <EmptyState icon="alert-circle-outline" title={error ? 'Chargement impossible' : 'Introuvable'}
      description={error ?? missing ?? 'Cet élément n’est plus disponible.'} />
    {error ? <Button label="Réessayer" variant="secondary" onPress={retry} /> : null}
  </Card>;
}

export function FormError({ message }: { message: string | null }) {
  if (!message) return null;
  return <Text accessibilityRole="alert" style={styles.error}>{message}</Text>;
}

export function LocalNotice() {
  return <View style={styles.notice}>
    <Ionicons name="shield-checkmark-outline" color={colors.cyan} size={17} />
    <Text style={styles.noticeText}>Vos données restent sur votre iPhone · hors ligne</Text>
  </View>;
}

export const featureStyles = StyleSheet.create({
  sections: { gap: 20 },
  cards: { gap: 12 },
  row: { flexDirection: 'row', alignItems: 'center', gap: 14 },
  grow: { flex: 1, minWidth: 0 },
  icon: {
    width: 48, height: 48, borderRadius: 15, alignItems: 'center', justifyContent: 'center',
    backgroundColor: '#123e65', borderWidth: 1, borderColor: '#236293',
  },
  title: { color: colors.text, fontSize: 18, fontWeight: '600', lineHeight: 25 },
  body: { color: colors.muted, fontSize: 14, lineHeight: 21 },
  meta: { color: colors.cyan, fontSize: 12, fontWeight: '500', marginTop: 8 },
  eyebrow: { color: colors.cyan, fontSize: 11, fontWeight: '700', letterSpacing: 1.8 },
});

const styles = StyleSheet.create({
  loading: { minHeight: 144, justifyContent: 'center', alignItems: 'center', gap: 16 },
  refreshNotice: { minHeight: 44, justifyContent: 'center', paddingVertical: 8 },
  muted: { color: colors.muted, fontSize: 15 },
  error: { color: colors.danger, fontSize: 14, lineHeight: 21 },
  notice: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7, paddingVertical: 6 },
  noticeText: { color: colors.muted, fontSize: 11, flexShrink: 1 },
});
