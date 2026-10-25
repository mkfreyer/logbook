# Validation M4B — Expo SDK 58

Exécutée le **25 octobre 2026**, Node.js **24.19.0**, Linux, depuis
`325ef229fedc3409cc390a651e8776eed96822d7`. Installation propre avec `npm ci`,
sans contournement de résolution des pairs.

| Contrôle | Résultat |
| --- | --- |
| `npm ci` | Réussi, verrou reproductible |
| `npx expo install --check` | Réussi, dépendances déclarées à jour pour SDK 58 |
| Même contrôle avec `EXPO_OFFLINE=1` (CI) | Réussi sur le catalogue installé ; le CLI avertit que la validation hors ligne est moins complète |
| `npm ls --all` | Réussi, aucun pair requis invalide ; dépendances de plateformes optionnelles absentes sous Linux attendues |
| `npx expo config --type public --json` | Résout `sdkVersion: 58.0.0`, identité conservée |
| `npx expo-doctor` | **18/20**, deux contrôles distants non conclusifs, voir ci-dessous |
| `npm run typecheck` | Réussi, règles TypeScript conservées |
| `npm run viewer:check` | Bundle Three.js embarqué identique et à jour |
| `npm test` | **546/546** : 219 SQLite/données, 13 navigation, 309 UI, 4 modèle/caméra/protocole, 1 nouveau test v8 |
| Pager avec `EXPO_PUBLIC_GESTURE_DEBUG=1` | **17/17**, mêmes scénarios dans le mode diagnostic |
| `npm run test:viewer-browser` | Réussi avec le véritable moteur WebGL, détails JSON ci-dessous |
| `npm run export:ios -- --max-workers 2` | Réussi, 2 035 modules, bundle Hermes + ressources |
| GLB exporté | SHA-256 identique au modèle validé `e45e5d8`, 1 993 204 octets |
| Conservation des sources d’exécution | 129 fichiers comparés ; 127 identiques en octets, 2 modifications de types avec JavaScript émis identique |
| Appareil iPhone / Expo Go 58 | **À tester par l’utilisateur** |

Les 545 tests précédents restent présents et passent. Aucun test désactivé ;
les tests d’interface ont été adaptés aux opérations asynchrones de Testing
Library 14 et à son renderer d’éléments hôtes. Le nouveau test v8 a aussi été
rejoué après l’ajustement du nettoyage des fichiers temporaires pour Windows.

## Expo Doctor : limite réseau explicite

Les contrôles **schéma Expo config** et **métadonnées React Native Directory**
n’ont pas pu conclure. Le premier reçoit une erreur réseau ; une requête
de diagnostic vers `exp.host` obtient **HTTP CONNECT 403** du proxy de
l’environnement. Le second signale une réponse serveur inattendue.
L’essai avec prise en charge du proxy Node aboutit également à 18/20.
Aucune de ces vérifications n’est exclue de la configuration du projet.

Le contrôle local SDK et `npm ls` passent séparément, mais ne remplacent pas
ces deux résultats distants. À relancer sur Windows :

```powershell
npx.cmd expo-doctor
```

## Visualiseur réellement exercé

Chromium + SwiftShader, gestes tactiles émulés, viewport 390 × 540,
aucune mesure de performance iPhone :

- 110 588 triangles effectivement rendus, GLB validé chargé.
- Rotation tactile cumulée **8,849 radians**, donc supérieure à 360°.
- Pincement avant/arrière, bornes de zoom, déplacement vertical et inclinaison.
- Boutons Face et Vue générale, cadrage complet et raycast réel.
- Gestes après coupure du réseau, **0 requête externe**.
- Arrêt du rendu au repos ; cinq cycles de destruction/réouverture : géométries
  libérées à zéro, canvas supprimé, contexte WebGL perdu volontairement.
- GLB invalide signalé comme erreur, aucune erreur JavaScript non gérée.

[Résultats WebGL](browser-results.json) ·
[Empreintes de préservation](preservation-hashes.json) ·
[Contrôle de l’asset exporté iOS](export-ios.json) ·
[Synthèse structurée](validation-results.json).

Captures de contrôle, **navigateur Linux et non iPhone** :
[vue générale](renders/vue-generale.png), [rotation](renders/rotation.png),
[dos](renders/vue-dos.png), [zoom et cadrage vertical](renders/zoom.png).

## Arrêt pour essai réel

La réussite de ces contrôles ne valide pas encore WKWebView, les gestes natifs,
la mémoire, l’audio, le partage Fichiers ni la reprise des données sur cet
iPhone. Aucune réinstallation ou suppression des données n’est demandée.
Suivre [le guide Windows → iPhone](../M4B_SDK58_IPHONE_WINDOWS.md), vérifier
les données existantes, les séances et le visualiseur, puis transmettre le
résultat avant toute suite.
