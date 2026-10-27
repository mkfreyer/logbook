# M4C — ajustement local de la bordure inférieure droite

**Proposition pour validation**, depuis `ad08cef`, PR #17 en brouillon.
La nouvelle annotation remplace la précédente. Elle sert à retirer le surplus
vert **sous** la ligne, sans réduire tout le deltoïde ni reprendre sa sculpture.

## Rendus

- [Avant / après à l’angle de la nouvelle capture](m4c/meshy-posterieur-droit-bord-inferieur/renders/comparatif-angle-annotation.png)
- [Gros plan sans annotation du contour corrigé](m4c/meshy-posterieur-droit-bord-inferieur/renders/apres-angle-annotation.png)
- [Trois quarts arrière droit](m4c/meshy-posterieur-droit-bord-inferieur/renders/apres-trois-quarts-arriere-droit.png)
- [Deux épaules directement de dos](m4c/meshy-posterieur-droit-bord-inferieur/renders/apres-epaules-dos.png) ·
  [Dos complet](m4c/meshy-posterieur-droit-bord-inferieur/renders/apres-dos-complet.png)
- [Arrière gauche](m4c/meshy-posterieur-droit-bord-inferieur/renders/apres-trois-quarts-arriere-gauche.png)
- [Comparatifs arrière](m4c/meshy-posterieur-droit-bord-inferieur/renders/comparatif-vues-arriere.png) ·
  [Profil droit](m4c/meshy-posterieur-droit-bord-inferieur/renders/apres-profil-droit.png) ·
  [Avant droit](m4c/meshy-posterieur-droit-bord-inferieur/renders/apres-avant-droit.png)

Les comparatifs conservent les matrices de caméra, le cadrage, le matériau mat
et les lumières. La capture correspond à la caméra arrière droite à −135° ;
le gros plan est rendu directement en haute résolution dans sa fenêtre de
cadrage, sans peinture ni retouche des pixels du mannequin.

## Correction appliquée

Une courbe cubique lissée interprète les repères orange en évitant les petites
irrégularités du dessin manuel. Elle est projetée sur la surface réelle du
Meshy. Les texels sont reliés à leurs points 3D et contrôlés par raycast ; le
retrait reste local et se raccorde à la pointe basse commune. La tolérance de
profondeur de 2 mm, déjà utilisée dans cette base, concerne les fines couches
superposées préexistantes du modèle. Aucune surface n’est créée ou déplacée.

La correction finale retire **3 410 texels d’ID 8 vers le neutre**. Aucun vert
n’est ajouté ; **30 945 texels** d’ID 8 restent présents. Ce sont des mesures
d’atlas UV avec marges, pas des mesures de volume musculaire.

L’arrondi supérieur est conservé : les **14 160 texels de couverture protégés**
au-dessus du début du tracé gardent exactement leurs poids et leurs IDs.
Les sept autres masques, dont le postérieur gauche, sont identiques octet pour
octet. Les texels bleus et rouges ne sont pas déplacés.

Un petit accroc détecté au gros plan provenait de valeurs constantes dans une
marge de couture UV. Le champ du masque y est maintenant prolongé selon le
triangle voisin, sans changer les coordonnées UV. Douze texels isolés de
marge vide ont été retirés ; aucun texel de surface couverte n’est concerné par
ce nettoyage. Le bord utilise une couverture antialiasée, tandis que l’atlas
de sélection garde des IDs entiers au seuil 128/255.

## Contrôles et sources

- Une seule composante par zone après recollage des coutures UV ; aucun trou
  interne détecté sur les texels contrôlés. Trois impacts 3D sous la nouvelle
  courbe passent du vert au gris ; les témoins supérieurs, verts, bleu et gris
  sont préservés. Les huit raycasts Three.js source/export passent.
- Positions, normales, UV et indices sont identiques à `ad08cef` dans les
  exports. Toujours **110 588 triangles**, 55 288 sommets Blender, 60 622
  sommets exportés avec les doublons UV existants. Aucun coût géométrique ajouté.
- Neuf vrais rendus Blender. Le rendu neutre de face et la vue arrière gauche
  sont identiques pixel par pixel à la référence. Les masques restent en
  2 048 × 2 048.
- Les 134 fichiers applicatifs protégés restent inchangés : GLB validé
  `e45e5d8`, visualiseur Expo SDK 58, fonctionnalités et SQLite. Aucune nouvelle
  mesure sur iPhone n’est revendiquée.

[Blender éditable](m4c/meshy-posterieur-droit-bord-inferieur/meshy-posterieur-droit-bord-inferieur.blend) ·
[Masque ID 8](m4c/meshy-posterieur-droit-bord-inferieur/textures/deltoid.right.posterior.png) ·
[GLB de contrôle](m4c/meshy-posterieur-droit-bord-inferieur/exports/meshy-eight-zones-control.glb) ·
[Toutes les sources et reproduction](m4c/meshy-posterieur-droit-bord-inferieur/README.md).

[Audit des données](m4c/meshy-posterieur-droit-bord-inferieur/verification.json) ·
[Continuité](m4c/meshy-posterieur-droit-bord-inferieur/continuity-audit.json) ·
[Caméras et contrôle neutre](m4c/meshy-posterieur-droit-bord-inferieur/render-verification.json).

Cette livraison reste une proposition de segmentation fitness à examiner sur
les vues fournies, pas une validation anatomique médicale. Les versions
précédentes sont conservées. **Arrêt pour validation visuelle**, sans fusion,
nouvelle segmentation globale ou intégration dans l’application.

Model created with Meshy — [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
