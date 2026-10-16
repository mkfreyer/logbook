import { useLocalSearchParams } from 'expo-router';
import { routeId } from '../../../src/features/programs/shared';
import { SessionSetEditor } from '../../../src/features/sessions/SessionSetEditor';
export default function AddSessionSetRoute() {
  const params = useLocalSearchParams<{ sessionId: string }>();
  return <SessionSetEditor sessionId={routeId(params.sessionId)} adding />;
}
