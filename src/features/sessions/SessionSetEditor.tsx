import { randomUUID } from 'expo-crypto';
import { router } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { Keyboard, Text, View } from 'react-native';
import type { ChangeScope } from '../../domain/session';
import { selectSessionStep, remainingSessionSets, PASSED_REFERENCE_MESSAGE } from '../../domain/session';
import { parseSetDraft, type SetDraft } from '../../domain/setDraft';
import { parseLoadPercentage, percentageWeight } from '../../domain/series';
import { setKindLabel, weightModeLabel, type SetTemplateInput } from '../../domain/training';
import { useSeriesDisplay } from '../../store/SeriesDisplayProvider';
import { Button, Card, Field, Heading, Screen } from '../../ui';
import { FormError, LoadState, messageFor } from '../programs/shared';
import { useConfirmedDelete } from '../programs/useConfirmedDelete';
import { LoadRuleFields } from '../training/LoadRuleFields';
import { useScreenOperation } from '../training/shared';
import { useSkipSet } from './useSkipSet';
import { Choice, NumericInput, sessionSeriesTitle, sessionStyles as s, useSessionData } from './shared';

const emptyDraft: SetDraft = { label: '', kind: 'work', notes: '', repetitionMode: 'exact', repsMin: '8', repsMax: '12', weight: '', rir: '', rest: '90' };

export function SessionSetEditor({ sessionId, setId, adding = false }: { sessionId?: string; setId?: string; adding?: boolean }) {
  const data = useSessionData(sessionId), operation = useScreenOperation(), display = useSeriesDisplay();
  const [pickingSet, setPickingSet] = useState(!setId);
  const [selectedId, setSelectedId] = useState(setId ?? ''), [exerciseId, setExerciseId] = useState('');
  const [draft, setDraft] = useState(emptyDraft), [scope, setScope] = useState<ChangeScope>('session');
  const [mode, setMode] = useState<'manual' | 'percentage' | 'performed'>('manual');
  const [advanced, setAdvanced] = useState(false), [referenceId, setReferenceId] = useState(''), [percent, setPercent] = useState('');
  const [validation, setValidation] = useState<string | null>(null), [programAvailable, setProgramAvailable] = useState(false);
  const [programError, setProgramError] = useState<string | null>(null);
  const token = useRef<string | null>(null), hydrated = useRef('');
  const session = data.session;
  const remaining = session ? remainingSessionSets(session) : [];
  const series = !adding ? session?.sets.find(item => item.id === (selectedId || remaining[0]?.id)) : undefined;
  const editable = session?.id === sessionId && session?.status === 'active' && (adding || !!series && remaining.some(item => item.id === series.id));
  const exercise = session?.exercises.find(item => item.id === (adding ? exerciseId : series?.sessionExerciseId));
  const exercises = session?.exercises.filter(item => !session.replacements?.some(replacement => replacement.fromExerciseId === item.id)) ?? [];
  useEffect(() => {
    if (!session || !adding || exerciseId) return;
    const step = selectSessionStep(session);
    const currentId = 'exercise' in step ? step.exercise.id : session.sets.find(item => item.id === session.performances.at(-1)?.sessionSetId)?.sessionExerciseId;
    setExerciseId(currentId ?? exercises[0]?.id ?? '');
  }, [session, adding, exerciseId]);
  useEffect(() => {
    if (!series || hydrated.current === series.id) return;
    hydrated.current = series.id;
    const t = series.targets;
    setSelectedId(series.id);
    setDraft({ label: series.label, kind: series.kind, notes: series.notes, repetitionMode: t.repsMin === t.repsMax ? 'exact' : 'range',
      repsMin: String(t.repsMin), repsMax: String(t.repsMax), weight: t.targetWeightKg === null ? '' : String(t.targetWeightKg),
      rir: t.targetRir === null ? '' : String(t.targetRir), rest: String(t.restAfterSec) });
    const rule = series.loadRule;
    setMode(rule ? rule.basis === 'performed_weight' ? 'performed' : 'percentage' : 'manual');
    setReferenceId(rule?.referenceSetId ?? ''); setPercent(rule ? String(rule.percent) : ''); setAdvanced(!!rule);
    setScope('session'); setValidation(null);
  }, [series]);
  useEffect(() => {
    let live = true;
    setProgramAvailable(false); setProgramError(null); setScope('session');
    if (session && exercise && editable) void data.repository.canUpdateProgram(session.id, exercise.id, adding ? undefined : series?.id)
      .then(value => { if (live) setProgramAvailable(value); })
      .catch(error => { if (live) setProgramError(messageFor(error)); });
    return () => { live = false; };
  }, [data.repository, session?.id, exercise?.id, series?.id, editable, adding]);
  const back = () => { if (!operation.lock.current && sessionId) { Keyboard.dismiss(); router.dismissTo({ pathname: '/sessions/[sessionId]', params: { sessionId } }); } };
  const deletion = useConfirmedDelete({ title: 'Retirer la série ajoutée ?', message: 'Cette série non réalisée sera retirée de cet entraînement. Le programme et toutes les performances restent conservés.',
    operationLock: operation.lock, remove: async () => { if (session && series) await data.repository.deleteAddedSet(session.id, series.id); },
    onDeleted: () => { if (sessionId) router.dismissTo({ pathname: '/sessions/[sessionId]', params: { sessionId } }); }, failureMessage: 'Impossible de retirer cette série. Réessayez.' });
  const skipping = useSkipSet({ operation, repository: data.repository, sessionId, leavesScreen: true,
    onSkipped: () => { if (sessionId) router.dismissTo({ pathname: '/sessions/[sessionId]', params: { sessionId } }); } });
  const busy = operation.busy || deletion.busy || skipping.confirming;
  const candidates = (session?.sets ?? []).filter(item => item.sessionExerciseId === exercise?.id && item.id !== series?.id && !item.loadRule &&
    (!item.loadRuleSnapshot || item.editScope) && (draft.kind === 'back_off' ? item.kind === 'top_set' : ['work','top_set','custom'].includes(item.kind)))
    .map(item => ({ ...item, displayIndex: item.seriesIndex, targetWeightKg: mode === 'performed'
      ? session?.performances.find(p => p.sessionSetId === item.id)?.weightKg ?? null : item.targets.targetWeightKg }));
  const reference = candidates.find(item => item.id === referenceId);
  let preview: number | null = null, calculationError: string | null = null;
  if (mode !== 'manual') {
    try {
      const p = parseLoadPercentage(percent);
      if (!reference) calculationError = 'Choisissez une série de référence compatible.';
      else if (series?.loadRule?.suspended && reference.id === series.loadRule.referenceSetId) calculationError = 'Calcul suspendu après remplacement ou retrait. Choisissez une référence compatible ou une charge manuelle.';
      else if (mode === 'performed' && reference.skippedAt) calculationError = PASSED_REFERENCE_MESSAGE;
      else if (mode === 'performed' && !session?.performances.some(item => item.sessionSetId === reference.id)) calculationError = 'En attente de la série de référence';
      else if (reference.targetWeightKg === null) calculationError = mode === 'performed' ? 'Charge réelle non renseignée : utilisez une cible manuelle.' : 'Charge prévue non renseignée : utilisez une cible manuelle.';
      else preview = percentageWeight(reference.targetWeightKg, p);
    } catch (error) { calculationError = messageFor(error); }
  }
  const manual = () => { if (mode !== 'manual') setDraft(current => ({ ...current, weight: preview === null ? '' : String(preview) })); setMode('manual'); };
  const change = <K extends keyof SetDraft>(key: K, value: SetDraft[K]) => { setDraft(current => ({ ...current, [key]: value })); setValidation(null); };
  const save = () => {
    if (!session || !exercise || !editable || data.loading || data.error || operation.lock.current) return;
    let input: SetTemplateInput;
    try {
      input = parseSetDraft({ ...draft, weight: mode === 'manual' ? draft.weight : '' });
      if (mode !== 'manual') {
        if (!reference) throw new Error('Choisissez une série de référence compatible.');
        input.loadRule = { basis: mode === 'performed' ? 'performed_weight' : 'planned_target', referenceSetId: reference.id, percent: parseLoadPercentage(percent) };
      } else input.loadRule = null;
      if (scope === 'program' && !programAvailable) throw new Error('Le modèle n’est plus disponible. Choisissez « Cette séance ».');
    } catch (error) { setValidation(messageFor(error)); return; }
    token.current ??= randomUUID();
    Keyboard.dismiss(); setValidation(null);
    void operation.run(() => adding ? data.repository.addSet(session.id, exercise.id, input, scope, token.current!)
      : data.repository.updateSet(session.id, series!.id, input, scope),
      () => router.dismissTo({ pathname: '/sessions/[sessionId]', params: { sessionId: session.id } }), true);
  };
  return <Screen compact footer={!data.loading && !data.error && editable && exercise ? <View style={{ gap: 8 }}>
    <FormError message={validation ?? operation.error ?? deletion.error} />
    <Button label={adding ? 'Ajouter la série' : 'Enregistrer les objectifs'} icon="checkmark" loading={operation.busy} disabled={busy} onPress={save} />
  </View> : undefined}>
    <Heading title={adding ? 'Ajouter une série' : 'Modifier la série'} subtitle={exercise?.name} back backDisabled={busy} onBack={back} />
    {data.loading || data.error || !editable ? <LoadState loading={data.loading} error={data.error} retry={data.retry} missing={series?.skippedAt ? "Cette série est passée. Utilisez « Réintégrer la série » depuis l’entraînement." : "Cette série n’est pas modifiable : elle est validée, retirée ou la séance est terminée."} /> : <View style={s.sections}>
      {adding ? <>
        <Text style={s.body}>Choisissez explicitement l’exercice. Une série supplémentaire reste à réaliser ; aucun repos en cours n’est modifié.</Text>
        <View accessibilityRole="radiogroup" accessibilityLabel="Exercice concerné" style={{ gap: 8 }}>{exercises.map(item => <Choice key={item.id} label={item.name} selected={item.id === exerciseId} disabled={busy} onPress={() => { if (item.id !== exerciseId) { setExerciseId(item.id); setReferenceId(''); setMode('manual'); setDraft(current => ({ ...current, weight: '' })); } }} />)}</View>
      </> : <>
        <Text style={s.eyebrow}>{series && sessionSeriesTitle(series, display)}</Text>
        {series?.editScope && <Text style={s.help}>Dernière portée enregistrée : {series.editScope === 'program' ? 'Programme' : 'Cette séance'}.</Text>}
        <Button label="Choisir une autre série restante" variant="ghost" disabled={busy} onPress={() => setPickingSet(value => !value)} />
        {pickingSet && <View style={{ gap: 8 }} accessibilityRole="radiogroup" accessibilityLabel="Série à modifier">{remaining.map(item => <Choice key={item.id}
          label={`${session?.exercises.find(e => e.id === item.sessionExerciseId)?.name} · ${sessionSeriesTitle(item, display)}`}
          selected={item.id === series?.id} disabled={busy} onPress={() => { setSelectedId(item.id); setPickingSet(false); }} />)}</View>}
      </>}
      <Field label="Nom de la série (facultatif)" value={draft.label} onChangeText={value => change('label', value)} maxLength={80} />
      <View style={s.choices} accessibilityRole="radiogroup" accessibilityLabel="Type de série">{(Object.keys(setKindLabel) as (keyof typeof setKindLabel)[]).map(kind =>
        <Choice key={kind} label={setKindLabel[kind]} selected={draft.kind === kind} disabled={busy} onPress={() => { if (kind !== draft.kind) { manual(); change('kind', kind); setAdvanced(false); } }} />)}</View>
      {(draft.kind === 'warmup' || draft.kind === 'back_off') && <>
        <Button label="Charge calculée (facultatif)" variant="secondary" disabled={busy} onPress={() => setAdvanced(value => !value)} />
        {advanced && <LoadRuleFields mode={mode} onManual={manual} onPercentage={() => setMode('percentage')} onPerformed={() => setMode('performed')}
          candidates={candidates} referenceId={referenceId} onReference={setReferenceId} percent={percent} onPercent={setPercent} preview={preview} error={calculationError} disabled={busy} />}
      </>}
      <View style={s.choices} accessibilityRole="radiogroup" accessibilityLabel="Cible de répétitions">
        <Choice label="Nombre exact" selected={draft.repetitionMode === 'exact'} disabled={busy} onPress={() => change('repetitionMode','exact')} />
        <Choice label="Plage min / max" selected={draft.repetitionMode === 'range'} disabled={busy} onPress={() => change('repetitionMode','range')} />
      </View>
      <View style={s.grid}>
        <Card style={s.gridCell}><Text style={s.smallLabel}>{exercise ? weightModeLabel[exercise.weightMode] : 'Charge cible'}</Text>
          <NumericInput label="Charge cible (kg)" value={mode === 'manual' ? draft.weight : preview === null ? '' : String(preview)} onChange={value => change('weight',value)} decimal disabled={busy || mode !== 'manual'} /></Card>
        <Card style={s.gridCell}><Text style={s.smallLabel}>Répétitions cibles</Text>
          {draft.repetitionMode === 'range' ? <View style={s.row}>
            <NumericInput label="Répétitions minimum" value={draft.repsMin} onChange={value => change('repsMin',value)} disabled={busy} />
            <NumericInput label="Répétitions maximum" value={draft.repsMax} onChange={value => change('repsMax',value)} disabled={busy} />
          </View> : <NumericInput label="Répétitions cibles" value={draft.repsMin} onChange={value => change('repsMin',value)} disabled={busy} />}</Card>
        <Card style={s.gridCell}><Text style={s.smallLabel}>RIR cible</Text><NumericInput label="RIR cible" value={draft.rir} onChange={value => change('rir',value)} disabled={busy} /></Card>
        <Card style={s.gridCell}><Text style={s.smallLabel}>Repos après cette série (s)</Text><NumericInput label="Repos cible (s)" value={draft.rest} onChange={value => change('rest',value)} disabled={busy} /></Card>
      </View>
      <Field label="Notes de la série (facultatives)" value={draft.notes} onChangeText={value => change('notes',value)} maxLength={1000} multiline />
      <Text style={s.subtitle}>Appliquer la modification à</Text>
      <View style={s.choices} accessibilityRole="radiogroup" accessibilityLabel="Portée de la modification">
        <Choice label="Cette séance" selected={scope === 'session'} disabled={busy} onPress={() => setScope('session')} />
        <Choice label="Programme" selected={scope === 'program'} disabled={busy || !programAvailable} onPress={() => setScope('program')} />
      </View>
      <Text style={s.help}>{scope === 'session' ? 'Seul cet entraînement est modifié.' : 'Cette série et sa programmation pour les futurs entraînements seront modifiées. Les entraînements précédents restent inchangés.'}</Text>
      {!programAvailable && <Text style={s.help}>{programError ?? 'Programme indisponible : modèle supprimé, exercice remplacé ou série uniquement locale. L’ajout et la modification restent possibles dans cette séance.'}</Text>}
      {!adding && series && <>
        <Text style={s.help}>Passer cette série concerne uniquement cet entraînement. Les objectifs déjà enregistrés sont conservés ; les champs non enregistrés ne sont pas appliqués.</Text>
        <Button label="Passer cette série" variant="ghost" disabled={busy} onPress={() => { setValidation(null); skipping.confirm(series); }} />
      </>}
      <Button label="Annuler" variant="ghost" disabled={busy} onPress={back} />
      {!adding && series?.addition && <Button label="Retirer la série ajoutée" variant="danger" icon="trash-outline" disabled={busy} onPress={deletion.confirm} />}
    </View>}
  </Screen>;
}
