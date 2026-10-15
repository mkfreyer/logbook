import { router } from 'expo-router';
import { useCallback, useState } from 'react';
import { Pressable, Text, View } from 'react-native';
import { historyRange, type HistoryPeriod } from '../../domain/history';
import { setKindLabel, weightModeLabel, type WeightMode, type SetKind } from '../../domain/training';
import { useSessions } from '../../store/SessionProvider';
import { Button, Card, EmptyState, Field, Heading, Screen } from '../../ui';
import { LoadState, RefreshNotice, useFocusedData } from '../programs/shared';
import { sessionStyles as s } from '../sessions/shared';
import { ProgressChart } from './ProgressChart';
import { h, HistoryPagination, HistoryTab, historyDate, historyNumber, historyWeight, PeriodPicker, useHistoryClock, useHistoryForegroundRefresh } from './shared';

export function ExerciseHistoryIndex() {
  const repository = useSessions().history, now = useHistoryClock();
  const [query, setQuery] = useState('');
  const { until } = historyRange('all', now);
  const data = useFocusedData(useCallback(() => repository.exercises({ until }), [repository, until]));
  useHistoryForegroundRefresh(data.retry);
  const normalize = (value: string) => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('fr-FR');
  const found = data.data?.filter(item => normalize(`${item.name} ${item.muscleGroup} ${item.equipment}`).includes(normalize(query.trim())));
  return <Screen compact><Heading title="Par exercice" subtitle="Uniquement les exercices réellement pratiqués" back />
    <Field label="Rechercher dans mes performances" value={query} onChangeText={setQuery} placeholder="Nom, muscle, matériel" />
    <RefreshNotice {...data} />
    {data.loading || data.error || !found ? <LoadState loading={data.loading} error={data.error} retry={data.retry} />
      : found.length === 0 ? <Card><EmptyState icon="barbell-outline" title={query ? 'Aucun résultat' : 'Vos premières performances'}
        description={query ? 'Essayez un autre nom, muscle ou matériel.' : 'Les exercices de vos entraînements terminés apparaîtront ici.'} /></Card>
        : found.map(item => <Pressable key={item.id} accessibilityRole="button" accessibilityLabel={`Performances de ${item.name}`}
          onPress={() => router.push({ pathname: '/history/exercises/[exerciseId]', params: { exerciseId: item.id } })}>
          <Card style={{ gap: 5 }}><Text style={s.subtitle}>{item.name}</Text><Text style={s.help}>{item.muscleGroup} · {item.equipment} · {item.sessionCount} séances</Text></Card>
        </Pressable>)}
  </Screen>;
}

export function ExerciseHistory({ exerciseId, initialMode }: { exerciseId?: string; initialMode?: WeightMode }) {
  const repository = useSessions().history, now = useHistoryClock();
  const [period, setPeriod] = useState<HistoryPeriod>('all'), [mode, setMode] = useState(initialMode), [page, setPage] = useState(0);
  const [metric, setMetric] = useState<'weight' | 'reps' | 'tonnage'>('weight');
  const { from, until } = historyRange(period, now);
  const data = useFocusedData(useCallback(() => repository.exercise(exerciseId ?? '', { from, until }, mode, page), [repository, exerciseId, from, until, mode, page]));
  useHistoryForegroundRefresh(data.retry);
  const result = data.data;
  const last = result?.lastPerformance;
  return <Screen compact><Heading title={result?.exercise?.name ?? 'Historique d’exercice'} subtitle="Performances réalisées · lecture seule" back />
    <PeriodPicker value={period} onChange={value => { setPeriod(value); setPage(0); }} />
    <RefreshNotice {...data} />
    {data.loading || data.error || !result ? <LoadState loading={data.loading} error={data.error} retry={data.retry} /> : !result.exercise ?
      <Card><EmptyState icon="barbell-outline" title="Pas de performance sur cette période" description="Aucune série réalisée disponible pour cet exercice. Élargissez la période pour retrouver vos entraînements." /></Card> : <View style={s.sections}>
      <Card style={{ gap: 8 }}><Text style={s.body}>{result.exercise.muscleGroup} · {result.exercise.equipment}</Text>
        <Text style={s.help}>{result.sessionCount} séances pratiquées{result.mode ? ` · ${weightModeLabel[result.mode]}` : ''}</Text>
        {last && <><Text style={s.eyebrow}>DERNIÈRE SÉRIE ENREGISTRÉE</Text>
          <Text style={s.body}>{historyWeight(last.weightKg)} × {last.reps} reps{last.rir === null ? '' : ` · RIR ${last.rir}`}</Text><Text style={s.help}>{historyDate(last.performedAt)}</Text></>}
      </Card>
      {result.modes.length > 1 && <View style={{ gap: 8 }}><Text style={s.help}>Modes de charge séparés pour conserver des comparaisons cohérentes.</Text>
        <View style={h.tabs}>{result.modes.map(item => <HistoryTab key={item} label={weightModeLabel[item]} selected={item === result.mode} onPress={() => { setMode(item); setPage(0); }} />)}</View></View>}
      {result.sessionCount === 0 && <Card><EmptyState icon="barbell-outline" title="Aucune série sur cette période"
        description="Ce mode de charge reste sélectionné. Élargissez la période ou choisissez explicitement un autre mode disponible." /></Card>}
      <View style={h.tabs}><HistoryTab label="Charge" selected={metric === 'weight'} onPress={() => setMetric('weight')} />
        <HistoryTab label="Répétitions" selected={metric === 'reps'} onPress={() => setMetric('reps')} />
        <HistoryTab label="Tonnage" selected={metric === 'tonnage'} onPress={() => setMetric('tonnage')} /></View>
      <ProgressChart title={metric === 'weight' ? 'Charge de travail' : metric === 'reps' ? 'Répétitions de travail' : 'Tonnage enregistré'}
        unit={metric === 'tonnage' ? 'kg enregistrés' : metric === 'reps' ? 'reps' : result.mode === 'per_hand' ? 'kg / haltère' : result.mode === 'additional' ? 'kg ajoutés' : 'kg'}
        points={result.points.map(point => ({ id: point.sessionId, date: point.finishedAt,
          label: metric === 'tonnage' || !point.representative ? point.workoutName : `${point.workoutName} · ${historyWeight(point.representative.weightKg)} × ${point.representative.reps} reps${point.representative.rir === null ? '' : ` · RIR ${point.representative.rir}`}`,
          value: metric === 'tonnage' ? point.loggedTonnageKg : metric === 'weight' ? point.representative?.weightKg ?? null : point.representative?.reps ?? null }))} />
      <Text style={s.help}>{metric === 'tonnage' ? 'Charges saisies × répétitions, échauffements inclus. Haltères non doublés, poids du corps non estimé.'
        : 'Une série hors échauffement par séance : charge renseignée la plus élevée, puis répétitions en cas d’égalité. Sans charge, la série avec le plus de répétitions. Charge et répétitions proviennent de la même série, sans tenir compte du RIR pour la sélection.'}</Text>
      {result.sessionCount > 120 && <Text style={s.help}>Graphique : 120 dernières séances de cette période et de ce mode. La liste paginée reste complète.</Text>}
      <Text style={s.eyebrow}>SÉRIES RÉALISÉES · PAR ENTRAÎNEMENT</Text>
      {result.visits.map(visit => <Card key={visit.sessionId} style={{ padding: 14, gap: 7 }}>
        <Text style={s.subtitle}>{visit.workoutName}</Text><Text style={s.help}>{historyDate(visit.finishedAt)} · {visit.programName}</Text>
        <View style={h.tableRow}><Text style={[s.help, h.seriesCell]}>Série</Text><Text style={[s.help, h.cell]}>Kg</Text><Text style={[s.help, h.cell]}>Reps</Text><Text style={[s.help, h.cell]}>RIR</Text></View>
        {visit.performances.map(performance => <View key={performance.id} style={h.tableRow}>
          <View style={h.seriesCell}><Text style={s.help}>{performance.label || (performance.kind === 'work' ? `Série ${performance.seriesIndex + 1}` : setKindLabel[performance.kind as SetKind])}</Text>
            {performance.exerciseName !== result.exercise!.name && <Text style={s.help}>{performance.exerciseName}</Text>}</View>
          <Text style={[s.body, h.cell]}>{performance.weightKg === null ? '—' : historyNumber(performance.weightKg)}</Text>
          <Text style={[s.body, h.cell]}>{performance.reps}</Text><Text style={[s.body, h.cell]}>{performance.rir ?? '—'}</Text>
        </View>)}
        <Button label="Consulter cette séance" variant="ghost" onPress={() => router.push({ pathname: '/history/sessions/[sessionId]', params: { sessionId: visit.sessionId } })} />
      </Card>)}
      <HistoryPagination page={result.page} count={result.pageCount} onChange={setPage} />
    </View>}
  </Screen>;
}
