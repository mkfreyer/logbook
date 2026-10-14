import { useLocalSearchParams } from 'expo-router';

import { routeId } from '../../../../../src/features/programs/shared';
import { CustomExerciseEditor } from '../../../../../src/features/training/CustomExerciseEditor';

export default function CustomExerciseRoute() {
  const params = useLocalSearchParams<{ id: string; workoutId: string; exerciseInstanceId?: string; catalogId?: string }>();
  return <CustomExerciseEditor programId={routeId(params.id)} workoutId={routeId(params.workoutId)} exerciseInstanceId={routeId(params.exerciseInstanceId)} catalogId={routeId(params.catalogId)} />;
}
