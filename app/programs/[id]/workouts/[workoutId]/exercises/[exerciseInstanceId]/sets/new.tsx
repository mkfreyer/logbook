import { useLocalSearchParams } from 'expo-router';

import { routeId } from '../../../../../../../../src/features/programs/shared';
import { SetEditor } from '../../../../../../../../src/features/training/SetEditor';

export default function NewSetRoute() {
  const params = useLocalSearchParams<{ id: string; workoutId: string; exerciseInstanceId: string }>();
  return <SetEditor mode="create" programId={routeId(params.id)} workoutId={routeId(params.workoutId)} exerciseInstanceId={routeId(params.exerciseInstanceId)} />;
}
