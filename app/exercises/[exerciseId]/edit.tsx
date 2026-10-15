import { useLocalSearchParams } from 'expo-router';
import { CatalogExerciseEditor } from '../../../src/features/exercises/CatalogExerciseEditor';
import { routeId } from '../../../src/features/programs/shared';
export default function CatalogExerciseEditRoute() {
  return <CatalogExerciseEditor exerciseId={routeId(useLocalSearchParams<{ exerciseId?: string }>().exerciseId)} />;
}
