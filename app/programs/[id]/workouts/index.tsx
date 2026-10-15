import { Ionicons } from '@expo/vector-icons';
import { router, useLocalSearchParams } from 'expo-router';
import { useCallback } from 'react';
import { Pressable, Text, View } from 'react-native';

import { useLogbook } from '../../../../src/store/LogbookProvider';
import { Button, Card, colors, EmptyState, Heading, Screen } from '../../../../src/ui';
import { featureStyles, LoadState, RefreshNotice, LocalNotice, routeId, useFocusedData } from '../../../../src/features/programs/shared';

export default function WorkoutsScreen() {
  const params = useLocalSearchParams<{ id: string; configuredWorkoutId?: string }>();
  const id = routeId(params.id);
  const configuredWorkoutId = routeId(params.configuredWorkoutId);
  const { getProgram, listWorkouts } = useLogbook();
  const load = useCallback(async () => {
    if (!id) return null;
    const program = await getProgram(id);
    if (!program) return null;
    return { program, workouts: await listWorkouts(id) };
  }, [getProgram, id, listWorkouts]);
  const { data, loading, error, refreshError, refreshing, retry } = useFocusedData(load);
  const configuredWorkout = data?.workouts.find(workout => workout.id === configuredWorkoutId);

  return <Screen>
    <Heading title="Vos séances" subtitle={data?.program.name} back />
    <RefreshNotice refreshError={refreshError} refreshing={refreshing} retry={retry} />
    {loading || error || !data ? <LoadState loading={loading} error={error} retry={retry}
      missing="Ce programme n’est pas disponible." /> : <View style={featureStyles.sections}>
        {configuredWorkout ? <Card style={{ gap: 6 }}>
          <Text accessibilityRole="alert" style={featureStyles.title}>Configuration enregistrée</Text>
          <Text style={featureStyles.body}>{configuredWorkout.name} · vos modifications sont sauvegardées.</Text>
        </Card> : null}
        <Text style={featureStyles.body}>Choisissez une séance pour configurer ses exercices et ses séries ou démarrer un entraînement.</Text>
        {data.workouts.length === 0 ? <Card>
          <EmptyState icon="layers-outline" title="Votre programme prend forme"
            description="Ajoutez votre première séance. Vous pourrez lui donner un nom et noter vos consignes." />
        </Card> : <View style={featureStyles.cards}>
          {data.workouts.map((workout, index) => <Card key={workout.id}>
            <Pressable accessibilityRole="button" accessibilityLabel={`Ouvrir la séance ${workout.name}`}
              onPress={() => router.push({ pathname: '/programs/[id]/workouts/[workoutId]', params: { id: data.program.id, workoutId: workout.id } })}
              style={featureStyles.row}>
              <View style={featureStyles.icon}><Ionicons name="fitness-outline" color={colors.cyan} size={25} /></View>
              <View style={featureStyles.grow}>
                <Text style={featureStyles.title}>{workout.name}</Text>
                {workout.notes ? <Text style={featureStyles.body} numberOfLines={2}>{workout.notes}</Text> : null}
                <Text style={featureStyles.meta}>Séance {index + 1} · Exercices et séries</Text>
              </View>
              <Ionicons name="chevron-forward" color={colors.muted} size={19} />
            </Pressable>
          </Card>)}
        </View>}
        <Button label="Ajouter une séance" icon="add"
          onPress={() => router.push({ pathname: '/programs/[id]/workouts/new', params: { id: data.program.id } })} />
        <LocalNotice />
      </View>}
  </Screen>;
}
