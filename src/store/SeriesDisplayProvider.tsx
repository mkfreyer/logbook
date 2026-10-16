import { useSQLiteContext } from 'expo-sqlite';
import { createContext, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { PreferencesRepository } from '../db/preferencesRepository';
import { DEFAULT_SERIES_DISPLAY, type SeriesDisplay } from '../domain/series';
import { messageFor } from '../features/programs/shared';

interface SeriesPreferences {
  mode: SeriesDisplay; loading: boolean; saving: boolean; error: string | null;
  setMode(mode: SeriesDisplay): Promise<void>; retry(): void;
}
const Context = createContext<SeriesPreferences | null>(null);
/** Independent display preference: no changes to the sound provider or timer. */
export function SeriesDisplayProvider({ children }: { children: ReactNode }) {
  const db = useSQLiteContext(), repository = useMemo(() => new PreferencesRepository(db), [db]);
  const [mode, setMode] = useState(DEFAULT_SERIES_DISPLAY), [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false), [error, setError] = useState<string | null>(null), [revision, setRevision] = useState(0);
  const mounted = useRef(true), desired = useRef(DEFAULT_SERIES_DISPLAY), confirmed = useRef(DEFAULT_SERIES_DISPLAY), generation = useRef(0), failed = useRef(false);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  useEffect(() => {
    let active = true; setLoading(true); setError(null); failed.current = false;
    void repository.getSeriesDisplay().then(value => {
      if (active) { desired.current = confirmed.current = value; setMode(value); }
    }).catch(failure => { if (active) { failed.current = true; setError(messageFor(failure)); } })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [repository, revision]);
  const save = async (value: SeriesDisplay) => {
    if (!mounted.current || loading || failed.current || value === desired.current) return;
    const request = ++generation.current; desired.current = value; setMode(value); setSaving(true);
    try { confirmed.current = await repository.setSeriesDisplay(value); }
    catch (failure) {
      if (mounted.current && request === generation.current) {
        desired.current = confirmed.current; setMode(confirmed.current); failed.current = true; setError(messageFor(failure));
      }
    } finally { if (mounted.current && request === generation.current) setSaving(false); }
  };
  return <Context.Provider value={{ mode, loading, saving, error, setMode: save,
    retry: () => { if (!saving) setRevision(value => value + 1); } }}>{children}</Context.Provider>;
}
export const useSeriesPreferences = () => useContext(Context);
export const useSeriesDisplay = () => useSeriesPreferences()?.mode ?? DEFAULT_SERIES_DISPLAY;
