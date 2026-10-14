import { Ionicons } from '@expo/vector-icons';
import { router, useFocusEffect } from 'expo-router';
import { useCallback, useMemo } from 'react';
import { PanResponder, StyleSheet, Text, View } from 'react-native';

import { useLogbook } from '../src/store/LogbookProvider';
import { Button, Card, colors, Heading, Screen } from '../src/ui';
import { featureStyles, LoadState, LocalNotice } from '../src/features/programs/shared';

export default function HomeScreen() {
  const { programs, loading, error, refresh } = useLogbook();
  useFocusEffect(useCallback(() => { void refresh().catch(() => undefined); }, [refresh]));
  const exploreGesture = useMemo(() => PanResponder.create({
    onMoveShouldSetPanResponderCapture: (_, gesture) => gesture.dy < -10 && Math.abs(gesture.dy) > Math.abs(gesture.dx) * 1.5,
    onPanResponderTerminationRequest: () => false,
    onPanResponderRelease: (_, gesture) => {
      if (gesture.dy < -30 && Math.abs(gesture.dy) > Math.abs(gesture.dx) * 1.5) router.push('/programs');
    },
  }), []);

  return <Screen>
    <Heading title="Bonjour," subtitle="Votre entraînement, à votre rythme." />
    <View style={featureStyles.sections}>
      <View style={styles.brand}>
        <View style={styles.brandIcon}><Ionicons name="barbell" size={22} color={colors.cyan} /></View>
        <Text style={styles.brandName}>LOGBOOK</Text>
      </View>

      <Card>
        <View style={styles.sectionHeader}>
          <Text style={featureStyles.eyebrow}>VOTRE PROGRESSION</Text>
          <Ionicons name="trending-up-outline" size={22} color={colors.cyan} />
        </View>
        <Text style={styles.cardTitle}>Chaque séance compte.</Text>
        <Text style={featureStyles.body}>Votre progression apparaîtra ici après vos premiers entraînements.</Text>
      </Card>

      {loading || error ? <LoadState loading={loading} error={error} retry={() => { void refresh().catch(() => undefined); }} /> : <Card>
        <View style={styles.sectionHeader}>
          <Text style={featureStyles.eyebrow}>VOS PROGRAMMES</Text>
          <Ionicons name="albums-outline" size={22} color={colors.cyan} />
        </View>
        <Text style={styles.cardTitle}>{programs.length ? 'Prêt pour la suite ?' : 'Votre premier pas.'}</Text>
        <Text style={featureStyles.body}>{programs.length
          ? `${programs.length} programme${programs.length > 1 ? 's' : ''} à retrouver et à organiser selon vos envies.`
          : 'Créez votre programme, puis ajoutez les séances qui correspondent à vos objectifs.'}</Text>
        <View style={styles.buttonSpace}><Button
          label={programs.length ? 'Retrouver mes programmes' : 'Créer mon premier programme'}
          icon={programs.length ? 'arrow-forward' : 'add'}
          onPress={() => router.push(programs.length ? '/programs' : '/programs/new')} />
        </View>
      </Card>}

      <View style={styles.explore} {...exploreGesture.panHandlers}>
        <Ionicons name="chevron-up" size={17} color={colors.muted} />
        <Text style={styles.exploreText}>Glissez vers le haut pour explorer</Text>
      </View>
      <Button label="Musculation" icon="barbell-outline" variant="secondary" onPress={() => router.push('/programs')} />
      <LocalNotice />
    </View>
  </Screen>;
}

const styles = StyleSheet.create({
  brand: { flexDirection: 'row', alignItems: 'center', gap: 9, marginBottom: 3 },
  brandIcon: { width: 38, height: 38, borderRadius: 13, alignItems: 'center', justifyContent: 'center', backgroundColor: '#123453' },
  brandName: { color: colors.cyan, fontSize: 12, fontWeight: '700', letterSpacing: 3 },
  sectionHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 15 },
  cardTitle: { color: colors.text, fontSize: 24, fontWeight: '600', lineHeight: 31, marginBottom: 9 },
  buttonSpace: { marginTop: 23 },
  explore: { alignItems: 'center', justifyContent: 'center', gap: 3, minHeight: 64, marginBottom: -12 },
  exploreText: { color: colors.muted, fontSize: 12 },
});
