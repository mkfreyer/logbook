import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { router } from 'expo-router';
import { useEffect, useState } from 'react';
import { Keyboard, Modal, Pressable, StyleSheet, Text, View } from 'react-native';
import { replacementOrigin, selectSessionStep, type WorkoutSession } from '../../domain/session';
import { Button, Card, colors, Heading, Screen } from '../../ui';
import { FormError, LoadState, messageFor } from '../programs/shared';
import { useScreenOperation } from '../training/shared';
import { RestTimer } from './RestTimer';
import { NumericCard, parseActualDraft, sessionSeriesTitle, sessionStyles, useSessionData } from './shared';
import { SessionSummaryView } from './SessionSummaryView';

const emptyActual = { weight: '', reps: '', rir: '' };

export function SessionScreen({ sessionId }: { sessionId?: string }) {
  const data = useSessionData(sessionId);
  const operation = useScreenOperation();
  const [draft, setDraft] = useState(emptyActual);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [actionsOpen, setActionsOpen] = useState(false);
  const session = data.session;
  const step = session ? selectSessionStep(session) : null;
  const activeSetId = step?.phase === 'set' ? step.set.id : null;
  const activeExerciseId = step?.phase === 'set' ? step.exercise.id : null;
  useEffect(() => { setDraft(emptyActual); setValidationError(null); setActionsOpen(false); }, [activeSetId, activeExerciseId]);
  const leave = () => {
    if (operation.lock.current) return;
    Keyboard.dismiss();
    router.dismissTo({ pathname: '/', params: { universe: 'musculation' } });
  };
  const mutate = (action: () => Promise<WorkoutSession>) => operation.run(async () => data.accept(await action()));
  const validate = () => {
    if (!session || step?.phase !== 'set' || operation.lock.current) return;
    let actual;
    try { actual = parseActualDraft(draft); } catch (error) { setValidationError(messageFor(error)); return; }
    setValidationError(null); Keyboard.dismiss();
    void mutate(() => data.repository.validateSet(session.id, step.set.id, actual));
  };
  const change = (field: keyof typeof draft, value: string) => { setDraft(current => ({ ...current, [field]: value })); setValidationError(null); };
  const restSet = step?.phase === 'rest' ? session?.sets.find(item => item.id === step.performed.sessionSetId) : null;
  const currentExercise = restSet ? session?.exercises.find(item => item.id === restSet.sessionExerciseId)
    : step && 'exercise' in step ? step.exercise : null;
  const exerciseIndex = currentExercise ? (currentExercise.plannedOrder ?? currentExercise.sortOrder) + 1 : null;
  const exerciseCount = session ? new Set(session.exercises.map(item => item.sourceWorkoutExerciseId)).size : 0;
  const progressLabel = session?.exerciseChoices?.length ? 'Position prévue' : 'Exercice';
  const sourceSets = session && currentExercise ? session.sets.filter(item => session.exercises.find(exercise => exercise.id === item.sessionExerciseId)?.sourceWorkoutExerciseId === currentExercise.sourceWorkoutExerciseId) : [];
  const replacedFrom = session && activeExerciseId ? replacementOrigin(session, activeExerciseId) : null;
  const showActions = !data.loading && !data.error && (step?.phase === 'set' || step?.phase === 'rest' || step?.phase === 'between_sets');
  const goAction = (kind: 'edit' | 'replace' | 'exercises') => {
    if (!session) return;
    void operation.run(async () => undefined, () => {
      setActionsOpen(false); Keyboard.dismiss();
      if (kind === 'exercises') router.push({ pathname: '/sessions/[sessionId]/exercises', params: { sessionId: session.id } });
      else if (step?.phase === 'set' && kind === 'edit') router.push({ pathname: '/sessions/[sessionId]/edit', params: { sessionId: session.id, setId: step.set.id } });
      else if (step?.phase === 'set') router.push({ pathname: '/sessions/[sessionId]/replace', params: { sessionId: session.id, exerciseId: step.exercise.id, setId: step.set.id } });
    }, true);
  };
  const title = step?.phase === 'rest' ? 'Repos entre les séries' : step?.phase === 'completed' ? 'Séance terminée' : session?.workoutName ?? 'Entraînement';
  const footer = !data.loading && !data.error && step?.phase === 'set' ? <View style={{ gap: 8 }}>
    <FormError message={validationError ?? operation.error} />
    <Button label="Valider la série" icon="checkmark" loading={operation.busy} onPress={validate} />
  </View> : undefined;
  if (!data.loading && !data.error && session && step?.phase === 'completed') {
    return <SessionSummaryView session={session} onExit={leave} onRetry={data.retry} />;
  }
  return <Screen compact footer={footer}>
    <Heading title={title} subtitle={step?.phase === 'rest' ? currentExercise?.name : exerciseIndex ? `${progressLabel} ${exerciseIndex} sur ${exerciseCount}` : undefined}
      back backDisabled={operation.busy} onBack={leave}
      action={showActions ? <Pressable accessibilityRole="button" accessibilityLabel="Actions de séance" disabled={operation.busy}
        accessibilityState={{ disabled: operation.busy }} style={styles.menu}
        onPress={() => { Keyboard.dismiss(); setActionsOpen(true); }}>
        <Ionicons name="ellipsis-horizontal" size={24} color={colors.cyan} />
      </Pressable> : undefined} />
    <Modal visible={actionsOpen} transparent animationType="fade" onRequestClose={() => setActionsOpen(false)}>
      <View style={styles.modal}>
        <Pressable style={styles.scrim} accessibilityRole="button" accessibilityLabel="Fermer les actions" onPress={() => setActionsOpen(false)} />
        <Card style={{ gap: 8 }}><View accessibilityViewIsModal>
          <Text style={[sessionStyles.subtitle, { marginBottom: 12 }]}>Actions de séance</Text>
          {step?.phase === 'set' && <>
            <Button label="Modifier les objectifs de la série" variant="ghost" icon="create-outline" disabled={operation.busy} onPress={() => goAction('edit')} />
            <Button label="Remplacer cet exercice" variant="ghost" icon="swap-horizontal" disabled={operation.busy} onPress={() => goAction('replace')} />
          </>}
          <Button label="Choisir le prochain exercice" variant="ghost" icon="grid-outline" disabled={operation.busy} onPress={() => goAction('exercises')} />
          <Button label="Fermer" variant="secondary" disabled={operation.busy} onPress={() => setActionsOpen(false)} />
        </View></Card>
      </View>
    </Modal>
    {data.loading || data.error || !session || !step ? <LoadState loading={data.loading} error={data.error} retry={data.retry} missing="Cet entraînement n’est pas disponible." /> : <View style={sessionStyles.sections}>
      {step.phase !== 'completed' && <View style={styles.progressSection}>
        <Text style={sessionStyles.help}>{session.performances.length} / {session.sets.length} séries validées</Text>
        <View style={styles.progressTrack}><View style={[styles.progress, { width: `${session.sets.length ? session.performances.length / session.sets.length * 100 : 0}%` }]} /></View>
      </View>}
      {step.phase === 'set' && <>
        <LinearGradient colors={['#123852', '#0b1b2a']} style={styles.exerciseHero}>
          <View style={styles.heroRow}>
            <View style={styles.exerciseIcon}><Ionicons name="barbell-outline" size={28} color={colors.cyan} /></View>
            <View style={{ flex: 1, gap: 4 }}>
              <Text style={sessionStyles.eyebrow}>{step.exercise.muscleGroup.toLocaleUpperCase('fr-FR')}</Text>
              <Text style={sessionStyles.title}>{step.exercise.name}</Text>
            </View>
          </View>
          <Text style={sessionStyles.body}>{sessionSeriesTitle(step.set)} · {step.set.seriesIndex + 1} / {sourceSets.length}</Text>
          {replacedFrom && <Text style={sessionStyles.help}>En remplacement de {replacedFrom.name} · charge cible à adapter.</Text>}
        </LinearGradient>
        <Card style={styles.targetCard}>
          <Text style={sessionStyles.eyebrow}>OBJECTIFS PROGRAMMÉS</Text>
          <Text style={sessionStyles.body}>{step.set.targets.repsMin === step.set.targets.repsMax ? step.set.targets.repsMin : `${step.set.targets.repsMin}–${step.set.targets.repsMax}`} répétitions · {step.set.targets.targetWeightKg === null ? 'Charge libre' : `${step.set.targets.targetWeightKg.toLocaleString('fr-FR')} kg${step.exercise.weightMode === 'per_hand' ? ' / haltère' : step.exercise.weightMode === 'additional' ? ' ajoutés' : ''}`}{step.set.targets.targetRir === null ? '' : ` · RIR ${step.set.targets.targetRir}`}</Text>
          {step.set.notes ? <Text style={sessionStyles.help}>{replacedFrom ? `Note prévue avant le remplacement : ${step.set.notes}` : step.set.notes}</Text> : null}
        </Card>
        <Text style={sessionStyles.eyebrow}>VOTRE SÉRIE RÉALISÉE</Text>
        <View style={styles.actualRow}>
          <NumericCard caption={step.exercise.weightMode === 'per_hand' ? 'Kg / haltère' : step.exercise.weightMode === 'additional' ? 'Kg ajoutés' : 'Charge (kg)'} label="Charge réelle (kg)" value={draft.weight} onChange={value => change('weight', value)} decimal disabled={operation.busy} />
          <NumericCard caption="Répétitions" label="Répétitions réelles" value={draft.reps} onChange={value => change('reps', value)} disabled={operation.busy} />
          <NumericCard caption="RIR" label="RIR réel" value={draft.rir} onChange={value => change('rir', value)} disabled={operation.busy} />
        </View>
        <Text style={sessionStyles.help}>Charge et RIR facultatifs. RIR : répétitions que vous auriez encore pu faire, de 0 à 10.</Text>
      </>}
      {step.phase === 'rest' && <>
        <FormError message={operation.error} />
        {session.selectedExerciseId && <Text style={sessionStyles.help}>À suivre : {step.exercise.name}. Terminez votre repos manuellement pour continuer.</Text>}
        <RestTimer rest={step.rest} busy={operation.busy}
          onPause={() => { void mutate(() => data.repository.pauseRest(session.id, step.rest.id)); }}
          onResume={() => { void mutate(() => data.repository.resumeRest(session.id, step.rest.id)); }}
          onComplete={() => { void mutate(() => data.repository.completeRest(session.id, step.rest.id)); }} />
      </>}
      {step.phase === 'between_sets' && <>
        <Card>
          <Ionicons name="checkmark-circle-outline" size={42} color="#49ebc4" />
          <Text style={sessionStyles.title}>Série enregistrée</Text>
          <Text style={sessionStyles.body}>À suivre : {step.exercise.name} · {sessionSeriesTitle(step.nextSet)}.</Text>
        </Card>
        <FormError message={operation.error} />
        <Button label="Passer à la série suivante" icon="arrow-forward" loading={operation.busy}
          onPress={() => { void mutate(() => data.repository.advanceAfterSet(session.id, step.performed.id)); }} />
      </>}
      {step.phase === 'ready_to_finish' && <>
        <Card>
          <Ionicons name="checkmark-done-circle-outline" size={48} color="#49ebc4" />
          <Text style={sessionStyles.title}>Toutes les séries sont enregistrées</Text>
          <Text style={sessionStyles.body}>Terminez la séance pour enregistrer son heure de fin.</Text>
        </Card>
        <FormError message={operation.error} />
        <Button label="Terminer la séance" icon="checkmark" loading={operation.busy}
          onPress={() => { void mutate(() => data.repository.finishSession(session.id)); }} />
      </>}
      <Button label="Quitter et reprendre plus tard" variant="ghost" disabled={operation.busy} onPress={leave} />
      <Text style={[sessionStyles.help, sessionStyles.center]}>Les séries validées sont sauvegardées. {step.phase === 'rest' ? 'Le repos continue pendant votre absence, sauf si vous mettez le minuteur en pause.' : 'Les champs non validés ne constituent pas une performance enregistrée.'}</Text>
    </View>}
  </Screen>;
}

const styles = StyleSheet.create({
  modal: { flex: 1, justifyContent: 'flex-end', padding: 24, paddingBottom: 40 },
  scrim: { position: 'absolute', top: 0, bottom: 0, left: 0, right: 0, backgroundColor: '#000a' },
  menu: { width: 44, height: 44, alignItems: 'center', justifyContent: 'center' },
  progressSection: { gap: 8 }, progressTrack: { height: 4, backgroundColor: colors.surfaceRaised, borderRadius: 2, overflow: 'hidden' },
  progress: { height: 4, backgroundColor: colors.blue, borderRadius: 2 },
  exerciseHero: { padding: 16, borderRadius: 24, gap: 12, borderWidth: 1, borderColor: colors.border },
  heroRow: { flexDirection: 'row', gap: 12, alignItems: 'center' },
  exerciseIcon: { width: 48, height: 48, borderRadius: 16, alignItems: 'center', justifyContent: 'center', backgroundColor: '#153e5a' },
  targetCard: { padding: 16, gap: 7 }, actualRow: { flexDirection: 'row', gap: 8 },
});
