# Contrôle arrière de daf5878 — rendus seulement

[Rapport et liens directs de toutes les vues](../../M4C_VERIFICATION_VISUELLE_ARRIERE.md).

Sources lues, sans réenregistrement :

- Après : [`meshy-residu-corrige.blend`](../meshy-deltoides-residu-local/meshy-residu-corrige.blend)
  et [masques de `daf5878`](../meshy-deltoides-residu-local/textures).
- Avant : [`meshy-eight-zones-corrected.blend`](../meshy-deltoides-limite-inferieure/meshy-eight-zones-corrected.blend),
  état `71f70dc` avant le retrait du petit résidu droit.
- Maître neutre : [`meshy-e45e5d8.glb`](../../../assets/models/meshy-e45e5d8.glb), inchangé.

Les fichiers de ce dossier sont uniquement des rendus et des métadonnées de
contrôle. Aucun nouveau modèle, texture ou masque n’est créé. Les deux petits
scripts sont des outils hors application.

Reproduction depuis la racine, avec les dépendances gratuites déjà utilisées
par les [outils M4C](../../../tools/m4c/README.md) :

```sh
blender -b -t 4 --python-exit-code 1 --python tools/m4c/render_back_validation.py
python tools/m4c/compose_back_validation.py
```

Le premier script ouvre les Blender en lecture, vérifie leurs images
embarquées, change uniquement la caméra et les réglages de rendu en mémoire,
puis écrit les PNG et les empreintes. Il n’enregistre aucun fichier Blender.
Le second vérifie la conservation des sources et les caméras des paires
avant/après ; il compose les planches sans retoucher les pixels du mannequin.

`renders/render-metadata.json` conserve les matrices de caméra, les paramètres,
les empreintes de géométrie, des lumières, des sources et des sept PNG bruts.
`verification.json` donne aussi les différences de pixels par vue ; celles-ci
ne remplacent pas l’examen visuel de la frontière.

La réserve concernant les petites irrégularités du bord vert/gris inférieur
droit est décrite dans le rapport. **Aucune correction effectuée ; validation
visuelle attendue.**

Model created with Meshy — [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
