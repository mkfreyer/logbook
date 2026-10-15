import { useFocusEffect } from 'expo-router';
import { useCallback, useState } from 'react';
import { AppState } from 'react-native';
import { localDayKey, localWeek } from '../../domain/activity';
import type { HomeActivity } from '../../domain/activity';
import { useSessions } from '../../store/SessionProvider';
import { messageFor } from '../programs/shared';

interface ActivitySnapshot {
  data: HomeActivity;
  from: string;
  until: string;
  weekStart: string;
}

/** Only the focused Home universe reads. No subscription to sets/rest writes and
 * no polling: refresh on completion, focus, foreground and next local midnight. */
export function useHomeActivity(enabled: boolean) {
  const repository = useSessions();
  const [now, setNow] = useState(() => new Date());
  const [snapshot, setSnapshot] = useState<ActivitySnapshot | null>(null), [reading, setReading] = useState(true);
  const [error, setError] = useState<string | null>(null), [revision, setRevision] = useState(0);
  useFocusEffect(useCallback(() => {
    if (!enabled) return;
    let mounted = true, request = 0, foreground = true;
    let midnight: ReturnType<typeof setTimeout>;
    const refresh = () => {
      if (!mounted || !foreground) return;
      clearTimeout(midnight);
      const date = new Date(), generation = ++request;
      const week = localWeek(date);
      // Keep both the last successful values and any failure notice until a
      // replacement is available. A normal refresh must not change the cards.
      setNow(date); setReading(true);
      midnight = setTimeout(refresh, new Date(date.getFullYear(), date.getMonth(), date.getDate() + 1).getTime() - date.getTime());
      void repository.history.homeActivity(date).then(value => {
        if (mounted && generation === request) {
          setSnapshot({ data: value, from: week.from, until: week.until, weekStart: week.days[0]!.key });
          setError(null);
        }
      }).catch(failure => { if (mounted && generation === request) setError(messageFor(failure)); })
        .finally(() => { if (mounted && generation === request) setReading(false); });
    };
    refresh();
    const unsubscribe = repository.subscribeCompleted(refresh);
    const appState = AppState.addEventListener('change', state => {
      foreground = state === 'active';
      if (foreground) refresh(); else { clearTimeout(midnight); request++; }
    });
    return () => { mounted = false; request++; clearTimeout(midnight); unsubscribe(); appState.remove(); };
  }, [repository, enabled, revision]));
  // Check the device calendar at render too: returning after a hidden midnight
  // must never briefly label the cached previous week as "Cette semaine".
  const date = new Date(), week = localWeek(date), today = localDayKey(date);
  const isCurrentWeek = !snapshot || (snapshot.from === week.from && snapshot.until === week.until);
  const data = snapshot ? { ...snapshot.data, days: snapshot.data.days.map(day => ({ ...day, today: isCurrentWeek && day.key === today })) } : null;
  return { now, data, isCurrentWeek, weekStart: snapshot?.weekStart ?? null,
    loading: reading && !snapshot, refreshing: reading && !!snapshot, error, retry: () => setRevision(value => value + 1) };
}
