import { Text, View } from 'react-native';
import { formatSeriesTitle } from '../../domain/series';
import type { SetTemplate } from '../../domain/training';
import { Button, Card } from '../../ui';
import { Choice, NumericInput } from '../sessions/shared';
import { trainingStyles as s } from './shared';

export function LoadRuleFields({ mode, onManual, onPercentage, onPerformed, candidates, referenceId, onReference,
  percent, onPercent, preview, error, disabled }: {
  mode: 'manual' | 'percentage' | 'performed'; onManual(): void; onPercentage(): void; onPerformed(): void;
  candidates: (Pick<SetTemplate, 'id' | 'label' | 'kind' | 'targetWeightKg'> & { displayIndex: number })[]; referenceId: string; onReference(id: string): void;
  percent: string; onPercent(value: string): void; preview: number | null; error: string | null; disabled: boolean;
}) {
  return <Card style={{ gap: 12 }}><Text style={s.title}>Charge de cette série</Text>
    <View accessibilityRole="radiogroup" accessibilityLabel="Mode de charge cible" style={{ gap: 8 }}>
      <Choice label="Charge manuelle" selected={mode === 'manual'} disabled={disabled} onPress={onManual} />
      <Choice label="Pourcentage d’une série prévue" selected={mode === 'percentage'} disabled={disabled} onPress={onPercentage} />
      <Choice label="Pourcentage de la charge réellement effectuée" selected={mode === 'performed'} disabled={disabled} onPress={onPerformed} />
    </View>
    {mode !== 'manual' && <>
      <Text style={s.body}>Choisissez explicitement une référence manuelle du même exercice. Les back-offs utilisent un top set.</Text>
      {candidates.length === 0 && <Text style={s.hint}>Aucune référence compatible. Enregistrez d’abord une série de travail ou un top set manuel, ou utilisez une charge manuelle.</Text>}
      <View accessibilityRole="radiogroup" accessibilityLabel="Série de référence" style={{ gap: 8 }}>
        {candidates.map(series => <Choice key={series.id} label={`Référence : ${formatSeriesTitle(series, series.displayIndex, 'both')} · ${series.targetWeightKg === null ? mode === 'performed' ? 'charge réelle non disponible' : 'charge cible non définie' : `${String(series.targetWeightKg).replace('.', ',')} kg${mode === 'performed' ? ' réalisés' : ' prévus'}`}`}
          selected={series.id === referenceId} disabled={disabled} onPress={() => onReference(series.id)} />)}
      </View>
      <View><Text style={s.body}>Pourcentage de charge</Text>
        <NumericInput label="Pourcentage de charge" value={percent} onChange={onPercent} placeholder="Ex. 50" decimal disabled={disabled} /></View>
      <Text accessibilityLabel="Charge calculée" style={s.title}>{preview === null ? 'Charge calculée non disponible' : `${String(preview).replace('.', ',')} kg`}</Text>
      {error && <Text style={s.hint}>{error}</Text>}
      <Text style={s.hint}>{mode === 'performed' ? 'Calcul sur la charge réellement validée de la référence, pendant cet entraînement.' : 'Calcul sur la cible prévue.'} Sans arrondi au matériel. Répétitions, RIR et repos restent propres à cette série. Aucune performance réelle n’est préremplie.</Text>
      <Button label="Remplacer par une charge manuelle" variant="secondary" disabled={disabled} onPress={onManual} />
    </>}
  </Card>;
}
