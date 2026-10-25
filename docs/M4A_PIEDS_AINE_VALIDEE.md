# M4A — Pieds retouchés avec l’aine de référence confirmée

À la suite du choix **« 41896cc — conserver la dernière finition de l’aine »**,
cette livraison assemble le corps de `41896cc` et les pieds proposés dans
`8a8b95e`. Elle remplace la combinaison précédente, qui conservait l’aine
de `d94297a`. Toutes les versions restent disponibles dans l’historique.

**Aucune nouvelle sculpture.** L’aine n’est pas retouchée. Les deux objets de
pieds sont transférés depuis leur fichier Blender publié, sans reconstruction,
filtrage, déplacement de sommets ni recalcul des normales.

## Rendus pour validation

- [Avant / après : face et trois quarts](m4a/ecorche-beatriz-pieds-aine-validee/renders/comparatif-pieds.png)
- [Profils des deux pieds](m4a/ecorche-beatriz-pieds-aine-validee/renders/comparatif-profils.png)
- [Gros plan cheville / pied](m4a/ecorche-beatriz-pieds-aine-validee/renders/raccords-chevilles.png)
- [Planche générale neutre](m4a/ecorche-beatriz-pieds-aine-validee/renders/planche-generale.png)

Avant : `41896cc`, pieds d’origine. Après : même mannequin et même aine,
avec les deux pieds de `8a8b95e`. Les douze images sont de nouveaux rendus
Blender/Cycles, avec matériau mat neutre, caméras, éclairage et paramètres
identiques entre avant et après. Les planches ajoutent seulement des légendes
et un redimensionnement uniforme.

## Ce qui est conservé

| Source | Éléments | Vérification |
| --- | --- | --- |
| `41896cc` | 297 objets, dont l’aine, la tête P5, la gorge, les deltoïdes et les muscles des jambes | Géométrie brute et évaluée, topologie, normales, matériaux et données associées identiques |
| `8a8b95e` | `m2_c001.left` et `m2_c001.right` | Géométrie, topologie, normales, matériaux et données associées identiques |

Les six identifiants des deltoïdes et leur correspondance avec les matériaux
et primitives du GLB sont conservés. Aucune segmentation supplémentaire.

Les pieds restent symétriques. Les contrôles des contacts enfouis, des
auto-intersections, des formes de l’avant-pied et des fragments sous-jacents
ont été réexécutés sur l’assemblage. Les données de géométrie, normales,
indices et autres attributs des 297 objets conservés sont également comparées
dans les exports GLB.

Les résultats détaillés et empreintes des fichiers figurent dans
[verification.json](m4a/ecorche-beatriz-pieds-aine-validee/verification.json) ;
les contrôles des douze rendus dans
[renders/verification.json](m4a/ecorche-beatriz-pieds-aine-validee/renders/verification.json).

## Géométrie et limites

| Mesure | `41896cc` | Assemblage proposé |
| --- | ---: | ---: |
| Objets de maillage | 299 | 299 |
| Triangles par pied | 10 934 | 16 000 |
| Total Blender | 539 220 | 549 352 |
| Total GLB | 539 219 | 549 351 |

Soit **+10 132 triangles (+1,88 %)** par rapport à `41896cc` ; aucun ajout
par rapport à la réunion des sources choisies. Le GLB fait **11,26 Mo**.
Le triangle d’écart Blender / GLB est le doublon source déjà omis avant ce
travail. Ce modèle reste un asset de validation, sans mesure de performances
dans Logbook.

La finition des pieds est celle de la proposition `8a8b95e` : surface adoucie,
rebord supérieur resserré et raccord local avec les chevilles. Le passage entre
les pieds lisses et l’anatomie disséquée des jambes reste perceptible. Les
contacts sont enfouis dans les volumes existants, sans soudure globale.
Les UV des pieds d’origine n’ont pas été conservés lors de cette précédente
reconstruction ; le matériau actuel est uni.

## Sources et arrêt

[Blender, GLB, filiation et procédure reproductible](m4a/ecorche-beatriz-pieds-aine-validee/README.md).
Le [rapport de la retouche des pieds](M4A_FINITION_PIEDS.md) décrit les modifications
réalisées précédemment ; il demeure conservé comme historique de la combinaison
avec l’ancienne aine.

**Arrêt pour validation visuelle de cet assemblage.** Application et SQLite
inchangées, aucun M4B, PR #12 conservée en brouillon, sans fusion.
