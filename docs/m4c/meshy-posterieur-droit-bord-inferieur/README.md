# Bordure inférieure du postérieur droit — sources

[Rapport et rendus](../../M4C_POSTERIEUR_DROIT_BORD_INFERIEUR.md).

- [Blender éditable](meshy-posterieur-droit-bord-inferieur.blend), textures
  embarquées et matériau `M4C_HUIT_ZONES__PALETTE_EDITABLE`.
- [Masque ID 8](textures/deltoid.right.posterior.png), couverture L8 antialiasée.
- [Atlas discret](textures/muscle-ids.png), ID 8 pour couverture ≥ 128/255.
- [Pack RGBA](textures/masks-rgba-1.png) : seul le canal alpha de l’ID 8 change.
- [GLB de contrôle](exports/meshy-eight-zones-control.glb), buffers géométriques
  copiés à l’identique ; seules les images dérivées et métadonnées changent.
- [Repères de la nouvelle courbe](lower-contour-guides.json) et
  [points projetés en 3D](projected-outline.json).

Base : [`ad08cef`, contour arrondi précédent](../meshy-posterieur-droit-arrondi/README.md).
Le maître [`meshy-e45e5d8.glb`](../../../assets/models/meshy-e45e5d8.glb) reste intact.
Les sept autres masques sont copiés à l’identique. Les dossiers précédents ne
sont pas réécrits et ce dossier n’est pas importé par l’application.

Reproduction depuis la racine, avec les dépendances gratuites des
[outils M4C](../../../tools/m4c/README.md) :

```sh
python tools/m4c/trim_posterior_lower.py prepare
blender -b -t 2 --python-exit-code 1 --python tools/m4c/project_mask_outline.py -- --asset-dir docs/m4c/meshy-posterieur-droit-bord-inferieur --base-blend docs/m4c/meshy-posterieur-droit-arrondi/meshy-posterieur-droit-arrondi.blend
python tools/m4c/trim_posterior_lower.py finish
python tools/m4c/audit_lower_posterior.py
python tools/m4c/audit_continuity.py --asset-dir docs/m4c/meshy-posterieur-droit-bord-inferieur
node tools/m4c/audit-picking.mjs docs/m4c/meshy-posterieur-droit-bord-inferieur
blender -b -t 4 --python-exit-code 1 --python tools/m4c/render_lower_posterior.py
python tools/m4c/compose_lower_posterior.py
```

Pour modifier les repères, ajuster la préparation puis régénérer les dérivés.
Les PNG sont éditables, mais l’atlas discret, le masque et les packs de rendu
doivent rester synchronisés. `source-green-samples.npz` conserve les points
de l’ancien vert, les projections réelles et les coordonnées de prolongement
dans les marges UV ; `surface-candidates.npz` et `surface-visibility.npz`
conservent le domaine local et ses contrôles.

Les planches utilisent seulement libellés, mise en page et réduction
proportionnelle. Les images brutes restent disponibles dans `renders`.
**Proposition non validée automatiquement. PR #17 en brouillon, sans fusion.**

Model created with Meshy — [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
