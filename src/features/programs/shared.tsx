import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect } from 'expo-router';
import { useCallback, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import { Button, Card, colors, EmptyState } from '../../ui';

export function routeId(value: string | string[] | undefined): string | undefined {
  return typeof value === 'string' && value.length > 0 ? value : undefined;
}

export function messageFor(error: unknown): string {
  return error instanceof Error ? error.message : 'Une erreur est survenue. Réessayez.';
}

/** Refresh route data when returning from an editor, ignoring late responses after blur. */
export function useFocusedData<T>(load: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [revision, setRevision] = useState(0);

  useFocusEffect(
    useCallback(() => {
      let active = true;
      setLoading(true);
      setError(null);
      void load()
        .then((result) => {
          if (active) setData(result);
        })
        .catch((failure: unknown) => {
          if (active) setError(messageFor(failure));
        })
        .finally(() => {
          if (active) setLoading(false);
        });
      return () => { active = false; };
    }, [load, revision]),
  );

  const retry = useCallback(() => setRevision((value) => value + 1), []);
  return { data, loading, error, retry };
}

export function LoadState({ loading, error, retry, missing }: {
  loading: boolean;
  error: string | null;
  retry: () => void;
  missing?: string;
}) {
  if (loading) {
    return <View style={styles.loading} accessibilityRole="progressbar" accessibilityLabel="Chargement">
      <ActivityIndicator color={colors.blue} size="large" />
      <Text style={styles.muted}>Chargement…</Text>
    </View>;
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
  loading: { paddingVertical: 60, alignItems: 'center', gap: 16 },
  muted: { color: colors.muted, fontSize: 15 },
  error: { color: colors.danger, fontSize: 14, lineHeight: 21 },
  notice: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7, paddingVertical: 6 },
  noticeText: { color: colors.muted, fontSize: 11, flexShrink: 1 },
});
