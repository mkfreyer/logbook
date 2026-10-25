# Aine — raccords fondus, proposition pour validation

Base `cf5569b` préservée intégralement. [Rapport et planches](../../M4A_AINE_RACCORDS_FONDUS.md).

## Fichiers

- `ecorche-aine-fondue.blend` : proposition dans **`24_AINE_RACCORDS_FONDUS`** ; scènes précédentes conservées.
- `ecorche-aine-fondue.glb` : proposition seule, matériau neutre ; six zones de deltoïdes conservées.
- `surface-fondue.npz` : nouvelle géométrie, normales, indices des bords et poids de raccord.
- `finition.json` : paramètres de construction, référence et empreintes.
- `verification.json` : 298 objets conservés, contacts, ouverture basse et GLB.
- `selection-map.json` : six IDs et primitives ; surface de l’aine exclue des muscles d’entraînement.
- `export.json` : compte géométrique, taille et empreinte du GLB.
- `renders/before` : quatre rendus Blender de `cf5569b` réutilisés et vérifiés.
- `renders/after` : cinq nouveaux rendus Blender, dont les pieds inchangés.
- `renders/*.png` : quatre planches de comparaison, dont le rapprochement avec les pieds.
- `renders/verification.json` : cadrages appariés et empreintes des neuf images.

La surface de présentation regroupe les plages de raccord utiles, avec des frontières ouvertes volontairement enfouies dans les voisins inchangés. Le nombre de composantes figure dans le contrôle automatique. Aucune soudure ou simplification globale des muscles n’est réalisée. Les coordonnées du contrôle des contacts figurent dans le rapport automatique.

## Reproduction depuis la racine du dépôt

Blender **4.3.2**, Python système avec NumPy/SciPy, **scikit-image 0.26.0** et `lazy-loader`. Les outils Python supplémentaires sont gratuits et installés uniquement dans un dossier temporaire, **sans dépendance ni changement applicatif**.

```bash
mkdir -p /tmp/m4a-aine-fondue
python -m pip install --no-deps --target /tmp/m4a-aine-fondue/python scikit-image==0.26.0 lazy-loader
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 \
  --python tools/m4a-ecorche/aine_fondue_fields.py -- \
  --baseline docs/m4a/ecorche-beatriz-finition-aine/ecorche-finition-aine.blend \
  --work /tmp/m4a-aine-fondue
PYTHONPATH=/tmp/m4a-aine-fondue/python python tools/m4a-ecorche/aine_fondue_surface.py --work /tmp/m4a-aine-fondue
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 \
  --python tools/m4a-ecorche/aine_fondue_build.py -- \
  --baseline docs/m4a/ecorche-beatriz-finition-aine/ecorche-finition-aine.blend \
  --work /tmp/m4a-aine-fondue --output docs/m4a/ecorche-beatriz-aine-fondue
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 \
  --python tools/m4a-ecorche/aine_fondue_export.py -- --asset docs/m4a/ecorche-beatriz-aine-fondue
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 \
  --python tools/m4a-ecorche/aine_fondue_verify.py -- --asset docs/m4a/ecorche-beatriz-aine-fondue
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 \
  --python tools/m4a-ecorche/aine_fondue_render.py -- --asset docs/m4a/ecorche-beatriz-aine-fondue --mode before
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 \
  --python tools/m4a-ecorche/aine_fondue_render.py -- --asset docs/m4a/ecorche-beatriz-aine-fondue --mode after \
  --views aine-face aine-trois-quarts face trois-quarts pieds
python tools/m4a-ecorche/aine_fondue_compose.py --asset docs/m4a/ecorche-beatriz-aine-fondue
```

La reproduction peut régénérer les quatre vues avant ; la livraison réutilise les images existantes avec leurs empreintes. Les fichiers de champs intermédiaires restent dans `/tmp/m4a-aine-fondue`. Le maillage de référence n’est jamais écrasé. Les indices des sommets de couture UV/normales à coordonnées identiques sont regroupés **uniquement pour contrôler la fermeture des références de calcul**, sans déplacement ni modification des objets Blender d’origine.

Corps : **Beatriz Gomez Santamaria — Ecorche - Anatomy study**, [Sketchfab](https://sketchfab.com/3d-models/ecorche-anatomy-study-e402d3d541eb4b199c57d5410f5d3c57), **CC BY 4.0**. Adaptations historiques Logbook et nouveaux raccords locaux. Tête / yeux : **Dan Ulrich / Blender Studio, Human Base Meshes v1.4.1**, **CC0**, [licence](../ecorche-beatriz-passe5/HEAD_SOURCE_LICENSE.md).
