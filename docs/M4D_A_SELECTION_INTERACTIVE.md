# M4D-A — Première sélection interactive des huit muscles

La segmentation M4C `06fa665` est intégrée au visualiseur local sous Expo SDK 58. Un toucher bref sélectionne une seule zone, son nom français est affiché et sa surface devient orange. Toucher une autre zone remplace la sélection ; toucher une surface neutre ou le fond, ou utiliser **Réinitialiser la sélection**, remet le mannequin au matériau neutre.

Cette livraison attend le test personnel sur iPhone. Elle n’inclut aucune orientation ou zoom automatique, carte thermique, liaison aux exercices ni nouvelle segmentation.

## Ressources et identification

`assets/models/meshy-e45e5d8.glb` reste inchangé. Le dérivé local `assets/models/meshy-m4d-uv.glb` reprend exactement les positions, normales, indices et UV du GLB de contrôle M4C validé, avec le matériau neutre du master. Les doublons de sommets aux coutures UV existent déjà dans M4C : aucune sculpture, subdivision ou frontière nouvelle.

`tools/m4d/build-selection.mjs` reconstruit ce dérivé et `src/features/model3d/generated/selectionData.ts` depuis les sources `docs/m4c/meshy-posterieurs-harmonises`. L’atlas L8 **2048 × 2048** est repris octet pour octet, sans miroir, rééchantillonnage ni changement de masque. Le contrôle `npm run viewer:check` vérifie les deux fichiers dérivés et le bundle Three.js.

Un raycast Three.js prend **la première intersection visible**, sans traverser une surface neutre pour sélectionner un muscle caché. Son UV glTF donne le texel `floor(uv × dimensions)`. La lecture CPU est entière, sans interpolation ; 0 signifie neutre. Les codes 1 à 8 conservent les identifiants :

| Code | Identifiant | Nom affiché |
| --- | --- | --- |
| 1 | `pectoralis.left` | Grand pectoral gauche |
| 2 | `pectoralis.right` | Grand pectoral droit |
| 3 | `deltoid.left.anterior` | Deltoïde antérieur gauche |
| 4 | `deltoid.left.lateral` | Deltoïde moyen gauche |
| 5 | `deltoid.left.posterior` | Deltoïde postérieur gauche |
| 6 | `deltoid.right.anterior` | Deltoïde antérieur droit |
| 7 | `deltoid.right.lateral` | Deltoïde moyen droit |
| 8 | `deltoid.right.posterior` | Deltoïde postérieur droit |

La lecture ne dépend pas de l’angle de caméra. Gauche et droite sont anatomiques : X positif du modèle = gauche.

## Apparence, gestes et cycle de vie

Le même atlas sert au shader : texture mono-canal `RedFormat`, espace de données sans correction de couleur, filtre `Nearest`, aucun mipmap, aucune inversion V. Le shader remplace uniquement la couleur diffuse dont le code est actif ; le matériau neutre, l’éclairage et les reliefs restent les mêmes. L’orange est défini par `SELECTION_COLOR` dans `src/features/model3d/selection.ts`. Les couleurs de contrôle M4C ne sont pas utilisées.

Le filtre de sélection impose un seul pointeur, un déplacement maximal de 8 pixels CSS sur **tout** le trajet et une durée de 350 ms maximum. Une sortie du seuil, même suivie d’un retour, un deuxième doigt ou une annulation invalide le toucher. Aucun raycast n’est lancé pour une rotation, un pincement ou un appui long. OrbitControls conserve ses réglages, rotation 360°, pincement et déplacement vertical. Les boutons Face et Vue générale conservent leur comportement et la sélection courante.

Le pont WebView n’accepte que les huit IDs connus ou `null`. Les messages périmés sont ignorés après fermeture/arrière-plan ; le nom actif est remis à zéro. Le démontage libère la texture d’IDs, le modèle et le moteur WebGL. Le rendu reste à la demande, sans boucle continue au repos.

## Coût et limites

- 110 588 triangles, inchangés. 60 622 sommets avec UV, contre 55 288 dans le master sans UV.
- GLB runtime : 2 606 152 octets, contre 1 993 204 pour le master ; le master n’est pas chargé simultanément par le visualiseur.
- Atlas PNG local : 31 679 octets, embarqué en base64 dans le bundle ; environ 42 Ko avant compression du bundle.
- Atlas décompressé : **4 Mio sur CPU + 4 Mio sur GPU**, sans mipmaps. Le décodage PNG emploie temporairement une image et un tampon RGBA de 16 Mio chacun ; le canvas est ensuite vidé et seule la copie L8 est conservée. La mémoire totale WebView/iOS dépend du moteur et n’est pas mesurée ici.
- Un raycast sur les 110 588 triangles par toucher admissible, aucune recherche à chaque déplacement et aucun appel réseau. Le coût tactile et les pointes mémoire doivent encore être observés sur l’iPhone réel.
- L’identification utilise le texel entier M4C validé. La frontière de coloration reste limitée à la résolution de l’atlas, particulièrement lors de très forts zooms ; pas de lissage des IDs pouvant inventer une zone.
- Les régions fines demandent une visée précise. Aucun élargissement automatique de cible et aucune sélection à travers le corps.

## Vérifications et captures

Les résultats détaillés sont dans [le dossier de contrôle](m4d/selection-interactive/). Les captures sont de véritables rendus du **visualiseur WebGL**, dans Chromium avec événements tactiles CDP et GPU logiciel SwiftShader, viewport mobile 430 × 760, facteur 1. Elles ne constituent ni des captures de l’interface native complète ni une mesure des performances iPhone.

- [Vue générale neutre](m4d/selection-interactive/neutre-vue-generale.png)
- [Pectoral gauche](m4d/selection-interactive/selection-pectoralis.left.png) · [Droit](m4d/selection-interactive/selection-pectoralis.right.png)
- [Deltoïde antérieur gauche](m4d/selection-interactive/selection-deltoid.left.anterior.png) · [Moyen gauche](m4d/selection-interactive/selection-deltoid.left.lateral.png) · [Postérieur gauche](m4d/selection-interactive/selection-deltoid.left.posterior.png)
- [Deltoïde antérieur droit](m4d/selection-interactive/selection-deltoid.right.anterior.png) · [Moyen droit](m4d/selection-interactive/selection-deltoid.right.lateral.png) · [Postérieur droit](m4d/selection-interactive/selection-deltoid.right.posterior.png)

Les tests couvrent les huit raycasts réels, les côtés anatomiques, l’identité de l’atlas, les coordonnées et normales de chaque triangle par rapport à `e45e5d8`, les messages du pont, les gestes, le nom français, le changement et la réinitialisation, ainsi que l’invalidation des anciens événements WebView.

Voir [le guide PowerShell → iPhone](M4D_A_GUIDE_IPHONE_WINDOWS.md) pour la validation manuelle.

Aucun fichier de programmes, séances, statistiques ou SQLite v8 modifié. PR empilée sur la PR #17, en brouillon, sans fusion. Arrêt après livraison pour test iPhone.

### Résultats de cette livraison

- Cohérence Expo SDK 58 : `npx expo install --check` en ligne, dépendances à jour ; `package-lock.json`, dépendances et identité inchangés.
- TypeScript, génération de l’asset/atlas et bundle embarqué : réussis.
- Suite complète : **551 tests réussis** (219 données, 13 navigation, 310 UI native, 8 modèle/sélection, 1 conservation SQLite v8).
- Diagnostic des gestes activé : **17 tests supplémentaires réussis**.
- Export JavaScript iOS : réussi ; il embarque bien `meshy-m4d-uv.glb`.
- [Contrôle WebGL des huit muscles](m4d/selection-interactive/browser-verification.json) : huit vrais touchers, lecture gauche/droite, changement direct, neutre/fond, appui long ignoré, rotation et pincement préservant la sélection, suppression visible de la surbrillance à la réinitialisation, aucune requête externe, nettoyage réussi.
- [Régression du visualiseur](m4d/selection-interactive/viewer-regression.json) : rotation tactile dépassant 360°, zoom/dézoom et limites, déplacement vertical, Face, Vue générale, rendu arrêté au repos, cinq cycles ouverture/fermeture libérant les géométries et le contexte WebGL, erreur propre sur fichier invalide. Le champ `asset` décrit le master de référence ; le fichier effectivement affiché est le dérivé UV M4D.
- [Vérification des fichiers protégés et journaux](m4d/selection-interactive/verification.json) : master, masques M4C, SQLite v8, identité et dépendances inchangés.
- [Planche des huit sélections](m4d/selection-interactive/planche-huit-selections.png) : recadrages des captures WebGL ; [après réinitialisation](m4d/selection-interactive/selection-reinitialisee.png).

Un premier passage des tests UI a atteint son délai de 5 s sur un test existant, sous charge de deux rendus logiciels simultanés ; la relance complète a réussi sans changer ce test ni son délai. Le banc navigateur utilise des timestamps de toucher explicites pour ses appuis brefs afin que la lenteur du GPU logiciel ne les transforme pas en appuis longs. Le contrôle initial de neutralité pixel pour pixel était trop strict pendant l’amortissement de caméra ; le contrôle final vérifie la suppression visible de l’orange et l’état de sélection, sans annoncer une identité pixel pour pixel entre des cadrages encore en mouvement.

Reproduction :

```sh
node tools/m4d/build-selection.mjs
npm run viewer:build
npm run viewer:check
npm run typecheck
npm test
npm run test:viewer-browser
npm run test:selection-browser
python tools/m4d/compose-captures.py
npm run export:ios
```

Les tests navigateur nécessitent Chromium local avec SwiftShader ; la composition des planches utilise Pillow et la police DejaVu Sans. Aucune de ces dépendances de contrôle n’est ajoutée à l’application.
