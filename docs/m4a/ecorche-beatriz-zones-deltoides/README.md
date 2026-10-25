# Deltoïdes P4 — six zones, aucune sculpture

Voir le [rapport de validation](../../M4A_DELTOIDES_P4_SIX_ZONES.md) et les [planches](renders/).

## Fichiers

| Fichier | Usage |
| --- | --- |
| `ecorche-p4-p5-zones.blend` | Master neutre ; scène `20_ZONES_DELTOIDES_P4`, 300 objets musculaires/de présentation. |
| `ecorche-p4-p5-zones.glb` | Export neutre, six matériaux de sélection indépendants. |
| `ecorche-p4-p5-zones-controle.glb` | Même géométrie, antérieur rouge / latéral bleu / postérieur vert. |
| `zones.json` | Méthode, repères et indices de faces Blender par zone. |
| `selection-map.json` | Correspondance stable ID ↔ nœud / primitive / matériau GLB. |
| `verification.json` | Comparaison indépendante avec `0ab3d83`, couverture, connexité, couleurs et réimports. |
| `export.json` | Poids, comptes et SHA-256 des deux exports. |
| `renders/neutral-provenance.json` | Vues neutres recalculées et vues P4 approuvées réutilisées. |
| `renders/zones/metadata.json` | Caméras et empreintes des rendus de contrôle. |

Les anciens groupes `DELT_*` restent des aides de sculpture, inchangées. La sélection proposée utilise **les indices de matériaux des faces**, pas ces groupes.

Dans Blender, sélectionner `P4P5__deltoid.left` ou `P4P5__deltoid.right`, puis un de ses trois matériaux. Chaque matériau porte le même nom que son ID. Modifier sa couleur Principled colore uniquement cette portion. Les six matériaux ont au départ les mêmes paramètres que `PASSE3_MAT_NEUTRE` ; restaurer ces paramètres permet de revenir au neutre sans perdre les six identifiants.

Les frontières colorées suivent les triangles existants et restent légèrement crénelées en gros plan. Aucun UV, sommet, triangle, relief, clé de forme ou normale n'est retouché. Les limites anatomiques proposées attendent une validation visuelle.

## Reproduire

Depuis la racine du dépôt, avec Blender 4.3.2, Python + NumPy + Pillow pour la composition. Aucun téléchargement ni service payant. Les commandes écrivent uniquement dans ce dossier d'assets ; elles ne modifient pas le fichier de référence.

```bash
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 \
  --python tools/m4a-ecorche/zones_deltoides_build.py -- \
  --baseline docs/m4a/ecorche-beatriz-combinaison-p4-p5/ecorche-p4-p5.blend \
  --output docs/m4a/ecorche-beatriz-zones-deltoides

blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 \
  --python tools/m4a-ecorche/zones_deltoides_export.py -- \
  --asset docs/m4a/ecorche-beatriz-zones-deltoides

blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 \
  --python tools/m4a-ecorche/zones_deltoides_verify.py -- \
  --baseline docs/m4a/ecorche-beatriz-combinaison-p4-p5/ecorche-p4-p5.blend \
  --asset docs/m4a/ecorche-beatriz-zones-deltoides

blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 \
  --python tools/m4a-ecorche/zones_deltoides_render.py -- \
  --asset docs/m4a/ecorche-beatriz-zones-deltoides --mode zones

blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 \
  --python tools/m4a-ecorche/zones_deltoides_render.py -- \
  --asset docs/m4a/ecorche-beatriz-zones-deltoides --mode neutral \
  --views epaule-droite epaule-profil

python tools/m4a-ecorche/zones_deltoides_compose.py \
  --asset docs/m4a/ecorche-beatriz-zones-deltoides \
  --baseline-asset docs/m4a/ecorche-beatriz-combinaison-p4-p5
```

La coloration des rendus est appliquée en mémoire : le master Blender reste enregistré en neutre. Pour recalculer toutes les vues neutres plutôt que réutiliser les huit vues identiques approuvées, omettre `--views` dans la commande `--mode neutral`.

## Attribution

Corps : **Ecorche - Anatomy study**, **Beatriz Gomez Santamaria**, [Sketchfab](https://sketchfab.com/3d-models/ecorche-anatomy-study-e402d3d541eb4b199c57d5410f5d3c57), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Adaptation Logbook : corps symétrisé/athlétique, gorge reconstruite et combinaison P4/P5 antérieures ; dans cette livraison, affectation de matériaux uniquement sur les deux deltoïdes.

Tête et yeux : **Dan Ulrich / Blender Studio, Human Base Meshes v1.4.1**, CC0 ; [provenance](../ecorche-beatriz-passe5/HEAD_SOURCE_LICENSE.md).

La référence `0ab3d83` et toutes les propositions historiques sont conservées. Aucune intégration Logbook, modification SQLite, M4B ou fusion. Attendre la validation des zones.
