import { Ionicons } from '@expo/vector-icons';
import { router, useLocalSearchParams } from 'expo-router';
import { useCallback } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { useLogbook } from '../../../src/store/LogbookProvider';
import { Button, Card, colors, Heading, Screen } from '../../../src/ui';
import { featureStyles, FormError, LoadState, LocalNotice, routeId, useFocusedData } from '../../../src/features/programs/shared';
import { useConfirmedDelete } from '../../../src/features/programs/useConfirmedDelete';

export default function ProgramScreen() {
  const params = useLocalSearchParams<{ id: string }>();
  const id = routeId(params.id);
  const { getProgram, deleteProgram } = useLogbook();
  const load = useCallback(() => id ? getProgram(id) : Promise.resolve(null), [getProgram, id]);
  const { data: program, loading, error, retry } = useFocusedData(load);
  const deletion = useConfirmedDelete({
    title: 'Supprimer le programme ?',
    message: `Le programme « ${program?.name ?? ''} » et toutes ses séances planifiées seront supprimés. Cette action est définitive.`,
    remove: async () => { if (program) await deleteProgram(program.id); },
    onDeleted: () => router.dismissTo({ pathname: '/', params: { universe: 'musculation' } }),
    failureMessage: 'Impossible de supprimer ce programme. Réessayez.',
  });

  return <Screen>
    <Heading title="Votre programme" back backDisabled={deletion.busy} />
    {loading || error || !program ? <LoadState loading={loading} error={error} retry={retry}
      missing="Ce programme n’est pas disponible. Retrouvez vos programmes depuis l’accueil." /> :
      <View style={featureStyles.sections}>
        <Card>
          <View style={styles.topline}>
            <Text style={featureStyles.eyebrow}>MUSCULATION</Text>
            <Ionicons name="barbell-outline" size={23} color={colors.cyan} />
          </View>
          <Text style={styles.name}>{program.name}</Text>
          <Text style={featureStyles.body}>{program.description || 'Un programme que vous construisez à votre rythme.'}</Text>
          <View style={styles.sessionCount}>
            <View style={featureStyles.icon}><Ionicons name="layers-outline" color={colors.cyan} size={23} /></View>
            <View>
              <Text style={styles.count}>{program.workoutCount}</Text>
              <Text style={featureStyles.body}>séance{program.workoutCount > 1 ? 's' : ''} dans ce programme</Text>
            </View>
          </View>
        </Card>
        <Card>
          <Text style={featureStyles.title}>Votre organisation</Text>
          <Text style={[featureStyles.body, styles.help]}>Ajoutez vos séances, donnez-leur un nom et retrouvez-les ici quand vous en avez besoin.</Text>
        </Card>
        <Button label="Voir les séances" icon="arrow-forward"
          disabled={deletion.busy} onPress={() => router.push({ pathname: '/programs/[id]/workouts', params: { id: program.id } })} />
        <Button label="Modifier le programme" icon="create-outline" variant="secondary"
          disabled={deletion.busy} onPress={() => router.push({ pathname: '/programs/[id]/edit', params: { id: program.id } })} />
        <FormError message={deletion.error} />
        <Button label="Supprimer le programme" icon="trash-outline" variant="danger"
          onPress={deletion.confirm} disabled={deletion.busy} loading={deletion.deleting} />
        <LocalNotice />
      </View>}
  </Screen>;
}

const styles = StyleSheet.create({
  topline: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 },
  name: { color: colors.text, fontSize: 29, fontWeight: '600', lineHeight: 36, marginBottom: 13 },
  sessionCount: { flexDirection: 'row', alignItems: 'center', gap: 14, marginTop: 26, paddingTop: 20, borderTopWidth: 1, borderColor: colors.border },
  count: { color: colors.cyan, fontSize: 26, lineHeight: 32, fontWeight: '600' },
  help: { marginTop: 8 },
});
