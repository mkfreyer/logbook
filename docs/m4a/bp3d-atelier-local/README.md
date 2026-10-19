# Atelier local BodyParts3D — scène éditable, sculpture à réaliser

[Rapport et verdict](../../M4A_ATELIER_ANATOMIQUE_BLENDER.md) ·
[Guide manuel précis](GUIDE_SCULPTURE.md) · [Identifiants](IDENTIFIANTS.md) ·
[Attribution et licences](ATTRIBUTION.md)

**Ouvrir [atelier-pectoraux-deltoide.blend](atelier-pectoraux-deltoide.blend).**
Blender 4.3.2 est la version contrôlée. Le fichier est autonome : pas d’add-on,
image externe, connexion réseau, pilote Python ou activation des scripts.
Le guide et les identités sont aussi embarqués comme Text datablocks.
Faire Save As avant toute intervention artistique.

Ce fichier ne contient **aucune sculpture artistique réussie ou revendiquée**.
Les neuf portions de travail sont identiques aux géométries sources après
normalisation et soudure des positions exactement identiques dans chaque OBJ.
La pose et les volumes restent ceux de l’atlas ; aucun corps complet, peau de
soutien, primitive musculaire, fusion globale ou D3/D4 n’est construit.

| Scène | Usage |
| --- | --- |
| `00_ATELIER` | Neuf copies éditables, trois groupes musculaires, repères osseux et de raccord |
| `01_SOURCES` | Neuf portions originales, données natives protégées de la sélection |
| `02_DEMO_PEC_G` | Trois portions du pectoral gauche entièrement orange |
| `03_DEMO_PEC_D` | Trois portions du pectoral droit entièrement orange |
| `04_DEMO_DELTOIDE_G` | Trois portions du deltoïde gauche entièrement orange |

Dans `TRAVAIL`, les groupes `source_FJ…` préservent la provenance ; les groupes
`DIAG_ILOT_…` isolent les composantes disjointes à inspecter. Les shape keys
`VOLUME_MANUEL` et `RACCORDS_MANUELS` sont vides et à zéro. Les scènes DEMO
partagent ces meshes de travail avec des matériaux d’objet différents : la
coloration n’utilise aucun masque de faces projeté. Les espaces géométriques
sources restent présents, même lorsque toutes les portions sont orange.

[controle-scene.json](controle-scene.json) contient les mesures réelles et les
contrôles de conservation/sélection. Les contacts BVH sont des candidats à
inspecter, pas un verdict médical de collision.
[reproduction-verifiee.json](reproduction-verifiee.json) consigne le contrôle
d’une reconstruction indépendante. Le SHA du conteneur `.blend` peut varier
entre sauvegardes ; les données et les propriétés sont vérifiées séparément.

## Reproduire sans l’archive officielle complète

Depuis la racine du dépôt, avec Blender 4.3.2 et son NumPy intégré :

```bash
mkdir -p work/m4a-atelier-reproduction
cp docs/m4a/bp3d-atelier-local/sources-originales.zip work/m4a-atelier-reproduction/
cp docs/m4a/bp3d-atelier-local/GUIDE_SCULPTURE.md work/m4a-atelier-reproduction/
blender --background --factory-startup --disable-autoexec --threads 3 --python tools/m4a/prepare_bp3d_atelier.py -- --bundle work/m4a-atelier-reproduction/sources-originales.zip --output work/m4a-atelier-reproduction
blender --background --factory-startup --disable-autoexec --threads 3 --python tools/m4a/check_bp3d_atelier.py -- --prepared work/m4a-atelier-reproduction
```

Le script lit le guide et la notice depuis le dépôt pour les embarquer ; les
options `--guide` et `--attribution` permettent d’indiquer leurs chemins.
Le ZIP contient les quinze OBJ **byte pour byte**, le manifeste d’identité et
la notice, avec leurs en-têtes historiques. Aucun téléchargement n’est requis.

Pour reconstituer le sous-ensemble depuis la source officielle déjà acquise :

```bash
python tools/m4a/acquire_sources.py --output-dir work/bodyparts3d --verify-only
blender --background --factory-startup --disable-autoexec --threads 3 --python tools/m4a/prepare_bp3d_atelier.py -- --source-dir work/bodyparts3d --output work/m4a-atelier-depuis-sources
```

La première commande suppose les sept fichiers officiels déjà présents.
Les empreintes de l’archive et des deux tables d’identité sont contrôlées par
le préparateur ; les quinze OBJ du ZIP local sont vérifiés individuellement.
Les outils préparent et contrôlent un atelier, sans sculpter automatiquement.
L’option `--diagnostic-dir` du contrôleur peut générer des vues techniques de
sources ; celles-ci ne constituent pas des rendus de résultat premium.

Budget d’acquisition : 0 €. Pas de rig, GLB, moteur tactile, app, SQLite ou M4B.
Aucune performance mobile ou validation artistique démontrée. Arrêt avant toute
extension : suivre le guide sur une copie puis soumettre une vraie passe artistique.
