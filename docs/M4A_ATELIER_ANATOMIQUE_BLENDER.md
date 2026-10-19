# M4A — Atelier anatomique local, reconstruction assistée dans Blender

19 octobre 2026 · [PR #11 en brouillon](https://github.com/mkfreyer/logbook/pull/11) ·
reprise depuis `0715368`, historique intégral conservé.

**Verdict : l’atelier est techniquement préparé et vérifié ; la faisabilité du
rendu premium n’est pas démontrée. Une sculpture/retopologie manuelle compétente
reste nécessaire.** Je ne peux pas garantir cette intervention artistique dans
cet environnement de commandes Blender, sans outil de sculpture interactive.
La voie de repli demandée est donc livrée : scène éditable, sources intactes,
identités, repères de raccord et guide exécutable. Aucun D3/D4, aucune nouvelle
variation procédurale présentée comme une sculpture aboutie.

## Livrables à reprendre

- **[Fichier Blender autonome](m4a/bp3d-atelier-local/atelier-pectoraux-deltoide.blend)**,
  préparé et contrôlé dans Blender 4.3.2, sans scripts de démarrage à autoriser.
- **[Guide de sculpture et retopologie étape par étape](m4a/bp3d-atelier-local/GUIDE_SCULPTURE.md)** :
  outils, protection des attaches, gestion des portions, îlots, raccords et critères d’arrêt.
- **[Identifiants lisibles](m4a/bp3d-atelier-local/IDENTIFIANTS.md)** et
  [manifeste exact FMA/BP/FJ](m4a/bp3d-atelier-local/identites.json).
- **[Quinze OBJ originaux, archive autonome](m4a/bp3d-atelier-local/sources-originales.zip)**,
  non retouchés et contrôlés par SHA-256, avec manifeste et attribution.
- [Contrôles de la scène](m4a/bp3d-atelier-local/controle-scene.json),
  [reproduction indépendante](m4a/bp3d-atelier-local/reproduction-verifiee.json),
  [instructions de reproduction](m4a/bp3d-atelier-local/README.md).

Aucun rendu « après » n’est publié : aucune passe de sculpture artistique
convaincante n’a été réalisée. Des vues internes de diagnostic ont seulement
contrôlé le cadrage des sources et la sélection ; elles ne sont pas des résultats
premium et ne remplacent pas la comparaison esthétique demandée après sculpture.

## Périmètre anatomique exact

Trois muscles logiques, **neuf portions distinctes**, **26 398 triangles locaux** :

| Identité logique | Portions originales conservées | FMA correspondants |
| --- | --- | --- |
| `pectoralis-major-left` | `FJ1447M` claviculaire ; `FJ1464M` sternocostale ; `FJ1446M` abdominale | `FMA34691`, `FMA79980`, `FMA45875` |
| `pectoralis-major-right` | `FJ1447` claviculaire ; `FJ1464` sternocostale ; `FJ1446` abdominale | `FMA34690`, `FMA79979`, `FMA45874` |
| `deltoid-left` | `FJ1468M` claviculaire ; `FJ1467M` acromiale ; `FJ1513M` spinale | `FMA34681`, `FMA34683`, `FMA34685` |

Six objets de contexte proviennent des mêmes tables et de la même archive :
clavicules gauche/droite, manubrium, corps du sternum, scapula gauche et humérus
gauche. Ils sont affichés en fil de fer, protégés de la sélection et exclus du
rendu. Les tissus ou muscles adjacents non inclus ne sont pas reconstruits.
Leur absence ne doit pas être interprétée comme un trou anatomique à remplir
par une forme inventée. Aucune peau, tête B+, sphère ou ellipsoïde musculaire.

Les deux tables IS-A épinglées, les correspondances de l’audit et l’archive
officielle déjà acquise sont réutilisées. Les sept fichiers sources ont été
revérifiés localement. L’archive officielle reste celle de 142 903 898 octets,
SHA-256 `40665852c49f218326590e204db91064a1ecfc3c6f8cbd7bbbcaac62c7cd409e`.
Aucune nouvelle source anatomique n’est importée.

## Ce que contient réellement la scène

`01_SOURCES` conserve les neuf meshes d’origine en coordonnées natives, avec
indices et positions importés sans déformation. Leur matrice applique uniquement
la translation et l’échelle uniformes du cadrage audité. Le ZIP préserve les OBJ
byte pour byte, y compris en-têtes et normales originales ; il est l’autorité de
restauration, Blender stockant les positions en précision simple.

`00_ATELIER` contient neuf datablocks indépendants, classés en trois collections.
Les positions exactement identiques sont soudées **à l’intérieur de chaque OBJ**
pour permettre l’édition. Les coordonnées normalisées et la géométrie des faces
restent celles de la source. Aucune fusion entre portions, déplacement de ventre
musculaire, décimation, Voxel Remesh, peau de soutien ou union globale.

Les shape keys `VOLUME_MANUEL` et `RACCORDS_MANUELS` sont initialement identiques
à Basis, valeurs nulles : ce sont des emplacements pour une vraie intervention,
pas des sculptures déjà effectuées. Des groupes `DIAG_ILOT_…` permettent
l’inspection de chaque composante ; aucun fragment source n’a été supprimé.

La scène conserve **la pose et les volumes anatomiques sources**. Elle ne prétend
pas fournir la pose ni les volumes athlétiques définitifs de la référence.
Changer ces proportions proprement nécessitera le travail local décrit dans le
guide, en préservant les attaches. Le fichier ne comprend aucun rig.

Trois caméras fixes — face, trois quarts et détail — et un éclairage bleu nuit
commun sont prêts pour une future comparaison source/travail. Le matériau est
bleu argenté satiné ; il ne simule pas des fibres ou de nouveaux muscles.
Le gros plan est un outil d’atelier ; aucune décision de zoom applicatif n’est implémentée.
La référence du chat a été consultée et reste externe, sans texture ou image générée substituée.

## Raccords et défauts constatés

Les Empty de [raccords-a-reprendre.json](m4a/bp3d-atelier-local/raccords-a-reprendre.json)
orientent l’inspection vers sternum, clavicule gauche, voisinage delto-pectoral,
humérus, pli axillaire antérieur et portion acromiale du deltoïde. **Ce sont des
repères géométriques approximatifs**, non des points d’attache anatomiques validés.
Le guide demande de les replacer avant toute protection ou déformation.

La latéralité et l’orientation concordent avec l’audit : +X gauche anatomique,
−Y avant, +Z haut. Les positions relatives d’origine sont conservées ; bornes,
centroïdes et volumes signés sont mesurés. Les tables nomment les structures mais
ne fournissent ni insertions annotées ni champ de fibres : leur justesse clinique
ne peut pas être déduite du nom FMA ou de la proximité d’une surface osseuse.
Les volumes signés sont indicatifs, en unités de scène, sans mesure physique garantie.

Le diagnostic rend explicite un obstacle auparavant masqué par les unions :
les portions ne sont pas toutes des volumes uniques.

| Portion | Îlots après soudure exacte |
| --- | ---: |
| Pectoral claviculaire, chaque côté | 13 |
| Pectoral sternocostal, chaque côté | 7 |
| Pectoral abdominal, chaque côté | 3 |
| Deltoïde claviculaire gauche | 1 |
| Deltoïde acromial gauche | 4 |
| Deltoïde spinal gauche | 20 |

Beaucoup d’îlots n’ont que 3 à 6 sommets ; la portion sternocostale possède aussi
une seconde composante de 402 sommets. Ils sont conservés et étiquetés pour revue.
Le contrôle trouve zéro bord ouvert, zéro arête non-manifold et zéro triangle
sous le seuil de dégénérescence sur ces copies, mais cela ne prouve pas une bonne
surface de sculpture ou l’absence de fragments très minces.
Des candidats de contact BVH subsistent entre portions d’un même muscle. Leur
nombre est publié sans les confondre avec un test précis de collision : les
superpositions et jonctions devront être inspectées manuellement.

Les volumes sources ont déjà un éventail musculaire identifiable, mais leurs
épaisseurs, raccords entre portions et transitions vers l’épaule ne constituent
pas le modèle fitness premium de la cible. Les corrections exigent de distinguer
ventres, attaches, bords de surface et faces profondes. Une nouvelle union globale
ou un réglage automatique de volume réintroduirait le problème D1/D2.

## Sélection indépendante et limites mobiles

Chaque portion porte `muscle_id`, `source_element_id`, `fma`, nom anatomique et
SHA-256 source. Les scènes `02_DEMO_PEC_G`, `03_DEMO_PEC_D`,
`04_DEMO_DELTOIDE_G` activent respectivement **les trois portions entières** du
muscle choisi en orange. Les six autres restent bleues. Les matériaux sont
attribués par objet, sans masque de faces projeté ou débordement de label vers
un muscle voisin. Les trois cas sont contrôlés indépendamment.

La discontinuité géométrique des sources reste visible entre certains morceaux ;
la sélection complète ne démontre pas une surface orange esthétiquement continue.
Les démonstrations partagent les meshes éditables ; elles refléteront une sculpture
à topologie fixe, mais de nouveaux objets retopologisés devront être raccordés
explicitement aux identités et scènes de démonstration.

Le volume de géométrie locale n’établit pas un budget pour le corps entier.
Aucun export de production, retopologie finale, bake de normales, moteur tactile,
WebView/Three.js, mesure mémoire ou test iPhone. Aucun tonnage, série ou part de
volume d’entraînement n’est branché. La lecture mobile du corps entier restera
à évaluer après une vraie validation artistique locale.

## Vérification, coût et arrêt

Le contrôleur vérifie les quinze OBJ conservés, les coordonnées et indices bruts,
l’indépendance des datablocks source/travail, la soudure exacte par OBJ, les
shape keys vides, les groupes d’îlots, la sélection des trois muscles et l’absence
de modificateurs, bibliothèques liées, images externes ou pilotes de démarrage.
Le guide présent dans Blender correspond au fichier Markdown livré.

Une nouvelle session Blender a reconstruit la scène **depuis le seul ZIP local**,
sans l’archive complète ou les OBJ extraits auparavant. Les données de géométrie,
identité et sélection sont identiques ; les SHA du conteneur `.blend` peuvent
varier entre sauvegardes. La reproduction est vérifiée, pas la sculpture.

**Recommandation : reprendre ce fichier avec le guide pour une intervention
manuelle locale compétente, puis juger le résultat avant toute extension.**
Je n’engage pas cette suite et ne revendique aucun prototype artistique réussi.
Un niveau de calcul supérieur ne remplace pas cette intervention ; aucun Astra
n’a été utilisé. Budget d’acquisition : **0 €**, aucun achat ni outil payant.

[Attribution et conditions applicables](m4a/bp3d-atelier-local/ATTRIBUTION.md) :
BodyParts3D/DBCLS, CC BY 4.0 déclarée actuellement, anciens en-têtes CC BY-SA 2.1
Japan conservés ; scène adaptée proposée sous CC BY-SA 4.0. Le code applicatif
n’est pas relicencié. Tous les travaux précédents restent conservés.
**PR #11 en brouillon ; aucune intégration, SQLite, M4B ou fusion. Arrêt pour validation.**
