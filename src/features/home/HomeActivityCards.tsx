import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { router } from 'expo-router';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { colors } from '../../ui';
import type { useHomeActivity } from './useHomeActivity';

export function HomeActivityCards({ activity }: { activity: ReturnType<typeof useHomeActivity> }) {
  const { data, loading, error } = activity;
  return <View style={{ gap: 8 }}><View style={styles.stats}>
    <LinearGradient colors={['#0d2432', '#091824']} style={styles.card}>
      <Text style={styles.label}>Cette semaine</Text>
      <Text style={styles.value} accessibilityLabel="Séances terminées cette semaine"
        accessibilityValue={{ text: loading ? 'Actualisation' : error || !data ? 'Indisponible' : String(data.sessionCount) }}>{loading ? '…' : error || !data ? '—' : data.sessionCount}</Text>
      <Text style={styles.caption}>{loading ? 'Actualisation…' : error ? 'Bilan indisponible' : data?.sessionCount ? `séance${data.sessionCount > 1 ? 's' : ''} terminée${data.sessionCount > 1 ? 's' : ''}` : 'Aucune séance cette semaine.'}</Text>
      {!loading && !error && data && <View style={styles.week}>
        {data.days.map(day => <View key={day.key} accessible accessibilityLabel={`${day.key} : ${day.count} séance${day.count > 1 ? 's' : ''} terminée${day.count > 1 ? 's' : ''}${day.today ? ', aujourd’hui' : ''}`} style={{ alignItems: 'center', gap: 4 }}>
          <View style={[styles.marker, day.count > 0 && styles.trained, day.today && styles.today]} /><Text style={styles.day}>{day.label}</Text>
        </View>)}
      </View>}
    </LinearGradient>
    <Pressable accessibilityRole="button" accessibilityLabel="Consulter ma progression par exercice" onPress={() => router.push('/history/exercises')} style={{ flex: 1 }}>
      <LinearGradient colors={['#0b252d', '#091824']} style={[styles.card, { flex: 1 }]}>
        <Text style={styles.label}>Progression</Text><Text style={styles.progress}>Vos courbes</Text>
        <Text style={styles.caption}>{!loading && !error && data?.totalCompleted === 0 ? 'Après votre première séance terminée.' : 'Comparez vos performances par exercice.'}</Text>
        <Ionicons name="stats-chart-outline" size={22} color="#45d4bf" />
      </LinearGradient>
    </Pressable>
  </View>
    {error && <Pressable accessibilityRole="button" accessibilityLabel="Actualiser les statistiques" onPress={activity.retry} style={{ minHeight: 44, justifyContent: 'center' }}>
      <Text style={{ color: colors.cyan, fontSize: 12 }}>Statistiques indisponibles · Réessayer</Text></Pressable>}
  </View>;
}
const styles = StyleSheet.create({
  stats: { flexDirection: 'row', gap: 12 },
  card: { flex: 1, minWidth: 0, borderColor: '#204253', borderWidth: 1, borderRadius: 18, padding: 14, gap: 4 },
  label: { color: '#bed2e0', fontSize: 12, lineHeight: 18 },
  value: { color: '#2bbcff', fontSize: 34, fontWeight: '600', lineHeight: 37 },
  progress: { color: '#45d4bf', fontSize: 19, fontWeight: '600', lineHeight: 27, marginVertical: 5 },
  caption: { color: '#9eb6c9', fontSize: 11, lineHeight: 16, minHeight: 32 },
  week: { flexDirection: 'row', justifyContent: 'space-between', gap: 2, marginTop: 4 },
  marker: { width: 10, height: 10, borderRadius: 5, borderWidth: 1, borderColor: '#416073', backgroundColor: '#132e40' },
  trained: { backgroundColor: colors.blue, borderColor: colors.cyan }, today: { borderWidth: 2, borderColor: colors.text },
  day: { color: colors.muted, fontSize: 9, lineHeight: 12 },
});
