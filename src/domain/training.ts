/** Catalog identity is independent of its uses in planned workouts. */
export type WeightMode = 'total' | 'per_hand' | 'additional';
export interface ExerciseCatalogItem {
  id: string; name: string; muscleGroup: string; equipment: string;
  instructions: string; weightMode: WeightMode; isCustom: boolean;
  createdAt: string; updatedAt: string;
}
export interface CatalogExerciseInput {
  name: string; muscleGroup: string; equipment: string; instructions?: string; weightMode: WeightMode;
}
/** One planned occurrence; the same catalog exercise can occur more than once. */
export interface WorkoutExercise {
  id: string; workoutTemplateId: string; exerciseId: string; sortOrder: number;
  notes: string; createdAt: string; updatedAt: string;
  exercise: ExerciseCatalogItem;
}
export interface WorkoutExerciseInput { exerciseId: string; notes?: string }
export type SetKind = 'work' | 'warmup' | 'top_set' | 'back_off' | 'custom';
/** Targets only. M1.2 will snapshot these in independent performed-session models. */
export interface SetTemplate {
  id: string; workoutExerciseId: string; sortOrder: number; label: string; kind: SetKind;
  repsMin: number; repsMax: number; targetWeightKg: number | null; targetRir: number | null;
  restAfterSec: number; notes: string; createdAt: string; updatedAt: string;
}
export interface SetTemplateInput {
  label?: string; kind: SetKind; repsMin: number; repsMax: number;
  targetWeightKg?: number | null; targetRir?: number | null; restAfterSec: number; notes?: string;
}
export interface PlannedExercise extends WorkoutExercise { sets: SetTemplate[] }

export const weightModeLabel: Record<WeightMode, string> = {
  total: 'Charge totale (kg)', per_hand: 'Charge par haltère (kg)', additional: 'Charge ajoutée (kg)',
};
export const setKindLabel: Record<SetKind, string> = {
  work: 'Travail', warmup: 'Échauffement', top_set: 'Top set', back_off: 'Back-off', custom: 'Personnalisée',
};
