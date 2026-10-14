import Ionicons from '@expo/vector-icons/Ionicons';
import { LinearGradient } from 'expo-linear-gradient';
import { router, useFocusEffect } from 'expo-router';
import { useCallback, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import { useUniverseIsActive, useUniverseNavigation } from '../../navigation/UniverseContext';
import { UniverseScreen } from '../../navigation/UniverseScreen';
import { useLogbook } from '../../store/LogbookProvider';
import { colors } from '../../ui';

function deviceDate() {
  const date = new Date().toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
  return date.charAt(0).toUpperCase() + date.slice(1);
}

/** The dashboard shows planning data only; completed sessions do not exist in M0. */
export default function HomeScreen() {
  const { programs, loading, error, refresh } = useLogbook();
  const { goTo } = useUniverseNavigation();
  const isActive = useUniverseIsActive();
  const [date, setDate] = useState(deviceDate);
  const firstProgram = programs[0];

  useFocusEffect(useCallback(() => {
    if (!isActive) return;
    setDate(deviceDate());
    void refresh().catch(() => undefined);
  }, [isActive, refresh]));

  return <UniverseScreen contentContainerStyle={styles.content} testID="home-universe">
    <View style={styles.header}>
      <View style={styles.headerText}>
        <Text style={styles.greeting}>Bonjour,</Text>
        <Text accessibilityRole="header" style={styles.headline}>À votre rythme.</Text>
        <Text style={styles.date}>{date}</Text>
      </View>
      <View style={styles.brandMark} accessibilityLabel="Logbook">
        <Ionicons name="barbell" size={24} color={colors.cyan} />
      </View>
    </View>

    <View style={styles.stats}>
      <LinearGradient colors={['#0d2432', '#091824']} style={styles.statCard}>
        <Text style={styles.statLabel}>Cette semaine</Text>
        <Text style={styles.statValue} accessibilityLabel="Aucune séance réalisée">—</Text>
        <Text style={styles.statCaption}>Aucune séance réalisée</Text>
        <View style={styles.weekMarkers} accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
          {Array.from({ length: 7 }, (_, day) => <View key={day} style={styles.weekMarker} />)}
        </View>
      </LinearGradient>
      <LinearGradient colors={['#0b252d', '#091824']} style={styles.statCard}>
        <Text style={styles.statLabel}>Progression</Text>
        <Text style={[styles.statValue, styles.progressValue]} accessibilityLabel="Aucune performance enregistrée">—</Text>
        <Text style={styles.statCaption}>Après vos premières séances</Text>
        <View style={styles.emptyProgress} accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
          <View style={styles.emptyProgressLine} />
          <View style={styles.emptyProgressDot} />
        </View>
      </LinearGradient>
    </View>

    <LinearGradient colors={['#0c2c42', '#0a1b2c', '#091724']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.programCard}>
      <View style={styles.programHeader}>
        <Text style={styles.eyebrow}>VOTRE PROGRAMME</Text>
        <Ionicons name="albums-outline" size={16} color={colors.cyan} />
      </View>
      {loading ? <View style={styles.status} accessibilityRole="progressbar" accessibilityLabel="Chargement des programmes">
        <ActivityIndicator color={colors.cyan} />
        <Text style={styles.body}>Chargement de vos programmes…</Text>
      </View> : error ? <View style={styles.status}>
        <Text style={styles.body} accessibilityRole="alert">{error}</Text>
        <Pressable accessibilityRole="button" accessibilityLabel="Réessayer" onPress={() => { void refresh().catch(() => undefined); }} style={({ pressed }) => [styles.programAction, pressed && styles.pressed]}>
          <Text style={styles.actionLabel}>Réessayer</Text>
          <Ionicons name="refresh" size={17} color={colors.text} />
        </Pressable>
      </View> : <>
        <View style={styles.programBody}>
          <View style={styles.programIllustration} accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
            <View style={styles.illustrationHalo} />
            <Ionicons name="barbell" size={54} color="#72ceff" />
          </View>
          <View style={styles.programText}>
            <Text style={styles.programTitle} numberOfLines={2}>{firstProgram?.name ?? 'Votre premier programme'}</Text>
            <Text style={styles.body}>{firstProgram
              ? `${firstProgram.workoutCount} séance${firstProgram.workoutCount > 1 ? 's' : ''} prévue${firstProgram.workoutCount > 1 ? 's' : ''} · à votre rythme`
              : 'Créez votre programme, puis organisez vos séances.'}</Text>
          </View>
        </View>
        <Pressable accessibilityRole="button" accessibilityLabel={firstProgram ? 'Retrouver mes programmes' : 'Créer mon premier programme'}
          onPress={() => firstProgram ? goTo('musculation') : router.push('/programs/new')}
          style={({ pressed }) => [styles.programAction, pressed && styles.pressed]}>
          <Ionicons name={firstProgram ? 'albums-outline' : 'add'} size={18} color={colors.text} />
          <Text style={styles.actionLabel}>{firstProgram ? 'Retrouver mes programmes' : 'Créer mon premier programme'}</Text>
          <Ionicons name="arrow-forward" size={17} color={colors.text} />
        </Pressable>
      </>}
    </LinearGradient>

    <View style={styles.footer}>
      <View style={styles.explore}>
        <View style={styles.exploreLine} />
        <View style={styles.exploreCopy}>
          <Ionicons name="chevron-up" size={15} color={colors.cyan} />
          <Text style={styles.exploreText}>Glissez vers le haut pour explorer</Text>
        </View>
        <View style={styles.exploreLine} />
      </View>

      <View style={styles.universes}>
        <Pressable accessibilityRole="button" accessibilityLabel="Musculation" accessibilityHint="Ouvre vos programmes avec une transition verticale."
          onPress={() => goTo('musculation')} style={({ pressed }) => [styles.universeButton, pressed && styles.pressed]}>
          <LinearGradient colors={['#0d4871', '#082537']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={[styles.universeGradient, styles.strength]}>
            <Ionicons name="barbell" size={26} color="#42c5ff" />
            <Text style={styles.universeLabel}>Musculation</Text>
          </LinearGradient>
        </Pressable>
        <Pressable disabled accessibilityRole="button" accessibilityLabel="Cardio, à venir" accessibilityState={{ disabled: true }} style={styles.universeButton}>
          <LinearGradient colors={['#0b312e', '#081e24']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={[styles.universeGradient, styles.cardio]}>
            <Ionicons name="walk-outline" size={25} color="#59b8a1" />
            <View style={styles.cardioText}>
              <Text style={[styles.universeLabel, styles.cardioLabel]}>Cardio</Text>
              <Text style={styles.comingSoon}>À venir</Text>
            </View>
          </LinearGradient>
        </Pressable>
      </View>
      <View style={styles.localNotice}>
        <Ionicons name="shield-checkmark-outline" size={13} color={colors.muted} />
        <Text style={styles.localNoticeText}>Sur cet iPhone · hors ligne</Text>
      </View>
    </View>
  </UniverseScreen>;
}

const styles = StyleSheet.create({
  content: { padding: 20, paddingTop: 14, paddingBottom: 16, gap: 18 },
  header: { flexDirection: 'row', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 },
  headerText: { flex: 1, minWidth: 0 },
  greeting: { color: '#c7d9ea', fontSize: 15, lineHeight: 21 },
  headline: { color: colors.text, fontSize: 30, fontWeight: '700', lineHeight: 37, letterSpacing: -0.8, marginTop: 1 },
  date: { color: '#9cb9cc', fontSize: 12, lineHeight: 18, marginTop: 4 },
  brandMark: { backgroundColor: '#103a57', borderColor: '#246186', borderWidth: 1, width: 42, height: 42, borderRadius: 15, alignItems: 'center', justifyContent: 'center', marginTop: 7 },
  stats: { flexDirection: 'row', gap: 12 },
  statCard: { flex: 1, minWidth: 0, borderColor: '#204253', borderWidth: 1, borderRadius: 18, padding: 14, gap: 3 },
  statLabel: { color: '#bed2e0', fontSize: 12, fontWeight: '500', lineHeight: 18 },
  statValue: { color: '#2bbcff', fontSize: 34, fontWeight: '600', lineHeight: 37, letterSpacing: -0.8 },
  progressValue: { color: '#45d4bf' },
  statCaption: { color: '#9eb6c9', fontSize: 11, lineHeight: 16, minHeight: 32 },
  weekMarkers: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 4, marginTop: 6, minHeight: 9 },
  weekMarker: { width: 8, height: 8, borderRadius: 4, borderWidth: 1, borderColor: '#416073', backgroundColor: '#132e40' },
  emptyProgress: { marginTop: 6, height: 9, flexDirection: 'row', alignItems: 'center' },
  emptyProgressLine: { flex: 1, height: 1, backgroundColor: '#315751' },
  emptyProgressDot: { width: 5, height: 5, borderRadius: 3, backgroundColor: '#49766e' },
  programCard: { borderColor: '#226e99', borderWidth: 1, borderRadius: 20, padding: 15, gap: 12, overflow: 'hidden' },
  programHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  eyebrow: { color: '#a7cee7', fontSize: 10, lineHeight: 14, fontWeight: '600', letterSpacing: 1.3 },
  programBody: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  programIllustration: { width: 65, height: 65, alignItems: 'center', justifyContent: 'center' },
  illustrationHalo: { position: 'absolute', width: 65, height: 65, borderRadius: 22, backgroundColor: '#113951', borderWidth: 1, borderColor: '#235575', transform: [{ rotate: '-12deg' }] },
  programText: { flex: 1, minWidth: 0, gap: 5 },
  programTitle: { color: colors.text, fontSize: 18, lineHeight: 23, fontWeight: '600', letterSpacing: -0.3 },
  body: { color: '#b2c9dc', fontSize: 12, lineHeight: 18, flexShrink: 1 },
  programAction: { minHeight: 44, paddingVertical: 11, paddingHorizontal: 11, backgroundColor: '#087dce', borderWidth: 1, borderColor: '#299ee4', borderRadius: 12, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7 },
  actionLabel: { color: colors.text, fontSize: 13, fontWeight: '600', lineHeight: 19, flexShrink: 1, textAlign: 'center' },
  status: { minHeight: 110, gap: 14, alignItems: 'center', justifyContent: 'center' },
  footer: { gap: 18, marginTop: 'auto' },
  explore: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: -6 },
  exploreLine: { flex: 1, height: 1, backgroundColor: '#203c4b' },
  exploreCopy: { alignItems: 'center', gap: 1, flexShrink: 1 },
  exploreText: { color: '#a4bece', fontSize: 10, lineHeight: 16, textAlign: 'center' },
  universes: { flexDirection: 'row', gap: 12 },
  universeButton: { flex: 1, minWidth: 0, borderRadius: 18 },
  universeGradient: { minHeight: 60, paddingHorizontal: 11, paddingVertical: 11, borderRadius: 18, borderWidth: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8 },
  strength: { borderColor: '#289ccb' },
  cardio: { borderColor: '#287769' },
  universeLabel: { color: '#edf7ff', fontSize: 13, lineHeight: 18, fontWeight: '600', flexShrink: 1 },
  cardioText: { gap: 1 },
  cardioLabel: { color: '#b6d3ca' },
  comingSoon: { color: '#7caa9c', fontSize: 10, lineHeight: 14 },
  localNotice: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 5, marginTop: -7 },
  localNoticeText: { color: '#7993a7', fontSize: 10, lineHeight: 15, flexShrink: 1 },
  pressed: { opacity: 0.75 },
});
