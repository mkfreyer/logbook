import { useLocalSearchParams } from 'expo-router';

import { routeId } from '../../../../../../../../../src/features/programs/shared';
import { SetEditor } from '../../../../../../../../../src/features/training/SetEditor';

export default function SetEditRoute() {
  const params = useLocalSearchParams<{ id: string; workoutId: string; exerciseInstanceId: string; setId: string }>();
  return <SetEditor mode="edit" programId={routeId(params.id)} workoutId={routeId(params.workoutId)} exerciseInstanceId={routeId(params.exerciseInstanceId)} setId={routeId(params.setId)} />;
}
