# M4A — Aine : surface arrondie et raccords fondus

## Proposition

Reprise de [`cf5569b`](https://github.com/mkfreyer/logbook/commit/cf5569b2e84727a800863301901126a6630884f3). **Seul l’objet de présentation de l’aine est reconstruit. Les 298 autres objets restent identiques**, notamment les adducteurs, les cuisses, les deltoïdes et leurs six zones, la tête, la gorge et les pieds.

La face antérieure aplatie et la terminaison presque horizontale de la surface précédente donnaient un effet de pièce rapportée. La nouvelle forme est arrondie, puis rentre progressivement vers l’arrière dans sa partie basse. Des raccords géométriques suivent les surfaces réelles des voisins ; leur ombrage reprend les normales de ces voisins aux contacts. La barre transversale est supprimée sans ajout de rainure ni sculpture des muscles.

L’image des pieds annoncée n’était pas disponible dans les pièces reçues. La référence de simplification est donc **celle des pieds du mannequin lui-même**, photographiés virtuellement sans aucune retouche de leur géométrie.

## Rendus pour validation

- [Avant / après central serré](m4a/ecorche-beatriz-aine-fondue/renders/comparatif-central-serre.png).
- [Face et trois quarts : avant / après](m4a/ecorche-beatriz-aine-fondue/renders/comparatif-aine.png).
- [Planche générale neutre](m4a/ecorche-beatriz-aine-fondue/renders/planche-neutre.png).
- [Comparaison du langage de surface avec les pieds](m4a/ecorche-beatriz-aine-fondue/renders/coherence-pieds.png), à des échelles de cadrage différentes.

Même matériau mat et même éclairage. Blender 4.3.2 / Cycles CPU, 32 échantillons, sans débruitage ni retouche des images individuelles. **Quatre rendus avant de `cf5569b` réutilisés après vérification des empreintes**, cinq nouveaux rendus après. Les quatre paires ont les mêmes caméras, cadrages et résolutions ; les recadrages des détails sont identiques.

## Méthode et contrôles

La reconstruction utilise un champ de distances local et une union adoucie de rayon **4,5 mm**, calculée sur une grille de **1,25 mm**. Les objets voisins servent de références, sans modification de leurs sommets. Les faces entièrement enfouies sont supprimées. La surface libre reçoit un lissage géométrique continu ; les normales anatomiques d’origine ne sont reprises qu’aux marges de contact. Le bord des nouvelles plages est projeté sur la surface voisine puis légèrement enfoui ; les normales lissées d’origine assurent la continuité d’ombrage.

Le [contrôle indépendant](m4a/ecorche-beatriz-aine-fondue/verification.json) confirme :

- **298 objets Blender conservés exactement**, ainsi que leurs positions, normales, indices et attributs dans le GLB. Six IDs de deltoïdes et correspondances matériaux / primitives préservés.
- Tous les bords de contact sous les surfaces voisines : enfouissement mesuré de **0,077 à 0,150 mm**. Aucune auto-intersection non adjacente détectée dans la nouvelle surface.
- **6 413 rayons dans l’ouverture basse entre les jambes : aucune occlusion ajoutée** par rapport à `cf5569b`. Les muscles des jambes ne sont pas déformés.

| Mesure | `cf5569b` | Proposition |
| --- | ---: | ---: |
| Objets / primitives GLB | 299 / 303 | 299 / 303 |
| Triangles de la surface neutre | 2 208 | 20 799 |
| Triangles Blender totaux | 502 940 | 521 531 |
| GLB | 10 396 860 octets | 10 746 948 octets |

Surcoût : **+18 591 triangles (+3,70 %)**, environ **342 Kio**, aucune texture ajoutée. Cette tessellation sert au prototype visuel ; aucune fluidité mobile n’est déclarée mesurée.

## Limites et arrêt

La nouvelle surface regroupe **les plages de raccord utiles dans un seul objet**. Leurs limites sont enfouies dans l’anatomie conservée : ce n’est pas une peau monobloc soudée et étanche. Les plis inguinaux et reliefs voisins restent visibles pour conserver les muscles validés ; leur disparition complète n’est pas revendiquée.

**Proposition : retenir cette version pour juger des raccords plus progressifs, avec une ouverture naturelle conservée. La validation esthétique reste à donner.** Aucun travail supplémentaire lancé après ces rendus : application et SQLite inchangées, pas de M4B, PR #12 en brouillon, sans fusion.

[Blender / GLB / reproduction](m4a/ecorche-beatriz-aine-fondue/README.md). Aucun achat, outil payant ou Astra Ultra. Corps : **Beatriz Gomez Santamaria, Ecorche - Anatomy study**, [Sketchfab](https://sketchfab.com/3d-models/ecorche-anatomy-study-e402d3d541eb4b199c57d5410f5d3c57), **CC BY 4.0**, adaptations Logbook et nouveaux raccords signalés. Tête / yeux : **Dan Ulrich / Blender Studio, Human Base Meshes v1.4.1**, **CC0** ; [provenance](m4a/ecorche-beatriz-passe5/HEAD_SOURCE_LICENSE.md).
