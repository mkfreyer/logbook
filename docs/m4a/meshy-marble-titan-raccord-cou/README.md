# M4A — Raccord tête / cou Marble Titan

> Model created with [Meshy](https://www.meshy.ai/) — [CC BY 4.0 License](https://creativecommons.org/licenses/by/4.0/).

Adaptation locale de l’assemblage `dbba75e` : retrait de la collerette et de la
bande inférieure de la tête, reconstruction d’une transition plus progressive.
Corps et partie supérieure de la tête préservés.

- [Rapport](../../M4A_MESHY_RACCORD_TETE_COU.md)
- [Comparatif serré](renders/comparatif-raccord.png)
- [Contrôle général](renders/controle-general.png)
- [Blender](meshy-corps-tete-assemble.blend)
- [GLB](meshy-corps-tete-assemble.glb)
- [Contrôles géométriques](verification.json)
- [Contrôles des rendus](renders/verification.json)
- [Assemblage précédent intact](../meshy-assemblage-tete-marble-titan/README.md)
- [Corps source réutilisé](../meshy/source.glb)
- [Tête donneuse source réutilisée](../meshy-assemblage-tete-marble-titan/source-tete.glb)

`assemblage.json` conserve les empreintes, transformations héritées et limites
de la reprise locale. `assembly-provenance.npz` contient les surfaces conservées
et leurs correspondances avec les triangles sources, sans code exécutable.
Les originaux ne sont pas dupliqués ou écrasés.
Les valeurs de placement de la tête, dont `head_attachment_z_m`, sont héritées
de l’ajustement initial ; le raccord reconstruit est décrit par le nouveau plan
`head_cut_plane_*` et par `local_z_range_m`.

Le Blender contient :

- `00_CORPS_ORIGINAL` : Anatomical Form complet d’origine.
- `02_AVANT_RACCORD` : assemblage Marble Titan publié dans `dbba75e`, inchangé.
- `01_ASSEMBLAGE_CORPS_TETE` : raccord corrigé, seule scène exportée en GLB.

La connectivité et les coordonnées du corps retenu sont identiques à la
référence. La topologie change seulement dans l’ancien raccord et la bande
inférieure de la tête, avec **664 triangles de moins** au total. Les attributs
de faces `surface_source` / `source_triangle` sont des contrôles de provenance
Blender, pas une segmentation interactive exportée.

## Reproduction

Depuis la racine du dépôt avec Blender 4.3.2 :

```bash
blender --background --factory-startup --disable-autoexec --python-exit-code 1 \
  --python tools/m4a-meshy/refine_head_neck.py -- \
  --source docs/m4a/meshy-assemblage-tete-marble-titan \
  --output docs/m4a/meshy-marble-titan-raccord-cou
```

Exécuter ensuite `export_head_assembly.py`, puis `check_neck_refinement.py`
avec Blender et `-- --asset docs/m4a/meshy-marble-titan-raccord-cou`.
Le second appelle aussi les contrôles indépendants de provenance de
`check_head_assembly.py`.

Pour chacun des modes `before` et `after` :

```bash
blender --background --factory-startup --disable-autoexec --python-exit-code 1 \
  --python tools/m4a-meshy/render_head_assembly.py -- \
  --asset docs/m4a/meshy-marble-titan-raccord-cou --mode after \
  --views face trois-quarts raccord-profil raccord-face raccord-trois-quarts
```

```bash
python tools/m4a-meshy/compose_neck_refinement.py \
  --asset docs/m4a/meshy-marble-titan-raccord-cou
```

Cycles CPU, 32 échantillons, sans débruitage. Images brutes intactes ; Pillow
sert seulement aux légendes et au redimensionnement uniforme des planches.
Aucun outil payant, aucune nouvelle génération ni dépendance applicative.
Pour cette livraison, les images « avant » terminées ont été réutilisées après
un contrôle exact de leur scène avec `check_neck_render_reuse.py` ;
`renders/before/reuse.json` en conserve la preuve et les métadonnées originales
restent inchangées. Une reproduction complète peut simplement recalculer les
deux modes sur le master fourni, sans cette réutilisation.

Les conditions et la déclaration de formule gratuite sont conservées dans la
[provenance Meshy](../meshy/LICENCE_ET_PROVENANCE.md). L’attribution et les
modifications figurent dans le GLB et les planches.

Arrêt pour validation visuelle ; PR #12 en brouillon, sans fusion. Aucune
modification de Logbook ou SQLite, aucun M4B ni segmentation musculaire.
