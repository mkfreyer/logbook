# Tester M0 sur votre iPhone

Vous allez lancer la première version depuis votre ordinateur, puis l'ouvrir sur votre iPhone avec **Expo Go**. Expo Go est une application gratuite qui permet d'essayer un projet Expo pendant son développement. Aucun abonnement développeur Apple payant n'est nécessaire pour ce parcours.

## 1. Préparer l'ordinateur et l'iPhone

Sur votre ordinateur Windows, macOS ou Linux :

1. Installer **Node.js 24** depuis [nodejs.org](https://nodejs.org/). npm est installé avec Node.js.
2. Installer **Git** depuis [git-scm.com](https://git-scm.com/downloads) si vous ne l'avez pas déjà.
3. Ouvrir un terminal : **Terminal** sur macOS ou Linux, **PowerShell** sur Windows. Le terminal est la fenêtre dans laquelle vous allez copier les commandes ci-dessous, puis appuyer sur Entrée.
4. Vérifier les installations :

```bash
node --version
npm --version
git --version
```

La première commande doit afficher une version commençant par `v24.`. Si une commande est introuvable après installation, fermer et rouvrir le terminal.

Sur votre iPhone :

1. Installer ou mettre à jour **Expo Go** depuis l'App Store.
2. Connecter l'iPhone et l'ordinateur au **même réseau Wi-Fi**.

Le projet utilise **Expo SDK 57**. Expo Go doit prendre en charge cette version. Si Expo Go indique une incompatibilité, vérifier sa mise à jour dans l'App Store. Si la version disponible reste incompatible, il faudra utiliser une version compatible ou préparer une compilation de développement iOS ; installer arbitrairement un ancien Expo Go n'est pas une solution garantie sur iPhone.

## 2. Télécharger cette version

Dans le terminal de votre ordinateur, copier ces commandes une par une :

```bash
git clone --branch feat/m0-programmes https://github.com/mkfreyer/logbook.git
cd logbook
npm ci
```

La première commande crée un dossier `logbook` contenant la branche de M0. La deuxième place le terminal dans ce dossier. La troisième télécharge les outils et bibliothèques nécessaires ; attendre qu'elle se termine avant de continuer.

Si le dépôt est privé, GitHub peut demander une authentification sur votre ordinateur. Utiliser votre accès habituel au dépôt, sans partager de mot de passe ni de jeton dans un message.

Pour retrouver le projet plus tard, ouvrir un terminal dans le dossier `logbook`. Sur macOS ou Linux, vous pouvez aussi taper `cd `, faire glisser le dossier dans la fenêtre du terminal, puis appuyer sur Entrée. Sous Windows, ouvrir le dossier dans l'Explorateur, faire un clic droit dans un espace vide, puis choisir **Ouvrir dans le Terminal** quand cette option est disponible.

## 3. Ouvrir l'application sur l'iPhone

Dans le dossier `logbook`, lancer :

```bash
npm start
```

Laisser ce terminal ouvert : il sert les fichiers de l'application pendant les essais. Un QR code apparaît.

1. Ouvrir **Appareil photo** sur l'iPhone et viser le QR code.
2. Toucher la proposition **Ouvrir dans Expo Go**.
3. Autoriser l'accès au **réseau local** si iOS le demande.
4. Attendre le chargement de l'application.

Si le terminal annonce une compilation de développement plutôt qu'Expo Go, appuyer sur `s` pour basculer vers Expo Go, puis scanner le QR code affiché.

Le QR code doit être celui de votre ordinateur. Une adresse `localhost` ou un QR code créé dans l'environnement cloud n'est pas automatiquement accessible depuis votre iPhone.

## 4. Vérifier le parcours de M0

Faire cette vérification avec vos propres noms de programmes. Les exemples ci-dessous sont des noms à saisir vous-même ; l'application ne les ajoute pas automatiquement.

- [ ] À la première ouverture, aucun programme ni aucune statistique fictive n'apparaît.
- [ ] Depuis l'accueil, ouvrir les programmes puis créer un programme nommé, par exemple, `Mon programme`.
- [ ] Ajouter une description facultative et enregistrer. Le programme apparaît dans la liste.
- [ ] Ouvrir le programme et modifier son nom ou sa description. Enregistrer puis vérifier le résultat.
- [ ] Utiliser **Voir les séances**, puis ajouter une première séance, par exemple `Séance A`.
- [ ] Ajouter une deuxième séance, par exemple `Séance B`. Les deux restent visibles dans le programme.
- [ ] Modifier le nom et les notes d'une séance puis vérifier le résultat.
- [ ] Revenir à la liste des programmes et vérifier les informations enregistrées.
- [ ] Fermer complètement Expo Go depuis le sélecteur d'applications de l'iPhone, puis rouvrir le même projet pendant que `npm start` reste actif. Les programmes, séances et modifications doivent toujours être présents.
- [ ] Après le chargement du projet, activer le mode avion et essayer de créer ou modifier un programme. Le stockage n'utilise pas Internet. Désactiver ensuite le mode avion pour retrouver le serveur de développement si nécessaire.

Un nom est obligatoire et limité à 80 caractères. Les descriptions de programmes et les notes de séances sont facultatives et limitées à 1 000 caractères. Un champ ne contenant que des espaces est considéré comme vide.

Dans M0, une **séance** est une préparation enregistrée dans votre programme. Vous ne pouvez pas encore y ajouter des exercices, démarrer un entraînement ni saisir des performances. Ces fonctions viendront au jalon M1.

Le fonctionnement local de SQLite est indépendant du réseau. En revanche, Expo Go peut avoir besoin du serveur sur votre ordinateur pour charger ou rouvrir les fichiers de développement. Le test en mode avion après chargement ne prouve donc pas encore le démarrage totalement autonome d'une application distribuée.

## Si l'application ne s'ouvre pas

| Ce que vous voyez | Action à essayer |
| --- | --- |
| `npm` ou `node` est introuvable | Installer Node.js 24, puis rouvrir le terminal. |
| `package.json` est introuvable | Le terminal n'est pas dans le dossier `logbook`. Ouvrir ce dossier puis relancer la commande. |
| Le QR code ne s'ouvre pas | Vérifier le même Wi-Fi, l'accès réseau local d'Expo Go et le pare-feu de l'ordinateur. Un réseau public peut empêcher les appareils de communiquer ; essayer un réseau privé. |
| Expo Go signale une version incompatible | Mettre Expo Go à jour et vérifier sa compatibilité avec Expo SDK 57. |
| Les données ont disparu | Vérifier que vous avez rouvert le même projet. Une désinstallation, un effacement de données ou un changement d'identité du projet peut supprimer ou déplacer la base locale. |

Si les appareils ne peuvent pas communiquer sur le réseau local, une solution de dépannage consiste à arrêter le serveur avec `Ctrl+C`, puis à lancer :

```bash
npm exec expo start -- --tunnel
```

Cette option utilise un service externe et peut demander l'installation d'`@expo/ngrok` ainsi qu'un accès Internet. Elle n'a pas été vérifiée dans l'environnement Linux de cette livraison. Scanner le nouveau QR code lorsqu'il apparaît ; si ce service est bloqué sur votre réseau, essayer un autre réseau privé.

## Conserver vos données et arrêter les essais

Les données survivent à la fermeture et au rechargement du **même projet**. Elles restent locales à Expo Go sur votre iPhone. Il n'y a pas encore de synchronisation iCloud, d'export ou de restauration sur un autre iPhone. Ne pas désinstaller Expo Go ni effacer ses données si vous souhaitez conserver vos essais.

Pour arrêter le serveur sur l'ordinateur, revenir au terminal et appuyer sur `Ctrl+C`. Vous pourrez le relancer plus tard avec `npm start` depuis le dossier `logbook`.

## Et pour une application installable normalement ?

Expo Go sert à tester cette version. Une distribution autonome ou via TestFlight demandera ensuite une compilation iOS, les outils de signature et généralement un compte Apple Developer payant. Aucun fichier installable ni publication App Store n'est produit par M0.

Le simulateur iOS nécessite macOS et Xcode. L'environnement Linux utilisé pour développer M0 vérifie le code, les tests SQLite et l'export JavaScript pour iOS ; le rendu, le clavier, l'accessibilité et la persistance réelle sur iPhone doivent encore être vérifiés avec la liste ci-dessus.
