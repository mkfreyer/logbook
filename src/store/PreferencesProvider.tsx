import { useSQLiteContext } from 'expo-sqlite';
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { PreferencesRepository } from '../db/preferencesRepository';
import type { Preferences } from '../domain/preferences';
import { messageFor } from '../features/programs/shared';

interface PreferencesState {
  data: Preferences | null; loading: boolean; saving: boolean; error: string | null;
  soundEnabled: boolean; retry(): void; setRestSoundEnabled(enabled: boolean): Promise<void>;
}
const Context = createContext<PreferencesState | null>(null);
export function PreferencesProvider({ children }: { children: ReactNode }) {
  const db = useSQLiteContext(), repository = useMemo(() => new PreferencesRepository(db), [db]);
  const [data, setData] = useState<Preferences | null>(null), [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false), [error, setError] = useState<string | null>(null), [revision, setRevision] = useState(0);
  const mounted = useRef(true), confirmed = useRef<Preferences | null>(null), desired = useRef<Preferences | null>(null);
  const latest = useRef(0), failed = useRef(false);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  useEffect(() => {
    let current = true; setLoading(true); setError(null); failed.current = false;
    void repository.getPreferences().then(value => {
      if (current) { confirmed.current = desired.current = value; setData(value); }
    })
      .catch(failure => { if (current) { failed.current = true; setError(messageFor(failure)); } })
      .finally(() => { if (current) setLoading(false); });
    return () => { current = false; };
  }, [repository, revision]);
  const setRestSoundEnabled = useCallback(async (enabled: boolean) => {
    if (!mounted.current || loading || !desired.current || failed.current || desired.current.restSoundEnabled === enabled) return;
    const request = ++latest.current;
    // UISwitch is controlled: acknowledge its native value in the SAME event.
    // SQLite's queue serializes writes; old completions must never reset a newer intent.
    desired.current = { restSoundEnabled: enabled };
    setData(desired.current); setSaving(true); setError(null);
    try {
      const value = await repository.setRestSoundEnabled(enabled);
      confirmed.current = value;
    } catch (failure) {
      if (mounted.current && request === latest.current) {
        desired.current = confirmed.current; setData(confirmed.current);
        failed.current = true; setError(messageFor(failure));
      }
    } finally { if (mounted.current && request === latest.current) setSaving(false); }
  }, [repository, loading]);
  return <Context.Provider value={{ data, loading, saving, error,
    soundEnabled: Boolean(data?.restSoundEnabled && !loading && !saving && !error),
    retry: () => setRevision(value => value + 1), setRestSoundEnabled }}>{children}</Context.Provider>;
}
export function usePreferences() {
  const value = useContext(Context);
  if (!value) throw new Error('usePreferences nécessite PreferencesProvider.');
  return value;
}
