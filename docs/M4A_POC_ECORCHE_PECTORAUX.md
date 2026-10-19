# M4A — PoC pectoraux / deltoïde : méthode insuffisante

18 octobre 2026. Départ : `43ac3c1`, B+ Premium Puissance. PR #11 en brouillon.

**Verdict : méthode insuffisante.** Le résultat conserve une lecture de mannequin avec reliefs. L'éventail pectoral, les portions du deltoïde et les fibres ne deviennent pas convaincants à taille mobile. **Modélisation arrêtée après ce seul essai visuel ; aucune V2 / V3 / V4 automatique.**

[Avant / après de face](m4a/pectoral-poc/comparaison-front.png) · [Trois quarts](m4a/pectoral-poc/comparaison-three-quarter.png) · [Gros plan diagnostique](m4a/pectoral-poc/after/detail.png) · [Pectoral gauche seul en orange](m4a/pectoral-poc/after/selection.png)

![Comparaison trois quarts](m4a/pectoral-poc/comparaison-three-quarter.png)

Chaque mannequin comparatif mesure **390 pixels de large**. La différence reste faible à cette taille ; le gros plan ne révèle pas de fibres convaincantes. Ce sont des constats d'échec, pas une validation sur iPhone.

## Méthode et blocage

Périmètre : deux pectoraux, **deltoïde droit** et jonctions sternum / clavicule / aisselle / haut du bras. Construction originale, sans asset anatomique tiers : surfaces pectorales courbes en éventail, origine médiale étendue et convergence humérale, huit faisceaux inégaux effilés ; surface deltoïde enveloppante à trois domaines convergeant vers le bras. Un attribut de normales accompagne les faisceaux.

Un raffinement triangulaire local permet leur raccord dans la surface existante. **La méthode reste un déplacement de l'enveloppe : elle ne reconstruit pas des muscles anatomiques autonomes avec des attaches retopologisées.** Cette limite conserve les formes artificielles du mannequin.

Le raccord complet produisait des retournements de triangles. Le contrôle d'orientation a limité la transformation à **8,59 % du déplacement demandé**, maximum conservé **6,08 mm**. Les contours pectoraux anciens restent dominants, l'épaule garde un aspect de capuchon et les fibres sont trop atténuées. Forcer les paramètres ne résoudrait pas les attaches et leurs raccords.

## Coût et régions préparées

| | B+ Puissance | Essai local |
|---|---:|---:|
| Triangles corporels | 110 000 | 133 870 |
| Triangles avec les yeux | 112 176 | **136 046** |
| Sommets corporels | 55 002 | 66 937 |
| Objets maillés | 3 | 3 |
| Régions de démonstration | 2 | **3** |

**+23 870 triangles, environ +21,3 %, sans gain visuel suffisant.** L'essai n'est pas recommandé pour remplacer B+ Puissance.

Trois masques scalaires indépendants et IDs entiers de faces disjoints : pectoral gauche (`1`, **4 659 triangles**), pectoral droit (`2`, **4 559**), deltoïde droit (`3`, **5 600**) ; `0` ailleurs. Les trois commandes Blender sont vérifiées séparément. Le rendu orange active uniquement le pectoral gauche anatomique. Masques interpolés et IDs par face restent des approximations de démonstration, sans segmentation anatomique finale ni interaction applicative.

## Contrôles et limites

Les positions des sommets d'origine hors périmètre et les deux yeux sont vérifiés inchangés. Les points ajoutés subdivisent localement la surface source ; aucun remodelage du reste du corps. Trois objets fermés, à une composante et de genre nul, sans bord non-manifold ni triangle quasi dégénéré détecté. Aucun croisement détecté dans les régions sculptées ; les **304 paires tête / pieds héritées** restent présentes. Des rotations locales importantes subsistent : produit scalaire minimal des normales **0,109**. Ces contrôles ne constituent pas une réussite visuelle ou une validation de production.

Six vrais rendus Blender 4.3.2 / Cycles CPU, 96 échantillons. Même matériau et éclairages, mêmes caméras comparatives ; détail et sélection utilisent un cadrage rapproché. Les attributs de l'essai portent ses détails locaux, absents du témoin. Aucune anatomie repeinte en 2D, aucune image générative, aucun benchmark mobile.

## Approche réellement nécessaire — non lancée

Blender et ses outils de sculpture sont disponibles. **Il manque ici une construction anatomique maîtrisée des masses et attaches**, pas une nouvelle augmentation de puissance. La suite demanderait une sculpture locale conduite par un artiste compétent, une reprise de topologie aux jonctions pectoral / deltoïde / aisselle, puis les faisceaux et leur cuisson vers un maillage mobile. B+ Puissance servirait de guide de proportions. Cette autre méthode de production n'est pas lancée.

[Sources et reproduction](m4a/pectoral-poc/README.md) · [Construction](m4a/pectoral-poc/experiment/construction.json) · [Géométrie](m4a/pectoral-poc/experiment/geometry-check.json) · [Périmètre et sélection](m4a/pectoral-poc/audit.json) · [Validation](m4a/pectoral-poc/validation.json) · [Manifest](m4a/pectoral-poc/manifest.json)

Source amont Dan Ulrich / Blender Studio, CC0 : [provenance](m4a/bplus-fitness/PROVENANCE.md). Aucun maillage CC BY-SA réintroduit, achat ou Astra Ultra. Anciens travaux préservés ; aucune intégration, modification SQLite, segmentation complète, M4B ou fusion. **Arrêt pour validation de ce constat.**
