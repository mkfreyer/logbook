import { useLocalSearchParams } from 'expo-router';
import { routeId } from '../../../src/features/programs/shared';
import { RemainingExercises } from '../../../src/features/sessions/RemainingExercises';

export default function RemainingRoute() {
  const params = useLocalSearchParams<{ sessionId: string }>();
  return <RemainingExercises sessionId={routeId(params.sessionId)} />;
}
