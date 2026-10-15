import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useCallback } from 'react';
import { Text, View } from 'react-native';
import { weightModeLabel } from '../../domain/training';
import { useTraining } from '../../store/TrainingProvider';
import { Button, Card, colors, Heading, Screen } from '../../ui';
import { LoadState, RefreshNotice, useFocusedData } from '../programs/shared';
import { trainingStyles as s } from '../training/shared';

export function ExerciseDetail({ exerciseId }: { exerciseId?: string }) {
  const repository = useTraining();
  const data = useFocusedData(useCallback(() => exerciseId ? repository.getCatalogExercise(exerciseId) : Promise.resolve(null), [repository, exerciseId]));
  const exercise = data.data;
  return <Screen compact><Heading title={exercise?.name ?? 'Fiche d’exercice'} subtitle={exercise?.isCustom ? 'Votre exercice personnalisé' : 'Catalogue Logbook'} back />
    <RefreshNotice {...data} />
    {data.loading || data.error || !exercise ? <LoadState loading={data.loading} error={data.error} retry={data.retry} /> : <View style={s.sections}>
      <Card><View style={s.row}><Ionicons name="barbell-outline" size={36} color={colors.cyan} /><View style={s.grow}>
        <Text style={s.title}>{exercise.muscleGroup}</Text><Text style={s.body}>{exercise.equipment}</Text></View></View>
        <Text style={s.meta}>{weightModeLabel[exercise.weightMode]}</Text>
        <Text style={s.body}>La charge reste facultative pendant l’entraînement. Vos performances conservent le mode utilisé lors de leur enregistrement.</Text>
      </Card>
      <Card><Text style={s.eyebrow}>INSTRUCTIONS</Text><Text style={s.body}>{exercise.instructions || 'Aucune instruction renseignée pour cet exercice.'}</Text></Card>
      <Button label="Voir mes performances" icon="stats-chart-outline" onPress={() => router.push({ pathname: '/history/exercises/[exerciseId]', params: { exerciseId: exercise.id } })} />
      {exercise.isCustom && <Button label="Modifier mon exercice personnalisé" variant="secondary" icon="create-outline"
        onPress={() => router.push({ pathname: '/exercises/[exerciseId]/edit', params: { exerciseId: exercise.id } })} />}
    </View>}
  </Screen>;
}
