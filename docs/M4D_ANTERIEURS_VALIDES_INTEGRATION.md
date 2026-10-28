# M4D-A — les deux contours antérieurs validés dans le visualiseur interactif

Les contours droit et gauche de la PR #19 (`09c61ab`) ont été validés par
l'utilisateur. M4C les publie dans la PR #17 au commit `d552e23` ; cette référence
est synchronisée dans la branche de la PR #18 sans réécrire l'historique.
**La branche et les fichiers de la PR #19 restent à `09c61ab`, inchangés.**

## Ce qui arrive dans l'application

Le pipeline existant `tools/m4d/build-selection.mjs` lit désormais
`docs/m4c/meshy-anterieurs-valides/`. Il régénère :

- `assets/models/meshy-m4d-uv.glb` : **2 606 320 octets**, géométrie/UV de la
  référence approuvée et matériaux neutres exacts du maître Meshy ;
- `src/features/model3d/generated/selectionData.ts` : l'atlas d'identification
  approuvé, embarqué dans le visualiseur ;
- `src/features/model3d/generated/viewerBundle.ts` avec `npm run viewer:build`.

**Le GLB de contrôle coloré n'est pas copié directement comme mannequin de
l'application.** Le générateur enlève ses images, textures et matériaux de
contrôle, puis remet les matériaux neutres de `meshy-e45e5d8.glb`. Seul le muscle
sélectionné reçoit l'orange du shader existant.

L'atlas d'identification de l'application est identique octet pour octet à celui
de `09c61ab`. Il fait 32 015 octets en PNG, à résolution inchangée 2 048² ; les
tampons CPU et GPU restent à 4 Mio chacun. Le GLB gagne 168 octets de métadonnées
par rapport à la version restaurée, sans ajout géométrique.

Les six masques protégés sont identiques à `06fa665`. Les huit IDs, noms français,
réinitialisation, rotation, pincement, déplacement vertical et boutons existants
sont conservés. Aucun code d'interface, de caméra, de gestes, de shader ou de
stockage n'est modifié. Seuls les fichiers générés changent dans `src/`.

## Captures du visualiseur

Ce sont de vraies captures du contenu WebGL local dans Chromium/SwiftShader,
avec événements tactiles CDP, **pas des captures d'un iPhone**.

- [Antérieur droit orange](m4d/anterieurs-valides/anterieur-droit-orange.png)
  ([capture complète](m4d/anterieurs-valides/selection-deltoid.right.anterior.png)).
- [Antérieur gauche orange](m4d/anterieurs-valides/anterieur-gauche-orange.png)
  ([capture complète](m4d/anterieurs-valides/selection-deltoid.left.anterior.png)).
- [Comparaison de face](m4d/anterieurs-valides/comparaison-face-anterieurs.png) :
  deux captures successives avec la même caméra, une seule zone active par
  capture, conformément au comportement existant.
- [Planche des huit sélections](m4d/anterieurs-valides/planche-huit-selections.png).
- [Vue générale neutre](m4d/anterieurs-valides/neutre-vue-generale.png) et
  [sélection réinitialisée](m4d/anterieurs-valides/selection-reinitialisee.png).

Les recadrages sont documentés dans
[`capture-provenance.json`](m4d/anterieurs-valides/capture-provenance.json).
Aucun pixel du mannequin n'est repeint ou combiné entre deux états de sélection.

## Vérifications exécutées

| Contrôle | Résultat / preuve |
| --- | --- |
| Atlas réel du visualiseur = `09c61ab` | [Audit des ressources](m4d/anterieurs-valides/asset-verification.json) |
| Six masques protégés et deux antérieurs exacts | Même audit, comparaison aux objets Git `06fa665` / `09c61ab` |
| Huit IDs, interfaces antérieur/moyen, coutures, absence de trous/chevauchements | [Audit M4C](m4c/meshy-anterieurs-valides/verification.json) et [continuité](m4c/meshy-anterieurs-valides/continuity-audit.json) |
| GLB neutre, positions/normales/UV/indices exacts | Audit des ressources et tests du modèle |
| `npm run viewer:check` | [Journal](m4d/anterieurs-valides/controle-ressources.txt) |
| `npm run typecheck` | [Journal](m4d/anterieurs-valides/controle-types.txt) |
| Suite complète `npm test` | **552 réussis** : 219 données, 13 navigation, 310 UI, 9 modèle/sélection, 1 préservation SQLite v8 ; [journal](m4d/anterieurs-valides/controle-tests.txt) |
| Huit sélections WebGL, orange, noms, changement direct, réinitialisation | [Résultats tactiles](m4d/anterieurs-valides/browser-verification.json) |
| Rotation complète, zoom/dézoom, limites, déplacement vertical, Face, Vue générale et nettoyage | [Régression WebGL](m4d/anterieurs-valides/viewer-regression.json) |
| Export JavaScript iOS | [Journal](m4d/anterieurs-valides/controle-ios.txt) |
| CI GitHub | Contrôles des PR #17 et #18 ; liens des exécutions dans leurs descriptions |

Le test du reset vérifie la suppression de l'orange sur les huit sélections,
puis la conservation du cadrage depuis une vue zoomée/déplacée stabilisée par
le bouton Face. Cela évite de confondre l'inertie résiduelle du moteur logiciel
avec un déplacement causé par le reset. Le code de production des gestes ne
change pas. Les commandes Face et Vue générale conservent aussi la sélection.

**Géométrie :** 110 588 triangles, aucun ajout et aucun déplacement de sommet.
Le maître Meshy `e45e5d8` garde son SHA-256
`421e593cad17f60d1c0c5e67707729fb88bbf69026795e22011ecc7d90b38959`.
Les fichiers applicatifs hors données générées, l'identité Expo, les chemins de
stockage, le schéma SQLite v8 et les dépendances verrouillées restent identiques
à `fd737ca`. Aucune migration ni suppression de données.

## Diagnostic Expo, distinct du transfert des masques

Le contrôle local hors ligne du SDK installé passe, avec l'avertissement habituel
d'Expo sur les limites d'une vérification hors ligne. La CI utilise également
ce contrôle. Les dépendances verrouillées de la version déjà testée sont conservées.

Le diagnostic **en ligne** a renvoyé un code non nul car le service Expo recommande
désormais trois correctifs plus récents du même SDK 58 :

| Paquet | Verrouillé | Recommandation en ligne |
| --- | --- | --- |
| `expo` | `58.0.19` | `~58.0.20` |
| `expo-file-system` | `58.0.11` | `~58.0.12` |
| `expo-router` | `58.0.26` | `~58.0.27` |

Ces correctifs ne sont pas appliqués dans cette livraison limitée aux masques.
Le [journal en ligne](m4d/anterieurs-valides/diagnostic-expo-en-ligne.txt) et le
[journal hors ligne](m4d/anterieurs-valides/controle-expo-hors-ligne.txt) sont
conservés ; le diagnostic en ligne n'est pas présenté comme réussi. Le projet
reste en SDK 58. La validation de cette nouvelle version sur l'iPhone réel reste
à effectuer par l'utilisateur.

## Lancer le test Windows → iPhone

Suivre le [guide PowerShell non destructif](M4D_ANTERIEURS_VALIDES_GUIDE_IPHONE_WINDOWS.md).
Il commence par `git status`, récupère la branche et crée un dossier de test
séparé sans toucher aux modifications du dossier actuel. Il utilise `npm.cmd ci`
puis `npx.cmd expo start --go --lan`. Aucune remise à zéro, réinstallation d'Expo
Go ou suppression de données.

PR #17 et #18 maintenues en brouillon, PR #19 intacte. Aucune PR fusionnée.
**Arrêt après livraison : attendre le test personnel sur iPhone avant la suite.**
