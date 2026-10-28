# Postérieur gauche adapté à la référence droite

[Rapport et rendus](../../M4C_HARMONISATION_POSTERIEURS.md).

- [Blender éditable](meshy-posterieurs-harmonises.blend), textures embarquées,
  matériau `M4C_HUIT_ZONES__PALETTE_EDITABLE`, huit valeurs `SHOW::<id>` et
  huit couleurs `COLOR::<id>`.
- [Masque gauche ID 5](textures/deltoid.left.posterior.png), couverture L8
  antialiasée ; [atlas discret](textures/muscle-ids.png), seuil 128/255.
- [Pack RGBA](textures/masks-rgba-1.png) : seul le canal rouge, ID 5, change.
- [GLB de contrôle](exports/meshy-eight-zones-control.glb), sans branchement
  à l’application.
- [Contour droit de référence](right-reference-outline.json),
  [adaptation 3D sur la gauche](surface-adaptation.json),
  [guide gauche](left-contour-guides.json) et
  [raycasts sur la surface gauche](projected-outline.json).

Base : [`977f68a`](../meshy-posterieur-droit-bord-inferieur/README.md).
Le maître [`meshy-e45e5d8.glb`](../../../assets/models/meshy-e45e5d8.glb) et
les sept autres masques ne sont pas modifiés. Les fichiers de cette proposition
sont livrés dans un nouveau dossier ; les anciens essais restent intacts.

Reproduction depuis la racine avec les dépendances gratuites des
[outils M4C](../../../tools/m4c/README.md) :

```sh
python tools/m4c/harmonize_left_posterior.py reference
blender -b -t 2 --python-exit-code 1 --python tools/m4c/adapt_left_surface.py
python tools/m4c/harmonize_left_posterior.py prepare
blender -b -t 2 --python-exit-code 1 --python tools/m4c/project_mask_outline.py -- --asset-dir docs/m4c/meshy-posterieurs-harmonises --base-blend docs/m4c/meshy-posterieur-droit-bord-inferieur/meshy-posterieur-droit-bord-inferieur.blend --guide left-contour-guides.json
python tools/m4c/harmonize_left_posterior.py finish
python tools/m4c/audit_left_harmonization.py
python tools/m4c/audit_continuity.py --asset-dir docs/m4c/meshy-posterieurs-harmonises
node tools/m4c/audit-picking.mjs docs/m4c/meshy-posterieurs-harmonises
blender -b -t 4 --python-exit-code 1 --python tools/m4c/render_left_harmonization.py
python tools/m4c/compose_left_harmonization.py
```

Le guide est construit en coordonnées 3D et adapté aux triangles gauches.
Les NPZ conservent le domaine local, les points de surface, la visibilité et
la bande de raccord protégée. Toute édition doit synchroniser le masque,
l’atlas discret et les packs dérivés.

Les rendus de silhouettes sont obtenus avec un matériau émissif temporaire,
sans éclairage ; ce matériau n’est pas le style du mannequin livré. Le miroir
et les couleurs de superposition concernent uniquement la présentation des
diagnostics. Les PNG bruts restent accessibles dans `renders`.

**PR #17 en brouillon, proposition à valider. Aucune fusion ni intégration.**
Model created with Meshy — [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
