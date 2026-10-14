# Logbook — première version M0

Application iPhone de musculation développée avec React Native, Expo, TypeScript, Expo Router et SQLite local.

Cette première version permet de créer et modifier ses programmes, d'y ajouter des séances prévues, puis de retrouver ces données après fermeture de l'application. Le premier lancement est vide : aucun programme, aucune performance et aucune statistique de démonstration ne sont enregistrés.

Le thème sombre, les accents bleus et les cartes arrondies reprennent les écrans 1 à 4 de la [maquette validée](docs/design/Maquette%20d’application%20fitness%20complète%20en%2021%20écrans.png). Le suivi d'un entraînement sera développé au jalon M1.

## Essayer sur iPhone

Suivre le [guide pas à pas pour débutants](docs/TESTER_SUR_IPHONE.md). Il faut un ordinateur avec **Node.js 24**, Git, un iPhone avec **Expo Go compatible avec Expo SDK 57**, et le même réseau Wi-Fi pour les deux appareils.

Depuis un terminal sur votre ordinateur :

```bash
git clone --branch feat/m0-programmes https://github.com/mkfreyer/logbook.git
cd logbook
npm ci
npm start
```

Scanner ensuite le QR code avec l'appareil photo de l'iPhone et ouvrir le projet dans Expo Go. Ce QR code doit provenir du serveur lancé sur votre ordinateur ; l'environnement cloud de développement ne fournit pas automatiquement un accès depuis votre iPhone.

## Vérifications de développement

Avec Node.js 24, dans le dossier `logbook` :

```bash
npm run typecheck
npm test
npm run export:ios
```

Les 20 tests couvrent les migrations et le stockage sur une vraie base SQLite avec le moteur de Node, ainsi que les formulaires et la navigation avec Jest. L'export iOS produit le JavaScript et les ressources ; il ne compile pas une application native installable et ne remplace pas un essai sur iPhone.

La CI GitHub lance ces mêmes vérifications. Voir [le périmètre et l'architecture de M0](docs/M0.md) pour les limites et la suite.

## Données locales

Aucun compte ni serveur n'est nécessaire pour les programmes. Ils restent dans la base SQLite du projet sur l'appareil. Il n'y a pas encore de sauvegarde iCloud ni d'export : désinstaller Expo Go, effacer ses données ou changer l'identité du projet peut faire perdre les programmes. Utiliser cette version pour des essais, en attendant une fonction de sauvegarde.

## Références

- [Spécification fonctionnelle et technique](SPECIFICATION_CODEX%20.md)
- [Maquette des 21 écrans](docs/design/Maquette%20d’application%20fitness%20complète%20en%2021%20écrans.png)
- [Comment tester sur iPhone](docs/TESTER_SUR_IPHONE.md)
