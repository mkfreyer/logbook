# M4C — cartographie et prototype biceps/triceps

**Quatre zones expérimentales à valider, sans intégration iPhone.** La branche
part de `d552e23`. Les huit sélections existantes sont validées sur l'iPhone ;
leurs masques, contours, IDs et ressources interactives restent intacts.

## Inventaire

[Inventaire complet des territoires superficiels proposés](M4C_INVENTAIRE_MUSCLES_SUPERFICIELS.md) :
33 paires candidates, avec noms français, emplacement, IDs, lisibilité et limites.
Les quatre zones de cette livraison en font partie ; les 62 autres territoires
ne sont pas segmentés. Le catalogue initial compte 15 exercices dans huit
familles ; il est examiné en lecture seule, sans lien exercice→muscle ni statistiques.

| Code | ID expérimental | Nom |
| --- | --- | --- |
| 9 | `biceps.left` | Biceps brachial gauche |
| 10 | `biceps.right` | Biceps brachial droit |
| 11 | `triceps.left` | Triceps brachial gauche |
| 12 | `triceps.right` | Triceps brachial droit |

Les codes 1–8 et leurs noms précédents sont conservés dans le
[registre des douze zones](m4c/meshy-bras-prototype/registry-twelve.json).
Les IDs proposés pour les lots suivants restent déclaratifs.

## Rendus de validation

- [Mannequin entier de face](m4c/meshy-bras-prototype/renders/face-complete.png)
  et [de dos](m4c/meshy-bras-prototype/renders/dos-complet.png).
- Biceps : [gauche](m4c/meshy-bras-prototype/renders/biceps-gauche.png),
  [droit](m4c/meshy-bras-prototype/renders/biceps-droit.png),
  [comparaison gauche/droite](m4c/meshy-bras-prototype/renders/comparatif-biceps.png).
- Triceps : [gauche](m4c/meshy-bras-prototype/renders/triceps-gauche.png),
  [droit](m4c/meshy-bras-prototype/renders/triceps-droit.png),
  [comparaison gauche/droite](m4c/meshy-bras-prototype/renders/comparatif-triceps.png).
- Profils : [gauche](m4c/meshy-bras-prototype/renders/profil-bras-gauche.png),
  [droit](m4c/meshy-bras-prototype/renders/profil-bras-droit.png),
  [côte à côte](m4c/meshy-bras-prototype/renders/comparatif-profils.png).
- [Quatre nouvelles zones séparément en orange](m4c/meshy-bras-prototype/renders/planche-quatre-zones.png).
- [Rendu neutre](m4c/meshy-bras-prototype/renders/neutre-complet.png)
  et [contrôle neutre avant/après](m4c/meshy-bras-prototype/renders/controle-neutre.png).

Chaque gros plan individuel active uniquement son muscle. Les vues générales
et de profil activent les quatre nouveaux masques pour voir leur couverture.
Les huit anciens masques restent grisés sur ces images. Les comparatifs
réfléchissent uniquement l'image droite pour rapprocher les angles ; aucune
texture UV n'est retournée. Les rendus sont produits dans Blender/Cycles avec
le matériau mat neutre, sans repeindre les pixels du modèle.

## Méthode et sources

Les repères sont posés séparément sur les deux côtés, projetés par rayons sur
les vrais triangles, puis convertis dans un repère axial/angulaire propre à
chaque bras. Les centres suivent les sections réelles du bras, situé en arrière
du torse sur cette pose. Les biceps suivent les creux visibles en face ; la
frontière fermée des triceps associe repères arrière et profil pour inclure la
portion latérale. Les courbes sont régulières et reprojetées sur la surface.

Les UV historiques ne couvrent pas le bas du bras jusqu'au coude. Un **second jeu
UV expérimental**, `M4C_ARMS_UV`, est donc ajouté sur une copie. Le jeu
`M4C_SURFACE_UV` et ses huit masques restent identiques. Le nouvel atlas ID L8
contient seulement les codes 9–12 ; un atlas RGBA contient les quatre couvertures
antialiasées. Les données indiquent explicitement quel jeu UV utiliser.

- [Blender éditable](m4c/meshy-bras-prototype/meshy-bras-prototype.blend), avec
  images embarquées, douze contrôles `SHOW::` / `COLOR::` et guides 3D cachés.
  Régler un seul `SHOW` à 1 pour une sélection indépendante ; tous à zéro pour le neutre.
- [Textures PNG](m4c/meshy-bras-prototype/textures/),
  [courbes 3D et repères](m4c/meshy-bras-prototype/surface-guides.json),
  `arms-uv-binding.npz` et échantillons de surface.
- [README de reproduction](m4c/meshy-bras-prototype/README.md).

Aucune sculpture, subdivision, modification de sommet ou de triangle. Aucun
masque des propositions rejetées n'est réutilisé. Source : Meshy `e45e5d8`,
CC BY 4.0, adaptation Logbook ; attribution conservée dans le Blender source.

## Limites et conflits observés

- Le relief permet de proposer les territoires globaux. Il ne permet pas de
  séparer sûrement les deux chefs du biceps ou les trois chefs du triceps.
  Chaque masque regroupe donc la surface visible du groupe ; les origines
  cachées, le brachial et les tendons distaux ne sont pas ajoutés artificiellement.
- Les repères proximaux des triceps rencontrent des territoires déjà attribués
  aux deltoïdes moyens/postérieurs. Le masque triceps est **limité au neutre** :
  2 789 échantillons UV couverts sont bloqués à gauche, 2 383 à droite, marge
  comprise. Les contacts directs concernent les codes 4/5 et 7/8. Une marge
  de sécurité de 1,5 mm et un raccord progressif jusqu'à 2,5 mm sont conservés.
  Ces décomptes ne sont pas des surfaces anatomiques. Les huit masques ne changent pas.
- Aucun conflit détecté pour les deux guides biceps. Le
  [rapport de conflits](m4c/meshy-bras-prototype/conflicts.json) donne les décomptes.
- Les deux bras présentent des différences de forme. Les contours sont adaptés
  à chaque surface, sans imposer une symétrie UV ou géométrique artificielle.
- Ce POC nécessite deux atlas d'identification. Le visualiseur actuel ne gère
  que l'atlas validé des huit zones : **aucune compatibilité interactive des douze
  zones sur iPhone n'est revendiquée ici**. L'intégration devra adapter le pipeline
  et organiser les UV/atlas des futurs lots. Les courbes en coordonnées 3D
  permettent de recalculer les masques sans resculpter les muscles.
- Un atlas L8 2 048² représente 4 Mio bruts ; en cas de conservation des deux
  atlas, les IDs représenteraient 8 Mio CPU et 8 Mio GPU, plus le second jeu UV.
  Le format et la résolution mobiles restent à valider ultérieurement. Aucun
  coût n'est ajouté à l'application actuelle, dont les ressources sont inchangées.

## Contrôles

- [Vérification indépendante](m4c/meshy-bras-prototype/verification.json) :
  huit PNG et atlas historiques identiques octet pour octet, douze IDs sans collision.
- [Continuité des huit zones historiques](m4c/meshy-bras-prototype/continuity-existing.json)
  et [des quatre nouvelles](m4c/meshy-bras-prototype/continuity-arms.json) :
  une composante par zone après raccord des coutures UV, aucun trou fermé détecté.
- Aucun recouvrement entre nouveaux masques ni avec les huit zones validées sur
  428 150 échantillons actifs indépendants de surface. Les contrôles utilisent
  des points barycentriques, y compris près des coutures, et non les seuls pixels
  qui ont servi au calcul des masques. Cela reste un contrôle échantillonné.
- [Quatre vrais raycasts sur le maillage](m4c/meshy-bras-prototype/picking-audit.json)
  : chaque ID proposé est résolu indépendamment sur une surface auparavant neutre.
- [Préservation Blender](m4c/meshy-bras-prototype/blender-preservation.json) :
  positions, indices, normales et UV0 identiques. **110 588 triangles, zéro ajout,
  déplacement maximal des sommets nul.** Les PNG neutres avant/après sont identiques.
- Les 613 fichiers déjà suivis à `d552e23` restent identiques. L'application,
  Expo SDK 58, SQLite et le catalogue ne sont pas modifiés. Les branches des
  PR #17, #18 et #19 restent intactes ; la PR #18 demeure à `35bb8ed`.

Les contrôles ci-dessus ne remplacent pas la validation anatomique visuelle.
**Arrêt après cette proposition des quatre bras.** Aucun autre muscle n'est
segmenté, aucun lien avec les exercices/statistiques, aucune intégration iPhone
et aucune fusion de PR. Budget additionnel : 0 €.
