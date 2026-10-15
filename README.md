# Logbook — historiques et progression M3.1

Application iPhone de musculation en React Native, Expo SDK 57, TypeScript, Expo Router et SQLite local. M0, M1.1, M1.2 et M2 ont été validés sur un véritable iPhone. La branche **`feat/m3-historiques-progression`** ajoute uniquement M3.1, à tester sur appareil avant validation.

Vous pouvez configurer vos programmes, exercices et séries, puis démarrer un entraînement. Une seule série est affichée pendant l’effort. Les résultats saisis sont sauvegardés à chaque validation, séparément des objectifs. Le repos circulaire utilise la durée propre à la série ; il peut être mis en pause ou terminé tôt, et continue en dépassement sans passer automatiquement à la suivante.

La séance et les horodatages du repos sont conservés après fermeture. Une carte sur l’accueil et dans Musculation permet de reprendre. **Terminer** et **Terminer la configuration** sortent de la préparation ; **Terminer la séance** clôt un entraînement réellement effectué.

Le menu « … » permet maintenant de remplacer temporairement l’exercice actif ou de choisir un exercice restant. Les programmes ne changent pas. Un remplacement partiel conserve les performances déjà validées sur leur exercice initial et efface les charges cibles des séries restantes, après confirmation. Un choix pendant le repos le conserve jusqu’à sa fin manuelle.

Après la fin, le bilan présente durée chronologique, séries réalisées, tonnage enregistré, RIR moyen et exercices réellement utilisés. **Historique des entraînements**, dans Musculation, permet de rouvrir ce même bilan sauvegardé, même après suppression de son programme.

M3.1 ajoute le parcours historique général → programme → séance réelle → exercice, les périodes locales et des graphiques tactiles sobres. Les performances restent en lecture seule, les modes de charge d’un exercice sont séparés, et les dates sont regroupées au-dessus des tableaux compacts de séries. Les listes sont paginées ; les graphiques affichent au plus les 120 dernières séances filtrées, sans limiter les totaux.

Le premier lancement ne contient aucun programme ni performance fictive. La bibliothèque d’exercices est distincte des programmes utilisateur. Aucun compte ni serveur n’est nécessaire.

## Tester sur iPhone depuis Windows

Suivre le [guide M3.1](docs/TESTER_M3_1_SUR_IPHONE.md), avec Node.js 24, Git et le même Expo Go compatible avec Expo SDK 57. Arrêter Metro avec **Ctrl+C**, ouvrir PowerShell dans `logbook`, puis :

```powershell
git fetch origin
git switch feat/m3-historiques-progression
git pull --ff-only origin feat/m3-historiques-progression
npm.cmd ci
npm.cmd start -- --clear
```

Si la branche n’existe pas localement, utiliser `git switch --track origin/feat/m3-historiques-progression` à la place du premier `git switch`. Scanner le QR code avec l’iPhone, sur le même réseau Wi-Fi. Conserver le même projet Expo Go pour retrouver les données.

## Vérifications

```powershell
npm.cmd run typecheck
npm.cmd test
npm.cmd run export:ios
```

Les tests couvrent les migrations M0 à M2, la persistance SQLite, les configurations, entraînements, remplacements, choix d’ordre, calculs du bilan, historiques filtrés, identités, dates locales, graphiques, erreurs et doubles validations. La CI vérifie aussi la navigation verticale. L’export iOS produit le JavaScript et les ressources, sans compiler une application native installable. Les nouveaux parcours M3.1, les interactions tactiles et la reprise doivent être testés sur iPhone.

## Données et limites

M3.1 n’ajoute **aucune migration** et conserve SQLite **version 4**. La migration M2 a ajouté le choix persistant et les journaux de remplacement/ordre au même fichier `logbook.db`. Elle conserve programmes, séances, exercices, séries, réalisations et pauses. Chaque entraînement conserve des instantanés indépendants : supprimer son programme ne supprime pas ses résultats. Les anciens codes M1.1/M1.2 refusent d’ouvrir une base v4 sans l’effacer ni la rétrograder.

Le décompte exclut les pauses manuelles ; **Repos réel** inclut tout le temps chronologique. L’arrière-plan ne met pas automatiquement en pause. Le son est une alerte locale au premier plan, soumise au volume et au mode silencieux ; aucune notification écran verrouillé n’est promise dans Expo Go.

Le tonnage est la somme **charge saisie × répétitions réalisées**, échauffements inclus. Une charge par haltère est comptée une fois, sans inventer le nombre de mains utilisées. Le poids corporel n’est pas estimé et les charges absentes sont exclues. Le RIR moyen exclut les valeurs absentes, tout en comptant un RIR explicitement saisi à zéro.

M3.2 ajoutera les performances précédentes pendant l’effort, les statistiques d’accueil et les fiches d’exercice. M3.3 traitera les préférences et l’export local si faisable. Ils ne sont pas commencés. Cardio, mannequin 3D, synchronisation, coach et refonte visuelle globale restent hors périmètre.

Les PR #2 → #3 → #4 → M3.1 restent empilées ; aucune fusion sans accord. La PR M3.1 cible `feat/m2-liberte-bilan` tant que ses parents ne sont pas fusionnés.

- [Architecture, calculs et limites M3.1](docs/M3.1.md)
- [Guide de test M3.1](docs/TESTER_M3_1_SUR_IPHONE.md)
- [Finition visuelle future](docs/DESIGN_BACKLOG.md)
- [Architecture et conventions M2](docs/M2.md)
- [Guide de test M2](docs/TESTER_M2_SUR_IPHONE.md)
- [Référence M1.2](docs/M1.2.md)
- [Spécification](SPECIFICATION_CODEX%20.md)
- [Maquette](docs/design/Maquette%20d’application%20fitness%20complète%20en%2021%20écrans.png)
- [Référence M1.1](docs/M1.1.md)
- [Référence M0](docs/M0.md)
