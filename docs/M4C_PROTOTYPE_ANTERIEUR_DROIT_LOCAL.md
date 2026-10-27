# M4C — prototype isolé du bord antérieur droit

**Proposition expérimentale, non validée, sans intégration.** Branche
`experiment/m4c-anterieur-droit-local`, créée exclusivement depuis `168ac61`
(masques restaurés de `06fa665`). Les branches des PR #17 et #18 ne sont pas
modifiées. Aucun fichier provenant de la segmentation rejetée `6817b08` n'est
réutilisé.

## Examiner la proposition

- [Avant/après au cadrage de référence](m4c/experience-anterieur-droit/renders/comparatif-reference.png).
- [Comparatif serré sans annotation](m4c/experience-anterieur-droit/renders/comparatif-serre.png).
- [Gros plan du contour, vue non inversée](m4c/experience-anterieur-droit/renders/gros-plan-contour.png).
- [Face](m4c/experience-anterieur-droit/renders/face.png),
  [profil droit](m4c/experience-anterieur-droit/renders/profil-droit.png),
  [trois quarts avant droit](m4c/experience-anterieur-droit/renders/trois-quarts-avant-droit.png).
- [Planche des trois angles](m4c/experience-anterieur-droit/renders/planche-controles.png).
- [Comparatif neutre](m4c/experience-anterieur-droit/renders/comparatif-neutre.png)
  et [mannequin complet neutre](m4c/experience-anterieur-droit/renders/neutre-complet.png).

## Modification réellement effectuée

Seul le bord **côté pectoral** du masque `deltoid.right.anterior` (code 6) est
étendu sur de la surface précédemment neutre. Le code 6 gagne **5 792 texels**
dans l'atlas 2 048 × 2 048 ; aucun texel précédemment identifié comme un autre
muscle n'est réaffecté. Son masque de couverture antialiasée change sur
6 007 texels, gouttières UV comprises.

La frontière antérieur/moyen reste identique, y compris une marge de filtrage
de quatre texels autour du masque moyen droit. La pointe se raccorde au
territoire existant ; aucune retouche du relief, du volume ou du maillage.

## Méthode et limites du recalage

1. Relever des points peu nombreux sur le tracé manuel et reconstruire une
   courbe cubique régulière. La terminaison est raccordée progressivement à la
   pointe existante, plutôt que recopier les irrégularités du dessin.
2. Selon la dernière précision de l'utilisateur, **la capture montre l'épaule
   gauche et son tracé doit être transposé au droit**. Recaler une caméra
   perspective du côté droit sur la silhouette correspondante, en réfléchissant
   le repère écran de la référence gauche. La projection est ensuite calculée
   sur la vraie surface droite. Aucune inversion de texture ou du mannequin ;
   le masque gauche n'est ni utilisé comme nouvelle base ni modifié.
3. Projeter 800 points du guide par rayons sur les vrais triangles du modèle,
   conserver les positions 3D, les indices de faces et les UV interpolées.
4. Modifier uniquement la bande comprise entre l'ancien bord et le guide,
   avec contrôle de visibilité et interpolation des valeurs dans les gouttières
   UV. Préserver les sept masques protégés et leurs poids antialiasés. Corriger
   les petits artefacts de rastérisation créés dans cette bande : 297 texels de
   trous fermés comblés et deux texels ajoutés isolés écartés.

**Le cadrage est reconstruit, pas garanti identique aux métadonnées iPhone.**
La capture fait seulement 305 × 221 pixels et ne fournit ni caméra ni focale.
L'écart RMS du recalage du contour actuel est d'environ 0,91 pixel sur ce relevé
manuel. L'éclairage reste celui du studio Blender mat neutre ; il est strictement
identique entre avant et après. Les deux comparatifs du côté droit sont présentés
avec une réflexion horizontale pour reprendre l'orientation de la capture gauche.
Il s'agit donc de la vue droite correspondante, pas d'un avant/après de l'épaule
gauche. Les vues face/profil/trois
quarts utilisent les côtés anatomiques réels, sans inversion.

**Le guide ne peut pas être suivi intégralement en préservant le pectoral.**
Une partie de sa portion supérieure/médiane se projette dans le masque existant
du pectoral droit, approximativement entre les ordonnées 83 et 126 de la petite
capture. Ce territoire est protégé. L'extension s'arrête donc à la surface grise
disponible, au lieu de déborder dans le pectoral. Cela limite la fidélité au tracé
à cet endroit et peut influencer sa courbure. Ce compromis est explicitement
soumis à validation, sans prétendre constituer une validation anatomique médicale.

## Sources éditables et export de contrôle

Tous les ajouts sont dans
[`docs/m4c/experience-anterieur-droit/`](m4c/experience-anterieur-droit/) :

- [Blender autonome avec atlas embarqués](m4c/experience-anterieur-droit/experience-anterieur-droit.blend).
  Le matériau expose les huit contrôles `SHOW::` et `COLOR::`. La scène s'ouvre
  avec uniquement le code 6 orange ; mettre les huit `SHOW` à zéro rétablit le
  matériau neutre commun. Le guide 3D est caché dans une collection dédiée,
  absent des rendus et de l'export du mannequin.
- [Masque antérieur droit L8](m4c/experience-anterieur-droit/textures/deltoid.right.anterior.png),
  sept masques protégés recopiés à l'identique, atlas d'IDs L8 et atlas RGBA.
- [GLB de contrôle](m4c/experience-anterieur-droit/exports/meshy-eight-zones-control.glb)
  avec la palette de contrôle des huit zones, UV et atlas d'IDs embarqué.
  Il ne remplace aucune ressource du visualiseur.
- [Guide/caméra éditables](m4c/experience-anterieur-droit/guide-camera.json),
  [projection 3D](m4c/experience-anterieur-droit/projected-curve.json),
  `surface-edit.npz`, `regions.json`, `region-binding.json`.

Les bornes de la région 6 sont étendues dans les données de correspondance,
sans changement des huit identifiants. Les autres données de référence restent
accessibles dans leurs dossiers existants, inchangés.

Outils ajoutés dans `tools/m4c/` : `experimental_anterior.py`,
`project_experimental_anterior.py`, `render_experimental_anterior.py`,
`compose_experimental_anterior.py`, `audit_experimental_anterior.py`.
Ils lisent la base validée et écrivent uniquement dans le nouveau dossier.
Le cache technique est extérieur au dépôt de travail.

## Vérifications

- [Audit indépendant](m4c/experience-anterieur-droit/verification.json) :
  sept PNG de masques identiques octet pour octet à `168ac61`, mêmes huit IDs,
  aucun chevauchement des poids, frontière antérieur/moyen inchangée.
- [Continuité des huit zones](m4c/experience-anterieur-droit/continuity-audit.json) :
  une composante par muscle après raccord des coutures UV ; aucun trou gris
  fermé détecté. Il s'agit d'un contrôle raster et d'échantillons de coutures,
  pas d'une preuve anatomique.
- [Huit raycasts Three.js réels](m4c/experience-anterieur-droit/picking-audit.json)
  sur le modèle source et le GLB de contrôle : mêmes IDs, correspondance UV
  exploitable, aucun changement du système tactile de la PR #18.
- [Préservation Blender](m4c/experience-anterieur-droit/blender-preservation.json) :
  positions, indices, normales et UV identiques. Les PNG avant/après en matériau
  neutre sont eux aussi identiques octet pour octet.
- Le GLB de contrôle conserve exactement les tampons géométriques et UV du GLB
  de référence : **110 588 triangles avant et après, zéro triangle ajouté,
  déplacement maximal des sommets : 0**. Aucun coût géométrique mobile nouveau.
- Tous les fichiers déjà suivis au commit `168ac61` restent identiques, y
  compris application, configuration SDK 58, SQLite et mannequin maître
  `e45e5d8` (SHA-256 `421e593cad17f60d1c0c5e67707729fb88bbf69026795e22011ecc7d90b38959`).

Le prototype n'est pas intégré à l'iPhone et ne modifie ni les ressources ni
les fonctionnalités de la PR #18. Les captures produites sont de vrais rendus
Blender, pas de nouvelles captures d'un test iPhone. Budget additionnel : 0 €.

**Arrêt après cette proposition.** Le résultat et les limites de projection
restent à examiner visuellement. En cas de rejet, abandonner cette branche
expérimentale suffit ; rien n'est à restaurer dans les PR #17 ou #18.
