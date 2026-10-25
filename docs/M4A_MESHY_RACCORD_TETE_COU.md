# M4A — Finition locale du raccord tête / cou

Base : **`dbba75e`**, corps Anatomical Form avec tête Marble Titan.
La correction concerne uniquement la base de la tête et son raccord cervical.
Le visage, la coiffure et le corps ne sont pas resculptés.

## Rendus de validation

- [Avant / après serré : profil, face et trois quarts](m4a/meshy-marble-titan-raccord-cou/renders/comparatif-raccord.png).
- [Contrôle général : avant / après de face et nouvelle vue trois quarts](m4a/meshy-marble-titan-raccord-cou/renders/controle-general.png).
- [Gros plan corrigé de profil](m4a/meshy-marble-titan-raccord-cou/renders/after/raccord-profil.png).
- [Gros plan corrigé de face](m4a/meshy-marble-titan-raccord-cou/renders/after/raccord-face.png).
- [Gros plan corrigé trois quarts](m4a/meshy-marble-titan-raccord-cou/renders/after/raccord-trois-quarts.png).

Dix vrais rendus Blender/Cycles, appariés avant/après : mêmes caméras,
échelle, éclairage à cinq sources, matériau mat neutre et réglages.
Les images individuelles ne sont pas retouchées ; les planches ajoutent
seulement des légendes et un redimensionnement uniforme.
Les vues « avant » déjà calculées sont réutilisées après vérification exacte
de l’identité de leur scène : géométrie, normales, transformation, matériau,
lumières et monde. Leurs métadonnées de rendu originales restent intactes ;
le contrôle de réutilisation est fourni avec les images.

## Correction réellement effectuée

L’ancien raccord très court conservait une base de tête évasée, ce qui créait
une collerette visible. Il est retiré, ainsi qu’une petite bande inférieure
de la tête donneuse, puis remplacé par une transition plus progressive.
Il ne s’agit ni d’une texture masquant la jonction ni d’un objet superposé.

La limite inférieure reste **strictement celle de `dbba75e`**, à Z = 0,695 m
dans les coordonnées Blender centrées du fichier. Tous les sommets et triangles
du corps conservé sous cette limite restent identiques, y compris le cou et
la gorge déjà présents dans cette partie.

La nouvelle limite supérieure suit un plan incliné sous la mâchoire et à la
base de la nuque : `z − 0,12 × y = 0,747`. Sa hauteur réelle varie autour de
la tête ; elle ne dépasse pas **Z = 0,755161 m**. La zone de raccord occupe
donc au maximum **60,2 mm verticalement**, contre 26 mm dans la proposition
précédente. Ces valeurs sont celles de l’asset ; les pieds sont à environ
Z = −0,951 m. Le visage, les oreilles et les cheveux au-dessus de cette limite
conservent leur surface source, sans changement de taille ou de position.

Le nouveau raccord utilise des profils continus, avec des tangentes progressives
et un léger lissage angulaire limité à sa surface neuve. Ses deux bords sont
partagés avec le corps et la tête. Les normales sont raccordées localement
pour atténuer la rupture d’éclairage. Aucun lissage global du mannequin n’est
appliqué.
Ses anneaux internes utilisent 192 points régulièrement répartis, pour éviter
les triangles très fins et le pincement visible avec la distribution précédente.
Les 185 sommets du bord du corps et les 146 du bord de tête ne sont pas déplacés.

La première mise au point a révélé que la connectivité de l’ancien raccord
supportait mal sa remise en forme. Le raccord est donc **reconstruit localement**,
avec contrôle des intersections, au lieu de conserver des triangles repliés.
Les essais techniques intermédiaires ne sont pas livrés comme variantes.

## Préservation et contrôles

| Contrôle | Résultat |
| --- | --- |
| Corps conservé contre le master `dbba75e` | **45 287 sommets et 90 395 triangles identiques**, aucun déplacement ni changement de connectivité |
| Contrôle supplémentaire contre le GLB Anatomical Form d’origine | 45 102 sommets originaux et 90 117 triangles entiers préservés ; morceaux de découpe sur leurs triangles sources |
| Partie supérieure de la tête contre `dbba75e` | **13 089 triangles entiers identiques** ; surface des triangles coupés vérifiée contre le donneur |
| Visage et cheveux au-dessus du raccord | Surface conservée, sans nouvelle sculpture |
| Dimensions hors tout | Boîte englobante strictement identique |
| Jonction | Fermée, une seule composante, aucune nouvelle intersection détectée |
| GLB | Surface exportée identique au master Blender |

Les normales du corps sont transférées ; leur réencodage Blender produit un
écart vectoriel maximal d’environ **0,000404**, sans déplacement géométrique.
La légère différence éventuelle d’ombres portées entre les images ne constitue
pas une modification du corps.

La topologie héritée des sources reste conservée hors du raccord : la
caractéristique d’Euler finale reste −6 comme dans `dbba75e`. Ce n’est pas une
ouverture nouvelle ; toutes les arêtes de l’assemblage appartiennent à deux faces.

[Résultats détaillés et empreintes](m4a/meshy-marble-titan-raccord-cou/verification.json).

| Géométrie | Avant | Après |
| --- | ---: | ---: |
| Corps conservé | 90 395 | 90 395 |
| Tête retenue, hors raccord | 14 132 | 13 306 |
| Raccord | 5 929 | 6 091 |
| **Total triangles** | **110 456** | **109 792** |

Soit **664 triangles de moins (−0,60 %)**. Le GLB fait **1 978 888 octets**,
environ 1,98 Mo, avec un maillage, un matériau et aucune texture. Aucun test
de fluidité dans l’application n’est lancé.

## Lecture visuelle et limites

Sur les rendus de contrôle, la marche horizontale et l’effet de tête posée sont
nettement réduits ; le dessous de la mâchoire rejoint le cou par une surface
progressive. Le contour de profil et de trois quarts est plus continu.

Les petits reliefs et irrégularités du cou et de la tête générés par Meshy ne
sont pas tous effacés. Cette passe vise la jonction, sans polissage général de
la tête ni correction des muscles du cou. Les images restent la base de la
validation esthétique ; les contrôles géométriques ne remplacent pas ce choix.

Le corps Meshy de cette lignée n’a pas encore de segmentation musculaire.
Les anciennes six zones du mannequin précédent ne sont ni modifiées ni
transférées pendant cette tâche ; leurs fichiers et tout l’historique restent
conservés. Aucune nouvelle sélection interactive n’est développée.

[Blender, GLB, sources et reproduction](m4a/meshy-marble-titan-raccord-cou/README.md).
Attribution conservée : **Model created with Meshy — CC BY 4.0 License**,
selon la formule gratuite déclarée dans cette conversation et la
[provenance déjà documentée](m4a/meshy/LICENCE_ET_PROVENANCE.md).
Sources originales et assemblage précédent intacts, budget additionnel nul.

**Arrêt pour validation visuelle.** Application et SQLite inchangées, aucun
M4B, aucune fusion. PR #12 maintenue en brouillon.
