# M4A — Surface centrale davantage lissée

Proposition de finition locale à partir de `d94297a`, à valider visuellement.
Les pieds du même mannequin constituent la référence de **langage de surface** :
uniformité, simplification et transitions douces. Ils ne sont pas retouchés.

- [Rapport](../../M4A_AINE_SURFACE_HOMOGENE.md)
- [Avant / après serré](renders/comparatif-central-serre.png)
- [Face et trois quarts](renders/comparatif-aine.png)
- [Planche générale neutre](renders/planche-neutre.png)
- [Comparaison directe avec les pieds](renders/coherence-pieds.png)
- [Source Blender](ecorche-aine-homogene.blend), scène `25_AINE_SURFACE_HOMOGENE`
- [Export GLB de contrôle](ecorche-aine-homogene.glb)

## Fichiers et contrôles

`surface-fondue.npz` contient les positions, triangles, normales, sommets de bord
et poids de contact de la seule surface dédiée `groin.neutral_surface`.
`finition.json` décrit la filiation, les paramètres et les empreintes des sources.
`verification.json` contrôle indépendamment les 298 autres objets, les raccords,
les intersections, l'ouverture entre les jambes et l'export.
`selection-map.json` préserve les six zones des deltoïdes ; la surface centrale
reste exclue de la sélection de muscles d'entraînement.

Les images individuelles sont des rendus Blender/Cycles sans retouche. Les quatre
vues « avant » à 32 échantillons proviennent directement de `d94297a` ; le détail
serré est rendu de nouveau à 128 échantillons des deux côtés, avec le même
recadrage effectué par Blender. Les planches ajoutent seulement des légendes et
un redimensionnement uniforme. Les cadrages de l'aine et des pieds ont des
échelles différentes, signalées sur la comparaison.

Les scripts reproductibles sont `tools/m4a-ecorche/aine_homogene_*.py` :
`fields` (Blender), `surface` (Python/NumPy/SciPy/scikit-image),
`build`, `export`, `verify`, `render` (Blender), puis
`compose` (Python/Pillow). Ces outils n'ajoutent aucune dépendance à l'application.
La surface est une finition de présentation avec des bords enfouis dans les
pièces voisines ; elle ne constitue pas une peau entière soudée et étanche.

## Attribution

Corps dérivé de **Ecorche - Anatomy study**, Beatriz Gomez Santamaria,
[source](https://sketchfab.com/3d-models/ecorche-anatomy-study-e402d3d541eb4b199c57d5410f5d3c57),
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Modifications Logbook : reconstruction et adaptation des passes précédentes,
puis reconstruction locale d’une enveloppe centrale plus homogène et plus lisse.
Tête et yeux : Dan Ulrich / Blender Studio, Human Base Meshes v1.4.1, CC0 ;
voir [la licence conservée](../ecorche-beatriz-passe5/HEAD_SOURCE_LICENSE.md).

Aucune intégration applicative, modification SQLite ou fusion. PR #12 en brouillon.
