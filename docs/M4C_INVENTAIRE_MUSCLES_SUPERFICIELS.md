# M4C — inventaire des principaux territoires superficiels restants

Base : `d552e23`, huit zones validées conservées. Cet inventaire propose **33 paires / 66 territoires** encore absents à cette base. Seuls les quatre biceps/triceps sont créés ici ; les 62 autres restent des propositions à examiner dans les lots suivants.

Le catalogue initial contient **15 exercices, huit familles** : Pectoraux (3), Dos (3), Quadriceps (2), Ischio-jambiers (2), Épaules (2), Biceps (1), Triceps (1), Abdominaux (1). Les catégories sont des textes libres, pas une nomenclature anatomique. Les exercices personnalisés de la base utilisateur ne sont ni lus ni modifiés. Aucun lien exercice→zone, coefficient de volume ou statistique n’est développé.

Les IDs 1–8 et leurs noms existants restent réservés. Les nouveaux IDs proposés ci-dessous sont distincts et tiennent dans un atlas L8 (maximum proposé : 74). Les codes futurs ne sont pas ajoutés au visualiseur.

## Bras

| Groupe / emplacement | IDs proposés gauche et droit | Lisibilité et limites |
| --- | --- | --- |
| **Biceps brachial** — Face antérieure du bras, sous le deltoïde, avant le coude. | `biceps.left` / `biceps.right`<br>Codes 9 / 10 | Bonne pour le ventre global ; chefs long/court non séparables de façon fiable. **POC.** |
| **Triceps brachial** — Face postérieure et externe du bras, vers le tendon du coude. | `triceps.left` / `triceps.right`<br>Codes 11 / 12 | Bonne pour le groupe ; portion médiale profonde et trois chefs non isolés. **POC.** |
| **Brachial** — Bandes latérales/distales entre biceps et triceps, au-dessus du coude. | `brachialis.left` / `brachialis.right`<br>Codes 13 / 14 | Moyenne : bande visible, limite exacte avec le biceps peu marquée. **Ultérieur.** |

## Avant-bras

| Groupe / emplacement | IDs proposés gauche et droit | Lisibilité et limites |
| --- | --- | --- |
| **Brachio-radial** — Relief externe proximal de l’avant-bras, côté pouce. | `brachioradialis.left` / `brachioradialis.right`<br>Codes 15 / 16 | Bonne pour le relief global ; raccord au coude à vérifier en rotation. **Ultérieur.** |
| **Fléchisseurs superficiels de l’avant-bras** — Face palmaire/antérieure, du coude au poignet. | `forearm.left.flexors` / `forearm.right.flexors`<br>Codes 17 / 18 | Groupe fonctionnel : les muscles individuels et tendons ne sont pas tous distincts. **Ultérieur.** |
| **Extenseurs superficiels de l’avant-bras** — Face dorsale/postérieure, du coude au poignet. | `forearm.left.extensors` / `forearm.right.extensors`<br>Codes 19 / 20 | Groupe fonctionnel : ne pas inventer une séparation de chaque tendon. **Ultérieur.** |

## Dos

| Groupe / emplacement | IDs proposés gauche et droit | Lisibilité et limites |
| --- | --- | --- |
| **Trapèze supérieur** — Du cou vers le sommet des épaules. | `trapezius.left.upper` / `trapezius.right.upper`<br>Codes 21 / 22 | Volume lisible, origine cervicale simplifiée ; ne pas altérer le cou validé. **Priorité suivante possible.** |
| **Trapèze moyen** — Haut du dos, entre rachis et omoplate. | `trapezius.left.middle` / `trapezius.right.middle`<br>Codes 23 / 24 | Moyenne : subdivisions du trapèze peu matérialisées, frontière fonctionnelle à valider. **Ultérieur.** |
| **Trapèze inférieur** — Triangle inférieur du haut du dos vers le rachis thoracique. | `trapezius.left.lower` / `trapezius.right.lower`<br>Codes 25 / 26 | Moyenne : transition vers les dorsaux graduelle. **Ultérieur.** |
| **Grand dorsal** — Large aile latérale et inférieure du dos, jusqu’au pli axillaire postérieur. | `latissimus.left` / `latissimus.right`<br>Codes 27 / 28 | Bonne pour l’aile ; raccord grand rond/triceps plus ambigu. **Priorité suivante possible.** |
| **Grand rond** — Sous le deltoïde postérieur, bord externe de l’omoplate. | `teres_major.left` / `teres_major.right`<br>Codes 29 / 30 | Partiel : très proche des dorsaux et du triceps ; bornes à contrôler. **Ultérieur.** |
| **Infra-épineux** — Partie postérieure de l’omoplate, sous son épine. | `infraspinatus.left` / `infraspinatus.right`<br>Codes 31 / 32 | Moyenne/faible : relief scapulaire stylisé, zone partiellement masquée par le deltoïde. **Optionnel.** |
| **Érecteurs du rachis** — Colonnes lombaires de part et d’autre de la colonne. | `erector_spinae.left` / `erector_spinae.right`<br>Codes 33 / 34 | Moyenne : groupe superficiel, pas de subdivision multifides/longissimus. **Ultérieur.** |

## Abdomen

| Groupe / emplacement | IDs proposés gauche et droit | Lisibilité et limites |
| --- | --- | --- |
| **Grand droit de l’abdomen** — De part et d’autre de la ligne médiane abdominale. | `rectus_abdominis.left` / `rectus_abdominis.right`<br>Codes 35 / 36 | Bonne : tablettes lisibles ; une région par côté, pas un muscle par tablette. **Priorité suivante possible.** |
| **Oblique externe** — Flancs, sous les côtes et vers le bassin. | `obliques.left.external` / `obliques.right.external`<br>Codes 37 / 38 | Bonne globalement ; limites basses simplifiées par la finition du bassin. **Ultérieur.** |
| **Dentelé antérieur** — Digitations latérales du thorax, sous les pectoraux. | `serratus_anterior.left` / `serratus_anterior.right`<br>Codes 39 / 40 | Reliefs visibles, plusieurs digitations regroupées ; respecter les pectoraux validés. **Ultérieur.** |

## Bassin et fessiers

| Groupe / emplacement | IDs proposés gauche et droit | Lisibilité et limites |
| --- | --- | --- |
| **Grand fessier** — Masse postérieure principale de la fesse. | `gluteus_maximus.left` / `gluteus_maximus.right`<br>Codes 41 / 42 | Bonne globalement ; jonction ischio-jambiers progressive. **Priorité suivante possible.** |
| **Moyen fessier superficiel** — Partie supérieure/externe de la hanche. | `gluteus_medius.left` / `gluteus_medius.right`<br>Codes 43 / 44 | Partiellement visible ; ne représenter que la surface exposée. **Ultérieur.** |
| **Tenseur du fascia lata** — Petite région antéro-externe de la hanche. | `tensor_fasciae_latae.left` / `tensor_fasciae_latae.right`<br>Codes 45 / 46 | Faible/moyenne : relief proche du quadriceps et du fessier, à confirmer. **Optionnel.** |

## Cuisses

| Groupe / emplacement | IDs proposés gauche et droit | Lisibilité et limites |
| --- | --- | --- |
| **Droit fémoral** — Ventre central de la face antérieure de cuisse. | `quadriceps.left.rectus_femoris` / `quadriceps.right.rectus_femoris`<br>Codes 47 / 48 | Bonne : volume principal lisible. **Priorité suivante possible.** |
| **Vaste latéral** — Face antéro-externe de la cuisse. | `quadriceps.left.vastus_lateralis` / `quadriceps.right.vastus_lateralis`<br>Codes 49 / 50 | Bonne : galbe latéral net, origine haute moins délimitée. **Ultérieur.** |
| **Vaste médial** — Goutte au-dessus du bord interne du genou. | `quadriceps.left.vastus_medialis` / `quadriceps.right.vastus_medialis`<br>Codes 51 / 52 | Bonne distalement ; raccord proximal plus progressif. **Ultérieur.** |
| **Biceps fémoral superficiel** — Partie postéro-externe de la cuisse. | `hamstrings.left.biceps_femoris` / `hamstrings.right.biceps_femoris`<br>Codes 53 / 54 | Bonne pour le territoire externe ; tendon bas à préserver neutre. **Priorité suivante possible.** |
| **Semi-tendineux superficiel** — Partie postéro-interne de la cuisse. | `hamstrings.left.semitendinosus` / `hamstrings.right.semitendinosus`<br>Codes 55 / 56 | Moyenne : ne pas attribuer arbitrairement le semi-membraneux profond. **Ultérieur.** |
| **Adducteurs superficiels** — Face interne de cuisse, sous le pli de l’aine. | `adductors.left` / `adductors.right`<br>Codes 57 / 58 | Groupe : origine proximale volontairement simplifiée ; préserver l’aine validée. **Ultérieur.** |
| **Gracile** — Bande fine médiale de cuisse. | `gracilis.left` / `gracilis.right`<br>Codes 59 / 60 | Faible : voisin des adducteurs, séparation non fiable partout. **Optionnel.** |
| **Sartorius** — Trajet diagonal de la hanche externe vers le genou interne. | `sartorius.left` / `sartorius.right`<br>Codes 61 / 62 | Faible/moyenne : ne pas inventer un ruban là où le relief est absent. **Optionnel.** |

## Jambes

| Groupe / emplacement | IDs proposés gauche et droit | Lisibilité et limites |
| --- | --- | --- |
| **Gastrocnémien médial** — Chef interne du mollet postérieur. | `gastrocnemius.left.medial` / `gastrocnemius.right.medial`<br>Codes 63 / 64 | Bonne pour les grands galbes, raccord au tendon d’Achille simplifié. **Priorité suivante possible.** |
| **Gastrocnémien latéral** — Chef externe du mollet postérieur. | `gastrocnemius.left.lateral` / `gastrocnemius.right.lateral`<br>Codes 65 / 66 | Bonne globalement ; séparation centrale à confirmer sous plusieurs angles. **Ultérieur.** |
| **Soléaire superficiel exposé** — Bords inférieurs/latéraux du mollet, sous les gastrocnémiens. | `soleus.left` / `soleus.right`<br>Codes 67 / 68 | Partiel : seule la portion réellement exposée est sélectionnable. **Ultérieur.** |
| **Tibial antérieur** — Face antéro-externe de la jambe, à côté du tibia. | `tibialis_anterior.left` / `tibialis_anterior.right`<br>Codes 69 / 70 | Moyenne : territoire long lisible mais cheville/pied volontairement lissés. **Ultérieur.** |
| **Fibulaires superficiels** — Bord externe de la jambe. | `fibularis.left` / `fibularis.right`<br>Codes 71 / 72 | Faible/moyenne : groupe fonctionnel, long/court fibulaire non distingués. **Optionnel.** |

## Cou — facultatif

| Groupe / emplacement | IDs proposés gauche et droit | Lisibilité et limites |
| --- | --- | --- |
| **Sterno-cléido-mastoïdien** — Bande oblique superficielle latérale du cou. | `neck.left.sternocleidomastoid` / `neck.right.sternocleidomastoid`<br>Codes 73 / 74 | Zone simplifiée et validée esthétiquement ; intérêt fitness secondaire, pas de retouche prévue. **Optionnel.** |

## Limites générales de la sculpture

- Les gros volumes sont exploitables pour une carte fitness. La sculpture Meshy reste stylisée : une frontière propre n’équivaut pas à une insertion anatomique chirurgicale. Les petites portions profondes ne doivent pas devenir des plaques superposées.
- Biceps et triceps sont proposés par groupe entier, sans inventer leurs deux/trois chefs. Les bandes du brachial et les avant-bras restent neutres dans ce POC.
- Les limites de certains muscles du dos, de la hanche et des avant-bras seront des approximations fonctionnelles. Les rhomboïdes, petit pectoral, transverse et vaste intermédiaire ne sont pas des régions superficielles indépendantes sur ce mannequin.
- La finition de l’aine, du cou et des pieds a volontairement simplifié des détails. Elle doit rester intacte ; les futurs masques devront s’arrêter sur les surfaces encore identifiables.
- Les tableaux décrivent des candidats et leurs difficultés, pas des masques déjà validés ni un engagement de découper chaque ligne séparément.

Données exploitables : [`inventory.json`](m4c/meshy-bras-prototype/inventory.json). **Arrêt après le prototype des quatre bras ; aucun autre groupe n’est segmenté dans cette livraison.**
