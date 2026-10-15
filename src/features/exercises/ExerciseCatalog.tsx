import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useCallback, useState } from 'react';
import { Pressable, Text, View } from 'react-native';
import { useTraining } from '../../store/TrainingProvider';
import { Button, Card, colors, EmptyState, Field, Heading, Screen } from '../../ui';
import { LoadState, RefreshNotice, useFocusedData } from '../programs/shared';
import { trainingStyles as s } from '../training/shared';

export function ExerciseCatalog() {
  const repository = useTraining();
  const data = useFocusedData(useCallback(() => repository.listCatalog(), [repository]));
  const [query, setQuery] = useState('');
  const normalize = (text: string) => text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('fr-FR');
  const terms = normalize(query.trim()).split(/\s+/).filter(Boolean);
  const found = data.data?.filter(item => terms.every(term => normalize(`${item.name} ${item.muscleGroup} ${item.equipment}`).includes(term)));
  return <Screen compact><Heading title="Bibliothèque d’exercices" subtitle="Vos références, distinctes des programmes" back />
    <Field label="Rechercher dans la bibliothèque" value={query} onChangeText={setQuery} placeholder="Nom, muscle, matériel" />
    <Button label="Créer un exercice personnalisé" variant="secondary" icon="add" onPress={() => router.push('/exercises/new')} />
    <RefreshNotice {...data} />
    {data.loading || data.error || !found ? <LoadState loading={data.loading} error={data.error} retry={data.retry} /> : found.length === 0 ? <Card>
      <EmptyState icon="search-outline" title="Aucun exercice trouvé" description="Essayez un autre nom, muscle ou matériel." /></Card> : <View style={s.cards}>
      {found.map(item => <Pressable key={item.id} accessibilityRole="button" accessibilityLabel={`Fiche de ${item.name}`}
        onPress={() => router.push({ pathname: '/exercises/[exerciseId]', params: { exerciseId: item.id } })}>
        <Card style={{ padding: 16 }}><View style={s.row}><Ionicons name="barbell-outline" color={colors.cyan} size={26} />
          <View style={s.grow}><Text style={s.title}>{item.name}</Text><Text style={s.body}>{item.muscleGroup} · {item.equipment}</Text>
            <Text style={s.meta}>{item.isCustom ? 'Exercice personnalisé' : 'Catalogue Logbook'}</Text></View><Ionicons name="chevron-forward" color={colors.muted} size={18} /></View></Card>
      </Pressable>)}
    </View>}
  </Screen>;
}
