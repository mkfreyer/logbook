import { router, useFocusEffect } from 'expo-router';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Text, View } from 'react-native';

import { useLogbook } from '../../store/LogbookProvider';
import { Button, Card, Field, Heading, Screen } from '../../ui';
import { featureStyles, FormError, LoadState, LocalNotice, messageFor, useFocusedData } from './shared';

export function WorkoutEditor({ mode, programId, workoutId }: {
  mode: 'create' | 'edit'; programId?: string; workoutId?: string;
}) {
  const editing = mode === 'edit';
  const { getProgram, getWorkout, createWorkout, updateWorkout } = useLogbook();
  const load = useCallback(async () => {
    if (!programId || (editing && !workoutId)) return null;
    const program = await getProgram(programId);
    if (!program) return null;
    const workout = editing && workoutId ? await getWorkout(workoutId) : null;
    if (editing && (!workout || workout.programId !== programId)) return null;
    return { program, workout };
  }, [editing, getProgram, getWorkout, programId, workoutId]);
  const { data, loading, error, retry } = useFocusedData(load);
  const [name, setName] = useState('');
  const [notes, setNotes] = useState('');
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const savingRef = useRef(false);
  const mounted = useRef(true);
  const focused = useRef(false);

  useFocusEffect(useCallback(() => {
    focused.current = true;
    return () => { focused.current = false; };
  }, []));

  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; };
  }, []);
  useEffect(() => {
    if (data?.workout) { setName(data.workout.name); setNotes(data.workout.notes ?? ''); }
  }, [data]);

  const returnToWorkouts = () => {
    if (router.canGoBack()) router.back();
    else if (programId) router.replace({ pathname: '/programs/[id]/workouts', params: { id: programId } });
    else router.replace({ pathname: '/', params: { universe: 'musculation' } });
  };
  const save = async () => {
    if (savingRef.current || !programId) return;
    if (!name.trim()) { setFormError('Donnez un nom à votre séance.'); return; }
    if (name.trim().length > 80 || notes.trim().length > 1000) {
      setFormError('Le nom est limité à 80 caractères et les notes à 1 000 caractères.'); return;
    }
    if (editing && !workoutId) return;
    savingRef.current = true;
    setSaving(true);
    setFormError(null);
    try {
      const input = { name: name.trim(), notes: notes.trim() };
      if (editing && workoutId) await updateWorkout(workoutId, input);
      else await createWorkout(programId, input);
      if (mounted.current && focused.current) returnToWorkouts();
    } catch (failure: unknown) {
      if (mounted.current && focused.current) setFormError(messageFor(failure));
    } finally {
      savingRef.current = false;
      if (mounted.current) setSaving(false);
    }
  };

  return <Screen>
    <Heading title={editing ? 'Modifier la séance' : 'Ajouter une séance'} subtitle={data?.program.name} back backDisabled={saving} />
    {loading || error || !data ? <LoadState loading={loading} error={error} retry={retry}
      missing="Cette séance ou son programme n’est pas disponible." /> : <View style={featureStyles.sections}>
      <Text style={featureStyles.body}>{editing
        ? 'Retrouvez vos repères et adaptez vos consignes.'
        : 'Donnez un nom à votre séance et ajoutez vos consignes si vous le souhaitez.'}</Text>
      <Card>
        <View style={featureStyles.sections}>
          <Field label="Nom de la séance" value={name} onChangeText={(value) => { setName(value); setFormError(null); }}
            placeholder="Ex. Séance du lundi" maxLength={80} />
          <Field label="Notes (facultatives)" value={notes} onChangeText={setNotes}
            placeholder="Vos consignes pour cette séance" multiline maxLength={1000} />
        </View>
      </Card>
      <FormError message={formError} />
      <Button label={editing ? 'Enregistrer les modifications' : 'Ajouter la séance'} onPress={() => { void save(); }}
        icon="checkmark" loading={saving} disabled={saving} />
      <Button label="Annuler" variant="ghost" onPress={returnToWorkouts} disabled={saving} />
      <Text style={featureStyles.body}>Vous pourrez ajouter les exercices dans la prochaine version.</Text>
      <LocalNotice />
    </View>}
  </Screen>;
}
