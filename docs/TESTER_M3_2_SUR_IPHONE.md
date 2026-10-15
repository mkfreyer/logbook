# Tester M3.2 sur iPhone avec Expo Go

M0 à M3.1 ont été validés par vous sur votre iPhone. Cette version ajoute **les derniers repères pendant l’effort, l’activité réelle de l’accueil et les fiches d’exercices**. Elle attend votre validation séparée sur appareil.

## 1. Mettre à jour depuis Windows

Arrêtez Expo avec **Ctrl+C**, puis ouvrez PowerShell dans le dossier `logbook` habituel :

```powershell
git status
git fetch origin
git switch feat/m3-performances-accueil
git pull --ff-only origin feat/m3-performances-accueil
npm.cmd ci
npm.cmd start -- --clear
```

Si la branche n’existe pas encore localement, remplacez `git switch` par :

```powershell
git switch --track origin/feat/m3-performances-accueil
```

Conservez vos modifications personnelles si `git status` en signale. Si Git refuse le changement de branche, transmettez son message plutôt que d’effacer vos fichiers.

Scannez le nouveau QR code sur le même réseau Wi-Fi, avec le même Expo Go compatible avec Expo SDK 57. Gardez le même projet et le même dossier pour retrouver SQLite. **Ne désinstallez pas Expo Go et n’effacez pas son stockage.** `--clear` concerne le cache de développement, pas vos programmes.

Si le Wi-Fi local bloque la connexion, arrêtez Expo et essayez :

```powershell
npx.cmd expo start --tunnel --clear
```

**Aucune migration SQLite : version 4 conservée**, même fichier et même identité Expo. M3.1 reste compatible avec cette base. Les anciens codes M1.1/M1.2 ne peuvent pas ouvrir v4. Aucun programme, entraînement ou résultat d’exemple n’est installé.

## 2. Retrouver ses dernières performances

1. Choisissez une séance dont vous avez déjà terminé un entraînement sur votre iPhone. Touchez **Démarrer la séance**.
2. Retrouvez une seule série active. Sous les trois champs réels, la petite carte **DERNIÈRE FOIS** doit montrer un résultat réellement enregistré, avec la date et la précision de la comparaison. Sur un petit écran, faites défiler pour lire la carte ; le bouton **Valider la série** reste en bas.
3. Vérifiez que charge, répétitions et RIR actuels restent **vides**. La charge cible et l’ancienne performance ne sont pas des résultats nouveaux.
4. Saisissez vos propres valeurs. Elles ne doivent jamais être remplacées quand la carte finit de charger. Le bouton principal reste **Valider la série**.
5. Passez à une série d’un autre type ou d’une autre position : vérifiez le repère correspondant. Une comparaison moins précise affiche **autre position** ou **autre type**. La date peut être plus ancienne si la dernière utilisation n’avait pas de série exactement comparable.
6. Vérifiez une ancienne série dont le RIR était absent : pas de « RIR 0 » inventé. Une charge absente doit indiquer **Charge non renseignée** ; un zéro réellement saisi doit rester zéro.
7. Pour un exercice jamais réalisé, la carte laisse place à **Pas encore de série comparable enregistrée**. Ce texte ne prétend pas que l’exercice n’a jamais eu d’échauffement ou un autre mode de charge.

### Règles de comparaison à connaître

- Même identifiant d’exercice réellement utilisé, et même mode de charge capturé.
- Séances terminées seulement, avant ou à l’heure du démarrage actuel ; aucun résultat de la séance en cours n’est réutilisé.
- Même type et même position de série en priorité ; sinon même type à une autre position ; sinon dernière série de cet exercice dans un autre type, explicitement signalée.
- Un repère de travail n’utilise jamais un échauffement. Un échauffement actif cherche seulement d’anciens échauffements.
- Dans chaque niveau de précision, le plus récent entraînement correspondant est retenu. Aucun pourcentage d’amélioration ni augmentation de charge n’est imposé.

Les règles complètes, dont les égalités de position, sont dans [M3.2.md](M3.2.md).

## 3. Tester les identités et le remplacement

Utilisez vos propres séances ou créez manuellement un programme de test. L’application n’en crée pas pour vous.

- Faites le même exercice dans deux programmes : il doit retrouver ses repères à travers les deux, selon le type et le mode.
- Remplacez temporairement un exercice de barre par un exercice d’haltères avec le menu M2. Le résultat de la barre ne doit pas apparaître comme une ancienne performance d’haltères. Si vous avez déjà terminé un entraînement avec cette alternative, son propre résultat peut apparaître.
- Vérifiez ce comportement aussi pour un remplacement après quelques séries, sans perdre les séries déjà validées.
- Si un exercice a des résultats avec plusieurs modes de charge, le mode de l’entraînement actuel doit filtrer le repère. Pas de charge totale affichée comme charge par haltère.
- Les résultats doivent rester accessibles après suppression du programme d’origine. Ne supprimez pour cet essai qu’un **programme de test que vous acceptez réellement de perdre**, pas votre programme personnel.
- Renommer un exercice personnalisé garde son identité : fiche au nouveau nom, anciens résultats avec leurs noms capturés. L’historique peut garder son ancien titre tant qu’aucun nouvel entraînement n’a été réalisé avec le nouveau nom.

## 4. Vérifier l’accueil

1. La carte **Cette semaine** compte les séances réellement **terminées** du lundi au dimanche local, selon leur heure de fin. Une séance encore en cours ne compte pas.
2. Comparez le compteur à vos séances terminées dans l’historique. Plusieurs séances le même jour comptent chacune ; le jour reste marqué une fois.
3. Vérifiez les sept marqueurs **L M M J V S D**. Les jours avec séance sont bleus et le jour courant est entouré.
4. Sans réalisation cette semaine, le compteur doit être **0**, sans objectif de quatre séances inventé. Sans historique du tout, la carte Progression annonce la disponibilité après la première séance terminée.
5. Terminez un entraînement puis revenez à l’accueil : le compteur et le bon jour doivent s’actualiser, sans doublon.
6. Revenez depuis l’historique, fermez et rouvrez le projet, puis revenez depuis l’arrière-plan : les valeurs doivent rester correctes.
7. Au prochain passage de minuit ou de dimanche à lundi, vérifiez le nouveau jour/semaine. Si vous changez de fuseau dans les réglages iOS, revenez dans Expo Go : le regroupement doit être recalculé selon ce fuseau. Il n’est pas nécessaire de modifier l’horloge de vos véritables entraînements pour tester ce jalon ; les cas de changement d’heure sont aussi couverts en tests automatiques.
8. Touchez **Progression → Vos courbes** : retrouvez les performances par exercice de M3.1. Aucun pourcentage ou gain de force ne doit être déduit automatiquement du tonnage.

## 5. Bibliothèque et fiches d’exercices

- Dans Musculation, ouvrez **Bibliothèque d’exercices**, même si vous n’avez plus de programme.
- Recherchez par nom, muscle ou matériel, avec plusieurs mots et sans accents.
- Ouvrez une fiche : nom, groupe musculaire, matériel, mode et instructions doivent correspondre aux données. Pas d’illustration ou de conseil inventé si le catalogue n’en contient pas.
- **Voir mes performances** doit ouvrir l’historique de cet exercice précis. Sans résultats, l’état vide M3.1 reste honnête.
- Ouvrez une référence personnalisée, modifiez son nom ou ses consignes, puis **Enregistrer l’exercice**. La fiche doit être actualisée et ses anciennes performances conservées. Le catalogue initial n’affiche pas ce bouton d’édition.
- Essayez **Créer un exercice personnalisé** depuis la bibliothèque générale : la référence apparaît dans le catalogue, sans créer de programme ni l’ajouter automatiquement à une séance.
- Dans la bibliothèque de configuration d’une séance, l’ajout reste direct. L’icône d’information ouvre la fiche **sans ajouter l’exercice**. Revenez et ajoutez-le avec son action d’ajout habituelle.
- Les boutons **Terminer** et **Terminer la configuration** restent fonctionnels dans les préparations.

## 6. Non-régression et confort réel sur iPhone

Vérifiez les swipes Accueil ↔ Musculation, les boutons accessibles, une seule série active, la sauvegarde des résultats, le choix libre d’exercice, les remplacements et les historiques.

Pendant une série, ouvrez le clavier numérique : les champs doivent rester utilisables, le défilement vertical confortable et **Valider la série** accessible. La carte précédente doit rester secondaire. Signalez les valeurs coupées ou les difficultés sur votre taille de texte habituelle.

Testez un repos : durée propre à la série, pause/reprise, dépassement, passage manuel, fermeture/réouverture. Les calculs et l’alerte M1.2 n’ont pas été modifiés. Le son reste limité au premier plan selon les réglages et le mode silencieux ; aucune nouvelle notification écran verrouillé n’est promise dans Expo Go.

Toutes les lectures sont locales. Une première ouverture Expo Go peut avoir besoin de Metro pour charger le JavaScript ; les programmes et performances ne sont pas synchronisés avec un serveur.

## Vérifications facultatives sur le PC

Après un premier démarrage d’Expo pour régénérer les routes typées, arrêtez-le puis :

```powershell
npm.cmd run typecheck
npm.cmd test
npm.cmd run export:ios
npm.cmd start -- --clear
```

L’export iOS produit le JavaScript et les ressources, pas une application App Store ni une validation UIKit.

## Limites et retour de test

La carte Progression est un accès neutre aux courbes : aucun nouvel indicateur de force n’est calculé. La comparaison précédente est descriptive et ne garantit pas une difficulté identique entre deux séries.

M3.3 reste à développer : préférences utiles, éventuel export local sécurisé, stabilisation. Pas d’export ni de restauration livrés ici. La refonte globale, le Cardio, la 3D, le cloud, le coach et les progressions automatiques restent reportés.

Les PR restent empilées : **#2 → #3 → #4 → #5 → M3.2**, sans fusion automatique. Transmettez le parcours testé, le résultat observé et tout message d’erreur. **M3.2 ne sera validé qu’après votre retour de test sur iPhone.**
