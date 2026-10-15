import { randomUUID } from 'expo-crypto';
import { useSQLiteContext } from 'expo-sqlite';
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { NotFoundError, ProgramRepository } from '../db/repository';
import type { Program, ProgramInput, WorkoutInput, WorkoutTemplate } from '../domain/models';

interface LogbookContextValue {
  programs: Program[];
  loading: boolean;
  hasLoaded: boolean;
  error: string | null;
  refresh(): Promise<void>;
  getProgram(id: string): Promise<Program | null>;
  listWorkouts(programId: string): Promise<WorkoutTemplate[]>;
  getWorkout(id: string): Promise<WorkoutTemplate | null>;
  createProgram(input: ProgramInput): Promise<Program>;
  updateProgram(id: string, input: ProgramInput): Promise<Program>;
  deleteProgram(id: string): Promise<void>;
  createWorkout(programId: string, input: WorkoutInput): Promise<WorkoutTemplate>;
  updateWorkout(id: string, input: WorkoutInput): Promise<WorkoutTemplate>;
  deleteWorkout(id: string): Promise<void>;
}

const LogbookContext = createContext<LogbookContextValue | null>(null);

export function LogbookProvider({ children }: { children: ReactNode }) {
  const db = useSQLiteContext();
  const repository = useMemo(() => new ProgramRepository(db, randomUUID), [db]);
  const [programs, setPrograms] = useState<Program[]>([]);
  const [loading, setLoading] = useState(true);
  const [hasLoaded, setHasLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const request = useRef(0);

  const refresh = useCallback(async () => {
    const version = ++request.current;
    try {
      const result = await repository.listPrograms();
      if (version === request.current) { setPrograms(result); setHasLoaded(true); setError(null); }
    } catch {
      if (version === request.current) setError('Impossible de lire vos programmes. Réessayez.');
    } finally {
      if (version === request.current) setLoading(false);
    }
  }, [repository]);
  useEffect(() => { void refresh(); return () => { request.current++; }; }, [refresh]);

  const getProgram = useCallback(async (id: string) => {
    try { return await repository.getProgram(id); }
    catch (e) { if (e instanceof NotFoundError) return null; throw e; }
  }, [repository]);
  const getWorkout = useCallback(async (id: string) => {
    try { return await repository.getWorkout(id); }
    catch (e) { if (e instanceof NotFoundError) return null; throw e; }
  }, [repository]);
  const listWorkouts = useCallback((id: string) => repository.listWorkouts(id), [repository]);
  const createProgram = useCallback(async (input: ProgramInput) => {
    const result = await repository.createProgram(input); await refresh(); return result;
  }, [repository, refresh]);
  const updateProgram = useCallback(async (id: string, input: ProgramInput) => {
    const result = await repository.updateProgram(id, input); await refresh(); return result;
  }, [repository, refresh]);
  const createWorkout = useCallback(async (id: string, input: WorkoutInput) => {
    const result = await repository.createWorkout(id, input); await refresh(); return result;
  }, [repository, refresh]);
  const updateWorkout = useCallback(async (id: string, input: WorkoutInput) => {
    const result = await repository.updateWorkout(id, input); await refresh(); return result;
  }, [repository, refresh]);

  const deleteProgram = useCallback(async (id: string) => {
    await repository.deleteProgram(id);
    // Invalidate older reads and remove the deleted card even if the subsequent
    // refresh fails. refresh() exposes read errors on the list for retry.
    request.current++;
    setPrograms(current => current.filter(program => program.id !== id));
    await refresh();
  }, [repository, refresh]);
  const deleteWorkout = useCallback(async (id: string) => {
    await repository.deleteWorkout(id);
    await refresh();
  }, [repository, refresh]);

  const value = useMemo(() => ({ programs, loading, hasLoaded, error, refresh, getProgram, listWorkouts, getWorkout, createProgram, updateProgram, deleteProgram, createWorkout, updateWorkout, deleteWorkout }),
    [programs, loading, hasLoaded, error, refresh, getProgram, listWorkouts, getWorkout, createProgram, updateProgram, deleteProgram, createWorkout, updateWorkout, deleteWorkout]);
  return <LogbookContext.Provider value={value}>{children}</LogbookContext.Provider>;
}

export function useLogbook() {
  const context = useContext(LogbookContext);
  if (!context) throw new Error('useLogbook nécessite LogbookProvider.');
  return context;
}
