# Sources et reprise — mannequin original M4A

[Étude et recommandation](../../M4A_MANNEQUIN_ORIGINAL.md) ·
[Origine](ORIGINE.md) · [Manifeste SHA-256](manifest.json) ·
[Contrôles de livraison](validation.json).

| Fichier | L1 — doux | L2 — musculaire |
| --- | --- | --- |
| Source géométrique, studio ajouté par le script de rendu | [BLEND](soft/logbook-original.blend) | [BLEND](defined/logbook-original.blend) |
| Scène de revue, studio et caméra déjà présents | [BLEND](soft/scene-review.blend) | [BLEND](defined/scene-review.blend) |
| Profils, coefficients et inventaire | [JSON](soft/construction.json) | [JSON](defined/construction.json) |
| Contrôle de surface/partition | [JSON](soft/geometry-check.json) | [JSON](defined/geometry-check.json) |
| Réglages et empreintes des PNG | [JSON](soft/render-metadata.json) | [JSON](defined/render-metadata.json) |

Les sources s’ouvrent avec Blender 4.3.2. La scène de revue est prête pour un rendu
manuel F12, avec la matière neutre et le trois quarts commun. La caméra des
comparaisons est orthographique ; l’orange des PNG ne signifie pas qu’un moteur
interactif existe.

Le corps contient **23 objets affichés** : 22 zones et un support non sélectionnable.
`LB.Construction.closed-surface` est l’enveloppe continue **cachée**, conservée
pour les contrôles et la reprise. Ne pas l’exporter avec les zones affichées comme
une seconde peau. Les sources et scènes sont sauvegardées directement dans Git,
sans dépendre d’une archive ou de téléchargements d’assets.

## Reconstruire la géométrie originale

Depuis la racine du dépôt, dans un dossier de travail libre :

```sh
for variant in soft defined; do
  blender --background --factory-startup --disable-autoexec --threads 2 \
    --python tools/m4a/build_original_mannequin.py -- \
    --variant "$variant" \
    --output "/workspace/work/m4a-original-rebuild/$variant"
  blender --background --factory-startup --disable-autoexec --threads 1 \
    --python tools/m4a/check_original_mannequin.py -- \
    --prepared "/workspace/work/m4a-original-rebuild/$variant"
done
```

Les logiciels utilisent leurs bibliothèques installées ; aucun modèle source
externe n’est requis. NumPy est fourni par Blender. La voxelisation utilise la
version du moteur installée : garder Blender 4.3.2 et les paramètres indiqués
pour comparer une reconstruction. Les empreintes de la livraison identifient
les fichiers effectivement inspectés, sans promettre le même binaire BLEND
avec une autre version de Blender ou une autre plateforme.

## Recalculer les PNG homogènes

Utiliser les **sources géométriques**, pas les scènes de revue qui contiennent
déjà les lumières. Le renderer ajoute lui-même le studio commun.

```sh
for variant in soft defined; do
  blender --background --factory-startup --disable-autoexec --threads 2 \
    --python tools/m4a/render_original_mannequin.py -- \
    --prepared "/workspace/logbook/docs/m4a/original/$variant" \
    --output "/workspace/work/m4a-original-rerender/$variant" \
    --resolution 800 1280 --samples 128
done
```

Le script calcule cinq vues et sauvegarde une scène de revue neutre. Pour assembler
les planches, copier aussi le `construction.json` de chaque variante dans son
dossier de rendu, puis :

```sh
python3 tools/m4a/make_original_sheets.py \
  --root /workspace/work/m4a-original-rerender
```

Pillow et DejaVu Sans servent seulement à l’assemblage des PNG, pas à fabriquer
ou retoucher les volumes. Ne pas écrire les nouveaux essais sur les livrables
déjà versionnés si l’on veut conserver leurs empreintes.

Ni application, SQLite, migration, dépendance mobile ou M4B nécessaire pour cette
reprise. Le choix de la direction artistique reste à l’utilisateur.
