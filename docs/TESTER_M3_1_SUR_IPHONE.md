# Tester M3.1 sur iPhone avec Expo Go

Cette livraison concerne **M3.1 : les historiques et les premiers graphiques**. M0–M2 ont été validés sur votre iPhone. M3.1 attend votre nouveau test ; les contrôles Linux ne remplacent pas cette validation.

## 1. Récupérer la version sur Windows

Arrêtez Expo dans votre terminal avec **Ctrl+C**. Ouvrez PowerShell dans le dossier `logbook` existant. Gardez le même dossier et le même projet Expo Go pour retrouver vos données. Ne désinstallez pas Expo Go et n’effacez pas son stockage.

```powershell
git status
git fetch origin
git switch feat/m3-historiques-progression
git pull --ff-only origin feat/m3-historiques-progression
npm.cmd ci
npm.cmd start -- --clear
```

Si la branche n’existe pas encore sur votre ordinateur, remplacez la commande `git switch` par :

```powershell
git switch --track origin/feat/m3-historiques-progression
```

Si `git status` montre vos propres modifications et que Git refuse de changer de branche, conservez-les et transmettez le message ; n’utilisez pas de commande qui les efface.

Utilisez le même Expo Go compatible avec Expo SDK 57, sur le même réseau Wi-Fi que le PC. Scannez le nouveau QR code avec l’appareil photo de l’iPhone. `--clear` vide le cache de développement, pas SQLite. Si le réseau local empêche la connexion, arrêtez Expo puis essayez :

```powershell
npx.cmd expo start --tunnel --clear
```

**Base de données : aucun changement de version.** M3.1 utilise directement la base SQLite v4 de M2, avec tous vos programmes et résultats. Aucune remise à zéro, aucun programme de démonstration. Les anciennes branches M1.1/M1.2 restent incompatibles avec v4 ; ne revenez pas dessus pour tester vos données actuelles.

## 2. Vérifier d’abord ce qui fonctionnait déjà

- Retrouvez vos programmes, séances et configurations réelles.
- Testez le swipe montant Accueil → Musculation et descendant depuis le haut de Musculation. Le bouton Accueil reste utilisable.
- Ouvrez une préparation : **Terminer**, **Terminer la configuration** et **Démarrer la séance** doivent garder leur comportement.
- Si vous avez un entraînement en cours, reprenez-le. Il doit conserver sa série active, ses résultats validés et son repos. M3.1 ne modifie pas le chronomètre ni ses limites sonores Expo Go.
- Pendant l’effort : toujours une seule série à la fois, sans saisie automatique d’une ancienne valeur.

## 3. Historique général et programme

1. Dans Musculation, touchez **Historique des entraînements**.
2. Si aucune séance n’a encore été terminée, un état vide doit apparaître, avec accès aux programmes. Aucune performance ni courbe d’illustration ne doit s’afficher.
3. Si vos résultats sont anciens, choisissez **Tout**. Les périodes bornées comptent les jours locaux, aujourd’hui inclus, selon la date de fin de la séance.
4. Vérifiez nombre d’entraînements terminés, durée cumulée, tonnage enregistré et séries. Un entraînement encore en cours ne doit pas compter.
5. Touchez le graphique : sa légende doit changer vers un relevé réel. Essayez aussi **Précédent** et **Suivant** sous le graphique. Avec moins de deux valeurs renseignées, il explique que la comparaison est insuffisante.
6. Sélectionnez un programme dans **Par programme**. Sa page ne doit contenir que ses propres séances. Changez de période ; essayez les vues **Tonnage** et **Séries**.
7. La comparaison avec la période précédente indique ses résultats sans inventer un pourcentage d’amélioration. **Tout** n’a pas de période précédente arbitraire.
8. Si vous avez plus de 20 réalisations, essayez les pages **Suivante/Précédente**. Plus de 120 séances : le graphique annonce sa limite, mais les totaux et les pages couvrent toute la période filtrée.

Les programmes portant le même nom sont séparés : vérifiez la référence courte et leurs propres séances. Pour essayer une suppression, utilisez uniquement un programme de test que vous acceptez réellement de supprimer. Son historique doit rester accessible et porter la mention **programme supprimé**.

## 4. Détail d’un entraînement

1. Touchez une séance dans l’historique du programme ou général.
2. Comparez le détail au bilan déjà connu : mêmes résultats M2, même durée, même tonnage et même RIR moyen.
3. Vérifiez les numéros réels de validation, surtout si vous aviez changé l’ordre des exercices. Si vous avez fait A, B puis de nouveau A, les blocs doivent suivre A → B → A.
4. Un exercice remplacé doit apparaître avec son **vrai nom** ; un remplacement partiel conserve aussi les séries réellement effectuées sur l’exercice initial.
5. Ouvrez **Horaires et repos** sous une série. Vérifiez repos prévu, repos réellement écoulé et temps actif du minuteur. Le repos réel inclut les pauses ; aucun repos inutile n’est inventé après la dernière série.
6. Vérifiez l’absence de champs de modification et de bouton **Valider la série**. Consulter l’historique ne doit pas modifier vos données.
7. Le retour doit retrouver votre écran précédent. Le bilan montré immédiatement après une fin d’entraînement conserve son bouton **Retour aux programmes**.

## 5. Historique d’exercice et graphiques

1. Touchez le nom d’un exercice dans le détail, ou **Performances par exercice** depuis l’historique général.
2. Essayez la recherche par nom, muscle ou matériel, y compris sans accents.
3. Le développé barre et le développé haltères doivent avoir des historiques distincts. Le remplacement M2 ne doit jamais attribuer les résultats d’haltères à la barre.
4. Vérifiez les séries regroupées sous les dates et noms d’entraînement. Le tableau possède seulement **Série, Kg, Reps, RIR** : aucune colonne Date et pas de défilement horizontal à faire pour lire les valeurs.
5. Une charge ou un RIR absent doit afficher **—**, pas zéro. Un zéro réellement saisi doit rester zéro.
6. Essayez les graphiques **Charge**, **Répétitions**, **Tonnage** et les périodes. Chaque point doit correspondre à un entraînement terminé.
7. Pour charge/répétitions, la même série hors échauffement est choisie par entraînement : charge renseignée la plus élevée, puis répétitions, puis première validation en cas d’égalité. Sans charge renseignée, le plus grand nombre de répétitions. Une séance composée uniquement d’échauffements ne donne pas de point de travail.
8. Si cet exercice a eu plusieurs modes de charge, sélectionnez-les séparément. Les données par haltère, totales et ajoutées ne doivent jamais être combinées dans cette courbe.
9. Renommer un exercice personnalisé ou supprimer son programme ne doit pas supprimer ses performances. Un ancien nom peut rester visible sur ses anciennes séries ; leur identité reste la même.

Le tonnage utilise **charge réellement saisie × répétitions**, échauffements inclus. Pas de poids corporel estimé ni doublement des haltères. Par exemple, pour des résultats que vous avez volontairement saisis : 40 kg × 8 = 320 kg enregistrés ; 20 kg par haltère × 10 = 200 kg enregistrés selon la convention, sans doubler ; une charge absente ne contribue pas. Ces exemples ne sont pas ajoutés par l’application.

## 6. Réouverture, hors ligne et nouvelle fin de séance

- Fermez puis rouvrez le projet dans Expo Go. Retrouvez les mêmes séances, repos et résultats dans l’historique.
- Ouvrez une page, passez temporairement l’iPhone hors ligne et consultez ses résultats. Les calculs et lectures sont locaux. La première ouverture d’un projet de développement peut nécessiter Metro pour charger le JavaScript : ce n’est pas une synchronisation de vos données.
- Terminez un véritable entraînement puis revenez dans l’historique. Il doit apparaître une seule fois. Les nouvelles valeurs ne doivent pas remplacer les anciennes réalisations de la même séance programmée.
- Revenez depuis l’arrière-plan : l’écran actualise ses dates et sa période. Un entraînement terminé près de minuit suit sa **date locale de fin**, sans décalage UTC artificiel.
- Essayez la petite taille d’écran et la taille de texte que vous utilisez habituellement. Signalez les valeurs coupées, les boutons difficiles à atteindre ou les gestes qui gênent le défilement.

## 7. Vérifications facultatives sur le PC

Après avoir démarré Expo une première fois pour régénérer ses routes typées, arrêtez-le avec Ctrl+C :

```powershell
npm.cmd run typecheck
npm.cmd test
npm.cmd run export:ios
npm.cmd start -- --clear
```

L’export produit le JavaScript iOS et les ressources. Il ne fabrique pas une application App Store et ne teste pas UIKit sur iPhone.

## Ce qui reste pour les prochains sous-lots

**M3.2** : dernière performance comparable pendant l’entraînement, statistiques réelles d’accueil et fréquence, améliorations des fiches d’exercice.

**M3.3** : préférences utiles, étude de l’export local et stabilisation. Il n’existe pas encore d’export ou de restauration dans M3.1.

La refonte visuelle globale, la 3D, le Cardio, le cloud et le coach restent hors périmètre. Les PR restent en brouillon sans fusion automatique ; l’ordre prévu est #2 → #3 → #4 → M3.1, après votre accord.

Pour votre retour : indiquez le parcours testé, le résultat attendu, le résultat observé et le message exact en cas d’erreur. **M3.1 ne sera considéré validé qu’après votre test iPhone.**
