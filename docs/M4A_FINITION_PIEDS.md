# M4A — Finition des deux pieds et raccords des chevilles

**Base : `d94297a`, conformément au commit demandé.** Ce mannequin conserve
l'aine de cette base à l'identique. La proposition d'aine `41896cc` est conservée
séparément dans son dossier, sans modification. Les versions précédentes restent
disponibles ; aucune intégration applicative n'est effectuée.

## Comparatifs de validation

- [Face et trois quarts](m4a/ecorche-beatriz-finition-pieds/renders/comparatif-pieds.png)
- [Profils droit et gauche](m4a/ecorche-beatriz-finition-pieds/renders/comparatif-profils.png)
- [Gros plan des raccords cheville / pied](m4a/ecorche-beatriz-finition-pieds/renders/raccords-chevilles.png)
- [Vue générale du mannequin](m4a/ecorche-beatriz-finition-pieds/renders/planche-generale.png)

Rendus Blender/Cycles avec le même matériau mat neutre, les mêmes caméras,
lumières et paramètres avant/après. Les images individuelles sont conservées
sans retouche ; les planches ajoutent seulement des légendes et un redimensionnement.

## Modifications réalisées

Les deux objets `m2_c001.left` et `m2_c001.right` sont remplacés par des pieds
reconstruits et symétriques. L'enveloppe supérieure du pied est légèrement
resserrée, progressivement, pour réduire le rebord évasé donnant l'aspect de
chausson. Les malléoles, le talon, la voûte et les cinq formes d'orteils restent
reconnaissables.

Un raccord implicite local sur 4,5 mm relie les pieds aux structures existantes
des chevilles. Un filtrage doux atténue les petites irrégularités de surface ;
une réduction du maillage limite ensuite chaque pied à 16 000 triangles en
protégeant ses bords de contact. Une marge locale de 0,6 mm près des chevilles
recouvre les petites extrémités sous-jacentes, sans modifier les jambes.
Les normales sont raccordées à celles des jambes près des jonctions.
Les cinq orteils sont conservés, avec des sillons
et détails d'ongles moins marqués.

Les nouveaux contacts se terminent entre 18,0 et 18,7 cm du sol, soit environ
2 cm au-dessus de l'ancienne enveloppe. **Aucun objet musculaire de la jambe
n'est déplacé, lissé ou redimensionné.** L'aine, la tête P5, la gorge, les
deltoïdes et le reste du corps sont inchangés.

## Contrôles techniques

| Contrôle | Résultat |
| --- | --- |
| Autres objets conservés | 297, géométrie brute et évaluée, normales, matériaux et données inchangés |
| Six identifiants des deltoïdes | Conservés, avec correspondance matériaux / primitives GLB |
| Symétrie des pieds | Écart inférieur à 1 µm |
| Auto-intersections des nouveaux pieds | Aucune détectée |
| Bords de contact | Sommets et milieux d'arêtes testés ; tous enfouis dans les structures inchangées |
| Fragments de jambe traversant le raccord | Aucun nouveau fragment sur les 27 642 rayons qualifiés des vues trois quarts de contrôle |
| Avant-pied | 95 % des sommets de référence testés à moins de 0,45 mm de la nouvelle surface ; maximum local 1,96 mm |
| Export GLB | Géométrie des nouveaux pieds vérifiée ; données des 297 autres objets identiques |

La comparaison de l'avant-pied mesure une distance de surface, et non une
correspondance entre sommets : la topologie des deux pieds est reconstruite.
Leurs UV d'origine ne sont pas conservés ; le matériau actuel est uni.

| Géométrie | Avant | Après |
| --- | ---: | ---: |
| Triangles par pied | 10 934 | 16 000 |
| Total Blender | 521 531 | 531 663 |

Soit **10 132 triangles supplémentaires (+1,94 %)**. Le GLB fait **10,93 Mo**,
avec 531 662 triangles ; le triangle d'écart est le doublon source déjà omis
avant cette retouche. Aucun test de performance dans l'application n'est effectué.

## Limites et arrêt

Le rebord est moins évasé et les transitions sont plus douces. Le passage entre
les pieds lisses et l'anatomie disséquée des jambes reste perceptible : il doit
être jugé sur le gros plan des chevilles. Les contacts sont enfouis dans les
structures conservées, sans soudure globale du mannequin. Les contrôles portent
sur la géométrie et les échantillons décrits.

**Proposition arrêtée pour validation visuelle.** Aucun changement de Logbook,
de SQLite ou des autres fonctionnalités ; aucun M4B et aucune fusion de la PR #12.

[Source Blender, GLB et fichiers de contrôle](m4a/ecorche-beatriz-finition-pieds/README.md).
