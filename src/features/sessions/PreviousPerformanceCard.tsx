import { useCallback } from 'react';
import { Pressable, Text } from 'react-native';
import type { SessionExercise, SessionSet } from '../../domain/session';
import { setKindLabel, type SetKind } from '../../domain/training';
import { useSessions } from '../../store/SessionProvider';
import { Card, colors } from '../../ui';
import { useFocusedData } from '../programs/shared';
import { sessionStyles as s } from './shared';

/** Observation only: never receives a setter for the current actual inputs. */
export function PreviousPerformanceCard({ sessionId, series, exercise }: { sessionId: string; series: SessionSet; exercise: SessionExercise }) {
  const repository = useSessions().history;
  const context = `${sessionId}:${series.id}:${exercise.id}:${exercise.sourceCatalogExerciseId}:${exercise.weightMode}:${series.kind}:${series.seriesIndex}`;
  const data = useFocusedData(useCallback(async () => ({ context, value: await repository.previousPerformance(sessionId, series.id) }),
    [repository, sessionId, series.id, context]));
  if (data.loading) return <Text style={s.help}>Recherche de votre dernier repère…</Text>;
  if (data.error) return <Pressable accessibilityRole="button" accessibilityLabel="Réessayer la dernière performance" onPress={data.retry} style={{ minHeight: 44, justifyContent: 'center' }}>
    <Text style={s.help}>Dernier repère indisponible · Réessayer</Text></Pressable>;
  if (data.data && data.data.context !== context) return <Text style={s.help}>Recherche de votre dernier repère…</Text>;
  if (!data.data?.value) return <Text style={s.help}>Pas encore de série comparable enregistrée.</Text>;
  const { performance: previous, comparison } = data.data.value;
  const weight = previous.weightKg === null ? 'Charge non renseignée' : `${previous.weightKg.toLocaleString('fr-FR')} kg${previous.weightMode === 'per_hand' ? ' / haltère' : previous.weightMode === 'additional' ? ' ajoutés' : ''}`;
  return <Card style={{ padding: 12, gap: 4 }}>
    <Text style={[s.eyebrow, { color: colors.muted }]}>DERNIÈRE FOIS</Text>
    <Text style={{ color: colors.text, fontSize: 15, lineHeight: 21 }}>{weight} × {previous.reps} répétitions{previous.rir === null ? '' : ` · RIR ${previous.rir}`}</Text>
    <Text style={s.help}>{comparison === 'same_series' ? 'Même type et position de série' : comparison === 'same_type' ? 'Même type · autre position' : 'Dernière performance de cet exercice · autre type'} · {setKindLabel[previous.kind as SetKind]} · {new Date(previous.finishedAt).toLocaleDateString('fr-FR')}</Text>
  </Card>;
}
