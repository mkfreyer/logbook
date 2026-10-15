import { router, useFocusEffect } from 'expo-router';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { TrainingNotFoundError } from '../../db/trainingRepository';
import { parseSetDraft, type SetDraft } from '../../domain/setDraft';
import { setKindLabel, weightModeLabel } from '../../domain/training';
import { useLogbook } from '../../store/LogbookProvider';
import { useTraining } from '../../store/TrainingProvider';
import { Button, Card, colors, Field, Heading, Screen } from '../../ui';
import { featureStyles, FormError, LoadState, RefreshNotice, messageFor, useFocusedData } from '../programs/shared';
import { useConfirmedDelete } from '../programs/useConfirmedDelete';

const initialDraft: SetDraft = { label: '', kind: 'work', repetitionMode: 'exact', repsMin: '8', repsMax: '12', weight: '', rir: '', rest: '90', notes: '' };

export function SetEditor({ mode, programId, workoutId, exerciseInstanceId, setId }: {
  mode: 'create' | 'edit'; programId?: string; workoutId?: string; exerciseInstanceId?: string; setId?: string;
}) {
  const editing = mode === 'edit';
  const training = useTraining();
  const { getProgram, getWorkout } = useLogbook();
  const load = useCallback(async () => {
    if (!programId || !workoutId || !exerciseInstanceId || (editing && !setId)) return null;
    try {
      const program = await getProgram(programId), workout = await getWorkout(workoutId);
      if (!program || !workout || workout.programId !== programId) return null;
      const occurrence = await training.getWorkoutExercise(exerciseInstanceId);
      if (occurrence.workoutTemplateId !== workoutId) return null;
      const set = editing && setId ? await training.getSet(setId) : null;
      if (set && set.workoutExerciseId !== exerciseInstanceId) return null;
      const sets = await training.listSets(exerciseInstanceId);
      const index = set ? sets.findIndex(item => item.id === set.id) : sets.length;
      if (index < 0) return null;
      return { program, workout, occurrence, set, number: index + 1 };
    } catch (failure) {
      if (failure instanceof TrainingNotFoundError) return null;
      throw failure;
    }
  }, [editing, exerciseInstanceId, getProgram, getWorkout, programId, setId, training, workoutId]);
  const { data, loading, error, refreshError, refreshing, retry } = useFocusedData(load);
  const [draft, setDraft] = useState<SetDraft>(initialDraft);
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const lock = useRef(false), mounted = useRef(true), focused = useRef(false);
  const returnToExercise = () => {
    if (programId && workoutId && exerciseInstanceId) router.dismissTo({
      pathname: '/programs/[id]/workouts/[workoutId]/exercises/[exerciseInstanceId]',
      params: { id: programId, workoutId, exerciseInstanceId },
    });
  };
  const deletion = useConfirmedDelete({
    title: 'Supprimer la série ?',
    message: `La série « ${data?.set?.label || `Série ${data?.number ?? ''}`} » et ses cibles seront supprimées. Les autres séries seront conservées.`,
    remove: async () => { if (!data?.set) throw new Error('Série indisponible.'); await training.deleteSet(data.set.id); },
    onDeleted: returnToExercise,
    failureMessage: 'Impossible de supprimer cette série. Réessayez.', operationLock: lock,
  });
  const busy = saving || deletion.busy;
  useFocusEffect(useCallback(() => { focused.current = true; return () => { focused.current = false; }; }, []));
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  useEffect(() => {
    if (!data?.set) return;
    const set = data.set;
    setDraft({ label: set.label, kind: set.kind, repetitionMode: set.repsMin === set.repsMax ? 'exact' : 'range',
      repsMin: String(set.repsMin), repsMax: String(set.repsMax), weight: set.targetWeightKg === null ? '' : String(set.targetWeightKg),
      rir: set.targetRir === null ? '' : String(set.targetRir), rest: String(set.restAfterSec), notes: set.notes });
  }, [data]);
  const change = <K extends keyof SetDraft>(key: K, value: SetDraft[K]) => { setDraft(current => ({ ...current, [key]: value })); setFormError(null); };
  const save = async () => {
    if (lock.current || !data) return;
    let input;
    try { input = parseSetDraft(draft); } catch (failure) { setFormError(messageFor(failure)); return; }
    lock.current = true; setSaving(true); setFormError(null);
    let leaving = false;
    try {
      if (data.set) await training.updateSet(data.set.id, input);
      else await training.createSet(data.occurrence.id, input);
      if (mounted.current && focused.current) { returnToExercise(); leaving = true; }
    } catch (failure) { if (mounted.current && focused.current) setFormError(messageFor(failure)); }
    finally {
      // Navigation is queued. Keep this removed form locked until it leaves so
      // another already queued tap cannot append the same preparation twice.
      if (!leaving) { lock.current = false; if (mounted.current) setSaving(false); }
    }
  };

  return <Screen>
    <Heading title={editing ? 'Modifier la série' : 'Ajouter une série'} subtitle={data?.occurrence.exercise.name} back backDisabled={busy} onBack={returnToExercise} />
    <RefreshNotice refreshError={refreshError} refreshing={refreshing} retry={retry} />
    {loading || error || !data ? <LoadState loading={loading} error={error} retry={retry} missing="Cette série ou son exercice n’est pas disponible." /> : <View style={featureStyles.sections}>
      <Text style={featureStyles.eyebrow}>SÉRIE PRÉVUE {data.number}</Text>
      <Text style={featureStyles.body}>Préparez les cibles de cette série. Vous pourrez renseigner vos résultats pendant l’entraînement dans la prochaine étape.</Text>
      <Field label="Étiquette (facultative)" value={draft.label} onChangeText={value => change('label', value)} placeholder="Ex. Ma série principale" maxLength={80} />
      <View style={styles.choices} accessibilityRole="radiogroup" accessibilityLabel="Type de série">
        {(Object.keys(setKindLabel) as (keyof typeof setKindLabel)[]).map(kind => <Choice key={kind} label={setKindLabel[kind]} selected={draft.kind === kind} disabled={busy} onPress={() => change('kind', kind)} />)}
      </View>
      <Text style={styles.help}>Échauffement : préparation. Top set : série principale. Back-off : série suivante avec une charge choisie par vous.</Text>
      <View style={styles.choices} accessibilityRole="radiogroup" accessibilityLabel="Cible de répétitions">
        <Choice label="Nombre exact" selected={draft.repetitionMode === 'exact'} disabled={busy} onPress={() => change('repetitionMode', 'exact')} />
        <Choice label="Plage min / max" selected={draft.repetitionMode === 'range'} disabled={busy} onPress={() => change('repetitionMode', 'range')} />
      </View>
      <View style={styles.grid}>
        <NumberBox label={`${weightModeLabel[data.occurrence.exercise.weightMode]} · facultative`} value={draft.weight} onChange={value => change('weight', value)} decimal disabled={busy} placeholder="Facultative" />
        <Card style={styles.numberCard}>
          <Text style={styles.label}>Répétitions cibles</Text>
          {draft.repetitionMode === 'range' ? <View style={styles.range}>
            <Numeric label="Répétitions minimum" value={draft.repsMin} onChange={value => change('repsMin', value)} disabled={busy} placeholder="Min" />
            <Text style={styles.rangeDash}>–</Text>
            <Numeric label="Répétitions maximum" value={draft.repsMax} onChange={value => change('repsMax', value)} disabled={busy} placeholder="Max" />
          </View> : <Numeric label="Répétitions cibles" value={draft.repsMin} onChange={value => change('repsMin', value)} disabled={busy} />}
        </Card>
        <NumberBox label="RIR cible (facultatif)" value={draft.rir} onChange={value => change('rir', value)} disabled={busy} placeholder="Facultatif" />
        <NumberBox label="Repos après cette série (s)" value={draft.rest} onChange={value => change('rest', value)} disabled={busy} />
      </View>
      <Text style={styles.help}>RIR : répétitions que vous estimez encore pouvoir faire, de 0 à 10. Laissez vide si vous ne souhaitez pas définir de cible.</Text>
      <Text style={styles.help}>Le repos appartient uniquement à l’intervalle après cette série. 0 signifie aucun repos. La valeur de la dernière série est conservée pour la préparation ; aucun chronomètre n’est lancé.</Text>
      <Field label="Notes de la série (facultatives)" value={draft.notes} onChangeText={value => change('notes', value)} maxLength={1000} multiline placeholder="Vos consignes" />
      <FormError message={formError ?? deletion.error} />
      <Button label={editing ? 'Enregistrer les modifications' : 'Ajouter la série'} icon="checkmark" loading={saving} disabled={busy} onPress={() => { void save(); }} />
      <Button label="Annuler" variant="ghost" disabled={busy} onPress={returnToExercise} />
      {editing && <Button label="Supprimer la série" variant="danger" icon="trash-outline" disabled={busy} loading={deletion.deleting} onPress={deletion.confirm} />}
    </View>}
  </Screen>;
}

function Choice({ label, selected, disabled, onPress }: { label: string; selected: boolean; disabled: boolean; onPress(): void }) {
  return <Pressable accessibilityRole="radio" accessibilityLabel={label} accessibilityState={{ checked: selected, disabled }} disabled={disabled} onPress={onPress}
    style={[styles.choice, selected && styles.selected]}><Text style={styles.choiceText}>{label}</Text></Pressable>;
}
function Numeric({ label, value, onChange, decimal = false, disabled, placeholder = '' }: {
  label: string; value: string; onChange(value: string): void; decimal?: boolean; disabled: boolean; placeholder?: string;
}) {
  return <TextInput accessibilityLabel={label} value={value} onChangeText={onChange} keyboardType={decimal ? 'decimal-pad' : 'number-pad'}
    editable={!disabled} selectionColor={colors.cyan} placeholder={placeholder} placeholderTextColor={colors.muted} style={styles.input} maxLength={16} />;
}
function NumberBox(props: Parameters<typeof Numeric>[0]) {
  return <Card style={styles.numberCard}><Text style={styles.label}>{props.label}</Text><Numeric {...props} /></Card>;
}
const styles = StyleSheet.create({
  choices: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  choice: { paddingHorizontal: 13, paddingVertical: 12, minHeight: 44, borderRadius: 12, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.surface },
  selected: { borderColor: colors.blue, backgroundColor: '#10365a' }, choiceText: { color: colors.text, fontSize: 13, fontWeight: '500' },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12 }, numberCard: { width: '47%', flexGrow: 1, padding: 13, gap: 12, minHeight: 105 },
  label: { color: colors.muted, fontSize: 12, lineHeight: 18 }, input: { flexGrow: 1, minWidth: 0, color: colors.text, fontSize: 21, minHeight: 44, paddingVertical: 5 },
  range: { flexDirection: 'row', alignItems: 'center', gap: 4 }, rangeDash: { color: colors.muted }, help: { color: colors.muted, fontSize: 12, lineHeight: 19 },
});
