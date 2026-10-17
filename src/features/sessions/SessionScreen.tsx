import { useSeriesDisplay } from '../../store/SeriesDisplayProvider';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { router } from 'expo-router';
import { useEffect, useState } from 'react';
import { Keyboard, Modal, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { replacementOrigin, selectSessionStep, sessionProgress, sessionProgressLabel, PASSED_REFERENCE_MESSAGE, type WorkoutSession } from '../../domain/session';
import { Button, Card, colors, Heading, Screen } from '../../ui';
import { FormError, LoadState, messageFor } from '../programs/shared';
import { useScreenOperation } from '../training/shared';
import { RestTimer } from './RestTimer';
import { NumericCard, parseActualDraft, sessionSeriesTitle, sessionStyles, useSessionData } from './shared';
import { SessionSummaryView } from './SessionSummaryView';
import { PassedSets } from './PassedSets';
import { useSkipSet } from './useSkipSet';
import { PreviousPerformanceCard } from './PreviousPerformanceCard';
import { replacementParams } from './useExerciseReplacement';
import { TrainingHelp } from '../exercises/TrainingHelp';

const emptyActual = { weight: '', reps: '', rir: '' };

export function SessionScreen({ sessionId }: { sessionId?: string }) {
  const seriesDisplay = useSeriesDisplay();
  const data = useSessionData(sessionId);
  const operation = useScreenOperation();
  const [draft, setDraft] = useState(emptyActual);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [actionsOpen, setActionsOpen] = useState(false);
  const skipping = useSkipSet({ operation, repository: data.repository, sessionId, onSkipped: data.accept });
  const busy = operation.busy || skipping.confirming;
  const session = data.session;
  const progress = session ? sessionProgress(session) : null;
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
    void mutate(() => data.repository.validateSet(session.id, step.set.id, actual, step.set.passageRevision ?? 0));
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
  const showActions = !data.loading && !data.error && (step?.phase === 'set' || step?.phase === 'rest' || step?.phase === 'between_sets' || step?.phase === 'ready_to_finish');
  const goAction = (kind: 'edit' | 'replace' | 'exercises' | 'add' | 'remaining' | 'notes' | 'guide') => {
    if (!session) return;
    void operation.run(async () => undefined, () => {
      setActionsOpen(false); Keyboard.dismiss();
      if (kind === 'add') router.push({ pathname: '/sessions/[sessionId]/add', params: { sessionId: session.id } });
      else if (kind === 'notes') router.push({ pathname: '/sessions/[sessionId]/notes', params: { sessionId: session.id } });
      else if (kind === 'remaining') router.push({ pathname: '/sessions/[sessionId]/edit', params: { sessionId: session.id } });
      else if (kind === 'exercises') router.push({ pathname: '/sessions/[sessionId]/exercises', params: { sessionId: session.id } });
      else if (step?.phase === 'set' && kind === 'guide') router.push({ pathname: '/exercises/[exerciseId]', params: { exerciseId: step.exercise.sourceCatalogExerciseId,
        ...replacementParams({ sessionId: session.id, exerciseId: step.exercise.id, setId: step.set.id }) } });
      else if (step?.phase === 'set' && kind === 'edit') router.push({ pathname: '/sessions/[sessionId]/edit', params: { sessionId: session.id, setId: step.set.id } });
      else if (step?.phase === 'set') router.push({ pathname: '/sessions/[sessionId]/replace', params: { sessionId: session.id, exerciseId: step.exercise.id, setId: step.set.id } });
    }, true);
  };
  const title = step?.phase === 'rest' ? 'Repos entre les séries' : step?.phase === 'completed' ? 'Séance terminée' : session?.workoutName ?? 'Entraînement';
  const footer = !data.loading && !data.error && step?.phase === 'set' ? <View style={{ gap: 8 }}>
    <FormError message={validationError ?? operation.error} />
    <Button label="Valider la série" icon="checkmark" loading={operation.busy} disabled={busy} onPress={validate} />
    <Button label="Passer cette série" variant="ghost" disabled={busy} onPress={() => { setValidationError(null); skipping.confirm(step.set); }} />
  </View> : undefined;
  if (!data.loading && !data.error && session && step?.phase === 'completed') {
    return <SessionSummaryView session={session} onExit={leave} onRetry={data.retry}
      onNotes={() => router.push({ pathname: '/sessions/[sessionId]/notes', params: { sessionId: session.id } })}
      onExercise={exercise => router.push({ pathname: '/history/exercises/[exerciseId]', params: { exerciseId: exercise.sourceCatalogExerciseId, mode: exercise.weightMode } })} />;
  }
  return <Screen compact footer={footer}>
    <Heading title={title} subtitle={step?.phase === 'rest' ? currentExercise?.name : exerciseIndex ? `${progressLabel} ${exerciseIndex} sur ${exerciseCount}` : undefined}
      back backDisabled={busy} onBack={leave}
      action={showActions ? <Pressable accessibilityRole="button" accessibilityLabel="Actions de séance" disabled={busy}
        accessibilityState={{ disabled: busy }} style={styles.menu}
        onPress={() => { Keyboard.dismiss(); setActionsOpen(true); }}>
        <Ionicons name="ellipsis-horizontal" size={24} color={colors.cyan} />
      </Pressable> : undefined} />
    <Modal visible={actionsOpen} transparent animationType="fade" onRequestClose={() => setActionsOpen(false)}>
      <View style={styles.modal}>
        <Pressable style={styles.scrim} accessibilityRole="button" accessibilityLabel="Fermer les actions" onPress={() => setActionsOpen(false)} />
        <Card style={{ gap: 8, maxHeight: '90%' }}><ScrollView style={{ flexShrink: 1 }} keyboardShouldPersistTaps="handled"><View accessibilityViewIsModal>
          <Text style={[sessionStyles.subtitle, { marginBottom: 12 }]}>Actions de séance</Text>
          {step?.phase === 'set' && <>
            <Button label="Modifier les objectifs de la série" variant="ghost" icon="create-outline" disabled={busy} onPress={() => goAction('edit')} />
            <Button label="Remplacer cet exercice" variant="ghost" icon="swap-horizontal" disabled={busy} onPress={() => goAction('replace')} />
          </>}
          <Button label="Ajouter une série" variant="ghost" icon="add-outline" disabled={busy} onPress={() => goAction('add')} />
          {!!progress?.remaining && <Button label="Modifier une série restante" variant="ghost" icon="create-outline" disabled={busy} onPress={() => goAction('remaining')} />}
          <Button label="Notes personnelles" variant="ghost" icon="document-text-outline" disabled={busy} onPress={() => goAction('notes')} />
          {!!progress?.remaining && <Button label="Choisir le prochain exercice" variant="ghost" icon="grid-outline" disabled={busy} onPress={() => goAction('exercises')} />}
          <Button label="Fermer" variant="secondary" disabled={busy} onPress={() => setActionsOpen(false)} />
        </View></ScrollView></Card>
      </View>
    </Modal>
    {data.loading || data.error || !session || !step ? <LoadState loading={data.loading} error={data.error} retry={data.retry} missing="Cet entraînement n’est pas disponible." /> : <View style={sessionStyles.sections}>
      {step.phase !== 'completed' && <View style={styles.progressSection}>
        <Text style={sessionStyles.help}>{sessionProgressLabel(session)}</Text>
        <View style={styles.progressTrack}><View style={[styles.progress, { width: `${progress && progress.total > progress.skipped ? progress.performed / (progress.total - progress.skipped) * 100 : 0}%` }]} /></View>
      </View>}
      {step.phase === 'set' && <>
        <Pressable accessibilityRole="button" accessibilityLabel={`Voir la fiche de ${step.exercise.name}`}
          accessibilityHint="Description, conseils et alternatives de cet exercice" accessibilityState={{ disabled: busy }} disabled={busy}
          onPress={() => goAction('guide')} style={({ pressed }) => pressed && styles.heroPressed}>
          <LinearGradient colors={['#123852', '#0b1b2a']} style={styles.exerciseHero}>
            <View style={styles.heroRow}>
              <View style={styles.exerciseIcon}><Ionicons name="barbell-outline" size={28} color={colors.cyan} /></View>
              <View style={{ flex: 1, gap: 4 }}>
                <Text style={sessionStyles.eyebrow}>{step.exercise.muscleGroup.toLocaleUpperCase('fr-FR')}</Text>
                <Text style={sessionStyles.title}>{step.exercise.name}</Text>
              </View>
              <Ionicons name="chevron-forward" size={18} color={colors.cyan} accessible={false} />
            </View>
            <Text style={sessionStyles.body}>{sessionSeriesTitle(step.set, seriesDisplay)} · {sourceSets.findIndex(item => item.id === step.set.id) + 1} / {sourceSets.length}</Text>
            {replacedFrom && <Text style={sessionStyles.help}>En remplacement de {replacedFrom.name} · charge cible à adapter.</Text>}
          </LinearGradient>
        </Pressable>
        <Card style={styles.targetCard}>
          <Text style={sessionStyles.eyebrow}>OBJECTIFS DE CETTE SÉRIE</Text>
          <Text style={sessionStyles.body}>{step.set.targets.repsMin === step.set.targets.repsMax ? step.set.targets.repsMin : `${step.set.targets.repsMin}–${step.set.targets.repsMax}`} répétitions · {step.set.targets.targetWeightKg === null ? 'Charge libre' : `${step.set.targets.targetWeightKg.toLocaleString('fr-FR', { maximumSignificantDigits: 21 })} kg${step.exercise.weightMode === 'per_hand' ? ' / haltère' : step.exercise.weightMode === 'additional' ? ' ajoutés' : ''}`}{step.set.targets.targetRir === null ? '' : ` · RIR ${step.set.targets.targetRir}`}</Text>
          {step.set.loadRule && <Text style={sessionStyles.help}>{step.set.loadRule.suspended ? 'Calcul suspendu après remplacement ou retrait : choisissez une cible manuelle ou une référence compatible.' : step.set.loadRule.basis === 'performed_weight'
            ? session.sets.find(item => item.id === step.set.loadRule!.referenceSetId)?.skippedAt ? PASSED_REFERENCE_MESSAGE : !session.performances.some(item => item.sessionSetId === step.set.loadRule!.referenceSetId) ? 'En attente de la série de référence' : step.set.targets.targetWeightKg === null ? 'Charge de référence non renseignée · charge libre' : `${step.set.loadRule.percent} % de la charge réellement validée · cible proposée`
            : `${step.set.loadRule.percent} % de la charge prévue · cible proposée`}</Text>}
          {step.set.notes ? <Text style={sessionStyles.help}>{replacedFrom ? `Note prévue avant le remplacement : ${step.set.notes}` : step.set.notes}</Text> : null}
        </Card>
        <Text style={sessionStyles.eyebrow}>VOTRE SÉRIE RÉALISÉE</Text>
        <View style={styles.actualRow}>
          <NumericCard caption={step.exercise.weightMode === 'per_hand' ? 'Kg / haltère' : step.exercise.weightMode === 'additional' ? 'Kg ajoutés' : 'Charge (kg)'} label="Charge réelle (kg)" value={draft.weight} onChange={value => change('weight', value)} decimal disabled={busy} />
          <NumericCard caption="Répétitions" label="Répétitions réelles" value={draft.reps} onChange={value => change('reps', value)} disabled={busy} />
          <NumericCard caption="RIR" label="RIR réel" value={draft.rir} onChange={value => change('rir', value)} disabled={busy} />
        </View>
        <PreviousPerformanceCard sessionId={session.id} series={step.set} exercise={step.exercise} />
        <Text style={sessionStyles.help}>Charge et RIR facultatifs. RIR : répétitions que vous auriez encore pu faire, de 0 à 10.</Text>
        <TrainingHelp />
      </>}
      {step.phase === 'rest' && <>
        <FormError message={operation.error} />
        {session.selectedExerciseId && step.nextSet && <Text style={sessionStyles.help}>À suivre : {step.exercise.name}. Terminez votre repos manuellement pour continuer.</Text>}
        <RestTimer rest={step.rest} busy={busy} showAction={!!step.nextSet}
          onPause={() => { void mutate(() => data.repository.pauseRest(session.id, step.rest.id)); }}
          onResume={() => { void mutate(() => data.repository.resumeRest(session.id, step.rest.id)); }}
          onComplete={() => { void mutate(() => data.repository.completeRest(session.id, step.rest.id)); }} />
      </>}
      {step.phase === 'rest' && !step.nextSet && <>
        <Text style={sessionStyles.help}>Aucune série restante. Votre repos continue jusqu’à votre fin manuelle.</Text>
        <Button label="Terminer le repos" loading={operation.busy} disabled={busy} onPress={() => { void mutate(() => data.repository.completeRest(session.id, step.rest.id)); }} />
      </>}
      {step.phase === 'between_sets' && <>
        <Card>
          <Ionicons name="checkmark-circle-outline" size={42} color="#49ebc4" />
          <Text style={sessionStyles.title}>Série enregistrée</Text>
          <Text style={sessionStyles.body}>{step.nextSet ? `À suivre : ${step.exercise.name} · ${sessionSeriesTitle(step.nextSet, seriesDisplay)}.` : 'Aucune série restante. Continuez pour accéder à la fin de séance.'}</Text>
        </Card>
        <FormError message={operation.error} />
        <Button label={step.nextSet ? "Passer à la série suivante" : "Continuer"} icon="arrow-forward" loading={operation.busy} disabled={busy}
          onPress={() => { void mutate(() => data.repository.advanceAfterSet(session.id, step.performed.id)); }} />
      </>}
      {step.phase === 'ready_to_finish' && <>
        <Card>
          <Ionicons name="checkmark-done-circle-outline" size={48} color="#49ebc4" />
          <Text style={sessionStyles.title}>{progress?.skipped ? 'Séries réalisées ou passées' : 'Toutes les séries sont enregistrées'}</Text>
          <Text style={sessionStyles.body}>{session.performances.length ? 'Terminez la séance pour enregistrer son heure de fin.' : 'Pour terminer, utilisez « Réintégrer la série » puis enregistrez au moins une performance réelle.'}</Text>
        </Card>
        <FormError message={operation.error} />
        <Button label="Terminer la séance" icon="checkmark" loading={operation.busy} disabled={busy || !session.performances.length}
          onPress={() => { void mutate(() => data.repository.finishSession(session.id)); }} />
      </>}
      <PassedSets session={session} busy={busy} onReintegrate={series => { setValidationError(null); void mutate(() => data.repository.reintegrateSet(session.id, series.id, series.passageRevision ?? 0)); }} />
      <Button label="Quitter et reprendre plus tard" variant="ghost" disabled={busy} onPress={leave} />
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
  heroPressed: { opacity: 0.82 },
  heroRow: { flexDirection: 'row', gap: 12, alignItems: 'center' },
  exerciseIcon: { width: 48, height: 48, borderRadius: 16, alignItems: 'center', justifyContent: 'center', backgroundColor: '#153e5a' },
  targetCard: { padding: 16, gap: 7 }, actualRow: { flexDirection: 'row', gap: 8 },
});
