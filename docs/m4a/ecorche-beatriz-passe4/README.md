# Écorché — quatrième passe de finition

[Rapport, comparatifs et limites](../../M4A_ECORCHE_PASSE4_FINITION.md).

La troisième passe est conservée à l’identique dans `../ecorche-beatriz-passe3/`.
Le nouveau master contient toutes les anciennes scènes, plus
`09_AVANT_PASSE4` (copie exacte de la passe 3) et `10_PASSE4_NEUTRE`.
La tête disséquée reste disponible dans les scènes historiques et la scène 09.
Seule la proposition 10 lui substitue une enveloppe de présentation simplifiée.
Le matériau est exactement `PASSE3_MAT_NEUTRE`, partagé avant/après.

Les deux deltoïdes conservent leur topologie et leurs trois groupes de poids
d’auteur. Les clés `AVANT_PASSE4` et `FINITION_ANTERIEURE_PASSE4` rendent leur
retouche réversible. Le GLB applique cette retouche et garde des objets séparés.
La nouvelle surface tête/gorge est signalée comme non musculaire dans ses extras.

## Reproduction

Blender 4.3.2 et son NumPy ; Python système avec NumPy, SciPy et Pillow.
Depuis la racine du dépôt, choisir un autre dossier `ASSET` pour préserver
les fichiers livrés :

```bash
ASSET=/workspace/work/ecorche-passe4-reproduction/asset
WORK=/workspace/work/ecorche-passe4-reproduction/work
mkdir -p "$WORK"
export XDG_CONFIG_HOME="$WORK/blender-config"
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/passe4_prepare.py -- --baseline docs/m4a/ecorche-beatriz-passe3/ecorche-passe3.blend --work "$WORK"
python tools/m4a-ecorche/passe4_surface.py --work "$WORK" --output "$WORK/head-throat.npz"
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/passe4_build.py -- --baseline docs/m4a/ecorche-beatriz-passe3/ecorche-passe3.blend --surface "$WORK/head-throat.npz" --output "$ASSET"
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/passe4_render.py -- --asset "$ASSET"
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/passe4_export.py -- --asset "$ASSET"
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/passe4_verify.py -- --asset "$ASSET"
python tools/m4a-ecorche/passe4_compose.py --asset "$ASSET"
```

Si le dossier de la passe 3 n’est pas voisin du dossier de reproduction, le
rendu recalcule les vues « avant » au lieu de recopier les six captures existantes.
Pour le vérificateur, placer le dossier reproduit à côté d’une copie intacte
de `ecorche-beatriz-passe3`, car il contrôle aussi son empreinte.

## Attribution

**Ecorche - Anatomy study — Beatriz Gomez Santamaria**
([source](https://sketchfab.com/3d-models/ecorche-anatomy-study-e402d3d541eb4b199c57d5410f5d3c57),
[autrice](https://sketchfab.com/BeatrizGomez)),
**[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)** selon les métadonnées
du GLB fourni. Adaptation Logbook : reconstruction symétrique, volumes
athlétiques, passes locales de finition ; quatrième passe sur deltoïdes
antérieurs et reconstruction d’une surface tête/gorge neutre.
Conserver crédit, licence et mention des modifications à la redistribution.
