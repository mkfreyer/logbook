# Écorché — troisième passe ciblée

[Rapport et rendus](../../M4A_ECORCHE_PASSE3_CIBLEE.md).

Les versions précédentes dans `../ecorche-beatriz-passe2/` et
`../ecorche-beatriz-retouche/` restent intactes. Le master contient les scènes
`07_AVANT_PASSE3` et `08_PASSE3_NEUTRE`. Les quatre pièces remaillées ont une
shape key `SURFACE_RECONSTRUITE`, qui est leur référence **après reconstruction** ;
elle ne reconstitue pas exactement leur ancienne topologie. La scène 07 permet
la comparaison exacte avec la passe 2. La clé `CORRECTIONS_PASSE3` est appliquée
dans le GLB de validation, lui aussi mat neutre.

## Reproduction

Blender 4.3.2, NumPy, Pillow. Depuis la racine du dépôt :

```bash
ASSET=docs/m4a/ecorche-beatriz-passe3
WORK=/workspace/work/ecorche-passe3-reproduction
mkdir -p "$WORK"
XDG_CONFIG_HOME="$WORK/blender-config" blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/passe3_build.py -- --baseline docs/m4a/ecorche-beatriz-passe2/ecorche-passe2.blend --output "$ASSET"
XDG_CONFIG_HOME="$WORK/blender-config" blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/passe3_midline.py -- --asset "$ASSET" --build-only
XDG_CONFIG_HOME="$WORK/blender-config" blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/passe3_render.py -- --asset "$ASSET"
XDG_CONFIG_HOME="$WORK/blender-config" blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/passe3_export.py -- --asset "$ASSET"
XDG_CONFIG_HOME="$WORK/blender-config" blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/passe3_verify.py -- --asset "$ASSET"
python tools/m4a-ecorche/passe3_compose.py --asset "$ASSET"
```

Utiliser un autre `ASSET` pour préserver les sorties livrées. La source et les
passes précédentes ne sont jamais écrites. Le diagnostic d’éclairage utilise
aussi le PNG inchangé `../ecorche-beatriz-passe2/renders/apres-face.png` ; son
empreinte est enregistrée dans les métadonnées de la planche.

## Attribution

**Ecorche - Anatomy study — Beatriz Gomez Santamaria**
([source](https://sketchfab.com/3d-models/ecorche-anatomy-study-e402d3d541eb4b199c57d5410f5d3c57),
[autrice](https://sketchfab.com/BeatrizGomez)),
**[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)** selon les métadonnées
du GLB fourni. L’attache médiane est une reconstruction stylisée
complémentaire de tissu de liaison ; son rôle non musculaire est conservé dans
les extras du GLB. Adaptation Logbook : reconstruction symétrique, volumes athlétiques,
troisième passe de forme et nettoyage local des surfaces et contacts.
Conserver crédit, licence et mention des modifications à la redistribution.
