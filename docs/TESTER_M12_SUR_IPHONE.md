# Tester M1.2 sur votre iPhone avec Expo Go

M1.2 est prête à être essayée, **pas encore validée sur votre iPhone**. Les tests Linux ne remplacent pas votre essai du clavier, du son et des gestes natifs.

## Mise à jour dans PowerShell

Conserver le même dossier `logbook` et le même projet dans Expo Go. Arrêter le serveur précédent avec **Ctrl+C**. Ouvrir PowerShell dans le dossier du projet, puis :

```powershell
git status
git fetch origin
git switch feat/m1-entrainement
git pull --ff-only origin feat/m1-entrainement
npm.cmd ci
npm.cmd start -- --clear
```

Si le premier `git switch` indique que la branche n’existe pas localement, utiliser :

```powershell
git switch --track origin/feat/m1-entrainement
```

Puis reprendre à `git pull`. Si `git status` montre vos propres modifications ou si Git refuse de changer de branche, ne les effacez pas : conserver les fichiers et transmettre le message. `npm.cmd` évite le problème de politique PowerShell avec `npm.ps1`.

Il faut **Node.js 24**, Git et Expo Go compatible avec **Expo SDK 57**. L’ordinateur et l’iPhone doivent être sur le même Wi-Fi. Scanner le nouveau QR code avec l’appareil photo et ouvrir dans Expo Go. Accepter l’accès au réseau local si iOS le demande. Si Expo ouvre encore l’ancienne version, recharger le projet depuis le nouveau serveur.

`--clear` vide le cache du serveur, pas vos programmes. Ne désinstallez pas Expo Go et n’effacez pas ses données. La migration version 3 conserve programmes, séances, exercices et séries. Après cette migration, revenir au code M1.1 peut afficher « Stockage indisponible » : remettre M1.2, sans effacer la base.

Si une connexion Wi-Fi locale échoue malgré le serveur lancé et l’autorisation réseau local, arrêter le serveur puis essayer un tunnel :

```powershell
npx.cmd expo start --tunnel --clear
```

Le tunnel peut demander l’installation de son outil et un accès Internet. Il ne change pas les données SQLite.

## Vérifications facultatives sur l’ordinateur

Avant de relancer le serveur :

```powershell
npm.cmd run typecheck
npm.cmd test
npm.cmd run export:ios
```

L’export vérifie le JavaScript et les ressources iOS ; il ne fabrique pas une app installable.

## 1. Retrouver et terminer la configuration

Vérifier vos programmes M0 et vos exercices/séries M1.1 existants, leurs noms, ordre, charges, plages de répétitions, RIR et repos individuels. Tester les swipes Accueil → Musculation et Musculation → Accueil depuis le haut de la liste, ainsi que leurs alternatives accessibles.

Dans un exercice, modifier une série et sauvegarder. **Terminer** doit retourner à la vue des exercices. Dans cette vue, **Terminer la configuration** doit retourner aux séances du programme avec « Configuration enregistrée ». Les flèches de retour restent disponibles. Ces actions ne doivent afficher aucun entraînement réalisé.

## 2. Démarrer et saisir une seule série

Utiliser une séance personnelle avec au moins un exercice et une série par exercice. Pour tester trois repos différents, prévoir **quatre séries** avec 60, 120, 180 et 0 secondes : la dernière série n’a jamais de repos après elle. Pour vérifier rapidement l’expiration, vous pouvez ensuite utiliser des durées courtes de 5 ou 10 secondes dans une séance que vous créez vous-même.

Appuyer sur **Démarrer la séance**. Une seule série active doit apparaître, avec les objectifs séparés des trois champs réels. Les champs réels doivent être vides. Saisir une charge avec virgule, des répétitions et un RIR, puis **Valider la série**. Vérifier aussi qu’une charge et un RIR laissés vides sont acceptés, mais que les répétitions doivent être renseignées. Faire plusieurs appuis rapides : une seule validation doit être enregistrée.

Avec le clavier ouvert, vérifier que les champs sont accessibles par défilement et que le bouton bleu de validation reste utilisable. Les caractères trop longs, les nombres négatifs, les répétitions décimales et un RIR supérieur à 10 doivent être refusés sans quitter l’écran.

## 3. Contrôler les repos

Après chaque validation, vérifier que Repos prévu utilise bien la durée de **cette série** : 01:00, 02:00 puis 03:00. Repos réel augmente. Pause/lecture se trouve au centre du cercle.

- Appuyer sur **Passer à la série suivante** avant expiration : la prochaine série apparaît sans retour à une liste.
- Laisser expirer un repos court : le cercle devient orange/rouge, le temps affiche `+00:01`, `+00:02` et continue. L’écran reste ouvert et le bouton devient **Repos terminé**.
- Appuyer sur **Repos terminé** : le repos est sauvegardé et la prochaine série apparaît avec des champs réels vides.
- Mettre en pause, attendre, puis reprendre : le décompte reste figé pendant la pause, mais Repos réel continue. Cela conserve séparément temps chronologique et temps actif.

Il n’existe aucun bouton +15/+30 secondes. Si la série suivante appartient à un autre exercice, seul le repos explicitement programmé après la série est utilisé. Aucune durée de transition supplémentaire n’est ajoutée. La dernière série conduit directement à la fin manuelle, sans repos imposé.

## 4. Fermer et reprendre

Pendant un repos, noter Repos prévu et Repos réel. Quitter Expo Go ou fermer son processus, attendre, puis rouvrir le même projet. La carte **Reprendre la séance** doit retrouver les séries déjà validées et le repos, avec le temps recalculé. Il ne doit pas repartir de zéro.

Faire le même essai avec un minuteur **mis en pause** : le décompte doit rester en pause tandis que Repos réel inclut votre absence. Faire aussi l’essai après expiration, puis après un passage anticipé : retrouver le dépassement ou la bonne série suivante, sans doublons.

**Quitter et reprendre plus tard** permet de revenir aux programmes. La carte de reprise doit apparaître sur l’accueil et dans Musculation. Depuis une autre séance programmée, une séance active doit être proposée à la reprise au lieu de créer un second entraînement. Les champs non validés ne sont pas sauvegardés comme performances.

## 5. Modifier les objectifs en cours

Sur une série encore non validée, ouvrir le menu « … ». Vérifier la grille charge/répétitions/RIR/repos.

Avec **Cette séance**, modifier un objectif et enregistrer. Vérifier que le programme initial reste inchangé. Avec **Programme**, choisir explicitement cette option et enregistrer ; la série planifiée pour les futurs entraînements doit être modifiée. Les séries déjà réalisées doivent garder leurs valeurs.

Le bouton Annuler ne doit pas sauvegarder. Si le programme ou la série prévue a été supprimé entre-temps, Programme doit afficher une erreur sans fermer l’éditeur ; Cette séance reste possible. La reprise fonctionne même si le programme d’origine a été supprimé. Tester les suppressions uniquement sur vos données de test choisies.

## 6. Terminer un véritable entraînement

Valider toutes les séries, puis appuyer sur **Terminer la séance**. La confirmation doit indiquer les séries réellement enregistrées, sans faux tonnage ni graphique. La carte de reprise disparaît. Démarrer à nouveau la même séance crée un nouvel entraînement indépendant ; le précédent reste conservé dans SQLite. Il n’y a pas encore d’écran d’historique complet pour le consulter : cela viendra dans les prochains jalons.

## Son et limites iOS

Avec l’application au premier plan, volume audible et mode silencieux désactivé, laisser expirer un repos court. Une courte alerte locale doit être essayée. Elle reste prévue lorsque vous êtes sur un autre écran de Logbook pendant ce repos.

**Aucune sonnerie ou notification écran verrouillé / app fermée n’est garantie ni implémentée.** Si le repos expire pendant l’absence, son temps est retrouvé au retour, sans alerte tardive. Le mode silencieux, le volume et une interruption audio peuvent empêcher le son ; le minuteur et les sauvegardes continuent. Ne changez pas manuellement l’heure du téléphone pendant les essais du chronomètre.

Les petits effets de flammes ne sont pas ajoutés ; le dépassement utilise le cercle et les accents orange/rouge. Remplacement temporaire d’exercice, sélection libre des exercices restants et bilan complet seront développés pendant M2.

## Ordre des PR

M1.2 est basée sur la PR #2 M1.1 tant qu’elle n’est pas fusionnée. Après validation, fusionner d’abord #2, puis changer la base de la PR M1.2 vers `main` et revérifier son diff/CI. M1.2 ne doit être fusionnée qu’après votre essai iPhone et votre accord.

En cas de problème, noter l’écran, les actions exactes, la durée programmée, l’état pause/lecture et si l’application était au premier plan. Les tests automatiques réussis ne remplacent pas ces observations.
