import { router } from 'expo-router';
import { Heading, Screen } from '../../ui';
import { LoadState } from '../programs/shared';
import { SessionSummaryView } from '../sessions/SessionSummaryView';
import { useSessionData } from '../sessions/shared';

/** Same summary source and calculations as M2; never mounts execution controls. */
export function SessionHistory({ sessionId }: { sessionId?: string }) {
  const data = useSessionData(sessionId);
  if (data.loading || data.error || !data.session || data.session.status !== 'completed') return <Screen>
    <Heading title="Détail de séance" back /><LoadState loading={data.loading} error={data.error} retry={data.retry}
      missing="Cet entraînement n’est pas terminé ou n’est plus disponible." /></Screen>;
  return <SessionSummaryView session={data.session} historical onRetry={data.retry}
    onNotes={() => router.push({ pathname: '/sessions/[sessionId]/notes', params: { sessionId: data.session!.id } })}
    onExit={() => router.canGoBack() ? router.back() : router.replace('/history')}
    onExercise={exercise => router.push({ pathname: '/history/exercises/[exerciseId]', params: { exerciseId: exercise.sourceCatalogExerciseId, mode: exercise.weightMode } })} />;
}
