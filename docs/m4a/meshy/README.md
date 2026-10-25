# M4A — masques de surface sur le mannequin Meshy

[Rapport et verdict](../../M4A_MESHY_MASQUES.md) ·
[Licence et provenance](LICENCE_ET_PROVENANCE.md) ·
[Raycasting, export et correction manuelle](RAYCAST_ET_EXPORT.md)

**POC partiel : sélection fonctionnelle sur géométrie intacte ; contours du
deltoïde encore provisoires.** La limite basse/postérieure ne doit pas être
considérée comme une segmentation anatomique validée. Aucun corps entier segmenté.

- [Blender éditable](renders/meshy-masques.blend) : cinq scènes partageant un
  seul mesh ; matériaux bleu argenté, sélections gauche/droite/deltoïde et diagnostic.
- [GLB source intact](source.glb) : fichier utilisateur conservé byte pour byte.
- [Masques](regions/regions.json) + [95 426 labels uint8](regions/triangle-regions.u8) :
  un ID par triangle original, identités stables `pectoralis.left`,
  `pectoralis.right`, `deltoid.left`, 0 pour le reste non attribué.
- [GLB de présentation à quatre primitives](export/meshy-zones.glb) : même mannequin,
  mêmes sommets et triangles, normales lissées et matériaux. Ce n’est pas une
  nouvelle variante anatomique. [Binding d’export](export/export-binding.json) et
  [table de permutation](export/draw-triangle-to-source.u32) obligatoires pour
  interpréter ses indices après regroupement par matériau.
- [Rendus Blender](renders) : face, trois quarts, sélection orange, détail des
  frontières et profil de contrôle. Le diagnostic orange/jaune/turquoise montre
  les trois masques, pas une sélection unique de pectoral.
- [Vérifications](verification.json) : buffers source/Blender/export et impacts de
  rayons sur les triangles source/export, sans test d’iPhone ou de moteur tactile.

Ouvrir le `.blend` avec Blender 4.3.2. Aucun add-on, script automatique, bibliothèque
liée ou image externe nécessaire. La licence et le guide sont embarqués comme
Text datablocks. Faire Save As avant toute correction ; les indices de matériau
sont l’autorité éditable des régions. Ne pas modifier les sommets ou la topologie.
Les trois régions sont chacune connectées avec une seule boucle de frontière ;
ce contrôle de continuité ne valide pas leur anatomie.

## Reproduction

Depuis la racine du dépôt, Python avec NumPy et Blender 4.3.2. Les outils sont
autonomes sur cette nouvelle branche et n’importent aucune ancienne reconstruction.
Les sorties peuvent aller dans `work/` ; garder l’arborescence `regions`, `renders`,
`export` et les deux notices si l’on veut exécuter le contrôleur complet.

```bash
python tools/m4a-meshy/segment.py --source docs/m4a/meshy/source.glb --contours docs/m4a/meshy/contours.json --output docs/m4a/meshy/regions
python tools/m4a-meshy/export_regions_glb.py --source docs/m4a/meshy/source.glb --regions docs/m4a/meshy/regions/regions.json --output docs/m4a/meshy/export
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-meshy/blender_demo.py -- --source docs/m4a/meshy/source.glb --regions docs/m4a/meshy/regions/regions.json --output docs/m4a/meshy/renders --samples 96
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-meshy/finish_demo.py -- --prepared docs/m4a/meshy
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-meshy/check_demo.py -- --prepared docs/m4a/meshy
```

Pour exporter une correction manuelle de faces, sans exporter la géométrie Blender :

```bash
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --threads 3 --python tools/m4a-meshy/save_regions.py -- --blend work/meshy-corrige.blend --source docs/m4a/meshy/source.glb --metadata docs/m4a/meshy/regions/regions.json --output work/regions-corrigees
python tools/m4a-meshy/export_regions_glb.py --source docs/m4a/meshy/source.glb --regions work/regions-corrigees/regions.json --output work/export-corrige
```

Les IDs de faces source sont contrôlés explicitement. Un export standard Blender
n’est pas supposé conserver les attributs personnalisés ou les indices. La voie
fournie garde le GLB original et écrit les masques séparément ; l’export GLB de
présentation a sa propre correspondance vérifiée par lecture des buffers écrits.
Les SHA de conteneurs `.blend` peuvent varier ; le contrôleur vérifie les tableaux
réels de sommets, de triangles et de labels, pas seulement un nom de fichier.

Aucune intégration, SQLite, M4B, achat ou fusion. Budget additionnel : 0 €.
La PR #11 est conservée intacte ; cette preuve se trouve sur une nouvelle branche
issue de `7c2aa5c47994f1bc58758302274a8c5b9693200b`.
