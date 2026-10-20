# M4A Meshy — une passe locale sur les trois masques

[Rapport et verdict](../../../M4A_MESHY_CORRECTION_MASQUES.md) ·
[Blender corrigé](renders/meshy-masques.blend) · [Rendus](renders) ·
[Masques](regions/regions.json) · [GLB et correspondance](export) ·
[Vérifications](verification.json)

**PARTIEL : correction locale du débordement de l’épaule, pas de validation
anatomique complète.** Les contours restent des attributions de triangles
existants. La géométrie et le GLB [Meshy original](../source.glb) sont intacts.
Tous les fichiers du premier POC `ff09299` sont conservés à leur emplacement.

## Autorité des données et reprise

Le nouveau masque est `correction/regions/triangle-regions.u8`. Les octets
indexent les triangles du GLB original, dans leur ordre original. Les valeurs
0 / 1 / 2 / 3 et les identifiants logiques n’ont pas changé.
`regions.json.source_file` est ici relatif au répertoire de `regions.json`.

**Ne pas lancer `segment.py` sur ces sorties.** Il reproduit l’ancienne
annotation projetée ; il ne conserve pas les corrections. Le fichier
[face-edits.json](face-edits.json) liste chaque attribution retirée, son ID de
triangle source, sa valeur précédente et le motif. L’outil `apply_face_edits.py`
applique cette liste au Blender original, vérifie l’état initial et ne fait
aucune classification globale ni opération de géométrie.

Pour une reprise humaine : ouvrir le nouveau Blender, choisir la scène du muscle
concerné, passer en sélection de faces, X-Ray désactivé. Les cinq scènes partagent
le même mesh ; seuls les overrides de matériaux de leurs objets diffèrent.
Les slots 0 / 1 / 2 / 3 signifient non attribué / pectoral gauche / pectoral droit /
deltoïde gauche. Utiliser **Assign**, sans déplacer les faces ni les sommets.

L’attribut FACE `contour_review` repère les frontières **encore à examiner** :
1 = clavicule/aisselle du pectoral gauche, 2 = côté droit contrôlé séparément,
3 = frontière postérieure/insertion du deltoïde. Ce ne sont ni de nouveaux
muscles, ni des labels d’interactivité. `source_triangle_index` donne la provenance.

Pour sélectionner un groupe depuis la console Blender, objet du mannequin actif
et mode Objet (puis revenir en mode Édition, sélection de faces) :

```python
import bpy
mesh = bpy.context.object.data
group = 3  # 1, 2 ou 3, selon la frontière à examiner
review = mesh.attributes['contour_review'].data
for face in mesh.polygons:
    face.select = review[face.index].value == group
```

Le Text datablock `CORRECTION_FACES.json` contient les listes intégrales des faces
modifiées et des faces à examiner. `REGIONS.json` contient les métadonnées mises
à jour, pas celles du premier POC. Les 33 candidats de retrait refusés par la
protection topologique sont également listés ; ne pas les retirer en bloc.

[manual-review.json](manual-review.json), embarqué comme `MANUAL_REVIEW.json`,
isole plus précisément les zones encore problématiques : languette postérieure
du deltoïde, pointe inférieure, sternum, clavicule et pli axillaire de chaque
pectoral. Pour sélectionner les faces d’une de ces zones depuis la console,
toujours en mode Objet sur le mannequin actif :

```python
import json
areas = json.loads(bpy.data.texts['MANUAL_REVIEW.json'].as_string())['areas']
ids = set(next(a for a in areas if a['id'] == 'deltoid_posterior_tongue')['source_triangles'])
source_ids = mesh.attributes['source_triangle_index'].data
for face in mesh.polygons:
    face.select = source_ids[face.index].value in ids
```

Cette liste signale des faces à examiner ; elle n’ordonne pas leur suppression.

## Exporter une édition supplémentaire, seulement après accord

Depuis la racine du dépôt, après un Save As manuel :

```bash
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --python tools/m4a-meshy/save_regions.py -- --blend work/meshy-edite.blend --source docs/m4a/meshy/source.glb --metadata docs/m4a/meshy/correction/regions/regions.json --output work/regions-editees
python tools/m4a-meshy/export_regions_glb.py --source docs/m4a/meshy/source.glb --regions work/regions-editees/regions.json --output work/export-edite
```

L’export contrôlé part des buffers Meshy originaux et produit une **nouvelle**
permutation avec le GLB. Ne jamais réutiliser l’ancien binding après une nouvelle
répartition des triangles. Le contrat de lookup reste celui du
[guide initial](../RAYCAST_ET_EXPORT.md), avec les nouveaux fichiers de
`correction/regions` et `correction/export` utilisés ensemble.

Le BLEU reste le matériau de repos des quatre primitives dans le GLB. L’orange
est un matériau de sélection démontré dans Blender ; un futur moteur devra
activer la primitive visée. Aucun moteur de sélection tactile n’est intégré.

## Reproduire cette livraison

`apply_face_edits.py` prend le Blender original de `ff09299` et la liste figée.
Ensuite : `save_regions.py`, `export_regions_glb.py`, `render_correction.py`
(`--version after`, puis `--version before`, `--samples 48`),
`finish_correction.py`, `compare_correction.py` et `check_correction.py`.
Les trois derniers prennent `--prepared docs/m4a/meshy`. Les rendus viennent des
scènes Blender existantes ; les planches assemblent des captures sans retoucher
la couleur ou les contours des muscles. Le plan mobile réduit chaque vue corps
entier à 390 px, sans zoom.

Les frontières proposées restent une interprétation visuelle sur ce Meshy
stylisé. Pas d’anatomie nouvelle, de segmentation complète, d’intégration,
de SQLite, de M4B, d’achat, d’Astra ou de fusion. PR #12 en brouillon ; PR #11 intacte.

Model created with Meshy – CC BY 4.0 License.
[Provenance et conditions conservées](../LICENCE_ET_PROVENANCE.md).
