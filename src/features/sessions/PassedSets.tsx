import { Text, View } from 'react-native';
import type { SessionSet, WorkoutSession } from '../../domain/session';
import { useSeriesDisplay } from '../../store/SeriesDisplayProvider';
import { Button, Card } from '../../ui';
import { sessionSeriesTitle, sessionStyles as s } from './shared';

/** Skipped goals are visibly separate from actual performance rows and totals. */
export function PassedSets({ session, busy = false, onReintegrate }: {
  session: WorkoutSession; busy?: boolean; onReintegrate?(series: SessionSet): void;
}) {
  const display = useSeriesDisplay(), skipped = session.sets.filter(item => !!item.skippedAt);
  if (!skipped.length) return null;
  return <View style={{ gap: 12 }}>
    <Text style={s.eyebrow}>SÉRIES PASSÉES · {skipped.length}</Text>
    {skipped.map(series => {
      const exercise = session.exercises.find(item => item.id === series.sessionExerciseId);
      const unit = exercise?.weightMode === 'per_hand' ? ' / haltère' : exercise?.weightMode === 'additional' ? ' ajoutés' : '';
      return <Card key={series.id} style={{ gap: 8 }}>
      <Text style={s.subtitle}>{exercise?.name}</Text>
      <Text style={s.body}>{sessionSeriesTitle(series, display)} · Passée</Text>
      <Text style={s.help}>Objectifs conservés : {series.targets.repsMin === series.targets.repsMax ? series.targets.repsMin : `${series.targets.repsMin}–${series.targets.repsMax}`} répétitions{series.targets.targetWeightKg === null ? ' · charge libre' : ` · ${series.targets.targetWeightKg.toLocaleString('fr-FR', { maximumSignificantDigits: 21 })} kg${unit}`}{series.targets.targetRir === null ? '' : ` · RIR ${series.targets.targetRir}`} · repos prévu {series.targets.restAfterSec} s</Text>
      {series.notes ? <Text style={s.help}>Note : {series.notes}</Text> : null}
      <Text style={s.help}>Aucune performance enregistrée pour cette série.</Text>
      {onReintegrate && session.status === 'active' && <Button label="Réintégrer la série" icon="return-up-back-outline" variant="secondary" disabled={busy} onPress={() => onReintegrate(series)} />}
    </Card>; })}
  </View>;
}
