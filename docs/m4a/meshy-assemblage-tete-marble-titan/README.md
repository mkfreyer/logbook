# M4A — Assemblage avec la tête Marble Titan

> Model created with [Meshy](https://www.meshy.ai/) — [CC BY 4.0 License](https://creativecommons.org/licenses/by/4.0/).

Adaptation : corps Anatomical Form conservé sous la découpe cervicale, tête
Marble Titan ajustée uniformément, raccord cervical reconstruit localement.
Visage et cheveux conservés. Les sources sont fournies par l’utilisateur.

- [Rapport](../../M4A_MESHY_TETE_MARBLE_TITAN.md)
- [Mannequin assemblé](renders/mannequin-assemble.png)
- [Comparatif des têtes](renders/comparatif-tetes.png)
- [Comparatif général](renders/comparatif-ensemble.png)
- [Blender](meshy-corps-tete-assemble.blend)
- [GLB](meshy-corps-tete-assemble.glb)
- [Corps source intact](../meshy/source.glb)
- [Source tête intacte](source-tete.glb)
- [Contrôles géométriques](verification.json)
- [Contrôles des rendus](renders/verification.json)

`assemblage.json` conserve les noms des fichiers utilisateur, les empreintes
SHA-256, les transformations et la référence de l’assemblage précédent.
`assembly-provenance.npz` contient les surfaces intermédiaires et leurs
correspondances avec les triangles sources, sans instruction exécutable.

Le Blender contient trois scènes :

- `00_CORPS_ORIGINAL` : corps Anatomical Form complet, intact.
- `01_ASSEMBLAGE_CORPS_TETE` : proposition Marble Titan, seule exportée en GLB.
- `02_ASSEMBLAGE_PRECEDENT` : copie exacte de l’assemblage Rib Reach publié,
  utilisée pour les comparatifs.

Les attributs de faces `surface_source` et `source_triangle` servent uniquement
au contrôle de provenance dans Blender. Ce ne sont pas des zones musculaires
interactives, et ils ne sont pas automatiquement exportés dans le GLB.

## Reproduction

Depuis la racine du dépôt, avec Blender 4.3.2 :

```bash
blender --background --factory-startup --disable-autoexec --python-exit-code 1 \
  --python tools/m4a-meshy/assemble_head.py -- \
  --body docs/m4a/meshy/source.glb \
  --head-source docs/m4a/meshy-assemblage-tete-marble-titan/source-tete.glb \
  --output docs/m4a/meshy-assemblage-tete-marble-titan \
  --comparison docs/m4a/meshy-assemblage-corps-tete
```

Exécuter ensuite `export_head_assembly.py`, puis `check_head_assembly.py`,
chacun par Blender avec `-- --asset docs/m4a/meshy-assemblage-tete-marble-titan`.
Exécuter `render_head_assembly.py` avec ce même argument et `--mode before`,
puis `--mode after`.

```bash
python tools/m4a-meshy/compose_head_assembly.py \
  --asset docs/m4a/meshy-assemblage-tete-marble-titan
```

Cycles CPU, 32 échantillons, sans débruitage ; Pillow pour les légendes et le
redimensionnement des planches. Aucune dépendance ajoutée à l’application.

La licence est documentée dans la [provenance Meshy](../meshy/LICENCE_ET_PROVENANCE.md)
et le rapport ; les originaux n’embarquent pas de licence. Les modifications
sont indiquées et l’attribution est conservée dans le GLB et les rendus.

Arrêt pour validation. PR #12 en brouillon, sans fusion. Application et SQLite
inchangées ; les anciens assemblages restent dans leurs dossiers et l’historique.
