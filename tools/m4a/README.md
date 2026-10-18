# Reproduire l’audit BodyParts3D de M4A

Ces outils produisent des preuves d’audit à partir de la source officielle. Ils
ne génèrent pas un asset produit validé, ne modifient pas SQLite et ne lancent
pas M4B. Une identité FMA ou une topologie correcte ne valide ni l’anatomie
visible ni la conformité à l’image de référence. Voir [M4A](../../docs/M4A.md).

Exécuter les commandes depuis la racine du dépôt. Prévoir Python 3.10 ou plus
(bibliothèque standard uniquement), `curl`, Blender 4.3.2 pour les rendus et
plusieurs Go libres. Les inventaires complets et surtout les huit rendus CPU
peuvent prendre plusieurs minutes. Les résultats intermédiaires restent dans
`work/` ; ne pas publier l’archive, les OBJ ou les inventaires volumineux dans Git.

## 1. Acquérir et vérifier les sources officielles

Le fichier [provenance.json](../../docs/m4a/bodyparts3d/provenance.json) contient
les URL, tailles et SHA-256 des dix fichiers acquis le 17 octobre 2026 : trois
pages, six tables IS-A/PART-OF et l’archive OBJ. Le pipeline télécharge et
vérifie uniquement les **sept fichiers de données** : l’archive et les six
tables. Les empreintes des trois pages HTML sont des observations datées,
pas des entrées épinglées : leurs nonces dynamiques peuvent changer à chaque
requête. Consulter ces pages séparément pour les informations de publication
et de licence. Les empreintes ont été calculées localement après téléchargement,
pas fournies par l’éditeur.

- Page officielle : <https://dbarchive.biosciencedbc.jp/en/bodyparts3d/download.html>
- Licence : <https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html>
- Archive : <https://dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/isa_BP3D_4.0_obj_99.zip>
- Taille de l’archive : **142 903 898 octets**, **2 234 OBJ**.
- SHA-256 de l’archive : `40665852c49f218326590e204db91064a1ecfc3c6f8cbd7bbbcaac62c7cd409e`.

```sh
AUDIT_DIR="work/m4a-audit"
python tools/m4a/acquire_sources.py --output-dir "$AUDIT_DIR/source"
python tools/m4a/acquire_sources.py --output-dir "$AUDIT_DIR/source" --verify-only
```

L’acquisition réutilise les fichiers déjà vérifiés, télécharge les absents avec
`curl` et conserve une interruption en `.part` pour permettre la reprise HTTP.
Un fichier final existant incorrect provoque un arrêt sans écrasement. Un
téléchargement n’est renommé qu’après vérification de sa taille et de son SHA.
Le mode `--verify-only` n’accède jamais au réseau. La politique réseau de
l’environnement doit autoriser `dbarchive.biosciencedbc.jp`.

`LATEST` peut changer : une différence d’empreinte demande un nouvel audit de
provenance, jamais une acceptation automatique. Une coupure réseau peut se
reprendre en relançant la même commande. Si une réponse complète est différente
de l’empreinte attendue, examiner la source avant d’enlever le `.part`.

## 2. Construire le manifeste anatomique et les listes d’extraction

```sh
python tools/m4a/build_manifest.py \
  --isa-dir "$AUDIT_DIR/source" \
  --partof-dir "$AUDIT_DIR/source" \
  --output-dir "$AUDIT_DIR/anatomy"
```

Les répertoires IS-A et PART-OF peuvent être distincts. La table de noms et la
table concept/élément définissent les identités ; aucun nom de muscle n’est
déduit d’une position, d’une boîte englobante ou du nom d’un OBJ.

Le script écrit automatiquement tous les fichiers utilisés dans la suite :

| Fichier dans `anatomy/` | Contenu |
| --- | --- |
| `selection-candidate.json` | 62 sélections latéralisées, 31 groupes, 86 OBJ ; identités documentées, sans validation produit |
| `selection-components.tsv` | Correspondances FMA/OBJ et lignes des tables officielles |
| `candidate-surface-obj-ids.txt` | Les 86 OBJ des sélections candidates |
| `all-muscle-audit-obj-ids.txt` | 425 éléments des concepts musculaires documentés et des candidats |
| `skin-obj-ids.txt` | FJ2810, peau / FMA7163 |
| `bone-obj-ids.txt` | 204 éléments, union de `bone organ` / FMA5018 et `zone of bone organ` / FMA10483 |
| `extraction-elements.json` | Les 426 éléments muscles + peau, pour le diagnostic topologique |
| `bone-elements.json` | Les 204 éléments osseux et leurs concepts source |
| `render-elements.json` | L’union des 630 éléments nécessaires aux deux variantes de rendu |

Les listes osseuses et d’extraction ne nécessitent aucune étape manuelle.
Le manifeste conserve explicitement les identités recherchées mais non
retrouvées dans les six tables : `latissimus dorsi` et `rectus abdominis`.
Cette absence de nom ne prouve pas à elle seule une absence de géométrie.

## 3. Inventorier l’archive et extraire les OBJ

```sh
python tools/m4a/inventory.py \
  --archive "$AUDIT_DIR/source/isa_BP3D_4.0_obj_99.zip" \
  --tables-dir "$AUDIT_DIR/source" \
  --elements-file "$AUDIT_DIR/anatomy/render-elements.json" \
  --extract-dir "$AUDIT_DIR/geometry/obj" \
  --output "$AUDIT_DIR/geometry/full-inventory.json"
```

Cette commande vérifie taille, SHA-256 et CRC de **tous** les membres avant
d’extraire le moindre OBJ. Elle inventorie les 2 234 éléments, mais extrait
seulement les 630 demandés dans des noms fixes `FJ….obj`. L’inventaire comprend
indices, coordonnées finies, bornes, faces, triangles dégénérés, arêtes et
appartenances aux tables. Il ne transforme pas les données source.

Pour recréer seulement les OBJ manquants à partir d’un inventaire complet déjà
conservé, utiliser la même commande avec `--extract-only` et un autre fichier
`--output`, par exemple `geometry/extraction-inventory.json`. Ne pas écraser
`full-inventory.json` avec ce rapport abrégé : le résumé exige ses statistiques.

## 4. Diagnostiquer les coutures et produire le résumé stable

```sh
python tools/m4a/topology_diagnostics.py \
  --obj-dir "$AUDIT_DIR/geometry/obj" \
  --elements-file "$AUDIT_DIR/anatomy/extraction-elements.json" \
  --output "$AUDIT_DIR/geometry/selected-topology.json"
python tools/m4a/summarize_inventory.py \
  --audit-dir "$AUDIT_DIR" \
  --output "$AUDIT_DIR/geometry/audit-summary.json"
```

Le diagnostic recalcule la connectivité après identification des coordonnées
strictement identiques à l’intérieur de chaque OBJ. Aucun arrondissement,
seuil spatial, déplacement, union entre organes ou réparation n’est appliqué.
Les OBJ restent inchangés. Les indices du fichier OBJ peuvent créer des
coutures de normales : leurs arêtes de bord brutes ne suffisent donc pas à
conclure à des trous. Le résumé rassemble les chiffres des 2 234 éléments et
le diagnostic détaillé des 426 éléments muscles + peau.

Les chemins locaux et durées restent dans les grands inventaires, pour la
traçabilité de chaque exécution. Le résumé et le manifeste publiés sont
indépendants de ces chemins et peuvent être comparés octet par octet :

```sh
cmp "$AUDIT_DIR/anatomy/selection-candidate.json" docs/m4a/bodyparts3d/selection-candidate.json
cmp "$AUDIT_DIR/anatomy/selection-components.tsv" docs/m4a/bodyparts3d/selection-components.tsv
cmp "$AUDIT_DIR/geometry/audit-summary.json" docs/m4a/bodyparts3d/audit-summary.json
```

## 5. Produire les vues d’audit

```sh
blender --background --threads 8 --python tools/m4a/render_audit.py -- \
  --obj-dir "$AUDIT_DIR/geometry/obj" \
  --anatomy-dir "$AUDIT_DIR/anatomy" \
  --out-dir "$AUDIT_DIR/render" \
  --mode skin --samples 128
blender --background --threads 8 --python tools/m4a/render_audit.py -- \
  --obj-dir "$AUDIT_DIR/geometry/obj" \
  --anatomy-dir "$AUDIT_DIR/anatomy" \
  --out-dir "$AUDIT_DIR/render" \
  --mode muscles-bones --samples 128 --orange-pectorals
```

Chaque variante écrit `front.png`, `three-quarter.png`, `side.png`, `back.png`
et `render-metadata.json` dans son propre dossier. `--views front` permet un
contrôle réduit ; les valeurs disponibles sont `front,three-quarter,side,back`.
Le mode optionnel `muscles` omet les os, il ne fait pas partie de la série finale.

Paramètres de la série finale : Blender 4.3.2, Cycles CPU, 128 échantillons,
600 × 1000 px, AgX, sans débruitage, subdivision 0. La compilation Blender de
l’audit ne proposait pas OpenImageDenoise ; le script désactive explicitement
le débruitage pour reproduire cette série. Le rendu est déterminé par ces
réglages, mais les pixels peuvent varier selon la version de Blender et le
matériel. Les images ne sont donc pas comparées par empreinte entre machines.

Le script copie les coordonnées source, fusionne seulement les positions
exactement égales au sein de chaque OBJ pour le calcul des normales lissées,
puis applique une translation et une échelle uniforme. Il ne sculpte pas le
corps. +Z est supérieur, −Y antérieur et +X gauche anatomique. La hauteur est
normalisée à 1,80 pour le cadrage, sans attribuer d’unité physique à la source.
Les quatre angles sont 0°, −35°, −90° et 180°. Matériau gris bleuté satiné,
éclairage doux et fond bleu nuit sont identiques entre variantes.

Le rendu `skin` contient un objet (101 691 sommets distincts, 203 382 faces).
`muscles-bones` contient 629 objets (1 460 004 sommets distincts, 2 912 682
faces). Les six vrais composants latéralisés du grand pectoral sont orange.
La peau n’est pas superposée aux muscles dans cette seconde variante.

Les métadonnées enregistrent IDs source, bornes, transformation, soudure exacte,
réglages, comptes et caméra. Les chemins d’images du script portable sont
relatifs au dossier contenant ces métadonnées ; c’est la seule différence de
chemin attendue avec les métadonnées brutes de la première exécution.

Les vues montrent deux alternatives de la source, pas un mannequin complet
inventé. La peau seule ne présente pas la définition musculaire attendue et
l’assemblage muscles + os reste un écorché. L’audit ne valide donc pas le
rendu produit demandé. L’attribution à conserver figure dans
[ATTRIBUTION.md](../../docs/m4a/bodyparts3d/ATTRIBUTION.md).
