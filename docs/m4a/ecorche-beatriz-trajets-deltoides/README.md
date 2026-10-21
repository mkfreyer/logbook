# Deltoïdes P4 — déplacement local des creux

[Rapport et comparatifs](../../M4A_RETOUCHE_TRAJETS_DELTOIDES.md).

- `ecorche-trajets-deltoides.blend` : scène active `17_TRAJETS_DELTOIDES` ;
  les scènes historiques et la combinaison P4/P5 d’origine sont conservées.
- `ecorche-trajets-deltoides.glb` : copie évaluée de contrôle, identifiants
  de pièces et forme géométrique conservés, sans lignes ni masques de couleur.
- `source.npz` : géométrie P4 d’origine et base de caméra, extraite de `0ab3d83`.
- `surface.npz` : coordonnées proposées, indices des faces inchangés,
  coordonnées sources, déplacement scalaire et sommets affectés.
- `surface.json` : trajets rouges/bleus relevés dans la référence et repères
  correspondants sur la surface, méthode et paramètres.
- `trajets.json`, `export.json`, `verification.json` : provenance et contrôles.
- `renders/` : captures Blender, planches et empreintes des images.

La shape key `TRAJETS_BLEUS_LOCAUX` est relative à la forme P4 active : sa valeur
0 restaure les deltoïdes P4, sa valeur 1 montre la proposition. Les pièces
du corps protégées partagent leurs données inchangées avec la scène précédente.
Les groupes d’auteur hérités restent présents, sans nouveau groupe, masque
ou découpage des faisceaux.

## Reproduction

Blender 4.3.2 avec NumPy ; Python système avec NumPy, SciPy et Pillow.
Depuis la racine du dépôt, choisir une nouvelle sortie pour préserver la livraison :

```bash
ASSET=docs/m4a/ecorche-beatriz-trajets-deltoides-reproduction
WORK=/workspace/work/ecorche-trajets-reproduction
mkdir -p "$WORK" "$ASSET"
export XDG_CONFIG_HOME="$WORK/blender-config"
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/trajets_deltoides_prepare.py -- --baseline docs/m4a/ecorche-beatriz-combinaison-p4-p5/ecorche-p4-p5.blend --output "$WORK"
python tools/m4a-ecorche/trajets_deltoides_surface.py --source "$WORK/source.npz" --output "$WORK/surface.npz"
cp "$WORK/source.npz" "$WORK/surface.npz" "$WORK/surface.json" "$ASSET/"
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/trajets_deltoides_build.py -- --baseline docs/m4a/ecorche-beatriz-combinaison-p4-p5/ecorche-p4-p5.blend --surface "$ASSET/surface.npz" --output "$ASSET"
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/trajets_deltoides_render.py -- --asset "$ASSET"
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/trajets_deltoides_export.py -- --asset "$ASSET"
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-ecorche/trajets_deltoides_verify.py -- --asset "$ASSET"
python tools/m4a-ecorche/trajets_deltoides_compose.py --asset "$ASSET"
```

Les repères sont manuels : les trois images guident la retouche, sans prétendre
à un recalage automatique des pixels du recadrage fourni. Les comparatifs
utilisent en revanche exactement les mêmes caméras et lumières avant/après.
Les cartes intermédiaires ne sont pas exportées en textures ou normal maps :
seules les positions réelles des sommets des deltoïdes changent.

## Attribution

Corps : **Ecorche - Anatomy study — Beatriz Gomez Santamaria**,
[source](https://sketchfab.com/3d-models/ecorche-anatomy-study-e402d3d541eb4b199c57d5410f5d3c57),
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), selon les métadonnées
du GLB fourni. Adaptations Logbook : reconstruction symétrique et athlétique,
finitions antérieures, combinaison P4/P5 et déplacement local des creux des deltoïdes.

Tête et yeux conservés : **Dan Ulrich / Blender Studio Human Base Meshes — CC0**,
[provenance P5](../ecorche-beatriz-passe5/HEAD_SOURCE_LICENSE.md).
Conserver les attributions, licences et mentions des modifications à la redistribution.
