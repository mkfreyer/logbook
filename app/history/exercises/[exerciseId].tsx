import { useLocalSearchParams } from 'expo-router';
import { ExerciseHistory } from '../../../src/features/history/ExerciseHistory';
import { routeId } from '../../../src/features/programs/shared';
export default function ExerciseHistoryRoute() {
  const params = useLocalSearchParams<{ exerciseId?: string; mode?: string }>();
  const mode = params.mode === 'total' || params.mode === 'per_hand' || params.mode === 'additional' ? params.mode : undefined;
  return <ExerciseHistory exerciseId={routeId(params.exerciseId)} initialMode={mode} />;
}
