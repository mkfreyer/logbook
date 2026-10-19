# Reprise manuelle dans Blender 4.3 — pectoraux et deltoïde gauche

**Ce fichier décrit un travail à effectuer. Aucune des sculptures ci-dessous
n’est déjà réalisée.** Le `.blend` fourni conserve les volumes sources, sans
correction artistique de silhouette ou d’attaches. La cible du chat reste à
consulter à côté de Blender ; elle n’est pas embarquée ni redistribuée.

## 1. Ouvrir et protéger le point de départ

1. Ouvrir `atelier-pectoraux-deltoide.blend` dans Blender 4.3.2 ou une version
   compatible. L’exécution automatique des scripts n’est pas nécessaire :
   aucun pilote Python, add-on, service externe ou script de démarrage.
2. Faire **File → Save As** sous un nouveau nom. Ne pas écraser la livraison.
3. Le sélecteur **Scene**, en haut de la fenêtre, propose `00_ATELIER`,
   `01_SOURCES`, `02_DEMO_PEC_G`, `03_DEMO_PEC_D` et `04_DEMO_DELTOIDE_G`.
   `00_ATELIER` est la scène active ; `01_SOURCES` conserve les neuf portions
   d’origine. Le cadenas de sélection des sources est une protection d’interface,
   pas une garantie contre une modification volontaire : les OBJ originaux
   byte pour byte restent récupérables dans `sources-originales.zip`.
4. Dans l’Outliner, `TRAVAIL` contient trois collections musculaires, chacune
   avec trois objets distincts. `REPERES_OSSEUX` contient les six objets sources
   de contexte, en fil de fer et non rendus. `RACCORDS_A_REPRENDRE` contient des
   Empty nommés : ce sont des aides approximatives à replacer, pas des attaches
   anatomiques validées ou de nouveaux volumes de muscle.
5. Ouvrir le workspace **Sculpting** après sélection d’une seule portion de
   travail. Ne jamais sculpter dans `01_SOURCES`. Les copies et les sources
   ont des datablocks indépendants. Les scènes de démonstration partagent en
   revanche les meshes de travail : une modification manuelle y sera répercutée.

## 2. Lire les volumes et les vrais raccords avant de sculpter

1. Dans `00_ATELIER`, **Numpad 1** pour la face, **Numpad 3** pour le profil,
   **Numpad 5** pour basculer orthographique/perspective. Sans pavé numérique :
   **View → Viewpoint**. **Numpad .** cadre la sélection ; cela ne concerne que
   l’outil Blender, aucune expérience de zoom applicative n’est créée.
2. Afficher les os, activer si utile **Alt+Z** en mode objet. Examiner sternum,
   clavicules, acromion sur la scapula, tête/diaphyse proximale de l’humérus.
   La pose est celle de BodyParts3D, non une pose athlétique reconstruite.
   Ne pas tourner isolément une épaule : les insertions et le bras devraient
   être traités ensemble. Aucun rig ne permet ici de garantir cette remise en pose.
3. Dans `01_SOURCES`, isoler successivement les portions claviculaires,
   sternocostales et abdominales des pectoraux, puis les trois portions du
   deltoïde. Utiliser **/** du pavé numérique pour la vue locale si nécessaire.
   Revenir à `00_ATELIER` pour modifier. Les noms FJ/FMA et `muscle_id` figurent
   dans **Object Properties → Custom Properties** ; voir aussi `identites.json`.
4. Replacer les Empty sur les vrais raccords observés. Le marqueur de proximité
   delto-pectorale n’est pas une preuve de sillon correct ; les tables sources
   nomment les pièces mais ne fournissent pas une carte d’attaches ou de fibres.
5. Contrôler en face, trois quarts, profil et sous l’aisselle. Repérer les
   chevauchements des portions, les éléments minces, les bords raides et les
   espaces internes normaux. Distinguer un sillon de surface d’un trou à travers
   l’assemblage. Ne pas remplir automatiquement un espace avec un volume inventé.

### Îlots sources à inspecter avant toute suppression

Le diagnostic après soudure exacte trouve 13 / 7 / 3 composantes dans les portions
claviculaire / sternocostale / abdominale de chaque pectoral, et 1 / 4 / 20 dans
les portions claviculaire / acromiale / spinale du deltoïde gauche. Beaucoup de
microcomposantes n’ont que 3 à 6 sommets ; la portion sternocostale comporte
également un deuxième îlot de 402 sommets. Aucune composante n’est supprimée.
Une surface sans bord ouvert peut néanmoins contenir ces fragments, voire des
faces opposées de faible épaisseur : elle n’est pas automatiquement un bon volume.

Chaque copie comporte des groupes `DIAG_ILOT_01_V…`, `DIAG_ILOT_02_V…`, etc.,
triés par taille. En **Edit Mode**, désélectionner tout, choisir le groupe dans
**Object Data Properties → Vertex Groups**, puis **Select**. **Shift+H** isole
la sélection, **Alt+H** restaure les faces cachées. Identifier la fonction de
l’îlot en regard de la source et des os avant toute décision. Pour tester une
suppression, travailler sur une duplication ; ne jamais supprimer un fragment
par son seul nombre de sommets. Le groupe `source_FJ…` couvre toute la portion
et sert à conserver sa provenance lors d’un éventuel Ctrl+J.

## 3. Choisir une topologie de travail sans refaire D1/D2

Les copies sont soudées **uniquement aux positions exactement identiques dans
chaque OBJ**. Aucun sommet de deux portions n’est soudé ensemble. Il n’y a ni
union voxel, ni peau de soutien, ni décimation, ni subdivision automatique.

**Premier passage, à topologie fixe :** garder les neuf objets et utiliser les
shape keys fournies. Dans **Object Data Properties → Shape Keys**, `Basis` est
la copie normalisée du volume source ; `VOLUME_MANUEL` et `RACCORDS_MANUELS`
sont des emplacements initialement identiques à Basis, sans sculpture préfaite.
Pour une passe de volume, sélectionner `VOLUME_MANUEL`, lui donner la valeur 1,
laisser `RACCORDS_MANUELS` à 0, puis sculpter. Revenir à 0 permet le contrôle
avant/après. Désactiver Dyntopo et ne pas lancer Voxel Remesh sur ces objets.

**Si les triangles ne permettent pas le travail :** arrêter la passe, conserver
la copie et faire une retopologie **locale et manuelle d’un seul muscle** :

1. Dupliquer ses trois portions avec **Shift+D**, clic droit pour conserver leur
   position. Créer une collection `RETOPO_PEC_G` ou `RETOPO_DELTOIDE_G`.
2. Pour créer une cible de référence unique, **Ctrl+J** sur ces seules copies
   rassemble les objets mais ne fusionne pas leurs surfaces. Les groupes de
   sommets `source_FJ…` conservent la provenance. Cette cible n’est pas le résultat
   final et ne doit pas être confondue avec une surface continue prête à sculpter.
3. Construire manuellement une surface de quads au-dessus des volumes sources,
   par exemple depuis un mesh vidé en mode Edit, avec **Poly Build**, **E** et **F**.
   Activer l’aimant **Face Project** pour le placement, puis un **Shrinkwrap**
   ciblant la référence de ce seul muscle, avec un très faible offset à contrôler.
   Ne jamais prendre l’ensemble de la peau ou l’épaule complète comme cible.
4. Tracer les boucles en suivant les bords et l’éventail du pectoral, ou les trois
   faisceaux du deltoïde. Faire circuler les quads autour du ventre et de la
   transition tendineuse ; fermer aussi les faces profondes nécessaires à un
   volume stable. Vérifier les raccords avant d’appliquer le Shrinkwrap.
5. Créer les shape keys après cette retopologie, ou utiliser une copie de
   sauvegarde puis **Multiresolution** à faible niveau. Ne pas mélanger Dyntopo,
   modification de topologie et shape keys fixes. Garder les trois muscles
   comme objets/ensembles indépendants. Aucun Remesh global ni simple primitive
   gonflée ne remplace ce travail de surface.

Cette retopologie est une tâche artistique réelle, non exécutée dans le fichier
livré. Si elle est nécessaire, les neuf copies initiales restent des références,
non une promesse de sculpture immédiate au pinceau.

## 4. Sculpter les pectoraux

1. Travailler d’abord le gauche, avec le droit comme comparaison anatomique,
   sans imposer une symétrie parfaite aux sources. Désactiver la symétrie du
   pinceau sur une portion isolée ; ne pas réfléchir tous les objets autour de
   leur origine locale par erreur.
2. Avec **Mask** (M), protéger les extrémités médiales vers le sternum, la zone
   claviculaire et la convergence latérale vers l’humérus, après les avoir
   vérifiées en profondeur. Les poids d’attaches ne sont pas prépeints : ne pas
   supposer que toute extrémité de la bounding box correspond à une insertion.
3. Utiliser **Grab** ou **Elastic Deform**, grand rayon, faible force : arrondir
   le ventre antérieur en conservant sa base d’attache et la convergence vers
   l’aisselle. Contrôler le profil après chaque déplacement. Éviter de décaler
   tout le muscle vers l’avant, ce qui le ferait flotter.
4. Avec **Clay Strips** ou **Inflate**, faible force, construire une convexité
   large. Revenir souvent à **Smooth** (Shift) pour supprimer les bosses. Le but
   est un éventail plein, pas trois plaques juxtaposées ou des bourrelets parallèles.
5. Retrouver la séparation sternale avec un passage très léger de **Draw Sharp**
   ou **Crease**, uniquement sur la copie sculptée. Garder un creux étroit et
   contrôlé, sans couper le mesh ni créer une fente ouverte.
6. Les subdivisions internes des portions ne doivent pas produire des marches.
   Si leurs surfaces restent superposées ou disjointes malgré de petits gestes,
   revenir à la retopologie de ce seul pectoral ; ne pas les masquer par une peau.
7. Reprendre le droit séparément avec les mêmes critères, en préservant sa
   provenance. Les nombres de triangles n’imposent pas une taille musculaire.

## 5. Deltoïde et raccords prioritaires

1. **Deltoïde gauche :** protéger les origines clavicule/acromion/épine de scapula
   et vérifier l’insertion humérale. Avec Grab puis Clay Strips, construire une
   enveloppe qui descend vers l’humérus ; garder les trois directions de faisceaux.
   Ne pas obtenir une sphère posée au bout du torse.
2. **Sillon delto-pectoral :** vérifier en trois quarts et profil que les bords
   se lisent comme deux muscles voisins. Réduire uniquement les lèvres trop
   saillantes avec Smooth/Flatten, plutôt qu’enfoncer une rigole noire. Aucun
   chevauchement de surfaces et aucune vue à travers un vide ne doit subsister.
3. **Clavicule :** ménager une transition amincie vers les deux origines
   musculaires ; ne pas tirer le ventre du pectoral sur tout l’os. Les faces
   profondes doivent rester cohérentes avec leur attache, pas seulement la face.
4. **Sternum :** contrôler les bords médiaux gauche/droit en vue frontale puis
   plongeante ; ne pas souder les deux pectoraux. Si une zone neutre de liaison
   est indispensable, sa surface doit être dessinée et identifiée séparément,
   à partir de repères anatomiques vérifiés, jamais remplie automatiquement.
5. **Pli axillaire antérieur :** suivre la convergence latérale du pectoral vers
   l’humérus. Préserver une épaisseur tendineuse crédible ; inspecter aussi sous
   le bras. Une portion source qui traverse un autre volume exige une correction
   locale vérifiée, pas une translation globale pour cacher la collision.
6. Si un raccord ne peut pas être résolu sans inventer son anatomie, le noter
   comme bloquant et demander une revue compétente. Les tables d’identité ne
   remplacent pas la connaissance d’anatomie de surface.

## 6. Suggérer les fibres seulement après validation des formes

1. Conserver une copie avant toute strie. Pour les pectoraux, suggérer l’éventail
   du sternum/clavicule vers la convergence humérale. Pour le deltoïde, partir
   de chaque origine vers l’insertion ; pas de stries parallèles uniformes.
2. Quelques passages très doux de **Draw Sharp/Crease** sur une copie de détail
   ou une couche Multires suffisent pour juger l’intention. Les fibres ne doivent
   ni réparer les raccords, ni faire écran à une silhouette incorrecte.
3. Comparer sans détail et à petite taille. Si le relief ne lit que de très près,
   ne pas ajouter de densité pour le mobile. Un bake normal éventuel ne vient
   qu’après validation de la sculpture ; aucun bake n’est préparé ici.

## 7. Sélection et vérification finale

1. Identités logiques : `pectoralis-major-left`, `pectoralis-major-right`,
   `deltoid-left`. Les trois objets d’un même groupe ont le même `muscle_id` et
   le même matériau de base. Ne pas attribuer un nouveau muscle à chaque portion.
2. Les trois scènes `DEMO` passent le muscle choisi en orange **par objets** ;
   chaque portion entière est activée, sans classification des faces par proximité.
   Les autres muscles restent bleus. Il n’y a ni moteur tactile, ni pilote Python.
3. Après une retopologie, recopier explicitement le bon `muscle_id`, conserver
   ses références FMA/FJ dans les métadonnées et mettre à jour les copies de
   démonstration. Elles partagent les meshes initiaux, pas de futurs objets créés.
4. Caméras disponibles : `CAM_FACE`, `CAM_TROIS_QUARTS`, `CAM_DETAIL`.
   Dans **Scene Properties/Outliner**, choisir la caméra active, ou la sélectionner
   puis **Ctrl+Numpad 0**. Garder les mêmes caméras, lumières et matériau entre
   `01_SOURCES` et le travail ; ne pas ajuster une seule version pour cacher un défaut.
5. Rendre face, trois quarts, détail et pectoral gauche orange **seulement après
   une passe artistique réelle**. Réduire la vue du torse à 390 pixels et vérifier
   séparations lisibles, pectoraux pleins, deltoïde crédible, absence de trous,
   flottement, collisions, effet de plaques et orange fragmenté. Ce cadrage local
   ne démontre pas la lecture d’un corps entier à 390 px : elle restera à tester.
6. Revue mesh sur les copies : Edit Mode → Select → Select All by Trait →
   Non-Manifold ; Face Orientation en overlay ; contrôle des normales et des
   collisions en vues croisées. Ne pas « réparer » les sources archivées.
7. Si un seul de ces points échoue, ne pas déclarer le prototype réussi et ne
   pas étendre au corps entier. Enregistrer un jalon et consigner le défaut.

La validation esthétique et anatomique exige une personne capable de réaliser
et juger cette sculpture. Le fichier livré prépare ce travail ; il ne le remplace
pas. Aucun coût, achat, Astra, corps complet, export mobile ou développement
applicatif n’est autorisé par ce guide. Arrêt pour validation de cette reprise.
