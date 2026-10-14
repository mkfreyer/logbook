# Tester M0 sur votre iPhone

Vous allez lancer la première version depuis votre ordinateur, puis l'ouvrir sur votre iPhone avec **Expo Go**. Expo Go est une application gratuite qui permet d'essayer un projet Expo pendant son développement. Aucun abonnement développeur Apple payant n'est nécessaire pour ce parcours.

Si vous avez déjà testé M0, commencez par la section suivante. Les étapes d'installation plus bas restent utiles pour un premier essai.

## Mettre à jour le projet déjà installé sur Windows

Cette mise à jour corrige la détection des glissements entre l'accueil et Musculation. L'accueil vers le haut doit fonctionner sans devoir rejoindre le bas de la page ; le retour depuis Musculation se fait depuis le haut de la liste. Elle conserve la même identité de projet et la même base SQLite ; vos programmes et séances ne doivent pas être effacés.

1. Dans le terminal où l'ancien serveur tourne, appuyer sur **Ctrl+C** pour l'arrêter.
2. Ouvrir votre dossier `logbook` dans l'Explorateur Windows, puis choisir **Ouvrir dans le Terminal** avec un clic droit dans un espace vide. Si le terminal est déjà dans ce dossier, le garder ouvert.
3. Vérifier les fichiers locaux :

```powershell
git status --short
```

Si rien ne s'affiche, passer aux commandes suivantes. Si des fichiers modifiés apparaissent, conserver vos modifications avant de mettre à jour, par exemple dans une copie séparée du dossier. Ne pas utiliser `git reset --hard` pour les effacer. En cas de doute, garder les fichiers et demander de l'aide avec les noms affichés.

4. Copier les commandes ci-dessous une par une, en attendant la fin de chacune :

```powershell
git switch feat/m0-programmes
git pull --ff-only origin feat/m0-programmes
npm ci
npm start -- --clear
```

`git pull` récupère la nouvelle version de la branche M0. `npm ci` met les bibliothèques de l'ordinateur en accord avec cette version. `--clear` vide uniquement le cache du serveur de développement : **cela ne vide pas la base SQLite sur votre iPhone**.

Si `git pull` échoue avec un message de branches divergentes, arrêter la mise à jour et conserver les fichiers locaux ; ne pas forcer ni réinitialiser la branche.

5. Laisser le terminal ouvert. Sur l'iPhone, scanner le nouveau QR code avec **Appareil photo** et ouvrir le même projet dans Expo Go, sur le même Wi-Fi que l'ordinateur.
6. Vérifier d'abord que vos programmes et séances sont toujours présents, puis faire les essais de navigation de la section 4.

Ne pas désinstaller Expo Go, effacer ses données ni créer un nouveau projet Expo pour faire cette mise à jour. Si Windows refuse `npm` en indiquant que l'exécution de scripts est désactivée, utiliser `npm.cmd ci` puis `npm.cmd start -- --clear` dans PowerShell.

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

Pour vérifier la correction de la navigation sur votre véritable iPhone :

- [ ] Après la mise à jour du même projet, vos anciens programmes et séances sont toujours présents.
- [ ] Sur l'accueil, les cartes reprennent le thème sombre, les accents bleus et les proportions de la maquette. Aucun entraînement n'ayant été réalisé dans M0, les cartes de progression affichent des états vides, même si vous avez déjà créé des séances prévues.
- [ ] Dès l'arrivée sur l'accueil, sans chercher le bas de la page, glisser lentement vers le haut et garder le doigt sur l'écran à mi-parcours : l'accueil monte avec le doigt, et Musculation apparaît depuis le bas. La transition ne doit pas être horizontale.
- [ ] Refaire le geste en partant de plusieurs endroits : le titre, une carte, un espace libre puis le bouton **Musculation**. Le mouvement doit suivre le doigt avant de le relâcher. Un simple toucher sur le bouton doit toujours fonctionner.
- [ ] Relâcher après un petit déplacement lent : vous restez sur l'écran de départ. Commencer un geste plus ample, revenir près du point de départ avec le doigt puis relâcher : la transition s'annule. Un glissement plus ample ou rapide mène à Musculation.
- [ ] Depuis le haut de la liste des programmes, glisser vers le bas : Musculation descend avec le doigt et l'accueil réapparaît depuis le haut. Essayer depuis le titre et depuis une carte, puis avec un petit geste qui revient à Musculation.
- [ ] Interrompre un geste en ajoutant un second doigt pendant le déplacement : la page doit revenir à son point de départ et rester utilisable au geste suivant.
- [ ] Utiliser les boutons de navigation entre l'accueil et Musculation sans faire de swipe. La transition reste verticale. Les boutons ouvrant un programme, une séance ou un formulaire continuent de fonctionner avec un simple toucher.
- [ ] Si la liste des programmes est assez longue pour défiler, descendre dans la liste, puis remonter : la liste doit défiler normalement. Aucun changement d'univers ne doit se produire au milieu de la liste. Après avoir atteint son début, lever le doigt puis commencer un nouveau glissement vers le bas pour revenir à l'accueil.
- [ ] Dans un formulaire de programme ou de séance, faire défiler les champs avec le clavier affiché. Le formulaire reste ouvert et ne déclenche pas de changement d'univers.
- [ ] Dans **Réglages → Accessibilité → Affichage et taille du texte** de l'iPhone, essayer une taille de texte plus grande. Les boutons et les informations importantes restent lisibles.
- [ ] Dans **Réglages → Accessibilité → Animation**, activer **Réduire les animations**, puis essayer les boutons de navigation. Les écrans restent accessibles avec une transition adaptée à ce réglage.

Pour vérifier que la création, la modification et la sauvegarde fonctionnent toujours :

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

## Si les swipes ne fonctionnent toujours pas

La correction doit être vérifiée sur l'appareil : les tests automatisés et l'export iOS réalisés sous Linux ne reproduisent pas les gestes natifs de l'iPhone. Un diagnostic facultatif permet de voir si les touchers arrivent jusqu'à l'application, puis si le geste est autorisé et activé.

1. Arrêter le serveur avec **Ctrl+C**.
2. Dans le même terminal **PowerShell**, toujours dans le dossier `logbook`, saisir ces deux lignes :

```powershell
$env:EXPO_PUBLIC_GESTURE_DEBUG='1'
npm start -- --clear
```

3. Ouvrir le même projet dans Expo Go avec le QR code. Un petit panneau **Diagnostic geste** apparaît en haut de l'écran. Il laisse passer les touchers et n'efface aucune donnée.
4. Faire un glissement vers le haut depuis l'accueil, puis un glissement vers le bas depuis le haut de Musculation. Observer le panneau. Les mêmes messages portent le préfixe `[UniversePager]` dans les journaux JavaScript lorsqu'ils sont affichés dans les outils de développement.

| Message observé | Ce qu'il indique |
| --- | --- |
| `vue: toucher reçu` | La vue React Native reçoit le toucher. |
| `pan: touch down`, puis `pan: began` | Le reconnaisseur du geste reçoit le début du toucher. L'ordre de certains messages peut varier. |
| `autorisé: home y=…` ou `autorisé: musculation y=0` | La direction et la position de la liste autorisent la transition. `y` est la position de défilement en points d'écran. |
| `pan: ACTIVE`, puis `pan: déplacement reçu` | Le geste est activé et transmet le mouvement utilisé pour déplacer l'écran. |
| `pan: terminé` | Le geste s'est terminé normalement. Un geste trop court peut tout de même revenir à la page de départ. |
| `liste / axe: y=…` | Le geste est laissé à la liste ou rejeté à cause de sa direction. C'est attendu au milieu de la liste de Musculation, mais pas pour un geste vertical net vers le haut depuis l'accueil. |
| `refus: animation / plusieurs doigts` ou `pan: annulé / refusé` | Le geste a été refusé ou interrompu. Un simple toucher sans glissement peut aussi se terminer ainsi. |

Si vous voyez le toucher de la vue mais aucun message du Pan, la réception par le reconnaisseur doit être examinée. Si `autorisé` apparaît sans `ACTIVE`, le blocage se situe au moment de l'activation native. Si `ACTIVE` et `déplacement reçu` apparaissent sans déplacement visible, c'est le suivi animé de la page qu'il faut examiner. Les messages indiquent une étape à examiner ; ils ne suffisent pas à identifier seuls la cause.

Pour signaler un problème, noter l'écran de départ, l'endroit où le doigt a commencé, la direction, la présence d'une longue liste et les derniers messages visibles. Un enregistrement d'écran pendant le geste permet de rapprocher les messages du comportement réel. Le panneau conserve seulement les derniers messages et peut faire disparaître les premières étapes.

Pour désactiver le diagnostic, arrêter le serveur avec **Ctrl+C**, puis lancer :

```powershell
Remove-Item Env:EXPO_PUBLIC_GESTURE_DEBUG -ErrorAction SilentlyContinue
npm start -- --clear
```

Recharger le même projet sur l'iPhone. Ce diagnostic est désactivé par défaut et disponible seulement en mode développement.

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

Le simulateur iOS nécessite macOS et Xcode. L'environnement Linux utilisé pour développer M0 vérifie le code, les tests SQLite et l'export JavaScript pour iOS. La création, la modification, la persistance, le nouvel accueil et les boutons ont déjà été testés sur un véritable iPhone par l'utilisateur. Les swipes de la version précédente n'y fonctionnaient pas malgré les tests réussis. La correction actuelle, sa coexistence avec le défilement et l'accessibilité doivent être vérifiées avec la liste ci-dessus.
