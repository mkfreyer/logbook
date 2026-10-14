import { useLocalSearchParams } from 'expo-router';

import { routeId } from '../../../../src/features/programs/shared';
import { WorkoutEditor } from '../../../../src/features/programs/WorkoutEditor';

export default function NewWorkoutScreen() {
  const params = useLocalSearchParams<{ id: string }>();
  return <WorkoutEditor mode="create" programId={routeId(params.id)} />;
}
