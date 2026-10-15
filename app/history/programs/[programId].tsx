import { useLocalSearchParams } from 'expo-router';
import { HistoryOverview } from '../../../src/features/history/HistoryOverview';
import { routeId } from '../../../src/features/programs/shared';
export default function ProgramHistoryRoute() {
  const params = useLocalSearchParams<{ programId?: string; name?: string; period?: string }>();
  const period = params.period === '30' || params.period === '90' || params.period === '365' || params.period === 'all' ? params.period : '30';
  return <HistoryOverview programId={routeId(params.programId)} programName={routeId(params.name)} initialPeriod={period} />;
}
