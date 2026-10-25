# Finition locale de l’aine — proposition M4A

Base : `d79692f`, conservée sans écrasement. Voir le [rapport](../../M4A_FINITION_AINE_LOCALISEE.md).

- `ecorche-finition-aine.blend` : ouvrir la scène **`23_FINITION_AINE_LOCALISEE`** pour la proposition ; **`22_ANATOMIE_DELTOIDES_P4`** conserve le mannequin antérieur complet.
- `ecorche-finition-aine.glb` : seule la proposition, matériau neutre, six zones de deltoïdes conservées. Aucun code d’intégration.
- `surface-neutre.npz` / `.json` : sommets, triangles et paramètres de la nouvelle surface.
- `finition.json` : référence, empreintes, périmètre et scène.
- `verification.json` : comparaison indépendante avec la référence et contrôle de la surface fermée.
- `selection-map.json` : correspondance des six IDs de deltoïdes ; `groin.neutral_surface` est exclue de la sélection d’entraînement.
- `export.json` : taille, compte géométrique et empreinte du GLB.
- `renders/before`, `renders/after` : sorties Blender originales et matrices de caméra.
- `renders/comparatif-central-serre.png`, `renders/comparatif-aine.png`, `renders/planche-neutre.png` : planches pour validation. Le détail central emploie un recadrage identique avant et après.
- `renders/verification.json` : empreintes des huit images et égalité des cadrages.

## Reproduction depuis la racine du dépôt

Python système avec NumPy ; Blender **4.3.2**. Aucun téléchargement ni outil payant. Le générateur crée une petite enveloppe neutre ; il ne lance aucune sculpture des maillages existants.

```bash
mkdir -p /tmp/m4a-aine
python tools/m4a-ecorche/aine_surface.py --output /tmp/m4a-aine/surface.npz
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 \
  --python tools/m4a-ecorche/aine_build.py -- \
  --baseline docs/m4a/ecorche-beatriz-anatomie-deltoides/ecorche-p4-p5-zones.blend \
  --surface /tmp/m4a-aine/surface.npz --output docs/m4a/ecorche-beatriz-finition-aine
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 \
  --python tools/m4a-ecorche/aine_export.py -- --asset docs/m4a/ecorche-beatriz-finition-aine
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 \
  --python tools/m4a-ecorche/aine_verify.py -- --asset docs/m4a/ecorche-beatriz-finition-aine
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 \
  --python tools/m4a-ecorche/aine_render.py -- --asset docs/m4a/ecorche-beatriz-finition-aine --mode before
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 \
  --python tools/m4a-ecorche/aine_render.py -- --asset docs/m4a/ecorche-beatriz-finition-aine --mode after
python tools/m4a-ecorche/aine_compose.py --asset docs/m4a/ecorche-beatriz-finition-aine
```

Ces commandes régénèrent la proposition dans son dossier dédié ; elles ne réécrivent pas le modèle validé. Le constructeur et l’exporteur conservent les objets historiques. L’export réutilise le codec GLB de `zones_deltoides_export.py` ; l’audit réutilise uniquement les fonctions de lecture et d’empreinte des contrôles précédents.

Corps : **Beatriz Gomez Santamaria — Ecorche - Anatomy study**, [Sketchfab](https://sketchfab.com/3d-models/ecorche-anatomy-study-e402d3d541eb4b199c57d5410f5d3c57), **CC BY 4.0**. Adaptations historiques Logbook et nouvelle surface locale de présentation. Tête / yeux : **Dan Ulrich / Blender Studio, Human Base Meshes v1.4.1**, **CC0** ; [licence conservée](../ecorche-beatriz-passe5/HEAD_SOURCE_LICENSE.md).
