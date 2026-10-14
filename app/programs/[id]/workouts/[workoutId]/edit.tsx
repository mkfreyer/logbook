import { useLocalSearchParams } from 'expo-router';

import { routeId } from '../../../../../src/features/programs/shared';
import { WorkoutEditor } from '../../../../../src/features/programs/WorkoutEditor';

export default function EditWorkoutScreen() {
  const params = useLocalSearchParams<{ id: string; workoutId: string }>();
  return <WorkoutEditor mode="edit" programId={routeId(params.id)} workoutId={routeId(params.workoutId)} />;
}
