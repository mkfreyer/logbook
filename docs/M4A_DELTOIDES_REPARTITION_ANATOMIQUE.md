# M4A — Répartition anatomique proposée des six zones du deltoïde

## Proposition

Reprise exclusive de [`990201f`](https://github.com/mkfreyer/logbook/commit/990201f214c91272a5274a53c28e049670128064). La méthode de découpage continu des triangles est conservée ; **le placement des frontières est redéfini en éventail anatomique**. La surface reste celle des deltoïdes P4, avec la tête P5 et la gorge validées.

Le précédent calcul rapprochait chaque point de trois chemins longitudinaux et produisait des bandes. Le nouveau repère relie le haut de l'épaule à la convergence humérale inférieure. Les frontières s'ouvrent vers le haut et se resserrent vers le bas, avec des profils différents sur l'avant et l'arrière.

| Portion | Placement proposé |
| --- | --- |
| **Antérieure — rouge** | Région claviculaire et enveloppement antérieur. Limite courbe et oblique avec le dôme latéral, largeur variable. |
| **Moyenne / latérale — bleue** | Éventail plus large sur le sommet et le dôme latéral sous la région acromiale, se resserrant vers l'insertion inférieure. |
| **Postérieure — verte** | Couverture arrière depuis la région de l'épine scapulaire, avec enveloppement postérieur et limite propre avec le dôme. |

**Il s'agit d'une proposition anatomique de surface à valider visuellement.** Six repères approximatifs, comprenant trois attaches proximales et trois ventres superficiels, tombent dans les régions prévues. Ce contrôle de cohérence ne démontre pas à lui seul l'exactitude anatomique des frontières.

## Rendus de validation

- [Avant / après du placement : face, profil, trois quarts et arrière oblique](m4a/ecorche-beatriz-anatomie-deltoides/renders/comparatif-anatomie.png).
- [Six zones : deux épaules de face et trois quarts, profil, arrière oblique et dos](m4a/ecorche-beatriz-anatomie-deltoides/renders/controle-six-zones-anatomiques.png).
- [Neutre : comparaison directe avec P4 + P5 original `0ab3d83`](m4a/ecorche-beatriz-anatomie-deltoides/renders/comparatif-neutre-P4.png).
- [Deux épaules de face au neutre](m4a/ecorche-beatriz-anatomie-deltoides/renders/epaules-face-neutres.png).
- [Rendus individuels](m4a/ecorche-beatriz-anatomie-deltoides/renders/after/).

Même matériau mat, mêmes caméras et éclairage que `990201f`. Blender/Cycles CPU, 48 échantillons, sans débruitage ni retouche des pixels. Rouge, bleu et vert sont uniquement les couleurs de contrôle.

## Méthode et préservation de P4

Le placement utilise un repère 3D huméral : axe longitudinal, direction antérieure et direction latérale. Deux profils d'ouverture continus définissent les limites antérieure/latérale et postérieure/latérale. La portion latérale s'élargit vers le dôme supérieur ; les origines claviculaires et scapulaires restent respectivement dans les portions antérieure et postérieure. Le même repère est réfléchi sur l'autre épaule. Aucune caméra ne participe à ce calcul.

Les nouvelles frontières traversent les triangles existants par le même découpage barycentrique qu'en `990201f`. Les nouveaux points sont interpolés sur leurs faces sources, avec transfert des normales et des attributs. **Aucune sculpture, aucun déplacement des sommets d'origine, aucune nouvelle rainure.** Les anciens découpages restent une triangulation interne sans séparation physique visible.

Voir les [paramètres et repères 3D](m4a/ecorche-beatriz-anatomie-deltoides/zones.json), la [provenance barycentrique](m4a/ecorche-beatriz-anatomie-deltoides/provenance-surface.npz) et le [rapport automatique](m4a/ecorche-beatriz-anatomie-deltoides/verification.json).

- **6 395 sommets de `990201f` conservés exactement par épaule**, dont les 5 971 sommets P4 vérifiés directement contre `0ab3d83`.
- Comparaison directe avec les faces P4 par composition des deux découpages : écart de stockage maximal **0,000083 mm**. Les coordonnées barycentriques idéales restent sur la surface ; cet écart provient des deux niveaux de stockage float32.
- Couverture complète des faces sources, sans trou ni chevauchement. Maillages fermés, deux faces par arête, caractéristique d'Euler 2 ; aucune intersection entre triangles non adjacents détectée.
- Variation relative de volume inférieure à **0,000001 %**, dans les arrondis de stockage.
- **298 autres objets inchangés** : géométrie brute, normales, matériaux et modificateurs, notamment tête P5, gorge, pectoraux et reste du corps.
- Normales identiques de part et d'autre des frontières de matériaux dans Blender et dans le GLB : écart mesuré **0**.

### Précision de l'ombrage

Le réencodage Blender des normales de quelques triangles très fins atteint environ **0,10°** sur cinq coins à droite. Le seuil de contrôle de ce cas est documenté à 0,115° ; le seuil par défaut de l'outil commun reste inchangé pour les anciennes livraisons. Les contrôles de géométrie, couverture et coutures restent actifs.

Les rendus neutres contrôlés ne montrent pas de couture ou de changement perceptible du relief. Sur les comparatifs profil et trois quarts avec `990201f`, moins de **0,014 % des pixels** diffèrent, avec un écart moyen inférieur à 0,0001 niveau sur 255 et un maximum isolé de 3 niveaux. Les comparaisons directes avec les rendus P4 originaux sont également consignées dans le [relevé des images](m4a/ecorche-beatriz-anatomie-deltoides/renders/comparisons.json). **L'image neutre n'est pas déclarée strictement identique pixel par pixel.**

## Six IDs et coût

Les IDs suivants sont conservés sans changement :

| Portion | Gauche | Droite |
| --- | --- | --- |
| Antérieure | `deltoid.left.anterior` | `deltoid.right.anterior` |
| Moyenne | `deltoid.left.lateral` | `deltoid.right.lateral` |
| Postérieure | `deltoid.left.posterior` | `deltoid.right.posterior` |

Six matériaux indépendants, trois primitives par deltoïde, couleur isolée et retour neutre testés. Correspondance dans [`selection-map.json`](m4a/ecorche-beatriz-anatomie-deltoides/selection-map.json), `material.name`, `material.extras.zone_id` et `primitive.extras.zone_id`. Les deux GLB sont réimportés et contrôlés. Les indices numériques de faces sont renouvelés ; les IDs sémantiques restent stables.

| Mesure | Droite | Gauche |
| --- | ---: | ---: |
| Sommets avant → après | 6 395 → 6 851 | 6 395 → 6 853 |
| Triangles avant → après | 12 786 → 13 698 | 12 786 → 13 702 |
| Faces sources redécoupées | 444 | 446 |

Le même repère anatomique est appliqué en miroir. Les quelques faces d'écart découlent du découpage des triangulations existantes et des arrondis ; aucun côté n'est resculpté pour égaliser ces comptes.

**+1 828 triangles au total (+0,37 % par rapport à `990201f`)**, soit 501 582 triangles Blender et 501 581 exportés, avec la même face doublonnée préexistante omise par l'exporteur. La structure reste à 300 objets, 304 primitives et 7 matériaux. GLB neutre : **10 372 220 octets**, soit **+35 080 octets** (~34,3 Kio), sans texture ajoutée. Le surcoût propre à cette révision est faible ; aucune performance mobile n'est déclarée mesurée, et le modèle complet reste à optimiser ultérieurement.

## Livraison et arrêt

[Master Blender](m4a/ecorche-beatriz-anatomie-deltoides/ecorche-p4-p5-zones.blend) · [GLB neutre](m4a/ecorche-beatriz-anatomie-deltoides/ecorche-p4-p5-zones.glb) · [GLB coloré](m4a/ecorche-beatriz-anatomie-deltoides/ecorche-p4-p5-zones-controle.glb) · [Sources et reproduction](m4a/ecorche-beatriz-anatomie-deltoides/README.md).

**Recommandation : examiner cette répartition en éventail pour remplacer les bandes de `990201f`.** La technique de découpage et la conservation de P4 sont contrôlées ; la validation du placement anatomique reste ouverte.

Arrêt après ces rendus. Aucune intégration Logbook, modification SQLite, M4B ou fusion. PR #12 conservée en brouillon ; tous les modèles antérieurs sont préservés. Aucun achat, service payant ou Astra Ultra.

Corps : **Ecorche - Anatomy study — Beatriz Gomez Santamaria**, [Sketchfab](https://sketchfab.com/3d-models/ecorche-anatomy-study-e402d3d541eb4b199c57d5410f5d3c57), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Adaptation Logbook et nouvelle répartition des zones signalées dans les GLB. Tête/yeux : **Dan Ulrich / Blender Studio, Human Base Meshes v1.4.1**, CC0 ; [provenance](m4a/ecorche-beatriz-passe5/HEAD_SOURCE_LICENSE.md).
