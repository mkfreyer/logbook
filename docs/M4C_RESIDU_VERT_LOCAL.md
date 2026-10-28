# M4C — retrait du petit résidu vert

**Proposition pour validation visuelle**, depuis `71f70dc`, dans la PR #17 en
brouillon. La capture désigne le petit retour du masque postérieur droit sur
le haut du bras. Seul ce résidu est retiré vers le **gris neutre**.

- [Avant / après serré, même caméra et même cadrage](m4c/meshy-deltoides-residu-local/renders/comparatif-residu-serre.png)
- [Après sans annotation](m4c/meshy-deltoides-residu-local/renders/apres-gros-plan.png)
- [Vue plus large : portion postérieure conservée](m4c/meshy-deltoides-residu-local/renders/comparatif-contexte.png)
- [Contrôle sous deux angles voisins](m4c/meshy-deltoides-residu-local/renders/comparatif-angles-voisins.png)
- [Rendu neutre](m4c/meshy-deltoides-residu-local/renders/neutre-face.png)
- [Sources Blender, GLB, masques et reproduction](m4c/meshy-deltoides-residu-local/README.md)

## Cause et correction

Le défaut est **présent dans les données du masque** : trois impacts 3D pris
dans l’ergot retournent l’ID `8` (`deltoid.right.posterior`) et un poids vert
interpolé de **1,0** avant correction. Ce n’est donc pas un simple débordement
causé par le filtrage. La limite précédente conservait un petit retour convexe
au raccord inférieur de l’épaule.

Une courte courbe continue remplace uniquement ce retour. Les repères de la
vue de référence sont projetés sur la **surface 3D réelle** par raycast ; une
emprise locale en coordonnées du modèle et un contrôle de proximité avec la
surface visible limitent la peinture UV. Les texels verts situés à l’extérieur
de cette courbe deviennent neutres. Aucun pixel d’une autre zone ne change et
aucune surface grise n’est ajoutée au vert. Le filtrage linéaire d’affichage
reste inchangé ; l’identification continue d’utiliser l’atlas discret.

**1 142 texels** passent de `8` à `0` dans l’atlas 2 048 × 2 048. Environ
**95,25 %** des texels du postérieur droit de `71f70dc` sont conservés.
Ce pourcentage inclut les marges UV : il ne mesure ni la surface anatomique ni
le volume musculaire. Les **sept autres fichiers de masque sont identiques
octet pour octet**, y compris le postérieur gauche. Aucune segmentation
complète n’est relancée.

## Fichiers concernés

Dans `docs/m4c/meshy-deltoides-residu-local/` :

- `textures/muscle-ids.png` : atlas d’identification corrigé ;
- `textures/deltoid.right.posterior.png` : masque séparé dérivé ;
- `textures/masks-rgba-1.png` : seul le canal alpha, correspondant à l’ID 8,
  change ; le premier pack et les trois autres canaux restent identiques ;
- `textures/control-basecolor.png` : palette statique dérivée de la correction ;
- `exports/meshy-eight-zones-control.glb` : PNG embarqués actualisés, buffers
  de géométrie copiés sans recalcul ;
- `meshy-residu-corrige.blend` : image de masque mise à jour et embarquée ;
- `regions.json`, `region-binding.json`, `patch-guides.json` et audits :
  huit IDs conservés, bornes du postérieur droit actualisées et traçabilité.

Les sept masques conservés et les témoins de sélection sont également copiés
dans ce dossier pour fournir un ensemble de contrôle complet. Les versions
précédentes restent intactes dans leurs dossiers et dans l’historique Git.

## Vérifications

- Seule transition d’ID autorisée : **postérieur droit → neutre**. Les trois
  impacts dans l’excroissance retournent désormais `0`, avec un poids vert
  de **0,0** ; cinq témoins voisins verts, bleu et gris sont conservés.
- Une composante par zone après recollage des coutures UV ; aucun trou gris
  interne détecté sur les texels de surface contrôlés. Les huit raycasts
  Three.js sur le modèle source et l’export retrouvent les huit IDs.
- Positions, normales, indices et UV des exports sont **identiques octet
  pour octet** à `71f70dc`. Même contrôle dans Blender. Toujours **110 588
  triangles**, 55 288 sommets source, 60 622 sommets dans le contrôle GLB
  avec les doublons UV déjà présents. Aucun coût géométrique supplémentaire.
- Huit vrais rendus Blender, matériau mat et éclairage conservés. Le gros
  plan est rendu directement en 500 × 650 pixels via une fenêtre de la caméra
  haute résolution, sans agrandissement artificiel de la capture. Caméra,
  cadrage et paramètres sont identiques entre chaque paire avant/après.
- Le rendu neutre de face est **identique pixel par pixel** à celui de
  `71f70dc`. La tête, les cheveux, le cou et le corps restent inchangés.
- Les **134 fichiers applicatifs protégés** sont inchangés : visualiseur,
  GLB validé `e45e5d8`, Expo SDK 58, fonctionnalités existantes et SQLite.
  Aucune nouvelle mesure sur iPhone n’est revendiquée pour cette retouche.

[Audit des données](m4c/meshy-deltoides-residu-local/verification.json) ·
[Diagnostic et impacts 3D](m4c/meshy-deltoides-residu-local/cause-and-probes.json) ·
[Continuité](m4c/meshy-deltoides-residu-local/continuity-audit.json) ·
[Caméras et neutralité](m4c/meshy-deltoides-residu-local/render-verification.json) ·
[Raycasts](m4c/meshy-deltoides-residu-local/picking-audit.json).

Les rendus montrent une bordure plus régulière et le retrait de l’ergot ciblé.
La précision reste celle de l’atlas et des contrôles échantillonnés ; il ne
s’agit pas d’une validation anatomique médicale. **Arrêt pour votre validation
visuelle.** Aucun branchement interactif, carte thermique, modification
applicative ou SQLite, ni fusion.

Model created with Meshy — [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Modification Logbook limitée au masque local et à ses dérivés.
