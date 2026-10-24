# M4A — Six zones fonctionnelles sur les deltoïdes P4

## Résultat et périmètre

**Six zones indépendantes sont préparées sans aucune modification géométrique.**
La référence est exclusivement [`0ab3d83`](https://github.com/mkfreyer/logbook/commit/0ab3d838c728a88f2d325edff7a6884400c9ed78) : deltoïdes P4, tête P5, gorge et corps validés.
Les sculptures rejetées `62fe3ff`, `39a8eb2` et `7a0af69` restent archivées et n'ont pas servi de base.

Cette livraison propose les **limites fonctionnelles à valider visuellement**. Elle ne certifie pas une segmentation anatomique médicale. Aucune sculpture, correction des creux, intégration applicative, modification SQLite ou opération M4B. PR #12 conservée en brouillon, sans fusion.

## Rendus pour validation

- [Planche neutre : face, profil, dos, trois quarts](m4a/ecorche-beatriz-zones-deltoides/renders/planche-neutre.png).
- [Gros plans des épaules, matériau mat neutre](m4a/ecorche-beatriz-zones-deltoides/renders/planche-epaules-neutres.png).
- [Planche colorée : six zones, vues générales](m4a/ecorche-beatriz-zones-deltoides/renders/planche-zones.png).
- [Contrôle des limites, épaules sous plusieurs angles](m4a/ecorche-beatriz-zones-deltoides/renders/planche-epaules-zones.png).
- [Même caméra : référence P4 / nouveau neutre / zones colorées](m4a/ecorche-beatriz-zones-deltoides/renders/comparatif-reference-neutre-zones.png).
- [Rendus individuels neutres](m4a/ecorche-beatriz-zones-deltoides/renders/neutral/) et [colorés](m4a/ecorche-beatriz-zones-deltoides/renders/zones/).

Rouge = antérieur ; bleu = moyen/latéral ; vert = postérieur. Gauche et droite sont les côtés anatomiques du mannequin.
Matériau mat P3/P4 conservé, caméras et éclairage symétrique d'origine, Cycles CPU, 48 échantillons, sans débruitage ni retouche des pixels.
Deux vues neutres sont recalculées pour comparaison : **leurs pixels RGB sont strictement identiques aux rendus de référence**. Les huit autres vues approuvées sont réutilisées après vérification de l'identité de géométrie et de configuration. La [provenance des images](m4a/ecorche-beatriz-zones-deltoides/renders/neutral-provenance.json) distingue ces cas.

## Délimitation anatomique proposée

Les anciens groupes de sommets sont des poids de sculpture qui se chevauchent. **Leurs maxima ne sont pas utilisés comme segmentation.**

Trois chemins longitudinaux sont construits sur les arêtes de la surface P4, à partir de repères approximatifs en 3D : origine claviculaire antérieure, région acromiale latérale, origine postérieure vers l'épine de la scapula, puis ventres superficiels et convergence distale vers l'humérus. Les coordonnées exactes et leurs projections sont consignées dans [`zones.json`](m4a/ecorche-beatriz-zones-deltoides/zones.json).

Chaque triangle est attribué au chemin le plus proche par distance sur le maillage, moyennée sur ses trois sommets. Cette construction suit la surface réelle, indépendamment de toute caméra. La correspondance des faces d'origine est réutilisée de l'autre côté pour obtenir la même partition en miroir. Les deux côtés restent à leurs coordonnées originales, y compris leur écart de symétrie préexistant de 0,000017 mm au maximum.

Les régions couvrent **toute** la surface de chaque deltoïde, y compris sa face profonde habituellement cachée. Chaque région est connectée par ses arêtes. La convergence distale commune est répartie entre les trois zones pour garantir une attribution exhaustive ; elle ne représente pas trois tendons physiquement détachés.

| Portion | Couleur de contrôle | Identifiant gauche | Identifiant droit | Triangles par épaule |
| --- | --- | --- | --- | ---: |
| Antérieure | Rouge | `deltoid.left.anterior` | `deltoid.right.anterior` | 5 082 |
| Moyenne / latérale | Bleu | `deltoid.left.lateral` | `deltoid.right.lateral` | 2 350 |
| Postérieure | Vert | `deltoid.left.posterior` | `deltoid.right.posterior` | 4 506 |

Ces nombres comprennent les faces profondes : ils ne correspondent pas à une mesure du volume ou de la taille anatomique des faisceaux.

## Structure et future sélection

Les deux objets deltoïdes sont conservés. Chacun comporte trois groupes de triangles associés à trois matériaux distincts, neutres et strictement identiques au matériau P4 au départ. Aucun volume n'est détaché et aucune surface n'est superposée.

- Dans Blender : `asset_id` de l'objet + index de matériau, correspondance `selection_regions`.
- Dans le GLB : trois primitives par deltoïde ; chaque matériau porte son identifiant stable dans `name` et `extras.zone_id`. L'identifiant est aussi ajouté aux `extras` de la primitive.
- [`selection-map.json`](m4a/ecorche-beatriz-zones-deltoides/selection-map.json) relie les six IDs aux nœuds, primitives, matériaux et triangles d'origine.
- Pour une future sélection tactile, résoudre le matériau du sous-maillage touché et son `zone_id`. Un `faceIndex` global n'est pas un identifiant stable après export. Selon le chargeur, plusieurs primitives deviennent plusieurs enfants ; les métadonnées du matériau constituent la correspondance principale.
- Chaque matériau peut être recoloré seul, y compris en orange. Les six matériaux sont indépendants. Le retour neutre restaure leurs paramètres P4 identiques ; garder leurs identifiants distincts évite de fusionner les zones lors d'un nouvel export.

**Aucun code de sélection ou d'interface Logbook n'est ajouté.** La compatibilité de structure GLB est vérifiée ; les performances sur téléphone et le comportement d'une future interface ne sont pas testés ici.

## Contrôles effectivement effectués

Le [rapport automatique](m4a/ecorche-beatriz-zones-deltoides/verification.json) compare les fichiers Blender sérialisés, puis les GLB réels :

- SHA-256 du fichier de départ vérifié contre l'asset de `0ab3d83`.
- **300/300 surfaces et topologies évaluées identiques, déplacement maximal : 0 m.**
- Coordonnées d'origine, clés de forme actives P4, UV, groupes de sommets, matrices et normales de coins conservés. Seuls les matériaux et leurs indices changent sur les deux deltoïdes.
- **298/298 autres objets et matériaux identiques**, dont tête P5, yeux, gorge et pectoraux.
- Silhouette et volumes strictement conservés ; aucune possibilité de nouveau trou ou de nouvelle intersection puisque la géométrie n'a pas changé. Les contacts préexistants P4 ne sont pas corrigés.
- 11 938 triangles par deltoïde, attribués une seule fois chacun, sans manque ni chevauchement ; une composante continue pour chaque région.
- Modification de chaque couleur isolément et retour neutre testés sans affecter les cinq autres.
- Export neutre et export de contrôle : mêmes buffers géométriques. Positions et normales exportées exactement identiques au GLB P4/P5 d'origine, indépendamment du rangement des primitives.
- Réimport des deux GLB réussi : les six matériaux/IDs sont retrouvés.

**Topologie : aucune modification.** Zéro sommet et zéro triangle ajoutés. Le mannequin reste à 300 objets et 498 058 triangles dans Blender. Le GLB compte 498 057 triangles : la même face doublonnée est omise par l'exporteur dans l'export de référence et dans ce nouvel export ; aucune omission supplémentaire.

Le GLB neutre fait 10 297 400 octets, soit environ 9,82 Mio et **16 712 octets de plus** que la référence. Il comporte 304 primitives au lieu de 300 et sept matériaux au lieu d'un. Le surcoût propre à ces zones est donc faible, sans texture ajoutée. Les ~498 000 triangles du corps complet restent toutefois un sujet d'optimisation mobile future ; aucun objectif de fluidité n'est déclaré atteint sans mesure sur appareil.

## Limites et recommandation

Les frontières suivent les arêtes existantes : **de petits crénelages sont visibles sur les gros plans colorés**, particulièrement en profil. Ce ne sont ni des incisions ni des défauts nouveaux de la surface ; ils disparaissent lorsque les matériaux repassent au neutre. Aucun découpage local supplémentaire n'a été réalisé pour privilégier la conservation exacte du modèle P4.

Les repères donnent une proposition superficielle cohérente pour une carte fitness, à valider sur les vues avant/profil/arrière. Ils ne démontrent pas la frontière anatomique exacte de chaque faisceau profond et ne doivent pas être traités comme une validation clinique.

**Recommandation : conserver cette structure à six IDs pour le contrôle fonctionnel et valider d'abord les limites colorées.** La conservation de P4 est confirmée techniquement. La précision visuelle des frontières reste la décision de cette étape. Aucune correction supplémentaire ni intégration n'est engagée après cette livraison.

## Sources utiles et droits

- [Master Blender neutre](m4a/ecorche-beatriz-zones-deltoides/ecorche-p4-p5-zones.blend).
- [GLB neutre avec six zones](m4a/ecorche-beatriz-zones-deltoides/ecorche-p4-p5-zones.glb).
- [GLB de contrôle rouge / bleu / vert](m4a/ecorche-beatriz-zones-deltoides/ecorche-p4-p5-zones-controle.glb).
- [Inventaire d'export](m4a/ecorche-beatriz-zones-deltoides/export.json).
- [Scripts reproductibles et mode d'emploi](m4a/ecorche-beatriz-zones-deltoides/README.md).

Corps : **Ecorche - Anatomy study**, Beatriz Gomez Santamaria, [source Sketchfab](https://sketchfab.com/3d-models/ecorche-anatomy-study-e402d3d541eb4b199c57d5410f5d3c57), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Adaptations Logbook et partition de surface signalées dans les métadonnées GLB. Tête/yeux P5 : Dan Ulrich / Blender Studio, Human Base Meshes v1.4.1, CC0 ; [provenance conservée](m4a/ecorche-beatriz-passe5/HEAD_SOURCE_LICENSE.md). Aucun achat, service payant ou Astra Ultra.
