import { router, useFocusEffect } from 'expo-router';
import { useCallback, useState } from 'react';
import { AppState, Text } from 'react-native';

import type { WorkoutSession } from '../../domain/session';
import { useSessions } from '../../store/SessionProvider';
import { Button, Card } from '../../ui';
import { featureStyles, FormError, messageFor } from '../programs/shared';

/** Both universe pages stay mounted: only refresh the visible page, also on foreground. */
export function useActiveSession(enabled = true) {
  const sessions = useSessions();
  const [data, setData] = useState<WorkoutSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [revision, setRevision] = useState(0);
  const retry = useCallback(() => setRevision(value => value + 1), []);
  useFocusEffect(useCallback(() => {
    if (!enabled) return;
    let focused = true;
    let request = 0;
    const refresh = async () => {
      const current = ++request;
      setLoading(true); setError(null);
      try {
        const result = await sessions.getActiveSession();
        if (focused && request === current) setData(result);
      } catch (failure: unknown) {
        if (focused && request === current) setError(messageFor(failure));
      } finally {
        if (focused && request === current) setLoading(false);
      }
    };
    void refresh();
    const listener = AppState.addEventListener('change', state => { if (state === 'active') void refresh(); });
    return () => { focused = false; listener.remove(); };
  }, [enabled, revision, sessions]));
  return { data, loading, error, retry };
}

export function ResumeSessionCard({ active = true }: { active?: boolean }) {
  const session = useActiveSession(active);
  if (session.error) return <Card>
    <FormError message="Impossible de retrouver l’entraînement en cours." />
    <Button label="Réessayer la reprise" variant="secondary" onPress={session.retry} />
  </Card>;
  if (!session.data) return null;
  const current = session.data;
  return <Card style={{ gap: 10 }}>
    <Text style={featureStyles.eyebrow}>ENTRAÎNEMENT EN COURS</Text>
    <Text style={featureStyles.title}>{current.workoutName}</Text>
    <Text style={featureStyles.body}>{current.performances.length} / {current.sets.length} séries validées · progression sauvegardée</Text>
    <Button label="Reprendre la séance" icon="play" disabled={session.loading}
      onPress={() => router.push({ pathname: '/sessions/[sessionId]', params: { sessionId: current.id } })} />
  </Card>;
}
