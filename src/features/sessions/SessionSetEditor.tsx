import { useSeriesDisplay } from '../../store/SeriesDisplayProvider';
import { router } from 'expo-router';
import { useEffect, useState } from 'react';
import { Keyboard, Text, View } from 'react-native';
import { parseSetDraft, type SetDraft } from '../../domain/setDraft';
import { selectSessionStep, type SetTargets } from '../../domain/session';
import { weightModeLabel } from '../../domain/training';
import { Button, Card, Heading, Screen } from '../../ui';
import { FormError, LoadState, messageFor } from '../programs/shared';
import { useScreenOperation } from '../training/shared';
import { Choice, NumericInput, sessionSeriesTitle, sessionStyles, useSessionData } from './shared';

const emptyDraft: SetDraft = { label: '', kind: 'work', repetitionMode: 'exact', repsMin: '', repsMax: '', weight: '', rir: '', rest: '', notes: '' };

export function SessionSetEditor({ sessionId, setId }: { sessionId?: string; setId?: string }) {
  const seriesDisplay = useSeriesDisplay();
  const data = useSessionData(sessionId);
  const operation = useScreenOperation();
  const [draft, setDraft] = useState(emptyDraft);
  const [scope, setScope] = useState<'session' | 'program'>('session');
  const [validationError, setValidationError] = useState<string | null>(null);
  const step = data.session ? selectSessionStep(data.session) : null;
  const editable = step?.phase === 'set' && step.set.id === setId ? step : null;
  useEffect(() => {
    if (!editable) return;
    const series = editable.set;
    const targets = series.targets;
    setDraft({ label: series.label, kind: series.kind, notes: series.notes,
      repetitionMode: targets.repsMin === targets.repsMax ? 'exact' : 'range',
      repsMin: String(targets.repsMin), repsMax: String(targets.repsMax),
      weight: targets.targetWeightKg === null ? '' : String(targets.targetWeightKg),
      rir: targets.targetRir === null ? '' : String(targets.targetRir), rest: String(targets.restAfterSec) });
  }, [editable?.set]);
  const back = () => {
    if (operation.lock.current || !sessionId) return;
    Keyboard.dismiss();
    router.dismissTo({ pathname: '/sessions/[sessionId]', params: { sessionId } });
  };
  const change = <K extends keyof SetDraft>(key: K, value: SetDraft[K]) => { setDraft(current => ({ ...current, [key]: value })); setValidationError(null); };
  const save = () => {
    if (!editable || !data.session || operation.lock.current) return;
    let targets: SetTargets;
    try {
      const parsed = parseSetDraft(draft);
      targets = { repsMin: parsed.repsMin, repsMax: parsed.repsMax, targetWeightKg: parsed.targetWeightKg ?? null,
        targetRir: parsed.targetRir ?? null, restAfterSec: parsed.restAfterSec };
    } catch (error) {
      setValidationError(messageFor(error)); return; }
    const currentSessionId = data.session.id, currentSetId = editable.set.id;
    setValidationError(null); Keyboard.dismiss();
    void operation.run(() => data.repository.updateSetTargets(currentSessionId, currentSetId, targets, scope),
      () => router.dismissTo({ pathname: '/sessions/[sessionId]', params: { sessionId: currentSessionId } }), true);
  };
  const footer = !data.loading && !data.error && editable ? <View style={{ gap: 8 }}>
    <FormError message={validationError ?? operation.error} />
    <Button label="Enregistrer les objectifs" icon="checkmark" loading={operation.busy} onPress={save} />
  </View> : undefined;
  return <Screen compact footer={footer}>
    <Heading title="Modifier la série" subtitle={editable?.exercise.name} back backDisabled={operation.busy} onBack={back} />
    {data.loading || data.error || !editable ? <LoadState loading={data.loading} error={data.error} retry={data.retry}
      missing="Seule la série active, non encore validée, peut être modifiée." /> : <View style={sessionStyles.sections}>
      <Text style={sessionStyles.eyebrow}>{sessionSeriesTitle(editable.set, seriesDisplay).toLocaleUpperCase('fr-FR')}</Text>
      {editable.set.loadRuleSnapshot && <Text style={sessionStyles.help}>La charge a été calculée au démarrage sur une cible prévue. Cet éditeur reste manuel : le choix Programme remplacera la règle future par la charge saisie, sans modifier l’origine capturée.</Text>}
      <Text style={sessionStyles.body}>Ajustez les objectifs de cette série. Les résultats déjà enregistrés sont conservés.</Text>
      <View style={sessionStyles.choices} accessibilityRole="radiogroup" accessibilityLabel="Cible de répétitions">
        <Choice label="Nombre exact" selected={draft.repetitionMode === 'exact'} disabled={operation.busy} onPress={() => change('repetitionMode', 'exact')} />
        <Choice label="Plage min / max" selected={draft.repetitionMode === 'range'} disabled={operation.busy} onPress={() => change('repetitionMode', 'range')} />
      </View>
      <View style={sessionStyles.grid}>
        <Card style={sessionStyles.gridCell}>
          <Text style={sessionStyles.smallLabel}>{weightModeLabel[editable.exercise.weightMode]}</Text>
          <NumericInput label="Charge cible (kg)" value={draft.weight} onChange={value => change('weight', value)} decimal disabled={operation.busy} />
        </Card>
        <Card style={sessionStyles.gridCell}>
          <Text style={sessionStyles.smallLabel}>Répétitions cibles</Text>
          {draft.repetitionMode === 'range' ? <View style={sessionStyles.row}>
            <NumericInput label="Répétitions minimum" value={draft.repsMin} onChange={value => change('repsMin', value)} disabled={operation.busy} placeholder="Min" />
            <Text style={sessionStyles.body}>–</Text>
            <NumericInput label="Répétitions maximum" value={draft.repsMax} onChange={value => change('repsMax', value)} disabled={operation.busy} placeholder="Max" />
          </View> : <NumericInput label="Répétitions cibles" value={draft.repsMin} onChange={value => change('repsMin', value)} disabled={operation.busy} />}
        </Card>
        <Card style={sessionStyles.gridCell}>
          <Text style={sessionStyles.smallLabel}>RIR cible</Text>
          <NumericInput label="RIR cible" value={draft.rir} onChange={value => change('rir', value)} disabled={operation.busy} />
        </Card>
        <Card style={sessionStyles.gridCell}>
          <Text style={sessionStyles.smallLabel}>Repos après la série (s)</Text>
          <NumericInput label="Repos cible (s)" value={draft.rest} onChange={value => change('rest', value)} disabled={operation.busy} />
        </Card>
      </View>
      <Text style={sessionStyles.help}>Charge et RIR facultatifs. Le repos concerne l’intervalle après cette série, s’il reste une série à effectuer.</Text>
      <Text style={sessionStyles.subtitle}>Appliquer la modification à</Text>
      <View style={sessionStyles.choices} accessibilityRole="radiogroup" accessibilityLabel="Portée de la modification">
        <Choice label="Cette séance" selected={scope === 'session'} disabled={operation.busy} onPress={() => setScope('session')} />
        <Choice label="Programme" selected={scope === 'program'} disabled={operation.busy} onPress={() => setScope('program')} />
      </View>
      <Text style={sessionStyles.help}>{scope === 'session' ? 'Seul cet entraînement est modifié.' : 'Cette série et sa programmation pour les futurs entraînements seront modifiées. Les entraînements précédents restent inchangés.'}</Text>
      <Button label="Annuler" variant="ghost" disabled={operation.busy} onPress={back} />
    </View>}
  </Screen>;
}
