import { randomUUID } from 'expo-crypto';
import { useSQLiteContext } from 'expo-sqlite';
import { createContext, useContext, useMemo, type ReactNode } from 'react';
import { TrainingRepository } from '../db/trainingRepository';

const TrainingContext = createContext<TrainingRepository | null>(null);

/** Shares M0's existing database; screen focus refreshes read the saved targets. */
export function TrainingProvider({ children }: { children: ReactNode }) {
  const db = useSQLiteContext();
  const repository = useMemo(() => new TrainingRepository(db, randomUUID), [db]);
  return <TrainingContext.Provider value={repository}>{children}</TrainingContext.Provider>;
}

export function useTraining(): TrainingRepository {
  const repository = useContext(TrainingContext);
  if (!repository) throw new Error('useTraining nécessite TrainingProvider.');
  return repository;
}
