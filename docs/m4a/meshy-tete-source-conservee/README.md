# M4A — Tête Marble Titan source conservée

> Model created with [Meshy](https://www.meshy.ai/) — [CC BY 4.0 License](https://creativecommons.org/licenses/by/4.0/).

Adaptation : tête donneuse et dessous du menton conservés, découpe de sa base
cervicale et jonction locale avec le corps Anatomical Form. La bande supérieure
de 12 mm du cou receveur est remplacée ; le reste du corps n’est pas retouché.

- [Rapport](../../M4A_MESHY_RETOUR_TETE_SOURCE.md)
- [Comparatif tête de base / proposition](renders/comparatif-tete-source.png)
- [Gros plan du raccord](renders/comparatif-raccord-source.png)
- [Mannequin complet](renders/mannequin-complet.png)
- [Blender](meshy-corps-tete-assemble.blend)
- [GLB](meshy-corps-tete-assemble.glb)
- [Vérifications géométriques](verification.json)
- [Vérifications des rendus](renders/verification.json)
- [Corps source réutilisé, intact](../meshy/source.glb)
- [Tête source réutilisée, intacte](../meshy-assemblage-tete-marble-titan/source-tete.glb)

Les noms de fichiers utilisateur, empreintes et découpes sont conservés dans
`assemblage.json`. `assembly-provenance.npz` conserve les surfaces intermédiaires
et leurs correspondances avec les triangles des originaux, sans code exécutable.
Les attributs de faces de provenance ne constituent pas une segmentation
musculaire interactive du GLB.

Le Blender contient quatre scènes :

- `00_CORPS_ORIGINAL` : Anatomical Form complet d’origine.
- `02_TETE_DONNEUSE_SOURCE` : donneur Marble Titan complet, intact, placé
  uniformément ; référence des comparatifs.
- `03_ASSEMBLAGE_DBBA75E` : ancien assemblage conservé pour le contrôle du corps.
- `01_ASSEMBLAGE_CORPS_TETE` : nouvelle proposition, seule exportée en GLB.

## Reproduction

Depuis la racine du dépôt, avec Blender 4.3.2 :

```bash
blender --background --factory-startup --disable-autoexec --python-exit-code 1 \
  --python tools/m4a-meshy/restore_native_head.py -- \
  --source docs/m4a/meshy-assemblage-tete-marble-titan \
  --output docs/m4a/meshy-tete-source-conservee
```

Puis `export_head_assembly.py` et `check_native_head.py`, via Blender, chacun
avec `-- --asset docs/m4a/meshy-tete-source-conservee`.

Rendus de référence avec `render_head_assembly.py` :

```bash
blender --background --factory-startup --disable-autoexec --python-exit-code 1 \
  --python tools/m4a-meshy/render_head_assembly.py -- \
  --asset docs/m4a/meshy-tete-source-conservee --mode before \
  --views tete-face tete-profil tete-trois-quarts raccord-profil
```

Reprendre la commande avec `--mode after` et ajouter `face` à la liste des vues.

```bash
python tools/m4a-meshy/compose_native_head.py \
  --asset docs/m4a/meshy-tete-source-conservee
```

Cycles CPU, 32 échantillons, sans débruitage ; images brutes intactes.
Pillow sert uniquement aux légendes et au redimensionnement des planches.
Aucune dépendance ajoutée à l’application.

Les originaux n’embarquent pas de licence ; la formule gratuite a été déclarée
dans la conversation. [Provenance et attribution Meshy](../meshy/LICENCE_ET_PROVENANCE.md).
Les modifications sont indiquées et l’attribution est embarquée dans le GLB.
Budget additionnel nul.

Les anciens fichiers restent intacts. PR #12 en brouillon, sans fusion ;
application et SQLite inchangées. Arrêt pour validation visuelle.
