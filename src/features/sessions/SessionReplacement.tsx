import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useCallback, useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { useTraining } from '../../store/TrainingProvider';
import { Button, Card, colors, EmptyState, Heading, Screen } from '../../ui';
import { FormError, LoadState, RefreshNotice, useFocusedData } from '../programs/shared';
import { sessionStyles as s, useSessionData } from './shared';
import { replacementParams, replacementStep, useExerciseReplacement } from './useExerciseReplacement';

const searchable = (text: string) => text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('fr-FR');

export function SessionReplacement({ sessionId, exerciseId, setId }: { sessionId?: string; exerciseId?: string; setId?: string }) {
  const data = useSessionData(sessionId), training = useTraining();
  const catalog = useFocusedData(useCallback(() => training.listCatalog(), [training]));
  const context = { sessionId, exerciseId, setId };
  const operation = useExerciseReplacement(data.repository, context);
  const [query, setQuery] = useState('');
  const current = replacementStep(data.session, context);
  const busy = operation.busy;
  const back = () => { if (!busy && sessionId) router.dismissTo({ pathname: '/sessions/[sessionId]', params: { sessionId } }); };
  const terms = searchable(query.trim()).split(/\s+/).filter(Boolean);
  const items = (catalog.data ?? []).filter(item => item.id !== current?.exercise.sourceCatalogExerciseId &&
    terms.every(term => searchable(`${item.name} ${item.muscleGroup} ${item.equipment}`).includes(term)));
  const done = new Set(data.session?.performances.map(item => item.sessionSetId));
  const remainingCount = data.session?.sets.filter(item => item.sessionExerciseId === exerciseId && !item.skippedAt && !done.has(item.id)).length ?? 0;
  const performedCount = data.session?.sets.filter(item => item.sessionExerciseId === exerciseId && done.has(item.id)).length ?? 0;
  return <Screen compact>
    <Heading title="Remplacer l’exercice" subtitle="Uniquement cet entraînement" back backDisabled={busy} onBack={back} />
    <RefreshNotice {...catalog} />
    {data.loading || catalog.loading || data.error || catalog.error || !current ? <LoadState
      loading={data.loading || catalog.loading} error={data.error ?? catalog.error}
      retry={() => { data.retry(); catalog.retry(); }} missing="Revenez à la série active pour remplacer son exercice. Le repos doit être terminé manuellement." /> : <View style={s.sections}>
      <Card style={{ gap: 8 }}><Text style={s.eyebrow}>EXERCICE ACTUEL</Text><Text style={s.subtitle}>{current.exercise.name}</Text>
        <Button label="Fiche et alternatives de l’exercice" variant="ghost" disabled={busy} icon="information-circle-outline"
          onPress={() => router.push({ pathname: '/exercises/[exerciseId]', params: { exerciseId: current.exercise.sourceCatalogExerciseId, tab: 'alternatives', ...replacementParams(context) } })} />
        <Text style={s.body}>{remainingCount} série{remainingCount > 1 ? 's' : ''} restante{remainingCount > 1 ? 's' : ''}{performedCount ? ` · ${performedCount} déjà validée${performedCount > 1 ? 's' : ''}` : ''}</Text>
      </Card>
      <View style={styles.search}><Ionicons name="search-outline" color={colors.muted} size={21} />
        <TextInput accessibilityLabel="Rechercher un remplacement" value={query} onChangeText={setQuery} editable={!busy}
          placeholder="Nom, muscle ou matériel…" placeholderTextColor={colors.muted} autoCapitalize="none" autoCorrect={false} style={styles.input} />
      </View>
      <Text style={s.help}>Choisissez une alternative. Les charges cibles seront à adapter au nouvel exercice.</Text>
      <FormError message={operation.error} />
      {operation.error && <Button label="Actualiser le remplacement" variant="secondary" disabled={busy} onPress={() => { operation.setError(null); data.retry(); catalog.retry(); }} />}
      {items.length === 0 ? <Card><EmptyState icon="search-outline" title="Aucun exercice trouvé" description="Essayez un autre nom ou un autre matériel." /></Card> : items.map(item =>
        <View key={item.id} style={styles.item}><Pressable key={item.id} accessibilityRole="button" accessibilityLabel={`Remplacer par ${item.name}`} disabled={busy}
          accessibilityState={{ disabled: busy }} onPress={() => operation.choose(item)} style={({ pressed }) => [{ flex: 1, flexDirection: 'row', alignItems: 'center', gap: 12 }, pressed && { opacity: 0.7 }]}>
          <View style={styles.icon}><Ionicons name="barbell-outline" color={colors.cyan} size={25} /></View>
          <View style={{ flex: 1 }}><Text style={s.subtitle}>{item.name}</Text><Text style={s.body}>{item.muscleGroup} · {item.equipment}</Text>
            {item.isCustom && <Text style={s.help}>Exercice personnalisé</Text>}</View>
          <Ionicons name="chevron-forward" color={colors.muted} size={19} />
        </Pressable><Pressable accessibilityRole="button" accessibilityLabel={`Fiche de ${item.name}`} disabled={busy}
          onPress={() => router.push({ pathname: '/exercises/[exerciseId]', params: { exerciseId: item.id, ...replacementParams(context) } })}
          style={{ minWidth: 44, minHeight: 44, alignItems: 'center', justifyContent: 'center' }}><Ionicons name="information-circle-outline" color={colors.cyan} size={24} /></Pressable></View>)}
      <Button label="Annuler le remplacement" variant="ghost" disabled={busy} onPress={back} />
    </View>}
  </Screen>;
}

const styles = StyleSheet.create({
  search: { flexDirection: 'row', gap: 10, alignItems: 'center', paddingHorizontal: 14, borderRadius: 16, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.surface },
  input: { flex: 1, minWidth: 0, minHeight: 54, paddingVertical: 14, color: colors.text, fontSize: 16 },
  item: { flexDirection: 'row', gap: 12, alignItems: 'center', padding: 14, borderRadius: 18, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.surface },
  icon: { width: 44, height: 44, borderRadius: 14, backgroundColor: '#153e5a', alignItems: 'center', justifyContent: 'center' },
});
