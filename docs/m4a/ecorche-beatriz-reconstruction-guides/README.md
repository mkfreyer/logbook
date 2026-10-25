# Reconstruction locale des creux — copie d’essai non validée

**Ne pas utiliser comme base finale.** Sept intersections de triangles subsistent
sur chaque deltoïde, avec des marques aux raccords. La référence visuelle reste
`0ab3d83`, et les guides validés restent ceux de `0fc6f0b`.

## Fichiers

- [`reconstruction-guides.blend`](reconstruction-guides.blend) : référence P4 +
  tête P5 et copie de reconstruction. Scènes `16_COMBINAISON_P4_P5` et
  `19_RECONSTRUCTION_GUIDES`. Les 298 objets hors deltoïdes sont préservés.
- [`reconstruction-guides.glb`](reconstruction-guides.glb) : **export technique
  d’essai non validé**, avec les 300 identifiants de pièces ; aucun guide ni
  découpage interactif des trois faisceaux. Ne pas intégrer dans l’application.
- [`surface.npz`](surface.npz) : positions de référence et proposées, triangles,
  correspondances avec P4, bordures et domaine local.
- [`surface.json`](surface.json), [`reconstruction.json`](reconstruction.json) :
  méthode, statistiques et provenance.
- `serialized-deltoid.right.npz` / `serialized-deltoid.left.npz` : coordonnées
  relues depuis les maillages Blender construits, pour la vérification indépendante.
- [`verification.json`](verification.json) : préservation et défauts réellement
  détectés. Un contrôle de fermeture réussi ne signifie pas absence d’intersection.
- [`export.json`](export.json) : taille et contenu de l’export GLB.
- [`renders/`](renders) : douze images Blender avant/après et planches comparatives.
- [Rapport de résultat](../../M4A_RECONSTRUCTION_CREUX_GUIDES_BLEUS.md).

Les anciennes versions restent dans leurs dossiers et dans l’historique Git.
Le master original de `0ab3d83` n’est pas réenregistré.

## Reproduction de l’essai

Outils de préparation uniquement : Blender 4.3.2 CPU, Python avec NumPy, SciPy,
Pillow, Matplotlib, **mapbox-earcut 2.1.0 (ISC)** et **Shapely 2.2.0 (BSD)**.
Aucun outil payant et aucune dépendance ajoutée à l’application.

```bash
python -m pip install mapbox-earcut==2.1.0 shapely==2.2.0

python tools/m4a-ecorche/reconstruction_guides_patch.py \
  --source docs/m4a/ecorche-beatriz-creux-localises/source.npz \
  --guides docs/m4a/ecorche-beatriz-guides-deltoides/guides.json \
  --output docs/m4a/ecorche-beatriz-reconstruction-guides

blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 \
  --python tools/m4a-ecorche/reconstruction_guides_build.py -- \
  --baseline docs/m4a/ecorche-beatriz-combinaison-p4-p5/ecorche-p4-p5.blend \
  --asset docs/m4a/ecorche-beatriz-reconstruction-guides

blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 \
  --python tools/m4a-ecorche/reconstruction_guides_render.py -- \
  --asset docs/m4a/ecorche-beatriz-reconstruction-guides

blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 \
  --python tools/m4a-ecorche/reconstruction_guides_export.py -- \
  --asset docs/m4a/ecorche-beatriz-reconstruction-guides

blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 \
  --python tools/m4a-ecorche/reconstruction_guides_verify.py -- \
  --asset docs/m4a/ecorche-beatriz-reconstruction-guides

python tools/m4a-ecorche/reconstruction_guides_compose.py \
  --asset docs/m4a/ecorche-beatriz-reconstruction-guides
```

Le script `reconstruction_guides_surface.py` fournit le repère de surface et le
calcul de fond lisse utilisés par `reconstruction_guides_patch.py`. **Ne pas
lancer son ancien chemin de déplacement de sommets comme variante finale** :
la livraison utilise la reconstruction de patches. L’option `--deps` de ce
dernier accepte un répertoire d’installation séparé des outils de préparation.

## Attribution

Corps : **[Ecorche - Anatomy study](https://sketchfab.com/3d-models/ecorche-anatomy-study-e402d3d541eb4b199c57d5410f5d3c57)**,
par **[Beatriz Gomez Santamaria](https://sketchfab.com/BeatrizGomez)**,
licence **[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)**.
Adaptation Logbook antérieure : reconstruction symétrique, volumes athlétiques,
gorge reconstruite et finitions P4. Cette copie ajoute une reconstruction locale
expérimentale des creux des deltoïdes et une modification de leur topologie.

Tête P5 et yeux : **Human Base Meshes v1.4.1 — Blender Studio / Dan Ulrich**,
CC0 ; [provenance et licence archivées](../ecorche-beatriz-passe5/HEAD_SOURCE_LICENSE.md).
Tête et gorge inchangées dans cet essai. Aucun nouvel asset n’est acheté ou ajouté.
