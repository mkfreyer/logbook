import { useLocalSearchParams } from 'expo-router';
import { routeId } from '../../../src/features/programs/shared';
import { SessionNotes } from '../../../src/features/sessions/SessionNotes';
export default function SessionNotesRoute() {
  const params = useLocalSearchParams<{ sessionId: string }>();
  return <SessionNotes sessionId={routeId(params.sessionId)} />;
}
