# M4A — Corps Anatomical Form et tête Rib Reach

Assemblage des deux GLB fournis par l’utilisateur, sur une copie, pour validation.

- **Corps :** `Meshy_AI_Anatomical_Form_1025014819_generate.glb`.
- **Tête :** `Meshy_AI_Rib_Reach_Exercise_In_1025014903_generate.glb`.

Le dernier envoi du corps est identique au précédent. Son SHA-256 est aussi
identique à la source Meshy déjà archivée dans le dépôt ; ce fichier original
est réutilisé, sans modification ni duplication inutile.

## Rendus pour validation

- [Mannequin assemblé : face, profil, trois quarts](m4a/meshy-assemblage-corps-tete/renders/mannequin-assemble.png)
- [Comparatif des têtes et du raccord, trois angles](m4a/meshy-assemblage-corps-tete/renders/comparatif-tetes.png)
- [Avant / après à l’échelle du mannequin](m4a/meshy-assemblage-corps-tete/renders/comparatif-ensemble.png)

Douze vrais rendus Blender/Cycles : même matériau mat neutre, mêmes caméras,
mêmes cinq lumières et mêmes paramètres avant/après. Les images individuelles
ne sont pas retouchées. Les planches ajoutent seulement des légendes et un
redimensionnement uniforme.

## Assemblage réalisé

Chaque GLB contient un maillage unique, sans matériau ni texture embarqués.
Le donneur contient aussi des éléments flottants autour du personnage : ils
sont exclus. Seule la région de sa tête sans visage est prélevée.

La tête d’origine du corps est retirée à une limite cervicale située à
**Z = 0,695 m**, dans les coordonnées Blender centrées du fichier source.
Cette valeur n’est pas une hauteur mesurée depuis le sol : les pieds sont à
environ Z = −0,951 m. Le corps receveur n’est ni déplacé, ni redimensionné,
ni lissé, ni remaillé.

La tête donneuse est mise à l’échelle **uniformément ×1,657**, puis translatée,
sans rotation, pour retrouver la hauteur totale du mannequin. Sa surface
supérieure est conservée après cette transformation. Le bas de sa région
cervicale, qui s’évasait vers ses propres épaules, est remplacé par une
**courte surface de raccord** remontant au maximum de Z = 0,695 à 0,7395 m,
soit 44,5 mm. Sa limite supérieure est inclinée sous la mâchoire afin de
conserver davantage le bas de la tête donneuse ; sa hauteur varie autour du cou.
Cette jonction partage les sommets des deux bords : pas de tête simplement
superposée sur un corps fermé. Les normales sont raccordées localement.

Les pectoraux, épaules, bras, mains, ventre, bassin, jambes et pieds du fichier
corps restent ceux de la source fournie. Leurs détails et irrégularités ne sont
pas corrigés pendant cet assemblage.

## Vérifications indépendantes

| Contrôle | Résultat |
| --- | --- |
| Sommets du corps conservé | 45 102 vérifiés, aucun déplacement |
| Triangles d’origine entièrement sous la limite | 90 117, coordonnées identiques |
| Triangles traversés par la découpe | Subdivisés sur leurs surfaces d’origine, erreur maximale de plan inférieure à 0,1 µm |
| Surface supérieure de la tête | Provenance donneuse vérifiée après mise à l’échelle uniforme et translation |
| Raccord et tête | Aucune nouvelle intersection détectée |
| Fermeture du maillage | Toutes les arêtes à deux faces, une seule composante connectée |
| Topologie générale | Caractéristique d’Euler inchangée ; les particularités du corps source ne sont pas réparées |
| GLB | Chaque triangle exporté correspond exactement à la surface du Blender |

Le contrôle du corps compare aussi les aires conservées **par triangle source**,
y compris les morceaux découpés : il ne repose pas seulement sur une vue ou
sur une comparaison de boîtes englobantes. La surface de la tête est comparée
aux triangles du donneur transformé.

[Résultats et empreintes détaillés](m4a/meshy-assemblage-corps-tete/verification.json).

| Géométrie | Triangles |
| --- | ---: |
| Corps complet d’origine, tête comprise | 95 426 |
| Corps après retrait de la tête et découpe de jonction | 90 395 |
| Tête donneuse retenue | 1 177 |
| Nouvelle surface de raccord | 5 852 |
| Assemblage final | **97 424** |

Soit **+1 998 triangles (+2,09 %)** par rapport au premier fichier complet.
Le GLB fait environ **1,76 Mo**, un maillage, un matériau, aucune texture. Aucun test
de performances dans Logbook ni optimisation globale n’est lancé.

## Sources, licence et limites

[Blender, GLB, source donneuse et reproduction](m4a/meshy-assemblage-corps-tete/README.md).
Les deux originaux sont préservés. Les fichiers générés par Meshy n’embarquent
pas eux-mêmes de licence ; la formule gratuite a été déclarée dans cette
conversation. L’assemblage conserve l’attribution **Model created with Meshy —
CC BY 4.0 License** et indique les modifications, conformément à la
[documentation Meshy vérifiée](https://help.meshy.ai/en/articles/10137554-what-is-the-ownership-of-the-generated-models).
Aucun achat, aucune nouvelle génération et aucun crédit de service utilisé.

Le raccord et les proportions de la tête restent une proposition à juger sur
les gros plans. L’anatomie générée du corps n’est pas médicalement validée.
Aucune segmentation musculaire n’est réalisée ou transférée sur cette nouvelle
base. Les mannequins et zones des essais précédents restent disponibles dans
leurs dossiers et dans l’historique.

**Arrêt pour validation visuelle.** Application et SQLite inchangées, aucun
M4B, PR #12 conservée en brouillon, aucune fusion.
