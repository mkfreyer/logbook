# M4B — migration contrôlée Expo SDK 57 → 58

Base : PR #15, `325ef229fedc3409cc390a651e8776eed96822d7`.
Branche distincte : `feat/m4b-migration-expo-sdk58`, destinée à une nouvelle PR
en brouillon reposant sur la branche de la PR #15. Aucune fusion des PR #12/#15.

## Résultat et périmètre

Le projet cible maintenant **Expo SDK 58 / React Native 0.88.0**, pour le client
Expo Go SDK 58 signalé sur l’iPhone. La validation physique de ce client reste
à effectuer par l’utilisateur. Cette migration ne produit pas de binaire IPA.

Les changements applicatifs sont limités à **deux adaptations de types** :

- `UniverseContext` utilise le type du constructeur `Gesture.Pan` déjà employé.
  Gesture Handler 3 expose désormais sous le nom `PanGesture` le type de sa
  nouvelle API à hooks ; l’ancienne API de construction reste prise en charge.
  Les décisions de reconnaissance et le pager ne sont pas réécrits.
- `ModelViewer` précise `WebView<unknown>` pour la référence et le JSX.
  WebView 14.0.1 déclare par défaut son paramètre supplémentaire `P = undefined`
  et ses propriétés `WebViewProps & P`, ce qui produit `never` avec les types
  actuels. `unknown` est ici l’élément neutre de l’intersection : toutes les
  propriétés WebView restent vérifiées, sans cast ni désactivation TypeScript.

Après effacement des types et commentaires, le JavaScript émis par TypeScript
pour ces deux fichiers est identique à celui de la base. Les autres fichiers
d’exécution comparés sont identiques octet pour octet ; voir
[les empreintes de préservation](m4b-sdk58/preservation-hashes.json).

## Dépendances

Versions verrouillées dans `package-lock.json` ; aucun passage au SDK 59.

| Dépendance | Base SDK 57 | Migration SDK 58 |
| --- | --- | --- |
| expo | 57.0.28 | 58.0.19 |
| React / React DOM | 19.2.3 | 19.3.0 |
| React Native | 0.86.3 | 0.88.0 |
| Expo Router | 57.0.26 | 58.0.26 |
| WebView | 13.16.1 | 14.0.1 |
| Reanimated | 4.5.1 | 4.7.1 |
| Worklets | 0.10.1 | 0.13.0 |
| Gesture Handler | 2.32.0 | 3.3.0 |
| Screens | 4.26.2 | 4.30.0 |
| Safe Area Context | 5.7.0 | 5.10.1 |
| SVG | 15.15.4 | 15.16.0 |
| Expo SQLite (module natif) | 57.0.4 | 58.0.14 |
| Jest / jest-expo | 29.7.0 / 57.0.6 | 30.5.2 / 58.0.12 |
| React Native Testing Library | 13.3.3 | 14.1.0 |
| Renderer des tests | react-test-renderer 19.2.3 | test-renderer 1.3.0 |

Les modules Asset, Audio, Constants, Crypto, File System, Font, Linking,
Sharing, Linear Gradient, Status Bar, System UI, Metro Runtime et Babel suivent
également le catalogue du SDK 58 installé. Three.js **0.186.1**, esbuild
**0.28.2**, Playwright **1.64.1** et TypeScript **6.0.3** restent inchangés.

Node.js **24 LTS** est utilisé pour les vérifications et recommandé sur Windows.
Le premier alignement npm a rencontré des conflits de pairs pendant le passage
entre versions. Les dépendances de test ont été alignées avec Expo Router 58
et Jest Expo 58, puis le verrou a été régénéré et vérifié avec `npm ci`.
Aucun `--force`, `--legacy-peer-deps` ou exclusion des contrôles Expo.

## Changements incompatibles examinés

La Strict TypeScript API de RN 0.88 est active. Aucun usage applicatif des
imports profonds `react-native/Libraries/*`, de `InteractionManager`, du type
racine `Touchable`, de `Modal.animated` ou des anciennes propriétés StatusBar
retirées n’a été trouvé. Aucun remplacement métier n’a donc été nécessaire.
Les propriétés et événements WebView sont toujours typés. `tsconfig.json`
conserve ses règles strictes ; aucun `@ts-ignore` ou cast `any` ajouté.

Le dépôt ne contient pas de projet natif iOS/Android personnalisé : les
changements AppDelegate/SceneDelegate relèvent ici du client Expo Go SDK 58.
Pas de `prebuild`, changement de moteur Hermes ou ajout de module natif hors Go.
Les configurations Metro (extension `.glb`) et Babel sont conservées.
Pas d’activation nouvelle du React Compiler dans cette migration ciblée.

Expo Router 58 impose la bibliothèque de test 14 comme pair optionnel lorsqu’elle
est installée. Ses opérations `render`, `renderHook`, `act`, `fireEvent`,
`rerender`, `unmount` et `cleanup` sont désormais attendues explicitement.
Les scénarios et assertions existants sont conservés. Les quelques anciennes
requêtes `UNSAFE_*` sont remplacées par des requêtes publiques ou une inspection
des éléments hôtes ; les doubles événements synchrones testent encore les
verrous anti double action via les événements natifs.

Les tests du pager incluent maintenant `GestureHandlerRootView`, comme le fait
déjà le véritable `_layout`. En Jest seulement, l’initialiseur natif Reanimated
est neutralisé : le mock officiel 4.7 importe son index qui tente d’enregistrer
un dispatcher CSS absent du backend JS de test. Le mock officiel reste utilisé
pour l’animation. Ceci ne remplace pas les tests natifs sur appareil et ne
modifie aucun code livré à Expo Go.

## Données et ressources préservées

- `app.json` inchangé : nom, slug `logbook`, scheme `logbook`, version `0.1.0`,
  bundleIdentifier `com.mkfreyer.logbook` et plugins conservés.
- `src/db/migrations.ts` et tout le code SQLite inchangés : schéma **v8**,
  même nom **`logbook.db`**, aucun nouveau script de migration ni effacement.
- Export personnel : même dossier `logbook-personal-exports` et mêmes APIs
  File System / Sharing, sans modification de l’exporteur.
- Nouveau test sur une base temporaire v8 remplie : réouverture, initialisation,
  reprise d’une séance avec repos en pause, historique terminé, préférences,
  comparaison de toutes les lignes, du schéma et d’un export JSON déterministe.
  Les tests SQLite utilisent le moteur SQLite Node, pas le binaire natif iOS.
- GLB validé `e45e5d8` : **1 993 204 octets**, **110 588 triangles**, SHA-256
  `421e593cad17f60d1c0c5e67707729fb88bbf69026795e22011ecc7d90b38959`.
  Fichier et moteur Three.js embarqué inchangés ; aucune retouche anatomique.

## Vérification et limites

Les résultats détaillés sont consignés dans
[la validation SDK 58](m4b-sdk58/VALIDATION.md).
La CI contrôle désormais aussi la cohérence avec le catalogue Expo installé,
sans dépendre du service distant pour ce contrôle.

`expo-doctor` a été exécuté : **18/20 contrôles validés**. Deux contrôles restent
non concluants dans cet environnement : schéma de configuration via l’API Expo
et métadonnées React Native Directory. L’accès à `exp.host` est refusé par la
politique réseau du conteneur (HTTP CONNECT 403) ; la vérification Directory
signale une réponse serveur inattendue. Ils ne sont ni désactivés ni comptés comme
réussis. `expo config` résout bien `sdkVersion: 58.0.0`, et le contrôle local des
versions SDK et l’arbre npm sont vérifiés séparément. Relancer `npx.cmd
expo-doctor` sur le PC Windows disposant d’un accès réseau normal.

Les tests navigateur utilisent Chromium/WebGL logiciel sous Linux. Ils
contrôlent le vrai moteur embarqué, mais ne prouvent ni la compatibilité WKWebView
sur cet iPhone ni ses performances GPU. L’export iOS valide le bundle et les
assets, sans exécuter les modules natifs sur un téléphone. Le chargement de
WebView 14, la reconnaissance tactile iOS, l’audio et la conservation effective
du sandbox Expo Go doivent encore être contrôlés sur l’appareil.

## Références suivies

- [Compétence officielle Expo `expo-upgrade`](https://github.com/expo/skills/blob/main/plugins/expo/skills/expo-upgrade/SKILL.md),
  lue et appliquée avec cible explicite SDK 58, conformément au périmètre demandé.
- [Procédure officielle de mise à niveau](https://docs.expo.dev/workflow/upgrading-expo-sdk-walkthrough/).
- [Guide de passage au SDK 58](https://expo.dev/blog/how-to-upgrade-to-sdk-58).
- [Notes de version SDK 58](https://expo.dev/changelog/sdk-58).
- [Migration de la bibliothèque de test 14](https://oss.callstack.com/react-native-testing-library/docs/start/migration-v14).

Pour le prochain essai : [guide Windows → iPhone, commandes `.cmd`](M4B_SDK58_IPHONE_WINDOWS.md).
Arrêt après migration et contrôles ; validation visuelle et fonctionnelle sur
l’iPhone laissée à l’utilisateur avant toute suite.
