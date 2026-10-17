import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { remainingSessionExercises, selectSessionStep } from '../../domain/session';
import { Button, Card, colors, Heading, Screen } from '../../ui';
import { FormError, LoadState } from '../programs/shared';
import { useScreenOperation } from '../training/shared';
import { sessionStyles as s, useSessionData } from './shared';
import { useSessionConfirmation } from './useSessionConfirmation';

export function RemainingExercises({ sessionId }: { sessionId?: string }) {
  const data = useSessionData(sessionId), operation = useScreenOperation(), confirmation = useSessionConfirmation();
  const session = data.session, step = session ? selectSessionStep(session) : null;
  const expectedSet = step?.phase === 'set' ? step.set : step?.phase === 'rest' || step?.phase === 'between_sets' ? step.nextSet : null;
  const entries = session ? remainingSessionExercises(session) : [];
  const busy = operation.busy || confirmation.confirming;
  const back = () => { if (!busy && sessionId) router.dismissTo({ pathname: '/sessions/[sessionId]', params: { sessionId } }); };
  const choose = (exerciseId: string, name: string) => {
    if (!session || !expectedSet || operation.lock.current) return;
    const apply = () => {
      void operation.run(() => data.repository.chooseNextExercise(session.id, exerciseId, expectedSet.id),
        () => router.dismissTo({ pathname: '/sessions/[sessionId]', params: { sessionId: session.id } }), true);
    };
    if (step?.phase === 'rest') confirmation.confirm('Repos encore en cours',
      `« ${name} » sera votre prochain exercice. Le repos continue et ne sera pas effacé. Terminez-le manuellement avant de commencer cet exercice.`, 'Choisir', apply);
    else apply();
  };
  return <Screen compact>
    <Heading title="Choisir un exercice" subtitle="Exercices restant à effectuer" back backDisabled={busy} onBack={back} />
    {data.loading || data.error || !session ? <LoadState loading={data.loading} error={data.error} retry={data.retry} missing="Cet entraînement n’est pas disponible." /> : <View style={s.sections}>
      <Text style={s.body}>Votre choix concerne seulement cet entraînement. Tous les exercices non terminés restent disponibles.</Text>
      {step?.phase === 'rest' && <Card style={{ gap: 6 }}><Text style={s.subtitle}>Votre repos continue</Text><Text style={s.help}>Choisir un exercice ne termine pas le chronomètre. Vous validerez la fin du repos à votre retour.</Text></Card>}
      <FormError message={operation.error} />
      {operation.error && <Button label="Actualiser les exercices" variant="secondary" disabled={busy} onPress={() => { operation.setError(null); data.retry(); }} />}
      {entries.length ? <View style={styles.grid}>{entries.map(({ exercise, sets }) => {
        const hasPerformed = session.performances.some(performance => session.sets.find(series => series.id === performance.sessionSetId)?.sessionExerciseId === exercise.id);
        const current = expectedSet?.sessionExerciseId === exercise.id;
        return <Pressable key={exercise.id} accessibilityRole="button" accessibilityLabel={`Choisir ${exercise.name}`}
          disabled={busy} accessibilityState={{ disabled: busy }} onPress={() => choose(exercise.id, exercise.name)}
          style={({ pressed }) => [styles.item, current && styles.current, pressed && { opacity: 0.7 }]}>
          <View style={styles.icon}><Ionicons name="barbell-outline" size={34} color={colors.cyan} /></View>
          <Text style={s.subtitle}>{exercise.name}</Text>
          <Text style={s.help}>{sets.length} série{sets.length > 1 ? 's' : ''} restante{sets.length > 1 ? 's' : ''}</Text>
          <Text style={[s.help, { color: colors.cyan }]}>{current || hasPerformed ? 'En cours' : 'À effectuer'}</Text>
        </Pressable>;
      })}</View> : <Card><Text style={s.subtitle}>Aucune série restante</Text><Text style={s.body}>Revenez à la séance pour la terminer ou consulter son bilan.</Text></Card>}
      <Button label={step?.phase === 'rest' ? 'Retour au repos' : 'Retour à la séance'} variant="ghost" disabled={busy} onPress={back} />
    </View>}
  </Screen>;
}

const styles = StyleSheet.create({
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12 },
  item: { width: '47%', flexGrow: 1, padding: 16, borderRadius: 20, gap: 8, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.surface },
  current: { borderColor: colors.blue, backgroundColor: '#0c2b43' },
  icon: { height: 64, alignItems: 'center', justifyContent: 'center', borderRadius: 15, backgroundColor: '#123852', marginBottom: 4 },
});
