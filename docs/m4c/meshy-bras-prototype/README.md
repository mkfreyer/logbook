# Prototype bras — quatre nouvelles régions, huit anciennes intactes

[Rapport et rendus](../../M4C_PROTO_BRAS_CARTOGRAPHIE.md) ·
[Inventaire des groupes restants](../../M4C_INVENTAIRE_MUSCLES_SUPERFICIELS.md).

Base `d552e23`, maître `e45e5d8`. UV0 et huit PNG historiques exacts.
UV1 est un jeu de travail local aux bras, sur une copie, sans changement de surface.
`muscle-ids.png` utilise UV0 ; `muscle-ids-arms.png` utilise UV1. Les deux PNG ne
doivent pas être superposés dans un même espace UV. Les codes 9–12 sont les seuls
nouveaux masques, non intégrés au visualiseur iPhone.

Ouvrir `meshy-bras-prototype.blend` : douze valeurs `SHOW::<id>` permettent les
contrôles de sélection. Tous les `SHOW` à zéro donnent le neutre. Les guides 3D
sont cachés et ne sont pas des volumes musculaires ajoutés. Les PNG individuels
et RGBA sont éditables ; `regions.json` et `registry-twelve.json` documentent les IDs.

Reproduction depuis la racine, avec Blender 4.3.2 et les outils Python gratuits
NumPy, SciPy, Pillow et Matplotlib :

```sh
blender -b --python-exit-code 1 --python tools/m4c/prepare_arm_prototype.py
blender -b --python-exit-code 1 --python tools/m4c/project_arm_guides.py
python tools/m4c/bake_arm_prototype.py
python tools/m4c/inventory_arm_scope.py
python tools/m4c/audit_arm_prototype.py
blender -b --python-exit-code 1 --python tools/m4c/render_arm_prototype.py
python tools/m4c/compose_arm_prototype.py
python tools/m4c/audit_arm_prototype.py --final
```

Les prévisualisations et adaptations temporaires des audits de continuité sont
écrites dans un dossier cache voisin du dépôt de travail, sans écraser les anciens
assets. Les UV de Blender ont l'origine en bas ; les PNG d'IDs et les coordonnées
de sélection glTF ont l'origine en haut (`v_gltf = 1 - v_blender`). Utiliser les
IDs en filtrage nearest sans mipmaps ; les couvertures RGBA sont des données
Non-Color, `CHANNEL_PACKED`, filtrées linéairement dans les rendus.

Le futur export GLB/visualiseur devra prendre en charge les deux jeux UV ou
consolider les nouveaux territoires. Aucun export interactif ni code iPhone ne
change dans cette livraison. La validation utilisateur est attendue avant la suite.
