# M4A — Finition locale du cou, base 62000ae

> Model created with [Meshy](https://www.meshy.ai/) — [CC BY 4.0 License](https://creativecommons.org/licenses/by/4.0/).

Adaptation : lissage local de la base de tête, des côtés du cou, de la nuque et
des raccords immédiats aux trapèzes. Déplacements limités à 3 mm, topologie
inchangée. Visage, menton, cheveux et corps hors zone protégés.

- [Rapport](../../M4A_MESHY_FINITION_LOCALE_COU.md)
- [Avant / après serré](renders/comparatif-finition-cou.png)
- [Contrôle de la tête](renders/controle-tete.png)
- [Mannequin complet](renders/mannequin-complet.png)
- [Blender](meshy-corps-tete-assemble.blend)
- [GLB](meshy-corps-tete-assemble.glb)
- [Contrôles géométriques](verification.json)
- [Contrôles des rendus](renders/verification.json)
- [Base précédente intacte](../meshy-tete-source-conservee/README.md)

Le Blender contient deux scènes :

- `00_AVANT_FINITION_62000AE` : copie de la proposition précédente, inchangée.
- `01_ASSEMBLAGE_CORPS_TETE` : finition locale, seule scène exportée en GLB.

`assemblage.json` conserve les empreintes de la référence et les paramètres de
finition. Les positions avant/après, les triangles, le masque et ses poids sont
dans `finish-provenance.npz`, sans code exécutable. Les attributs de faces hérités
indiquent la provenance initiale ; ils ne signifient pas que la surface retouchée
du cou est encore strictement identique aux sources Meshy brutes. Il ne s’agit
pas d’une segmentation musculaire interactive.
Les champs hérités du découpage décrivent la construction de la base ; les
comptes de protection effectifs de cette finition sont ceux de `verification.json`
et du masque conservé dans `finish-provenance.npz`.

## Reproduction

Depuis la racine du dépôt, avec Blender 4.3.2 :

```bash
blender --background --factory-startup --disable-autoexec --python-exit-code 1 \
  --python tools/m4a-meshy/finish_native_neck.py -- \
  --source docs/m4a/meshy-tete-source-conservee \
  --output docs/m4a/meshy-finition-locale-cou
```

Puis `export_head_assembly.py` et `check_neck_finish.py`, via Blender avec
`-- --asset docs/m4a/meshy-finition-locale-cou`.

Pour chacun des modes `before` et `after` :

```bash
blender --background --factory-startup --disable-autoexec --python-exit-code 1 \
  --python tools/m4a-meshy/render_head_assembly.py -- \
  --asset docs/m4a/meshy-finition-locale-cou --mode before \
  --views tete-face tete-profil tete-trois-quarts \
  raccord-profil raccord-face raccord-trois-quarts
```

Ajouter `face` à la liste des vues du mode `after` pour le mannequin complet.

```bash
python tools/m4a-meshy/compose_neck_finish.py \
  --asset docs/m4a/meshy-finition-locale-cou
```

Cycles CPU, 32 échantillons, sans débruitage ; images brutes intactes. Pillow
ajoute seulement les légendes et le redimensionnement uniforme des planches.
Aucune dépendance ajoutée à l’application.

Sources réutilisées sans modification : [corps](../meshy/source.glb) et
[tête Marble Titan](../meshy-assemblage-tete-marble-titan/source-tete.glb).
La formule gratuite a été déclarée dans la conversation ; les originaux ne
contiennent pas de licence embarquée. [Provenance Meshy](../meshy/LICENCE_ET_PROVENANCE.md).
Attribution et modifications embarquées dans le GLB, aucune dépense supplémentaire.

PR #12 en brouillon, sans fusion. Application et SQLite inchangées.
Arrêt pour validation visuelle.
