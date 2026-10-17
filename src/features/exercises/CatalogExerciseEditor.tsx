import { router } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { Text, View } from 'react-native';
import type { CatalogExerciseInput, ExerciseCatalogItem, WeightMode } from '../../domain/training';
import { weightModeLabel } from '../../domain/training';
import { useTraining } from '../../store/TrainingProvider';
import { Button, Card, Field, Heading, Screen } from '../../ui';
import { FormError, LoadState, RefreshNotice, useFocusedData } from '../programs/shared';
import { Choice } from '../sessions/shared';
import { trainingStyles as s, useScreenOperation } from '../training/shared';
import { replacementParams, type ReplacementContext } from '../sessions/useExerciseReplacement';

/** Independent catalog editor: creating a reference never installs a program or
 * inserts it into a workout. Updates retain its stable catalog ID. */
export function CatalogExerciseEditor({ exerciseId, replacementContext }: { exerciseId?: string; replacementContext?: ReplacementContext }) {
  const repository = useTraining(), editing = Boolean(exerciseId);
  const data = useFocusedData(useCallback(() => exerciseId ? repository.getCatalogExercise(exerciseId) : Promise.resolve(null), [repository, exerciseId]));
  const operation = useScreenOperation();
  const [draft, setDraft] = useState<CatalogExerciseInput>({ name: '', muscleGroup: '', equipment: '', instructions: '', weightMode: 'total' });
  useEffect(() => { if (data.data?.isCustom) setDraft({ name: data.data.name, muscleGroup: data.data.muscleGroup, equipment: data.data.equipment, instructions: data.data.instructions, weightMode: data.data.weightMode }); }, [data.data]);
  const change = (key: keyof CatalogExerciseInput, value: string) => setDraft(previous => ({ ...previous, [key]: value }));
  const save = () => {
    if (data.loading || data.error || operation.lock.current || editing && !data.data?.isCustom) return;
    let saved: ExerciseCatalogItem;
    void operation.run(async () => { saved = editing ? await repository.updateCustomExercise(exerciseId!, draft) : await repository.createCustomExercise(draft); }, () => {
      const target = { pathname: '/exercises/[exerciseId]' as const, params: { exerciseId: saved.id, ...(replacementContext ? replacementParams(replacementContext) : {}) } };
      if (editing) router.dismissTo(target); else router.replace(target);
    }, true);
  };
  return <Screen><Heading title={editing ? 'Modifier votre exercice' : 'Votre exercice'} subtitle="Référence personnelle" back backDisabled={operation.busy} />
    <RefreshNotice {...data} />
    {data.loading || data.error || editing && !data.data?.isCustom ? <LoadState loading={data.loading} error={data.error} retry={data.retry} missing="Seuls vos exercices personnalisés peuvent être modifiés." /> : <View style={s.sections}>
      <Text style={s.body}>{editing ? 'Le même exercice sera mis à jour dans vos préparations. Les performances passées gardent leurs noms et modes de charge enregistrés. Si vous changez le mode, vérifiez les charges prévues.' : 'Cette référence restera dans votre bibliothèque, sans créer de programme ni de séance.'}</Text>
      <Card><Field label="Nom de l’exercice" value={draft.name} onChangeText={value => change('name', value)} maxLength={80} />
        <Field label="Groupe musculaire" value={draft.muscleGroup} onChangeText={value => change('muscleGroup', value)} maxLength={80} />
        <Field label="Matériel" value={draft.equipment} onChangeText={value => change('equipment', value)} maxLength={80} />
        <Text style={s.body}>Comment indiquez-vous la charge ?</Text>
        {(['total', 'per_hand', 'additional'] as WeightMode[]).map(mode => <Choice key={mode} label={weightModeLabel[mode]} selected={draft.weightMode === mode} disabled={operation.busy} onPress={() => change('weightMode', mode)} />)}
        <Field label="Consignes (facultatives)" value={draft.instructions ?? ''} onChangeText={value => change('instructions', value)} maxLength={1000} multiline />
      </Card><FormError message={operation.error} />
      <Button label={editing ? 'Enregistrer l’exercice' : 'Créer l’exercice'} icon="checkmark" loading={operation.busy} onPress={save} />
    </View>}
  </Screen>;
}
