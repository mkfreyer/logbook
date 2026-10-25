# M4A — Corps Anatomical Form, tête Marble Titan

Nouvelle copie de l’assemblage : le corps Anatomical Form est conservé et la
tête Rib Reach est remplacée par celle du fichier **Marble Titan** fourni par
l’utilisateur. Son visage et ses cheveux sont conservés, conformément à ce
nouveau choix. La variante précédente reste disponible au commit `b11223d`
et dans son [dossier dédié](m4a/meshy-assemblage-corps-tete/README.md).

## Rendus pour validation

- [Mannequin : face, profil et trois quarts](m4a/meshy-assemblage-tete-marble-titan/renders/mannequin-assemble.png)
- [Tête précédente / Marble Titan, trois angles](m4a/meshy-assemblage-tete-marble-titan/renders/comparatif-tetes.png)
- [Comparatif à l’échelle du corps](m4a/meshy-assemblage-tete-marble-titan/renders/comparatif-ensemble.png)

Douze vrais rendus Blender/Cycles : matériau mat neutre, caméras et cinq
lumières identiques avant/après. Les planches ajoutent uniquement les légendes
et un redimensionnement uniforme. Les rendus individuels sont conservés.

## Modifications réalisées

Le corps provient de `Meshy_AI_Anatomical_Form_1025014819_generate.glb` ;
ses envois successifs sont identiques à la source Meshy déjà archivée.
La nouvelle tête provient exclusivement de
`Meshy_AI_Marble_Titan_1025022845_generate.glb`.

La découpe du corps reste à **Z = 0,695 m**, dans les coordonnées Blender
centrées de la source. Le corps sous cette limite n’est ni déplacé, ni lissé,
ni redimensionné : épaules, torse, bras, mains, bassin, jambes et pieds restent
ceux du fichier utilisateur. Les éventuelles irrégularités du corps source ne
sont pas corrigées pendant cet assemblage.

La tête Marble Titan est extraite de son corps, réduite **uniformément de
2,24 %**, puis translatée, sans rotation. Sa hauteur retrouve celle du mannequin
receveur. Le visage et la chevelure ne sont pas resculptés. Un raccord cervical
local remplace la partie basse extraite : il remonte au maximum de **26 mm**
au-dessus de la découpe du corps. Sa limite supérieure inclinée conserve la
mâchoire de la tête donneuse. Les bords partagent réellement leurs sommets ;
il ne s’agit pas d’une tête posée par-dessus un corps fermé.

## Contrôles et coût géométrique

| Contrôle | Résultat |
| --- | --- |
| Sommets originaux du corps conservé | **45 102, aucun déplacé** |
| Triangles entiers du corps conservé | **90 117, coordonnées identiques** |
| Triangles traversés par la découpe | Découpés sur leur plan d’origine ; erreur maximale inférieure à 0,1 µm |
| Surface donneuse de la tête | Conforme à la source après transformation uniforme et découpe |
| Assemblage précédent de comparaison | Surface identique à son GLB publié |
| Raccord / tête | Aucune nouvelle intersection détectée |
| Fermeture | Une seule composante ; toutes les arêtes à deux faces, orientation cohérente |
| GLB exporté | Surface identique au fichier Blender |

La tête donneuse conserve ses particularités topologiques, notamment dans les
cheveux. La caractéristique d’Euler finale est **−6**, conformément à la somme
des deux surfaces retenues ; celle du corps complet source était −2. Ce contrôle
ne signale aucune ouverture au raccord et ne prétend pas réparer les détails
hérités des sources. [Mesures détaillées](m4a/meshy-assemblage-tete-marble-titan/verification.json).

| Élément | Triangles |
| --- | ---: |
| Corps conservé après découpe | 90 395 |
| Tête Marble Titan retenue | 14 132 |
| Nouveau raccord | 5 929 |
| **Assemblage final** | **110 456** |
| Assemblage précédent avec tête Rib Reach | 97 424 |

L’écart est de **+13 032 triangles (+13,38 %)**, principalement pour le visage
et les cheveux. Le GLB fait **1 990 728 octets**, soit environ **1,99 Mo** :
un maillage, un matériau, aucune texture. Aucun test de fluidité sur téléphone
n’est réalisé ; cette livraison reste une proposition d’asset, sans intégration
ni segmentation musculaire. La chevelure et le visage gardent la qualité et
les détails générés de la source ; leur rendu se juge sur les gros plans.
Le raccord est fermé géométriquement, mais une démarcation cervicale reste
perceptible en gros plan, notamment de profil : la fermeture du maillage ne
constitue pas une validation esthétique du raccord. Aucun lissage supplémentaire
du corps ou du visage n’est entrepris pour la masquer.

## Sources et arrêt

[Blender, GLB, sources et reproduction](m4a/meshy-assemblage-tete-marble-titan/README.md).
Les deux originaux et toutes les variantes précédentes sont préservés.
L’ancienne description complète de la PR est conservée dans une
[archive exacte](m4a/historique-pr12/2026-10-25-avant-marble-titan.md).

Les GLB originaux indiquent `meshy-scene`, sans licence embarquée. La formule
gratuite a été déclarée dans cette conversation ; l’adaptation conserve
**Model created with Meshy — CC BY 4.0 License**, conformément aux
[conditions Meshy](https://help.meshy.ai/en/articles/10137554-what-is-the-ownership-of-the-generated-models)
et à la [provenance existante](m4a/meshy/LICENCE_ET_PROVENANCE.md).
Aucun achat, aucune nouvelle génération ni crédit de service utilisé.

**Arrêt pour validation visuelle de cette combinaison.** Application et SQLite
inchangées ; aucun M4B, aucune fusion ; PR #12 conservée en brouillon.
