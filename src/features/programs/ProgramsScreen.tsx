import Ionicons from '@expo/vector-icons/Ionicons';
import { router, useFocusEffect } from 'expo-router';
import { useCallback } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useUniverseIsActive, useUniverseNavigation } from '../../navigation/UniverseContext';
import { UniverseScreen } from '../../navigation/UniverseScreen';
import { useLogbook } from '../../store/LogbookProvider';
import { Button, Card, colors, EmptyState, Heading } from '../../ui';
import { featureStyles, LoadState, LocalNotice, RefreshNotice } from './shared';
import { ResumeSessionCard } from '../sessions/ResumeSessionCard';

export default function ProgramsScreen() {
  const { programs, loading, hasLoaded, error, refresh } = useLogbook();
  const { goTo } = useUniverseNavigation();
  const active = useUniverseIsActive();
  useFocusEffect(useCallback(() => { if (active) void refresh(); }, [active, refresh]));

  return <UniverseScreen testID="programs-scroll">
    <Heading title="Programmes" subtitle="Musculation"
      action={<Button label="Accueil" icon="home-outline" variant="ghost" onPress={() => goTo('home')} />} />
    <View style={featureStyles.sections}>
      <ResumeSessionCard active={active} />
      <Button label="Historique des entraînements" icon="stats-chart-outline" variant="ghost" onPress={() => router.push('/history')} />
      <Button label="Bibliothèque d’exercices" icon="barbell-outline" variant="ghost" onPress={() => router.push('/exercises')} />
      <Button label="Paramètres" icon="settings-outline" variant="ghost" onPress={() => router.push('/settings')} />
      <Pressable accessibilityRole="button" accessibilityLabel="Ouvrir le mannequin 3D" onPress={() => router.push('/muscle-viewer')}
        style={({ pressed }) => [previewStyles.link, pressed && { opacity: 0.7 }]}>
        <Ionicons name="cube-outline" color={colors.cyan} size={17} />
        <Text style={previewStyles.text}>Mannequin 3D</Text><Text style={previewStyles.tag}>Aperçu</Text>
      </Pressable>
      <RefreshNotice refreshError={hasLoaded ? error : null} retry={() => { void refresh(); }} />
      {!hasLoaded && (loading || error) ? <LoadState loading={loading} error={error} retry={() => { void refresh(); }} /> :
        programs.length === 0 ? <Card>
          <EmptyState icon="barbell-outline" title="Un programme à votre image"
            description="Vous n’avez pas encore de programme. Créez le vôtre et organisez vos premières séances." />
        </Card> : <View style={featureStyles.cards}>
          {programs.map(program => <Card key={program.id}>
            <Pressable accessibilityRole="button" accessibilityLabel={`Ouvrir le programme ${program.name}`}
              onPress={() => router.push({ pathname: '/programs/[id]', params: { id: program.id } })}
              style={featureStyles.row}>
              <View style={featureStyles.icon}><Ionicons name="barbell" color={colors.cyan} size={27} /></View>
              <View style={featureStyles.grow}>
                <Text style={featureStyles.title}>{program.name}</Text>
                {program.description ? <Text style={featureStyles.body} numberOfLines={2}>{program.description}</Text> : null}
                <Text style={featureStyles.meta}>{program.workoutCount} séance{program.workoutCount > 1 ? 's' : ''}</Text>
              </View>
              <Ionicons name="chevron-forward" color={colors.muted} size={19} />
            </Pressable>
          </Card>)}
        </View>}
      <Button label="Créer un programme" icon="add" onPress={() => router.push('/programs/new')} disabled={loading || !!error} />
      <Text style={featureStyles.body}>Depuis le haut de la liste, glissez vers le bas pour revenir à l’accueil.</Text>
      <LocalNotice />
    </View>
  </UniverseScreen>;
}

const previewStyles = StyleSheet.create({
  link: { minHeight: 44, alignSelf: 'center', flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 12 },
  text: { color: colors.cyan, fontSize: 14 }, tag: { color: colors.muted, fontSize: 11 },
});
