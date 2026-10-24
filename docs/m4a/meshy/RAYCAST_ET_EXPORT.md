# Correspondance stable triangle → muscle

Cette livraison prépare les données ; aucun moteur tactile ni code applicatif
n’est intégré. Les identités logiques sont stables :

| Valeur | Identifiant | Usage |
| ---: | --- | --- |
| 0 | `unassigned` | Reste du corps, non segmenté |
| 1 | `pectoralis.left` | Grand pectoral gauche |
| 2 | `pectoralis.right` | Grand pectoral droit |
| 3 | `deltoid.left` | Deltoïde gauche |

Les limites actuelles sont visuelles et provisoires. Une identité stable ne vaut
pas une validation anatomique du contour, notamment sous le deltoïde.

## 1. Charger le GLB original inchangé

`source.glb` contient un nœud, un mesh, une primitive TRIANGLES indexée.
`regions/triangle-regions.u8` contient exactement 95 426 octets : l’octet `i`
est la valeur du muscle du **triangle original i**, soit le triplet
`indices[3*i : 3*i+3]`. `regions.json` donne le registre, les dimensions et les
SHA-256 du fichier GLB, des positions, des indices et du masque. Aucun attribut
Blender n’est supposé avoir traversé un export GLB.

Après vérification des empreintes au chargement, un raycast sur cette primitive
peut utiliser `faceIndex` comme indice de triangle source, **à condition que le
chargeur n’ait ni réordonné, ni décimé ou réindexé les triangles**. Vérifier cette
condition ; ne pas l’inférer seulement du nom de fichier. Un matériau ou le calcul
des normales ne requiert pas, à lui seul, de changer la correspondance.

```js
// Schéma de lookup, pas une intégration dans Logbook.
const sourceTriangle = hit.faceIndex;
const regionValue = regionBytes[sourceTriangle];
const regionId = registry[regionValue];
```

Les trois surfaces restent dans le même maillage ; pas besoin de les reconstruire
ou de fabriquer un muscle séparé pour chaque sélection.

## 2. Export concret avec quatre primitives matérielles

[meshy-zones.glb](export/meshy-zones.glb) démontre une voie simple de coloration :
quatre primitives, une pour le reste du corps et une pour chaque région testée.
**Elles partagent le même accessor de 47 711 positions**, sans duplication ni
déplacement de sommet. Des normales lissées calculées sur ces mêmes triangles
sont ajoutées pour la présentation, sans modifier les positions ou la topologie. Chaque triangle original apparaît exactement une fois.
Les matériaux sont tous bleus au repos ; passer seulement le matériau de la
primitive sélectionnée en orange est alors indépendant des autres zones.

Cet export **réordonne les triangles**, en gardant leur triplet de sommets intact.
Il ne faut donc pas appliquer naïvement le `faceIndex` du GLB exporté au masque
original. La correspondance est fournie dans :

- [export-binding.json](export/export-binding.json) : SHA de l’export, primitives,
  plage dans la table de correspondance et identités ;
- [draw-triangle-to-source.u32](export/draw-triangle-to-source.u32) : 95 426 entiers
  uint32 **little-endian**, une permutation des triangles originaux.

Pour un impact sur la primitive `p`, le triangle local `j` correspond à :

```js
// p doit être la primitive glTF identifiée au chargement, pas l'index d'un
// objet trouvé par hasard dans la scène ou un ordre supposé de children[].
const record = exportBinding.primitives[p];
const sourceTriangle = drawToSource[record.map_triangle_offset + hit.faceIndex];
const regionValue = regionBytes[sourceTriangle];
const regionId = registry[regionValue];
```

Le chargeur devra associer explicitement chaque objet rendu à son mesh/primitive
glTF. Les `extras.logbook_region` et `extras.logbook_value` sont des aides
embarquées ; le contrat vérifiable reste le fichier de binding et la lecture de
la primitive correspondante. La présence d’un `extras` n’est pas une garantie
universelle d’exposition par tous les viewers.

Le script d’export relit le GLB écrit, vérifie l’égalité des positions et de tous
les triangles via cette permutation, ainsi que l’appartenance de chaque primitive
à une seule région. Le contrôleur Blender effectue également une relecture des
buffers et de la table. Aucun Draco, meshopt, quantification ou optimiseur implicite.

## 3. Modifier les contours dans Blender

1. Faire une copie de `renders/meshy-masques.blend`. Choisir `04_CONTROLE_REGIONS`
   pour voir orange = pectoral gauche, jaune = droit, turquoise = deltoïde gauche.
   Ces trois couleurs servent au diagnostic, pas à une sélection unique.
2. Le même datablock mesh est partagé entre les cinq scènes. En mode Edit,
   sélection de **faces**, X-Ray désactivé, ajouter/retirer de petites bandes de
   faces sur la surface visible. Contrôler aussi profil et dos : une sélection
   rectangulaire traversante pourrait colorer un muscle voisin.
3. Les quatre slots de matériau correspondent aux valeurs 0 / 1 / 2 / 3.
   Utiliser **Assign** pour attribuer les faces au bon slot ; 0 retire une face
   de ces trois régions. Les slots de `00_NEUTRE` portent les identifiants et
   ont tous le même bleu ; les overrides de chaque scène donnent la coloration.
4. Ne pas déplacer de sommet, sculpter, subdiviser, trianguler à nouveau, fusionner
   ou remesher. L’attribut `source_triangle_index` conserve la provenance des faces.
   `muscle_zone` est la photographie initiale des labels : les indices de matériau
   sont l’autorité éditable et l’exporteur les relit explicitement.
5. Enregistrer puis exécuter `save_regions.py` selon le README. Il vérifie les
   positions, chaque triplet de sommets et le bijectif des IDs source, écrit le
   masque dans l’ordre du GLB original et refuse des régions disjointes ou trouées.
   Il ne suppose pas que les attributs soient exportés par Blender.
6. Refaire l’export de zones et les vérifications. Un export standard Blender peut
   répartir les matériaux en primitives et réordonner/séparer les sommets : ne pas
   réutiliser l’ancien binding avec ce nouveau fichier. La voie contrôlée fournie
   évite ce cas en repartant des buffers du GLB original.

## 4. Architecture ultérieure, sans la développer ici

Rotation 360° du corps, distinction tap/glissement, rayon puis lookup ci-dessus,
sélection d’un matériau de région, cadrage fluide vers la boîte de la région,
puis présentation des statistiques associées à l’identifiant logique. Le centre
et les bornes viennent des sommets réellement étiquetés, dans le repère du modèle,
puis sont transformés dans le repère caméra ; aucune sphère ou halo de sélection.
Les animations doivent pouvoir être interrompues et l’orientation conservée.

Le zoom décrit ici est une possibilité demandée pour la suite, pas un comportement
implémenté ou imposé. Les statistiques, tonnages, séries et parts de volume ne
sont pas calculés. Aucun accès SQLite. La correspondance données d’entraînement →
identifiants restera à définir après validation visuelle, sans supposer que le
triangle ou le volume géométrique du muscle mesure un volume d’entraînement.

Quatre primitives peuvent simplifier la coloration de ce POC ; elles ne constituent
pas un budget de draw calls établi pour le corps entier segmenté. Aucune fluidité
ni consommation mémoire sur iPhone n’est annoncée sans test réel.
