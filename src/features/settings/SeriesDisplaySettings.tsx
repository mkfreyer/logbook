import { Text, View } from 'react-native';
import { useSeriesPreferences } from '../../store/SeriesDisplayProvider';
import { Button, Card } from '../../ui';
import { Choice, sessionStyles as s } from '../sessions/shared';

export function SeriesDisplaySettings() {
  const preference = useSeriesPreferences();
  if (!preference) return null;
  return <Card style={{ gap: 10 }}><Text style={s.subtitle}>Affichage des séries</Text>
    <View accessibilityRole="radiogroup" accessibilityLabel="Affichage des séries" style={{ gap: 8 }}>
      {([{ mode: 'number', label: 'Numéro uniquement' }, { mode: 'name', label: 'Nom uniquement' }, { mode: 'both', label: 'Numéro et nom' }] as const)
        .map(item => <Choice key={item.mode} label={item.label} selected={preference.mode === item.mode}
          disabled={preference.loading || !!preference.error} onPress={() => { void preference.setMode(item.mode); }} />)}
    </View>
    <Text style={s.help}>Sans nom, le type de série ou son numéro reste affiché. Ce choix modifie seulement l’affichage, y compris dans les historiques.</Text>
    {preference.error && <><Text accessibilityRole="alert" style={s.help}>Le réglage d’affichage n’a pas pu être enregistré ou relu.</Text>
      <Button label="Réessayer l’affichage des séries" variant="secondary" disabled={preference.saving} onPress={preference.retry} /></>}
  </Card>;
}
