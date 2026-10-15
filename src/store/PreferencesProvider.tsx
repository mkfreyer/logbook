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
  const lock = useRef(false), mounted = useRef(true);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  useEffect(() => {
    let current = true; setLoading(true); setError(null);
    void repository.getPreferences().then(value => { if (current) setData(value); })
      .catch(failure => { if (current) setError(messageFor(failure)); })
      .finally(() => { if (current) setLoading(false); });
    return () => { current = false; };
  }, [repository, revision]);
  const setRestSoundEnabled = useCallback(async (enabled: boolean) => {
    if (lock.current || !mounted.current || loading || !data) return;
    lock.current = true; setSaving(true); setError(null);
    try {
      const value = await repository.setRestSoundEnabled(enabled);
      if (mounted.current) setData(value);
    } catch (failure) { if (mounted.current) setError(messageFor(failure)); }
    finally { lock.current = false; if (mounted.current) setSaving(false); }
  }, [repository, loading, data]);
  return <Context.Provider value={{ data, loading, saving, error,
    soundEnabled: Boolean(data?.restSoundEnabled && !loading && !saving && !error),
    retry: () => setRevision(value => value + 1), setRestSoundEnabled }}>{children}</Context.Provider>;
}
export function usePreferences() {
  const value = useContext(Context);
  if (!value) throw new Error('usePreferences nécessite PreferencesProvider.');
  return value;
}
