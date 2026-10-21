# Six zones du deltoïde — frontières traversant les triangles

[Rapport](../../M4A_DELTOIDES_FRONTIERES_CONTINUES.md) · [Comparatifs](renders/) · [Contrôles](verification.json).

Base : `fb68f5ee9ab3b47f3ae046cd7a1ce11129a98857`, géométrie P4 + tête P5 de `0ab3d83`. Aucune ancienne sculpture des creux réutilisée.

## Contenu

- `ecorche-p4-p5-zones.blend` : scène `21_FRONTIERES_DELTOIDES_P4`, master mat neutre, 300 objets.
- `ecorche-p4-p5-zones.glb` : neutre, six matériaux indépendants et IDs stables.
- `ecorche-p4-p5-zones-controle.glb` : même géométrie, antérieur rouge / moyen bleu / postérieur vert.
- `zones.json` : paramètres, références, répartition des nouveaux indices de faces.
- `selection-map.json` : ID stable ↔ nœud / primitive / matériau / indices du nouveau master.
- `provenance-surface.npz` : source de chaque nouveau point/triangle et coordonnées barycentriques ; champs de répartition avant/après régularisation. Préfixes `right_` et `left_`, `parent` = face d'origine de chaque triangle enfant, `bary` = trois coordonnées barycentriques pour chacun de ses coins. Les `f` référencent les sommets partagés du nouveau maillage.
- `verification.json` : identité des sommets d'origine et des 298 autres objets, couverture, absence de chevauchement, maillages fermés, normales et exports.
- `export.json` : comptes et empreintes des GLB.
- `renders/comparisons.json` : caméras avant/après, origine des images, écarts neutres et empreintes des planches.

**Topologie locale modifiée, surface P4 préservée.** Les sommets existants gardent exactement leurs coordonnées évaluées ; les nouveaux points sont barycentriques sur les faces d'origine, à la précision float32 près. Les clés de forme des deux deltoïdes sont figées à leur état P4 visible dans cette copie uniquement. Les originaux sont conservés dans le dossier précédent.

Les six identifiants `deltoid.{left|right}.{anterior|lateral|posterior}` restent portés par les matériaux et primitives GLB. Recolorer un matériau agit sur une seule zone. Restaurer les six couleurs Principled neutres conserve la répartition et ses IDs. Aucune interface tactile n'est programmée.

## Reproduction

Blender 4.3.2 ; Python système avec NumPy, SciPy et Pillow, déjà disponibles dans l'environnement. Aucun service payant, aucune dépendance ajoutée à Logbook. Depuis la racine du dépôt, utiliser un dossier temporaire de travail, par exemple `/tmp/logbook-frontieres` :

```bash
mkdir -p /tmp/logbook-frontieres

blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 \
  --python tools/m4a-ecorche/frontieres_deltoides_build.py -- \
  --baseline docs/m4a/ecorche-beatriz-zones-deltoides/ecorche-p4-p5-zones.blend \
  --snapshot /tmp/logbook-frontieres/source.npz

python tools/m4a-ecorche/frontieres_deltoides_prepare.py \
  --source /tmp/logbook-frontieres/source.npz \
  --zones docs/m4a/ecorche-beatriz-zones-deltoides/zones.json \
  --output /tmp/logbook-frontieres/cut.npz

blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 \
  --python tools/m4a-ecorche/frontieres_deltoides_build.py -- \
  --baseline docs/m4a/ecorche-beatriz-zones-deltoides/ecorche-p4-p5-zones.blend \
  --prepared /tmp/logbook-frontieres/cut.npz \
  --output docs/m4a/ecorche-beatriz-frontieres-deltoides

blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 \
  --python tools/m4a-ecorche/frontieres_deltoides_export.py -- \
  --asset docs/m4a/ecorche-beatriz-frontieres-deltoides

blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 \
  --python tools/m4a-ecorche/frontieres_deltoides_verify.py -- \
  --baseline docs/m4a/ecorche-beatriz-zones-deltoides/ecorche-p4-p5-zones.blend \
  --asset docs/m4a/ecorche-beatriz-frontieres-deltoides

blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 \
  --python tools/m4a-ecorche/frontieres_deltoides_render.py -- \
  --asset docs/m4a/ecorche-beatriz-frontieres-deltoides --mode neutral \
  --output docs/m4a/ecorche-beatriz-frontieres-deltoides/renders/neutral \
  --views epaule-profil epaule-droite epaule-face-droite epaule-face-gauche

blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 \
  --python tools/m4a-ecorche/frontieres_deltoides_render.py -- \
  --asset docs/m4a/ecorche-beatriz-frontieres-deltoides --mode zones \
  --output docs/m4a/ecorche-beatriz-frontieres-deltoides/renders/after \
  --views epaule-profil epaule-droite epaule-gauche epaules-face epaules-dos epaule-arriere epaule-face-droite epaule-face-gauche

blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 \
  --python tools/m4a-ecorche/frontieres_deltoides_render.py -- \
  --asset docs/m4a/ecorche-beatriz-zones-deltoides --mode zones \
  --output docs/m4a/ecorche-beatriz-frontieres-deltoides/renders/before \
  --views epaule-face-droite epaule-face-gauche

python tools/m4a-ecorche/frontieres_deltoides_compose.py \
  --asset docs/m4a/ecorche-beatriz-frontieres-deltoides \
  --baseline-asset docs/m4a/ecorche-beatriz-zones-deltoides
```

L'exporteur réutilise `zones_deltoides_export.py` pour les six matériaux et complète les métadonnées de subdivision. Le vérificateur réutilise les fonctions indépendantes de lecture/fingerprint des audits précédents. Les scripts antérieurs restent inchangés. Le compositeur utilise les anciens rendus colorés pour les caméras existantes et les deux nouveaux rendus « avant » pour les caméras frontales rapprochées ; il ne repeint pas le mannequin.

Les frontières sont des polylignes de surface interpolées, pas des courbes infiniment lisses. Le neutre est visuellement conservé aux angles testés, avec de très faibles écarts de pixels documentés ; ne pas annoncer une identité pixel par pixel. Aucun FPS mobile mesuré.

## Attribution et arrêt

Corps : **Ecorche - Anatomy study — Beatriz Gomez Santamaria**, [Sketchfab](https://sketchfab.com/3d-models/ecorche-anatomy-study-e402d3d541eb4b199c57d5410f5d3c57), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Adaptation Logbook : travaux P4/P5 antérieurs, six zones de surface, puis découpage local barycentrique des frontières dans cette livraison.

Tête/yeux : **Dan Ulrich / Blender Studio, Human Base Meshes v1.4.1**, CC0 ; [provenance](../ecorche-beatriz-passe5/HEAD_SOURCE_LICENSE.md).

Attendre la validation visuelle. Aucune intégration, modification SQLite, M4B ou fusion ; PR #12 en brouillon.
