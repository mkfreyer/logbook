import { useFocusEffect } from 'expo-router';
import { useCallback, useState } from 'react';
import { AppState } from 'react-native';
import type { HomeActivity } from '../../domain/activity';
import { useSessions } from '../../store/SessionProvider';
import { messageFor } from '../programs/shared';

/** Only the focused Home universe reads. No subscription to sets/rest writes and
 * no polling: refresh on completion, focus, foreground and next local midnight. */
export function useHomeActivity(enabled: boolean) {
  const repository = useSessions();
  const [now, setNow] = useState(() => new Date());
  const [data, setData] = useState<HomeActivity | null>(null), [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null), [revision, setRevision] = useState(0);
  useFocusEffect(useCallback(() => {
    if (!enabled) return;
    let mounted = true, request = 0, foreground = true;
    let midnight: ReturnType<typeof setTimeout>;
    const refresh = () => {
      if (!mounted || !foreground) return;
      clearTimeout(midnight);
      const date = new Date(), generation = ++request;
      setNow(date); setLoading(true); setError(null);
      midnight = setTimeout(refresh, new Date(date.getFullYear(), date.getMonth(), date.getDate() + 1).getTime() - date.getTime() + 50);
      void repository.history.homeActivity(date).then(value => {
        if (mounted && generation === request) setData(value);
      }).catch(failure => { if (mounted && generation === request) setError(messageFor(failure)); })
        .finally(() => { if (mounted && generation === request) setLoading(false); });
    };
    refresh();
    const unsubscribe = repository.subscribeCompleted(refresh);
    const appState = AppState.addEventListener('change', state => {
      foreground = state === 'active';
      if (foreground) refresh(); else { clearTimeout(midnight); request++; }
    });
    return () => { mounted = false; request++; clearTimeout(midnight); unsubscribe(); appState.remove(); };
  }, [repository, enabled, revision]));
  return { now, data, loading, error, retry: () => setRevision(value => value + 1) };
}
