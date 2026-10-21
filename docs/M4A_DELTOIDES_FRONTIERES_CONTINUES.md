# M4A — Frontières continues des six zones, surface P4 conservée

## Résultat proposé

Les frontières colorées de `fb68f5e` sont remplacées par des **courbes de séparation qui traversent les triangles**. Les faces traversées sont découpées localement, sans sculpture ni modification du bombé ou des creux P4.

Base exclusive : [`fb68f5e`](https://github.com/mkfreyer/logbook/commit/fb68f5ee9ab3b47f3ae046cd7a1ce11129a98857), lui-même géométriquement identique à la combinaison P4 + tête P5 de `0ab3d83`. Les anciennes sculptures rejetées ne sont pas utilisées. Les versions précédentes restent intactes.

## Rendus à examiner

- [Avant / après des frontières, mêmes caméras](m4a/ecorche-beatriz-frontieres-deltoides/renders/comparatif-frontieres.png).
- [Six zones : épaules droite/gauche de face et de trois quarts, profil et dos](m4a/ecorche-beatriz-frontieres-deltoides/renders/controle-six-zones.png).
- [Comparatif neutre P4 / copie découpée](m4a/ecorche-beatriz-frontieres-deltoides/renders/comparatif-neutre.png).
- [Gros plans neutres des deux épaules de face](m4a/ecorche-beatriz-frontieres-deltoides/renders/epaules-face-neutres.png).
- [Rendus individuels après découpage](m4a/ecorche-beatriz-frontieres-deltoides/renders/after/).

Antérieur rouge, moyen/latéral bleu, postérieur vert. Les côtés sont ceux du mannequin. Même matériau mat neutre, éclairage et caméras que précédemment ; deux caméras frontales rapprochées supplémentaires sont identiques avant/après. Rendus Blender/Cycles CPU, 48 échantillons, sans débruitage ni peinture des pixels.

## Méthode

1. Reprendre les chemins anatomiques et distances de surface de `fb68f5e`.
2. Régulariser les **champs de répartition des zones uniquement** par diffusion sur la surface, avec une échelle de 6 mm. Aucune coordonnée géométrique n'est lissée.
3. Définir les séparations par l'égalité des champs entre portions. Ces courbes sont continues sur la surface triangulée, indépendamment des caméras.
4. Intersecter ces frontières avec les faces P4. Chaque nouveau point est obtenu par coordonnées barycentriques dans son triangle d'origine. Les sommets d'origine gardent exactement leurs positions P4 évaluées.
5. Subdiviser seulement les faces traversées et réattribuer leurs triangles aux trois matériaux existants. Les sommets de frontière sont partagés : aucune plaque, incision ou surface superposée.

Les normales de coins P4 sont interpolées, normalisées et conservées comme normales personnalisées. Les deux côtés d'une frontière reçoivent la même normale. Couleurs de sommets, éventuels UV et poids de groupes sont également interpolés. Les clés de forme des **deux seuls deltoïdes** sont figées à leur pose P4 évaluée dans cette nouvelle copie ; elles restent intactes dans le master original archivé.

Il ne s'agit pas d'une nouvelle validation médicale des limites anatomiques. La partition antérieure / latérale / postérieure est conservée dans son principe, avec régularisation locale des frontières ; les délimitations restent proposées pour validation visuelle.

## Coût géométrique et mobile

| Mesure | Avant, par épaule | Après, par épaule | Écart |
| --- | ---: | ---: | ---: |
| Sommets | 5 971 | 6 395 | +424 |
| Triangles | 11 938 | 12 786 | +848 |
| Faces d'origine subdivisées | — | 419 | 3,51 % des faces d'origine |

Les **11 519 autres faces par épaule** ne sont pas subdivisées. Total du mannequin Blender : **499 754 triangles**, soit **+1 696 triangles / +0,34 %**. L'export GLB compte 499 753 triangles, avec la même face doublonnée préexistante omise par l'exporteur.

La structure reste à **300 objets, 304 primitives GLB et 7 matériaux** : aucun surcoût de primitive ou de matériau par rapport à `fb68f5e`. GLB neutre : **10 337 140 octets**, soit **+39 740 octets** (~38,8 Kio). Aucune texture ajoutée.

Le surcoût du découpage est faible. Le corps complet reste proche de 500 000 triangles : ce POC ne constitue pas une optimisation mobile finale et ne démontre pas un nombre d'images par seconde sur téléphone. Aucune optimisation globale n'est engagée à cette étape.

## Contrôles réellement effectués

Voir le [rapport automatique](m4a/ecorche-beatriz-frontieres-deltoides/verification.json) et les [comparaisons de rendus](m4a/ecorche-beatriz-frontieres-deltoides/renders/comparisons.json).

- **Tous les sommets d'origine des deux surfaces P4 sont inchangés bit à bit.**
- Nouveaux points reconstruits sur leurs triangles sources, sans déplacement intentionnel hors surface. Après stockage float32 Blender/GLB, l'écart maximal à la position barycentrique théorique est **0,000061 mm**. Il s'agit de la précision numérique de stockage, pas d'une retouche de forme.
- Chaque face source est entièrement couverte par ses enfants ; somme des rapports d'aire égale à 1 à ~2,3 × 10⁻¹⁶ près. Aucun chevauchement entre enfants au-delà de l'arrondi numérique.
- Les deux maillages restent fermés, à deux faces par arête, caractéristique d'Euler 2. **Aucune intersection entre triangles non adjacents détectée.**
- Variation relative de volume inférieure à **0,000001 %**, correspondant aux arrondis float32. Pas de modification voulue de silhouette, de bombé ou de creux.
- Normales de boucle identiques de part et d'autre des frontières de matériaux dans Blender **et dans le GLB** : écart mesuré **0**. Le réencodage des normales personnalisées à l'export ajoute un écart maximal de composante de 0,000063 par rapport au master. L'interpolation et l'encodage ne sont donc pas strictement identiques au champ d'ombrage d'avant subdivision.
- **298/298 autres objets** conservent leurs géométries brutes, matériaux, normales et modificateurs, notamment la tête P5, la gorge, les pectoraux et le reste du corps.
- Chaque zone est continue et tous les triangles sont attribués exactement une fois. Les six matériaux sont indépendants ; coloration isolée et retour neutre testés.
- Positions sérialisées, identifiants et correspondance des primitives vérifiés dans les GLB neutre/coloré ; buffers géométriques identiques entre ces exports, réimport des deux réussi.

La frontière antérieur/moyen n'est plus une marche d'arêtes successives. Son changement de direction médian mesuré en 3D passe d'environ **80° à 4°** ; ce chiffre décrit les polylignes du maillage et ne remplace pas l'examen des rendus. Les séparations restent des polylignes sur une surface triangulée, pas des courbes mathématiquement infiniment lisses.

### Contrôle neutre : résultat et limite

Sur les vues profil et trois quarts comparées à l'identique, environ **99,97 % des pixels RGB sont inchangés**. L'écart moyen est inférieur à **0,0003 niveau sur 255** ; écarts maximaux isolés : 9 niveaux en profil et 3 en trois quarts. Ces écarts de rendu et d'interpolation sont consignés sans retouche.

Le comparatif neutre ne montre **ni couture visible ni modification perceptible des volumes** aux angles contrôlés. **L'image n'est pas strictement identique pixel par pixel.** La conservation des sommets d'origine et la provenance barycentrique démontrent séparément l'absence de sculpture.

## Six identifiants conservés

| Portion | Gauche | Droite | Triangles par épaule après découpage |
| --- | --- | --- | ---: |
| Antérieure | `deltoid.left.anterior` | `deltoid.right.anterior` | 5 344 |
| Moyenne / latérale | `deltoid.left.lateral` | `deltoid.right.lateral` | 2 704 |
| Postérieure | `deltoid.left.posterior` | `deltoid.right.posterior` | 4 738 |

Les nombres incluent la surface profonde habituellement cachée. Chaque ID reste dans `material.name`, `material.extras.zone_id` et `primitive.extras.zone_id`. La [table de sélection](m4a/ecorche-beatriz-frontieres-deltoides/selection-map.json) correspond aux **nouveaux** indices de faces/primitives. La provenance vers les faces P4 est conservée séparément ; ne pas réutiliser les anciens indices numériques comme identifiants stables.

## Fichiers et décision

[Master Blender](m4a/ecorche-beatriz-frontieres-deltoides/ecorche-p4-p5-zones.blend) · [GLB neutre](m4a/ecorche-beatriz-frontieres-deltoides/ecorche-p4-p5-zones.glb) · [GLB coloré](m4a/ecorche-beatriz-frontieres-deltoides/ecorche-p4-p5-zones-controle.glb) · [Provenance barycentrique](m4a/ecorche-beatriz-frontieres-deltoides/provenance-surface.npz) · [Scripts et reproduction](m4a/ecorche-beatriz-frontieres-deltoides/README.md).

**Recommandation : retenir ce découpage local plutôt que les frontières suivant les anciennes arêtes.** Le défaut majeur de dents de scie est corrigé dans les vues contrôlées, sans nouvelle sculpture. La validation finale des limites et de l'absence de couture visuelle vous revient.

**Arrêt après cette proposition.** Aucune intégration Logbook, modification SQLite, M4B ou fusion. PR #12 maintenue en brouillon. Aucun achat, service payant ou Astra Ultra.

Corps : **Ecorche - Anatomy study**, Beatriz Gomez Santamaria, [Sketchfab](https://sketchfab.com/3d-models/ecorche-anatomy-study-e402d3d541eb4b199c57d5410f5d3c57), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Adaptation Logbook et subdivision locale signalées dans les GLB. Tête/yeux : Dan Ulrich / Blender Studio, Human Base Meshes v1.4.1, CC0 ; [provenance](m4a/ecorche-beatriz-passe5/HEAD_SOURCE_LICENSE.md).
