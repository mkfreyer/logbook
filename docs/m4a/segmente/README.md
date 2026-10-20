# Reprendre le pilote segmenté

[Rapport et verdict](../../M4A_PILOTE_SEGMENTE.md) · [Licence](LICENCE.md) · [Archives](ARCHIVES.md)

## Fichiers utiles

- `pilote-haut-corps.blend` : source de travail Blender, huit pièces et un support.
- `pilote-haut-corps.glb` : neuf objets neutres, matériaux PBR individuels, sans texture.
- `source/meshy-original.glb` : entrée originale inchangée, contexte corps complet archivé.
- `../../../tools/m4a-segmente/` : courbes, partition, construction, export, contrôles, planches.
- `renders/` : 18 rendus et 7 planches/images de revue ; les noms `baseline-*` désignent
  le Meshy recadré au même cadrage, les noms `select-*` une seule pièce orange.
- `verification.json` : contrôles d'indépendance, relecture GLB, rayons et défauts détectés.
- `gltf-validation.json` : contrôle de format Khronos ; `manifest.json` : empreintes de livraison.

## Vérifier la sélection dans Blender

Ouvrir le BLEND sans exécuter de script embarqué. La scène s'ouvre sur le haut du
corps neutre. Sélectionner `M4A.pectoralis.left` dans l'Outliner ; la touche `/`
isole cet objet en vue locale. Les sept autres groupes se manipulent de la même
manière. Le matériau orange existe déjà pour une démonstration de recoloration.
Chaque pièce a un maillage et un matériau indépendants dans le BLEND sauvegardé.

`M4A.support` est le contexte ; `M4A.baseline` est un témoin masqué, exclu du GLB.
Ne pas activer ce dernier par-dessus le pilote, ce qui superposerait deux états
du modèle. Les huit pièces sont des volumes stylisés de groupes de surface,
pas des muscles internes médicaux : voir les limites du rapport avant réutilisation.

## Reproduction hors réseau

Depuis la racine du dépôt, avec Python 3 + NumPy + Pillow et Blender 4.3.2 :

```sh
python tools/m4a-segmente/partition.py /tmp/m4a-patches.npz
blender -b -t 3 --python tools/m4a-segmente/build_blender.py -- /tmp/m4a-patches.npz
blender -b -t 3 --python tools/m4a-segmente/verify_blender.py
python tools/m4a-segmente/compare.py
```

L'option `--build-only` après le NPZ construit BLEND/GLB sans lancer les rendus.
`--preview` calcule trois diagnostics rapides à 24 échantillons ; ils ne sont
pas les rendus finaux publiés. Le rendu final utilise 64 échantillons CPU sans
débruitage, le Blender de cet environnement ne fournissant pas OpenImageDenoise.
La sauvegarde Blender peut changer des métadonnées et donc l'empreinte binaire ;
la vérification porte sur la géométrie effectivement reconstruite/exportée.

Contrôle facultatif avec le module gratuit `gltf-validator` de Khronos :

```sh
node tools/m4a-segmente/validate_gltf.cjs /chemin/vers/node_modules/gltf-validator
python tools/m4a-segmente/finalize.py
```

Aucune installation ni dépendance de l'application n'est nécessaire. Les fichiers
NPZ intermédiaires et les journaux de calcul restent dans les dossiers temporaires.
Aucun OBJ supplémentaire n'est livré : le GLB garde mieux les identifiants et
matériaux, et le BLEND conserve la source éditable et le témoin.
