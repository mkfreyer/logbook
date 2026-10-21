# Deltoïdes P4 — répartition en éventail anatomique proposée

[Rapport](../../M4A_DELTOIDES_REPARTITION_ANATOMIQUE.md) · [Rendus](renders/) · [Contrôles](verification.json).

Base exacte : `990201f214c91272a5274a53c28e049670128064`, master SHA-256 `34af46851680f8edce0d55b138603caa6df0d2eb0253d587499d3be866d70c91`. Aucune ancienne sculpture des creux utilisée.

## Contenu

- `ecorche-p4-p5-zones.blend` : master neutre, scène `22_ANATOMIE_DELTOIDES_P4`.
- `ecorche-p4-p5-zones.glb` et `ecorche-p4-p5-zones-controle.glb` : mêmes buffers géométriques ; six matériaux indépendants, neutres ou rouge/bleu/vert.
- `zones.json` : repère anatomique, profils d'ouverture et six repères de surface approximatifs ; correspondance des nouveaux indices de faces.
- `selection-map.json` : six IDs stables ↔ primitives / matériaux / faces du nouveau master.
- `provenance-surface.npz` : `parent` et `bary` pour chaque triangle enfant, plus provenance de chaque sommet, coordonnées et labels ; préfixes `right_` et `left_`. Les parents référencent les faces de `990201f`.
- `verification.json` : audit de la surface de `990201f`, puis comparaison directe à P4 original par composition avec la provenance du dossier précédent.
- `export.json` : comptes, poids et empreintes des exports.
- `renders/comparisons.json` : caméras avant/après, provenance des images, comparaison neutre à `990201f` et directement à P4 original.

La répartition antérieure / latérale / postérieure suit un repère huméral 3D avec élargissement proximal du dôme latéral et convergence distale. Les champs sont continus, les frontières traversent les triangles et les coordonnées de la surface ne sont pas lissées. Les limites restent une proposition pour validation visuelle, avec repères approximatifs.

L'axe interne de construction n'est pas une nouvelle surface ou une attache à exporter. Seules les zones et leur découpage sont conservés. Les six IDs `deltoid.{left|right}.{anterior|lateral|posterior}` restent dans les noms et métadonnées des matériaux/primitives. Pour recolorer une portion, modifier son matériau ; restaurer les six couleurs Principled neutres garde tous les IDs indépendants.

## Reproduire

Blender 4.3.2 ; Python avec NumPy/SciPy/Pillow. Outils gratuits déjà présents, aucune dépendance ajoutée à Logbook. Depuis la racine du dépôt :

```bash
mkdir -p /tmp/logbook-anatomie

blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 \
  --python tools/m4a-ecorche/anatomie_deltoides_build.py -- \
  --baseline docs/m4a/ecorche-beatriz-frontieres-deltoides/ecorche-p4-p5-zones.blend \
  --snapshot /tmp/logbook-anatomie/source.npz

python tools/m4a-ecorche/anatomie_deltoides_prepare.py \
  --source /tmp/logbook-anatomie/source.npz \
  --zones docs/m4a/ecorche-beatriz-frontieres-deltoides/zones.json \
  --output /tmp/logbook-anatomie/cut.npz

blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 \
  --python tools/m4a-ecorche/anatomie_deltoides_build.py -- \
  --baseline docs/m4a/ecorche-beatriz-frontieres-deltoides/ecorche-p4-p5-zones.blend \
  --prepared /tmp/logbook-anatomie/cut.npz \
  --output docs/m4a/ecorche-beatriz-anatomie-deltoides

blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 \
  --python tools/m4a-ecorche/anatomie_deltoides_export.py -- \
  --asset docs/m4a/ecorche-beatriz-anatomie-deltoides

blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 \
  --python tools/m4a-ecorche/anatomie_deltoides_verify.py -- \
  --baseline docs/m4a/ecorche-beatriz-frontieres-deltoides/ecorche-p4-p5-zones.blend \
  --asset docs/m4a/ecorche-beatriz-anatomie-deltoides

blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 \
  --python tools/m4a-ecorche/frontieres_deltoides_render.py -- \
  --asset docs/m4a/ecorche-beatriz-anatomie-deltoides --mode neutral \
  --output docs/m4a/ecorche-beatriz-anatomie-deltoides/renders/neutral \
  --views epaule-profil epaule-droite epaule-face-droite epaule-face-gauche

blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 \
  --python tools/m4a-ecorche/frontieres_deltoides_render.py -- \
  --asset docs/m4a/ecorche-beatriz-anatomie-deltoides --mode zones \
  --output docs/m4a/ecorche-beatriz-anatomie-deltoides/renders/after \
  --views epaule-profil epaule-droite epaule-gauche epaules-face epaules-dos epaule-arriere epaule-face-droite epaule-face-gauche

python tools/m4a-ecorche/anatomie_deltoides_compose.py \
  --asset docs/m4a/ecorche-beatriz-anatomie-deltoides \
  --baseline-asset docs/m4a/ecorche-beatriz-frontieres-deltoides
```

Le découpage barycentrique, le transfert des attributs, l'export et l'audit géométrique réutilisent les outils antérieurs. L'audit commun conserve son seuil de normales par défaut à 0,001 ; le nouvel audit fixe explicitement 0,002 (~0,115°) pour l'encodage de cinq coins de triangles très fins. Tous les contrôles de surface et de coutures sont maintenus. Les données des livraisons précédentes ne sont pas réécrites.

Les planches reprennent les rendus colorés de `990201f` pour les comparatifs, sans les repeindre. Le neutre présente de faibles écarts d'interpolation documentés ; ne pas annoncer une identité pixel par pixel. Aucun FPS mobile mesuré.

## Attribution et arrêt

Corps : **Ecorche - Anatomy study — Beatriz Gomez Santamaria**, [Sketchfab](https://sketchfab.com/3d-models/ecorche-anatomy-study-e402d3d541eb4b199c57d5410f5d3c57), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Adaptation Logbook : travaux P4/P5 antérieurs, zones fonctionnelles et nouvelle répartition en éventail sur surface conservée.

Tête/yeux : **Dan Ulrich / Blender Studio, Human Base Meshes v1.4.1**, CC0 ; [provenance](../ecorche-beatriz-passe5/HEAD_SOURCE_LICENSE.md).

PR #12 en brouillon. Aucune intégration, modification SQLite, M4B ou fusion. Attendre la validation du placement des zones.
