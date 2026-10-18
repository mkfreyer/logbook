# Sauvegarde M4A écorché — 18 octobre 2026

Recherche hors application, PR #11 en brouillon, arrêt pour choix utilisateur.
Les sauvegardes/études B, B+, V2 et l’audit initial restent conservés.

[Archive des scènes sélectionnées](m4a-ecorche-2026-10-18.tar.xz) ·
[Manifeste tailles/SHA-256](manifest.json) ·
[Comparatif et limites](../../../M4A_ECORCHE.md) ·
[Licences/attribution](../ATTRIBUTION.md)

L’archive contient les **trois vrais fichiers Blender musculaires**, leurs
inventaires, contrôles géométriques, origines, sources épinglées, notices et
scripts de reproduction. Aucun squelette, organe, rein/oreille interne, add-on
tiers ou runtime Logbook. Les données d’atlas inutilisées sont purgées ; les
empreintes des positions/index/polygones sélectionnés restent identiques après
sauvegarde et rechargement. `checkpoint-origin.json` documente la différence
entre le SHA du fichier de préparation utilisé pour les rendus et celui du
fichier sauvegardé après purge ; **la géométrie sélectionnée est identique**.
Les PNG et leurs métadonnées sont directement versionnés dans le dossier parent.

Les assets dérivés restent sous CC BY-SA 4.0, avec les attributions fournies.
Le code de l’app n’est pas relicencié. Pour Z-Anatomy, conserver l’examen de
provenance du sous-ensemble avant une distribution commerciale ; la sauvegarde
sélectionnée ne vaut pas autorisation de distribuer l’atlas intégral.

## Restaurer sans réseau et sans écraser

Depuis la racine du dépôt, Python 3.11+ :

```sh
python3 tools/m4a/restore_ecorche_checkpoint.py \
  --destination /workspace/work/m4a-ecorche-restored
python3 tools/m4a/restore_ecorche_checkpoint.py \
  --destination /workspace/work/m4a-ecorche-restored --verify-only
```

Le script vérifie l’archive puis chaque fichier extrait dans un dossier
temporaire ; il refuse les liens et membres imprévus, les chemins dangereux,
les tailles/empreintes différentes et toute destination déjà existante.
Il ne lance ni application, ni SQLite, ni installation de dépendances.

## Recalculer les images depuis la sauvegarde

Avec Blender 4.3.2, depuis le dépôt :

```sh
for candidate in bodyparts3d z-anatomy ecorche; do
  blender --background --factory-startup --disable-autoexec --threads 2 \
    --python tools/m4a/render_ecorche.py -- \
    --prepared "/workspace/work/m4a-ecorche-restored/prepared/$candidate" \
    --output "/workspace/work/m4a-ecorche-regenerated/$candidate"
done
python3 tools/m4a/make_ecorche_sheets.py \
  --root /workspace/work/m4a-ecorche-regenerated
```

L’archive contient aussi les copies exactes des outils utilisés et un jeu minimal
de métadonnées sous `tools/` et `docs/`. Le module Pillow de Python sert uniquement
à la mise en page ; Blender calcule les rendus 3D. Ni code d’atlas ni add-on exécuté.

## Repartir des sources publiques épinglées

Ces opérations réseau utilisent le proxy et les CA normaux de l’environnement.
Les téléchargements ont taille et SHA attendus ; aucune mise à jour implicite.

```sh
python3 tools/m4a/acquire_ecorche.py \
  --output-dir /workspace/work/m4a-ecorche/sources

blender --background --factory-startup --disable-autoexec \
  --python tools/m4a/prepare_ecorche.py -- --candidate bodyparts3d \
  --source /workspace/work/m4a-ecorche/sources/bodyparts3d/obj \
  --selection docs/m4a/bodyparts3d/selection-candidate.json \
  --output /workspace/work/m4a-ecorche/prepared/bodyparts3d

blender --background --factory-startup --disable-autoexec \
  --python tools/m4a/prepare_ecorche.py -- --candidate z-anatomy \
  --source /workspace/work/m4a-ecorche/sources/Z-Anatomy--Models-of-human-anatomy/extracted/Z-Anatomy/Startup.blend \
  --output /workspace/work/m4a-ecorche/prepared/z-anatomy

blender --background --factory-startup --disable-autoexec \
  --python tools/m4a/prepare_ecorche.py -- --candidate ecorche \
  --source /workspace/work/m4a-ecorche/sources/Charleeh--ecorche/model/ecorche.glb \
  --output /workspace/work/m4a-ecorche/prepared/ecorche
```

Le téléchargement des atlas complets reste hors application. Les scènes
sélectionnées n’utilisent que les objets explicités dans les inventaires.
Pour le contrôle numérique, utiliser `check_ecorche_geometry.py --prepared …
--output …`. Ces contrôles ne certifient ni toute l’anatomie ni la fluidité iPhone.
