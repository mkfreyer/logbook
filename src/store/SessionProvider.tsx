import { randomUUID } from 'expo-crypto';
import { useSQLiteContext } from 'expo-sqlite';
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { AppState } from 'react-native';
import { SessionRepository } from '../db/sessionRepository';
import { selectSessionStep, type RestInterval } from '../domain/session';
import { useRestAlert } from '../features/sessions/useRestAlert';

const SessionContext = createContext<SessionRepository | null>(null);

/** Executions share logbook.db, but own their snapshots and recorded performances. */
export function SessionProvider({ children }: { children: ReactNode }) {
  const db = useSQLiteContext();
  const repository = useMemo(() => new SessionRepository(db, randomUUID), [db]);
  return <SessionContext.Provider value={repository}><RestSoundObserver repository={repository} />{children}</SessionContext.Provider>;
}

/** Keep the foreground cue alive when navigating away from the rest screen. */
function RestSoundObserver({ repository }: { repository: SessionRepository }) {
  const [rest, setRest] = useState<RestInterval | null>(null);
  useRestAlert(rest, true);
  useEffect(() => {
    let mounted = true, request = 0;
    const refresh = async () => {
      const version = ++request;
      try {
        const session = await repository.getActiveSession();
        if (!mounted || version !== request) return;
        const step = session ? selectSessionStep(session) : null;
        setRest(step?.phase === 'rest' ? step.rest : null);
      } catch {
        if (mounted && version === request) setRest(null);
        // Resume cards/screens expose a retry for storage errors.
      }
    };
    void refresh();
    const unsubscribe = repository.subscribe(() => { void refresh(); });
    const appState = AppState.addEventListener('change', state => { if (state === 'active') void refresh(); });
    return () => { mounted = false; unsubscribe(); appState.remove(); };
  }, [repository]);
  return null;
}

export function useSessions(): SessionRepository {
  const repository = useContext(SessionContext);
  if (!repository) throw new Error('useSessions nécessite SessionProvider.');
  return repository;
}
