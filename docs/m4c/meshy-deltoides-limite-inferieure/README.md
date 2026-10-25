# Correction locale du masque postérieur — PR #17

- [Rapport](../../M4C_CORRECTION_DELTOIDES_POSTERIEURS.md)
- [Comparatif à l’angle annoté](renders/comparatif-angle-reference.png)
- [Deux épaules](renders/comparatif-deux-epaules.png)
- [Profils et arrière trois quarts](renders/comparatif-profils-arriere.png)
- [Blender corrigé, texture embarquée](meshy-eight-zones-corrected.blend)
- [GLB coloré de contrôle](exports/meshy-eight-zones-control.glb)
- [Huit masques, atlas d’IDs et palette](textures)
- [Huit identifiants et courbes de correction](regions.json)
- [Binding source et bornes actualisées](region-binding.json)

Le maître neutre reste [le GLB validé](../../../assets/models/meshy-e45e5d8.glb).
Les UV et bindings binaires du [prototype initial](../meshy-huit-zones/README.md)
sont réutilisés à l’identique. Le GLB coloré reste un contrôle statique, sans
branchement à l’interface de Logbook.

Reproduction, depuis la racine du dépôt, avec les dépendances gratuites des
[outils M4C](../../../tools/m4c/README.md) :

```sh
blender -b -t 2 --python-exit-code 1 --python tools/m4c/capture_posterior_crease.py
python tools/m4c/correct_posterior_masks.py
python tools/m4c/audit_posterior_correction.py
python tools/m4c/audit_continuity.py --asset-dir docs/m4c/meshy-deltoides-limite-inferieure
node tools/m4c/audit-picking.mjs docs/m4c/meshy-deltoides-limite-inferieure
blender -b -t 4 --python-exit-code 1 --python tools/m4c/render_posterior_correction.py
python tools/m4c/compose_posterior_comparisons.py
```

Les repères de raccord sont dans `crease-landmarks.json`. Les points intérieurs
pris sur la vue annotée sont dans `annotated-surface-probes.json`. Ils sont
contrôlés contre les deux atlas pour confirmer le passage vert → neutre.
Les seules données modifiées sont les masques postérieurs et leurs dérivés.
Les positions, normales, UV et indices ne sont ni recalculés ni réexportés par
Blender : le GLB copie leurs buffers existants et remplace les PNG embarqués.

`blender-preservation.json` compare aussi les empreintes des coordonnées,
indices, UV et normales par coin avant/après remplacement de l’image de masque.
Les images brutes restent disponibles dans `renders` ; les planches ajoutent
uniquement libellés, recadrage commun et redimensionnement proportionnel.

**Placement proposé, en attente de validation.**
Model created with Meshy — [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
