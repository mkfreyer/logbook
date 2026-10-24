# M4A — Tête de mannequin sans visage

**Base : `d83fc44`.** Une seule proposition, arrêtée pour validation visuelle.
Le corps anatomique, les six zones des deltoïdes, l’aine de `41896cc` et les
pieds retouchés sont conservés.

## Rendus

- [Ancienne / nouvelle tête : face et trois quarts](m4a/ecorche-beatriz-tete-neutre/renders/comparatif-tete-face-trois-quarts.png)
- [Ancienne / nouvelle tête : profil et arrière](m4a/ecorche-beatriz-tete-neutre/renders/comparatif-tete-profil-arriere.png)
- [Mannequin complet avant / après](m4a/ecorche-beatriz-tete-neutre/renders/planche-generale.png)
- [Images individuelles](m4a/ecorche-beatriz-tete-neutre/renders/after)

Vrais rendus Blender/Cycles, matériau mat neutre et cinq lumières hérités.
Caméras, cadrages, échantillonnage et éclairage identiques avant/après.
Aucun lissage ni effacement sur les images ; les planches ajoutent uniquement
des légendes et un redimensionnement uniforme.

## Modifications réalisées

La tête humaine P5 est remplacée par une **nouvelle surface 3D continue** :
crâne légèrement ovale, côtés arrondis, partie inférieure resserrée et sommet
fermé. Aucun œil, nez, bouche, sourcil, oreille, cheveu ou détail facial.
Le sommet reste à 1,800 m, contre 1,80007 m précédemment.

La forme est construite par sections elliptiques à profils cubiques, avec une
calotte arrondie analytique. Elle ne résulte ni d’un floutage du visage P5,
ni d’une coque posée par-dessus. Les deux objets des yeux sont retirés de la
nouvelle scène et de son export ; ils restent dans les versions antérieures.

La tête et la gorge partageaient l’objet `head_throat.neutral_surface`.
Sa partie cervicale validée est conservée **exactement jusqu’à 1,570 m** :
10 637 triangles, mêmes positions et mêmes surfaces. Seule l’ancienne jonction
P5 située au-dessus, sous le menton, est reconstruite avec la tête. La nouvelle
surface partage le bord cervical existant : pas de plaque superposée, pas de
trou entre la tête et cette gorge.

Le raccord tient compte des attaches anatomiques conservées à l’arrière et sur
les côtés. Les muscles voisins ne sont ni déplacés ni lissés. Les normales de
la gorge sont transférées et celles de la nouvelle tête raccordées localement ;
leur écart maximal de réencodage est de **0,088°**, sans déplacement géométrique.
Aucune texture, normal map ou ligne peinte ne crée l’aspect sans visage.

## Contrôles

| Contrôle | Résultat |
| --- | --- |
| Autres objets conservés | 296, géométrie brute et évaluée, normales, matériaux et données associées identiques à `d83fc44` |
| Gorge protégée | 10 637 triangles d’origine conservés, déplacement nul |
| Nouvelle tête / gorge | Une composante fermée, arêtes à deux faces, orientation cohérente |
| Auto-intersections de cette surface | Aucune détectée |
| Anatomie sous-jacente auparavant masquée | Aucun nouveau dépassement sur 38 016 rayons qualifiés, face, trois quarts et profils bilatéraux, arrière |
| Six identifiants des deltoïdes | Conservés, correspondance matériaux / primitives GLB vérifiée |
| Export | Surface tête / gorge comparée au Blender ; attributs des 296 autres objets identiques au GLB source |

Les empreintes des sources, contrôles détaillés et échantillons sont disponibles
dans [verification.json](m4a/ecorche-beatriz-tete-neutre/verification.json).
Le contrôle de visibilité utilise une grille de rayons à pas de 1 mm sur la
région supérieure de raccord : il complète les vues de validation sans constituer
une preuve exhaustive de toutes les intersections entre objets du corps modulaire.

| Mesure | Avant | Après |
| --- | ---: | ---: |
| Objets de maillage | 299 | 297 |
| Tête + gorge, hors yeux | 34 732 triangles | 29 328 triangles |
| Total Blender | 549 352 triangles | 541 772 triangles |
| Total GLB | 549 351 triangles | 541 771 triangles |

**7 580 triangles en moins (−1,38 %).** Le GLB fait environ 11,13 Mo,
sans nouvelle texture. Le triangle d’écart Blender / GLB est le doublon source
déjà omis avant ce travail. Le matériau uni de la nouvelle tête ne nécessite
pas d’UV ; aucune optimisation globale ni mesure dans l’application n’est lancée.

## Limites et arrêt

La tête est volontairement sobre et sans oreilles ; les repères anatomiques
du cou restent visibles, conformément à leur conservation. Les proportions
et la qualité du raccord sont à valider sur les vues rapprochées et générales.
Il s’agit d’une proposition de mannequin fitness, sans validation clinique.

[Sources Blender / GLB et reproduction](m4a/ecorche-beatriz-tete-neutre/README.md).
Toutes les versions précédentes restent disponibles. Application et SQLite
inchangées, aucun M4B, PR #12 en brouillon, sans fusion.

**Arrêt pour validation visuelle avant toute intégration.**
