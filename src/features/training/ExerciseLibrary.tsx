import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useCallback, useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import type { ExerciseCatalogItem } from '../../domain/training';
import { Button, Card, colors, EmptyState, Heading, Screen } from '../../ui';
import { FormError, LoadState, useFocusedData } from '../programs/shared';
import { trainingStyles as s, useScreenOperation, type TrainingRoute } from './shared';
import { useWorkoutPlan } from './useWorkoutPlan';

function searchable(value: string): string { return value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('fr-FR'); }

export function ExerciseLibrary({ programId, workoutId, exerciseInstanceId }: TrainingRoute) {
  const plan = useWorkoutPlan({ programId, workoutId, exerciseInstanceId });
  const load = useCallback(() => plan.training.listCatalog(), [plan.training]);
  const catalog = useFocusedData(load);
  const operation = useScreenOperation();
  const [query, setQuery] = useState('');
  const replacing = Boolean(exerciseInstanceId);
  const terms = searchable(query.trim()).split(/\s+/).filter(Boolean);
  const items = catalog.data?.filter(item => {
    const text = searchable(`${item.name} ${item.muscleGroup} ${item.equipment}`);
    return terms.every(term => text.includes(term));
  }) ?? [];
  const goBack = () => {
    if (router.canGoBack()) router.back();
    else if (programId && workoutId && exerciseInstanceId) router.replace({ pathname: '/programs/[id]/workouts/[workoutId]/exercises/[exerciseInstanceId]', params: { id: programId, workoutId, exerciseInstanceId } });
    else if (programId && workoutId) router.replace({ pathname: '/programs/[id]/workouts/[workoutId]', params: { id: programId, workoutId } });
    else router.replace({ pathname: '/', params: { universe: 'musculation' } });
  };
  const retry = () => { plan.retry(); catalog.retry(); };
  const select = (item: ExerciseCatalogItem) => {
    if (!plan.data) return;
    const data = plan.data;
    void operation.run(async () => {
      if (data.exercise) await plan.training.updateWorkoutExercise(data.exercise.id, { exerciseId: item.id, notes: data.exercise.notes });
      else await plan.training.addWorkoutExercise(data.workout.id, { exerciseId: item.id });
    }, () => {
      if (data.exercise) router.dismissTo({ pathname: '/programs/[id]/workouts/[workoutId]/exercises/[exerciseInstanceId]', params: { id: data.program.id, workoutId: data.workout.id, exerciseInstanceId: data.exercise.id } });
      else router.dismissTo({ pathname: '/programs/[id]/workouts/[workoutId]', params: { id: data.program.id, workoutId: data.workout.id } });
    }, true);
  };
  return <Screen>
    <Heading title="Bibliothèque d’exercices" subtitle={replacing ? 'Choisir un autre exercice prévu' : plan.data?.workout.name} back backDisabled={operation.busy} onBack={goBack} />
    {plan.loading || catalog.loading || plan.error || catalog.error || !plan.data || !catalog.data ? <LoadState
      loading={plan.loading || catalog.loading} error={plan.error ?? catalog.error} retry={retry} missing="Cette séance n’est plus disponible." /> : <View style={s.sections}>
      <View style={styles.search}>
        <Ionicons name="search-outline" color={colors.muted} size={22} />
        <TextInput accessibilityLabel="Rechercher un exercice" placeholder="Rechercher un exercice…" placeholderTextColor={colors.muted}
          value={query} onChangeText={setQuery} editable={!operation.busy} autoCapitalize="none" autoCorrect={false}
          selectionColor={colors.cyan} style={styles.searchInput} returnKeyType="search" />
      </View>
      <Text style={s.hint}>{replacing
        ? 'Les séries et les charges prévues seront conservées. Vérifiez-les après un changement de matériel ou de mode de charge.'
        : 'Touchez un exercice pour l’ajouter à votre séance. Vos programmes restent entièrement personnalisés.'}</Text>
      <FormError message={operation.error} />
      {items.length === 0 ? <Card><EmptyState icon="search-outline" title="Aucun exercice trouvé"
        description="Essayez un autre nom, un muscle ou un matériel. Vous pouvez aussi créer votre exercice." /></Card> : <View style={s.cards}>
        {items.map(item => <Pressable key={item.id} accessibilityRole="button" accessibilityLabel={`${replacing ? 'Choisir' : 'Ajouter'} ${item.name}`}
          disabled={operation.busy} accessibilityState={{ disabled: operation.busy }} onPress={() => select(item)}
          style={({ pressed }) => [styles.exercise, pressed && s.pressed, operation.busy && s.disabled]}>
          <View style={s.icon}><Ionicons name="barbell-outline" size={26} color={colors.cyan} /></View>
          <View style={s.grow}><Text style={s.title}>{item.name}</Text><Text style={s.body}>{item.muscleGroup} · {item.equipment}</Text>
            {item.isCustom ? <Text style={s.meta}>Exercice personnalisé</Text> : null}</View>
          <Ionicons name={replacing ? 'chevron-forward' : 'add-circle-outline'} size={22} color={colors.cyan} />
        </Pressable>)}
      </View>}
      <Button label="Créer un exercice personnalisé" variant="secondary" icon="create-outline" disabled={operation.busy}
        onPress={() => router.push({ pathname: '/programs/[id]/workouts/[workoutId]/custom-exercise', params: { id: plan.data!.program.id, workoutId: plan.data!.workout.id, ...(exerciseInstanceId ? { exerciseInstanceId } : {}) } })} />
    </View>}
  </Screen>;
}

const styles = StyleSheet.create({
  search: { flexDirection: 'row', alignItems: 'center', gap: 10, backgroundColor: colors.surface, borderColor: colors.border, borderWidth: 1, borderRadius: 16, paddingHorizontal: 16, minHeight: 56 },
  searchInput: { color: colors.text, fontSize: 16, minHeight: 54, flex: 1, minWidth: 0, paddingVertical: 13 },
  exercise: { flexDirection: 'row', alignItems: 'center', gap: 12, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border, borderRadius: 18, padding: 14, minHeight: 86 },
});
