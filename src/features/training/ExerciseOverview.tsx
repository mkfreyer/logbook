import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { Pressable, Text, View } from 'react-native';

import { weightModeLabel } from '../../domain/training';
import { Button, Card, colors, EmptyState, Heading, Screen } from '../../ui';
import { FormError, LoadState, LocalNotice } from '../programs/shared';
import { useConfirmedDelete } from '../programs/useConfirmedDelete';
import { OrderControls, seriesTitle, SetTargetSummary, swappedIds, trainingStyles as s, useScreenOperation, type TrainingRoute } from './shared';
import { useWorkoutPlan } from './useWorkoutPlan';

export function ExerciseOverview({ programId, workoutId, exerciseInstanceId }: TrainingRoute) {
  const { data, loading, error, retry, training } = useWorkoutPlan({ programId, workoutId, exerciseInstanceId });
  const operation = useScreenOperation();
  const exercise = data?.exercise;
  const deletion = useConfirmedDelete({
    title: 'Supprimer cet exercice ?',
    message: `« ${exercise?.exercise.name ?? ''} » et ses séries prévues seront retirés de cette séance. L’exercice restera dans la bibliothèque.`,
    remove: async () => { if (exercise) await training.deleteWorkoutExercise(exercise.id); },
    onDeleted: () => router.dismissTo({ pathname: '/programs/[id]/workouts/[workoutId]', params: { id: programId!, workoutId: workoutId! } }),
    failureMessage: 'Impossible de supprimer cet exercice. Réessayez.', operationLock: operation.lock,
  });
  const busy = operation.busy || deletion.busy;
  const finish = () => {
    if (!data || !exercise || operation.lock.current || operation.error || deletion.error) return;
    operation.lock.current = true;
    router.dismissTo({ pathname: '/programs/[id]/workouts/[workoutId]', params: { id: data.program.id, workoutId: data.workout.id } });
  };
  const goBack = () => {
    if (router.canGoBack()) router.back();
    else if (programId && workoutId) router.replace({ pathname: '/programs/[id]/workouts/[workoutId]', params: { id: programId, workoutId } });
    else router.replace({ pathname: '/', params: { universe: 'musculation' } });
  };
  const move = (index: number, delta: -1 | 1) => {
    if (!exercise) return;
    void operation.run(() => training.reorderSets(exercise.id, swappedIds(exercise.sets, index, delta)), retry);
  };
  return <Screen>
    <Heading title={exercise?.exercise.name ?? 'Exercice prévu'} subtitle={data?.workout.name} back backDisabled={busy} onBack={goBack} />
    {loading || error || !exercise || !data ? <LoadState loading={loading} error={error} retry={retry} missing="Cet exercice prévu n’est plus disponible." /> : <View style={s.sections}>
      <Card style={{ padding: 16, gap: 10 }}>
        <View style={s.row}><View style={s.icon}><Ionicons name="barbell-outline" color={colors.cyan} size={27} /></View>
          <View style={s.grow}><Text style={s.title}>{exercise.exercise.muscleGroup}</Text><Text style={s.body}>{exercise.exercise.equipment}</Text><Text style={s.meta}>{weightModeLabel[exercise.exercise.weightMode]}</Text></View>
        </View>
        {exercise.notes ? <Text style={s.body}>{exercise.notes}</Text> : null}
        {exercise.exercise.instructions ? <Text style={s.body}>{exercise.exercise.instructions}</Text> : null}
        <Button label="Fiche de l’exercice" variant="ghost" icon="information-circle-outline" disabled={busy}
          onPress={() => router.push({ pathname: '/exercises/[exerciseId]', params: { exerciseId: exercise.exercise.id } })} />
      </Card>
      <Text style={s.eyebrow}>SÉRIES PRÉVUES</Text>
      {exercise.sets.length === 0 ? <Card><EmptyState icon="layers-outline" title="Votre première série"
        description="Définissez les répétitions, la charge et le RIR facultatifs, puis le repos propre à cette série." /></Card> : <View style={s.cards}>
        {exercise.sets.map((series, index) => <Card key={series.id} style={{ padding: 16, gap: 12 }}>
          <Pressable accessibilityRole="button" accessibilityLabel={`Modifier ${seriesTitle(series, index)}`} disabled={busy}
            onPress={() => router.push({ pathname: '/programs/[id]/workouts/[workoutId]/exercises/[exerciseInstanceId]/sets/[setId]/edit', params: { id: data.program.id, workoutId: data.workout.id, exerciseInstanceId: exercise.id, setId: series.id } })}
            style={s.row}>
            <SetTargetSummary series={series} index={index} mode={exercise.exercise.weightMode} />
            <Ionicons name="chevron-forward" color={colors.muted} size={18} />
          </Pressable>
          <OrderControls label={`${seriesTitle(series, index)} (position ${index + 1})`} first={index === 0} last={index === exercise.sets.length - 1} disabled={busy}
            onUp={() => move(index, -1)} onDown={() => move(index, 1)} />
        </Card>)}
      </View>}
      <FormError message={operation.error} /><FormError message={deletion.error} />
      <Button label="Terminer" icon="checkmark" disabled={busy || !!operation.error || !!deletion.error} onPress={finish} />
      <Button label="Ajouter une série" variant="secondary" icon="add" disabled={busy}
        onPress={() => router.push({ pathname: '/programs/[id]/workouts/[workoutId]/exercises/[exerciseInstanceId]/sets/new', params: { id: data.program.id, workoutId: data.workout.id, exerciseInstanceId: exercise.id } })} />
      <Button label="Modifier l’exercice prévu" variant="secondary" icon="create-outline" disabled={busy}
        onPress={() => router.push({ pathname: '/programs/[id]/workouts/[workoutId]/exercises/[exerciseInstanceId]/edit', params: { id: data.program.id, workoutId: data.workout.id, exerciseInstanceId: exercise.id } })} />
      {exercise.exercise.isCustom ? <Button label="Modifier mon exercice personnalisé" variant="ghost" icon="create-outline" disabled={busy}
        onPress={() => router.push({ pathname: '/programs/[id]/workouts/[workoutId]/custom-exercise', params: { id: data.program.id, workoutId: data.workout.id, exerciseInstanceId: exercise.id, catalogId: exercise.exercise.id } })} /> : null}
      <Button label="Supprimer cet exercice de la séance" variant="danger" icon="trash-outline" disabled={busy} loading={deletion.deleting} onPress={deletion.confirm} />
      <Text style={s.hint}>Chaque série garde son propre repos. Un repos de 0 seconde indique qu’aucun repos n’est prévu après cette série.</Text>
      <LocalNotice />
    </View>}
  </Screen>;
}
