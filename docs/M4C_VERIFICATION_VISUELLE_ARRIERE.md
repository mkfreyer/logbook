# M4C — vérification visuelle arrière

**Rendus supplémentaires uniquement**, à partir de `daf5878`, PR #17 en
brouillon. Le modèle, les huit masques et leurs identifiants sont conservés.
L’état « avant » des comparatifs est `71f70dc`, juste avant le retrait local
du petit résidu vert droit. Aucune correction supplémentaire n’est effectuée.

## Rendus

- [Mannequin complet de dos](m4c/meshy-validation-arriere/renders/apres-dos-complet.png)
- [Gros plan arrière des deux épaules](m4c/meshy-validation-arriere/renders/apres-epaules-dos.png)
- [Trois quarts arrière droit](m4c/meshy-validation-arriere/renders/apres-trois-quarts-arriere-droit.png)
- [Trois quarts arrière gauche](m4c/meshy-validation-arriere/renders/apres-trois-quarts-arriere-gauche.png)
- [Avant / après du dos complet](m4c/meshy-validation-arriere/renders/comparatif-dos-complet.png)
- [Avant / après des deux épaules de dos](m4c/meshy-validation-arriere/renders/comparatif-epaules-dos.png)
- [Avant / après trois quarts arrière droit](m4c/meshy-validation-arriere/renders/comparatif-arriere-droit.png)

Les côtés désignent la **droite et la gauche anatomiques du mannequin**.
Sur la vue de dos, sa droite apparaît à droite de l’image. Le dos et les bras
restent majoritairement gris : seules les huit zones déjà proposées sont actives.

## Constat visuel

Les deux zones vertes couvrent la partie arrière des épaules. Ces vues ne
montrent pas de longue languette verte isolée descendant sur les triceps,
ni de trou gris fermé dans les portions vertes. Les frontières vert/bleu
restent continues et la convergence basse des portions est conservée.

**Une réserve reste visible : le bord inférieur vert/gris du deltoïde droit
présente de petites irrégularités à fort grossissement**, particulièrement
sur la vue trois quarts arrière droite. Ce bord de `daf5878` n’est donc pas
parfaitement régulier. Il est livré tel quel, sans lissage, reprise du masque
ou modification de la surface. La convergence en pointe vers l’insertion
reste visible ; elle doit aussi être jugée sur ces images, sans être
automatiquement assimilée à un débordement sur le bras.

La couverture gauche/droite est globalement comparable, avec des différences
locales de contour : ce n’est pas un miroir strict. La correction locale est
très discrète sur le mannequin complet de dos, et plus lisible dans le
comparatif rapproché trois quarts arrière droit. Ces observations ne constituent
pas une certification anatomique ni une validation à la place de l’utilisateur.

## Préservation et contrôles

- Sept images brutes rendues dans Blender 4.3.2/Cycles CPU, avec le matériau
  mat et l’éclairage studio des fichiers sources. Les trois comparatifs
  utilisent exactement les mêmes matrices de caméra, cadrages et lumières
  avant/après. Les planches ajoutent seulement libellés, mise en page et
  réduction proportionnelle ; aucun pixel du mannequin n’est repeint.
- Les **35 fichiers sources contrôlés** restent identiques octet pour octet,
  notamment les deux Blender, les textures, les GLB de contrôle et le maître
  Meshy `e45e5d8`. Les images embarquées dans Blender correspondent aux PNG
  de leurs versions respectives.
- Positions, indices, UV et normales sont inchangés pendant les rendus et
  identiques entre les deux scènes. Huit identifiants conservés. Aucun Blender,
  GLB ou masque n’est réenregistré par cette tâche.
- Les **134 fichiers applicatifs protégés** restent identiques : application,
  visualiseur Expo SDK 58, données de référence et SQLite. Aucun nouveau test
  sur iPhone ni changement fonctionnel n’est revendiqué.

[Vérifications](m4c/meshy-validation-arriere/verification.json) ·
[Caméras, empreintes des sources et des rendus](m4c/meshy-validation-arriere/renders/render-metadata.json) ·
[Sources utilisées et reproduction](m4c/meshy-validation-arriere/README.md).

**Arrêt pour validation visuelle.** PR #17 maintenue en brouillon, sans fusion.
Les petites irrégularités signalées ne déclenchent aucune retouche automatique.

Model created with Meshy — [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
