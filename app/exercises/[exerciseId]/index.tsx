import { useLocalSearchParams } from 'expo-router';
import { ExerciseDetail } from '../../../src/features/exercises/ExerciseDetail';
import { routeId } from '../../../src/features/programs/shared';
export default function ExerciseDetailRoute() {
  return <ExerciseDetail exerciseId={routeId(useLocalSearchParams<{ exerciseId?: string }>().exerciseId)} />;
}
