import { useLocalSearchParams } from 'expo-router';

import { routeId } from '../../../../../src/features/programs/shared';
import { WorkoutOverview } from '../../../../../src/features/training/WorkoutOverview';

export default function WorkoutOverviewRoute() {
  const params = useLocalSearchParams<{ id: string; workoutId: string }>();
  return <WorkoutOverview programId={routeId(params.id)} workoutId={routeId(params.workoutId)} />;
}
