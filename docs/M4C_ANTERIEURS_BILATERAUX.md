# M4C — transposition du contour antérieur validé sur l'épaule gauche

**Droit validé conservé ; gauche proposé pour validation.** Cette version part
de `7b69e3d`, dans la branche existante `experiment/m4c-anterieur-droit-local`
de la PR #19. Le dossier de référence
[`experience-anterieur-droit`](m4c/experience-anterieur-droit/) reste intégralement
identique. La nouvelle version est isolée dans
[`experience-anterieurs-bilateraux`](m4c/experience-anterieurs-bilateraux/).

## Rendus à examiner

| Vue | Lien direct |
| --- | --- |
| Face, deux antérieurs orange | [Face bilatérale](m4c/experience-anterieurs-bilateraux/renders/face-bilaterale.png) |
| Gros plan droit validé | [Épaule droite](m4c/experience-anterieurs-bilateraux/renders/epaule-droite-validee.png) |
| Gros plan gauche proposé | [Épaule gauche](m4c/experience-anterieurs-bilateraux/renders/epaule-gauche-nouvelle.png) |
| Comparaison à angles équivalents | [Côte à côte](m4c/experience-anterieurs-bilateraux/renders/comparaison-bilaterale.png) |
| Trois quarts avant droit | [Vue droite](m4c/experience-anterieurs-bilateraux/renders/trois-quarts-avant-droit.png) |
| Trois quarts avant gauche | [Vue gauche](m4c/experience-anterieurs-bilateraux/renders/trois-quarts-avant-gauche.png) |
| Avant/après gauche | [Comparatif gauche](m4c/experience-anterieurs-bilateraux/renders/comparatif-gauche.png) |
| Mannequin neutre | [Vue complète](m4c/experience-anterieurs-bilateraux/renders/neutre-complet.png) |
| Lecture des contours sans ombrage | [Silhouettes droite / gauche avant / gauche après](m4c/experience-anterieurs-bilateraux/renders/comparaison-contours.png) |
| Planche des vues générales | [Face et trois quarts](m4c/experience-anterieurs-bilateraux/renders/planche-bilaterale.png) |
| Conservation du rendu neutre | [Comparatif neutre](m4c/experience-anterieurs-bilateraux/renders/comparatif-neutre.png) |

Les gros plans utilisent les caméras symétriques ±45°, la même échelle et le
même cadrage. La vue droite est réfléchie uniquement dans les deux planches de
comparaison pour faciliter la lecture. Les textures UV ne sont jamais retournées.
Les rendus séparés gardent leur orientation anatomique. Le studio mat neutre est
identique ; son éclairage peut donner une luminosité différente aux deux côtés.
La comparaison en émission permet de juger les contours sans cet effet.

## Méthode

La source est **la frontière réelle du masque droit validé**, y compris son
arrêt au pectoral, et non l'ancienne annotation qui dépassait cette limite.
430 points du contour à couverture 50 % sont relevés par rayons sur les triangles
du mannequin. Leurs coordonnées 3D sont réfléchies autour de X = 0, puis projetées
sur les vrais triangles de l'épaule gauche. Une courbe régularisée est de nouveau
projetée par rayons sur cette surface ; ses 900 points, faces et UV sont conservés.

La distance entre le miroir théorique et la projection gauche vaut **0,84 mm
en moyenne, 3,72 mm au maximum**. Ce sont des distances de correspondance entre
surfaces asymétriques ; aucun sommet du mannequin n'est déplacé.

Seule la bande entre l'ancien bord gauche côté pectoral et le nouveau guide
est modifiée. Le masque `deltoid.left.anterior` (ID 3) gagne 4 161 texels et en
rend 187 au neutre. Sa couverture antialiasée change sur 4 654 texels. Le masque
droit ID 6 et les six autres masques sont recopiés octet pour octet. Les deux
frontières antérieur/moyen sont conservées, avec une marge de filtrage immuable
de quatre texels autour du moyen gauche.

Les valeurs sont calculées à partir des UV interpolées sur les triangles réels,
avec contrôle de visibilité et raccord des gouttières. Le nettoyage reste local :
14 texels de trous raster fermés comblés, 39 texels ajoutés de gouttière isolés et
sept pixels ajoutés isolés sur surface écartés. Aucun nouveau découpage global.

## Différences résiduelles et masques protégés

La symétrie recherchée est visuelle ; les surfaces et les frontières protégées
des deux côtés ne sont pas exactement symétriques.

- **Pectoral gauche :** 193 des 900 échantillons du guide adapté rencontrent des
  texels déjà identifiés comme pectoraux, sur la portion haute/médiale du bord
  côté pectoral (ordonnées 90,46 à 125,20 dans la vue de comparaison 305 × 221).
  Le masque pectoral et ses poids antialiasés restent intacts. Dans cette portion,
  l'écart mesuré entre le contour final et le guide adapté reste inférieur à
  0,33 pixel ; le guide n'est pas imposé au détriment du pectoral.
- **Départ claviculaire :** l'écart maximal au guide est de 2,74 pixels à
  l'ordonnée 70, tout au début du contour. Le raccord au sommet existant est
  conservé ; aucune nouvelle extension supérieure n'est forcée.
- **Convergence inférieure :** trois échantillons atteignent la marge immuable
  du moyen gauche, vers les ordonnées 175,72 à 175,95. La frontière avec ce
  faisceau reste inchangée ; l'écart maximal au guide dans la portion terminale
  est de 1,25 pixel.

Sur les lignes communes de cette vue reconstruite, l'écart moyen entre les bords
gauche et droit passe de **3,77 à 0,61 pixel**. L'écart moyen au guide déjà adapté
à la surface gauche est de 0,053 pixel. Ces mesures dépendent du cadrage et du
seuil raster ; elles ne démontrent pas une identité anatomique en tout point.
Les [mesures détaillées](m4c/experience-anterieurs-bilateraux/contour-comparison.json)
et les [points de transfert 3D](m4c/experience-anterieurs-bilateraux/surface-transfer.json)
permettent de vérifier ces différences.
Sur les rendus des masques sans ombrage à ±45°, le recouvrement miroir des
silhouettes (intersection/union, sans translation de recalage) passe de **87,5 %
à 95,7 %**. Les [résultats raster](m4c/experience-anterieurs-bilateraux/silhouette-comparison.json)
complètent la comparaison visuelle sans exiger une identité géométrique des épaules.

## Sources et contrôles

- [Blender autonome éditable](m4c/experience-anterieurs-bilateraux/experience-anterieurs-bilateraux.blend),
  atlas embarqués, huit contrôles `SHOW::` / `COLOR::`, deux antérieurs orange
  à l'ouverture et guides 3D cachés. Mettre les huit `SHOW` à zéro pour le neutre.
- [Masques PNG et atlas](m4c/experience-anterieurs-bilateraux/textures/),
  [GLB de contrôle](m4c/experience-anterieurs-bilateraux/exports/meshy-eight-zones-control.glb),
  correspondance des huit identifiants dans `regions.json` et `region-binding.json`.
- [Audit indépendant](m4c/experience-anterieurs-bilateraux/verification.json) :
  sept masques identiques, dont le droit validé ; atlas RGBA contenant le droit
  identique ; deux interfaces antérieur/moyen identiques ; aucun chevauchement
  des poids ; huit identifiants conservés.
- [Continuité](m4c/experience-anterieurs-bilateraux/continuity-audit.json) :
  une composante par zone après raccord des coutures UV, aucun trou fermé détecté.
- [Huit raycasts Three.js](m4c/experience-anterieurs-bilateraux/picking-audit.json)
  réussis sur le modèle source et l'export. Aucune intégration tactile nouvelle.
- [Préservation Blender](m4c/experience-anterieurs-bilateraux/blender-preservation.json) :
  positions, normales, indices et UV identiques. Rendus droit avant/après et
  neutre avant/après identiques octet pour octet après suppression des métadonnées
  d'horodatage PNG, sans changement des pixels.
- GLB : **110 588 triangles avant et après ; zéro triangle ajouté et déplacement
  des sommets nul**. Le mannequin maître Meshy `e45e5d8` conserve son SHA-256
  `421e593cad17f60d1c0c5e67707729fb88bbf69026795e22011ecc7d90b38959`.
- Les 630 fichiers déjà suivis dans `7b69e3d` restent identiques. Les changements
  sont uniquement des ajouts expérimentaux. La CI de la PR #19 contrôle aussi
  Expo SDK 58, le moteur embarqué, TypeScript, les tests de Logbook et l'export iOS.

Les outils nouveaux et les commandes de reproduction sont décrits dans le
[README des sources](m4c/experience-anterieurs-bilateraux/README.md).
Les PR #17 et #18, leurs branches et leurs ressources restent inchangées.
Aucun changement d'application, de visualiseur ou de SQLite ; aucune fusion.
Budget additionnel : 0 €. **Arrêt pour validation visuelle du côté gauche.**
