import { useLocalSearchParams } from 'expo-router';

import { routeId } from '../../../../../src/features/programs/shared';
import { ExerciseLibrary } from '../../../../../src/features/training/ExerciseLibrary';

export default function ExerciseLibraryRoute() {
  const params = useLocalSearchParams<{ id: string; workoutId: string; exerciseInstanceId?: string }>();
  return <ExerciseLibrary programId={routeId(params.id)} workoutId={routeId(params.workoutId)} exerciseInstanceId={routeId(params.exerciseInstanceId)} />;
}
