# M4B — Ouvrir le mannequin sur iPhone depuis Windows

Le prototype est sur la branche **`feat/m4b-visualiseur-meshy-iphone`**.
Le test sur votre véritable iPhone reste nécessaire avant validation.

## 1. Vérifier d’abord Expo Go

Ce projet reste en **Expo SDK 57**, React Native 0.86.3. Le visualiseur utilise
`react-native-webview` **13.16.1**, inclus dans
[Expo Go pour ce SDK](https://docs.expo.dev/versions/v57.0.0/sdk/webview/).
Il n’a pas besoin d’un nouveau module natif compilé pour ce client.

Vous avez indiqué ne pas encore avoir vérifié l’ouverture de Logbook dans
Expo Go. Le premier essai doit donc confirmer la compatibilité du **client
Expo Go installé** avec le SDK 57. La version App Store courante n’accepte pas
nécessairement un ancien SDK. Informations officielles : [Expo Go](https://expo.dev/go).

Si Expo Go signale « SDK incompatible », arrêtez l’essai et transmettez le
message exact. Ne lancez pas une mise à niveau générale du projet ou une
réinstallation effaçant ses données pour contourner ce message.
L’alternative est un client de développement compatible et signé ; sur iPhone,
une installation gratuite hors Expo Go demande notamment un Mac/Xcode.
[Contraintes officielles](https://docs.expo.dev/develop/development-builds/introduction/).
Aucune compilation native, inscription payante ou dépense n’est engagée ici.
Le choix d’une alternative sera distinct si le client SDK 57 est indisponible.

## 2. Lancer le projet sur le PC

Utiliser Node.js 24 et npm, comme la CI du dépôt. Dans PowerShell, depuis le
répertoire de Logbook :

```powershell
git fetch origin
git switch feat/m4b-visualiseur-meshy-iphone
npm ci
npm run viewer:check
npx expo start --go --lan
```

Le moteur 3D précompilé est déjà dans la branche. `viewer:check` vérifie sa
cohérence ; pas de génération externe, clé API, CDN ou service payant.
La première installation des dépendances et d’Expo Go nécessite Internet.

## 3. Connecter l’iPhone

1. Connecter le PC et l’iPhone au même Wi-Fi local, sans réseau invité isolant
   les appareils. Autoriser Node.js sur le réseau **privé** dans le pare-feu
   Windows si la demande apparaît.
2. Garder Metro ouvert dans PowerShell. Scanner le QR code affiché avec
   l’appareil photo de l’iPhone, puis ouvrir dans Expo Go.
3. Autoriser Expo Go à accéder au réseau local si iOS le demande.
4. Ouvrir **Musculation**, puis le lien discret **Mannequin 3D · Aperçu**, sous
   les accès habituels. Le bouton retour retrouve la navigation existante.

Si le QR code ne fonctionne pas, vérifier l’adresse LAN affichée par Metro et
le port indiqué, généralement 8081. Un VPN, un pare-feu ou un Wi-Fi invité peut
empêcher la connexion locale. Aucun tunnel ou abonnement n’est requis.

## 4. Gestes et commandes

- **Un doigt :** tourner à 360° horizontalement. Le mouvement vertical permet
  une inclinaison limitée, avec la tête conservée en haut.
- **Deux doigts qui s’écartent / se rapprochent :** zoom et dézoom.
- **Deux doigts qui glissent verticalement :** déplacer le cadrage vers la tête
  ou les jambes, notamment après un zoom.
- **Vue générale :** remettre tout le corps dans le cadre et revenir de face.
- **Face :** revenir devant, en conservant le zoom et le cadrage vertical actuels.

Le zoom est borné pour garder la caméra hors du mannequin. Le balayage natif
« retour » depuis le bord est désactivé **uniquement sur cette page**, afin de
ne pas voler une rotation ; le bouton Retour reste disponible.

## 5. Vérifier le mode sans Internet

Le moteur, le GLB et les ressources du visualiseur sont locaux. Aucune requête
vers un CDN, Meshy ou un serveur 3D n’est nécessaire.

Pour tester sans accès Internet tout en conservant le réseau local de développement :

```powershell
npx expo start --go --lan --offline
```

Le PC et l’iPhone doivent toujours se joindre sur leur Wi-Fi. Une fois le
mannequin chargé, couper l’accès Internet ne doit pas empêcher les gestes.

**Expo Go est un client de développement : il peut encore avoir besoin de Metro
pour charger le JavaScript et les assets au démarrage. Ce n’est pas une
installation autonome de Logbook, et son cache ne garantit pas une relance
après arrêt complet sans réseau local.** Un binaire Logbook installé avec ces
bundles embarquera le moteur et le GLB ; ce binaire signé n’est pas produit
pendant ce prototype. L’export iOS contrôlé est un export JavaScript/assets,
pas un fichier IPA installable.

## 6. Validation sur votre appareil

Vérifier au minimum :

- tête et pieds entièrement visibles à l’ouverture et après **Vue générale** ;
- visage, coiffure et reliefs conformes au mannequin validé ;
- tours complets face / profil / dos sans retournement brusque ;
- zoom à deux doigts, déplacement vertical et limites de rapprochement ;
- retour **Face**, puis **Vue générale**, y compris juste après une rotation ;
- dix ouvertures/retours successifs, puis un passage en arrière-plan et retour ;
- comportement sans Internet et absence d’écran noir ou de chargement bloqué.

En cas d’échec, relever le modèle d’iPhone, la version iOS, la version d’Expo Go,
l’action et une capture. Pas de FPS annoncé sans mesure réelle. La mémoire
processus et la fluidité sur iPhone ne sont pas mesurées par les tests Linux.

Aucune sélection anatomique, coloration musculaire ou statistique n’est encore
présente. Cette livraison s’arrête à votre validation du visualiseur.
