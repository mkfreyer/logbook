# Logbook — entraînements et repos M1.2

Application iPhone de musculation en React Native, Expo SDK 57, TypeScript, Expo Router et SQLite local. M0 et M1.1 ont été testés sur iPhone. La branche **`feat/m1-entrainement`** ajoute M1.2, à vérifier sur appareil avant validation.

Vous pouvez configurer vos programmes, exercices et séries, puis démarrer un entraînement. Une seule série est affichée pendant l’effort. Les résultats saisis sont sauvegardés à chaque validation, séparément des objectifs. Le repos circulaire utilise la durée propre à la série ; il peut être mis en pause ou terminé tôt, et continue en dépassement sans passer automatiquement à la suivante.

La séance et les horodatages du repos sont conservés après fermeture. Une carte sur l’accueil et dans Musculation permet de reprendre. **Terminer** et **Terminer la configuration** sortent de la préparation ; **Terminer la séance** clôt un entraînement réellement effectué.

Le premier lancement ne contient aucun programme ni performance fictive. La bibliothèque d’exercices est distincte des programmes utilisateur. Aucun compte ni serveur n’est nécessaire.

## Tester sur iPhone depuis Windows

Suivre le [guide M1.2](docs/TESTER_M12_SUR_IPHONE.md), avec Node.js 24, Git et Expo Go compatible avec Expo SDK 57. Arrêter Metro avec **Ctrl+C**, ouvrir PowerShell dans `logbook`, puis :

```powershell
git fetch origin
git switch feat/m1-entrainement
git pull --ff-only origin feat/m1-entrainement
npm.cmd ci
npm.cmd start -- --clear
```

Si la branche n’existe pas localement, utiliser `git switch --track origin/feat/m1-entrainement` à la place du premier `git switch`. Scanner le QR code avec l’iPhone, sur le même réseau Wi-Fi. Conserver le même projet Expo Go pour retrouver les données.

## Vérifications

```powershell
npm.cmd run typecheck
npm.cmd test
npm.cmd run export:ios
```

Les tests couvrent les migrations, la persistance réelle SQLite, les parcours de configuration et d’entraînement, les pauses, les repos individuels, les erreurs et les doubles validations. La CI vérifie aussi la navigation verticale. L’export iOS produit le JavaScript et les ressources, sans compiler une application native installable. Gestes, clavier, son et reprise doivent être testés sur iPhone.

## Données et limites

La migration **version 3** ajoute les entraînements dans le même fichier `logbook.db`, sans effacer les programmes, séances ou séries. Chaque entraînement conserve un instantané indépendant : supprimer son programme ne supprime pas ses résultats. Une ancienne version M1.1 refuse d’ouvrir une base passée en version 3 sans la rétrograder.

Le décompte exclut les pauses manuelles ; **Repos réel** inclut tout le temps chronologique. L’arrière-plan ne met pas automatiquement en pause. Le son est une alerte locale au premier plan, soumise au volume et au mode silencieux ; aucune notification écran verrouillé n’est promise dans Expo Go.

M2 apportera le remplacement temporaire d’exercice, le choix d’un exercice restant et le bilan complet. Graphiques, historique avancé, Cardio, mannequin 3D et coach restent hors périmètre.

- [Architecture et conventions M1.2](docs/M1.2.md)
- [Guide de test M1.2](docs/TESTER_M12_SUR_IPHONE.md)
- [Spécification](SPECIFICATION_CODEX%20.md)
- [Maquette](docs/design/Maquette%20d’application%20fitness%20complète%20en%2021%20écrans.png)
- [Référence M1.1](docs/M1.1.md)
- [Référence M0](docs/M0.md)
