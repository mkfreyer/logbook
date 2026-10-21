# Écorché — passe 6 : reprise ciblée des deltoïdes

[Rapport et comparatifs P4 / P5 / P6](../../M4A_ECORCHE_PASSE6_DELTOIDES.md).

La base complète reste la passe 5. **Seuls les deux deltoïdes changent** ;
la tête, les yeux, toute la gorge et toutes les autres pièces sont conservés
à l’identique. Les fichiers précédents restent intacts.

Le master conserve les scènes historiques et ajoute :

- `13_TEMOIN_PASSE4` : géométrie exacte de la passe 4.
- `14_TEMOIN_PASSE5` : géométrie exacte de la passe 5.
- `15_PASSE6_NEUTRE` : proposition actuelle, avec les deux deltoïdes reconstruits.

Les deltoïdes gardent leurs identifiants et trois groupes de poids d’auteur.
Leur topologie est reconstruite ; les anciens indices de triangles ne sont donc
pas transférables directement. Les scènes témoins servent de référence exacte,
plutôt qu’une shape key entre deux topologies différentes. Aucune segmentation
interactive définitive n’est produite.

## Sources utiles

`shoulder-surface.npz` contient les données de départ et les champs de courbure
avant reconstruction Blender ; son JSON décrit les paramètres. Le master et le
GLB contiennent les surfaces finales après raccord et reconstruction locale.

## Reproduction

Blender 4.3.2 / NumPy ; Python système avec NumPy, SciPy et Pillow.
Depuis la racine du dépôt, utiliser une nouvelle sortie voisine des passes
précédentes pour préserver les fichiers livrés :

```bash
ASSET=docs/m4a/ecorche-beatriz-passe6-reproduction
WORK=/workspace/work/ecorche-passe6-reproduction
mkdir -p "$WORK"
export XDG_CONFIG_HOME="$WORK/blender-config"
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/passe6_probe.py -- --baseline docs/m4a/ecorche-beatriz-passe5/ecorche-passe5.blend --output "$WORK"
python tools/m4a-ecorche/passe6_surface.py --baseline "$WORK/shoulder-baselines.npz" --output "$WORK/shoulder-surface.npz"
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/passe6_build.py -- --baseline docs/m4a/ecorche-beatriz-passe5/ecorche-passe5.blend --surface "$WORK/shoulder-surface.npz" --output "$ASSET"
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/passe6_render.py -- --asset "$ASSET"
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/passe6_export.py -- --asset "$ASSET"
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/passe6_verify.py -- --asset "$ASSET"
python tools/m4a-ecorche/passe6_compose.py --asset "$ASSET"
```

On peut aussi utiliser directement le NPZ et le JSON livrés avec `passe6_build.py`.
Les captures antérieures disponibles sont recopiées à l’identique. La vue P4
« trois quarts arrière » vient de `../ecorche-beatriz-passe5/renders/avant-epaule-arriere.png`,
qui représentait déjà exactement la passe 4. Les empreintes et chemins figurent
dans les métadonnées des rendus.

## Attribution

Corps : **Ecorche - Anatomy study — Beatriz Gomez Santamaria**,
[source](https://sketchfab.com/3d-models/ecorche-anatomy-study-e402d3d541eb4b199c57d5410f5d3c57),
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) selon les métadonnées
du GLB fourni. Adaptations Logbook : reconstruction symétrique et athlétique,
passes de finition ; cette passe reconstruit localement les deux deltoïdes,
réduit leur gabarit et adoucit le raccord pectoral/deltoïde.

Tête et yeux conservés : **Dan Ulrich / Blender Studio — CC0**,
[provenance conservée dans la passe 5](../ecorche-beatriz-passe5/HEAD_SOURCE_LICENSE.md).
Conserver attribution, licences et mention des modifications à la redistribution.
