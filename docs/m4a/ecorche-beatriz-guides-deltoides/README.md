# Guides 3D des creux — étape 1, sans sculpture

Base inchangée : **P4 + tête P5, `0ab3d83`**. Fichier autonome de contrôle,
sans dépendance à un logiciel ou asset payant. Aucun export applicatif nouveau.

## Fichiers

- [`guides-deltoides-p4.blend`](guides-deltoides-p4.blend) : les 300 maillages
  approuvés, les caméras, le matériau et les lumières conservés, plus les guides
  CURVE. Scène active `18_GUIDES_SANS_SCULPTURE`. Deux collections
  `GUIDES_RETRAIT_FACILE_RIGHT` et `GUIDES_RETRAIT_FACILE_LEFT` permettent de tout
  masquer ou supprimer sans modifier le mannequin. Les anciens masters et toutes
  leurs scènes restent archivés dans leurs dossiers d’origine.
- [`guides.json`](guides.json) : points manuels de l’image 320 × 384, projections
  3D sur le deltoïde, normales, identités des surfaces visibles/masquantes,
  recalage de caméra et paramètres d’affichage. Les portions bleues sous le bras
  restent sur le deltoïde ; les pointillés orange sont des repères séparés de
  visibilité sur la surface masquante, pas des guides de sculpture.
- [`maillage-audit.json`](maillage-audit.json) : mesures du maillage P4, sans
  densification ni déformation.
- [`verification.json`](verification.json) : comparaison indépendante de tous
  les maillages sérialisés avec le master de `0ab3d83`.
- [`renders/`](renders) : sept rendus Blender bruts, quatre planches composées
  exclusivement à partir de leurs pixels, métadonnées et empreintes.
- [Rapport de validation et méthode future](../../M4A_GUIDES_3D_DELTOIDES_P4.md).

Les tubes colorés ont seulement un décalage d’affichage de 0,4 mm au-dessus des
points de surface, rayon 0,22 mm. Ne pas les confondre avec un relief sculpté.
Dans la superposition, le premier haut commun est affiché en rouge ; dans la vue
des nouveaux trajets, il est bleu. Le cadre est recalé manuellement sur l’image
utilisateur, sans prétention de registration automatique exacte.

## Reproduction

Depuis la racine du dépôt, avec Blender 4.3.2 CPU et Python avec Pillow :

```bash
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 \
  --python tools/m4a-ecorche/guides_deltoides.py -- \
  --baseline docs/m4a/ecorche-beatriz-combinaison-p4-p5/ecorche-p4-p5.blend \
  --camera docs/m4a/ecorche-beatriz-creux-localises/camera.json \
  --output docs/m4a/ecorche-beatriz-guides-deltoides --render

blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 \
  --python tools/m4a-ecorche/guides_deltoides_verify.py -- \
  --baseline docs/m4a/ecorche-beatriz-combinaison-p4-p5/ecorche-p4-p5.blend \
  --asset docs/m4a/ecorche-beatriz-guides-deltoides

python tools/m4a-ecorche/guides_deltoides_compose.py \
  --asset docs/m4a/ecorche-beatriz-guides-deltoides
```

L’option facultative `--reuse-unchanged-controls` réutilise les deux contrôles
sans guide/rouges déjà calculés, avec vérification des empreintes et de la caméra.
Elle n’est pas nécessaire à la reproduction complète.

## Attribution

Corps : **[Ecorche - Anatomy study](https://sketchfab.com/3d-models/ecorche-anatomy-study-e402d3d541eb4b199c57d5410f5d3c57)**,
par **[Beatriz Gomez Santamaria](https://sketchfab.com/BeatrizGomez)**,
licence **[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)**.
Le corps est une adaptation Logbook antérieure : reconstruction symétrique,
retouches des volumes et finitions P4. Cette étape ajoute uniquement des courbes
de contrôle, sans modification supplémentaire de sa géométrie.

Tête P5 : **Human Base Meshes v1.4.1 — Blender Studio / Dan Ulrich**, CC0 ;
voir la [provenance et licence archivées](../ecorche-beatriz-passe5/HEAD_SOURCE_LICENSE.md).
Tête, yeux et gorge inchangés ici. Les transformations historiques restent
documentées dans les dossiers précédents.

Arrêt pour validation des trajectoires. Aucune sculpture, segmentation,
intégration applicative ou fusion dans cette livraison.
