import { router } from 'expo-router';
import { remainingSessionSets, selectSessionStep, type WorkoutSession } from '../../domain/session';
import type { ExerciseCatalogItem } from '../../domain/training';
import { weightModeLabel } from '../../domain/training';
import type { SessionRepository } from '../../db/sessionRepository';
import { useScreenOperation } from '../training/shared';
import { useSessionConfirmation } from './useSessionConfirmation';

export interface ReplacementContext { sessionId?: string; exerciseId?: string; setId?: string }

export function replacementStep(session: WorkoutSession | null, context: ReplacementContext) {
  if (!session || session.id !== context.sessionId || session.status !== 'active') return null;
  if (session.replacements?.some(item => item.fromExerciseId === context.exerciseId)) return null;
  const step = selectSessionStep(session);
  return step.phase === 'set' && step.set.id === context.setId && step.exercise.id === context.exerciseId ? step : null;
}

export function replacementParams(context: ReplacementContext) {
  return { replacementSessionId: context.sessionId, replacementExerciseId: context.exerciseId, replacementSetId: context.setId };
}

/** Shared by the existing search and the exercise sheet. Native confirmation
 * precedes the existing atomic repository mutation; neither path edits a plan. */
export function useExerciseReplacement(repository: SessionRepository, context: ReplacementContext) {
  const operation = useScreenOperation(), confirmation = useSessionConfirmation();
  const choose = (item: ExerciseCatalogItem) => {
    if (operation.lock.current || confirmation.confirming) return;
    let fresh: WorkoutSession;
    void operation.run(async () => {
      const value = context.sessionId ? await repository.getSession(context.sessionId) : null;
      const step = replacementStep(value, context);
      if (!step || !value) throw new Error('Ce remplacement n’est plus disponible. Revenez à la séance ; tout repos doit être terminé manuellement.');
      if (step.exercise.sourceCatalogExerciseId === item.id) throw new Error('Cet exercice est déjà celui de la série active.');
      fresh = value;
    }, () => {
      const step = replacementStep(fresh, context)!;
      const count = remainingSessionSets(fresh).filter(set => set.sessionExerciseId === step.exercise.id).length;
      confirmation.confirm('Remplacer cet exercice ?',
        `« ${step.exercise.name} » → « ${item.name} » pour les ${count} série${count > 1 ? 's' : ''} restante${count > 1 ? 's' : ''}.\n\nLes séries déjà validées et les séries passées restent inchangées. Les charges cibles restantes seront effacées et les calculs liés suspendus pour être vérifiés (${weightModeLabel[item.weightMode]}). Répétitions, RIR et repos restent conservés. Votre programme ne change pas.`,
        'Remplacer', () => {
          void operation.run(async () => {
            // Re-read after the alert: the session may have changed meanwhile.
            const latest = await repository.getSession(fresh.id);
            if (!replacementStep(latest, context)) throw new Error('La série active a changé. Revenez à la séance avant de remplacer son exercice.');
            await repository.replaceExercise(fresh.id, step.exercise.id, item.id, step.set.id);
          }, () => router.dismissTo({ pathname: '/sessions/[sessionId]', params: { sessionId: fresh.id } }), true);
        });
    });
  };
  return { ...operation, busy: operation.busy || confirmation.confirming, choose };
}
