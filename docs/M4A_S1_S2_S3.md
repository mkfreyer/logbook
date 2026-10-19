# M4A — S1 / S2 / S3 : nouvelles constructions anatomiques

**Recommandation : S2 comme base à choisir pour la suite**, sous réserve de
validation visuelle. L1/L2/L3 sont abandonnés comme base principale et conservés
intégralement. Cette livraison reste une exploration : pas d’intégration,
SQLite, M4B, WebView, Three.js ou fusion. PR #11 en brouillon. Pas d’Astra Ultra.

![S1 / S2 / S3, trois quarts](m4a/stylized/comparaison-three-quarter.png)

[Face](m4a/stylized/comparaison-front.png) ·
[Trois quarts](m4a/stylized/comparaison-three-quarter.png) ·
[Dos](m4a/stylized/comparaison-back.png) ·
[Profil](m4a/stylized/comparaison-side.png) ·
[Pectoraux orange](m4a/stylized/comparaison-selection.png) ·
[Détail du torse](m4a/stylized/detail-torse.png) ·
[Vue d’ensemble](m4a/stylized/comparaison.png).

## Rupture avec L3 et construction

Les trois variantes partent des **vraies formes des muscles superficiels** de
l’atlas Écorché déjà audité, dérivé de BodyParts3D / Z-Anatomy. Aucun mesh L1,
L2 ou L3 n’est chargé. Ce sont trois constructions d’une même source anatomique,
pas trois assets indépendants ni trois matières appliquées au mannequin L3.
Les adaptations et rendus sont sous **CC BY-SA 4.0**, avec
[attributions et notices conservées](m4a/stylized/ATTRIBUTION.md).

Les volumes d’origine guident les éventails pectoraux, les trois parties du
deltoïde, biceps / triceps, plans scapulaires, dorsaux, vastes, ischios et mollets.
Le physique est élargi, les ventres musculaires renforcés et la taille affinée ;
les bras sont légèrement écartés pour lire les flancs. Les stries sont adoucies,
les terminaisons trop fines coupées. Des volumes abdominaux arrondis sont ajoutés
sur les grands droits. Tête neutre sans ouvertures faciales, mains, pieds, cou et
raccords articulaires sont couverts par de nouvelles formes de design.
Aucun os, organe, œil ou muscle facial n’est incorporé au résultat.

| Variante | Différence de construction et de lecture | Triangles | Objets visibles / sélectionnables | Identifiants de zones |
| --- | --- | ---: | ---: | ---: |
| **S1 — Anatomique stylisé doux** | Union de toutes les masses et du support ; reliefs fondus, silhouette un peu plus étroite. Découpe provisoire de l’enveloppe suivant la proximité des muscles sources. | **74 000** | **55 / 54** | **54** |
| **S2 — Anatomique stylisé premium** | Parties d’une même famille regroupées puis remeshées en masses arrondies ; carrure et volumes plus présents, cou neutre. Dorsaux, pectoraux et épaules restent distincts du support. | **99 946** | **53 / 52** | **52** |
| **S3 — Écorché fitness simplifié** | Davantage de pièces anatomiques séparées ; têtes musculaires et faisceaux plus lisibles, contours plus découpés et cou plus anatomique. Détails fins simplifiés. | **107 862** | **111 / 110** | **54** |

## Proximité de la référence et choix

**S2 offre le meilleur compromis** : le corps est construit comme un ensemble
musculaire, avec une lecture du dos et des jambes très différente du mannequin
lisse L3. Les deltoïdes sont des volumes anatomiques effilés, les pectoraux des
éventails et les cuisses plusieurs masses. Le cou neutre et les regroupements
réduisent l’effet médical de S3. S1 est plus doux mais perd une partie de la
séparation recherchée ; S3 montre davantage la logique d’un atlas et paraît
plus technique, avec plus de pièces et de creux.

À échelle réduite, les écarts visuels entre S2 et S3 restent modérés : ils
portent surtout sur le cou, les contours anatomiques et la structure des pièces.

La cible premium n’est toutefois **pas entièrement atteinte** : les séparations
pectoraux / abdomen / aisselles restent trop profondes par endroits, les abdos
trop réguliers, le bassin et les pieds simplifiés. Certaines jonctions donnent
encore un effet de pièces rapportées. Le visage volontairement neutre répond au
brief, sans chercher celui de la référence. Les trois silhouettes partagent une
pose un peu plus ouverte que l’image fournie. La recommandation porte sur la
**base de construction**, pas sur une validation de finition ou d’intégration.

## Structure, sélection et mobile

- **S1 : exploitable pour comparer, continuité à reprendre.** Les patches affichés
  reproduisent exactement les 74 000 faces de l’union, une fois chacune. L’enveloppe
  n’a aucun bord ouvert / non-manifold, mais comporte **3 composantes** et une
  caractéristique d’Euler **−84** : des tunnels résiduels subsistent entre les
  volumes. Les zones par proximité peuvent être fragmentées ; leur frontière orange est
  visiblement crénelée dans ce prototype. Elles ne sont pas une segmentation
  finale. Ne pas confondre surface fermée et peau nettoyée.
- **S2 : meilleure base technique de cette exploration.** Aucun bord non-manifold
  détecté sur les pièces visibles ; 52 zones nommées. Le support et les masses
  se recouvrent : ce n’est pas une peau partitionnée sans intersections.
  Structure utilisable pour une future sélection par objets, à nettoyer après
  choix. Ce n’est pas une retopologie animable ou une segmentation complète.
- **S3 : pièces exploitables visuellement, nettoyage topologique requis.**
  **1 522 bords non-manifold** subsistent sur certaines pièces sources simplifiées.
  Les 110 objets sélectionnables se rattachent à 54 zones ; plusieurs objets
  d’un même groupe devront être sélectionnés ensemble. Plus de contours et de
  surfaces internes rendent ce candidat moins rentable pour mobile.

Les noms de zones et côtés sont conservés ; les deux pectoraux deviennent orange
par changement de matériau sur les **vrais objets 3D**. Il n’existe encore aucun
moteur tactile, raycast applicatif ou surlignage 2D. Les contrôles ne détectent
aucune coordonnée non finie, triangle dégénéré au seuil mesuré ou sommet isolé.
Ils ne constituent pas un contrôle exhaustif des intersections ou de l’anatomie.

Les budgets de 74 k à 108 k triangles rendent une future adaptation iPhone
plausible, **sans démontrer la fluidité**. Nombre d’objets, surfaces cachées,
matériaux et mémoire devront être mesurés après le choix ; aucun benchmark,
export applicatif, LOD ou travail M4B n’est lancé maintenant.

## Rendus et reprise

**15 vrais PNG Blender 4.3.2 / Cycles CPU**, 720 × 1 152, 96 échantillons,
5 vues identiques par variante, même matière bleu argenté, caméra, éclairage
et fond sombre. Matière satinée opaque pour rendre les volumes comparables et
limiter le coût de calcul. Sept planches sont assemblées sans peinture ou
anatomie ajoutée en 2D. Les scènes de revue conservent les mêmes coordonnées,
faces, normales et zones que les sources.

[Sources BLEND, paramètres et reproduction](m4a/stylized/README.md) ·
[Validation de livraison](m4a/stylized/validation.json) ·
[Audit des scènes](m4a/stylized/review-validation.json) ·
[Manifeste SHA-256](m4a/stylized/manifest.json).

**Arrêt après cette publication : choisir S1, S2 ou S3 avant toute suite technique.**
