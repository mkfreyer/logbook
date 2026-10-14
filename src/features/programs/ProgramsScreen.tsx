import Ionicons from '@expo/vector-icons/Ionicons';
import { router, useFocusEffect } from 'expo-router';
import { useCallback } from 'react';
import { Pressable, Text, View } from 'react-native';
import { useUniverseIsActive, useUniverseNavigation } from '../../navigation/UniverseContext';
import { UniverseScreen } from '../../navigation/UniverseScreen';
import { useLogbook } from '../../store/LogbookProvider';
import { Button, Card, colors, EmptyState, Heading } from '../../ui';
import { featureStyles, LoadState, LocalNotice } from './shared';
import { ResumeSessionCard } from '../sessions/ResumeSessionCard';

export default function ProgramsScreen() {
  const { programs, loading, error, refresh } = useLogbook();
  const { goTo } = useUniverseNavigation();
  const active = useUniverseIsActive();
  useFocusEffect(useCallback(() => { if (active) void refresh(); }, [active, refresh]));

  return <UniverseScreen testID="programs-scroll">
    <Heading title="Programmes" subtitle="Musculation"
      action={<Button label="Accueil" icon="home-outline" variant="ghost" onPress={() => goTo('home')} />} />
    <View style={featureStyles.sections}>
      <ResumeSessionCard active={active} />
      {loading || error ? <LoadState loading={loading} error={error} retry={() => { void refresh(); }} /> :
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
