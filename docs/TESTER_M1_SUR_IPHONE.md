# Tester M1.1 sur votre iPhone

Cette version ajoute la **préparation des exercices et des séries**. Elle conserve le projet Expo et les données M0 déjà présents sur votre iPhone. Vous ne démarrez pas encore un entraînement : vous configurez ses objectifs pour vérifier cette partie avant M1.2.

## Mettre à jour votre dossier Logbook

1. Dans le terminal où l'ancien serveur tourne, appuyer sur **Ctrl+C**.
2. Ouvrir votre dossier existant `logbook` dans l'Explorateur Windows, puis faire un clic droit dans un espace vide et choisir **Ouvrir dans le Terminal**. Le terminal doit être dans ce dossier, pas dans un nouveau projet.
3. Vérifier vos fichiers :

```powershell
git status --short
```

Si rien ne s'affiche, continuer. Si des fichiers modifiés apparaissent, conserver vos modifications avant de changer de branche, par exemple dans une copie séparée. Ne pas utiliser `git reset --hard` pour les effacer. En cas de doute, garder les fichiers et demander de l'aide avec les noms affichés.

4. Récupérer les branches et ouvrir celle de M1.1, en attendant la fin de chaque commande :

```powershell
git fetch origin
git switch --track origin/feat/m1-exercices-series
```

La seconde commande sert au **premier essai de cette branche sur votre ordinateur**. Si Git indique que `feat/m1-exercices-series` existe déjà, utiliser simplement :

```powershell
git switch feat/m1-exercices-series
```

5. Mettre à jour la branche, installer les bibliothèques et effectuer les vérifications :

```powershell
git pull --ff-only origin feat/m1-exercices-series
npm ci
npm run typecheck
npm test
npm run export:ios
npm start -- --clear
```

`npm test` utilise des données temporaires sur votre ordinateur, sans modifier celles de l'iPhone. `--clear` vide seulement le cache du serveur de développement : **il ne supprime pas votre base SQLite**. L'export iOS est un contrôle supplémentaire du code ; le QR code vient de `npm start`, pas de l'export.

Si Git signale des branches divergentes ou si une vérification échoue, conserver le message d'erreur et les fichiers locaux ; ne pas forcer la mise à jour. Si PowerShell refuse `npm` parce que l'exécution de scripts est désactivée, remplacer `npm` par `npm.cmd` dans ces commandes.

6. Laisser le terminal ouvert, connecter l'ordinateur et l'iPhone au même Wi-Fi, puis scanner le QR code avec l'application **Appareil photo** et ouvrir le même projet dans **Expo Go**. Il faut Node.js 24 sur l'ordinateur et Expo Go compatible avec Expo SDK 57 sur l'iPhone.

**Garder Expo Go installé et conserver ses données.** Il n'est pas nécessaire de créer un nouveau projet, de réinstaller l'application ni de posséder un abonnement développeur Apple pour cet essai.

## Vérifier d'abord les données M0

À la première ouverture, la migration ajoute les tables M1.1 à la base existante. Vérifier immédiatement que vos programmes, noms, notes et séances M0 sont toujours présents. Tester aussi le swipe montant depuis l'accueil, le retour descendant depuis le haut de Musculation et les boutons de navigation.

La migration passe la base locale en version 2. Si vous relancez ensuite l'ancien code M0 sur ce même projet, son écran pourra indiquer **Stockage indisponible** : il ne sait pas ouvrir cette version de base et ne l'efface pas. Pour poursuivre les essais, rester sur `feat/m1-exercices-series` et relancer son serveur.

## Composer une séance d'essai

Utiliser un programme temporaire si vous souhaitez garder vos préparations habituelles intactes.

1. Ouvrir un programme, puis **Voir les séances**. Créer une séance d'essai ou ouvrir une séance existante.
2. Une séance sans exercice doit afficher une invitation à la composer, sans performance ni programme préinstallé. Ouvrir **Ajouter un exercice**.
3. Rechercher un exercice réel dans la bibliothèque, par exemple un développé ou un tirage, puis l'ajouter. La recherche doit réduire la liste ; une recherche sans résultat doit proposer un état vide clair.
4. Ajouter un autre exercice, puis utiliser les flèches **Monter/Descendre** pour changer leur ordre. Vérifier les noms et l'ordre dans la vue d'ensemble.
5. Créer un exercice personnalisé avec un nom reconnaissable, son groupe musculaire et son matériel. Choisir sa convention de charge : totale, par haltère ou ajoutée. L'ajouter à la séance et vérifier qu'il peut être retrouvé dans la bibliothèque.
6. Modifier l'exercice prévu et vérifier que ses consignes sont conservées après sauvegarde.

Depuis la configuration de votre exercice personnalisé, **Modifier mon exercice personnalisé** permet de corriger son nom ou ses informations sans le recréer. La correction s'applique à sa fiche et aux séances prévues qui la référencent. Essayer aussi **Choisir un autre exercice** : l'occurrence garde ses séries, que vous pouvez ensuite ajuster au nouveau matériel.

Supprimer un exercice **de la séance** ne retire pas sa fiche de la bibliothèque. Si le même exercice est utilisé ailleurs, son autre utilisation doit rester présente.

## Configurer trois séries indépendantes

Ouvrir un exercice prévu et ajouter trois séries. Cet exemple est uniquement un parcours de test, pas un programme d'entraînement conseillé.

| Série | Étiquette et type | Répétitions cibles | Charge cible | RIR cible | Repos après la série |
| --- | --- | --- | --- | --- | --- |
| 1 | Échauffement | 8 exactement | Vide | Vide | 60 secondes |
| 2 | Top set | Plage 8 à 12 | `12,5` | 2 | 120 secondes |
| 3 | Back-off, avec une étiquette libre | 10 exactement | Facultative | Facultatif | 180 secondes |

Chaque série doit conserver **son propre repos** : aucun champ global à l'exercice ne doit remplacer ces trois valeurs. La charge est en kilogrammes selon la convention indiquée par l'exercice ; `12,5` et `12.5` doivent être acceptés. Laisser charge ou RIR vide ne doit pas produire une valeur imposée.

1. Revenir à la vue d'ensemble et vérifier les répétitions, charges, étiquettes et repos enregistrés.
2. Modifier uniquement la deuxième série. Vérifier que les valeurs des deux autres restent inchangées.
3. Déplacer la troisième série au-dessus de la deuxième avec la flèche. Ses valeurs et son repos doivent suivre la série ; aucune autre série ne doit être perdue.
4. Mettre le repos d'une série à `0` et vérifier le texte indiquant qu'aucun repos n'est prévu.
5. Essayer une saisie invalide, par exemple une plage minimum supérieure au maximum. L'écran doit expliquer le problème, rester ouvert et ne pas enregistrer la modification.

Le RIR cible est facultatif et limité à un entier de 0 à 10 dans cette version. Les répétitions et le repos sont des entiers ; le repos est saisi en **secondes**, sans minuteur déclenché par la sauvegarde. Le repos de la dernière série est seulement une valeur prévue enregistrée.

## Suppressions, fermeture et confort sur iPhone

Sur les données d'essai, vérifier ces comportements :

- Demander la suppression d'une série, puis choisir **Annuler** : elle doit rester présente. Confirmer ensuite la suppression : les autres séries et leur ordre doivent être conservés.
- Demander la suppression d'un exercice, puis annuler. Confirmer ensuite : seules cette occurrence et ses séries doivent disparaître ; les autres exercices et les autres séances restent présents.
- Fermer Expo Go complètement, puis rouvrir le même projet avec le serveur toujours lancé. Les exercices, séries, valeurs indépendantes, exercice personnalisé et positions doivent être retrouvés.
- Vérifier les formulaires avec le clavier ouvert : champs numériques, boutons de sauvegarde accessibles et défilement. Tester si possible une grande taille de texte dans les réglages iOS, ainsi que les confirmations natives de suppression.
- Retester une création, modification et suppression M0 sur un programme temporaire. Les swipes entre univers et les retours des sous-écrans doivent conserver leur comportement.

Ne supprimer vos vrais programmes que si vous le souhaitez : ces suppressions sont définitives dans la version actuelle. Il n'existe pas encore de sauvegarde iCloud ou d'export de restauration.

## Ce qui reste à venir

Les tests sur ordinateur et l'export iOS vérifient le code, les migrations et la persistance simulée. Ils ne prouvent pas le rendu, les claviers, les gestes ni les confirmations natives sur votre véritable iPhone. Ce parcours sert à valider précisément ces points et la conservation de votre base M0.

M1.2 ajoutera le démarrage réel, la saisie d'**une seule série active à la fois**, l'enregistrement progressif des performances, le repos prévu/réel et la reprise d'un entraînement interrompu. Il n'y a actuellement aucun chronomètre, historique avancé, mannequin 3D, Cardio ni bouton factice « Démarrer la séance ».

Si un problème apparaît, conserver le message exact, le nom de l'écran et les étapes qui l'ont provoqué. Ne pas effacer les données pour tenter de le résoudre.
