# M4A — Simplification esthétique locale de l’aine

## Proposition à valider

Base exclusive : [`d79692f`](https://github.com/mkfreyer/logbook/commit/d79692f380e39312939290ab0d3e038e448aa9b2), avec les deltoïdes P4 et leurs six zones, la tête P5 et la gorge validée. **Aucun muscle existant n’est sculpté ni déplacé.**

La proposition remplace **deux petites pièces centrales exposées** par une surface de présentation plus sobre. Elle atténue les détails centraux et leur séparation sans recouvrir les ventres des adducteurs ni refaire le bassin. La surface est reculée sous les muscles voisins, avec une partie inférieure rentrante pour éviter une masse projetée en avant.

L’image annoncée dans la demande n’était pas disponible parmi les pièces reçues. Le périmètre a donc été défini d’après la description écrite et l’examen du modèle. Cette livraison reste une proposition esthétique, à valider sur les rendus.

## Comparatifs Blender

- [Avant / après très serré du centre](m4a/ecorche-beatriz-finition-aine/renders/comparatif-central-serre.png), recadrage identique des deux rendus de face.
- [Avant / après : face et trois quarts](m4a/ecorche-beatriz-finition-aine/renders/comparatif-aine.png).
- [Planche neutre à l’échelle du mannequin : face et trois quarts](m4a/ecorche-beatriz-finition-aine/renders/planche-neutre.png).
- [Rendus après retouche](m4a/ecorche-beatriz-finition-aine/renders/after/) et [référence avant retouche](m4a/ecorche-beatriz-finition-aine/renders/before/).

Blender 4.3.2 / Cycles CPU, matériau mat neutre hérité, éclairage à cinq sources conservé, 32 échantillons, sans débruitage. Les quatre paires utilisent les mêmes matrices de caméra, cadrages et résolutions. Les images individuelles sont des sorties Blender sans retouche ; les planches ajoutent des légendes, redimensionnent les images et proposent un même recadrage pour le détail central.

## Modifications réellement effectuées

| Élément | Intervention |
| --- | --- |
| `m0_c098__CENTRAL__ATHLETIQUE` | Retiré uniquement de la nouvelle scène de présentation. |
| `m1_c084__CENTRAL__ATHLETIQUE` | Retiré uniquement de la nouvelle scène de présentation. |
| `groin.neutral_surface` | Nouvelle surface neutre fermée et symétrique, placée dans la région centrale. Ce n’est ni un organe reconstitué ni un muscle d’entraînement. |
| 298 autres objets | Géométrie, reliefs, topologie, clés de forme, groupes, UV, transformations, normales et matériaux conservés. |

Les noms techniques des pièces sources ne constituent pas une identification anatomique certifiée. Leurs coordonnées et l’examen du modèle les situent dans la région centrale demandée.

La nouvelle surface mesure **10,4 cm de largeur et 6,1 cm de hauteur** dans ses dimensions complètes ; une grande partie reste sous les surfaces voisines. Son profil antérieur est aplati et sa partie basse recule. Il s’agit d’une reconstruction géométrique locale, sans texture de camouflage.

Les deux pièces substituées restent intactes dans la scène historique `22_ANATOMIE_DELTOIDES_P4` du nouveau Blender, ainsi que dans le fichier original. La proposition est dans `23_FINITION_AINE_LOCALISEE`.

## Préservation et coût

Le [contrôle indépendant](m4a/ecorche-beatriz-finition-aine/verification.json) compare les fichiers Blender sérialisés et les GLB avec la référence :

- **298 objets conservés à l’identique**, dont les deltoïdes, la tête, la gorge, les pectoraux et tous les muscles des cuisses. Aucun sommet d’origine déplacé.
- Positions, normales, indices et attributs des **298 maillages GLB conservés identiques bit à bit**.
- Nouvelle surface fermée, connexe, symétrique et sans auto-intersection non adjacente détectée.
- Les **six identifiants des deltoïdes** et leurs matériaux / primitives restent disponibles dans la [table de sélection](m4a/ecorche-beatriz-finition-aine/selection-map.json).

| Mesure | Référence | Proposition |
| --- | ---: | ---: |
| Objets visibles/exportés | 300 | 299 : deux remplacés par un |
| Triangles Blender | 501 582 | 502 940 |
| Triangles GLB | 501 581 | 502 939 |
| Primitives GLB | 304 | 303 |
| Matériaux GLB | 7 | 7 |
| Textures ajoutées | — | 0 |

La nouvelle surface comporte **2 208 triangles** et remplace 850 triangles, soit **+1 358 triangles nets (+0,27 %)**. Le détail exact de taille et les empreintes des fichiers figurent dans [export.json](m4a/ecorche-beatriz-finition-aine/export.json). Aucun test de fluidité mobile ni optimisation globale n’est réalisé dans cette tâche.

## Limites et recommandation

La retouche est volontairement discrète : elle neutralise les petites structures centrales, mais **conserve les plis inguinaux, les insertions et les reliefs musculaires voisins**. Elle n’efface pas toute l’anatomie visible en profondeur entre les jambes. L’ouverture naturelle entre les cuisses reste présente.

La surface est insérée sous les muscles par des recouvrements enfouis ; ce n’est pas une peau globale soudée. Le contrôle de fermeture concerne la nouvelle surface elle-même, pas une certification d’absence d’intersections de tout le mannequin anatomique. Elle est exclue des zones musculaires d’entraînement ; les muscles conservés gardent leur structure existante.

**Recommandation : juger cette simplification centrale sur le gros plan et la planche générale, sans changer les volumes validés.** La validation esthétique reste ouverte. Arrêt après cette proposition : aucune intégration Logbook, modification SQLite, M4B ou fusion ; PR #12 conservée en brouillon.

## Sources

[Blender](m4a/ecorche-beatriz-finition-aine/ecorche-finition-aine.blend) · [GLB neutre](m4a/ecorche-beatriz-finition-aine/ecorche-finition-aine.glb) · [Paramètres et reproduction](m4a/ecorche-beatriz-finition-aine/README.md).

Corps : **Ecorche - Anatomy study — Beatriz Gomez Santamaria**, [source Sketchfab](https://sketchfab.com/3d-models/ecorche-anatomy-study-e402d3d541eb4b199c57d5410f5d3c57), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Adaptation Logbook : retouches historiques et substitution locale de présentation signalées dans le GLB. Tête / yeux : **Dan Ulrich / Blender Studio, Human Base Meshes v1.4.1**, CC0 ; [provenance](m4a/ecorche-beatriz-passe5/HEAD_SOURCE_LICENSE.md). Aucun achat, service payant ou Astra Ultra.
