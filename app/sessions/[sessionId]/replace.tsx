import { useLocalSearchParams } from 'expo-router';
import { routeId } from '../../../src/features/programs/shared';
import { SessionReplacement } from '../../../src/features/sessions/SessionReplacement';

export default function ReplaceRoute() {
  const params = useLocalSearchParams<{ sessionId: string; exerciseId: string; setId: string }>();
  return <SessionReplacement key={`${routeId(params.sessionId)}:${routeId(params.exerciseId)}:${routeId(params.setId)}`}
    sessionId={routeId(params.sessionId)} exerciseId={routeId(params.exerciseId)} setId={routeId(params.setId)} />;
}
