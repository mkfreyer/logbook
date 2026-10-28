# Meshy — huit zones M4C proposées

**Placement anatomique à valider. Aucun branchement dans Logbook.**

- [Rapport principal](../../M4C_MESHY_HUIT_ZONES.md)
- [Blender éditable, textures embarquées](meshy-eight-zones.blend)
- [GLB coloré de contrôle](exports/meshy-eight-zones-control.glb)
- [GLB neutre validé, conservé sans changement](../../../assets/models/meshy-e45e5d8.glb)
- [Huit identifiants, repères et convention gauche/droite](regions.json)
- [Binding de sélection et bornes des zones](region-binding.json)
- [Atlas d’IDs et huit masques](textures)
- [Six angles](renders/planche-huit-zones.png)
- [Pectoraux](renders/planche-pectoraux.png)
- [Deltoïdes](renders/planche-deltoides.png)
- [Contrôle neutre comparé](renders/controle-neutre.png)
- [Mannequin complet neutre](renders/neutre-complet.png)
- [Une seule zone activée](renders/independance-pectoral-gauche.png)

## Fichiers techniques

`source-uv-binding.npz` contient les UV par coin des triangles source (convention
Blender, V vers le haut) et leur support. `exports/source-face-indices.u32` et
`exports/source-corner-uv.f32` sont le binding compact pour un `SurfaceHit` du
visualiseur actuel, dont le modèle source n’a aucun UV. Leurs valeurs sont en
little-endian, avec UV glTF (V vers le bas). Le binding est lié au SHA-256 du
GLB source ; les noms anatomiques stables ne sont pas des indices de triangles.

`exports/export-source-binding.npz` prouve la correspondance des doublons UV
avec les sommets source. `uv-repair.json` documente les quelques petites faces
isolées en UV pour supprimer des recouvrements de projection ; aucun triangle
3D n’est découpé. `mask-cleanup.json` décrit le nettoyage de quelques texels.
`face-samples.npy` est un diagnostic par centres de faces, **pas la segmentation**.

Le GLB coloré embarque une texture couleur PBR **statique** pour le contrôle.
L’atlas d’IDs est aussi embarqué, référencé dans les extras du matériau ; un
chargeur glTF ne l’active pas automatiquement. La future sélection dynamique
nécessitera un chargement explicite des IDs et une palette/shader appropriée,
après validation des contours. Les huit contrôles de couleur indépendants sont
éditables et visibles dans Blender dès maintenant.

## Vérifications

[Buffers et surface](verification.json) · [Continuité des masques](continuity-audit.json) ·
[Raycasts source/export](picking-audit.json) · [Import Blender](blender-import-audit.json) ·
[Comparaisons neutres](render-verification.json) · [Coûts](delivery-metrics.json).

Voir les [outils reproductibles](../../../tools/m4c/README.md). Les caméras,
matériaux et éclairages sont communs aux comparaisons. Les planches ajoutent
uniquement des libellés, une légende et un redimensionnement proportionnel.

**Model created with [Meshy](https://www.meshy.ai/) — [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).**
Adaptation Logbook : assemblage et finition du cou `e45e5d8` conservés ; ajout
M4C d’UV, de masques de surface et de couleurs de contrôle, sans sculpture.
[Provenance et attribution de la source](../../../assets/models/README.md).
