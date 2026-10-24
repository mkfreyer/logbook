# M4A — Assemblage pieds / aine validée

- Corps et aine : `41896cc`, conservés à l’identique hors des deux pieds remplacés.
- Pieds : `8a8b95e`, transférés à l’identique. Aucune nouvelle sculpture.
- [Rapport](../../M4A_PIEDS_AINE_VALIDEE.md)
- [Face / trois quarts](renders/comparatif-pieds.png)
- [Profils](renders/comparatif-profils.png)
- [Chevilles](renders/raccords-chevilles.png)
- [Vue générale](renders/planche-generale.png)
- [Blender](ecorche-pieds-aine-validee.blend), scène `27_PIEDS_AINE_VALIDEE`
- [GLB neutre de contrôle](ecorche-pieds-aine-validee.glb)

`finition.json` documente les deux sources et leurs empreintes.
`verification.json` compare les 297 objets du corps à `41896cc` et les deux
pieds à `8a8b95e`, y compris topologie, normales et matériaux. Il réexécute
les contrôles locaux des pieds et vérifie l’export.
`selection-map.json` conserve les six zones des deltoïdes et leur correspondance
avec les primitives GLB. Les contacts des pieds restent enfouis, sans soudure
globale. Les fichiers `foot-left.npz` et `foot-right.npz` d’origine restent
disponibles dans [le dossier de la retouche des pieds](../ecorche-beatriz-finition-pieds/).

## Reproduction

Depuis la racine du dépôt, avec Blender 4.3.2 :

```bash
blender --background --factory-startup --disable-autoexec --python-exit-code 1 \
  --python tools/m4a-ecorche/pieds_assemblage.py -- \
  --body docs/m4a/ecorche-beatriz-aine-homogene/ecorche-aine-homogene.blend \
  --feet docs/m4a/ecorche-beatriz-finition-pieds/ecorche-finition-pieds.blend \
  --output docs/m4a/ecorche-beatriz-pieds-aine-validee
```

Exécuter ensuite `pieds_export.py`, puis `pieds_verify.py` avec
`-- --asset docs/m4a/ecorche-beatriz-pieds-aine-validee`.
`pieds_render.py` reçoit en plus `--mode before`, puis `--mode after`.
Enfin, `python tools/m4a-ecorche/pieds_compose.py --asset
docs/m4a/ecorche-beatriz-pieds-aine-validee` compose les planches avec Pillow.
Les images individuelles sont de vrais rendus Cycles CPU, 32 échantillons,
sans débruitage ni retouche. Aucune dépendance applicative ajoutée.

## Attribution

Corps : **Ecorche - Anatomy study**, Beatriz Gomez Santamaria,
[source](https://sketchfab.com/3d-models/ecorche-anatomy-study-e402d3d541eb4b199c57d5410f5d3c57),
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Adaptations Logbook des passes précédentes, finition des pieds et assemblage
avec l’aine choisie. Tête / yeux : Dan Ulrich, Blender Studio Human Base Meshes
v1.4.1, CC0 ; [licence conservée](../ecorche-beatriz-passe5/HEAD_SOURCE_LICENSE.md).

PR #12 en brouillon, sans fusion. Arrêt pour validation avant toute intégration.
