# M4A — POC matériaux / normal maps

18 octobre 2026. PR #11 en brouillon. Source : **B+ Premium Puissance**, conservée à l'identique ; le maillage de l'essai géométrique insuffisant n'est pas réutilisé.

**Verdict : approche insuffisante pour ce POC et le critère de lecture mobile.** Les normales révèlent une orientation de fibres, mais le résultat évoque encore des stries régulières sur un mannequin. Les formes de plaques dominent et la lecture anatomique n'est pas convaincante à 390 pixels. **Un seul matériau testé ; aucun nouvel essai automatique après ce constat.**

[Avant / après de face](m4a/material-poc/comparaison-front.png) · [Trois quarts](m4a/material-poc/comparaison-three-quarter.png) · [Gros plan](m4a/material-poc/renders/detail.png) · [Pectoral gauche orange](m4a/material-poc/renders/selection.png)

![Comparaison à 390 pixels par mannequin](m4a/material-poc/comparaison-three-quarter.png)

## Méthode gratuite, sans sculpture

Les deux pectoraux et deltoïdes reçoivent des **cartes originales créées avec NumPy et Pillow**, appliquées dans Blender. Les abdominaux et le reste du corps conservent le traitement B+ Puissance. Aucun sommet, triangle ou normale géométrique n'est modifié ; aucune subdivision, sculpture ou displacement n'est utilisé.

Deux coordonnées UV locales suivent l'éventail pectoral et l'enveloppe du deltoïde. Les faisceaux procéduraux varient en largeur et convergent vers les insertions ; des détails plus fins suivent leur direction. Un champ de hauteur virtuel produit **deux normal maps tangentielles RGB8, convention OpenGL +Y**. Le champ ne déplace jamais le maillage.

Deux cartes RGBA supplémentaires portent couverture, roughness, modulation de teinte et information de fibres. Le matériau mélange localement ces normales et variations avec le satin bleu argenté existant. Les changements de reflet sont bien calculés en 3D ; aucune anatomie n'est repeinte sur les rendus.

## Résultat et limites

Le gros plan montre des fibres orientées et des reflets différents, sans morceaux ajoutés, trous ou nouvelle géométrie cassée. Toutefois, les stries restent trop régulières, proches d'un effet peigné. Elles ne remplacent pas la construction des masses, de leurs bords et des attaches ; les deltoïdes ne se lisent pas comme trois portions anatomiques convaincantes.

À **390 pixels par mannequin**, les détails fins perdent de leur force et la séparation reste largement celle du B+ initial. La normal map ne change ni silhouette, ni profondeur réelle, ni ombres portées. Le POC démontre un effet de matière, **pas le niveau d'écorché fitness demandé**. Ce constat concerne ce contenu procédural ; il ne prouve pas l'impossibilité générale d'obtenir ce style avec des textures artistiquement maîtrisées.

## Coût et exploitation future

| Élément | Résultat |
|---|---|
| Budget additionnel | **0 €**, aucun achat, outil payant ou service commercial ajouté |
| Géométrie | **112 176 triangles, trois objets, +0 triangle** |
| Textures originales | **Quatre PNG 1 024 × 1 024** : deux normales et deux surfaces |
| Données ajoutées | Deux jeux UV et quatre masques locaux ; UV d'origine conservé |
| Sélection de démonstration | IDs 1 / 2 : pectoraux gauche / droit ; 3 / 4 : deltoïdes gauche / droit |
| Rendu orange | ID 1 uniquement : pectoral gauche anatomique |

Sous l'hypothèse de quatre textures GPU RGBA8 : **16 Mio sans mipmaps, environ 21,3 Mio avec mipmaps**, estimation non mesurée. Les UV supplémentaires, raccords et coût du shader doivent aussi être évalués. Le matériau Blender multicouche demanderait une consolidation vers un atlas PBR ou un port du mélange ; **aucun export mobile ou FPS iPhone n'est validé**. Les masques restent provisoires, sans segmentation complète ou interaction applicative.

## Vérifications et arrêt

Quatre vrais rendus Blender 4.3.2 / Cycles CPU, 96 échantillons. Les deux images de référence B+ Puissance sont réutilisées à l'identique, avec mêmes cadrages, lumières et paramètres du matériau de base. Deux planches les redimensionnent à 390 pixels par mannequin ; détail et sélection sont de vrais gros plans Blender.

[Prototype et reproduction](m4a/material-poc/README.md) · [Construction](m4a/material-poc/experiment/construction.json) · [Géométrie / UV / textures](m4a/material-poc/audit.json) · [Validation](m4a/material-poc/validation.json) · [Manifest](m4a/material-poc/manifest.json)

La géométrie, ses normales et l'UV original sont comparés à la source ; les quatre textures sont vérifiées dans le BLEND autonome. Les contacts tête / pieds connus restent ceux du [B+ Puissance inchangé](m4a/bplus-power/power/geometry-check.json). [Provenance CC0 du modèle](m4a/bplus-fitness/PROVENANCE.md) ; textures originales, aucun asset anatomique tiers ou image de référence incorporée.

**Arrêt après publication de ce constat.** Historique préservé, aucune V2 automatique, intégration, modification SQLite, M4B, fusion ou utilisation d'Astra Ultra.
