# M4C — outils hors application

Ces scripts produisent et vérifient **une proposition de huit zones**. Ils ne
sont importés ni par Logbook, ni par son visualiseur. Aucun code tactile,
statistique, carte thermique ou migration SQLite.

Source unique : `assets/models/meshy-e45e5d8.glb`, SHA-256 vérifié à chaque
lecture. Ne jamais remplacer ce fichier par un export de contrôle.

Prérequis gratuits : Blender 4.3.2, Python 3.12 avec les paquets du fichier
`requirements.txt`, Node.js 24 et les dépendances npm déjà verrouillées.
Le Python de Blender utilise son NumPy embarqué ; les étapes de peinture/audit
avec SciPy et Pillow utilisent le Python externe.

Depuis la racine du dépôt, sur **une copie de travail** (les résultats du
prototype sont régénérés) :

```sh
python -m pip install -r tools/m4c/requirements.txt
blender -b -t 4 --python-exit-code 1 --python tools/m4c/prepare_uv.py
python tools/m4c/bake_masks.py
blender -b -t 4 --python-exit-code 1 --python tools/m4c/assemble_blender.py
python tools/m4c/export_control.py
python tools/m4c/audit_asset.py
python tools/m4c/audit_continuity.py
node tools/m4c/audit-picking.mjs
blender -b -t 4 --python-exit-code 1 --python tools/m4c/audit_blender_import.py
blender -b -t 4 --python-exit-code 1 --python tools/m4c/render_controls.py
python tools/m4c/compose_boards.py
python tools/m4c/measure_delivery.py
```

Dans cet environnement Linux restreint, les caches peuvent être placés dans
`/workspace/.cache` via `MPLCONFIGDIR` et `BLENDER_USER_CONFIG`. Pour les petits
calculs matriciels, `OPENBLAS_NUM_THREADS=1` évite une surallocation de threads.
Ces variables ne font pas partie de l’application.

Le fichier `regions.json` décrit les repères en mètres dans le repère original
du GLB, la convention anatomique et les huit IDs. `regions.py` porte les règles
continues en 3D ; `front_visibility.py` exclut les surfaces plus profondes sous
le pectoral. Il ne s’agit pas d’une reconnaissance anatomique automatique.
Toute modification des repères doit refaire les contrôles et attendre une
validation visuelle ; ne pas réutiliser les coordonnées du mannequin P4.

Le fichier Blender contient un maillage intact, des UV et deux images RGBA
embarquées. Dans le matériau `M4C_HUIT_ZONES__PALETTE_EDITABLE`, chaque zone a :

- `SHOW::<id>` : 1 = couleur de contrôle, 0 = matériau neutre ;
- `COLOR::<id>` : couleur indépendante éditable.

Les PNG de masques séparés sont des dérivés de l’atlas d’IDs. Ne pas les éditer
indépendamment puis prétendre que le picking correspond encore à la couleur.
L’ID est une **donnée linéaire discrète**, sans interpolation ni conversion sRGB.
Les poids et couleurs de rendu peuvent être interpolés.

`audit-picking.mjs` exécute les véritables raycasts Three.js, avec les buffers
source et exportés. `surface-lookup.mjs` est une préparation portable de lookup,
**pas une fonctionnalité d’interface installée dans Logbook**.
Les résultats sont dans `docs/m4c/meshy-huit-zones`.
