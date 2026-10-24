# M4A — Lissage supplémentaire de la surface centrale

Proposition à valider, issue de **`d94297a`**, dans la PR #12 en brouillon.
Les **pieds du même mannequin sont bien la référence de finition** : surface
homogène, volumes simplifiés et transitions douces. Ils sont conservés à l'identique.

## Rendus de validation

- [Avant / après serré](m4a/ecorche-beatriz-aine-homogene/renders/comparatif-central-serre.png)
- [Face et trois quarts, avant / après](m4a/ecorche-beatriz-aine-homogene/renders/comparatif-aine.png)
- [Planche générale neutre](m4a/ecorche-beatriz-aine-homogene/renders/planche-neutre.png)
- [Comparaison directe avec les pieds](m4a/ecorche-beatriz-aine-homogene/renders/coherence-pieds.png)

Même matériau mat, mêmes caméras et mêmes lumières par paire. Le détail serré
est rendu à 128 échantillons des deux côtés, directement sur la même portion de
l'image ; les autres vues utilisent 32 échantillons. Aucun lissage d'image ni
retouche des rendus. Les quatre vues « avant » à 32 échantillons sont réutilisées
depuis `d94297a` avec vérification de leurs empreintes. Les cadrages des pieds
et de l'aine ont des échelles différentes, explicitement indiquées.

## Modifications réellement effectuées

Seule la surface de présentation **`groin.neutral_surface`** est reconstruite.
L'enveloppe arrondie est un peu plus haute et plus large à la racine pubienne,
et rentre progressivement vers le bas. Elle simplifie les petits reliefs centraux
sans déplacer les pièces anatomiques qu'elle recouvre.

La construction utilise une union implicite locale, des raccords progressifs
sur 8 mm et un filtrage du champ à l'échelle de 1 mm. Les marges sont enfouies
par le champ de construction, sans projection des sommets sur les muscles
voisins, pour éviter les plis. Le transfert des normales près des contacts
raccorde l'ombrage avec celui des pièces inchangées.

La topologie de **cette seule surface** est reconstruite : **38 488 triangles**
contre 20 799 auparavant, soit **17 689 supplémentaires**. Le mannequin passe
à **539 220 triangles Blender** (+3,4 %) et conserve 299 objets, dont **298
strictement inchangés**, y compris les pieds, adducteurs, cuisses, deltoïdes,
tête et gorge. La simplification mobile de l'ensemble reste à traiter plus tard.
L'export GLB fait **11,08 Mo**, contient 539 219 triangles et conserve les six
identifiants des deltoïdes. L'écart d'un triangle vient du doublon source déjà
omis par l'exporteur avant cette retouche.

## Contrôles et limites

[Les contrôles indépendants](m4a/ecorche-beatriz-aine-homogene/verification.json)
comparent les positions, faces, normales, matériaux, transformations et données
des 298 objets à `d94297a`, ainsi que leurs données exportées dans le GLB.
Ils contrôlent aussi l'absence d'auto-intersection de la surface retouchée,
le maintien des bords sous les pièces voisines, l'ouverture entre les jambes
et les changements de couverture antérieure sur des rayons échantillonnés.
Ces tests échantillonnés ne constituent pas une garantie de visibilité sous
tous les angles.

**La surface centrale est visiblement plus homogène et plus proche de la finition
simplifiée des pieds.** Les limites des muscles et les reliefs des pièces voisines
restent présents. L'enveloppe ne simplifie pas l'ensemble du bassin ou des adducteurs.

Le bord inférieur est plus rentrant : 65 rayons de contrôle révèlent davantage
les pièces déjà présentes en profondeur, dans une bande de 5 mm au bas de
l'enveloppe (hauteur 0,900 à 0,905 m dans le modèle). Aucun nouveau masquage n'est
détecté sur les 1 001 rayons qui traversaient l'ouverture naturelle entre les
jambes. Les détails visibles dans l'ombre à cet endroit restent un point de
validation esthétique ; ils n'ont pas été lissés dans les 298 pièces conservées.

La surface conserve des bords enfouis, sans soudure avec les autres pièces :
ce n'est pas une peau complète étanche. Les versions précédentes sont conservées.
Arrêt ici pour validation, sans nouvelle extension automatique de la retouche.

## Sources

[Blender](m4a/ecorche-beatriz-aine-homogene/ecorche-aine-homogene.blend),
[GLB de contrôle](m4a/ecorche-beatriz-aine-homogene/ecorche-aine-homogene.glb),
[paramètres](m4a/ecorche-beatriz-aine-homogene/finition.json) et
[fichiers / attribution](m4a/ecorche-beatriz-aine-homogene/README.md).
Corps : Beatriz Gomez Santamaria, CC BY 4.0 ; tête / yeux : Dan Ulrich,
Blender Studio, CC0. Adaptations et lissage local signalés dans les sources.

Application et SQLite inchangées. Aucune fusion ; PR #12 maintenue en brouillon.
