import { useState } from 'react';
import { Text, View } from 'react-native';
import { Button, Card } from '../../ui';
import { trainingStyles as s } from '../training/shared';

export const TRAINING_HELP = [
  ['Cible et résultat', 'Une cible est un objectif prévu. Seules vos valeurs réelles, saisies puis validées, deviennent une performance. Logbook ne les remplit pas à votre place.'],
  ['RIR', 'Le RIR estime les répétitions que vous pensez encore pouvoir faire à la fin de la série. RIR 2 signifie environ deux répétitions en réserve. Ce champ reste facultatif.'],
  ['Types de séries', 'Échauffement : préparation progressive. Travail : série prévue pour votre entraînement. Top set : série principale que vous identifiez. Back-off : série généralement plus légère après une série principale. Aucun type ni pourcentage n’est obligatoire.'],
  ['Comment noter la charge ?', 'Par haltère : notez le poids d’un seul haltère, sans doubler. Charge ajoutée : notez seulement le lest, sans votre poids corporel. Charge totale : poids de la barre et des disques, ou indication de la machine. Une charge vide ne signifie pas 0 kg.'],
  ['Remplacer ou modifier le programme ?', 'Un remplacement pendant l’entraînement concerne cette séance uniquement. Modifier un exercice dans le programme change la préparation des séances futures, sans réécrire les performances passées.'],
  ['Passer ou supprimer ?', 'Passer une série la met de côté pour aujourd’hui ; vous pouvez la réintégrer. Cela ne la supprime pas du programme. Supprimer une série prévue change votre configuration future.'],
] as const;

/** Optional and local: never blocks the active-set form or saves preferences. */
export function TrainingHelp() {
  const [open, setOpen] = useState(false);
  return <View style={{ gap: 12 }}>
    <Button label={open ? 'Fermer l’aide entraînement' : 'Comprendre les termes d’entraînement'} variant="ghost" icon="help-circle-outline" onPress={() => setOpen(value => !value)} />
    {open && <Card>{TRAINING_HELP.map(([title, text]) => <View key={title} style={{ gap: 5 }}>
      <Text style={s.title}>{title}</Text><Text style={s.body}>{text}</Text>
    </View>)}</Card>}
  </View>;
}
