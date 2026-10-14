# Tester M2 sur iPhone avec Expo Go

M0, M1.1 et M1.2 ont été validés sur votre iPhone. **M2 attend votre essai et votre validation.** Les tests automatiques ne remplacent pas les gestes, confirmations et saisies natifs.

## Récupérer la version dans PowerShell

Arrêter l’ancien serveur avec **Ctrl+C**. Ouvrir PowerShell dans votre dossier `logbook`, puis :

```powershell
git status
git fetch origin
git switch feat/m2-liberte-bilan
git pull --ff-only origin feat/m2-liberte-bilan
npm.cmd ci
npm.cmd start -- --clear
```

Si la branche n’existe pas localement, remplacer `git switch feat/m2-liberte-bilan` par :

```powershell
git switch --track origin/feat/m2-liberte-bilan
```

Puis reprendre à `git pull`. Si Git signale vos propres modifications ou refuse la mise à jour, conserver les fichiers et transmettre le message, sans les effacer. `npm.cmd` évite le blocage PowerShell de `npm.ps1`.

Utiliser Node.js 24, Git et le même Expo Go compatible avec Expo SDK 57 que pour M1.2. Aucun nouveau module natif n’a été ajouté. Scanner le nouveau QR code avec l’appareil photo de l’iPhone, sur le même Wi-Fi que l’ordinateur.

**Conserver Expo Go et les données du même projet.** `--clear` vide le cache du serveur, pas SQLite. La migration v4 garde vos programmes, configurations, performances et repos. Les anciens codes M1.1/M1.2 peuvent ensuite afficher « Stockage indisponible » parce qu’ils ne lisent pas la v4 : revenir à M2, sans effacer la base.

Si la connexion Wi-Fi locale ne fonctionne pas malgré l’accès au réseau local autorisé sur iOS, arrêter le serveur puis essayer :

```powershell
npx.cmd expo start --tunnel --clear
```

Un tunnel peut demander son outil et un accès Internet ; il ne change pas les données SQLite.

## Vérifications facultatives sur Windows

Après avoir démarré Expo au moins une fois sur M2 pour actualiser les routes, arrêter le serveur avec **Ctrl+C**, puis :

```powershell
npm.cmd run typecheck
npm.cmd test
npm.cmd run export:ios
```

L’export vérifie le JavaScript et les ressources iOS, sans compiler une application native installable.

Relancer ensuite `npm.cmd start -- --clear` pour les essais sur iPhone.

## 1. Vérifier la conservation M0/M1

Retrouver vos programmes, séances, exercices, séries, charges, plages de répétitions, RIR et repos individuels. Vérifier **Terminer**, **Terminer la configuration**, **Démarrer la séance** et **Quitter et reprendre plus tard**.

Tester le swipe Accueil → Musculation, le retour depuis le haut de la liste et les boutons accessibles. Si une séance M1.2 était interrompue, sa reprise doit conserver progression, repos et pauses. Dans **Bilans de séances**, vérifier aussi vos entraînements M1.2 déjà terminés.

## 2. Préparer vos essais M2

Utiliser une séance personnelle avec plusieurs exercices et au moins deux séries pour le premier, afin d’essayer un remplacement partiel. Un autre exercice situé plus loin permet de tester le changement d’ordre. Si vous préférez isoler les essais, créez vous-même un programme de test ; aucun programme de démonstration n’est installé.

Une durée de repos courte, par exemple 10 secondes choisies par vous, facilite les essais. Chaque série garde son propre repos. Les données non validées ne constituent pas une performance.

## 3. Annuler puis confirmer un remplacement

Sur la série active, ouvrir « … », puis **Remplacer cet exercice**. Vérifier le nom actuel, le nombre de séries restantes et la recherche par nom, muscle ou matériel. Retrouver un exercice personnalisé existant.

Choisir une alternative. La confirmation doit nommer les deux exercices et annoncer l’effacement des charges cibles restantes. Appuyer sur **Annuler** : l’exercice, ses objectifs et le programme doivent rester identiques.

Refaire le choix et confirmer **Remplacer**. Le retour affiche le vrai nom et le mode de charge de l’alternative. Les champs réels sont vides, même si vous aviez saisi une valeur sans la valider avant le remplacement. Les charges cibles sont à adapter ; répétitions, RIR, repos et étiquettes restent disponibles. Utiliser « … » → **Modifier les objectifs de la série** → **Cette séance** si nécessaire.

Faire plusieurs appuis rapides : une seule substitution doit être sauvegardée. Une erreur doit rester visible avec possibilité de réessayer/actualiser, sans fermeture automatique.

## 4. Remplacer après une série déjà réalisée

Valider une série sur l’exercice initial, puis terminer son repos manuellement. À la série suivante, remplacer l’exercice. Vérifier que seul le nombre de séries restantes est concerné.

Valider les séries restantes sur l’alternative avec leurs résultats propres. À la fin, le bilan doit montrer **l’exercice initial pour les séries réellement faites dessus**, puis **l’alternative pour ses propres performances**. Une charge à la barre ne doit pas devenir une charge par haltère.

Vous pouvez également essayer deux remplacements successifs avant de valider : le bilan montrera uniquement les exercices effectivement utilisés, avec la provenance de l’exercice programmé initial.

## 5. Choisir un exercice plus loin et retrouver celui qui a été sauté

Ouvrir « … » → **Choisir le prochain exercice**. Chaque carte indique un nom, un nombre de séries restantes et un état. Les exercices terminés ne doivent pas apparaître.

Choisir un exercice situé plus loin. Une seule série de cet exercice doit apparaître, sans validation fictive de celui temporairement sauté. Terminer ses séries, puis poursuivre : l’application reprend l’ordre prévu parmi les exercices non terminés.

Si vous avez quitté un exercice partiellement réalisé, le retrouver dans la grille avec seulement ses séries restantes. Toutes les séries de la séance doivent pouvoir être effectuées une fois, sans perte ni doublon. Les numéros du bilan reflètent l’ordre réel de validation, indépendamment des positions du programme.

Fermer Expo Go après un choix exceptionnel, puis rouvrir le même projet et **Reprendre la séance**. Le choix doit être retrouvé. Vérifier également la fermeture après un remplacement : identité, objectifs adaptés et séries validées doivent rester présents.

## 6. Choisir pendant un repos

Pendant le chronomètre, ouvrir « … » → **Choisir le prochain exercice**, puis toucher une carte. Une confirmation doit préciser que le repos continue et doit être terminé manuellement.

Annuler : aucun choix ne doit être enregistré. Confirmer : le retour reste sur **le même repos**, avec sa cible, son temps écoulé et sa pause éventuelle. L’expiration ne doit jamais changer d’écran automatiquement. Appuyer sur **Passer à la série suivante** ou **Repos terminé** pour enregistrer la durée réelle, puis ouvrir la série de l’exercice choisi.

Faire aussi l’essai pendant un repos mis en pause, puis après fermeture/réouverture : le décompte reste en pause, tandis que Repos réel inclut l’absence, selon la convention M1.2. Le remplacement est proposé seulement sur une série active, après le repos.

## 7. Vérifier le bilan

Terminer toutes les séries, puis **Terminer la séance**. Vérifier :

- **Durée totale** : de l’heure de démarrage à l’heure de fin, pauses et absences comprises. Elle n’est pas du temps d’effort pur.
- **Séries réalisées** : seulement celles réellement validées.
- **Tonnage enregistré** : charges réellement saisies × répétitions, jamais les objectifs.
- **RIR moyen** : seulement les RIR renseignés. Un RIR zéro compte ; une valeur vide ne compte pas.
- **Exercices réalisés** : vrais noms, résultats et modes de charge, y compris après remplacement partiel. Aucun exercice non réalisé ne doit figurer comme réalisé.

Le tonnage inclut les échauffements. Une charge par haltère est comptée une fois, sans doublement automatique. Seule une charge ajoutée saisie est utilisée pour un exercice au poids du corps : aucun poids corporel n’est inventé. Les séries sans charge sont exclues ; si toutes sont sans charge, « — » est affiché. Sans RIR, la moyenne affiche aussi « — ».

Exemple de calcul pour comparer à des valeurs que vous auriez volontairement saisies : 40 kg × 8 donne 320 kg ; 20 kg par haltère × 10 ajoute 200 kg ; une série sans charge ne rajoute pas un poids inventé. Le total enregistré est alors 520 kg. Avec des RIR 2, vide et 0, la moyenne est 1. Cet exemple n’est jamais ajouté automatiquement à l’application.

Toucher **Convention de calcul du tonnage** pour voir les limites et les contributions par mode. Vérifier le confort de lecture sur votre iPhone et le bouton de retour fixé en bas.

## 8. Retrouver le bilan et le programme initial

Quitter le bilan, fermer/reouvrir Expo Go, puis dans Musculation ouvrir **Bilans de séances**. Retrouver la séance terminée et le même bilan, sans créer un nouvel entraînement.

Démarrer à nouveau la séance programmée : l’exercice initial et ses charges prévues doivent revenir. Les réalisations précédentes restent distinctes.

Facultatif, uniquement sur un **programme de test que vous acceptez de supprimer** : supprimer le programme après un entraînement terminé. Son bilan doit rester accessible dans Bilans de séances. Ne supprimer aucune de vos données réelles pour cet essai.

## Limites et ordre des PR

Le remplacement conserve la structure restante ; il ne compose pas automatiquement un protocole adapté à l’alternative. Vérifier ses répétitions, RIR et repos. Le bilan contient une liste simple ; graphiques, filtres et historique avancé viendront avec M3. Aucun Cardio, 3D, volume musculaire, compte, cloud ou coach.

Le chronomètre et les limites sonores M1.2 restent identiques : alerte au premier plan selon volume/mode silencieux, sans promesse de notification application fermée ou iPhone verrouillé.

La PR M2 dépend de #3, qui dépend de #2. Fusionner seulement avec votre accord, dans l’ordre #2 → #3 → M2. Après les parents, changer la base de M2 vers `main`, revérifier diff et CI. M2 ne sera validée qu’après votre retour iPhone.

En cas de problème, noter l’écran, les actions, l’exercice initial/choisi, les séries déjà validées, le repos en cours et si Expo Go venait d’être fermé. Une réussite des tests automatiques ne remplace pas ces observations.
