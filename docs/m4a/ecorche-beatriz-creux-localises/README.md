# Creux localisés — P4 + tête P5

**Essai non validé : le bombé est préservé, mais la correction visuelle des creux reste insuffisante.**
La référence validée reste `0ab3d83`, pas cette proposition.

[Rapport et rendus](../../M4A_CREUX_LOCALISES_VENTRE_PRESERVE.md).

Le fichier `ecorche-creux-localises.blend` conserve les scènes historiques de
`0ab3d83` et ajoute `17_CREUX_LOCALISES`. `16_COMBINAISON_P4_P5` reste la référence
exacte. Les fichiers de la proposition rejetée `62fe3ff` sont conservés séparément,
sans servir de base à cette retouche.

`ecorche-creux-localises.glb` est un export de contrôle. Les identifiants d’objets
sont conservés ; aucun masque interactif ni texture de sélection n’est ajouté.

Les NPZ sont des données de travail : `source.npz` contient le maillage P4,
la projection et la visibilité ; `surface.npz` contient les positions proposées,
les bandes géodésiques, les verrous du ventre/contour et les courbes 3D.
Ces verrous sont des contrôles d’édition, pas une segmentation des faisceaux.
Les JSON décrivent la caméra, la méthode, les contrôles et l’export.

La méthode précédente par enveloppe de profondeur et lissage étendu est abandonnée.
Le nouveau calcul raccorde transversalement l’ancien fond dans une bande étroite,
puis applique une dépression arrondie dans la bande cible. L’équilibre du volume
se fait uniquement entre ces bandes, sans compensation sur le ventre.

## Reproduction

Blender 4.3.2 avec NumPy ; Python système avec NumPy, SciPy et Pillow.
Depuis la racine du dépôt, utiliser une sortie distincte pour préserver la livraison :

```bash
CREUX_ASSET=docs/m4a/ecorche-beatriz-creux-localises-reproduction
CREUX_WORK=/workspace/work/ecorche-creux-reproduction
mkdir -p "$CREUX_WORK" "$CREUX_ASSET"
export XDG_CONFIG_HOME="$CREUX_WORK/blender-config"
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/creux_localises_prepare.py -- --baseline docs/m4a/ecorche-beatriz-combinaison-p4-p5/ecorche-p4-p5.blend --output "$CREUX_WORK"
python tools/m4a-ecorche/creux_localises_surface.py --source "$CREUX_WORK/source.npz" --camera "$CREUX_WORK/camera.json" --output "$CREUX_WORK/surface.npz"
cp "$CREUX_WORK/source.npz" "$CREUX_WORK/camera.json" "$CREUX_WORK/surface.npz" "$CREUX_WORK/surface.json" "$CREUX_ASSET/"
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/creux_localises_build.py -- --baseline docs/m4a/ecorche-beatriz-combinaison-p4-p5/ecorche-p4-p5.blend --surface "$CREUX_ASSET/surface.npz" --camera "$CREUX_ASSET/camera.json" --output "$CREUX_ASSET"
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/creux_localises_render.py -- --asset "$CREUX_ASSET"
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/creux_localises_export.py -- --asset "$CREUX_ASSET"
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/creux_localises_verify.py -- --asset "$CREUX_ASSET"
python tools/m4a-ecorche/creux_localises_compose.py --asset "$CREUX_ASSET"
```

Les normales peuvent tourner fortement lors du comblement d’un ancien fond
très creux. Les contrôles portent sur l’orientation projetée, les triangles
non dégénérés, la fermeture et les auto-intersections ; une rotation par rapport
à une ancienne normale n’est pas assimilée à elle seule à un maillage retourné.

## Attribution

Corps : **Ecorche - Anatomy study — Beatriz Gomez Santamaria**,
[source](https://sketchfab.com/3d-models/ecorche-anatomy-study-e402d3d541eb4b199c57d5410f5d3c57),
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), selon les métadonnées
du GLB fourni. Adaptations Logbook : reconstruction symétrique et athlétique,
finitions antérieures, combinaison P4/P5 et correction locale des creux.

Tête et yeux conservés : **Dan Ulrich / Blender Studio Human Base Meshes — CC0**,
[provenance P5](../ecorche-beatriz-passe5/HEAD_SOURCE_LICENSE.md).
Conserver attribution, licences et mention des modifications à la redistribution.
