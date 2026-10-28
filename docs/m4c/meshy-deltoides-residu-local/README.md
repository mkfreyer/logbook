# Petit résidu vert — sources de contrôle M4C

- [Rapport de correction](../../M4C_RESIDU_VERT_LOCAL.md)
- [Avant / après serré](renders/comparatif-residu-serre.png)
- [Après brut sans annotation](renders/apres-gros-plan.png)
- [Contexte](renders/comparatif-contexte.png)
- [Angles voisins](renders/comparatif-angles-voisins.png)
- [Blender corrigé avec masques embarqués](meshy-residu-corrige.blend)
- [GLB coloré de contrôle](exports/meshy-eight-zones-control.glb)
- [Atlas et huit masques](textures)
- [Huit identifiants](regions.json) et [binding](region-binding.json)

Base : correction `71f70dc` dans
[`meshy-deltoides-limite-inferieure`](../meshy-deltoides-limite-inferieure/README.md).
Les sept autres masques sont copiés à l’identique. Le maître neutre reste
[`meshy-e45e5d8.glb`](../../../assets/models/meshy-e45e5d8.glb), non modifié.
Ce dossier n’est importé ni par l’application ni par son visualiseur.

Reproduction depuis la racine, avec les prérequis gratuits des
[outils M4C](../../../tools/m4c/README.md) :

```sh
blender -b -t 2 --python-exit-code 1 --python tools/m4c/capture_residue_patch.py
python tools/m4c/refine_posterior_residue.py
python tools/m4c/audit_residue_correction.py
python tools/m4c/audit_continuity.py --asset-dir docs/m4c/meshy-deltoides-residu-local
node tools/m4c/audit-picking.mjs docs/m4c/meshy-deltoides-residu-local
blender -b -t 4 --python-exit-code 1 --python tools/m4c/render_residue_correction.py
python tools/m4c/compose_residue_comparisons.py
```

`patch-guides.json` décrit la courte frontière et son emprise autorisée.
`surface-samples.json` contient les impacts sur la surface source.
`cause-and-probes.json` compare IDs et poids de texture aux mêmes points avant
et après. `textures/changed-texels.png` montre les seuls texels retirés.

L’audit compare les buffers GLB, le fichier source validé, les sept autres
masques et les fichiers applicatifs protégés. `blender-preservation.json`
compare aussi positions, indices, UV et normales par coin dans Blender.
`renders/render-metadata.json` conserve les empreintes des images brutes, les
matrices de caméra et le cadrage. Les planches ajoutent uniquement libellés,
mise en page et réduction proportionnelle : aucun pixel du mannequin n’est
repeint dans les rendus.

**Proposition non validée automatiquement. PR #17 en brouillon, sans fusion.**
Model created with Meshy — [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
