import { useCallback } from 'react';

import { TrainingNotFoundError } from '../../db/trainingRepository';
import type { PlannedExercise } from '../../domain/training';
import { useLogbook } from '../../store/LogbookProvider';
import { useTraining } from '../../store/TrainingProvider';
import { useFocusedData } from '../programs/shared';
import type { TrainingRoute } from './shared';

export function useWorkoutPlan({ programId, workoutId, exerciseInstanceId }: TrainingRoute) {
  const { getProgram, getWorkout } = useLogbook();
  const training = useTraining();
  const load = useCallback(async () => {
    if (!programId || !workoutId) return null;
    const program = await getProgram(programId);
    const workout = await getWorkout(workoutId);
    if (!program || !workout || workout.programId !== programId) return null;
    try {
      const exercises = await training.listWorkoutExercises(workoutId);
      const planned: PlannedExercise[] = await Promise.all(exercises.map(async exercise => ({
        ...exercise, sets: await training.listSets(exercise.id),
      })));
      const exercise = exerciseInstanceId ? planned.find(item => item.id === exerciseInstanceId) : undefined;
      if (exerciseInstanceId && !exercise) return null;
      return { program, workout, exercises: planned, exercise };
    } catch (failure) {
      if (failure instanceof TrainingNotFoundError) return null;
      throw failure;
    }
  }, [exerciseInstanceId, getProgram, getWorkout, programId, training, workoutId]);
  return { ...useFocusedData(load), training };
}
