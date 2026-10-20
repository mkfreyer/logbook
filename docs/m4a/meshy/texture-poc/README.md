# Meshy — masque peint unique du pectoral gauche

[Rapport et verdict](../../../M4A_MESHY_MASQUE_PEINT.md) ·
[Blender](meshy-painted-mask.blend) · [Rendus](renders) · [Contrôles](verification.json)

**Approche prometteuse pour le contour de ce POC uniquement.** Aucun autre muscle
testé, aucun code applicatif. Base `898aac6`, géométrie Meshy conservée.

## Sources

- `painted-contour.svg` : contour de peinture en courbes, dessiné dans le repère
  1000 × 840 de la caméra `CAM_DETAIL_TROIS_QUARTS` existante. Pas une capture retouchée.
- `textures/projection-stencil.png` : raster du dessin avec antialiasing.
- `textures/pectoralis-left-mask.png` : résultat de projection sur le UV local,
  PNG 1024² gris, **données linéaires**, un seul identifiant `pectoralis.left`.
- `uv-loops.f32` : 95 426 × 3 × 2 float32 little-endian, UV Blender par coin de
  triangle, dans l’ordre original du GLB. `uv-chart-triangles.u32` liste les
  triangles du support UV, pas une nouvelle segmentation musculaire.
- `meshy-painted-mask.blend` : deux scènes, neutre et masque peint ; un seul
  mesh partagé. Le masque utilisé par le shader est packed, donc embarqué.
  Les textes contiennent le SVG, ce guide, les paramètres du POC et la provenance
  Meshy. Les anciens guides d’édition de faces ne sont pas embarqués dans ce POC.
- `build.json` : empreintes, origine du Blender, paramètres, contrôles UV et
  visibilité de la peinture projetée.
- `export/meshy-painted-selection.glb` : présentation PBR statique avec orange,
  trois PNG embarqués, UV, normales, une primitive et conservation de l’ordre
  des triangles source. `export/vertex-to-source.u32` est la correspondance des
  sommets exportés vers les originaux, après duplication aux coutures UV.
- `textures/selected-basecolor-srgb.png` et
  `textures/selected-coat-roughness-metallic-linear.png` : textures PBR précalculées
  du test GLB ; canaux R=coat, G=roughness, B=metallic pour la seconde. Elles ne
  sont pas nécessaires au shader Blender, qui mélange les matériaux via le masque.

Le source original reste [../source.glb](../source.glb), SHA-256
`9fab861a65407e69b9401bec077bf7b40f58d36404e80bad9db6147f24320a14`.
Les anciens fichiers de régions et tous leurs rendus restent intacts.
L’attribut historique `muscle_zone` hérité du fichier base n’est **pas** la source
de vérité de cette nouvelle sélection ; le shader utilise uniquement le masque UV.

## Édition après validation

Ouvrir la scène `01_MASQUE_PEINT`. Le matériau de l’objet expose le nœud image
`MASK__pectoralis.left__linear`, UV `UV_LOCAL_PECTORAL`. Le noir laisse le bleu,
le blanc donne l’orange ; le bord antialiasé conserve une transition très courte.
Les reliefs viennent toujours du Meshy et de ses normales lissées.

Il est possible de reprendre cette image en Texture Paint ou de modifier le SVG
et refaire la projection. Ces deux voies ne sont pas équivalentes : régénérer
depuis le SVG écraserait une peinture manuelle ultérieure. Faire une copie avant
édition, puis sauvegarder l’image et le Blender. **Ne pas peindre la case noire
réservée au reste du corps** : les faces non dépliées y partagent un même point.
Ce UV local ne convient pas à la peinture d’autres muscles sans préparation.

## Futur pointage UV, non implémenté dans l’app

Le GLB exporté ne change pas l’ordre des triangles : le triangle source est le
`faceIndex` de son unique primitive. Cela est vérifié avec la table des sommets,
pas supposé pour tous les chargeurs ou optimiseurs. Après interpolation UV au
point d’impact, le canal rouge du masque échantillonné en linéaire et clamp donne :

```js
// Contrat conceptuel ; aucun moteur tactile ou code de l’app livré ici.
const regionId = maskValue >= 0.5 ? 'pectoralis.left' : null;
```

PNG : ligne 0 en haut. UV Blender : V=0 en bas. **UV glTF : (U, 1−V Blender)**,
donc la ligne PNG se calcule avec le V glTF directement. Ne pas ajouter un autre
retournement aux textures de GLTFLoader. Le masque est en données linéaires,
jamais sRGB. L’échantillonnage CPU doit gérer interpolation et clamp ; la texture
couleur PBR est, elle, sRGB. Le binding expose le masque comme texture glTF 2 via
les extras du matériau ; cette texture n’est pas utilisée par le PBR standard et
doit être chargée explicitement pour une interactivité future.

L’export affiche l’orange précalculé. Pour une sélection activable à la volée,
un futur shader devra mélanger bleu et orange avec le masque et l’état sélectionné,
ou mettre à jour les textures. Aucun tel runtime, WebView ou zoom n’est intégré.

## Reproduction, sans changer le dessin

Depuis la racine du dépôt ; Python avec NumPy/Pillow/SciPy, Blender 4.3.2 :

```bash
python tools/m4a-meshy/raster_painted_contour.py --prepared docs/m4a/meshy
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-meshy/build_texture_poc.py -- --prepared docs/m4a/meshy
python tools/m4a-meshy/export_texture_poc.py --prepared docs/m4a/meshy
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-meshy/render_texture_poc.py -- --prepared docs/m4a/meshy
python tools/m4a-meshy/compare_texture_poc.py --prepared docs/m4a/meshy
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 1 --python tools/m4a-meshy/finish_texture_poc.py -- --prepared docs/m4a/meshy
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 1 --python tools/m4a-meshy/check_texture_poc.py -- --prepared docs/m4a/meshy
```

Le build édite seulement UV/matériaux et vérifie les sommets/indices à l’identique.
L’export contrôlé part des buffers originaux, conserve l’ordre des faces et
documente les sommets dupliqués pour UV. Les raycasts vérifient aussi deux valeurs
de masque différentes **dans le même triangle**. Ne pas utiliser `segment.py`
pour reproduire cette méthode, ni l’ancien binding à quatre primitives pour ce GLB.
Les empreintes de conteneurs Blender peuvent varier selon la session ; les
contrôles relisent les tableaux de géométrie, UV, textures et bindings réels.
Le post-traitement final change seulement les textes informatifs : l’empreinte
du Blender utilisé pour les rendus et celle du fichier livré sont conservées
séparément dans `build.json` et les métadonnées de rendu.

Model created with Meshy – CC BY 4.0 License.
[Provenance existante conservée](../LICENCE_ET_PROVENANCE.md).
PR #12 en brouillon, PR #11 intacte, aucun achat, Astra, M4B, SQLite ou fusion.
Arrêt pour validation avant toute extension ou intégration.
