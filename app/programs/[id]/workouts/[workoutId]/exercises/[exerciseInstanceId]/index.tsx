import { useLocalSearchParams } from 'expo-router';

import { routeId } from '../../../../../../../src/features/programs/shared';
import { ExerciseOverview } from '../../../../../../../src/features/training/ExerciseOverview';

export default function ExerciseOverviewRoute() {
  const params = useLocalSearchParams<{ id: string; workoutId: string; exerciseInstanceId: string }>();
  return <ExerciseOverview programId={routeId(params.id)} workoutId={routeId(params.workoutId)} exerciseInstanceId={routeId(params.exerciseInstanceId)} />;
}
