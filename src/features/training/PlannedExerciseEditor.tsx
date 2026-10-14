import { router } from 'expo-router';
import { useEffect, useState } from 'react';
import { Text, View } from 'react-native';

import { Button, Card, Field, Heading, Screen } from '../../ui';
import { FormError, LoadState } from '../programs/shared';
import { trainingStyles as s, useScreenOperation, type TrainingRoute } from './shared';
import { useWorkoutPlan } from './useWorkoutPlan';

export function PlannedExerciseEditor({ programId, workoutId, exerciseInstanceId }: TrainingRoute) {
  const { data, loading, error, retry, training } = useWorkoutPlan({ programId, workoutId, exerciseInstanceId });
  const exercise = data?.exercise;
  const operation = useScreenOperation();
  const [notes, setNotes] = useState('');
  useEffect(() => { if (exercise) setNotes(exercise.notes); }, [exercise]);
  const goBack = () => {
    if (router.canGoBack()) router.back();
    else if (programId && workoutId && exerciseInstanceId) router.replace({ pathname: '/programs/[id]/workouts/[workoutId]/exercises/[exerciseInstanceId]', params: { id: programId, workoutId, exerciseInstanceId } });
    else router.replace({ pathname: '/', params: { universe: 'musculation' } });
  };
  const save = () => {
    if (!exercise) return;
    void operation.run(() => training.updateWorkoutExercise(exercise.id, { exerciseId: exercise.exerciseId, notes: notes.trim() }), goBack, true);
  };
  return <Screen>
    <Heading title="Modifier l’exercice prévu" subtitle={exercise?.exercise.name} back backDisabled={operation.busy} onBack={goBack} />
    {loading || error || !data || !exercise ? <LoadState loading={loading} error={error} retry={retry} missing="Cet exercice prévu n’est plus disponible." /> : <View style={s.sections}>
      <Card><Text style={s.title}>{exercise.exercise.name}</Text><Text style={s.body}>{exercise.exercise.muscleGroup} · {exercise.exercise.equipment}</Text>
        <Field label="Consignes pour cette séance (facultatives)" value={notes} onChangeText={setNotes} multiline maxLength={1000} placeholder="Vos repères pour cet exercice dans cette séance" />
      </Card>
      <FormError message={operation.error} />
      <Button label="Enregistrer les consignes" icon="checkmark" disabled={operation.busy} loading={operation.busy} onPress={save} />
      <Button label="Choisir un autre exercice" icon="swap-horizontal-outline" variant="secondary" disabled={operation.busy}
        onPress={() => router.push({ pathname: '/programs/[id]/workouts/[workoutId]/library', params: { id: data.program.id, workoutId: data.workout.id, exerciseInstanceId: exercise.id } })} />
      <Text style={s.hint}>Changer l’exercice conserve cette position et ses séries prévues. Vous pourrez ajuster chaque cible après le changement.</Text>
      <Button label="Annuler" variant="ghost" disabled={operation.busy} onPress={goBack} />
    </View>}
  </Screen>;
}
