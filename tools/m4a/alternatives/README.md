# Rendus des alternatives M4A

Outils hors application. Ils génèrent et rendent de vraies géométries ; aucune
segmentation musculaire ou scène interactive n’est créée. La comparaison reste
en cours dans [M4A_CHOIX_MODELE.md](../../../docs/M4A_CHOIX_MODELE.md).

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
  Normales lissées et un niveau de subdivision de comparaison, documentés dans
  les métadonnées. Pas de sculpture, déformation anatomique inventée ou retouche d’image.
- Pose native conservée ; les éventuelles différences de pose entre modèles
  doivent être signalées. Le cadrage sera contrôlé pour chaque modèle ajouté.

Chaque dossier contient `front.png`, `three-quarter.png`, `back.png` et
`render-metadata.json`. Le script n’introduit aucun muscle ou groupe de sélection.
Le SHA du `.blend` local identifie l’exécution ; la reproduction de la géométrie
repose sur les sources épinglées et paramètres, pas sur l’égalité binaire de deux
fichiers Blender contenant des métadonnées de sauvegarde.

## Acquisition Blender Studio en attente

Source officielle prévue :
`https://download.blender.org/demo/asset-bundles/human-base-meshes/human-base-meshes-bundle-v1.4.1.zip`.
Le téléchargement exige une politique réseau active autorisant ce domaine.
Après récupération : vérifier taille/SHA/CRC, lire les licences internes, lister
les collections/objets masculins et leurs modificateurs, puis utiliser le même
script avec les vrais noms d’objets. Aucun modèle de substitution ne doit être
inventé pour remplir une colonne de la comparaison.
