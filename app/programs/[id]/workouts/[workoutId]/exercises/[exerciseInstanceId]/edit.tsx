import { useLocalSearchParams } from 'expo-router';

import { routeId } from '../../../../../../../src/features/programs/shared';
import { PlannedExerciseEditor } from '../../../../../../../src/features/training/PlannedExerciseEditor';

export default function PlannedExerciseEditRoute() {
  const params = useLocalSearchParams<{ id: string; workoutId: string; exerciseInstanceId: string }>();
  return <PlannedExerciseEditor programId={routeId(params.id)} workoutId={routeId(params.workoutId)} exerciseInstanceId={routeId(params.exerciseInstanceId)} />;
}
