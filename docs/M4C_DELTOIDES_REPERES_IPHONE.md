# M4C — Repositionnement des six faisceaux d’après les captures iPhone

Proposition à valider visuellement. Base : segmentation `06fa665` (PR #17), visualiseur `268ea3e` (PR #18), sculpture Meshy `e45e5d8` conservée.

## Changements

- Antérieurs : surfaces réorientées vers l’avant de l’épaule et la région delto-pectorale ; la limite commune avec le moyen quitte son ancien trajet trop latéral.
- Moyens : répartition plus large sur le dôme latéral et le sommet ; leurs deux limites partagées sont recalculées avec les antérieurs et postérieurs.
- Postérieurs : arrondi supérieur élargi selon les repères jaunes et bord commun avec le moyen régularisé en 3D. Les modifications ne sont pas six peintures indépendantes superposées.
- Gauche : les guides droits réfléchis en 3D sont reprojetés sur les vrais triangles de l’épaule gauche, puis les frontières sont recalculées sur cette surface. Aucun pixel UV n’est inversé. Distance maximale de reprojection : 4,15 mm.
- Les deux pectoraux restent strictement identiques, y compris leurs franges de masque et les deux canaux correspondants du premier atlas RGBA.

Aucune sculpture, aucun déplacement de sommet, aucune modification des normales, des UV, de la silhouette ou du nombre de triangles. Aucun changement applicatif dans cette PR M4C.

## Méthode et interprétation des repères

Les traits jaunes ont été transcrits en points guides depuis les trois captures. Les vues ont été reconstituées avec la perspective du visualiseur (champ vertical de 36°), en ajustant la projection de l’ancien masque orange aux contours visibles. L’erreur quadratique moyenne sur les enveloppes projetées transcrites est de 4,0 à 5,8 pixels, à la résolution de référence 942 × 1186. Ce chiffre décrit l’ajustement des enveloppes, pas une égalité de tous les pixels.

**Les paramètres exacts des caméras iPhone ne figurent pas dans les captures.** Les angles sont donc des reconstitutions proches ; chaque couple avant/après emploie en revanche une caméra et un éclairage rigoureusement identiques, enregistrés dans les métadonnées.

Les courbes lissées sont projetées par raycast sur la surface réelle. Elles déterminent des frontières communes dans un repère de surface autour de chaque épaule. L’arc supérieur postérieur est également contraint par son guide 3D afin d’éviter un petit repli de frontière au raccord avec le moyen. Toute surface reprise par ce bord est retirée du faisceau voisin dans le même atlas.

**Compromis sur les pointes inférieures :** les trois extrémités dessinées ne se superposent pas en 3D. Les reproduire littéralement donnerait trois insertions différentes. Une insertion commune a été choisie sur la surface d’origine en minimisant l’erreur de reprojection vers les trois extrémités. Elle reste proche de l’insertion existante. Les écarts résiduels sont environ 63 pixels en vues postérieure et antérieure, et 5 pixels en vue moyenne. Les pointes jaunes ne sont donc pas reproduites simultanément au pixel près ; les limites sont raccordées progressivement pour garder une convergence unique. Ce compromis fait partie de la présente validation visuelle.

L’atlas entier définit un seul ID par texel. Les six masques éditables en sont dérivés, sans chevauchement. Les frontières communes partagent donc exactement les mêmes pixels de séparation. Le contrôle de continuité raccorde les îlots UV via les véritables arêtes du maillage. De minuscules fragments isolés de bord/padding sont supprimés ; leur liste, leur étendue et leurs texels réellement couverts sont enregistrés dans `correction.json`. Aucun de ces nettoyages ne touche les pectoraux ou la géométrie.

## Comparatifs et sources

- [Postérieur droit avant/après](m4c/meshy-deltoides-reperes-iphone/renders/comparatif-posterior.png)
- [Moyen droit avant/après](m4c/meshy-deltoides-reperes-iphone/renders/comparatif-lateral.png)
- [Antérieur droit avant/après](m4c/meshy-deltoides-reperes-iphone/renders/comparatif-anterior.png)
- [Face, dos et quatre vues trois quarts](m4c/meshy-deltoides-reperes-iphone/renders/planche-vues-anatomiques.png)
- [Six faisceaux colorés indépendamment](m4c/meshy-deltoides-reperes-iphone/renders/planche-six-faisceaux.png)
- [Mannequin neutre](m4c/meshy-deltoides-reperes-iphone/renders/apres-neutre.png)
- [Blender éditable](m4c/meshy-deltoides-reperes-iphone/meshy-deltoides-reperes-iphone.blend)
- [GLB de contrôle](m4c/meshy-deltoides-reperes-iphone/exports/meshy-eight-zones-control.glb)
- [Masques PNG et atlas RGBA](m4c/meshy-deltoides-reperes-iphone/textures/)
- [Guides projetés sur les triangles](m4c/meshy-deltoides-reperes-iphone/surface-guides.json) · [Frontières communes](m4c/meshy-deltoides-reperes-iphone/shared-frontiers.json)

Les images sont de vrais rendus Blender/Cycles CPU, matériau mat neutre, 16 échantillons et graine 0 ; les planches n’ajoutent que des légendes et des mises en page. Les courbes jaunes ne sont pas peintes sur les rendus finaux.

## Contrôles

- Huit codes stables (1–8) et fond neutre 0 ; aucune superposition des huit champs de masque.
- Un composant de surface par zone après raccordement des coutures UV et aucun trou interne neutre détecté.
- Deux masques pectoraux identiques octet pour octet.
- Toutes les positions et normales par coin de triangle identiques au master `e45e5d8` ; indices et UV du GLB de contrôle identiques à `06fa665`.
- Guides gauche et droit sur les triangles d’origine, vérifiés par coordonnées barycentriques.
- Huit raycasts Three.js sur le master et le GLB corrigé : identifiants retrouvés.
- Maillage toujours à 110 588 triangles ; aucun coût géométrique supplémentaire. Atlas toujours 2048 × 2048.
- Comparaison neutre avant/après et empreintes Blender : voir les contrôles ci-dessous.

Les audits de topologie et d’atlas n’établissent pas une validation médicale. La lecture anatomique et le compromis aux insertions doivent être approuvés par l’utilisateur.

### Nombre de texels par zone

Ces nombres concernent l’atlas UV ; ils ne mesurent ni une surface anatomique ni un volume musculaire.

| Zone | Avant | Proposition |
| --- | ---: | ---: |
| `pectoralis.left` | 90081 | 90081 |
| `pectoralis.right` | 90130 | 90130 |
| `deltoid.left.anterior` | 38171 | 26063 |
| `deltoid.left.lateral` | 38139 | 46654 |
| `deltoid.left.posterior` | 28907 | 35430 |
| `deltoid.right.anterior` | 39009 | 25268 |
| `deltoid.right.lateral` | 38585 | 49453 |
| `deltoid.right.posterior` | 30945 | 37451 |

[Audit technique](m4c/meshy-deltoides-reperes-iphone/verification.json) · [Continuité](m4c/meshy-deltoides-reperes-iphone/continuity-audit.json) · [Raycasts](m4c/meshy-deltoides-reperes-iphone/picking-audit.json) · [Préservation Blender](m4c/meshy-deltoides-reperes-iphone/blender-preservation.json) · [Contrôle des rendus](m4c/meshy-deltoides-reperes-iphone/render-verification.json).

## Reproduction

```sh
python tools/m4c/iphone_deltoid_guides.py
blender -b -t 2 --python-exit-code 1 --python tools/m4c/project_iphone_deltoids.py
python tools/m4c/repartition_deltoids_iphone.py
python tools/m4c/audit_continuity.py --asset-dir docs/m4c/meshy-deltoides-reperes-iphone
python tools/m4c/audit_iphone_deltoids.py
node tools/m4c/audit-picking.mjs docs/m4c/meshy-deltoides-reperes-iphone
blender -b -t 2 --python-exit-code 1 --python tools/m4c/render_iphone_deltoids.py
python tools/m4c/compose_iphone_deltoids.py
```

Le cache de positions de surface est calculé dans le dossier de travail parent, hors dépôt ; il est entièrement reconstructible. Python utilise NumPy, SciPy et Pillow ; Blender 4.3.2 et Three.js sont gratuits. Aucun achat, nouvel abonnement ou changement de dépendances de l’application.

Les anciennes versions restent conservées. La PR #17 reste en brouillon ; les ressources interactives correspondantes sont propagées séparément dans la PR #18, sans fusion de Pull Request ni réécriture de l’historique. Arrêt pour validation visuelle et nouveau test iPhone.
