# M4B — Premier visualiseur Meshy interactif

Prototype isolé sur `feat/m4b-visualiseur-meshy-iphone`, à partir du socle
applicatif M3.4C `7c2aa5c` et du mannequin validé M4A **`e45e5d8`**.
La PR #12 et ses deux lignées de modèles restent intactes et en brouillon.
Aucune fusion, migration SQLite, modification des données personnelles,
segmentation anatomique ou carte thermique.

## Technologie retenue

**Three.js 0.186.1 dans une WebView locale**, avec GLTFLoader et OrbitControls.
`react-native-webview` **13.16.1** est la version du catalogue SDK 57 et est
[incluse dans Expo Go pour ce SDK](https://docs.expo.dev/versions/v57.0.0/sdk/webview/).
Le chargement local utilise `expo-asset` 57.0.20 et `expo-file-system` déjà présent.
Le fichier GLB est déclaré comme asset Metro. Aucun nouveau code natif ni plugin
exigeant un rebuild du client Expo Go SDK 57.

`expo-gl` est aussi une possibilité gratuite ; une intégration Three.js native
nécessiterait davantage d’adaptations de chargement et d’événements DOM.
La WebView fournit ces API au GLTFLoader/OrbitControls et isole ses gestes de la
navigation React Native. [Documentation GLView](https://docs.expo.dev/versions/v57.0.0/sdk/gl-view/).
Le choix vise la simplicité de ce premier prototype, pas une supériorité de
performances mesurée sur iPhone.

Three.js et son code de chargement/contrôle sont compilés par esbuild en un
bundle local versionné. Aucun import HTTP, CDN, génération Meshy ou service payant.
[OrbitControls](https://threejs.org/docs/#OrbitControls) et
[GLTFLoader](https://threejs.org/docs/#GLTFLoader) sont ceux de la même version.
La licence MIT de Three.js accompagne le bundle.

## Modèle et rendu

Le GLB dans `assets/models/meshy-e45e5d8.glb` est une copie **binaire exacte**
de `docs/m4a/meshy-finition-locale-cou/meshy-corps-tete-assemble.glb` au commit
M4A validé : **1 993 204 octets, 110 588 triangles**, un maillage, un matériau,
aucune texture. [Empreinte et attribution](../assets/models/README.md).
Aucune décimation, sculpture ou régénération des normales du modèle.

Le groupe de scène est seulement recentré ; ses buffers de géométrie restent
inchangés. Fond sombre Logbook, matériau neutre chargé depuis le GLB,
éclairage simple sans ombres coûteuses. La densité du canvas est plafonnée à
1,75 ; cela réduit le coût de pixels, sans dégrader le mesh.

Une page dédiée `/muscle-viewer` est accessible par un lien discret dans
Musculation. Les parcours programmes, séances, chrono, historiques, exercices
et paramètres ne sont pas réécrits. Aucun appel à un repository de données
depuis le visualiseur.

## Gestes et caméra

- Rotation horizontale à 360° à un doigt, avec inclinaison verticale limitée pour
  éviter les retournements.
- Zoom/dézoom par pincement, déplacement vertical à deux doigts.
- **Vue générale** : cadrage entier et vue de face ; **Face** : orientation
  frontale avec le zoom courant conservé.

Le cadrage dépend des dimensions réelles du canvas et des bornes du modèle.
Les cibles restent sur l’axe vertical du corps. La distance minimale tient
compte du rayon horizontal et de l’inclinaison autorisée : la caméra reste hors
cylindre enveloppant. Aucun zoom anatomique automatique ni sélection simulée.

Le rendu est demandé uniquement lors d’un changement de caméra, d’un chargement
ou d’un redimensionnement, y compris la fin d’amortissement. À l’inactivité il
ne conserve pas une boucle de rendu permanente.
La fermeture, la perte de focus ou le passage en arrière-plan détruisent la
WebView ; le moteur expose aussi une libération de ses géométries, matériaux,
écouteurs, RAF et contexte WebGL. Une interruption du processus de rendu donne
un état explicite avec **Réessayer**, pas un écran noir silencieux.

## Architecture future, sans faux muscles

`SurfaceHit` contient seulement l’identifiant **technique de l’asset**, un point
en coordonnées du maillage, l’index du triangle et les UV lorsqu’ils existent.
Un tap réel est testé par Raycaster ; le callback ne change aucune couleur,
n’affiche aucune statistique et n’invente aucun identifiant musculaire.

La frontière est : `surface touchée → SurfaceHit → futur résolveur anatomique`.
Les masques, la coloration par région, le focus sur un muscle et les statistiques
viendront après validation de régions adaptées au Meshy. Un index de triangle
n’est pas un identifiant anatomique durable ; une future variante optimisée
exigera une correspondance propre et un autre identifiant d’asset.
Les six zones de deltoïdes P4 appartiennent à l’ancien mannequin, **pas à ce GLB**.

La caméra, le protocole de messages, le chargement d’asset, l’écran natif et le
moteur web sont séparés dans `src/features/model3d/`. Les messages entrants sont
validés. Le HTML est local, les connexions externes sont interdites par CSP et
les navigations de WebView sont limitées à son document local.

## Hors ligne et iPhone

Le visualiseur lui-même n’utilise aucun serveur distant. Le modèle et le moteur
sont embarqués dans l’export iOS. Expo Go reste néanmoins un client de
**développement**, pouvant nécessiter Metro au lancement : cela ne prouve pas
une relance autonome de Logbook en mode avion après installation d’un IPA.
Aucun IPA signé n’est produit et aucun service de compilation payant n’est utilisé.

La compatibilité du client Expo Go installé sur l’iPhone de l’utilisateur est
**encore à vérifier**. Le module est compatible avec le client SDK 57 ; cela ne
signifie pas que toute version App Store d’Expo Go accepte ce SDK.
[Guide Windows → iPhone, prérequis et limites](M4B_GUIDE_IPHONE_WINDOWS.md).

## Contrôles et limites de mesure

TypeScript, les 545 tests, le mode diagnostic du pager et l’export JavaScript
iOS ont réussi. Le contrôle Expo en ligne signale aussi des recommandations
de correctifs préexistantes du socle, détaillées dans le relevé ; aucune mise
à niveau générale n’est appliquée.

Les commandes et résultats définitifs sont consignés dans
[le relevé de validation](m4b/VALIDATION.md).
Les tests du moteur utilisent un **vrai WebGL Chromium/SwiftShader avec gestes
émulés**, pas un moteur 3D simulé. Les tests React Native portent uniquement
sur le protocole, les états, la navigation et le cycle de vie ; leur WebView
mockée n’est pas présentée comme une validation graphique.

Les buffers typés de géométrie chargés dans le test du moteur représentent
**1 990 440 octets**. Ce chiffre n’est ni la mémoire totale du processus iPhone,
ni une mesure complète de la VRAM : HTML/base64, moteur JS et buffers de rendu
ajoutent une consommation supplémentaire. Aucun FPS, RAM iPhone ou stabilité
WKWebView sur appareil réel n’est annoncé sans cet essai.

L’apparence Three.js diffère de Blender par son éclairage ; le fichier modèle
et ses normales sont conservés. L’essai physique iPhone reste une condition
explicite de validation, notamment pour les gestes et ouvertures répétées.

**Arrêt après cette première intégration.** Aucune segmentation ni carte
thermique, aucun calcul de volume musculaire, aucune fusion automatique.
