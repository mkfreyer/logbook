# M4A — Retour à la tête source Marble Titan

La proposition de « raccord fondu » `7c40e5b` est **rejetée** et n’est pas
utilisée comme base géométrique. La référence est désormais la tête du GLB
Marble Titan fourni par l’utilisateur, correspondant à son image de référence.

Cette livraison conserve sa surface native : visage, cheveux, profil du menton
et dessous de la mâchoire. Elle ne reconstruit pas une masse sous le menton.

## Rendus pour validation

- [Tête de base / proposition : face, profil et trois quarts](m4a/meshy-tete-source-conservee/renders/comparatif-tete-source.png).
- [Gros plan du raccord : source / proposition](m4a/meshy-tete-source-conservee/renders/comparatif-raccord-source.png).
- [Mannequin complet](m4a/meshy-tete-source-conservee/renders/mannequin-complet.png).

La colonne « tête de base » montre **le donneur original complet**, sans coupe
ni sculpture, placé à la même échelle et à la même position que la tête montée.
Elle ne montre ni l’assemblage `dbba75e` ni le raccord fondu rejeté.
Les comparatifs utilisent les mêmes caméras, matériau mat neutre et cinq lumières.
Neuf vrais rendus Blender/Cycles sont conservés, sans retouche des images brutes.
Les planches ajoutent uniquement des légendes et un redimensionnement uniforme.

## Intervention conservatrice

Le donneur est repris directement dans
`Meshy_AI_Marble_Titan_1025022845_generate.glb`. Son ajustement uniforme et sa
position restent ceux de `dbba75e` : **aucune nouvelle mise à l’échelle**, aucune
modification du visage, de la coiffure ou des proportions de la tête.

La différence essentielle est la **conservation du menton et de son dessous
d’origine**. Les découpes précédentes passaient trop haut ; la reconstruction
du raccord fondu avait remplacé cette zone par une surface artificielle.
Ici, seuls les prolongements bas du cou donneur sont coupés, suivant deux plans
obliques sous le menton : `z − 0,20x − 0,16y = 0,698` et
`z + 0,20x − 0,16y = 0,698`, en coordonnées Blender centrées.
La surface conservée du donneur n’est ni déplacée, ni lissée, ni gonflée.

Pour joindre ce cou natif sans couper le menton, la limite du cou receveur
descend de **12 mm**, de Z = 0,695 à **0,683 m**. C’est la seule bande du corps
de `dbba75e` remplacée. Le reste du cou, la gorge sous cette limite et tout le
corps restent conservés. Le nouveau raccord est situé entre Z = 0,683 et
0,721239 m au maximum, avec un bord supérieur variable selon le tour du cou.
Il ne remonte plus vers Z = 0,755 comme la tentative rejetée.

Cette courte jonction relie des bords partagés, sans pièce superposée. Son
lissage et ses normales sont limités à la surface neuve. Le menton natif reste
devant le cou avec sa concavité d’origine ; le raccord ne comble pas cet espace.

## Contrôles réalisés

| Contrôle | Résultat |
| --- | --- |
| Scène de référence | Donneur original vérifié intégralement contre son GLB, après le seul placement uniforme hérité |
| Surface de tête conservée | **14 191 triangles sources entiers identiques** ; morceaux coupés sur leurs triangles d’origine |
| Zone de contrôle du menton / avant de la tête | **5 153 triangles vérifiés**, aucun coupé ni déformé dans cette zone |
| Partie supérieure du visage / cheveux | **13 345 triangles vérifiés**, conservés |
| Déformation des sommets sources de tête | **Aucune** |
| Corps sous Z = 0,683 | **89 798 triangles sources entiers identiques**, également comparés à `dbba75e` |
| Maillage | Fermé, orienté, une seule composante ; aucune nouvelle intersection tête/cou détectée |
| GLB | Surface identique au master Blender ; dimensions hors tout identiques à `dbba75e` |

Le contrôle du menton utilise les triangles entièrement en avant de Y = −0,065
et au-dessus de Z = 0,695 ; il est complété par la comparaison de toute la
surface donneuse conservée et des aires par triangle après les deux découpes.
Les erreurs maximales de plan sont inférieures à 0,1 µm.
[Résultats détaillés](m4a/meshy-tete-source-conservee/verification.json).

| Élément | Triangles |
| --- | ---: |
| Corps conservé, découpe comprise | 90 090 |
| Tête et partie native du cou retenues | 14 402 |
| Jonction locale | 6 096 |
| **Total** | **110 588** |

Soit **132 triangles supplémentaires (+0,12 %)** par rapport à `dbba75e`.
Le GLB fait **1 993 164 octets**, environ 1,99 Mo : un maillage, un matériau,
aucune texture. Pas de mesure de performances dans Logbook.

## Limites et arrêt

La comparaison vise l’identité de la **forme 3D de la source**, pas l’identité
pixel à pixel avec la capture fournie, dont l’éclairage et le cadrage diffèrent.
Les détails et asymétries générés par Meshy restent conservés ; aucun nouveau
polissage général n’est entrepris. Le raccord cervical et les proportions
restent soumis à la validation visuelle de l’utilisateur.

Le corps Meshy et tous les fichiers des variantes et zones antérieures restent
préservés dans leurs dossiers. Aucune segmentation ou intégration n’est lancée.
[Blender, GLB, sources et reproduction](m4a/meshy-tete-source-conservee/README.md).

Attribution conservée : **Model created with Meshy — CC BY 4.0 License**,
suivant la formule gratuite déclarée et la
[provenance existante](m4a/meshy/LICENCE_ET_PROVENANCE.md). Aucun achat, aucune
nouvelle génération ni outil payant.

**Arrêt après les rendus pour validation.** Application et SQLite inchangées,
aucun M4B, aucune fusion ; PR #12 maintenue en brouillon.
