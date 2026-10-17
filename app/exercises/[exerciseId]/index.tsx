import { useLocalSearchParams } from 'expo-router';
import { ExerciseDetail } from '../../../src/features/exercises/ExerciseDetail';
import { routeId } from '../../../src/features/programs/shared';
export default function ExerciseDetailRoute() {
  const params = useLocalSearchParams<{ exerciseId?: string; tab?: string; replacementSessionId?: string; replacementExerciseId?: string; replacementSetId?: string }>();
  const context = { sessionId: routeId(params.replacementSessionId), exerciseId: routeId(params.replacementExerciseId), setId: routeId(params.replacementSetId) };
  return <ExerciseDetail exerciseId={routeId(params.exerciseId)} initialTab={params.tab === 'alternatives' ? 'alternatives' : 'description'}
    replacementContext={context.sessionId || context.exerciseId || context.setId ? context : undefined} />;
}
