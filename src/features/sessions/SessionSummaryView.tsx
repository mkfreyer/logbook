import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import type { WorkoutSession } from '../../domain/session';
import { formatSessionDuration, summarizeSession } from '../../domain/sessionSummary';
import { Button, Card, colors, Heading, Screen } from '../../ui';
import { LoadState } from '../programs/shared';
import { sessionSeriesTitle, sessionStyles as s } from './shared';

const number = (value: number) => value.toLocaleString('fr-FR', { maximumFractionDigits: 2 });

export function SessionSummaryView({ session, onExit, onRetry }: { session: WorkoutSession; onExit(): void; onRetry(): void }) {
  const [details, setDetails] = useState(false);
  let summary;
  try { summary = summarizeSession(session); } catch (failure) {
    return <Screen><Heading title="Bilan de séance" back onBack={onExit} /><LoadState loading={false}
      error={failure instanceof Error ? failure.message : 'Bilan indisponible.'} retry={onRetry} /></Screen>;
  }
  return <Screen compact footer={<Button label="Retour aux programmes" icon="arrow-back" onPress={onExit} />}>
    <Heading title="Séance terminée" back onBack={onExit} />
    <LinearGradient colors={['#123954', '#0c1d2c']} style={styles.hero}>
      <View style={styles.trophy}><Ionicons name="trophy-outline" color={colors.cyan} size={36} /></View>
      <Text style={s.title}>Entraînement enregistré</Text>
      <Text style={s.subtitle}>{session.workoutName}</Text>
      <Text style={s.help}>{new Date(session.finishedAt!).toLocaleString('fr-FR', { dateStyle: 'medium', timeStyle: 'short' })}</Text>
    </LinearGradient>
    <View style={styles.grid}>
      <Metric label="Tonnage enregistré" value={summary.loggedTonnageKg === null ? '—' : `${number(summary.loggedTonnageKg)} kg`} icon="barbell-outline" />
      <Metric label="Durée totale" value={formatSessionDuration(summary.durationMs)} icon="time-outline" />
      <Metric label="Séries réalisées" value={String(summary.performedSetCount)} icon="checkmark-done-outline" />
      <Metric label="RIR moyen" value={summary.meanRir === null ? '—' : number(summary.meanRir)} icon="fitness-outline" />
    </View>
    <View style={{ gap: 7 }}>
      <Text style={s.help}>Durée écoulée, pauses et absences comprises.</Text>
      <Text style={s.help}>{summary.unchargedSetCount ? `${summary.unchargedSetCount} série${summary.unchargedSetCount > 1 ? 's' : ''} sans charge renseignée, exclue${summary.unchargedSetCount > 1 ? 's' : ''} du tonnage.` : 'Tonnage calculé sur les charges réellement saisies.'}</Text>
      {(summary.tonnageByMode.per_hand > 0 || summary.tonnageByMode.additional > 0) && <Text style={s.help}>Charges par haltère non doublées. Poids du corps non estimé.</Text>}
      <Text style={s.help}>{summary.rirSetCount ? `RIR moyen sur ${summary.rirSetCount} série${summary.rirSetCount > 1 ? 's' : ''} renseignée${summary.rirSetCount > 1 ? 's' : ''}.` : 'Aucun RIR renseigné.'}</Text>
      <Pressable accessibilityRole="button" accessibilityLabel="Convention de calcul du tonnage" accessibilityState={{ expanded: details }}
        onPress={() => setDetails(value => !value)} style={styles.explanation}>
        <Ionicons name="information-circle-outline" color={colors.cyan} size={18} /><Text style={[s.help, { color: colors.cyan }]}>Charges saisies × répétitions · convention de calcul</Text>
      </Pressable>
      {details && <Card style={{ gap: 8 }}>
        <Text style={s.help}>Somme des charges saisies × répétitions réalisées, échauffements inclus. Une charge par haltère est comptée une fois, sans supposer deux haltères. Une charge ajoutée exclut le poids du corps. Une charge vide est exclue. Ce chiffre n’est pas la masse totale déplacée.</Text>
        <Text style={s.help}>Charges totales : {number(summary.tonnageByMode.total)} kg · Par haltère : {number(summary.tonnageByMode.per_hand)} kg · Charges ajoutées : {number(summary.tonnageByMode.additional)} kg</Text>
      </Card>}
    </View>
    <Text style={s.eyebrow}>EXERCICES RÉALISÉS</Text>
    {summary.exercises.map(({ exercise, performances, replacedFrom }) => <Card key={exercise.id} style={{ gap: 10 }}>
      <View style={s.row}><Ionicons name="barbell-outline" color={colors.cyan} size={26} /><View style={{ flex: 1 }}>
        <Text style={s.subtitle}>{exercise.name}</Text><Text style={s.help}>{performances.length} série{performances.length > 1 ? 's' : ''} réalisée{performances.length > 1 ? 's' : ''}</Text>
      </View></View>
      {replacedFrom && <Text style={[s.help, { color: colors.cyan }]}>En remplacement de {replacedFrom.name}</Text>}
      {performances.map(({ performance, series }) => <View key={performance.id} style={styles.performance}>
        <Text style={s.help}>{performance.sortOrder + 1}. {sessionSeriesTitle(series)}</Text>
        <Text style={s.body}>{performance.weightKg === null ? 'Charge non renseignée' : `${number(performance.weightKg)} kg${exercise.weightMode === 'per_hand' ? ' / haltère' : exercise.weightMode === 'additional' ? ' ajoutés' : ''}`} · {performance.reps} reps{performance.rir === null ? '' : ` · RIR ${performance.rir}`}</Text>
      </View>)}
    </Card>)}
    <Text style={s.help}>Les numéros indiquent l’ordre réel de validation. Vos résultats et vos repos sont conservés sur cet iPhone.</Text>
  </Screen>;
}

function Metric({ label, value, icon }: { label: string; value: string; icon: 'time-outline' | 'barbell-outline' | 'checkmark-done-outline' | 'fitness-outline' }) {
  return <Card style={styles.metric}><View style={styles.metricHeader}><Ionicons name={icon} color={colors.cyan} size={20} /><Text style={s.help}>{label}</Text></View>
    <Text style={styles.value} accessibilityLabel={label}>{value}</Text></Card>;
}
const styles = StyleSheet.create({
  hero: { padding: 20, borderWidth: 1, borderColor: colors.border, borderRadius: 24, alignItems: 'center', gap: 8 },
  trophy: { width: 64, height: 64, borderRadius: 22, alignItems: 'center', justifyContent: 'center', backgroundColor: '#143f5d' },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12 }, metric: { width: '47%', flexGrow: 1, padding: 14, gap: 10 },
  metricHeader: { flexDirection: 'row', gap: 7, alignItems: 'center', flexWrap: 'wrap' },
  value: { color: colors.text, fontSize: 23, fontWeight: '600', fontVariant: ['tabular-nums'] },
  explanation: { minHeight: 44, flexDirection: 'row', alignItems: 'center', gap: 7 },
  performance: { gap: 3, borderTopWidth: 1, borderTopColor: colors.border, paddingTop: 8 },
});
