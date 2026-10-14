import { Ionicons } from '@expo/vector-icons';
import { router, useLocalSearchParams } from 'expo-router';
import { useCallback } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { useLogbook } from '../../../../src/store/LogbookProvider';
import { Button, Card, colors, EmptyState, Heading, Screen } from '../../../../src/ui';
import { featureStyles, LoadState, LocalNotice, routeId, useFocusedData } from '../../../../src/features/programs/shared';

export default function WorkoutsScreen() {
  const params = useLocalSearchParams<{ id: string }>();
  const id = routeId(params.id);
  const { getProgram, listWorkouts } = useLogbook();
  const load = useCallback(async () => {
    if (!id) return null;
    const program = await getProgram(id);
    if (!program) return null;
    return { program, workouts: await listWorkouts(id) };
  }, [getProgram, id, listWorkouts]);
  const { data, loading, error, retry } = useFocusedData(load);

  return <Screen>
    <Heading title="Vos séances" subtitle={data?.program.name} back />
    {loading || error || !data ? <LoadState loading={loading} error={error} retry={retry}
      missing="Ce programme n’est pas disponible." /> : <View style={featureStyles.sections}>
        <Text style={featureStyles.body}>Choisissez une séance pour la modifier.</Text>
        {data.workouts.length === 0 ? <Card>
          <EmptyState icon="layers-outline" title="Votre programme prend forme"
            description="Ajoutez votre première séance. Vous pourrez lui donner un nom et noter vos consignes." />
        </Card> : <View style={featureStyles.cards}>
          {data.workouts.map((workout, index) => <Card key={workout.id}>
            <Pressable accessibilityRole="button" accessibilityLabel={`Modifier la séance ${workout.name}`}
              onPress={() => router.push({ pathname: '/programs/[id]/workouts/[workoutId]/edit', params: { id: data.program.id, workoutId: workout.id } })}
              style={featureStyles.row}>
              <View style={featureStyles.icon}><Ionicons name="fitness-outline" color={colors.cyan} size={25} /></View>
              <View style={featureStyles.grow}>
                <Text style={featureStyles.title}>{workout.name}</Text>
                {workout.notes ? <Text style={featureStyles.body} numberOfLines={2}>{workout.notes}</Text> : null}
                <Text style={featureStyles.meta}>Séance {index + 1} · Modifier</Text>
              </View>
              <Ionicons name="chevron-forward" color={colors.muted} size={19} />
            </Pressable>
          </Card>)}
        </View>}
        <Button label="Ajouter une séance" icon="add"
          onPress={() => router.push({ pathname: '/programs/[id]/workouts/new', params: { id: data.program.id } })} />
        <View style={styles.future}>
          <Ionicons name="information-circle-outline" size={19} color={colors.muted} />
          <Text style={styles.futureText}>L’ajout d’exercices et le suivi pendant l’entraînement arriveront dans la prochaine version.</Text>
        </View>
        <LocalNotice />
      </View>}
  </Screen>;
}

const styles = StyleSheet.create({
  future: { flexDirection: 'row', gap: 9, alignItems: 'flex-start', paddingHorizontal: 3 },
  futureText: { color: colors.muted, fontSize: 13, lineHeight: 20, flex: 1 },
});
