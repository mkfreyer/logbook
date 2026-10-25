# M4A — Assemblage des deux modèles Meshy fournis

> Model created with [Meshy](https://www.meshy.ai/) — [CC BY 4.0 License](https://creativecommons.org/licenses/by/4.0/).

Adaptation Logbook : retrait de la tête du corps Anatomical Form, extraction
de la tête Rib Reach Exercise, ajustement uniforme et reconstruction locale
de la jonction. Aucun changement du corps conservé sous la découpe.

- [Rapport](../../M4A_MESHY_ASSEMBLAGE_CORPS_TETE.md)
- [Trois vues du mannequin assemblé](renders/mannequin-assemble.png)
- [Comparatif des têtes et raccords](renders/comparatif-tetes.png)
- [Comparatif général](renders/comparatif-ensemble.png)
- [Blender](meshy-corps-tete-assemble.blend)
- [GLB assemblé](meshy-corps-tete-assemble.glb)
- [Corps source intact](../meshy/source.glb)
- [Source tête intacte](source-tete.glb)
- [Contrôles indépendants](verification.json)

Le corps archivé est byte pour byte identique au fichier utilisateur
`Meshy_AI_Anatomical_Form_1025014819_generate.glb`.
La source de la tête est le fichier utilisateur
`Meshy_AI_Rib_Reach_Exercise_In_1025014903_generate.glb`.
`assemblage.json` conserve leurs SHA-256 et la transformation utilisée.
`assembly-provenance.npz` conserve les surfaces intermédiaires et leurs
correspondances avec les triangles sources, sans instruction exécutable.

Dans Blender :

- `00_CORPS_ORIGINAL` : le premier modèle complet, intact.
- `01_ASSEMBLAGE_CORPS_TETE` : l’assemblage proposé, seul exporté en GLB.

Les attributs de faces `surface_source` et `source_triangle` servent au
contrôle de provenance dans Blender, sans être présentés comme une segmentation
musculaire interactive ou comme des attributs automatiquement disponibles dans
le GLB. L’export contient la provenance et l’attribution dans ses métadonnées.

## Reproduction

Depuis la racine du dépôt, avec Blender 4.3.2 :

```bash
blender --background --factory-startup --disable-autoexec --python-exit-code 1 \
  --python tools/m4a-meshy/assemble_head.py -- \
  --body docs/m4a/meshy/source.glb \
  --head-source docs/m4a/meshy-assemblage-corps-tete/source-tete.glb \
  --output docs/m4a/meshy-assemblage-corps-tete
```

Puis `export_head_assembly.py`, suivi de `check_head_assembly.py`, chacun avec
`-- --asset docs/m4a/meshy-assemblage-corps-tete`.
Exécuter `render_head_assembly.py` avec le même argument et `--mode before`,
puis `--mode after`.

```bash
python tools/m4a-meshy/compose_head_assembly.py \
  --asset docs/m4a/meshy-assemblage-corps-tete
```

Rendus Cycles CPU, 32 échantillons, sans débruitage ni retouche d’image.
Les planches utilisent Pillow pour les légendes et le redimensionnement.
Aucune dépendance ajoutée à l’application.

## Conditions et arrêt

La déclaration de formule gratuite et les conditions sont documentées dans
[la provenance Meshy existante](../meshy/LICENCE_ET_PROVENANCE.md) et dans le
[centre d’aide officiel](https://help.meshy.ai/en/articles/10137554-what-is-the-ownership-of-the-generated-models).
Les nouveaux fichiers sont fournis par l’utilisateur dans la même conversation ;
les métadonnées GLB indiquent `meshy-scene`, sans licence embarquée dans les
originaux. L’adaptation et les rendus conservent l’attribution Meshy.

PR #12 en brouillon, sans fusion. Application et SQLite inchangées.
Arrêt pour validation avant toute intégration.
