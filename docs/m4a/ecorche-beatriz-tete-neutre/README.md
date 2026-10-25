# M4A — Tête lisse sans visage

Proposition dérivée de `d83fc44`, limitée à la tête et à sa jonction supérieure
avec la gorge. Les 296 autres objets sont conservés, ainsi que la surface
cervicale protégée. Les deux yeux P5 sont retirés de la nouvelle scène.

- [Rapport](../../M4A_TETE_NEUTRE_SANS_VISAGE.md)
- [Face / trois quarts](renders/comparatif-tete-face-trois-quarts.png)
- [Profil / arrière](renders/comparatif-tete-profil-arriere.png)
- [Mannequin complet](renders/planche-generale.png)
- [Blender](ecorche-tete-neutre.blend), scène `28_TETE_NEUTRE`
- [GLB neutre](ecorche-tete-neutre.glb)
- [Filiation et paramètres](tete.json)
- [Contrôles indépendants](verification.json)
- [Six zones des deltoïdes](selection-map.json)

La nouvelle tête n’a ni visage, ni yeux, ni oreilles, ni cheveux. C’est une
surface fermée à sections ovales et calotte arrondie, partageant son bord avec
la gorge d’origine. Les anciennes scènes restent dans le fichier Blender à
titre d’historique ; seule `28_TETE_NEUTRE` est exportée.

## Reproduction

Depuis la racine du dépôt, avec Blender 4.3.2 :

```bash
blender --background --factory-startup --disable-autoexec --python-exit-code 1 \
  --python tools/m4a-ecorche/tete_neutre_build.py -- \
  --baseline docs/m4a/ecorche-beatriz-pieds-aine-validee/ecorche-pieds-aine-validee.blend \
  --output docs/m4a/ecorche-beatriz-tete-neutre
```

Exécuter ensuite `tete_neutre_export.py`, puis `tete_neutre_verify.py`, avec
`-- --asset docs/m4a/ecorche-beatriz-tete-neutre`.
Rendre `tete_neutre_render.py` avec le même argument et `--mode before`, puis
`--mode after`. Enfin :

```bash
python tools/m4a-ecorche/tete_neutre_compose.py \
  --asset docs/m4a/ecorche-beatriz-tete-neutre
```

Rendus Cycles CPU, 48 échantillons sur les têtes et 32 sur l’ensemble,
sans débruitage ni retouche. Pillow sert uniquement à composer les planches.
Aucune dépendance de l’application ajoutée.

## Attribution

Corps : **Ecorche - Anatomy study**, Beatriz Gomez Santamaria,
[source](https://sketchfab.com/3d-models/ecorche-anatomy-study-e402d3d541eb4b199c57d5410f5d3c57),
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Adaptations Logbook des passes précédentes, puis reconstruction de la tête
sans visage. La gorge conservée provient des adaptations antérieures ; la
filiation CC0 de la tête P5 reste documentée dans
[la licence source](../ecorche-beatriz-passe5/HEAD_SOURCE_LICENSE.md),
Dan Ulrich / Blender Studio Human Base Meshes v1.4.1.

PR #12 conservée en brouillon, sans fusion. Arrêt pour validation visuelle.
