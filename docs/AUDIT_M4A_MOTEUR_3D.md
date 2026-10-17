# M4A — Audit des moteurs 3D pour Expo SDK 57

Audit documentaire et de sources publié le 17 octobre 2026. Aucun moteur ni modèle n’a été intégré à Logbook. Aucune dépendance, donnée ou configuration de l’application n’a été modifiée par cet audit. Aucun test natif sur iPhone n’a été réalisé.

## Conclusion provisoire

**Three.js dans une WebView locale est le candidat privilégié à éprouver**, une fois l’asset anatomique réellement inspecté et jugé acceptable. `react-native-webview` est intégré à Expo Go SDK 57 et fournit un environnement navigateur habituel à Three et à son chargeur GLB. Cela évite les adaptations DOM/chargement et un conflit de prototypes identifié dans les sources publiées d’`expo-gl` 57.0.2 avec Three récent.

Il ne s’agit pas encore d’une sélection validée : les accès aux fichiers locaux, le rendu GPU, la consommation mémoire, les reprises après arrière-plan et les gestes doivent être vérifiés dans Expo Go sur l’iPhone cible avec **l’asset final**. Une comparaison de performances sans modèle représentatif n’établirait pas la qualité recherchée. Aucun development build n’est imposé.

## Versions réellement examinées

Le projet installé contient Expo `57.0.28`, React `19.2.3`, React Native `0.86.3`. Son fichier `node_modules/expo/bundledNativeModules.json` recommande :

| Élément | Version SDK 57 / publiée examinée | État |
| --- | --- | --- |
| `expo-gl` | `~57.0.2` ; sources npm 57.0.2 lues | Inclus Expo Go selon documentation SDK 57 |
| `react-native-webview` | `13.16.1` ; sources npm lues | Inclus Expo Go selon documentation SDK 57 |
| `expo-asset` | `~57.0.19` | Version du manifeste SDK local |
| `three` | `0.186.1` | Bibliothèque JS MIT, aucune peer dependency native |
| `expo-three` | `8.0.0` | Peer Three **`^0.166.0`**, incompatible avec 0.186.1 sans changement de version |
| `@react-three/fiber` | `9.8.2` | Peers React `>=19 <19.4`, RN `>=0.78`, Three `>=0.156`, Expo `>=43` compatibles au niveau des plages, pas une preuve de rendu natif |

Les versions npm ont été lues depuis le registre officiel, les archives ont été extraites uniquement sous `/tmp` pour inspection. Ni `--force`, ni `--legacy-peer-deps`, ni modification du lockfile.

## Comparaison

| Critère | Three + expo-gl | Three + WebView locale |
| --- | --- | --- |
| Expo Go | Module natif fourni par SDK 57 | Module natif fourni par SDK 57 |
| Qualité | Matériaux PBR et éclairage Three, sous réserve du sous-ensemble GL exposé | Matériaux PBR et éclairage Three sur WebGL2 standard de WKWebView |
| GLB | Lecture locale puis `GLTFLoader.parse`; adapters requis pour certaines API images/DOM | Chargeur officiel GLTFLoader ; ressources locales et éventuels décodeurs à embarquer |
| Gestes | RN Gesture Handler/PanResponder à relier aux coordonnées de scène | Pointer Events sur le canvas, sans bridge par frame ; scroll/pinch de WebView désactivés pour cette route |
| Raycasting | Three.Raycaster, métadonnées des vrais meshes | Identique |
| Caméra | Mathématiques Three identiques | Identique |
| Ressources | Pas de processus Web séparé, mais appels GL synchrones et charge du runtime JS RN | Processus WebKit et mémoire supplémentaire ; boucle JS/rendu isolée de RN |
| Cycle de vie | Arrêt RAF, dispose Three, destruction du contexte selon propriété du GLView | Arrêt RAF, dispose Three, démontage WebView ; gérer terminaison du processus WebKit |
| Hors ligne | Asset embarqué et accessible localement | HTML, JS, GLB et décodeurs embarqués ; aucun CDN/API distant |
| Maintenance | Couche d’adaptation GL/DOM/loaders et compatibilité du module Expo à suivre | Contrat de messages typé et distribution locale à maintenir ; moteur WebGL standard |
| Mesures iPhone | Non réalisées | Non réalisées |

Ni les plages npm ni un export JavaScript réussi ne prouvent le rendu du mannequin sur iPhone.

## Points techniques confirmés pour expo-gl

La documentation officielle SDK 57 expose un contexte ressemblant à WebGL2 et `endFrameEXP()` après chaque rendu. Elle documente plusieurs méthodes non implémentées, dont `renderbufferStorageMultisample`, certaines textures compressées, les sync objects et plusieurs getters. Les arguments ne sont pas systématiquement vérifiés avant l’appel natif. Pour un prototype, éviter les pipelines avancés supposant un WebGL2 entièrement conforme.

La même documentation précise que **Three.js ne s’exécute pas directement dans un worklet Reanimated**. Il ne faut donc pas promettre le déplacement automatique du moteur Three sur le thread UI à partir de l’API worklet de GLView.

### Conflit précis à traiter avant toute intégration directe

Dans l’archive npm `expo-gl@57.0.2`, `common/EXWebGLRenderer.cpp`, la fonction d’installation crée explicitement l’héritage :

```text
WebGL2RenderingContext extends WebGLRenderingContext
```

Dans `three@0.186.1/src/renderers/WebGLRenderer.js`, le constructeur recevant un contexte fourni rejette :

```js
if (typeof WebGLRenderingContext !== 'undefined' && context instanceof WebGLRenderingContext) {
  throw new Error('THREE.WebGLRenderer: WebGL 1 is not supported since r163.');
}
```

Une reproduction Node utilisant **le vrai constructeur Three 0.186.1** et la chaîne de prototypes indiquée par Expo produit cette erreur avant l’initialisation GL. Cela établit une incompatibilité entre ces deux comportements de sources, **pas** l’observation d’un crash dans le binaire Expo Go de l’utilisateur. Un contournement consistant à supprimer un constructeur global ou masquer les capacités ne constituerait pas une intégration durable. Il faudrait vérifier une correction officiellement prise en charge ou un adaptateur testé, sans masquer les warnings ni les incompatibilités.

`expo-three@8.0.0` propose des adapters de chargement et un faux canvas, mais impose Three `^0.166.0` ; installer la dernière version de Three avec cet adapter ne respecte donc pas son contrat. React Three Fiber expose bien une entrée native et prend en charge `expo-file-system/legacy`, mais ajoute une couche de rendu React et ne démontre pas à lui seul que ce conflit de contexte et toutes les API GL utilisées sont résolus. Pour une seule scène simple, cette couche n’est pas nécessaire à priori.

## Proposition d’intégration WebView à vérifier

### Distribution locale

- Une route Expo Router séparée de l’UniversePager, accessible depuis Musculation ; les swipes validés ne sont pas modifiés.
- WebView `13.16.1`, version recommandée par Expo SDK57 ; Three épinglé à une version testée avec son GLTFLoader correspondant.
- Un bundle JS navigateur produit au build et livré localement avec l’HTML, le GLB et les éventuels décodeurs. Aucun CDN, import distant, Google Font ou chargement réseau à l’ouverture de la carte.
- Aucun accès SQLite depuis la WebView. Le contrat RN ↔ scène transporte uniquement des événements validés (`ready`, `selection`, `cleared`, `error`, état de cycle de vie).
- Bloquer les navigations externes et ressources distantes. `originWhitelist` seul n’est pas une politique de sécurité complète ; le document local doit aussi limiter ses ressources et ne contenir aucune URL externe d’exécution.
- L’API `allowingReadAccessToURL` existe dans la version 13.16.1 et ne s’applique qu’à un `source.uri` de type `file://`. Restreindre la lecture au dossier propre à la carte. Tester effectivement les lectures des ressources relatives dans WKWebView ; ne pas supposer que `fetch(file://…)` et les modules ES locaux sont interchangeables.
- Un HTML autonome avec GLB encodé évite certains problèmes de ressources relatives, mais crée un surcoût mémoire concret : base64 ~4/3 des octets, chaîne JS, ArrayBuffer décodé puis buffers GPU. À évaluer seulement après mesure de la taille du modèle ; ne pas dupliquer un gros GLB dans des messages répétés du bridge.
- Dans Expo Go, le premier chargement du bundle de développement et de ses assets nécessite Metro. « Hors ligne » signifie ensuite que la carte n’effectue aucun appel serveur propre ; une application standalone pourra embarquer l’ensemble. Vérifier le mode avion après chargement, sans promettre qu’une session Expo Go jamais chargée s’ouvre hors ligne.

### Rendu et interaction

- Un canvas WebGL2, pas une image 2D ; vérifier la création du contexte et présenter une erreur lisible si impossible.
- Matériaux satinés gris bleuté, éclairage doux, fond bleu nuit ; d’abord sans textures lourdes ni post-traitement. La qualité dépend surtout du vrai mesh et des normales.
- Rotation horizontale uniquement, angle libre 360°, verticale stable ; pas d’OrbitControls autorisant accidentellement pinch/pan/zoom. Gestes directement dans le canvas, sans émission d’angle vers React à chaque frame.
- Tap distingué d’un drag grâce au déplacement maximal depuis le début et au nombre de pointeurs ; un drag revenu à son origine reste un drag. Annulation et multi-touch ne sélectionnent pas. Les seuils de la carte ne modifient pas ceux de l’UniversePager.
- Raycasting sur les triangles réellement visibles. L’identification doit provenir de métadonnées anatomiques conservées, jamais d’une zone tactile ou du nom approximatif d’un muscle.
- Caméra : conserver le vecteur d’orientation actuel et interpoler cible/distance vers la bounding box du groupe sélectionné. Pas de réinitialisation de l’azimut. Limiter le rapprochement avec une distance de sécurité et near plane adaptés ; vérifier profil et dos.
- Le retour restaure le cadrage corps entier avec l’orientation choisie. Une nouvelle sélection pendant un mouvement commence depuis la pose de caméra courante, sans saut.
- Un panneau RN accessible est une option simple pour le nom et exactement les trois indicateurs neutres ; réserver son espace au cadrage sélectionné pour ne pas masquer la région utile. Aucune statistique SQLite n’est calculée en M4A.

### Cycle de vie et budget

- Rendu à la demande : RAF uniquement pendant gestes/transition/chargement ; une vue immobile ne nécessite pas 60 rendus par seconde.
- Arrêter la boucle lors du blur de route, de l’arrière-plan et du démontage. AppState RN et événement de visibilité du document complètent la suspension automatique de WebKit.
- `renderer.dispose()`, `geometry.dispose()`, `material.dispose()`, textures/contrôles/listeners/RAF libérés ; annuler ou ignorer les chargements asynchrones après démontage.
- Traiter `onContentProcessDidTerminate` sur iOS : erreur propre et réouverture/rechargement contrôlé de la seule scène, jamais réinitialisation des données de Logbook.
- Conserver les identités gauche/droite dans les meshes même si plusieurs meshes utilisent le même matériau de base. Cloner ou gérer distinctement le matériau sélectionné afin de ne pas recolorer tout le corps.
- Mesurer `renderer.info` (triangles/draw calls/géométries/textures), temps de chargement, frame times en rotation, temps de fermeture/réouverture et comportement mémoire sur iPhone. Aucune promesse de 60 FPS ou budget d’asset final avant ces mesures.

## Tests à prévoir une fois l’asset disponible

1. Validation du manifeste des meshes : IDs uniques, left/right, association anatomique justifiée, géométries référencées présentes.
2. Raycasting réel sur un GLB connu : pectoraux, deltoïde et grand dorsal, premier hit visible.
3. Geste : tap, drag, aller-retour, multi-touch, cancellation ; zéro sélection accidentelle pendant rotation.
4. Caméra : continuité pendant interruption, dos/profil conservés, distances bornées, retour cadrage entier.
5. Panneau : trois valeurs neutres exactes, fermeture, changement de sélection ; aucune lecture/écriture SQLite.
6. Messages natifs : types/IDs autorisés, erreur chargement, stale callback après fermeture, interruption processus.
7. Test navigateur local avec le vrai bundle et GLB pour le rendu ; distinct de la validation tactile/GPU Expo Go.
8. Suite Logbook existante, TypeScript, export iOS, CI. Puis guide iPhone avec mode avion, arrière-plan et ouvertures/fermetures répétées.

## Sources vérifiables

- Versions Expo SDK57 installées : `node_modules/expo/bundledNativeModules.json` du projet (Expo 57.0.28).
- Documentation Expo GL SDK57, source officielle : https://github.com/expo/expo/blob/main/docs/pages/versions/v57.0.0/sdk/gl-view.mdx
- Documentation Expo WebView SDK57, source officielle : https://github.com/expo/expo/blob/main/docs/pages/versions/v57.0.0/sdk/webview.mdx
- Métadonnées npm exactes : https://registry.npmjs.org/expo-gl/57.0.2 ; https://registry.npmjs.org/react-native-webview/13.16.1 ; https://registry.npmjs.org/three/0.186.1 ; https://registry.npmjs.org/expo-three/8.0.0 ; https://registry.npmjs.org/@react-three/fiber/9.8.2
- Source Expo GL au gitHead de l’archive examinée : https://github.com/expo/expo/blob/b9503d06b8e130abfca1bc16f671dbefb41ad709/packages/expo-gl/common/EXWebGLRenderer.cpp
- Three : https://github.com/mrdoob/three (source exacte auditée dans l’archive npm 0.186.1, `src/renderers/WebGLRenderer.js` et `examples/jsm/loaders/GLTFLoader.js`).
- React Native WebView : https://github.com/react-native-webview/react-native-webview (API exacte auditée dans l’archive npm 13.16.1, `lib/WebViewTypes.d.ts`).

L’accès à npm et aux sources GitHub a réellement réussi via le proxy configuré. La documentation sur `docs.expo.dev` n’était pas nécessaire à cet audit : son contenu officiel versionné a été lu sur GitHub. L’état des fichiers BodyParts3D relève d’un audit séparé ; rien dans ce document n’atteste que le modèle anatomique a été récupéré ou inspecté.
