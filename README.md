# Logbook — configuration des exercices et séries M1.1

Application iPhone de musculation développée avec React Native, Expo, TypeScript, Expo Router et SQLite local.

M0 a été validé sur un véritable iPhone avec Expo Go : programmes et séances prévues, modification, suppression confirmée, sauvegarde locale et navigation verticale interactive. La branche de développement **`feat/m1-exercices-series`** ajoute uniquement **M1.1**, la préparation des exercices et de leurs séries. Elle conserve les fonctionnalités et les données M0.

Une séance peut maintenant contenir des exercices issus d'une bibliothèque recherchable ou créés par l'utilisateur. Chaque exercice possède des séries indépendantes : étiquette, répétitions exactes ou plage, charge et RIR facultatifs, **repos après cette série en secondes**. Les exercices et les séries sont modifiables, réordonnables et supprimables. La vue d'ensemble affiche ces objectifs avec le thème sombre, les accents bleus et les cartes arrondies de la [maquette validée](docs/design/Maquette%20d’application%20fitness%20complète%20en%2021%20écrans.png).

Le premier lancement ne contient aucun programme ni performance de démonstration. Le catalogue initial contient des exercices réels, distincts des programmes utilisateur. L'entraînement en direct, la validation d'une série réalisée et le chronomètre viendront pendant M1.2 ; aucun bouton factice de démarrage n'est affiché.

## Essayer sur iPhone

Suivre le [guide M1.1 pour Windows et iPhone](docs/TESTER_M1_SUR_IPHONE.md). Il faut un ordinateur avec **Node.js 24**, Git, un iPhone avec **Expo Go compatible avec Expo SDK 57**, et le même réseau Wi-Fi pour les deux appareils.

Depuis un terminal sur votre ordinateur :

```bash
git clone --branch feat/m1-exercices-series https://github.com/mkfreyer/logbook.git
cd logbook
npm ci
npm start
```

Scanner ensuite le QR code avec l'appareil photo de l'iPhone et ouvrir le projet dans Expo Go. Ce QR code doit provenir du serveur lancé sur votre ordinateur ; l'environnement cloud de développement ne fournit pas automatiquement un accès depuis votre iPhone.

Si le projet est déjà installé sur votre ordinateur Windows, suivre la [mise à jour du dossier existant](docs/TESTER_M1_SUR_IPHONE.md#mettre-à-jour-votre-dossier-logbook). Utiliser le même projet dans Expo Go pour retrouver les données M0. La migration SQLite s'effectue à sa première ouverture.

## Vérifications de développement

Avec Node.js 24, dans le dossier `logbook` :

```bash
npm run typecheck
npm test
npm run export:ios
```

Les tests couvrent les migrations depuis une base M0, les créations, modifications, réorganisations, suppressions et la persistance sur une vraie base SQLite avec le moteur de Node. Les tests Jest couvrent aussi les formulaires, les états vides et la navigation verticale. L'export iOS produit le JavaScript et les ressources ; il ne compile pas une application native installable et ne remplace pas un essai des écrans, claviers et confirmations sur iPhone.

La CI GitHub lance ces mêmes vérifications. Voir [le périmètre et l'architecture de M1.1](docs/M1.1.md) pour les limites et la suite. Les [notes de M0](docs/M0.md) restent disponibles comme référence de la version validée.

## Données locales

Aucun compte ni serveur n'est nécessaire. Les programmes, séances et configurations restent dans la base **`logbook.db`** du même projet sur l'appareil. La migration version 2 ajoute les tables M1.1 sans supprimer les programmes ou séances M0. Il n'y a pas encore de sauvegarde iCloud ni d'export : conserver Expo Go et ses données pendant les mises à jour.

## Références

- [Spécification fonctionnelle et technique](SPECIFICATION_CODEX%20.md)
- [Maquette des 21 écrans](docs/design/Maquette%20d’application%20fitness%20complète%20en%2021%20écrans.png)
- [Comment tester M1.1 sur iPhone](docs/TESTER_M1_SUR_IPHONE.md)
- [Architecture et limites M1.1](docs/M1.1.md)
- [Guide de la version M0](docs/TESTER_SUR_IPHONE.md)
