# M4A — Finition locale du cou sur la tête conservée

Base : **`62000ae`**, tête Marble Titan restaurée sur le corps Anatomical Form.
Cette passe conserve cette direction et traite uniquement les petites cassures
de surface visibles sur les zooms : base de tête, côtés du cou et raccords
immédiats avec les trapèzes. Aucune nouvelle tête ni nouveau raccord massif.

## Rendus de validation

- [Avant / après serré : profil, face et trois quarts](m4a/meshy-finition-locale-cou/renders/comparatif-finition-cou.png).
- [Contrôle de la tête : face, profil et trois quarts](m4a/meshy-finition-locale-cou/renders/controle-tete.png).
- [Mannequin complet](m4a/meshy-finition-locale-cou/renders/mannequin-complet.png).

Treize vrais rendus Blender/Cycles, dont six paires avant/après avec les mêmes
caméras, le même matériau mat neutre, les mêmes cinq lumières et les mêmes
réglages. La colonne « avant » est l’assemblage publié dans `62000ae`.
Les images brutes ne sont pas retouchées ; les planches ajoutent seulement
des légendes et un redimensionnement uniforme.

## Corrections réellement effectuées

Le travail porte sur une **copie du maillage actuel**, sans nouvelle découpe,
sans remplacement de la tête et sans changement de topologie.

- **Base de tête et nuque :** atténuation des petits changements brusques de
  courbure. La zone remonte légèrement à l’arrière pour traiter la cassure de
  nuque montrée sur les zooms, sans toucher aux cheveux.
- **Côtés du cou :** lissage des irrégularités et des angles résiduels, avec
  raccord progressif vers la surface conservée.
- **Cou / trapèzes :** adoucissement limité au raccord immédiat supérieur ;
  le reste des trapèzes, les deltoïdes et le torse ne sont pas resculptés.

Une relaxation locale des sommets atténue les irrégularités, puis des étapes
alternées limitent la rétraction de la forme. L’influence s’annule
progressivement au bord de la zone. Chaque déplacement est plafonné à **3 mm**,
avec un plafond encore plus faible dans les raccords progressifs.
Les normales lisses sont recalculées dans cette même zone, afin de réduire
les facettes d’éclairage sans changer le matériau.

Le menton et son avant restent protégés, pour ne pas recréer la masse sous la
mâchoire du raccord fondu rejeté. Aucun changement de coiffure, de placement,
de taille de tête ou de silhouette générale du corps n’est réalisé.

## Contrôles de préservation

| Contrôle | Résultat |
| --- | --- |
| Sommets et triangles | **55 288 sommets, 110 588 triangles**, identiques en nombre et connectivité à `62000ae` |
| Sommets modifiés localement | **4 317** |
| Déplacement moyen parmi les sommets modifiés | **1,12 mm** |
| Déplacement maximal | **3 mm**, à l’arrondi float32 près |
| Sommets hors zone autorisée | **50 971 identiques**, aucun déplacé |
| Visage protégé, menton et cheveux | Aucun déplacement dans les régions de contrôle |
| Deltoïdes, torse, bras, bassin, aine, jambes et pieds | Géométrie inchangée |
| Dimensions hors tout | Strictement identiques |
| Maillage | Fermé, orienté, une composante, aucune nouvelle intersection locale détectée |
| GLB | Surface exportée identique au master Blender |

Le contrôle compare chaque position de sommet et chaque triangle avec
l’assemblage précédent, y compris la scène « avant » contre son GLB publié.
Les anciennes versions et les fichiers des zones précédentes restent intacts.

Le domaine maximal est centré sur le cou : Z entre 0,645 et 0,775 m, |X| inférieur
à 0,135 m et Y supérieur à −0,065 m, dans les coordonnées Blender centrées.
La limite haute est plus basse à l’avant (0,735 m) qu’à l’arrière (0,775 m).
Ce volume définit une enveloppe de contrôle ; l’influence réelle est progressive.
Le visage avant, le menton et les cheveux sont contrôlés séparément.

Le rayon moyen des sommets retouchés diminue d’environ **0,054 mm** : pas
d’épaississement global du cou. Les angles entre triangles voisins du domaine
passent en moyenne de **5,39° à 3,91°**, ce qui confirme une atténuation des
cassures géométriques. Cet indicateur ne constitue pas une validation anatomique.

Le réencodage des normales sur les faces protégées entraîne un écart vectoriel
maximal d’environ 0,000467, sans déplacement de surface.
[Mesures et empreintes détaillées](m4a/meshy-finition-locale-cou/verification.json).

## Limites et fichiers

Le résultat vise une finition douce tout en conservant les volumes et les
reliefs simples du cou actuel. Les particularités générées de la tête et du
corps ne sont pas corrigées globalement. Le lissage plafonné ne cherche pas à
effacer tous les reliefs anatomiques : les gros plans restent la base de la
validation esthétique.

Le GLB fait **1 993 204 octets**, environ 1,99 Mo : un maillage, un matériau,
aucune texture. **Aucun triangle supplémentaire** ni nouvelle dépendance.
Aucun test de fluidité dans l’application.

[Blender, GLB, provenance et reproduction](m4a/meshy-finition-locale-cou/README.md).
Attribution conservée : **Model created with Meshy — CC BY 4.0 License**,
suivant la [provenance existante](m4a/meshy/LICENCE_ET_PROVENANCE.md).
Budget additionnel nul, aucune nouvelle génération ni outil payant.

**Arrêt pour validation visuelle.** Application et SQLite inchangées, aucun M4B
ni segmentation ; aucune fusion ; PR #12 conservée en brouillon.
