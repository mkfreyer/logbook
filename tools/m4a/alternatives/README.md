# Rendus des alternatives M4A

Outils hors application. Ils génèrent et rendent de vraies géométries ; aucune
segmentation musculaire ou scène interactive n’est créée. La comparaison reste
en cours dans [M4A_CHOIX_MODELE.md](../../../docs/M4A_CHOIX_MODELE.md).

Pour restaurer les sources, fichiers Blender et rendus après redémarrage, lire
le [guide de reprise](../../../docs/M4A_REPRISE_ENVIRONNEMENT.md).
`restore_checkpoint.py` utilise uniquement la bibliothèque standard Python 3.11+,
vérifie les empreintes et refuse tout écrasement d’un dossier de travail existant.

## Source MPFB

- MPFB : `https://github.com/makehumancommunity/mpfb2`, commit
  `3af0cd5a2ffba072e93a34e5f6f494fdc4813ddf`.
- Yeux low-poly MakeHuman : commit
  `a8bc2d54ff0ac92e78ff71431b1023eda42bf482`, fichiers
  `makehuman/data/eyes/low-poly/low-poly.obj` et `low-poly.mhclo`.
- Assets CC0 ; le générateur GPL reste un outil externe. Les sources et fichiers
  Blender de travail ne sont pas ajoutés au runtime Logbook.

Avec Python de Blender 4.3.2, depuis la racine du dépôt, adapter les chemins :

```sh
blender --background --factory-startup --python-exit-code 1 \
  --python tools/m4a/alternatives/generate_mpfb.py -- \
  --mpfb-dir /chemin/mpfb2 --eyes-dir /chemin/eyes-low-poly \
  --work-dir /chemin/work/mpfb-user --output /chemin/work/mpfb-athletic.blend

blender --background --factory-startup --threads 8 --python-exit-code 1 \
  --python tools/m4a/alternatives/render_comparison.py -- \
  --blend /chemin/work/mpfb-athletic.blend \
  --objects MPFB_Athletic_Body MPFB_Core_Eyes \
  --candidate mpfb-athletic --output /chemin/work/renders/mpfb-athletic \
  --samples 128
```

Le bootstrap charge l’extension dans un espace de noms de session et redirige ses
données vers `--work-dir` ; il ne l’installe pas dans le profil utilisateur. Le
message de classe de préférences déjà enregistrée provient de cette initialisation
préalable nécessaire pour définir le dossier de travail. Le matériau des yeux
est ignoré : la géométrie seule est chargée, puis reçoit le matériau commun.

## Protocole commun

- Corps entier, 900 × 1400 pixels, Cycles CPU, 128 échantillons, sans débruitage.
- Hauteur normalisée à 1,8 unité de scène, transformation uniforme conservant les
  proportions ; caméra orthographique 2,30 unités, angles 0°, −35°, 180°.
- Satin gris bleuté : couleur linéaire `(0.23, 0.30, 0.41)`, rugosité 0,37,
  métallisation 0,12 ; fond bleu nuit et quatre éclairages fixes identiques.
- Matériaux et textures des sources remplacés pour comparer le relief géométrique.
  Normales lissées ; un niveau de subdivision pour MPFB et le stylisé,
  Multires source niveau 3 sans subdivision supplémentaire pour le réaliste,
  documentés dans les métadonnées. Pas de sculpture, déformation anatomique inventée ou retouche d’image.
- Pose native conservée ; les éventuelles différences de pose entre modèles
  doivent être signalées. Le cadrage sera contrôlé pour chaque modèle ajouté.

Chaque dossier contient `front.png`, `three-quarter.png`, `back.png` et
`render-metadata.json`. Le script n’introduit aucun muscle ou groupe de sélection.
Le SHA du `.blend` local identifie l’exécution ; la reproduction de la géométrie
repose sur les sources épinglées et paramètres, pas sur l’égalité binaire de deux
fichiers Blender contenant des métadonnées de sauvegarde.

## Acquisition et inventaire Blender Studio vérifiés

Source officielle acquise lors de la reprise depuis `1da5ba6` :
`https://download.blender.org/demo/asset-bundles/human-base-meshes/human-base-meshes-bundle-v1.4.1.zip`.
Taille **50 643 039 octets**, SHA-256 et CRC vérifiés ; licence et inventaire
conservés dans [blender-studio](../../../docs/m4a/alternatives/blender-studio/).
Le fichier original reste dans `/workspace/work/m4a-alternatives/sources/blender-studio/`.

```sh
python3 tools/m4a/alternatives/acquire_studio.py \
  --destination /workspace/work/m4a-alternatives/sources/blender-studio

blender --background --factory-startup --disable-autoexec --threads 2 \
  --python-exit-code 1 --python tools/m4a/alternatives/inspect_studio.py -- \
  --blend /workspace/work/m4a-alternatives/sources/blender-studio/extracted/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend \
  --output /workspace/work/m4a-alternatives/studio-selected-inventory.json
```

Pour les rendus, réutiliser `render_comparison.py`, `--samples 128`, et le même
fichier source. Le réaliste utilise `--candidate studio-realistic`,
`--objects GEO-body_male_realistic GEO-body_male_realistic.eye.L GEO-body_male_realistic.eye.R`
et **`--subdivision 0`** : son Multires source niveau 3 est déjà évalué en entier.
Le stylisé utilise `--candidate studio-stylized`,
`--objects GEO-body_male_stylized GEO-body_male_stylized.eye.L GEO-body_male_stylized.eye.R`
et **`--subdivision 1`**, comme MPFB. Ajouter `--disable-autoexec` au lancement.
Les modificateurs source, niveaux et décomptes de base/évalués sont consignés
dans les nouvelles métadonnées. Les trois images MPFB sont reprises telles quelles.

Les corps du bundle ont des face sets numériques de sculpture (102 réaliste,
42 stylisé), sans correspondance musculaire nommée. Ils ne dispensent pas d'une
segmentation anatomique après choix. Aucun script ne modifie SQLite ou le runtime.

## Planche et contrôles de la comparaison

La planche est une mise en page des PNG, avec réduction uniforme et légendes,
sans retouche de l'anatomie. Pillow est utilisé uniquement comme outil d'audit
externe, sans dépendance ajoutée à Logbook :

```sh
python3 tools/m4a/alternatives/build_sheet.py \
  --renders-root docs/m4a/alternatives \
  --output /workspace/work/m4a-alternatives/comparaison.png
```

Les neuf empreintes des images sont conservées dans
[render-files.json](../../../docs/m4a/alternatives/render-files.json).
À cette reprise : dimensions/protocoles contrôlés, trois PNG MPFB identiques à
`1da5ba6`, inventaire Blender reproduit indépendamment à l'identique, planche
reproduite pixel pour pixel, JSON/liens/syntaxe Python et `git diff --check` validés.
Les tests applicatifs n'ont pas été relancés localement pour cette livraison
documentaire ; aucun code de l'application ni fichier SQLite n'a changé.
