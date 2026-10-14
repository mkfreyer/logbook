import { useLocalSearchParams } from 'expo-router';
import { routeId } from '../../../src/features/programs/shared';
import { SessionScreen } from '../../../src/features/sessions/SessionScreen';

export default function SessionRoute() {
  const params = useLocalSearchParams<{ sessionId: string }>();
  return <SessionScreen sessionId={routeId(params.sessionId)} />;
}
