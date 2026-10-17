import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useCallback, useState } from 'react';
import { Pressable, Text, View } from 'react-native';
import { availableAlternatives, exerciseGuide, loadExplanation } from '../../data/exerciseGuides';
import type { ExerciseCatalogItem } from '../../domain/training';
import { weightModeLabel } from '../../domain/training';
import { useTraining } from '../../store/TrainingProvider';
import { useSessions } from '../../store/SessionProvider';
import { Button, Card, colors, Heading, Screen } from '../../ui';
import { FormError, LoadState, RefreshNotice, useFocusedData } from '../programs/shared';
import { replacementParams, replacementStep, useExerciseReplacement, type ReplacementContext } from '../sessions/useExerciseReplacement';
import { trainingStyles as s } from '../training/shared';
import { TrainingHelp } from './TrainingHelp';

export type ExerciseTab = 'description' | 'advice' | 'alternatives';
const tabs = [['description', 'Description'], ['advice', 'Conseils'], ['alternatives', 'Alternatives']] as const;

function Paragraphs({ title, items }: { title: string; items: readonly string[] }) {
  return <Card><Text style={s.eyebrow}>{title}</Text>{items.map((text, index) => <Text key={index} style={s.body}>{index + 1}. {text}</Text>)}</Card>;
}

function Alternatives({ exercise, context }: { exercise: ExerciseCatalogItem; context?: ReplacementContext }) {
  const repository = useTraining();
  const catalog = useFocusedData(useCallback(() => repository.listCatalog(), [repository]));
  const alternatives = catalog.data ? availableAlternatives(exercise, catalog.data) : [];
  return <View style={s.sections}>
    <Text style={s.body}>Ces pistes ne sont pas des équivalences exactes. Vérifiez le mouvement, le matériel et la charge avant de remplacer un exercice.</Text>
    <RefreshNotice {...catalog} />
    {catalog.loading || catalog.error ? <LoadState {...catalog} /> : alternatives.length ? alternatives.map(({ exercise: item, reason }) =>
      <Pressable key={item.id} accessibilityRole="button" accessibilityLabel={`Fiche de ${item.name}`}
        onPress={() => router.push({ pathname: '/exercises/[exerciseId]', params: { exerciseId: item.id, ...(context ? replacementParams(context) : {}) } })}>
        <Card style={{ padding: 16, gap: 8 }}><View style={s.row}><Ionicons name="swap-horizontal" color={colors.cyan} size={24} />
          <Text style={[s.title, s.grow]}>{item.name}</Text><Ionicons name="chevron-forward" color={colors.muted} size={20} /></View>
          <Text style={s.body}>{item.muscleGroup} · {item.equipment}</Text><Text style={s.meta}>{weightModeLabel[item.weightMode]}</Text><Text style={s.body}>{reason}</Text>
        </Card>
      </Pressable>) : <Card><Text style={s.title}>Aucune alternative renseignée</Text><Text style={s.body}>Aucune alternative disponible n’est explicitement associée à cet exercice.{context ? ' La recherche de remplacement permet de consulter toute votre bibliothèque.' : ''}</Text></Card>}
  </View>;
}

/** A library sheet without explicit training context performs no session lookup. */
function ReplacementPanel({ context, exercise }: { context: ReplacementContext; exercise: ExerciseCatalogItem }) {
  const repository = useSessions();
  const data = useFocusedData(useCallback(() => context.sessionId ? repository.getSession(context.sessionId) : Promise.resolve(null), [repository, context.sessionId]));
  const operation = useExerciseReplacement(repository, context);
  const current = replacementStep(data.data, context);
  return <View style={s.sections}>
    <RefreshNotice {...data} />
    {data.loading ? <LoadState {...data} /> : <Card>
      <Text style={s.eyebrow}>CET ENTRAÎNEMENT UNIQUEMENT</Text>
      {data.error ? <><Text style={s.body}>Impossible de vérifier le contexte de remplacement.</Text><Button label="Réessayer le remplacement" variant="secondary" onPress={data.retry} /></>
        : !current ? <Text style={s.body}>Ce remplacement n’est plus disponible. Revenez à la série active ; un repos doit être terminé manuellement. Aucune donnée n’a été modifiée.</Text>
        : current.exercise.sourceCatalogExerciseId === exercise.id ? <Text style={s.body}>C’est l’exercice de la série active. Consultez ses alternatives pour choisir un autre mouvement.</Text>
        : <><Text style={s.body}>Remplacer « {current.exercise.name} » pour les séries restantes. Le programme restera inchangé.</Text>
          <Button label="Remplacer pour cette séance" icon="swap-horizontal" loading={operation.busy} disabled={!!data.refreshError}
            onPress={() => operation.choose(exercise)} /></>}
      <FormError message={operation.error} />
      {operation.error && <Button label="Actualiser le remplacement" variant="secondary" disabled={operation.busy} onPress={() => { operation.setError(null); data.retry(); }} />}
      {!!context.sessionId && <Button label="Revenir à la séance" variant="ghost" disabled={operation.busy}
        onPress={() => router.dismissTo({ pathname: '/sessions/[sessionId]', params: { sessionId: context.sessionId! } })} />}
    </Card>}
  </View>;
}

export function ExerciseDetail({ exerciseId, replacementContext, initialTab = 'description' }: { exerciseId?: string; replacementContext?: ReplacementContext; initialTab?: ExerciseTab }) {
  const repository = useTraining();
  const data = useFocusedData(useCallback(() => exerciseId ? repository.getCatalogExercise(exerciseId) : Promise.resolve(null), [repository, exerciseId]));
  const [selection, setSelection] = useState({ exerciseId, tab: initialTab });
  const tab = selection.exerciseId === exerciseId ? selection.tab : initialTab;
  const exercise = data.data;
  const guide = exercise ? exerciseGuide(exercise) : undefined;
  return <Screen compact><Heading title={exercise?.name ?? 'Fiche d’exercice'} subtitle={exercise?.isCustom ? 'Votre exercice personnalisé' : 'Catalogue Logbook'} back />
    <RefreshNotice {...data} />
    {data.loading || data.error || !exercise ? <LoadState loading={data.loading} error={data.error} retry={data.retry} /> : <View style={s.sections}>
      <Card><View style={s.row}><Ionicons name="barbell-outline" size={36} color={colors.cyan} /><View style={s.grow}>
        <Text style={s.title}>{exercise.muscleGroup}</Text><Text style={s.body}>{exercise.equipment}</Text></View></View>
        <Text style={s.meta}>{weightModeLabel[exercise.weightMode]}</Text>
      </Card>
      <View accessibilityRole="tablist" style={{ flexDirection: 'row', gap: 4 }}>
        {tabs.map(([key, title]) => <Pressable key={key} accessibilityRole="tab" accessibilityLabel={title} accessibilityState={{ selected: tab === key }}
          onPress={() => setSelection({ exerciseId, tab: key })}
          style={{ flex: 1, minHeight: 48, paddingHorizontal: 4, paddingVertical: 12, borderRadius: 12, borderWidth: 1, borderColor: tab === key ? colors.blue : colors.border, backgroundColor: tab === key ? '#10365a' : colors.surface, justifyContent: 'center' }}>
          <Text style={[s.body, { textAlign: 'center', color: colors.text }]}>{title}</Text>
        </Pressable>)}
      </View>
      {tab === 'description' && <>
        {guide && <Card><Text style={s.eyebrow}>LE MOUVEMENT</Text><Text style={s.body}>{guide.description}</Text><Text style={s.title}>Position de départ</Text><Text style={s.body}>{guide.start}</Text></Card>}
        <Card><Text style={s.eyebrow}>{exercise.isCustom ? 'CONSIGNES PERSONNELLES' : 'CONSIGNES'}</Text><Text style={s.body}>{exercise.instructions || 'Aucune instruction renseignée pour cet exercice.'}</Text></Card>
        {guide && <Paragraphs title="RÉALISATION" items={guide.steps} />}
      </>}
      {tab === 'advice' && <>
        {guide ? <><Paragraphs title="REPÈRES UTILES" items={guide.tips} /><Paragraphs title="ERREURS À ÉVITER" items={guide.mistakes} /></> :
          <Card><Text style={s.title}>Aucun conseil spécifique renseigné</Text><Text style={s.body}>Vos consignes restent disponibles dans Description.{exercise.isCustom ? ' Vous pouvez les compléter en modifiant votre exercice personnalisé.' : ' Aucun contenu spécifique supplémentaire n’est disponible pour cette référence.'}</Text></Card>}
        <Card><Text style={s.eyebrow}>CHARGE À ENREGISTRER</Text><Text style={s.body}>{guide?.load ?? loadExplanation[exercise.weightMode]}</Text>
          <Text style={s.body}>La charge réelle reste facultative et n’est jamais déduite automatiquement de votre objectif.</Text></Card>
        <TrainingHelp />
      </>}
      {tab === 'alternatives' && <Alternatives exercise={exercise} context={replacementContext} />}
      {replacementContext && <ReplacementPanel key={`${exerciseId}:${replacementContext.sessionId}:${replacementContext.exerciseId}:${replacementContext.setId}`} context={replacementContext} exercise={exercise} />}
      <Button label="Voir mes performances" variant={replacementContext ? 'secondary' : 'primary'} icon="stats-chart-outline" onPress={() => router.push({ pathname: '/history/exercises/[exerciseId]', params: { exerciseId: exercise.id } })} />
      {exercise.isCustom && <Button label="Modifier mon exercice personnalisé" variant="secondary" icon="create-outline"
        onPress={() => router.push({ pathname: '/exercises/[exerciseId]/edit', params: { exerciseId: exercise.id, ...(replacementContext ? replacementParams(replacementContext) : {}) } })} />}
    </View>}
  </Screen>;
}
