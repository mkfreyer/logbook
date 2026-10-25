# M4A — Pieds : finition et raccords des chevilles

Base géométrique : **`d94297a`**, explicitement demandé. Seuls les deux pieds
et leurs raccords immédiats sont retouchés ; les 297 autres objets de cette
base sont identiques. La proposition d'aine `41896cc` reste conservée séparément.

- [Rapport](../../M4A_FINITION_PIEDS.md)
- [Comparatif face / trois quarts](renders/comparatif-pieds.png)
- [Profils droit / gauche](renders/comparatif-profils.png)
- [Raccords des chevilles](renders/raccords-chevilles.png)
- [Vue générale](renders/planche-generale.png)
- [Blender](ecorche-finition-pieds.blend), scène `26_FINITION_PIEDS`
- [GLB neutre de contrôle](ecorche-finition-pieds.glb)

`foot-left.npz` et `foot-right.npz` contiennent les nouvelles géométries et
normales. `finition.json` décrit la filiation et les paramètres ; `verification.json`
contient les contrôles indépendants. `selection-map.json` conserve les six
identifiants des deltoïdes et leurs correspondances GLB, sans segmentation nouvelle.
Les bords des pieds sont enfouis dans les volumes des chevilles conservées.

Les scripts `tools/m4a-ecorche/pieds_*.py` permettent de reproduire la proposition :

1. `pieds_fields.py` dans Blender : lecture de la base et champs locaux.
2. `pieds_surface.py` dans Python/NumPy/SciPy/scikit-image : extraction de surface.
3. `pieds_build.py` dans Blender : reconstruction, réduction et miroir.
4. `pieds_export.py`, puis `pieds_verify.py` dans Blender : export et contrôles.
5. `pieds_render.py` dans Blender pour chaque mode `before` / `after`, puis
   `pieds_compose.py` dans Python/Pillow pour les planches.

Passer les options après `--` pour les scripts Blender ; `--help` décrit leurs
arguments. Ces outils ne changent aucune dépendance de l'application.
Versions utilisées : Blender 4.3.2, Python 3.12, scikit-image 0.26.0.
Les rendus utilisent Cycles CPU, 32 échantillons, sans débruitage ni retouche.

## Attribution

Corps dérivé de **Ecorche - Anatomy study**, Beatriz Gomez Santamaria,
[source](https://sketchfab.com/3d-models/ecorche-anatomy-study-e402d3d541eb4b199c57d5410f5d3c57),
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Modifications Logbook : adaptations des passes précédentes, puis reconstruction
esthétique locale des deux pieds et de leurs raccords de cheville.
Tête / yeux : Dan Ulrich, Blender Studio Human Base Meshes v1.4.1, CC0 ;
voir [la licence conservée](../ecorche-beatriz-passe5/HEAD_SOURCE_LICENSE.md).

PR #12 en brouillon, sans fusion. Arrêt pour validation avant toute intégration.
