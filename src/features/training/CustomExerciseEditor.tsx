import { router } from 'expo-router';
import { useEffect, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { weightModeLabel, type WeightMode } from '../../domain/training';
import { Button, Card, colors, Field, Heading, Screen } from '../../ui';
import { FormError, LoadState, LocalNotice } from '../programs/shared';
import { trainingStyles as s, useScreenOperation, type TrainingRoute } from './shared';
import { useWorkoutPlan } from './useWorkoutPlan';

const modes: WeightMode[] = ['total', 'per_hand', 'additional'];

export function CustomExerciseEditor({ programId, workoutId, exerciseInstanceId, catalogId }: TrainingRoute & { catalogId?: string }) {
  const { data, loading, error, retry, training } = useWorkoutPlan({ programId, workoutId, exerciseInstanceId });
  const editing = Boolean(catalogId);
  const customExercise = data?.exercise?.exercise;
  const validEdit = !editing || Boolean(customExercise?.isCustom && customExercise.id === catalogId);
  const operation = useScreenOperation();
  const [name, setName] = useState(''); const [muscleGroup, setMuscleGroup] = useState('');
  const [equipment, setEquipment] = useState(''); const [instructions, setInstructions] = useState('');
  const [weightMode, setWeightMode] = useState<WeightMode>('total');
  useEffect(() => {
    if (editing && customExercise?.isCustom && customExercise.id === catalogId) {
      setName(customExercise.name); setMuscleGroup(customExercise.muscleGroup); setEquipment(customExercise.equipment);
      setInstructions(customExercise.instructions); setWeightMode(customExercise.weightMode);
    }
  }, [catalogId, customExercise, editing]);
  const goBack = () => {
    if (router.canGoBack()) router.back();
    else if (editing && programId && workoutId && exerciseInstanceId) router.replace({ pathname: '/programs/[id]/workouts/[workoutId]/exercises/[exerciseInstanceId]', params: { id: programId, workoutId, exerciseInstanceId } });
    else if (programId && workoutId) router.replace({ pathname: '/programs/[id]/workouts/[workoutId]/library', params: { id: programId, workoutId, ...(exerciseInstanceId ? { exerciseInstanceId } : {}) } });
    else router.replace({ pathname: '/', params: { universe: 'musculation' } });
  };
  const save = () => {
    if (!data || !validEdit || operation.lock.current) return;
    if (!name.trim() || !muscleGroup.trim() || !equipment.trim()) {
      operation.setError('Renseignez le nom, le groupe musculaire et le matériel.'); return;
    }
    const input = { name: name.trim(), muscleGroup: muscleGroup.trim(), equipment: equipment.trim(), instructions: instructions.trim(), weightMode };
    void operation.run(() => editing && catalogId ? training.updateCustomExercise(catalogId, input) : training.createCustomExercise(input), goBack, true);
  };
  return <Screen>
    <Heading title={editing ? 'Modifier votre exercice' : 'Votre exercice'} subtitle={editing ? 'Votre référence personnalisée' : 'Ajouter à votre bibliothèque'} back backDisabled={operation.busy} onBack={goBack} />
    {loading || error || !data || !validEdit ? <LoadState loading={loading} error={error} retry={retry} missing="Cet exercice ou cette séance n’est plus disponible." /> : <View style={s.sections}>
      <Text style={s.body}>{editing ? 'Le même exercice sera mis à jour dans la bibliothèque et dans les séances qui l’utilisent. Son identifiant et ses séries seront conservés ; vérifiez les charges prévues si vous changez leur mode.' : 'Créez votre référence personnelle. Retrouvez-la ensuite dans la bibliothèque pour l’ajouter à une séance.'}</Text>
      <Card>
        <Field label="Nom de l’exercice" value={name} onChangeText={setName} maxLength={80} placeholder="Ex. Rowing unilatéral" />
        <Field label="Groupe musculaire" value={muscleGroup} onChangeText={setMuscleGroup} maxLength={80} placeholder="Ex. Dos" />
        <Field label="Matériel" value={equipment} onChangeText={setEquipment} maxLength={80} placeholder="Ex. Haltère" />
        <Text style={styles.label}>Comment indiquez-vous la charge ?</Text>
        <View accessibilityRole="radiogroup" style={styles.modes}>{modes.map(mode => <Pressable key={mode} accessibilityRole="radio"
          accessibilityLabel={weightModeLabel[mode]} accessibilityState={{ checked: weightMode === mode, disabled: operation.busy }}
          disabled={operation.busy} onPress={() => setWeightMode(mode)} style={[styles.mode, weightMode === mode && styles.selected]}>
          <View style={[styles.radio, weightMode === mode && styles.radioSelected]} /><Text style={styles.modeText}>{weightModeLabel[mode]}</Text>
        </Pressable>)}</View>
        <Field label="Consignes (facultatives)" value={instructions} onChangeText={setInstructions} maxLength={1000} multiline placeholder="Vos repères pour cet exercice" />
      </Card>
      <FormError message={operation.error} />
      <Button label={editing ? 'Enregistrer l’exercice' : 'Créer l’exercice'} icon="checkmark" disabled={operation.busy} loading={operation.busy} onPress={save} />
      <Button label="Annuler" variant="ghost" disabled={operation.busy} onPress={goBack} />
      <LocalNotice />
    </View>}
  </Screen>;
}

const styles = StyleSheet.create({
  label: { color: colors.text, fontSize: 15, fontWeight: '500' }, modes: { gap: 8 },
  mode: { minHeight: 48, paddingHorizontal: 12, paddingVertical: 10, borderRadius: 12, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.surfaceRaised, flexDirection: 'row', alignItems: 'center', gap: 10 },
  selected: { borderColor: colors.blue, backgroundColor: '#102e4a' },
  modeText: { color: colors.text, fontSize: 14, flex: 1 },
  radio: { width: 18, height: 18, borderRadius: 9, borderWidth: 2, borderColor: colors.muted }, radioSelected: { borderColor: colors.blue, backgroundColor: colors.blue },
});
