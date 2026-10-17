import { useLocalSearchParams } from 'expo-router';
import { CatalogExerciseEditor } from '../../../src/features/exercises/CatalogExerciseEditor';
import { routeId } from '../../../src/features/programs/shared';
export default function CatalogExerciseEditRoute() {
  const params = useLocalSearchParams<{ exerciseId?: string; replacementSessionId?: string; replacementExerciseId?: string; replacementSetId?: string }>();
  const context = { sessionId: routeId(params.replacementSessionId), exerciseId: routeId(params.replacementExerciseId), setId: routeId(params.replacementSetId) };
  return <CatalogExerciseEditor exerciseId={routeId(params.exerciseId)} replacementContext={context.sessionId || context.exerciseId || context.setId ? context : undefined} />;
}
