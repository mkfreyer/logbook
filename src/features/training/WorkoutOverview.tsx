import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { Pressable, Text, View } from 'react-native';

import { Button, Card, colors, EmptyState, Heading, Screen } from '../../ui';
import { FormError, LoadState, LocalNotice } from '../programs/shared';
import { OrderControls, SetTargetSummary, swappedIds, trainingStyles as s, useScreenOperation, type TrainingRoute } from './shared';
import { useWorkoutPlan } from './useWorkoutPlan';

export function WorkoutOverview({ programId, workoutId }: TrainingRoute) {
  const { data, loading, error, retry, training } = useWorkoutPlan({ programId, workoutId });
  const operation = useScreenOperation();
  const goBack = () => {
    if (router.canGoBack()) router.back();
    else if (programId) router.replace({ pathname: '/programs/[id]/workouts', params: { id: programId } });
    else router.replace({ pathname: '/', params: { universe: 'musculation' } });
  };
  const move = (index: number, delta: -1 | 1) => {
    if (!data) return;
    void operation.run(() => training.reorderWorkoutExercises(data.workout.id, swappedIds(data.exercises, index, delta)), retry);
  };
  return <Screen>
    <Heading title={data?.workout.name ?? 'Votre séance'} subtitle={data?.program.name} back backDisabled={operation.busy} onBack={goBack} />
    {loading || error || !data ? <LoadState loading={loading} error={error} retry={retry} missing="Cette séance n’est plus disponible." /> : <View style={s.sections}>
      {data.workout.notes ? <Text style={s.body}>{data.workout.notes}</Text> : null}
      <Text style={s.eyebrow}>EXERCICES PRÉVUS</Text>
      {data.exercises.length === 0 ? <Card><EmptyState icon="barbell-outline" title="Composez votre séance"
        description="Choisissez votre premier exercice dans la bibliothèque, puis configurez ses séries." /></Card> : <View style={s.cards}>
        {data.exercises.map((exercise, index) => <Card key={exercise.id} style={{ padding: 16, gap: 12 }}>
          <Pressable accessibilityRole="button" accessibilityLabel={`Configurer ${exercise.exercise.name}`} disabled={operation.busy}
            onPress={() => router.push({ pathname: '/programs/[id]/workouts/[workoutId]/exercises/[exerciseInstanceId]', params: { id: data.program.id, workoutId: data.workout.id, exerciseInstanceId: exercise.id } })}
            style={s.row}>
            <View style={s.icon}><Ionicons name="barbell-outline" color={colors.cyan} size={27} /></View>
            <View style={s.grow}><Text style={s.title}>{index + 1}. {exercise.exercise.name}</Text>
              <Text style={s.body}>{exercise.exercise.muscleGroup} · {exercise.exercise.equipment}</Text>
              <Text style={s.meta}>{exercise.sets.length === 0 ? 'Séries à configurer' : `${exercise.sets.length} série${exercise.sets.length > 1 ? 's' : ''} prévue${exercise.sets.length > 1 ? 's' : ''}`}</Text>
            </View>
            <Ionicons name="chevron-forward" size={19} color={colors.muted} />
          </Pressable>
          {exercise.sets.length > 0 ? <View style={s.sets}>{exercise.sets.map((series, seriesIndex) => <SetTargetSummary key={series.id} compact series={series} mode={exercise.exercise.weightMode} index={seriesIndex} />)}</View> : null}
          <OrderControls label={exercise.exercise.name} first={index === 0} last={index === data.exercises.length - 1} disabled={operation.busy}
            onUp={() => move(index, -1)} onDown={() => move(index, 1)} />
        </Card>)}
      </View>}
      <FormError message={operation.error} />
      <Button label="Ajouter un exercice" icon="add" disabled={operation.busy}
        onPress={() => router.push({ pathname: '/programs/[id]/workouts/[workoutId]/library', params: { id: data.program.id, workoutId: data.workout.id } })} />
      <Button label="Modifier la séance" variant="ghost" icon="create-outline" disabled={operation.busy}
        onPress={() => router.push({ pathname: '/programs/[id]/workouts/[workoutId]/edit', params: { id: data.program.id, workoutId: data.workout.id } })} />
      <Text style={s.hint}>Ces valeurs sont des objectifs programmés. Les performances réalisées seront enregistrées lors d’une prochaine version.</Text>
      <LocalNotice />
    </View>}
  </Screen>;
}
