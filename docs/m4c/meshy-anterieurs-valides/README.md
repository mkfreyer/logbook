# M4C — référence approuvée des antérieurs

[Rapport de promotion et contrôles](../../M4C_ANTERIEURS_VALIDES_REFERENCE.md).

Source approuvée : PR #19, commit `09c61ab`. Les deux contours antérieurs et les
atlas sont exacts ; les six autres masques sont ceux de `06fa665`.
`provenance.json` relie chaque fichier officiel à son chemin source et à son SHA.

Le Blender conserve les images empaquetées de la version approuvée. Il s'ouvre
avec les deux antérieurs orange pour contrôle ; mettre tous les `SHOW::` à zéro
pour le matériau neutre. Les huit IDs et les guides cachés restent disponibles.
Le GLB coloré est réservé au contrôle. L'application utilise la dérivation neutre
produite par `tools/m4d/build-selection.mjs`.

Depuis la racine, avec les outils gratuits déjà utilisés pour M4C :

```sh
python tools/m4c/promote_validated_anterior.py
python tools/m4c/audit_continuity.py --asset-dir docs/m4c/meshy-anterieurs-valides
node tools/m4c/audit-picking.mjs docs/m4c/meshy-anterieurs-valides
python tools/m4c/audit_validated_anterior.py
```

Les commandes lisent les objets Git de `09c61ab` sans changer la branche de la
PR #19, puis régénèrent les atlas. Aucun outil payant, sculpture ou changement UV.
