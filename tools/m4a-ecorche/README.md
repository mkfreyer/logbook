# Reconstruction et retouche de l’écorché fourni

Scripts hors application. Python système : NumPy, SciPy et Pillow.
Blender utilisé : **4.3.2**, rendu Cycles CPU. Aucun service ni asset payant.

Depuis la racine du dépôt, avec `ASSET` et `WORK` choisis dans un répertoire
inscriptible :

```bash
ASSET=docs/m4a/ecorche-beatriz-retouche
WORK=/workspace/work/ecorche-retouche-reproduction
mkdir -p "$WORK"
python tools/m4a-ecorche/prepare_parts.py --source "$ASSET/source.glb" --output "$WORK/prepared"
XDG_CONFIG_HOME="$WORK/blender-config" blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/build_asset.py -- --prepared "$WORK/prepared" --output "$ASSET"
XDG_CONFIG_HOME="$WORK/blender-config" blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/render_asset.py -- --asset "$ASSET"
XDG_CONFIG_HOME="$WORK/blender-config" blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/export_asset.py -- --asset "$ASSET"
XDG_CONFIG_HOME="$WORK/blender-config" blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/verify_asset.py -- --asset "$ASSET"
python tools/m4a-ecorche/compose_comparisons.py --asset "$ASSET"
```

Ces commandes remplacent les **sorties dérivées** dans `ASSET` : utiliser une
copie de ce dossier pour conserver les fichiers livrés. Le GLB source n’est
jamais écrit. Exécuter les étapes dans cet ordre : le rendu enregistre le master
avec ses caméras, puis la vérification contrôle ses empreintes finales.

`source_parts.py` vérifie la source par SHA-256 et retrouve les composants
géométriques aux coutures de buffers, sans inventer une nomenclature anatomique.
`build_asset.py` conserve séparément l’original, la reconstruction et les volumes
renforcés. Le bouton de shape key `ATHLETIQUE` permet de comparer les deux derniers
états sur les pièces bilatérales ; le fichier exporté applique cette valeur.

`verify_asset.py` contrôle la symétrie, la cohérence aux coutures source, les
orientations de triangles, la correspondance des surfaces du GLB effectivement
sérialisé et les empreintes des 12 rendus. Les signatures de surface sont comparées
à une précision d’un micromètre. Il distingue les suppressions de faces dupliquées
par l’exporteur d’une perte de surface visible. Les sondes médianes renseignent
la couverture ; elles ne constituent ni un test complet d’intersections ni une
certification des insertions musculaires.
