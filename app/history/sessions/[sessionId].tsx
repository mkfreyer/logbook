import { useLocalSearchParams } from 'expo-router';
import { SessionHistory } from '../../../src/features/history/SessionHistory';
import { routeId } from '../../../src/features/programs/shared';
export default function SessionHistoryRoute() {
  return <SessionHistory sessionId={routeId(useLocalSearchParams<{ sessionId?: string }>().sessionId)} />;
}
