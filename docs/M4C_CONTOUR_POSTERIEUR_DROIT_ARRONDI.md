# M4C — nouveau contour du deltoïde postérieur droit

**Proposition à valider**, depuis `18e1a44`, PR #17 en brouillon.
La ligne orange est interprétée comme le **nouveau contour extérieur** :
du vert est ajouté dans l’espace gris jusqu’à une courbe plus arrondie.
Aucune partie verte existante n’est retirée.

## Rendus

- [Avant / après à l’angle de l’annotation](m4c/meshy-posterieur-droit-arrondi/renders/comparatif-angle-annotation.png)
- [Gros plan sans annotation de la nouvelle frontière](m4c/meshy-posterieur-droit-arrondi/renders/apres-angle-annotation.png)
- [Deux épaules directement de dos](m4c/meshy-posterieur-droit-arrondi/renders/apres-epaules-dos.png)
- [Trois quarts arrière droit](m4c/meshy-posterieur-droit-arrondi/renders/apres-trois-quarts-arriere-droit.png)
- [Trois quarts arrière gauche](m4c/meshy-posterieur-droit-arrondi/renders/apres-trois-quarts-arriere-gauche.png)
- [Comparatifs arrière](m4c/meshy-posterieur-droit-arrondi/renders/comparatif-vues-arriere.png)
- [Profil droit](m4c/meshy-posterieur-droit-arrondi/renders/apres-profil-droit.png) ·
  [Contrôle avant droit](m4c/meshy-posterieur-droit-arrondi/renders/apres-avant-droit.png)

Les caméras sont celles du contrôle arrière précédent. Le comparatif de
référence utilise la même caméra à −135° et un cadrage serré correspondant à
la capture fournie, rendu directement à plus haute résolution. Le matériau
mat et l’éclairage restent identiques. Aucun pixel du mannequin n’est repeint
sur les images de rendu.

## Modification du masque

Des repères de l’annotation définissent une courbe cubique continue,
régularisée pour éviter les petites irrégularités du dessin manuel. Elle est
projetée par raycast sur la **surface réelle** du Meshy. Chaque texel candidat
est ensuite associé à son point 3D et contrôlé par raycast avant peinture UV.
Une tolérance locale de profondeur de 2 mm couvre les fines surfaces
superposées déjà présentes dans le modèle, sans peindre à travers le corps
ni modifier cette géométrie.

Le masque s’élargit sur son bord extérieur et inférieur et se referme
progressivement sur la pointe commune. Les contraintes verrouillent tous les
texels des sept autres zones : les limites existantes vert/bleu et bleu/rouge
ne sont pas déplacées. L’épaule gauche n’est pas retouchée.

**11 436 texels** de l’atlas passent de `0` à `8` ; aucun `8` ne redevient gris.
Cette mesure concerne l’atlas UV et ses marges, pas un volume musculaire.
Le bord d’affichage de l’ID 8 utilise une couverture légèrement adoucie selon
l’empreinte des texels. L’atlas de sélection reste discret : la zone devient
ID 8 à partir d’une couverture de 128/255. Ce traitement concerne uniquement
la frontière vert/gris ; les sept autres masques restent identiques.

Le gros plan montre un contour plus arrondi, sans les petites dents visibles
sur le bord inférieur précédent. La pointe basse reste rattachée à la
convergence des faisceaux. Les vues complémentaires permettent de juger la
couverture du relief de l’épaule : il s’agit d’une proposition de segmentation
fitness sur un Meshy généré, pas d’une certification anatomique médicale.
Le vert droit est désormais plus large que le vert gauche, conservé tel quel :
cette livraison est volontairement limitée au côté demandé.

## Sources et contrôles

- [Blender éditable, textures embarquées](m4c/meshy-posterieur-droit-arrondi/meshy-posterieur-droit-arrondi.blend)
- [Masque postérieur droit éditable](m4c/meshy-posterieur-droit-arrondi/textures/deltoid.right.posterior.png)
- [Atlas d’IDs](m4c/meshy-posterieur-droit-arrondi/textures/muscle-ids.png),
  [pack RGBA](m4c/meshy-posterieur-droit-arrondi/textures/masks-rgba-1.png) et
  [GLB de contrôle](m4c/meshy-posterieur-droit-arrondi/exports/meshy-eight-zones-control.glb)
- [Paramètres de courbe](m4c/meshy-posterieur-droit-arrondi/outline-guides.json),
  [points projetés en 3D](m4c/meshy-posterieur-droit-arrondi/projected-outline.json) et
  [reproduction](m4c/meshy-posterieur-droit-arrondi/README.md)

Contrôles : une composante par zone après recollage des coutures UV, aucun
trou interne détecté sur les texels contrôlés ; cinq impacts 3D dans
l’extension deviennent verts et deux témoins extérieurs restent gris.
Les huit raycasts Three.js sur la source et l’export retrouvent les huit IDs.
Les sept autres masques et les trois autres canaux du pack RGBA sont
identiques octet pour octet.
Le neutre de face est identique pixel par pixel à la référence. La vue colorée
gauche présente au maximum un niveau d’écart sur 255 ; son masque reste
strictement identique.

Positions, normales, UV et indices sont conservés à l’identique dans Blender
et dans le GLB : **110 588 triangles**, 55 288 sommets Blender et 60 622 sommets
exportés avec les doublons UV existants. Coût géométrique supplémentaire :
**zéro**. Les textures restent en 2 048 × 2 048. Les 134 fichiers applicatifs
protégés, le GLB validé `e45e5d8`, le visualiseur SDK 58 et SQLite sont inchangés.
Aucune nouvelle mesure de performances sur iPhone n’est revendiquée.

[Audit des données](m4c/meshy-posterieur-droit-arrondi/verification.json) ·
[Continuité](m4c/meshy-posterieur-droit-arrondi/continuity-audit.json) ·
[Contrôle des rendus](m4c/meshy-posterieur-droit-arrondi/render-verification.json).

Toutes les versions précédentes sont conservées. **Arrêt pour validation
visuelle**, sans intégration, carte thermique, changement applicatif ou fusion.

Model created with Meshy — [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Modification Logbook limitée au masque ID 8 et à ses dérivés.
