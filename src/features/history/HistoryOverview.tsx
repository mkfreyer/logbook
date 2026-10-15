import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useCallback, useState } from 'react';
import { Pressable, Text, View } from 'react-native';
import { historyRange, previousHistoryRange, type HistoryPeriod } from '../../domain/history';
import { formatSessionDuration } from '../../domain/sessionSummary';
import { useSessions } from '../../store/SessionProvider';
import { Button, Card, colors, EmptyState, Heading, Screen } from '../../ui';
import { LoadState, RefreshNotice, useFocusedData } from '../programs/shared';
import { sessionStyles as s } from '../sessions/shared';
import { ProgressChart } from './ProgressChart';
import { h, HistoryMetric, HistoryPagination, HistoryTab, historyDate, historyWeight, PeriodPicker, useHistoryClock, useHistoryForegroundRefresh } from './shared';

export function HistoryOverview({ programId, programName, initialPeriod = '30' }: { programId?: string; programName?: string; initialPeriod?: HistoryPeriod }) {
  const repository = useSessions().history;
  const [period, setPeriod] = useState<HistoryPeriod>(initialPeriod), [page, setPage] = useState(0);
  const [metric, setMetric] = useState<'tonnage' | 'sets'>('tonnage');
  const now = useHistoryClock();
  const range = historyRange(period, now), previous = previousHistoryRange(period, now);
  const data = useFocusedData(useCallback(() => repository.overview({ from: range.from, until: range.until, programId }, page,
    previous ? { from: previous.from, until: previous.until } : null), [repository, range.from, range.until, previous?.from, previous?.until, programId, page]));
  useHistoryForegroundRefresh(data.retry);
  const result = data.data;
  const title = programId ? result?.programs[0]?.name ?? programName ?? 'Historique du programme' : 'Historique';
  return <Screen compact>
    <Heading title={title} subtitle={programId ? 'Entraînements de ce programme' : 'Vos entraînements réellement terminés'} back />
    <PeriodPicker value={period} onChange={value => { setPeriod(value); setPage(0); }} />
    {!programId && <Button label="Performances par exercice" icon="barbell-outline" variant="secondary" onPress={() => router.push('/history/exercises')} />}
    <RefreshNotice {...data} />
    {data.loading || data.error || !result ? <LoadState loading={data.loading} error={data.error} retry={data.retry} /> : <View style={s.sections}>
      {result.stats.sessionCount === 0 ? <Card>
        <EmptyState icon="stats-chart-outline" title="Votre histoire commence ici"
          description={period === 'all' ? 'Terminez une séance pour retrouver vos résultats réels et suivre leur évolution.' : 'Aucun entraînement terminé sur cette période. Consultez toute la période ou commencez une séance.'} />
        {period !== 'all' && <Button label="Voir toute la période" variant="secondary" onPress={() => { setPeriod('all'); setPage(0); }} />}
        <Button label="Voir mes programmes" onPress={() => router.dismissTo({ pathname: '/', params: { universe: 'musculation' } })} />
      </Card> : <>
        <View style={h.metrics}>
          <HistoryMetric label="Entraînements" value={String(result.stats.sessionCount)} />
          <HistoryMetric label="Tonnage enregistré" value={historyWeight(result.stats.loggedTonnageKg)} />
          <HistoryMetric label="Durée cumulée" value={formatSessionDuration(result.stats.durationMs)} />
          <HistoryMetric label="Séries réalisées" value={String(result.stats.performedSetCount)} />
        </View>
        <Text style={s.help}>Durées écoulées, pauses et absences comprises. Charges saisies × répétitions, échauffements inclus. Haltères non doublés, poids du corps non estimé.{result.stats.unchargedSetCount ? ` ${result.stats.unchargedSetCount} séries sans charge exclues du tonnage.` : ''}</Text>
        {programId && result.programs[0]?.deleted === 1 && <Text style={s.help}>Programme supprimé · ses entraînements restent conservés.</Text>}
        {programId && result.previous && <Card style={{ gap: 6 }}>
          <Text style={s.eyebrow}>PÉRIODE PRÉCÉDENTE DE MÊME DURÉE</Text>
          <Text style={s.body}>{result.previous.sessionCount} séances · {result.previous.performedSetCount} séries · {historyWeight(result.previous.loggedTonnageKg)}</Text>
          <Text style={s.help}>Comparaison descriptive : les exercices et les charges renseignées peuvent différer.</Text>
        </Card>}
        {programId && <View style={h.tabs}>
          <HistoryTab label="Tonnage" selected={metric === 'tonnage'} onPress={() => setMetric('tonnage')} />
          <HistoryTab label="Séries" selected={metric === 'sets'} onPress={() => setMetric('sets')} />
        </View>}
        <ProgressChart title={metric === 'tonnage' ? 'Tonnage par séance' : 'Séries par séance'} unit={metric === 'tonnage' ? 'kg enregistrés' : 'séries'}
          points={result.points.map(point => ({ id: point.id, date: point.finishedAt, label: point.workoutName,
            value: metric === 'tonnage' ? point.loggedTonnageKg : point.performedSetCount }))} />
        {result.stats.sessionCount > 120 && <Text style={s.help}>Graphique limité aux 120 dernières séances de la période. Les totaux et la liste incluent toutes les séances filtrées.</Text>}
        {!programId && <>
          <Text style={s.eyebrow}>PAR PROGRAMME</Text>
          {result.programs.map(program => <Pressable key={program.id} accessibilityRole="button" accessibilityLabel={`Historique du programme ${program.name}, ${program.sessionCount} séances`}
            onPress={() => router.push({ pathname: '/history/programs/[programId]', params: { programId: program.id, name: program.name, period } })}>
            <Card style={{ gap: 6 }}><View style={s.row}><Ionicons name="barbell-outline" color={colors.cyan} size={22} />
              <View style={{ flex: 1 }}><Text style={s.subtitle}>{program.name}</Text><Text style={s.help}>{program.sessionCount} séances{program.deleted ? ' · programme supprimé' : ''}</Text>
                <Text style={s.help}>Référence {program.id.slice(-8)}</Text></View><Ionicons name="chevron-forward" color={colors.muted} size={18} /></View></Card>
          </Pressable>)}
        </>}
        <Text style={s.eyebrow}>SÉANCES TERMINÉES · PLUS RÉCENTES EN PREMIER</Text>
        {result.sessions.map(session => <Pressable key={session.id} accessibilityRole="button" accessibilityLabel={`Consulter ${session.workoutName}, ${historyDate(session.finishedAt)}`}
          onPress={() => router.push({ pathname: '/history/sessions/[sessionId]', params: { sessionId: session.id } })}>
          <Card style={{ gap: 6 }}><Text style={s.help}>{historyDate(session.finishedAt)}</Text>
            <Text style={s.subtitle}>{session.workoutName}</Text><Text style={s.body}>{session.programName}</Text>
            <Text style={s.help}>{formatSessionDuration(session.durationMs)} · {session.performedSetCount} séries réalisées · {historyWeight(session.loggedTonnageKg)}</Text></Card>
        </Pressable>)}
        <HistoryPagination page={result.page} count={result.pageCount} onChange={setPage} />
      </>}
    </View>}
  </Screen>;
}
