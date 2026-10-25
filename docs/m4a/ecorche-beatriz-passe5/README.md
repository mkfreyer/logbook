# Écorché — cinquième passe ciblée

[Rapport et comparatifs](../../M4A_ECORCHE_PASSE5_TETE_DELTOIDES.md).

La passe 4 et tous ses fichiers restent intacts. Le nouveau master conserve
toutes les anciennes scènes, plus `11_AVANT_PASSE5` (passe 4 exacte) et
`12_PASSE5_NEUTRE`. La tête précédente reste donc accessible.

Les deltoïdes ont les clés `AVANT_PASSE5` et
`DEFINITION_TROIS_FAISCEAUX_PASSE5`, ainsi que trois groupes de poids d’auteur.
Leur topologie est conservée. La surface tête/gorge conserve la géométrie de la
gorge sous Z = 1,570 m, puis reçoit la tête humaine et un raccord local.
Le corps et les autres pièces cervicales restent identiques. Les deux yeux sont
des objets de présentation non musculaires ; le GLB applique les shape keys et
conserve ces rôles dans ses extras.

## Reproduction

Blender 4.3.2 / NumPy ; Python avec Pillow pour les planches. Depuis la racine
du dépôt, choisir une sortie sœur des passes précédentes pour les contrôles
et la réutilisation des captures « avant ». Les fichiers livrés ne doivent pas
être écrasés :

```bash
ASSET=docs/m4a/ecorche-beatriz-passe5-reproduction
WORK=/workspace/work/ecorche-passe5-reproduction
mkdir -p "$WORK"
export XDG_CONFIG_HOME="$WORK/blender-config"
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/passe5_build.py -- --baseline docs/m4a/ecorche-beatriz-passe4/ecorche-passe4.blend --donor docs/m4a/ecorche-beatriz-passe5/head-donor.npz --output "$ASSET"
cp docs/m4a/ecorche-beatriz-passe5/head-donor.npz "$ASSET/"
cp docs/m4a/ecorche-beatriz-passe5/head-donor.json "$ASSET/"
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/passe5_render.py -- --asset "$ASSET"
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/passe5_export.py -- --asset "$ASSET"
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/passe5_verify.py -- --asset "$ASSET"
python tools/m4a-ecorche/passe5_compose.py --asset "$ASSET"
```

Pour réextraire les données depuis le bundle officiel décompressé, au lieu
d’utiliser le NPZ livré :

```bash
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/passe5_head.py -- --bundle /chemin/human_base_meshes_bundle.blend --output "$WORK/donor"
```

`passe5_build.py` utilise aussi les repères d’auteur de
`../ecorche-beatriz-passe3/passe3.json`, conservés dans le dépôt.

## Licences

Corps : **Beatriz Gomez Santamaria — CC BY 4.0** ; nouvelle tête et yeux :
**Dan Ulrich / Blender Studio — CC0**. Sources, déclarations et modifications :
[HEAD_SOURCE_LICENSE.md](HEAD_SOURCE_LICENSE.md). Attribution du corps conservée
dans le GLB, le rapport et les scènes historiques.
