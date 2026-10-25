# M4B — Relevé de validation

Environnement : Linux, Node.js 24.19.0, Expo 57.0.28, React Native 0.86.3,
React 19.2.3. **Aucun iPhone physique ni simulateur iOS disponible ici.**
La validation définitive attend l’essai sur l’iPhone de l’utilisateur.

| Vérification | Résultat |
| --- | --- |
| `npm run viewer:check` | Bundle Three.js embarqué à jour et reproductible |
| `npm run typecheck` | Réussi |
| `npm test` | **545 tests réussis** : 219 données/SQLite de test, 13 navigation, 309 UI, 4 spécifiques au modèle/caméra/protocole/HTML |
| `EXPO_PUBLIC_GESTURE_DEBUG=1 npm run test:ui -- --runTestsByPath tests/pager.test.tsx --silent` | **17 tests réussis**, mode diagnostic des gestes existants |
| `npm run export:ios -- --max-workers 2` | Export JavaScript Hermes et assets iOS réussi ; **pas un IPA signé** |
| Identité du GLB exporté | 1 993 204 octets, SHA-256 identique au master validé |
| `npm run test:viewer-browser` | Vrai WebGL Chromium/SwiftShader, gestes émulés et cycle de vie réussis |
| Appareil iPhone, Expo Go installé, WKWebView | **À tester par l’utilisateur** |

Les tests SQLite existants utilisent leurs fixtures temporaires. Aucun code de
base de données, migration ni donnée personnelle n’est modifié.
Un premier lancement de la suite en concurrence avec l’export et le test
WebGL a dépassé les 5 secondes d’un test UI existant. La relance séquentielle
complète a réussi **sans modifier ce test ni augmenter ses délais**.

## Contrôles du moteur réel

[Résultats machine](renders/browser-results.json) et
[synthèse d’export](validation-results.json).

Le test ouvre le même HTML et le même bundle que le visualiseur, charge le
vrai GLB, crée un contexte WebGL et envoie de vrais événements tactiles via
Chromium. Ce n’est pas un moteur 3D mocké. Le contexte de test remplace seulement
le pont de messages normalement fourni par la WebView native.

Ont été vérifiés :

- 110 588 triangles réellement rendus, un objet géométrique chargé ;
- cadrage initial avec tête et pieds à l’intérieur du viewport ;
- rotation tactile cumulée supérieure à un tour complet, sans sortie des limites
  d’inclinaison ;
- pincement dans les deux sens, distance minimale/maximale et déplacement vertical ;
- retour **Face** avec zoom conservé et réinitialisation exacte de la vue générale ;
- intersection réelle d’un point touché, sans identifiant anatomique inventé ;
- absence de rendu continu à l’arrêt ;
- fonctionnement des gestes après mise hors ligne du contexte de navigateur ;
- cinq cycles de libération/réouverture, zéro géométrie restante après libération
  et perte volontaire du contexte WebGL ;
- erreur explicite pour un fichier de modèle invalide ;
- **zéro requête externe**, hors chargement du document par le serveur local de test.

Les vues ci-dessous sont des captures du **moteur WebGL sous Chromium avec
rendu logiciel**, dans un viewport tactile de 390 × 540. Ce ne sont pas des
captures de Logbook sur iPhone :

- [Vue générale](renders/vue-generale.png)
- [Après rotation](renders/rotation.png)
- [Vue arrière après rotation](renders/vue-dos.png)
- [Zoom et cadrage vertical](renders/zoom.png)

Les buffers typés de géométrie représentent 1 990 440 octets. Le moteur peut
allouer aussi des textures de framebuffer internes malgré l’absence de texture
dans le GLB. Ces chiffres ne mesurent pas la mémoire totale du processus ni la
VRAM réelle sur iPhone. **Aucun FPS iPhone n’est annoncé.**

Les tests UI natifs portent sur l’état de chargement, les erreurs et reprises,
les commandes caméra, la navigation, le focus/arrière-plan et les événements
périmés. Ils utilisent une WebView mockée pour ces contrats seulement ; leur
réussite ne prétend pas démontrer la fluidité du rendu natif.

## Compatibilité et recommandations Expo

Le catalogue local de `expo@57.0.28` et la documentation SDK 57 confirment
`react-native-webview@13.16.1`. Le contrôle en ligne recommande des correctifs
pour six dépendances **déjà présentes dans le socle** : `expo`,
`@expo/metro-runtime`, `expo-constants`, `expo-linking`, `expo-router` et
`expo-sharing`. Leurs déclarations et versions verrouillées ne sont pas
modifiées par ce prototype. Cette recommandation de mise à jour ne constitue
pas une validation sur appareil ni une raison de lancer une mise à niveau
sans tâche dédiée. Le nouvel ajout `expo-asset@57.0.20` suit la recommandation
SDK 57 en ligne ; Three.js n’introduit aucun module natif.

La version d’Expo Go de l’iPhone reste inconnue. Si elle n’accepte pas le
SDK 57, suivre le [guide de précontrôle](../M4B_GUIDE_IPHONE_WINDOWS.md) ; aucun
client natif payant ou changement général de SDK n’est engagé automatiquement.

## Reproduction

```bash
npm ci
npm run viewer:check
npm run typecheck
npm test
npm run export:ios
```

Pour le contrôle graphique de développement, un Chromium local est nécessaire :

```bash
CHROMIUM_PATH=/usr/bin/chromium npm run test:viewer-browser
```

Le script accepte `M4B_ARTIFACT_DIR` pour le dossier des captures. Ces tests ne
remplacent pas la [validation manuelle iPhone](../M4B_GUIDE_IPHONE_WINDOWS.md).
