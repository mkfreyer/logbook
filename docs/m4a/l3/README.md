# L3 — sources et reproduction

[Analyse visuelle](../../M4A_L3.md) · [Manifeste](manifest.json) ·
[Validation](validation.json) · [Scènes de revue](review-validation.json).

| Contenu | L2, géométrie historique | L3, nouvelle exploration |
| --- | --- | --- |
| Source géométrique | [BLEND historique inchangé](../original/defined/logbook-original.blend) | [BLEND](l3/logbook-original.blend) |
| Studio prêt pour F12 | [BLEND](l2/scene-review.blend) | [BLEND](l3/scene-review.blend) |
| Profils / inventaire | [JSON, copie de l’historique](l2/construction.json) | [JSON](l3/construction.json) |
| Géométrie contrôlée | [JSON historique](../original/defined/geometry-check.json) | [JSON](l3/geometry-check.json) |
| Paramètres et empreintes des images | [JSON](l2/render-metadata.json) | [JSON](l3/render-metadata.json) |

Les cinq PNG par modèle sont `front`, `three-quarter`, `back`, `side` et
`selection`. Les sept planches sont des assemblages de ces PNG, sans peinture
ou ajout de relief. Les fichiers de construction sans studio et les scènes
avec studio contiennent la même géométrie, les mêmes normales personnalisées
et les mêmes attributs de partition (voir contrôle des scènes).

## Origine et portée

Les profils L3 et les reliefs sont écrits pour cette exploration Logbook : aucun
mesh, texture, scan, atlas, donnée anatomique ou addon externe n’est lu par le
générateur. Les méthodes de loft, union voxel, réduction, découpage des zones
et transfert des normales reprennent le générateur M4A au commit `f3bfda6`,
sans modifier ce générateur historique. Les profils du corps, les déformations
musculaires et les limites de sélection L3 sont définis dans le nouveau script.
Ce n’est ni une acquisition anatomique, ni une validation médicale.

L3 : **89 672 triangles affichés, 49 708 sommets affichés** en comptant les
frontières communes dupliquées dans les objets. Enveloppe de construction :
44 838 sommets, hauteur observée 1,787 m (sommet vers 1,80 m ; dessous du pied
vers 0,013 m). L2 : 81 036 triangles ; évolution L3 **+10,7 %** pour les nouveaux
reliefs, sans texture ni subdivision au rendu.

22 régions sélectionnables et un support sont visibles. La construction
`LB.Construction.closed-surface` reste cachée. Les objets affichés sont des
sous-ensembles disjoints de ses faces, **pas une deuxième couche superposée**.
Les frontières sont ouvertes sur chaque sous-objet, fermées sur leur réunion.
Ne pas inclure la construction cachée avec ces objets lors d’un éventuel export.
Axes : +Z vertical, −Y avant, +X gauche anatomique ; unité : mètre.

## Reconstruire dans un dossier libre

Avec Blender 4.3.2 (NumPy fourni), depuis la racine du dépôt :

```sh
blender --background --factory-startup --disable-autoexec --threads 2 \
  --python tools/m4a/build_l3_mannequin.py -- \
  --output /workspace/work/l3-rebuild --voxel .0025 --triangles 80000
blender --background --factory-startup --disable-autoexec --threads 1 \
  --python tools/m4a/check_original_mannequin.py -- \
  --prepared /workspace/work/l3-rebuild
```

Le budget de 80 000 précède la découpe exacte des frontières : les triangles
supplémentaires servent à cette partition. Les paramètres et le SHA-256 du
script utilisé figurent dans `construction.json`. Les BLEND publiés sont la
sauvegarde inspectée ; une reconstruction peut produire un autre binaire selon
le moteur ou la plateforme.

## Recalculer les vues sans toucher aux livrables

```sh
mkdir -p /workspace/work/l3-rerender/l2 /workspace/work/l3-rerender/l3
blender --background --factory-startup --disable-autoexec --threads 2 \
  --python tools/m4a/render_l3_mannequin.py -- \
  --prepared docs/m4a/original/defined \
  --output /workspace/work/l3-rerender/l2 --resolution 800 1280 --samples 128
blender --background --factory-startup --disable-autoexec --threads 2 \
  --python tools/m4a/render_l3_mannequin.py -- \
  --prepared docs/m4a/l3/l3 \
  --output /workspace/work/l3-rerender/l3 --resolution 800 1280 --samples 128
cp docs/m4a/original/defined/construction.json /workspace/work/l3-rerender/l2/
cp docs/m4a/l3/l3/construction.json /workspace/work/l3-rerender/l3/
python3 tools/m4a/make_l3_sheets.py --root /workspace/work/l3-rerender
```

Utiliser les **sources géométriques**, pas les scènes contenant déjà le studio.
Le script remet les matériaux bleus et la caméra trois quarts avant de sauver
la scène F12. Le moteur CPU disponible n’a pas OpenImageDenoise : les PNG sont
calculés sans débruitage. Pillow et DejaVu Sans servent seulement aux planches.

Pour contrôler les scènes et les empreintes publiées dans le dépôt :

```sh
blender --background --factory-startup --disable-autoexec --threads 1 \
  --python tools/m4a/audit_l3_review.py -- --root docs/m4a/l3
python3 tools/m4a/validate_l3_delivery.py
```

Le contrôle de géométrie ne teste pas exhaustivement les auto-intersections.
Aucune performance mobile, retopologie de rig ou compatibilité de shader avec
un moteur applicatif n’est affirmée. **M4A s’arrête pour validation visuelle.**
