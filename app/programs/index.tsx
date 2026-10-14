import { Ionicons } from '@expo/vector-icons';
import { router, useFocusEffect } from 'expo-router';
import { useCallback } from 'react';
import { Pressable, Text, View } from 'react-native';

import { useLogbook } from '../../src/store/LogbookProvider';
import { Button, Card, colors, EmptyState, Heading, Screen } from '../../src/ui';
import { featureStyles, LoadState, LocalNotice } from '../../src/features/programs/shared';

export default function ProgramsScreen() {
  const { programs, loading, error, refresh } = useLogbook();
  useFocusEffect(useCallback(() => { void refresh().catch(() => undefined); }, [refresh]));

  return <Screen>
    <Heading title="Programmes" subtitle="Musculation" back />
    <View style={featureStyles.sections}>
      {loading || error ? <LoadState loading={loading} error={error} retry={() => { void refresh().catch(() => undefined); }} /> :
        programs.length === 0 ? <Card>
          <EmptyState icon="barbell-outline" title="Un programme à votre image"
            description="Vous n’avez pas encore de programme. Créez le vôtre et organisez vos premières séances." />
        </Card> : <View style={featureStyles.cards}>
          {programs.map((program) => <Card key={program.id}>
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
      <LocalNotice />
    </View>
  </Screen>;
}
