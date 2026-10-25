# M4C — retrait de la languette verte des deltoïdes

**Proposition ciblée à valider**, depuis `8b723d9`, PR #17 toujours en brouillon.
La languette verte visible sur la capture correspond à la vue rapprochée de
l’épaule droite, caméra avant à −45° du prototype. Le comparatif conserve cette
caméra exacte et ajoute un cadrage serré de la même région.

- [Avant / après à l’angle de référence](m4c/meshy-deltoides-limite-inferieure/renders/comparatif-angle-reference.png)
- [Contrôle des deux épaules, avant et arrière](m4c/meshy-deltoides-limite-inferieure/renders/comparatif-deux-epaules.png)
- [Profils gauche/droit et arrière trois quarts](m4c/meshy-deltoides-limite-inferieure/renders/comparatif-profils-arriere.png)
- [Blender corrigé, GLB, textures et vérifications](m4c/meshy-deltoides-limite-inferieure/README.md)

## Correction réalisée

Le rendu neutre permet de distinguer le bombé du deltoïde et le relief du haut
du bras sous son raccord inférieur. L’ancien masque vert descendait sur ce
second relief. Des repères ont été pris par raycast sur chacune des deux
épaules ; la nouvelle limite suit une courbe continue en coordonnées 3D,
avec un raccord vers l’insertion commune déjà proposée.

**Seules des surfaces vertes deviennent neutres.** Elles ne sont attribuées
ni au deltoïde moyen ni à un nouveau masque triceps. Leur localisation est
compatible avec la région supérieure du bras/tricipitale, mais ce Meshy généré
ne permet pas de certifier une subdivision anatomique médicale. Le choix
conservateur est de les laisser non attribuées jusqu’à la segmentation du bras.

La correction est adaptée séparément à la surface de chaque épaule, sans miroir
de géométrie. Le volume principal postérieur reste présent : environ **94,7 %**
des texels du masque postérieur gauche et **90,9 %** de celui de droite sont
conservés. Ces pourcentages concernent l’atlas UV et ses marges, pas une mesure
de volume musculaire. Cinq texels isolés de bordure ont aussi été retirés.

## Préservation vérifiée

- **Aucun déplacement, sculpture, lissage, nouvelle incision ou changement d’UV.**
- Positions, normales, UV et indices du GLB corrigé sont bit-identiques à ceux
  du contrôle `8b723d9`. Toujours **110 588 triangles**, 60 622 sommets exportés
  avec les mêmes doublons UV ; Blender conserve ses 55 288 sommets d’origine.
- Les six autres fichiers de masque sont **identiques octet pour octet**.
  Les frontières rouge/bleu et les pectoraux ne sont pas déplacés.
- Les huit identifiants restent présents. Les seules transitions de l’atlas
  sont `deltoid.left.posterior → neutre` et `deltoid.right.posterior → neutre`.
- Une composante par zone après recollage des coutures UV ; aucun trou interne
  détecté sur les texels de surface contrôlés. Les courbes restent limitées à
  la résolution du masque, sans précision médicale revendiquée.
- Quatre impacts 3D pris dans les languettes de la vue de référence passent du
  vert au neutre. Les huit raycasts de sélection sur source/export restent bons.
- Les nouveaux rendus neutres face et profil sont identiques pixel par pixel
  à ceux de `8b723d9`, avec caméras, éclairage et matériau identiques.
- Les 134 fichiers applicatifs protégés sont inchangés : SDK 58, visualiseur,
  modèle neutre, SQLite v8, programmes, séances, historique et statistiques.

[Audit des changements](m4c/meshy-deltoides-limite-inferieure/verification.json) ·
[Continuité](m4c/meshy-deltoides-limite-inferieure/continuity-audit.json) ·
[Caméras et contrôle neutre](m4c/meshy-deltoides-limite-inferieure/render-verification.json) ·
[Raycasts](m4c/meshy-deltoides-limite-inferieure/picking-audit.json).

Le prototype initial et tous ses fichiers restent conservés dans
[`meshy-huit-zones`](m4c/meshy-huit-zones/README.md). La correction est livrée dans
un dossier distinct. Aucune intégration interactive, carte thermique, nouvelle
segmentation ou fusion. **Arrêt pour validation visuelle de cette limite.**

Model created with Meshy — CC BY 4.0. Géométrie `e45e5d8` conservée ; modification
Logbook limitée aux masques de contrôle postérieurs.
