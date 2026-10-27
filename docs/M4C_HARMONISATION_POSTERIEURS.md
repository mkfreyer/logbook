# M4C — harmonisation du postérieur gauche sur la référence droite

**Proposition à valider**, depuis `977f68a`, PR #17 en brouillon.
Seul le masque `deltoid.left.posterior` (**ID 5**) est adapté. Le postérieur
droit (**ID 8**) reste la référence immuable.

## Rendus

- [Deux épaules directement de dos, grand format](m4c/meshy-posterieurs-harmonises/renders/apres-dos-grand.png)
- [Épaule gauche avant / après](m4c/meshy-posterieurs-harmonises/renders/comparatif-gauche.png)
- [Trois quarts arrière gauche](m4c/meshy-posterieurs-harmonises/renders/apres-trois-quarts-arriere-gauche.png)
- [Trois quarts arrière droit](m4c/meshy-posterieurs-harmonises/renders/apres-trois-quarts-arriere-droit.png)
- [Comparaison en miroir des rendus colorés](m4c/meshy-posterieurs-harmonises/renders/comparaison-miroir-couleur.png)
- [Superposition des silhouettes avant / après](m4c/meshy-posterieurs-harmonises/renders/comparaison-silhouettes-miroir.png)
- [Comparatif de dos](m4c/meshy-posterieurs-harmonises/renders/comparatif-dos.png)

Les rendus colorés conservent le matériau mat et l’éclairage du modèle. Le
miroir est appliqué uniquement à l’image gauche de la planche comparative.
Les silhouettes sont de vrais rendus des poids de masque sans éclairage,
avec des caméras et une échelle identiques ; leur superposition est un
diagnostic graphique, pas une retouche de l’asset.

## Méthode et changements

Le contour droit validé est reconstruit à partir de ses guides supérieur et
inférieur, puis échantillonné sur sa surface réelle. Les **points guides 3D**
sont réfléchis autour du plan médian et reprojetés sur les triangles existants
de l’épaule gauche. L’écart de projection moyen est d’environ **1,43 mm**, le
maximum **3,88 mm**. Cette adaptation conserve les différences locales de forme
du Meshy ; aucun pixel UV n’est recopié ou inversé pour fabriquer le masque.

Une courbe régulière issue de ces points est à nouveau projetée sur la gauche,
puis peinte dans ses propres UV. Le raccord vert/bleu existant est verrouillé,
avec une transition progressive vers la zone adaptée. Les marges UV suivent
le champ du triangle voisin pour éviter les dents aux coutures.

Le bord inférieur gauche est régularisé et son lobe trop long est réduit.
Le haut médial est aussi élargi pour retrouver l’arrondi et une proportion
visuelle comparables à droite. **Ce n’est donc pas une réduction uniforme** :
l’atlas compte **6 561 texels ajoutés** et **263 retirés** pour l’ID 5.
Ces nombres incluent les marges UV et ne mesurent ni le volume du muscle ni
sa surface anatomique. Un trou de seuil d’un texel au raccord est résolu et
34 texels isolés de marge vide sont retirés.

Les différences restantes aux raccords et à la pointe sont liées à la
géométrie gauche et aux frontières conservées. L’objectif est une symétrie
visuelle naturelle, pas une identité artificielle des deux épaules.

Sur les silhouettes rendues à échelle égale, le recouvrement intersection/union
en miroir passe de **79,0 % à 93,4 %**. L’aire projetée gauche représente
**96,8 %** de celle de droite après adaptation, contre 80,9 % auparavant.
Ces mesures concernent uniquement ce cadrage, pas les volumes anatomiques.

## Préservation et contrôles

- Le masque droit et les six autres PNG sont **identiques octet pour octet**.
  Les canaux G/B/A du second pack RGBA sont inchangés ; seul R porte le nouvel
  ID 5. Le premier pack est entièrement inchangé. Les huit IDs sont conservés.
- **1 157 texels** du raccord gauche protégé gardent leur couverture exacte.
  Aucun texel bleu ou rouge n’est déplacé et aucune autre couverture n’est
  recouverte par le nouveau masque.
- Une composante par zone après recollage des coutures UV, aucun trou interne
  détecté sur les texels contrôlés. Huit raycasts Three.js source/export passent.
- Positions, normales, UV et indices sont identiques dans Blender et le GLB :
  **110 588 triangles**, 55 288 sommets Blender et 60 622 sommets exportés avec
  les doublons UV existants. Aucun coût géométrique supplémentaire.
- Neuf vrais rendus Blender. Le neutre de face et la silhouette droite sans
  éclairage sont identiques pixel par pixel à la référence. Le rendu droit
  coloré présente au maximum un niveau d’écart sur 255 ; ses masques restent
  strictement identiques.
- Les 134 fichiers applicatifs protégés restent identiques : Meshy `e45e5d8`,
  visualiseur Expo SDK 58, fonctionnalités de Logbook et SQLite. Aucune nouvelle
  mesure sur iPhone n’est revendiquée.

[Audit des données](m4c/meshy-posterieurs-harmonises/verification.json) ·
[Continuité](m4c/meshy-posterieurs-harmonises/continuity-audit.json) ·
[Caméras et comparaison des silhouettes](m4c/meshy-posterieurs-harmonises/render-verification.json).

## Sources

[Blender éditable](m4c/meshy-posterieurs-harmonises/meshy-posterieurs-harmonises.blend) ·
[Masque gauche ID 5](m4c/meshy-posterieurs-harmonises/textures/deltoid.left.posterior.png) ·
[GLB de contrôle](m4c/meshy-posterieurs-harmonises/exports/meshy-eight-zones-control.glb) ·
[Sources complètes et reproduction](m4c/meshy-posterieurs-harmonises/README.md).

Cette segmentation fitness sur un Meshy généré reste une proposition visuelle,
sans certification anatomique médicale. Toutes les versions précédentes sont
préservées. **Arrêt pour votre validation**, sans fusion, intégration ni suite M4C.

Model created with Meshy — [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
