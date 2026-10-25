# M4B SDK 58 — tester sur iPhone depuis Windows

Cette branche migre le prototype de la PR #15 vers le SDK **58** attendu par
votre Expo Go. Le test sur votre iPhone reste à faire. Node.js **24 LTS** est
recommandé sur le PC. Aucun Mac, abonnement ou build natif n’est nécessaire
pour cet essai dans Expo Go SDK 58.

## 1. Récupérer la branche

Fermer l’ancien serveur Expo avec **Ctrl+C**. Ouvrir PowerShell dans le dossier
du dépôt Logbook et exécuter :

```powershell
git status --short
git fetch origin
git switch feat/m4b-migration-expo-sdk58
git pull --ff-only origin feat/m4b-migration-expo-sdk58
node --version
npm.cmd ci
npm.cmd run viewer:check
npx.cmd expo start --go --lan
```

Si `git status` montre des modifications personnelles, les conserver avant de
changer de branche ; ne pas utiliser `git reset --hard`. Lors du premier
`git switch`, Git crée automatiquement la branche locale depuis `origin`.
Les suffixes **`.cmd`** évitent le blocage de `npm.ps1` par PowerShell, sans
changer la politique de sécurité Windows.

## 2. Ouvrir dans Expo Go

1. Garder le PC et l’iPhone sur le **même Wi-Fi**, sans réseau invité isolé.
2. Autoriser Node.js dans le pare-feu Windows pour le réseau **privé**.
3. Scanner le **nouveau QR code** avec l’appareil photo de l’iPhone et ouvrir
   dans Expo Go. Ne pas réutiliser une ancienne entrée du projet SDK 57.
4. Autoriser le **réseau local** pour Expo Go si iOS le demande.
5. Dans Logbook : **Musculation → Mannequin 3D · Aperçu**.

Ne pas désinstaller Expo Go, ne pas supprimer ses données et ne pas effacer
la base Logbook. Le nom du projet, son identité et `logbook.db` sont conservés.
Si vos données habituelles ne sont pas visibles, arrêter l’essai et le signaler
avant toute réinitialisation.

## 3. Vérifier le prototype

- Vérifier d’abord les programmes, l’historique et les paramètres existants.
  Si une séance était active, vérifier sa reprise et le chronomètre de repos.
- Un doigt : rotation horizontale à 360°, inclinaison verticale limitée.
- Deux doigts : pincer pour zoomer ; glisser verticalement pour déplacer le cadre.
- **Face** revient devant en gardant le zoom et le cadrage vertical.
- **Vue générale** replace le mannequin entier de face.
- Revenir à l’application, rouvrir le visualiseur, puis tester un passage en
  arrière-plan et un retour. Signaler écran noir, fermeture ou gestes bloqués.

Le GLB et Three.js sont embarqués, sans CDN. Expo Go reste un client de
développement : Metro sur le PC sert le JavaScript et les fichiers au lancement.
Garder ce terminal ouvert et le réseau local actif pendant le test.

## 4. Si le lancement bloque encore

Vérifier les versions depuis le dossier du dépôt :

```powershell
git branch --show-current
npm.cmd ls expo react-native react-native-webview
npx.cmd expo install --check
npx.cmd expo-doctor
```

Versions attendues : Expo **58.0.x**, React Native **0.88.0**, WebView **14.0.1**.
Si Expo Go annonce encore SDK 57, vérifier le dossier courant, fermer les
anciens serveurs avec Ctrl+C, puis relancer **ce dossier** :

```powershell
npx.cmd expo start --go --lan --clear
```

`--clear` vide uniquement le cache de compilation Metro sur le PC ; il ne
supprime pas les données SQLite de l’iPhone. Pour un QR inaccessible, vérifier
le VPN, le Wi-Fi et le pare-feu plutôt que réinstaller l’application.

Transmettre le message exact si le problème persiste, ainsi que la version
d’iOS et d’Expo Go. La validation finale dépend de ce test sur votre appareil.
