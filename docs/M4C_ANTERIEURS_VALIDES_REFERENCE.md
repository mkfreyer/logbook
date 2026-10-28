# M4C — les deux antérieurs validés deviennent la référence officielle

Validation utilisateur : les contours droit et gauche de la PR #19,
commit `09c61ab`, sont approuvés pour transfert dans M4C puis M4D-A.
La PR #19, sa branche et ses fichiers ne sont pas modifiés.

## Référence à utiliser désormais

[`docs/m4c/meshy-anterieurs-valides/`](m4c/meshy-anterieurs-valides/) contient :

- les huit [masques éditables](m4c/meshy-anterieurs-valides/textures/) ;
- les atlas L8 d'identification et RGBA régénérés depuis ces huit masques ;
- le [Blender validé](m4c/meshy-anterieurs-valides/meshy-anterieurs-valides.blend),
  copie exacte de la source bilatérale approuvée, avec les images embarquées ;
- le [GLB de contrôle](m4c/meshy-anterieurs-valides/exports/meshy-eight-zones-control.glb),
  copie exacte de l'export approuvé dont les images embarquées correspondent aux
  atlas régénérés ;
- les courbes 3D, les bornes des régions, les témoins de sélection et la
  [provenance de chaque fichier](m4c/meshy-anterieurs-valides/provenance.json).

Les masques `deltoid.left.anterior` (ID 3) et `deltoid.right.anterior` (ID 6)
sont identiques octet pour octet à `09c61ab`. Les six autres PNG sont identiques
à la fois à `09c61ab` et à `06fa665`. Aucun contour rejeté de `6817b08` ou
`265d058` n'est utilisé. Les anciens dossiers restent inchangés pour l'historique.

## Contrôles réalisés

- [Audit indépendant](m4c/meshy-anterieurs-valides/verification.json) : huit IDs,
  six masques protégés identiques, frontières antérieur/moyen et marges de
  filtrage de quatre texels inchangées, aucun chevauchement des poids.
- [Continuité UV](m4c/meshy-anterieurs-valides/continuity-audit.json) : une
  composante par zone après raccord des coutures, aucun trou fermé détecté.
- [Huit raycasts Three.js](m4c/meshy-anterieurs-valides/picking-audit.json) sur
  le modèle source et le GLB de contrôle : tous réussis.
- Atlas régénérés identiques octet pour octet aux atlas approuvés de `09c61ab`.
- Positions, normales, UV et indices identiques à la référence M4C restaurée :
  **110 588 triangles, aucun ajout, déplacement des sommets nul**.
- Mannequin maître `e45e5d8` inchangé : SHA-256
  `421e593cad17f60d1c0c5e67707729fb88bbf69026795e22011ecc7d90b38959`.
- Fichiers applicatifs, configuration Expo SDK 58, dépendances et tests M4C
  identiques à `168ac61`. Aucune modification de SQLite ou de données.

Les [rendus approuvés de face](m4c/meshy-anterieurs-valides/renders/face-bilaterale.png),
[du côté droit](m4c/meshy-anterieurs-valides/renders/epaule-droite-validee.png) et
[du côté gauche](m4c/meshy-anterieurs-valides/renders/epaule-gauche-validee.png)
sont recopiés sans retouche depuis `09c61ab`. Les asymétries résiduelles déjà
acceptées sont conservées ; aucune nouvelle interprétation anatomique.

## Transfert vers M4D-A

Le GLB coloré est un fichier de contrôle, pas le mannequin à afficher dans
l'application. `tools/m4d/build-selection.mjs` doit lire cette nouvelle référence,
réutiliser exactement sa géométrie/UV et rétablir les matériaux neutres du maître
Meshy avant de générer le GLB interactif. L'atlas d'IDs reste séparé du matériau
neutre et pilote uniquement la sélection orange existante.

La PR #17 reste en brouillon. Aucune fusion de PR. La PR #18 reçoit la référence
par une synchronisation de branche conservant l'historique, puis régénère ses
ressources avec le pipeline M4D-A existant. Aucun changement de gestes ou d'interface.
