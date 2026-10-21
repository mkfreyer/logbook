# Assemblage exact — deltoïdes P4, tête P5, corps conservé

[Rapport et planches de validation](../../M4A_ECORCHE_COMBINAISON_P4_P5.md).

Le master `ecorche-p4-p5.blend` conserve les scènes historiques et ajoute
`16_COMBINAISON_P4_P5`. Les deux objets deltoïdes sont des copies exactes
de P4. Les 298 autres objets sont des copies exactes de P5, dont la tête humaine,
les yeux et l’ensemble de la gorge. Aucun raccord supplémentaire n’est nécessaire.

Les shape keys et groupes d’auteur présents dans P4 sont conservés à l’identique.
Aucun masque, aucune nouvelle séparation, aucune sculpture ni segmentation
ne sont créés. Les trois faisceaux ne sont pas exportés comme zones interactives.

## Reproduction

Blender 4.3.2 avec NumPy ; Python avec Pillow pour les seules planches.
Depuis la racine du dépôt, utiliser une nouvelle sortie pour préserver la livraison :

```bash
ASSET=docs/m4a/ecorche-beatriz-combinaison-p4-p5-reproduction
WORK=/workspace/work/ecorche-combinaison-reproduction
mkdir -p "$WORK"
export XDG_CONFIG_HOME="$WORK/blender-config"
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/combinaison_p4_p5_build.py -- --archive docs/m4a/ecorche-beatriz-passe6/ecorche-passe6.blend --output "$ASSET"
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/combinaison_p4_p5_render.py -- --asset "$ASSET"
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/combinaison_p4_p5_export.py -- --asset "$ASSET"
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/combinaison_p4_p5_verify.py -- --asset "$ASSET"
python tools/m4a-ecorche/combinaison_p4_p5_compose.py --asset "$ASSET"
```

Le script de contrôle compare le résultat aux fichiers d’origine P4 et P5,
et à P6 pour les pièces protégées. Les empreintes des sources, du master,
du GLB et des captures sont livrées dans les JSON voisins.

## Attribution

Corps : **Ecorche - Anatomy study — Beatriz Gomez Santamaria**,
[source](https://sketchfab.com/3d-models/ecorche-anatomy-study-e402d3d541eb4b199c57d5410f5d3c57),
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), selon les métadonnées
du GLB fourni. Adaptations Logbook : reconstruction symétrique et athlétique,
finitions antérieures, assemblage des deltoïdes P4 et de la tête P5.

Tête et yeux conservés : **Dan Ulrich / Blender Studio Human Base Meshes — CC0**,
[provenance conservée dans P5](../ecorche-beatriz-passe5/HEAD_SOURCE_LICENSE.md).
Conserver les attributions, licences et mentions des modifications à la redistribution.
