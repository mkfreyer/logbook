# M4A — reconstructions exploratoires BodyParts3D

[Rapport et verdict](../../M4A_BP3D_RECONSTRUCTION.md) ·
[Groupes et sources exactes](groups.json) · [Attribution](ATTRIBUTION.md)

Deux constructions sont conservées comme preuve technique, **aucune n’est
recommandée comme base finale**. L’union automatique conserve des raccords
visuellement artificiels, surtout sur l’abdomen et le bassin.

- `soft/` : soutien plus proche de la peau, muscles moins dégagés.
- `defined/` : soutien plus en retrait, volumes musculaires plus présents.
- `comparisons/` : deux colonnes fixes ; aucun muscle déplacé ou retouché en 2D.

Chaque variante contient `model.blend`, `construction.json`, `geometry-check.json`,
quatre rendus Cycles CPU, leurs paramètres/empreintes et une scène de revue
`renders/scene-review.blend`. Dans cette scène, le nœud **M4A selection enabled**
active le masque orange du pectoral gauche ; aucune interaction applicative.
Les IDs de faces `m4a_fitness_zone` vont de 1 à 30, avec 0 pour le support non assigné.
Ils constituent une classification provisoire, pas une segmentation finale.

Reproduction depuis la racine du dépôt, avec Blender 4.3.2, NumPy et Pillow :

```bash
python tools/m4a/acquire_sources.py --output-dir work/bodyparts3d --verify-only
blender --background --factory-startup --threads 3 --python tools/m4a/build_bp3d_fitness.py -- --archive work/bodyparts3d/isa_BP3D_4.0_obj_99.zip --groups docs/m4a/bp3d-fitness/groups.json --head docs/m4a/bplus-power/power/model.blend --variant soft --output work/bp3d-soft
blender --background --factory-startup --threads 3 --python tools/m4a/check_bp3d_fitness.py -- --prepared work/bp3d-soft
blender --background --factory-startup --threads 3 --python tools/m4a/render_bp3d_fitness.py -- --prepared work/bp3d-soft --output work/bp3d-soft/renders --samples 96 --resolution 720 1152 --views front,three-quarter,back,selection
python tools/m4a/compose_bp3d_fitness.py --root docs/m4a/bp3d-fitness
python tools/m4a/validate_bp3d_fitness.py
```

La première commande suppose l’archive et les tables déjà acquises dans le dossier
indiqué. Sans `--verify-only`, l’acquéreur existant peut récupérer les sources
officielles. Refaire les trois commandes Blender avec `defined` pour la seconde
construction. Le compositeur attend les rendus publiés sous `soft/renders` et
`defined/renders` ; adapter `--root` pour une reproduction dans `work/`.
Les SHA-256 des `.blend` peuvent varier entre sessions Blender ; les paramètres,
comptages, sources et images doivent être contrôlés séparément.

Aucun GLB de production, aucun rig, aucun code applicatif ou accès SQLite.
Aucune mesure de fluidité iPhone n’a été réalisée. Budget d’acquisition : 0 €.
