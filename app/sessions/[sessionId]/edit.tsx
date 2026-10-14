import { useLocalSearchParams } from 'expo-router';
import { routeId } from '../../../src/features/programs/shared';
import { SessionSetEditor } from '../../../src/features/sessions/SessionSetEditor';

export default function SessionSetEditorRoute() {
  const params = useLocalSearchParams<{ sessionId: string; setId: string }>();
  return <SessionSetEditor sessionId={routeId(params.sessionId)} setId={routeId(params.setId)} />;
}
