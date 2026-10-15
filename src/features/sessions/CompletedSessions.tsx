import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useCallback } from 'react';
import { Pressable, Text, View } from 'react-native';
import { useSessions } from '../../store/SessionProvider';
import { Card, colors, EmptyState, Heading, Screen } from '../../ui';
import { LoadState, RefreshNotice, useFocusedData } from '../programs/shared';
import { sessionStyles as s } from './shared';

/** A simple access to saved summaries, without the charts/filters/history tree of M3. */
export function CompletedSessions() {
  const repository = useSessions();
  const data = useFocusedData(useCallback(() => repository.listCompletedSessions(), [repository]));
  return <Screen compact>
    <Heading title="Bilans de séances" subtitle="Vos entraînements terminés" back />
    <RefreshNotice {...data} />
    {data.loading || data.error || !data.data ? <LoadState loading={data.loading} error={data.error} retry={data.retry} /> :
      data.data.length === 0 ? <Card><EmptyState icon="checkmark-circle-outline" title="Votre premier bilan"
        description="Terminez un entraînement pour retrouver ici son bilan enregistré." /></Card> : <View style={s.sections}>
        {data.data.map(session => <Pressable key={session.id} accessibilityRole="button" accessibilityLabel={`Voir le bilan ${session.workoutName}`}
          onPress={() => router.push({ pathname: '/sessions/[sessionId]', params: { sessionId: session.id } })}>
          <Card><View style={s.row}><Ionicons name="checkmark-circle-outline" color={colors.cyan} size={28} /><View style={{ flex: 1 }}>
            <Text style={s.subtitle}>{session.workoutName}</Text><Text style={s.help}>{session.programName}</Text>
            <Text style={s.body}>{new Date(session.finishedAt!).toLocaleString('fr-FR', { dateStyle: 'medium', timeStyle: 'short' })}</Text>
            <Text style={s.help}>{session.performedSetCount} série{session.performedSetCount > 1 ? 's' : ''} réalisée{session.performedSetCount > 1 ? 's' : ''}</Text>
          </View><Ionicons name="chevron-forward" color={colors.muted} size={20} /></View></Card>
        </Pressable>)}
      </View>}
  </Screen>;
}
