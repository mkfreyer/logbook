# Écorché — deuxième passe ciblée

[Rapport, rendus et limites](../../M4A_ECORCHE_PASSE2_CIBLEE.md).

La première passe dans `../ecorche-beatriz-retouche/` est conservée intégralement.
`ecorche-passe2.blend` contient l’avant/après en mat neutre et la présentation bleue.
`ecorche-passe2.glb` applique les corrections et conserve les objets avec leur
identifiant. Les trois groupes d’édition du deltoïde restent dans Blender ;
ils ne sont pas des masques interactifs exportés.

## Reproduction

Python : NumPy et Pillow. Blender 4.3.2. Depuis la racine du dépôt :

```bash
ASSET=docs/m4a/ecorche-beatriz-passe2
WORK=/workspace/work/ecorche-passe2-reproduction
mkdir -p "$WORK"
XDG_CONFIG_HOME="$WORK/blender-config" blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/passe2_build.py -- --baseline docs/m4a/ecorche-beatriz-retouche/ecorche-athletique.blend --output "$ASSET"
XDG_CONFIG_HOME="$WORK/blender-config" blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/passe2_render.py -- --asset "$ASSET"
XDG_CONFIG_HOME="$WORK/blender-config" blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/passe2_export.py -- --asset "$ASSET"
XDG_CONFIG_HOME="$WORK/blender-config" blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/passe2_verify.py -- --asset "$ASSET"
python tools/m4a-ecorche/passe2_compose.py --asset "$ASSET"
```

Ces commandes remplacent les sorties de la deuxième passe : utiliser un autre
`ASSET` pour préserver les fichiers livrés. La source et la première passe ne
sont jamais écrites. Le vérificateur confirme leur conservation, les 378 objets
inchangés, les indices et les coutures, la symétrie, le volume des deltoïdes,
les profils du sillon dorsal et les surfaces du GLB réellement exporté.
La géométrie est contrôlée à une précision d’un micromètre pour l’export ;
ce n’est pas une certification médicale ni un test sur appareil mobile.

## Attribution

**Ecorche - Anatomy study — Beatriz Gomez Santamaria**
([source](https://sketchfab.com/3d-models/ecorche-anatomy-study-e402d3d541eb4b199c57d5410f5d3c57),
[autrice](https://sketchfab.com/BeatrizGomez)).
**[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)** selon les métadonnées
du fichier fourni. Adaptation Logbook : reconstruction symétrique, volumes
athlétiques et deuxième passe ciblée sur deltoïdes, bras, sillon dorsal et surfaces.
Conserver crédit, lien de licence et mention des modifications à la redistribution.
