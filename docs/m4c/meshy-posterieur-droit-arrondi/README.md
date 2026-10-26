# Deltoïde postérieur droit — contour arrondi

[Rapport et rendus](../../M4C_CONTOUR_POSTERIEUR_DROIT_ARRONDI.md).

- [Blender éditable](meshy-posterieur-droit-arrondi.blend), matériau
  `M4C_HUIT_ZONES__PALETTE_EDITABLE` avec `SHOW::<id>` et `COLOR::<id>`.
- [Masque de couverture droit](textures/deltoid.right.posterior.png), PNG L8
  adouci uniquement sur sa nouvelle bordure vert/gris.
- [Atlas d’identification](textures/muscle-ids.png), PNG L8 discret, ID 8 si
  couverture ≥ 128/255. L’identification utilise un échantillonnage nearest.
- [Deux packs RGBA](textures) : seul le canal alpha du second pack change.
- [GLB coloré de contrôle](exports/meshy-eight-zones-control.glb), sans
  intégration à l’application.
- [Repères éditables de la courbe](outline-guides.json) et
  [projections 3D / raycasts](projected-outline.json).

Base géométrique et masques de `18e1a44` :
[`meshy-deltoides-residu-local`](../meshy-deltoides-residu-local/README.md).
Les sept autres PNG sont copiés à l’identique. Le maître neutre
[`meshy-e45e5d8.glb`](../../../assets/models/meshy-e45e5d8.glb) n’est jamais remplacé.

Les PNG sont éditables, mais toute retouche doit garder l’atlas discret et les
packs de rendu synchronisés. La source paramétrique de cette proposition est
la courbe de `outline-guides.json`, reproduite par les repères du script de
préparation. Les fichiers `surface-candidates.npz` et `surface-visibility.npz`
conservent les texels, leurs points 3D, leurs poids et le contrôle de profondeur.

Reproduction depuis la racine, avec les dépendances gratuites des
[outils M4C](../../../tools/m4c/README.md) :

```sh
python tools/m4c/round_posterior_outline.py prepare
blender -b -t 2 --python-exit-code 1 --python tools/m4c/project_posterior_outline.py
python tools/m4c/round_posterior_outline.py finish
python tools/m4c/audit_rounded_posterior.py
python tools/m4c/audit_continuity.py --asset-dir docs/m4c/meshy-posterieur-droit-arrondi
node tools/m4c/audit-picking.mjs docs/m4c/meshy-posterieur-droit-arrondi
blender -b -t 4 --python-exit-code 1 --python tools/m4c/render_rounded_posterior.py
python tools/m4c/compose_rounded_posterior.py
```

Pour modifier les repères paramétriques, ajuster ceux de la préparation puis
régénérer les dérivés et leurs contrôles. Ne pas lancer les scripts des anciens
essais : leurs dossiers doivent rester intacts.

**Proposition à valider, PR #17 en brouillon, sans fusion.**
Model created with Meshy — [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
