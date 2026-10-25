# M4A — Assemblage des deux modèles Meshy fournis

Commit [`b11223d`](https://github.com/mkfreyer/logbook/commit/b11223ddb2c89158e73bfabba612f2d905494a58). Corps **Anatomical Form**, tête **Rib Reach Exercise**, ajustée et raccordée localement.

- [Face / profil / trois quarts](https://github.com/mkfreyer/logbook/blob/b11223ddb2c89158e73bfabba612f2d905494a58/docs/m4a/meshy-assemblage-corps-tete/renders/mannequin-assemble.png)
- [Comparatif des têtes et raccords](https://github.com/mkfreyer/logbook/blob/b11223ddb2c89158e73bfabba612f2d905494a58/docs/m4a/meshy-assemblage-corps-tete/renders/comparatif-tetes.png)
- [Rapport](https://github.com/mkfreyer/logbook/blob/b11223ddb2c89158e73bfabba612f2d905494a58/docs/M4A_MESHY_ASSEMBLAGE_CORPS_TETE.md)
- [Blender / GLB et sources](https://github.com/mkfreyer/logbook/blob/b11223ddb2c89158e73bfabba612f2d905494a58/docs/m4a/meshy-assemblage-corps-tete/README.md)

45 102 sommets du corps conservé inchangés ; surface donneuse vérifiée après ajustement uniforme. Maillage fermé, aucune nouvelle intersection tête/raccord détectée. GLB : 97 424 triangles, 1,76 Mo. Douze vrais rendus Blender comparatifs. Attribution Meshy CC BY 4.0 conservée.

**Arrêt pour validation visuelle.** Aucune intégration, aucune segmentation, application et SQLite inchangées. PR en brouillon, sans fusion ; versions précédentes préservées.

<details>
<summary>Historique intégral des livraisons précédentes</summary>

# M4A — Tête de mannequin lisse et sans visage

Proposition pour validation : [`265da5d`](https://github.com/mkfreyer/logbook/commit/265da5ddac5a16afc6d0dd69cede7f8027cc0e5a), à partir de `d83fc44`.

Nouvelle géométrie continue et légèrement ovale, sans yeux, nez, bouche, oreilles ni cheveux. Matériau mat neutre conservé. Seule la tête et son raccord supérieur sont reconstruits ; les deux yeux P5 sont retirés de la nouvelle scène. Les anciennes versions restent disponibles.

- [Avant / après — face et trois quarts](https://github.com/mkfreyer/logbook/blob/265da5ddac5a16afc6d0dd69cede7f8027cc0e5a/docs/m4a/ecorche-beatriz-tete-neutre/renders/comparatif-tete-face-trois-quarts.png)
- [Avant / après — profil et arrière](https://github.com/mkfreyer/logbook/blob/265da5ddac5a16afc6d0dd69cede7f8027cc0e5a/docs/m4a/ecorche-beatriz-tete-neutre/renders/comparatif-tete-profil-arriere.png)
- [Mannequin complet](https://github.com/mkfreyer/logbook/blob/265da5ddac5a16afc6d0dd69cede7f8027cc0e5a/docs/m4a/ecorche-beatriz-tete-neutre/renders/planche-generale.png)
- [Rapport](https://github.com/mkfreyer/logbook/blob/265da5ddac5a16afc6d0dd69cede7f8027cc0e5a/docs/M4A_TETE_NEUTRE_SANS_VISAGE.md)
- [Sources Blender / GLB et contrôles](https://github.com/mkfreyer/logbook/blob/265da5ddac5a16afc6d0dd69cede7f8027cc0e5a/docs/m4a/ecorche-beatriz-tete-neutre/README.md)

**Conservation vérifiée :** 296 autres objets identiques, 10 637 triangles de gorge P4 inchangés, six IDs des deltoïdes conservés. Normales cervicales : écart maximal de réencodage 0,088°, sans déplacement géométrique. Surface tête / gorge fermée, aucune auto-intersection détectée ; aucun nouveau dépassement sur 38 016 rayons qualifiés. Dix vrais rendus Blender dans les mêmes conditions avant/après. Total : 7 580 triangles en moins.

Les reliefs anatomiques du cou restent visibles sous la tête neutre. La forme et le raccord sont proposés pour validation visuelle.

Application et SQLite inchangées. Aucun M4B. **PR conservée en brouillon, sans fusion. Arrêt avant toute intégration.**

<details>
<summary>Historique intégral des livraisons précédentes</summary>

# M4A — Pieds retouchés, dernière finition de l’aine conservée

Livraison pour validation : [`d83fc44`](https://github.com/mkfreyer/logbook/commit/d83fc44c3d26fd8a5685e359fcefefc4dd0b941e).

Choix confirmé : **aine et corps de `41896cc`**, avec les **deux pieds de `8a8b95e`**. Assemblage exact, aucune nouvelle sculpture. Les 297 autres objets sont identiques à `41896cc` ; les deux pieds sont identiques à `8a8b95e`, y compris topologie et normales. Six zones des deltoïdes conservées.

- [Face / trois quarts avant-après](https://github.com/mkfreyer/logbook/blob/d83fc44c3d26fd8a5685e359fcefefc4dd0b941e/docs/m4a/ecorche-beatriz-pieds-aine-validee/renders/comparatif-pieds.png)
- [Profils des deux pieds](https://github.com/mkfreyer/logbook/blob/d83fc44c3d26fd8a5685e359fcefefc4dd0b941e/docs/m4a/ecorche-beatriz-pieds-aine-validee/renders/comparatif-profils.png)
- [Raccords cheville / pied](https://github.com/mkfreyer/logbook/blob/d83fc44c3d26fd8a5685e359fcefefc4dd0b941e/docs/m4a/ecorche-beatriz-pieds-aine-validee/renders/raccords-chevilles.png)
- [Planche générale neutre](https://github.com/mkfreyer/logbook/blob/d83fc44c3d26fd8a5685e359fcefefc4dd0b941e/docs/m4a/ecorche-beatriz-pieds-aine-validee/renders/planche-generale.png)
- [Rapport](https://github.com/mkfreyer/logbook/blob/d83fc44c3d26fd8a5685e359fcefefc4dd0b941e/docs/M4A_PIEDS_AINE_VALIDEE.md)
- [Sources Blender / GLB et contrôles](https://github.com/mkfreyer/logbook/blob/d83fc44c3d26fd8a5685e359fcefefc4dd0b941e/docs/m4a/ecorche-beatriz-pieds-aine-validee/README.md)

Douze nouveaux rendus Blender avec caméras, éclairage et matériau mat identiques avant/après. Contrôles d’identité des deux sources, contacts des pieds et export GLB réussis. Les transitions pieds lisses / jambes disséquées restent perceptibles, sans nouvelle retouche.

Application et SQLite inchangées. Aucun M4B. **PR en brouillon, sans fusion ; arrêt pour validation visuelle.**

<details>
<summary>Historique intégral des livraisons précédentes</summary>

## M4A — Finition des pieds et raccords des chevilles

Proposition au commit [`8a8b95e`](https://github.com/mkfreyer/logbook/commit/8a8b95ed31aeddff47bd038ac09183273009edf3), **pour validation visuelle**.

**Base géométrique : `d94297a`, explicitement demandé.** L'aine de cette base est inchangée ; la proposition d'aine `41896cc` reste conservée séparément, sans modification.

Seuls les deux pieds et leurs raccords immédiats sont reconstruits et adoucis : rebord supérieur moins évasé, transition progressive aux chevilles et détails des orteils simplifiés. **297 autres objets strictement identiques** à `d94297a`, dont muscles des jambes, mollets, tête P5, gorge et six zones des deltoïdes.

- [Face et trois quarts](https://github.com/mkfreyer/logbook/blob/8a8b95ed31aeddff47bd038ac09183273009edf3/docs/m4a/ecorche-beatriz-finition-pieds/renders/comparatif-pieds.png)
- [Profils droit et gauche](https://github.com/mkfreyer/logbook/blob/8a8b95ed31aeddff47bd038ac09183273009edf3/docs/m4a/ecorche-beatriz-finition-pieds/renders/comparatif-profils.png)
- [Gros plan des raccords](https://github.com/mkfreyer/logbook/blob/8a8b95ed31aeddff47bd038ac09183273009edf3/docs/m4a/ecorche-beatriz-finition-pieds/renders/raccords-chevilles.png)
- [Vue générale](https://github.com/mkfreyer/logbook/blob/8a8b95ed31aeddff47bd038ac09183273009edf3/docs/m4a/ecorche-beatriz-finition-pieds/renders/planche-generale.png)
- [Rapport et sources Blender / GLB](https://github.com/mkfreyer/logbook/blob/8a8b95ed31aeddff47bd038ac09183273009edf3/docs/M4A_FINITION_PIEDS.md)

Contrôles : symétrie, absence d'auto-intersection détectée, bords de contact enfouis, absence de nouveaux fragments visibles dans les vues trois quarts testées, conservation des données GLB des 297 autres objets et des six identifiants des deltoïdes. **16 000 triangles par pied ; +1,94 % au total ; GLB 10,93 Mo.** La transition avec l'anatomie disséquée des jambes reste perceptible et soumise à validation esthétique.

**Aucune modification applicative ou SQLite. Aucun M4B, aucune intégration, aucune fusion. PR en brouillon ; arrêt pour validation.**

<details>
<summary>Historique conservé — propositions et rapports précédents</summary>

## M4A — Aine : finition plus homogène, référence pieds

Proposition issue de `d94297a`, commit [`41896cc`](https://github.com/mkfreyer/logbook/commit/41896cc1d606295b9ea8286e5569a6a964c20fb2), **pour validation visuelle**. Les pieds du mannequin sont la référence du niveau de simplification recherché.

La seule enveloppe centrale est reconstruite avec des raccords plus progressifs et un filtrage du champ à 1 mm. Les **298 autres objets sont strictement identiques** : géométrie, normales, matériaux et données GLB contrôlés, dont cuisses, adducteurs, deltoïdes, tête et gorge. L'ouverture naturelle entre les jambes reste libre sur les rayons de contrôle.

- [Avant / après serré](https://github.com/mkfreyer/logbook/blob/41896cc1d606295b9ea8286e5569a6a964c20fb2/docs/m4a/ecorche-beatriz-aine-homogene/renders/comparatif-central-serre.png)
- [Face et trois quarts](https://github.com/mkfreyer/logbook/blob/41896cc1d606295b9ea8286e5569a6a964c20fb2/docs/m4a/ecorche-beatriz-aine-homogene/renders/comparatif-aine.png)
- [Planche générale neutre](https://github.com/mkfreyer/logbook/blob/41896cc1d606295b9ea8286e5569a6a964c20fb2/docs/m4a/ecorche-beatriz-aine-homogene/renders/planche-neutre.png)
- [Comparaison directe avec les pieds](https://github.com/mkfreyer/logbook/blob/41896cc1d606295b9ea8286e5569a6a964c20fb2/docs/m4a/ecorche-beatriz-aine-homogene/renders/coherence-pieds.png)
- [Rapport, contrôles et sources Blender / GLB](https://github.com/mkfreyer/logbook/blob/41896cc1d606295b9ea8286e5569a6a964c20fb2/docs/M4A_AINE_SURFACE_HOMOGENE.md)

**Coût :** 17 689 triangles supplémentaires (+3,4 %) ; GLB 11,08 Mo. Six identifiants des deltoïdes conservés. Aucune auto-intersection détectée sur la surface retouchée ; bords enfouis contrôlés. Le bord inférieur plus rentrant révèle un peu plus les pièces déjà présentes en profondeur, dans une bande de 5 mm ; ce point reste soumis à validation esthétique.

**Application et SQLite inchangées. Aucune intégration, aucun M4B, aucune fusion. PR en brouillon ; arrêt pour validation.**

<details>
<summary>Historique conservé — propositions et rapports précédents</summary>

## Proposition actuelle — aine : raccords plus fondus

Reprise de `cf5569b`. La surface centrale est reconstruite avec un profil arrondi et rentrant et des raccords géométriques progressifs aux voisins. Le rebord transversal précédent est supprimé ; les normales de finition sont lissées sur la zone libre et raccordées aux normales source aux contacts. **Les 298 autres objets sont conservés à l’identique**, dont les adducteurs, les cuisses, les deltoïdes P4, la tête P5, la gorge et les pieds.

- Commit : [`d94297a`](https://github.com/mkfreyer/logbook/commit/d94297af21a05dacaa1f19a1ce64c7b64f447ea4).
- [Avant / après central serré](https://github.com/mkfreyer/logbook/blob/d94297af21a05dacaa1f19a1ce64c7b64f447ea4/docs/m4a/ecorche-beatriz-aine-fondue/renders/comparatif-central-serre.png).
- [Comparatifs face et trois quarts](https://github.com/mkfreyer/logbook/blob/d94297af21a05dacaa1f19a1ce64c7b64f447ea4/docs/m4a/ecorche-beatriz-aine-fondue/renders/comparatif-aine.png).
- [Planche générale neutre](https://github.com/mkfreyer/logbook/blob/d94297af21a05dacaa1f19a1ce64c7b64f447ea4/docs/m4a/ecorche-beatriz-aine-fondue/renders/planche-neutre.png).
- [Rapprochement avec les pieds inchangés](https://github.com/mkfreyer/logbook/blob/d94297af21a05dacaa1f19a1ce64c7b64f447ea4/docs/m4a/ecorche-beatriz-aine-fondue/renders/coherence-pieds.png).
- [Rapport](https://github.com/mkfreyer/logbook/blob/d94297af21a05dacaa1f19a1ce64c7b64f447ea4/docs/M4A_AINE_RACCORDS_FONDUS.md) · [Blender / GLB / reproduction](https://github.com/mkfreyer/logbook/blob/d94297af21a05dacaa1f19a1ce64c7b64f447ea4/docs/m4a/ecorche-beatriz-aine-fondue/README.md).

### Contrôles et limites

298 objets identiques dans Blender et le GLB, six IDs de deltoïdes et correspondances matériaux / primitives conservés. Tous les bords de contact sont enfouis dans les voisins (0,077 à 0,150 mm) ; aucune auto-intersection détectée dans la nouvelle surface. 6 413 rayons dans l’ouverture basse : aucune occlusion ajoutée. Quatre vues avant de `cf5569b` réutilisées et vérifiées, cinq nouveaux rendus Cycles, cadrages des quatre paires identiques.

La surface reste un objet de présentation avec des plages ouvertes aux marges enfouies, sans peau globale soudée. Les plis inguinaux et reliefs voisins validés sont préservés. +18 591 triangles nets (+3,70 %), environ +342 Kio de GLB, aucune texture ajoutée ; aucune performance mobile déclarée mesurée.

L’image des pieds annoncée n’était pas disponible dans les pièces reçues : la comparaison utilise les pieds du mannequin actuel, géométrie inchangée. **Validation visuelle ouverte.**

Application et SQLite inchangées. Aucun M4B, aucune intégration, aucun achat ni Astra Ultra. **PR #12 maintenue en brouillon, sans fusion. Arrêt après les rendus pour validation.**

<details>
<summary>Historique de la PR avant cette proposition — conservé intégralement</summary>

## Proposition actuelle — finition esthétique locale de l’aine

Reprise de `d79692f`. Deux petites pièces centrales exposées sont remplacées, dans une nouvelle scène de présentation, par une surface pubienne neutre et plus sobre. **Aucun sommet d’un muscle existant déplacé** : les adducteurs, les deltoïdes P4 et leurs six zones, la tête P5, la gorge et les autres volumes restent inchangés.

- Commit : [`cf5569b`](https://github.com/mkfreyer/logbook/commit/cf5569b2e84727a800863301901126a6630884f3).
- [Avant / après central très serré](https://github.com/mkfreyer/logbook/blob/cf5569b2e84727a800863301901126a6630884f3/docs/m4a/ecorche-beatriz-finition-aine/renders/comparatif-central-serre.png).
- [Comparatifs face et trois quarts](https://github.com/mkfreyer/logbook/blob/cf5569b2e84727a800863301901126a6630884f3/docs/m4a/ecorche-beatriz-finition-aine/renders/comparatif-aine.png).
- [Planche neutre à l’échelle du mannequin](https://github.com/mkfreyer/logbook/blob/cf5569b2e84727a800863301901126a6630884f3/docs/m4a/ecorche-beatriz-finition-aine/renders/planche-neutre.png).
- [Rapport](https://github.com/mkfreyer/logbook/blob/cf5569b2e84727a800863301901126a6630884f3/docs/M4A_FINITION_AINE_LOCALISEE.md) · [Blender / GLB / paramètres](https://github.com/mkfreyer/logbook/blob/cf5569b2e84727a800863301901126a6630884f3/docs/m4a/ecorche-beatriz-finition-aine/README.md).

### Vérifications

298 objets conservés à l’identique dans Blender et le GLB ; les deux pièces remplacées restent intactes dans la scène historique et les sources précédentes. Nouvelle surface fermée, symétrique, sans auto-intersection détectée. Six IDs de deltoïdes et correspondances matériaux / primitives conservés. Huit vrais rendus Cycles, cadrages avant/après identiques. +1 358 triangles nets (+0,27 %), aucune texture ajoutée.

La retouche reste délibérément centrale : plis inguinaux et anatomie voisine conservés, sans lissage général du bassin ou des jambes. L’image de référence annoncée n’était pas disponible ; le périmètre suit la demande écrite. **Validation visuelle ouverte.**

Application et SQLite inchangées. Aucun M4B, aucune intégration, aucun achat ni Astra Ultra. **PR #12 maintenue en brouillon, sans fusion. Arrêt pour validation.**

<details>
<summary>Historique de la PR avant cette finition locale — conservé intégralement</summary>

## Livraison actuelle — répartition anatomique proposée des six zones

Commit : [`d79692f`](https://github.com/mkfreyer/logbook/commit/d79692f380e39312939290ab0d3e038e448aa9b2). Reprise exclusive de `990201f`, surface P4 + tête P5 de `0ab3d83` conservée.

### Rendus à valider

- [Avant / après du placement : face, profil, trois quarts, arrière oblique](https://github.com/mkfreyer/logbook/blob/d79692f380e39312939290ab0d3e038e448aa9b2/docs/m4a/ecorche-beatriz-anatomie-deltoides/renders/comparatif-anatomie.png).
- [Six zones et gros plans des deux épaules sous plusieurs angles](https://github.com/mkfreyer/logbook/blob/d79692f380e39312939290ab0d3e038e448aa9b2/docs/m4a/ecorche-beatriz-anatomie-deltoides/renders/controle-six-zones-anatomiques.png).
- [Neutre comparé directement à P4 original](https://github.com/mkfreyer/logbook/blob/d79692f380e39312939290ab0d3e038e448aa9b2/docs/m4a/ecorche-beatriz-anatomie-deltoides/renders/comparatif-neutre-P4.png).
- [Deux épaules de face au neutre](https://github.com/mkfreyer/logbook/blob/d79692f380e39312939290ab0d3e038e448aa9b2/docs/m4a/ecorche-beatriz-anatomie-deltoides/renders/epaules-face-neutres.png).

Antérieur rouge : région claviculaire et enveloppement avant. Moyen bleu : éventail plus large sur le dôme supérieur/latéral, resserré vers l'insertion. Postérieur vert : couverture arrière depuis la région scapulaire. Deux profils de séparation distincts dans un repère huméral 3D remplacent la proximité de trois chemins longitudinaux.

### Contrôles et limites

- Méthode de découpage continu conservée. Aucun sommet de `990201f` déplacé ; les 5 971 sommets P4 par épaule restent aussi inchangés, vérifiés directement contre `0ab3d83`.
- Nouveaux points barycentriques sur surface conservée, écart maximal direct à P4 **0,000083 mm** après stockage float32. Maillages fermés, couverture complète, aucune intersection non adjacente détectée.
- Les **298 autres objets** sont inchangés, notamment tête P5, gorge et corps. Six IDs et matériaux indépendants conservés ; GLB neutre/coloré réimportés, normales identiques entre matériaux sur les frontières.
- **+1 828 triangles (+0,37 %)** par rapport à `990201f`, **+35 080 octets** pour le GLB neutre. Aucun matériau ou primitive supplémentaire.
- Petit écart d'encodage des normales (~0,10° sur quelques coins très fins), documenté. Les comparatifs neutres avec `990201f` montrent moins de 0,014 % de pixels différents, sans couture ou changement de relief perceptible. Aucune identité pixel par pixel revendiquée.
- Six repères approximatifs sont cohérents avec les portions proposées. **Le placement anatomique reste à valider visuellement** ; pas de certification médicale ou de mesure FPS mobile.

[Rapport](https://github.com/mkfreyer/logbook/blob/d79692f380e39312939290ab0d3e038e448aa9b2/docs/M4A_DELTOIDES_REPARTITION_ANATOMIQUE.md) · [Blender / GLB, provenance et reproduction](https://github.com/mkfreyer/logbook/blob/d79692f380e39312939290ab0d3e038e448aa9b2/docs/m4a/ecorche-beatriz-anatomie-deltoides/README.md) · [Contrôles](https://github.com/mkfreyer/logbook/blob/d79692f380e39312939290ab0d3e038e448aa9b2/docs/m4a/ecorche-beatriz-anatomie-deltoides/verification.json).

**Arrêt pour validation.** Aucune intégration Logbook, modification SQLite, M4B ou fusion. PR #12 maintenue en brouillon. Toutes les versions précédentes conservées.

<details>
<summary>Historique des propositions précédentes — conservé intégralement</summary>

## Livraison actuelle — frontières continues des six zones deltoïdes

Commit : [`990201f`](https://github.com/mkfreyer/logbook/commit/990201f214c91272a5274a53c28e049670128064). Base exclusive `fb68f5e`, géométrie P4 + tête P5 de `0ab3d83`. Aucune sculpture des creux reprise.

### Validation visuelle

- [Avant / après des frontières : profil, trois quarts, face et dos](https://github.com/mkfreyer/logbook/blob/990201f214c91272a5274a53c28e049670128064/docs/m4a/ecorche-beatriz-frontieres-deltoides/renders/comparatif-frontieres.png).
- [Six zones : gros plans des deux épaules de face et trois quarts, profil et dos](https://github.com/mkfreyer/logbook/blob/990201f214c91272a5274a53c28e049670128064/docs/m4a/ecorche-beatriz-frontieres-deltoides/renders/controle-six-zones.png).
- [Avant / après neutre](https://github.com/mkfreyer/logbook/blob/990201f214c91272a5274a53c28e049670128064/docs/m4a/ecorche-beatriz-frontieres-deltoides/renders/comparatif-neutre.png).
- [Deux épaules de face au neutre](https://github.com/mkfreyer/logbook/blob/990201f214c91272a5274a53c28e049670128064/docs/m4a/ecorche-beatriz-frontieres-deltoides/renders/epaules-face-neutres.png).

Antérieur rouge, moyen bleu, postérieur vert. Les frontières traversent désormais les triangles au lieu de suivre les anciennes arêtes.

### Méthode et contrôles

- Découpage barycentrique local de 419 triangles d'origine par épaule. Aucun sommet d'origine déplacé, aucune sculpture ou modification intentionnelle de forme. Nouveaux points sur les faces P4, écart de stockage float32 maximal **0,000061 mm**.
- **+848 triangles par épaule, +1 696 au total (+0,34 %)**. GLB neutre **+39 740 octets** ; 300 objets, 304 primitives et 7 matériaux, inchangés par rapport à `fb68f5e`.
- Maillages fermés, couverture complète, sans chevauchement ; aucune intersection non adjacente détectée. Les 298 autres objets, tête P5 et gorge comprises, sont inchangés.
- Normales identiques entre matériaux sur les frontières dans Blender et dans le GLB. Six IDs, couleurs indépendantes et deux réimports GLB vérifiés.
- Le rendu neutre ne présente pas de couture perceptible aux angles contrôlés. **Il n'est pas identique pixel par pixel** : environ 0,03 % des pixels diffèrent sur les deux comparatifs, écarts documentés dans le rapport.
- Pas de FPS mobile mesuré. Les frontières restent des polylignes sur la surface ; leurs limites anatomiques attendent votre validation.

[Rapport](https://github.com/mkfreyer/logbook/blob/990201f214c91272a5274a53c28e049670128064/docs/M4A_DELTOIDES_FRONTIERES_CONTINUES.md) · [Sources Blender / GLB, provenance et reproduction](https://github.com/mkfreyer/logbook/blob/990201f214c91272a5274a53c28e049670128064/docs/m4a/ecorche-beatriz-frontieres-deltoides/README.md) · [Contrôles techniques](https://github.com/mkfreyer/logbook/blob/990201f214c91272a5274a53c28e049670128064/docs/m4a/ecorche-beatriz-frontieres-deltoides/verification.json).

**Arrêt pour validation.** Aucune intégration applicative, modification SQLite, M4B ou fusion. PR #12 maintenue en brouillon, historique intégralement conservé.

<details>
<summary>Historique des propositions précédentes — conservé intégralement</summary>

## Livraison actuelle — six zones sur les deltoïdes P4, sans sculpture

Commit : [`fb68f5e`](https://github.com/mkfreyer/logbook/commit/fb68f5ee9ab3b47f3ae046cd7a1ce11129a98857).

Référence géométrique exclusive : `0ab3d83` (deltoïdes P4, tête P5, gorge et corps validés). Les essais `62fe3ff`, `39a8eb2` et `7a0af69` sont conservés mais ne servent pas de base.

### Rendus à valider

- [Neutre : face / profil / dos / trois quarts](https://github.com/mkfreyer/logbook/blob/fb68f5ee9ab3b47f3ae046cd7a1ce11129a98857/docs/m4a/ecorche-beatriz-zones-deltoides/renders/planche-neutre.png).
- [Épaules neutres](https://github.com/mkfreyer/logbook/blob/fb68f5ee9ab3b47f3ae046cd7a1ce11129a98857/docs/m4a/ecorche-beatriz-zones-deltoides/renders/planche-epaules-neutres.png).
- [Contrôle des six zones, vues générales](https://github.com/mkfreyer/logbook/blob/fb68f5ee9ab3b47f3ae046cd7a1ce11129a98857/docs/m4a/ecorche-beatriz-zones-deltoides/renders/planche-zones.png).
- [Gros plans des zones, plusieurs angles](https://github.com/mkfreyer/logbook/blob/fb68f5ee9ab3b47f3ae046cd7a1ce11129a98857/docs/m4a/ecorche-beatriz-zones-deltoides/renders/planche-epaules-zones.png).
- [Référence / nouveau neutre / couleurs, même caméra](https://github.com/mkfreyer/logbook/blob/fb68f5ee9ab3b47f3ae046cd7a1ce11129a98857/docs/m4a/ecorche-beatriz-zones-deltoides/renders/comparatif-reference-neutre-zones.png).

Antérieur rouge, moyen/latéral bleu, postérieur vert. Les six IDs demandés sont conservés dans les matériaux et primitives GLB ; [correspondance de sélection](https://github.com/mkfreyer/logbook/blob/fb68f5ee9ab3b47f3ae046cd7a1ce11129a98857/docs/m4a/ecorche-beatriz-zones-deltoides/selection-map.json).

### Vérifications et limite

- 300/300 objets : géométrie et normales identiques à `0ab3d83` ; déplacement maximal **0 m**. Aucun changement topologique.
- 298 autres objets et matériaux inchangés, dont tête P5, gorge et pectoraux.
- Couverture complète, sans chevauchement ; six zones continues et six matériaux indépendants. Coloration isolée et retour neutre testés.
- GLB neutre et contrôle réimportés ; six IDs retrouvés, positions/normales exportées identiques à la référence. Deux vues neutres recalculées identiques pixel par pixel aux rendus approuvés.
- **Limite : petits crénelages des frontières colorées en gros plan**, liés aux triangles P4. Limites anatomiques superficielles proposées, en attente de validation ; aucune certification médicale ni mesure de FPS mobile.

[Rapport](https://github.com/mkfreyer/logbook/blob/fb68f5ee9ab3b47f3ae046cd7a1ce11129a98857/docs/M4A_DELTOIDES_P4_SIX_ZONES.md) · [Sources Blender / GLB et mode d'emploi](https://github.com/mkfreyer/logbook/blob/fb68f5ee9ab3b47f3ae046cd7a1ce11129a98857/docs/m4a/ecorche-beatriz-zones-deltoides/README.md) · [Contrôles techniques](https://github.com/mkfreyer/logbook/blob/fb68f5ee9ab3b47f3ae046cd7a1ce11129a98857/docs/m4a/ecorche-beatriz-zones-deltoides/verification.json).

**Arrêt pour validation visuelle et technique.** Aucune intégration applicative, SQLite, M4B ou fusion. PR #12 maintenue en brouillon. Tous les travaux antérieurs sont conservés.

<details>
<summary>Historique des livraisons précédentes — conservé intégralement</summary>

## Étape 2 — reconstruction locale : essai insuffisant, non validé

Les trajectoires de **`0fc6f0b` ont été validées par l’utilisateur**. Cette livraison essaie de reconstruire les anciens fonds et de former les nouveaux sillons sur ces guides, depuis **`0ab3d83` (deltoïdes P4 + tête P5)**.

**La proposition ne satisfait pas encore les critères.** Des marques persistent aux raccords et les contrôles détectent **7 intersections de triangles par deltoïde**. La référence reste **`0ab3d83`** ; cette copie ne doit pas être validée ni intégrée.

- [Rapport : méthode, préservation et défauts](https://github.com/mkfreyer/logbook/blob/7a0af6921e80e94f50115d275c8bfab30adf7b02/docs/M4A_RECONSTRUCTION_CREUX_GUIDES_BLEUS.md)
- [Avant / après — vue de référence](https://github.com/mkfreyer/logbook/blob/7a0af6921e80e94f50115d275c8bfab30adf7b02/docs/m4a/ecorche-beatriz-reconstruction-guides/renders/comparatif-reference.png)
- [Bombé protégé](https://github.com/mkfreyer/logbook/blob/7a0af6921e80e94f50115d275c8bfab30adf7b02/docs/m4a/ecorche-beatriz-reconstruction-guides/renders/bombe-preserve.png) · [Premier creux](https://github.com/mkfreyer/logbook/blob/7a0af6921e80e94f50115d275c8bfab30adf7b02/docs/m4a/ecorche-beatriz-reconstruction-guides/renders/creux-1-detail.png) · [Second creux](https://github.com/mkfreyer/logbook/blob/7a0af6921e80e94f50115d275c8bfab30adf7b02/docs/m4a/ecorche-beatriz-reconstruction-guides/renders/creux-2-detail.png)
- [Face](https://github.com/mkfreyer/logbook/blob/7a0af6921e80e94f50115d275c8bfab30adf7b02/docs/m4a/ecorche-beatriz-reconstruction-guides/renders/comparatif-face.png) · [Profil](https://github.com/mkfreyer/logbook/blob/7a0af6921e80e94f50115d275c8bfab30adf7b02/docs/m4a/ecorche-beatriz-reconstruction-guides/renders/comparatif-profil.png) · [Trois quarts](https://github.com/mkfreyer/logbook/blob/7a0af6921e80e94f50115d275c8bfab30adf7b02/docs/m4a/ecorche-beatriz-reconstruction-guides/renders/comparatif-trois-quarts.png) · [Arrière oblique](https://github.com/mkfreyer/logbook/blob/7a0af6921e80e94f50115d275c8bfab30adf7b02/docs/m4a/ecorche-beatriz-reconstruction-guides/renders/comparatif-arriere-oblique.png)
- [Topologie locale](https://github.com/mkfreyer/logbook/blob/7a0af6921e80e94f50115d275c8bfab30adf7b02/docs/m4a/ecorche-beatriz-reconstruction-guides/renders/topologie-locale.png) · [Sources Blender/GLB d’essai et reproduction](https://github.com/mkfreyer/logbook/blob/7a0af6921e80e94f50115d275c8bfab30adf7b02/docs/m4a/ecorche-beatriz-reconstruction-guides/README.md) · [Contrôles](https://github.com/mkfreyer/logbook/blob/7a0af6921e80e94f50115d275c8bfab30adf7b02/docs/m4a/ecorche-beatriz-reconstruction-guides/verification.json)

Deux patches locaux remplacent 1 724 faces initiales par épaule. Le fond est reconstruit, puis un profil arrondi suit chaque guide bleu. Les **901 sommets du bombé protégé par épaule et les 298 autres objets restent strictement identiques**. Les dimensions maximales sont conservées ; l’enveloppe sous certains angles varie néanmoins jusqu’à 1,7 mm. Le volume du deltoïde augmente d’environ 0,44 %, sans compensation sur le ventre principal.

La topologie passe de 11 938 à 53 984 triangles par deltoïde (582 150 au total), un coût local trop élevé pour présenter cet essai non conforme comme une base mobile finale. Les rendus utilisent les mêmes caméras, lumières et matériau mat neutre. Aucun trait peint ne simule les sillons.

**Arrêt : aucune nouvelle série automatique de retouches.** Une reprise manuelle de topologie/sculpture serait préférable, mais elle n’est pas lancée. Tous les historiques et fichiers précédents sont préservés. Aucun changement applicatif ou SQLite, aucune segmentation interactive, aucun M4B, aucune fusion. PR #12 en brouillon. Outils de préparation gratuits ; aucun achat ni Astra Ultra.

<details>
<summary>Historique des livraisons précédentes conservé</summary>

## Validation des trajectoires 3D uniquement — aucune sculpture

La référence de sécurité reste **`0ab3d83` (deltoïdes P4 + tête P5)**. Les essais `62fe3ff` et `39a8eb2` ne deviennent pas la nouvelle base.

Cette livraison ajoute des courbes 3D sur la surface P4 : rouges d’après les anciens tracés annotés, bleues suivant les trajets demandés, avec leur miroir sur l’autre épaule. **Les 300 objets de maillage sont strictement inchangés**, dont les deux deltoïdes et les 298 autres objets. Le matériau mat neutre et les cinq lumières sont conservés.

- [Rapport, limites du recalage et méthode future non exécutée](https://github.com/mkfreyer/logbook/blob/0fc6f0b3a0ffacc2283d26a06afa852ef3be35ad/docs/M4A_GUIDES_3D_DELTOIDES_P4.md)
- [Planche des quatre contrôles : sans guides / rouges / bleus / superposition](https://github.com/mkfreyer/logbook/blob/0fc6f0b3a0ffacc2283d26a06afa852ef3be35ad/docs/m4a/ecorche-beatriz-guides-deltoides/renders/controle-trajets.png)
- [Superposition pleine résolution](https://github.com/mkfreyer/logbook/blob/0fc6f0b3a0ffacc2283d26a06afa852ef3be35ad/docs/m4a/ecorche-beatriz-guides-deltoides/renders/reference-superposition.png) · [Bleus seuls](https://github.com/mkfreyer/logbook/blob/0fc6f0b3a0ffacc2283d26a06afa852ef3be35ad/docs/m4a/ecorche-beatriz-guides-deltoides/renders/reference-nouveaux-bleus.png)
- [Terminaisons — détails](https://github.com/mkfreyer/logbook/blob/0fc6f0b3a0ffacc2283d26a06afa852ef3be35ad/docs/m4a/ecorche-beatriz-guides-deltoides/renders/detail-terminaisons.png) · [Profil et face](https://github.com/mkfreyer/logbook/blob/0fc6f0b3a0ffacc2283d26a06afa852ef3be35ad/docs/m4a/ecorche-beatriz-guides-deltoides/renders/controle-surface-3d.png) · [Deux épaules](https://github.com/mkfreyer/logbook/blob/0fc6f0b3a0ffacc2283d26a06afa852ef3be35ad/docs/m4a/ecorche-beatriz-guides-deltoides/renders/controle-deux-epaules.png)
- [Blender, projections, audit, attribution et reproduction](https://github.com/mkfreyer/logbook/blob/0fc6f0b3a0ffacc2283d26a06afa852ef3be35ad/docs/m4a/ecorche-beatriz-guides-deltoides/README.md) · [Preuve de préservation des 300 maillages](https://github.com/mkfreyer/logbook/blob/0fc6f0b3a0ffacc2283d26a06afa852ef3be35ad/docs/m4a/ecorche-beatriz-guides-deltoides/verification.json)

**Points à valider :** l’orientation reprend la caméra d’origine à −55°, avec cadrage/aspect recalés manuellement sur l’image, sans garantie de registration automatique pixel à pixel. Les deux terminaisons ont des portions masquées par des pièces du bras. Les vrais guides continuent sur le deltoïde sous-jacent ; des pointillés orange séparés signalent les occlusions. Aucun raccourcissement ou changement arbitraire de trajectoire n’est imposé.

L’audit du maillage prépare seulement l’étape suivante : domaine local englobant ancien/nouveau creux, possible régularisation locale et préservation explicite du bombé. **Aucun comblement, creusement, lissage, remesh ou subdivision n’est exécuté. Arrêt pour validation des trajectoires avant toute sculpture.**

Aucune segmentation interactive, modification de Logbook ou SQLite, ni M4B. Aucun nouvel asset ou outil payant. PR #12 maintenue en brouillon, sans fusion ; historique intégral conservé.

<details>
<summary>Livraisons précédentes conservées — historique</summary>

## Essai non validé — bombé P4 verrouillé, creux encore insuffisants

**Verdict visuel : anciens trajets encore visibles, raccords irréguliers sur le premier creux, déplacement du second pas assez net. La demande n’est pas encore satisfaite. La référence validée reste `0ab3d83`.**

Cette proposition repart du modèle P4 + tête P5 (`0ab3d83`). Seuls 203 sommets par deltoïde changent, dans des bandes géodésiques de 3 mm autour des anciens et nouveaux trajets. Le ventre principal est verrouillé, et le volume est équilibré exclusivement entre les bandes.

- [Rapport et limites](https://github.com/mkfreyer/logbook/blob/39a8eb2d3c6713e023e021cbb517c3ea7b0020b4/docs/M4A_CREUX_LOCALISES_VENTRE_PRESERVE.md)
- [Avant / après serré — vue de référence](https://github.com/mkfreyer/logbook/blob/39a8eb2d3c6713e023e021cbb517c3ea7b0020b4/docs/m4a/ecorche-beatriz-creux-localises/renders/comparatif-reference.png)
- [Bombé préservé — extrait du rendu](https://github.com/mkfreyer/logbook/blob/39a8eb2d3c6713e023e021cbb517c3ea7b0020b4/docs/m4a/ecorche-beatriz-creux-localises/renders/ventre-preserve.png)
- [Premier creux](https://github.com/mkfreyer/logbook/blob/39a8eb2d3c6713e023e021cbb517c3ea7b0020b4/docs/m4a/ecorche-beatriz-creux-localises/renders/creux-1-detail.png) · [Second creux](https://github.com/mkfreyer/logbook/blob/39a8eb2d3c6713e023e021cbb517c3ea7b0020b4/docs/m4a/ecorche-beatriz-creux-localises/renders/creux-2-detail.png)
- [Autres rendus](https://github.com/mkfreyer/logbook/tree/39a8eb2d3c6713e023e021cbb517c3ea7b0020b4/docs/m4a/ecorche-beatriz-creux-localises/renders) · [Blender, GLB et reproduction](https://github.com/mkfreyer/logbook/tree/39a8eb2d3c6713e023e021cbb517c3ea7b0020b4/docs/m4a/ecorche-beatriz-creux-localises)

Contrôles : 901 sommets du bombé strictement inchangés par épaule, zéro déplacement hors bandes, 298 autres objets inchangés, topologie conservée, volume et dimensions conservés à la précision numérique. Les images avant/après utilisent les mêmes caméras, lumières et matériau mat.

La terminaison du second tracé est atténuée au dernier point visible du deltoïde ; le point bleu final tombe sur une pièce du bras, conservée intacte. La profondeur reste modérée (amplitude nominale environ 1 mm) : les contrôles de préservation ne prouvent pas une disparition visuelle complète des anciennes lignes. Validation des gros plans encore nécessaire.

Aucune nouvelle segmentation interactive, aucune modification applicative ou SQLite, aucun M4B, aucune fusion. Arrêt après publication ; PR maintenue en brouillon. Toutes les versions précédentes restent intactes.

<details>
<summary>Historique précédent de la PR — conservé intégralement</summary>

## Retouche ciblée des trajets des creux des deltoïdes — base 0ab3d83

Une seule proposition géométrique sur la combinaison P4 + tête P5. Partie supérieure du premier creux conservée, terminaisons prolongées plus bas et second trajet déplacé selon les annotations. Le fond des anciennes dépressions est repris localement, sans gonflement compensateur des portions voisines.

- [Rapport et limites visuelles](https://github.com/mkfreyer/logbook/blob/62fe3ff801c9c2edddf8237e684b558b2c2231f8/docs/M4A_RETOUCHE_TRAJETS_DELTOIDES.md)
- [Avant / après — détail sans annotations](https://github.com/mkfreyer/logbook/blob/62fe3ff801c9c2edddf8237e684b558b2c2231f8/docs/m4a/ecorche-beatriz-trajets-deltoides/renders/comparatif-reference-detail.png)
- [Comparatif complet de référence](https://github.com/mkfreyer/logbook/blob/62fe3ff801c9c2edddf8237e684b558b2c2231f8/docs/m4a/ecorche-beatriz-trajets-deltoides/renders/comparatif-reference.png)
- [Les deux épaules](https://github.com/mkfreyer/logbook/blob/62fe3ff801c9c2edddf8237e684b558b2c2231f8/docs/m4a/ecorche-beatriz-trajets-deltoides/renders/deux-deltoides-apres.png)
- [Face / profil / trois quarts et autres comparatifs](https://github.com/mkfreyer/logbook/tree/62fe3ff801c9c2edddf8237e684b558b2c2231f8/docs/m4a/ecorche-beatriz-trajets-deltoides/renders)
- [Sources Blender, GLB et reproduction](https://github.com/mkfreyer/logbook/tree/62fe3ff801c9c2edddf8237e684b558b2c2231f8/docs/m4a/ecorche-beatriz-trajets-deltoides)

Topologie conservée : 11 938 triangles par deltoïde, aucun triangle ajouté. Volume par épaule environ −0,20 %, gabarit global conservé. 298 autres objets inchangés, dont tête, gorge, pectoraux et reste du corps. Chaque comparatif emploie exactement les mêmes caméras, lumières et matériau mat.

Les trajets ont été repérés manuellement sur le recadrage fourni ; aucun recalage automatique pixel par pixel n’est revendiqué. La seconde transition reste irrégulière par endroits et moins contrastée que les séparations des obliques/dentelés : validation visuelle encore nécessaire.

Aucun nouveau masque ou segmentation interactive des faisceaux. Aucun changement applicatif, aucune modification SQLite, aucun M4B, aucune fusion. Arrêt pour choix visuel ; PR maintenue en brouillon.

<details>
<summary>Historique antérieur de la PR — conservé intégralement</summary>

## Combinaison à valider : deltoïdes P4 exacts et tête P5

Les deux deltoïdes de P4 sont restaurés à l’identique, sans nouvelle sculpture. Le reste du corps validé, la gorge reconstruite en P4 et la tête humaine P5 sont conservés.

- [Rapport et vérifications](https://github.com/mkfreyer/logbook/blob/0ab3d838c728a88f2d325edff7a6884400c9ed78/docs/M4A_ECORCHE_COMBINAISON_P4_P5.md)
- [Planche face / profil / dos / trois quarts](https://github.com/mkfreyer/logbook/blob/0ab3d838c728a88f2d325edff7a6884400c9ed78/docs/m4a/ecorche-beatriz-combinaison-p4-p5/renders/planche-finale.png)
- [Gros plans des deux épaules](https://github.com/mkfreyer/logbook/blob/0ab3d838c728a88f2d325edff7a6884400c9ed78/docs/m4a/ecorche-beatriz-combinaison-p4-p5/renders/deux-deltoides.png)
- [Rendus individuels](https://github.com/mkfreyer/logbook/tree/0ab3d838c728a88f2d325edff7a6884400c9ed78/docs/m4a/ecorche-beatriz-combinaison-p4-p5/renders)
- [Sources Blender, GLB et méthode reproductible](https://github.com/mkfreyer/logbook/tree/0ab3d838c728a88f2d325edff7a6884400c9ed78/docs/m4a/ecorche-beatriz-combinaison-p4-p5)

Contrôle sur les fichiers d’origine : géométrie, topologie, normales et volume des deltoïdes identiques à P4 ; 298 autres objets identiques à P5. Dix rendus Blender avec le même matériau mat neutre. Les reliefs et contacts P4 sont restaurés sans nouvelle correction.

Aucune nouvelle segmentation des faisceaux commencée. Aucun changement applicatif, aucune modification SQLite, aucun M4B, aucune fusion. Arrêt pour validation visuelle de cette combinaison ; PR maintenue en brouillon.

<details>
<summary>Historique de la PR avant cette combinaison — conservé intégralement</summary>

## Passe 6 — reprise des deltoïdes à valider

Le gabarit d’épaule repart de P4 ; la tête, la gorge et toutes les autres pièces validées restent exactement celles de P5.

- Deux deltoïdes reconstruits localement pour remplacer les creux internes hérités et travailler trois convexités musculaires raccordées, sans faux traits peints ni incision ajoutée.
- Volume fermé d’épaule −3,9 % par rapport à P4/P5, sans élargissement de la silhouette de face par rapport à P4 sur les coupes contrôlées.
- Bord deltoïdien approché et arrondi vers le pectoral fixe ; écart médian des échantillons de contrôle : P4 6,2 mm / P5 7,0 mm / P6 3,6 mm.
- 298 autres objets inchangés, mêmes matériau mat neutre et éclairage équilibré. Aucun triangle supplémentaire : 11 938 triangles par deltoïde, master 498 058 triangles / 300 objets. La topologie locale change.

[Rapport et limites](https://github.com/mkfreyer/logbook/blob/cc7af9aa1330eb37d062c1f402f61fc4bf7472ca/docs/M4A_ECORCHE_PASSE6_DELTOIDES.md) · [Sources Blender / GLB / captures](https://github.com/mkfreyer/logbook/tree/cc7af9aa1330eb37d062c1f402f61fc4bf7472ca/docs/m4a/ecorche-beatriz-passe6/)

![Comparatif frontal P4 / P5 / P6](https://github.com/mkfreyer/logbook/blob/cc7af9aa1330eb37d062c1f402f61fc4bf7472ca/docs/m4a/ecorche-beatriz-passe6/renders/comparatif-epaules-face.png?raw=true)

Comparatifs [profil](https://github.com/mkfreyer/logbook/blob/cc7af9aa1330eb37d062c1f402f61fc4bf7472ca/docs/m4a/ecorche-beatriz-passe6/renders/comparatif-epaule-profil.png), [arrière](https://github.com/mkfreyer/logbook/blob/cc7af9aa1330eb37d062c1f402f61fc4bf7472ca/docs/m4a/ecorche-beatriz-passe6/renders/comparatif-epaules-dos.png), [trois quarts avant](https://github.com/mkfreyer/logbook/blob/cc7af9aa1330eb37d062c1f402f61fc4bf7472ca/docs/m4a/ecorche-beatriz-passe6/renders/comparatif-epaule-droite.png), [trois quarts arrière](https://github.com/mkfreyer/logbook/blob/cc7af9aa1330eb37d062c1f402f61fc4bf7472ca/docs/m4a/ecorche-beatriz-passe6/renders/comparatif-epaule-arriere.png), [deux deltoïdes P6](https://github.com/mkfreyer/logbook/blob/cc7af9aa1330eb37d062c1f402f61fc4bf7472ca/docs/m4a/ecorche-beatriz-passe6/renders/deux-deltoides.png). [Mannequin complet P6](https://github.com/mkfreyer/logbook/blob/cc7af9aa1330eb37d062c1f402f61fc4bf7472ca/docs/m4a/ecorche-beatriz-passe6/renders/validation-corps.png).

La lecture des trois portions reste plus douce que les bords entre objets séparés des obliques / dentelés ; elle doit être validée sur les rendus, indépendamment du succès des contrôles géométriques.

Contrôles réussis : scènes témoins P4/P5 exactes, 298 objets P5 inchangés, deltoïdes fermés et connectés sans auto-contact non adjacent détecté, symétrie et limite frontale contrôlées sur 41 hauteurs, raccord mesuré sur 206 points sources fixes. Triangles GLB comparés au master et réimport Blender réussi. 21 captures / 9 planches ; huit captures antérieures réutilisées. GLB : 498 057 triangles / 300 objets / 10,28 Mo. Aucun FPS mobile affirmé.

**PR toujours en brouillon, sans fusion. Aucun changement applicatif, SQLite ou M4B. Arrêt pour choix visuel.**

<details>
<summary>Historique conservé — passe 5 et travaux précédents</summary>

## Cinquième passe ciblée — tête et deltoïdes à valider

Le corps et la gorge de la passe 4 sont conservés. Cette proposition remplace la tête trop abstraite par une tête humaine sobre, puis renforce la lecture des trois faisceaux du deltoïde à volume d’épaule constant.

- Tête issue uniquement de la collection CC0 « Head (Animation) - Realistic », Dan Ulrich / Blender Studio, déjà disponible dans le bundle audité. Calage sur les attaches cervicales fixes, paupières, nez, lèvres et oreilles conservés ; deux yeux neutres, pas de cheveux ou textures ajoutés.
- Gorge protégée sous Z = 1,570 m ; raccord sous-mandibulaire construit sur la nouvelle tête. Les autres pièces cervicales ne sont pas retouchées.
- Deltoïdes : trois ventres convexes suivant les trajets en éventail ; transitions plus nettes, topologie et volume total conservés. Aucune incision étroite ni faux trait peint.
- 295 autres pièces du corps inchangées, mêmes matériau mat et éclairage symétrique avant/après. Versions précédentes conservées.

[Rapport et limites](https://github.com/mkfreyer/logbook/blob/354d36486cb0d44ad51dfae35278b967153a1424/docs/M4A_ECORCHE_PASSE5_TETE_DELTOIDES.md) · [Sources Blender / GLB / rendus](https://github.com/mkfreyer/logbook/tree/354d36486cb0d44ad51dfae35278b967153a1424/docs/m4a/ecorche-beatriz-passe5/)

![Face / profil / dos](https://github.com/mkfreyer/logbook/blob/354d36486cb0d44ad51dfae35278b967153a1424/docs/m4a/ecorche-beatriz-passe5/renders/validation-mat-neutre.png?raw=true)

Comparatifs : [tête en trois vues](https://github.com/mkfreyer/logbook/blob/354d36486cb0d44ad51dfae35278b967153a1424/docs/m4a/ecorche-beatriz-passe5/renders/tete-trois-vues.png), [deux épaules](https://github.com/mkfreyer/logbook/blob/354d36486cb0d44ad51dfae35278b967153a1424/docs/m4a/ecorche-beatriz-passe5/renders/deux-epaules.png), [trois angles du deltoïde](https://github.com/mkfreyer/logbook/blob/354d36486cb0d44ad51dfae35278b967153a1424/docs/m4a/ecorche-beatriz-passe5/renders/deltoide-trois-angles.png). Les avant/après individuels sont dans le rapport.

Contrôles réussis : 295 pièces inchangées ; 10 251 triangles de gorge protégés identiques ; volume et symétrie des épaules conservés ; surfaces fermées ; contacts de fermeture des lèvres identiques à la source ; GLB décodé puis réimporté dans Blender. 20 captures / 14 planches. GLB : 498 057 triangles, 300 objets, 10,28 Mo. Master à optimiser pour mobile ; aucune intégration ou mesure de FPS applicatif.

**PR toujours en brouillon, sans fusion. Aucun changement applicatif, SQLite ou M4B. Arrêt pour validation visuelle.**

<details>
<summary>Historique préservé — quatrième passe et travaux antérieurs</summary>

## Quatrième passe de finition — proposition à valider

Conserver la base de la troisième passe et les volumes validés ; clarifier le deltoïde antérieur, nettoyer la gorge et simplifier fortement le visage.

- Deltoïdes : redistribution locale du ventre antérieur et de la transition antérieur/moyen, sans agrandir l’épaule ; volume conservé et topologie inchangée.
- Gorge / tête : enveloppe continue guidée par les contours sources, cavités de dissection recouvertes, visage neutre très simplifié. Les 94 pièces remplacées restent dans les scènes historiques et dans la comparaison avant.
- 295 autres pièces conservées exactement. Même matériau mat neutre que la passe 3, même éclairage équilibré avant/après.

[Rapport et limites](https://github.com/mkfreyer/logbook/blob/9e49c787c58986b306d818a2d35a23a0e71aef87/docs/M4A_ECORCHE_PASSE4_FINITION.md) · [Tous les fichiers et rendus](https://github.com/mkfreyer/logbook/tree/9e49c787c58986b306d818a2d35a23a0e71aef87/docs/m4a/ecorche-beatriz-passe4/)

![Face / profil / dos](https://github.com/mkfreyer/logbook/blob/9e49c787c58986b306d818a2d35a23a0e71aef87/docs/m4a/ecorche-beatriz-passe4/renders/validation-mat-neutre.png?raw=true)

Gros plans et comparatifs : [épaules](https://github.com/mkfreyer/logbook/blob/9e49c787c58986b306d818a2d35a23a0e71aef87/docs/m4a/ecorche-beatriz-passe4/renders/deux-epaules.png), [gorge](https://github.com/mkfreyer/logbook/blob/9e49c787c58986b306d818a2d35a23a0e71aef87/docs/m4a/ecorche-beatriz-passe4/renders/gorge-deux-vues.png), [tête en trois vues](https://github.com/mkfreyer/logbook/blob/9e49c787c58986b306d818a2d35a23a0e71aef87/docs/m4a/ecorche-beatriz-passe4/renders/tete-trois-vues.png). Les liens avant/après individuels sont dans le rapport.

Validation : 22 captures Blender, 15 planches, conservation du volume des deltoïdes, 295 pièces inchangées, nouvelles surfaces fermées sans auto-contact non adjacent détecté, comparaison du GLB réellement sérialisé et réimport Blender réussis. GLB : 488 821 triangles / 298 objets / 10,1 Mo. Master à optimiser pour mobile ; aucune performance applicative affirmée.

Les anciennes versions, audits et rendus sont conservés. **PR toujours en brouillon, sans fusion. Aucun changement applicatif, SQLite ou M4B. Arrêt pour validation visuelle.**

<details>
<summary>Historique de description préservé — troisième passe et travaux antérieurs</summary>

La troisième passe nettoie les surfaces des pectoraux, remodèle les deltoïdes et reprend les contacts du haut du dos et du thorax, en conservant les volumes de la version `0297e9b`. **Proposition visuelle à valider ; aucune intégration.**

L’asymétrie apparente des épaules vient de l’ancien éclairage : leur géométrie était déjà symétrique à 0,00002 mm près. Les nouveaux rendus utilisent le même matériau mat neutre et un éclairage blanc physiquement symétrique. Le diagnostic compare l’ancienne géométrie sous les deux éclairages, sans mélanger ce test avec les corrections de forme.

- [Rapport, méthode et limites](https://github.com/mkfreyer/logbook/blob/033a92ae274d26f6043404ba1a435e0cc8a9ff8f/docs/M4A_ECORCHE_PASSE3_CIBLEE.md)
- [Face / profil / dos — mat neutre](https://github.com/mkfreyer/logbook/blob/033a92ae274d26f6043404ba1a435e0cc8a9ff8f/docs/m4a/ecorche-beatriz-passe3/renders/validation-mat-neutre.png)
- [Les deux épaules](https://github.com/mkfreyer/logbook/blob/033a92ae274d26f6043404ba1a435e0cc8a9ff8f/docs/m4a/ecorche-beatriz-passe3/renders/deux-epaules.png) · [Deltoïde sous trois angles](https://github.com/mkfreyer/logbook/blob/033a92ae274d26f6043404ba1a435e0cc8a9ff8f/docs/m4a/ecorche-beatriz-passe3/renders/deltoide-trois-angles.png)
- [Diagnostic d’éclairage](https://github.com/mkfreyer/logbook/blob/033a92ae274d26f6043404ba1a435e0cc8a9ff8f/docs/m4a/ecorche-beatriz-passe3/renders/diagnostic-eclairage.png)
- [Haut du dos avant/après](https://github.com/mkfreyer/logbook/blob/033a92ae274d26f6043404ba1a435e0cc8a9ff8f/docs/m4a/ecorche-beatriz-passe3/renders/comparatif-haut-dos.png)
- [Pectoraux avant/après](https://github.com/mkfreyer/logbook/blob/033a92ae274d26f6043404ba1a435e0cc8a9ff8f/docs/m4a/ecorche-beatriz-passe3/renders/comparatif-pectoraux.png) · [Thorax latéral](https://github.com/mkfreyer/logbook/blob/033a92ae274d26f6043404ba1a435e0cc8a9ff8f/docs/m4a/ecorche-beatriz-passe3/renders/comparatif-thorax-lateral.png)
- [Blender éditable](https://github.com/mkfreyer/logbook/blob/033a92ae274d26f6043404ba1a435e0cc8a9ff8f/docs/m4a/ecorche-beatriz-passe3/ecorche-passe3.blend) · [GLB mat neutre](https://github.com/mkfreyer/logbook/blob/033a92ae274d26f6043404ba1a435e0cc8a9ff8f/docs/m4a/ecorche-beatriz-passe3/ecorche-passe3.glb) · [Vérifications](https://github.com/mkfreyer/logbook/blob/033a92ae274d26f6043404ba1a435e0cc8a9ff8f/docs/m4a/ecorche-beatriz-passe3/verification.json)

**Modifications mesurées :** volume des deltoïdes −0,33 %, volume pectoral pratiquement identique, trapèzes −0,01 %. Les bras, grands dorsaux, cuisses et mollets sont inchangés. 18 objets corrigés, 372 inchangés. L’écart médian des trapèzes est réduit de 52–82 % supplémentaires sur les quatre coupes mesurées ; une petite attache médiane de liaison est reconstruite pour combler la fente visuelle, avec un sillon peu profond. Les volumes des muscles restent inchangés par cet ajout.

La réparation des replis sources nécessite une reconstruction locale des deux deltoïdes et des deux pectoraux, suivie d’une réduction de maillage : **572 805 triangles dans le master, +7,72 %, 391 objets dont une attache médiane reconstruite non musculaire**. Les quatre surfaces reconstruites sont fermées et d’un seul tenant ; aucun auto-contact non adjacent n’y est détecté par le contrôle effectué. Leurs anciens indices de triangles changent ; les identifiants d’objets sont conservés. Les mesures exactes du GLB sont fournies dans `export.json` ; les deux occurrences omises par l’exporteur sont des faces dupliquées, sans perte de surface visible. Correspondance des surfaces et réimport Blender vérifiés.

Les trois portions du deltoïde sont des régions continues de forme, avec des poids d’édition, sans séparation peinte ni segmentation médicale finale. La lisibilité doit encore être validée sur les rendus ; certaines jonctions entre portions gardent un liseré irrégulier en très gros plan. Les rapports ne certifient pas toute l’anatomie ni tous les contacts entre les 390 pièces ; optimisation mobile et interactivité restent à faire après validation.

20 vrais rendus Blender / Cycles CPU (les dix vues après sont recalculées avec l’attache médiane, les vues avant inchangées sont conservées), sans retouche des captures. Original et versions précédentes intégralement conservés. Source Beatriz Gomez Santamaria, CC BY 4.0, attribution et modifications documentées.

**PR maintenue en brouillon, sans fusion. Aucun changement applicatif, SQLite ou M4B. Aucun achat ni Astra Ultra. Arrêt pour validation.**

<details>
<summary>Livraisons précédentes conservées — passes 1/2 et historique Meshy</summary>

Deuxième passe ciblée sur l’écorché athlétique validé dans `03aa2eb`. **Silhouette conservée, retouches locales et nouveaux rendus mats neutres pour validation.**

- Deltoïdes : redistribution géométrique continue des portions antérieure, moyenne et postérieure ; volume −0,13 %, sans agrandir le gabarit. Différenciation encore modérée, à juger sur les gros plans. Trois groupes d’édition conservés dans Blender, sans segmentation médicale finale ni masques interactifs exportés.
- Triceps légèrement renforcés, biceps plus discrètement : déplacements locaux ≤ 3 mm et ≤ 1,1 mm respectivement.
- Sillon du haut du dos atténué par rapprochement médian des trapèzes : écart réduit de 58–74 % sur quatre coupes contrôlées. Une rainure reste visible.
- Finition bornée des surfaces ciblées ; volume pectoral pratiquement identique. Grands dorsaux, cuisses et mollets inchangés.

**12 objets retouchés, 378 inchangés. Aucun triangle ajouté.** Master 531 777 triangles ; GLB 531 775 triangles et 390 objets. Les deux occurrences retirées par l’exporteur sont des faces dupliquées, sans perte de surface visible. Topologie et identifiants conservés, symétrie, coutures, volumes, surfaces sérialisées et réimport Blender vérifiés. Le modèle reste un master à optimiser avant tout usage mobile.

- [Rapport court, mesures et limites](https://github.com/mkfreyer/logbook/blob/0297e9bc19c7adf8bbb3a369ab7691cd295821be/docs/M4A_ECORCHE_PASSE2_CIBLEE.md)
- [Face / profil / dos — mat neutre](https://github.com/mkfreyer/logbook/blob/0297e9bc19c7adf8bbb3a369ab7691cd295821be/docs/m4a/ecorche-beatriz-passe2/renders/validation-mat-neutre.png)
- [Épaules — trois angles en mat neutre](https://github.com/mkfreyer/logbook/blob/0297e9bc19c7adf8bbb3a369ab7691cd295821be/docs/m4a/ecorche-beatriz-passe2/renders/deltoides-mat-neutre.png)
- [Avant/après du deltoïde de profil](https://github.com/mkfreyer/logbook/blob/0297e9bc19c7adf8bbb3a369ab7691cd295821be/docs/m4a/ecorche-beatriz-passe2/renders/comparatif-epaule-profil.png) · [haut du dos](https://github.com/mkfreyer/logbook/blob/0297e9bc19c7adf8bbb3a369ab7691cd295821be/docs/m4a/ecorche-beatriz-passe2/renders/comparatif-haut-dos.png)
- [Présentation bleue](https://github.com/mkfreyer/logbook/blob/0297e9bc19c7adf8bbb3a369ab7691cd295821be/docs/m4a/ecorche-beatriz-passe2/renders/apres-bleu-trois-quarts.png)
- [Blender éditable](https://github.com/mkfreyer/logbook/blob/0297e9bc19c7adf8bbb3a369ab7691cd295821be/docs/m4a/ecorche-beatriz-passe2/ecorche-passe2.blend) · [GLB retouché](https://github.com/mkfreyer/logbook/blob/0297e9bc19c7adf8bbb3a369ab7691cd295821be/docs/m4a/ecorche-beatriz-passe2/ecorche-passe2.glb) · [Vérifications](https://github.com/mkfreyer/logbook/blob/0297e9bc19c7adf8bbb3a369ab7691cd295821be/docs/m4a/ecorche-beatriz-passe2/verification.json)

Rendus Cycles CPU réels, même matériau mat neutre, caméras et éclairage avant/après ; aucune retouche des captures. Original de Beatriz Gomez Santamaria, CC BY 4.0, attribution et modifications documentées. Original, première passe et historique Meshy conservés.

**PR toujours en brouillon, sans fusion. Aucun changement applicatif ou SQLite, aucun M4B ni Astra Ultra. Arrêt pour validation visuelle.**

<details>
<summary>Livraisons précédentes conservées — première retouche et historique Meshy</summary>

Le nouveau GLB fourni, **Ecorche - Anatomy study de Beatriz Gomez Santamaria (CC BY 4.0)**, est reconstruit depuis son côté droit anatomique pour obtenir une proposition bilatérale, puis ses principaux ventres musculaires sont renforcés modérément. L’original et l’ensemble des travaux précédents sont conservés. **Proposition à valider, aucune intégration.**

- [Rapport, méthode et limites](https://github.com/mkfreyer/logbook/blob/03aa2eb1d34c984e1477211576c5e9b26eae4d59/docs/M4A_ECORCHE_RECONSTRUCTION_ATHLETIQUE.md)
- [Rendus face / profil / dos](https://github.com/mkfreyer/logbook/blob/03aa2eb1d34c984e1477211576c5e9b26eae4d59/docs/m4a/ecorche-beatriz-retouche/renders/planche-validation.png)
- [Comparaison de face](https://github.com/mkfreyer/logbook/blob/03aa2eb1d34c984e1477211576c5e9b26eae4d59/docs/m4a/ecorche-beatriz-retouche/renders/comparatif-face.png) · [profil](https://github.com/mkfreyer/logbook/blob/03aa2eb1d34c984e1477211576c5e9b26eae4d59/docs/m4a/ecorche-beatriz-retouche/renders/comparatif-profil.png) · [dos](https://github.com/mkfreyer/logbook/blob/03aa2eb1d34c984e1477211576c5e9b26eae4d59/docs/m4a/ecorche-beatriz-retouche/renders/comparatif-dos.png)
- [Reconstruction seule / volumes renforcés](https://github.com/mkfreyer/logbook/blob/03aa2eb1d34c984e1477211576c5e9b26eae4d59/docs/m4a/ecorche-beatriz-retouche/renders/comparatif-volumes.png)
- [Contrôle des épaules](https://github.com/mkfreyer/logbook/blob/03aa2eb1d34c984e1477211576c5e9b26eae4d59/docs/m4a/ecorche-beatriz-retouche/renders/controle-deltoide.png) · [Pectoral gauche orange](https://github.com/mkfreyer/logbook/blob/03aa2eb1d34c984e1477211576c5e9b26eae4d59/docs/m4a/ecorche-beatriz-retouche/renders/selection-comparatif.png)
- [Master Blender](https://github.com/mkfreyer/logbook/blob/03aa2eb1d34c984e1477211576c5e9b26eae4d59/docs/m4a/ecorche-beatriz-retouche/ecorche-athletique.blend) · [Export GLB](https://github.com/mkfreyer/logbook/blob/03aa2eb1d34c984e1477211576c5e9b26eae4d59/docs/m4a/ecorche-beatriz-retouche/ecorche-athletique.glb) · [Contrôles géométriques](https://github.com/mkfreyer/logbook/blob/03aa2eb1d34c984e1477211576c5e9b26eae4d59/docs/m4a/ecorche-beatriz-retouche/verification.json)

**Réserve explicite : les trois faisceaux du deltoïde ne sont pas encore assez différenciés et ne sont pas segmentés indépendamment.** Le sillon médian du haut du dos reste accentué. Cette proposition est une base de retouche avec modifications à prévoir, et ne satisfait pas encore entièrement les exigences anatomiques finales.

Master : **531 777 triangles, 390 objets** (155 paires + 80 structures médianes). GLB : **531 775 triangles, 335 173 sommets, 11 551 668 octets**. L’exporteur retire deux occurrences de faces dupliquées, sans perte de surface visible. Symétrie contrôlée, coutures source cohérentes, aucun retournement de triangle détecté sur les retouches ; correspondance des surfaces sérialisées et réimport Blender vérifiées. Les 12 captures sont de vrais rendus Cycles, sans retouche 2D. Le master reste trop détaillé pour une livraison mobile directe.

**PR en brouillon, sans fusion. Aucun code applicatif, SQLite, M4B, achat, service payant ou Astra Ultra. Arrêt pour validation visuelle.**

<details>
<summary>Travaux Meshy antérieurs conservés, dont le POC de masque peint</summary>

Un **POC unique de masque peint UV sur le pectoral gauche** remplace ici la frontière imposée par les triangles. **Verdict : approche prometteuse pour ce POC.** En trois quarts et en profil, le contour est plus continu, le repli sous l’aisselle reste bleu et la jonction avec le deltoïde est plus propre. Le bord au sternum reste légèrement ondulé ; la clavicule et les attaches restent une interprétation artistique. Aucun autre muscle n’est validé par cet essai.

Base Meshy conservée depuis `898aac6` : **47 711 sommets et 95 426 triangles**, positions et indices Blender identiques à la source. Le rendu neutre est **pixel-identique** au précédent. Le GLB de test ajoute seulement **229 duplications aux coutures UV** (47 940 sommets), sans triangle ajouté ni déplacement de surface.

Le contour SVG est dessiné sur la vue réelle du Meshy, projeté une seule fois sur un UV local et enregistré en masque linéaire 1024². Le contrôle de visibilité évite de peindre les replis cachés. Pas de floutage des labels de faces, de sculpture, d’objet superposé, de normal map nouvelle ou de retouche 2D des captures. Ce n’est pas une peinture à la souris : le dessin vectoriel et sa projection sont reproductibles par script.

- [Rapport et verdict](https://github.com/mkfreyer/logbook/blob/d195974a455cb7bd00d865f86f4741389693b2a8/docs/M4A_MESHY_MASQUE_PEINT.md)
- [Comparaison rapprochée avant/après](https://github.com/mkfreyer/logbook/blob/d195974a455cb7bd00d865f86f4741389693b2a8/docs/m4a/meshy/texture-poc/renders/comparison-detail.png) · [Profil / aisselle](https://github.com/mkfreyer/logbook/blob/d195974a455cb7bd00d865f86f4741389693b2a8/docs/m4a/meshy/texture-poc/renders/comparison-profile.png)
- [Comparaison à 390 px par panneau, sans zoom](https://github.com/mkfreyer/logbook/blob/d195974a455cb7bd00d865f86f4741389693b2a8/docs/m4a/meshy/texture-poc/renders/comparison-mobile-390.png)
- [Tous les rendus Blender](https://github.com/mkfreyer/logbook/tree/d195974a455cb7bd00d865f86f4741389693b2a8/docs/m4a/meshy/texture-poc/renders) : neutre, sélection face/trois quarts, gros plans face/trois quarts/profil et contrôle par triangles
- [Blender éditable avec masque et guide embarqués](https://github.com/mkfreyer/logbook/blob/d195974a455cb7bd00d865f86f4741389693b2a8/docs/m4a/meshy/texture-poc/meshy-painted-mask.blend?raw=true)
- [Textures, SVG, UV et reproduction](https://github.com/mkfreyer/logbook/blob/d195974a455cb7bd00d865f86f4741389693b2a8/docs/m4a/meshy/texture-poc/README.md)
- [GLB de présentation statique](https://github.com/mkfreyer/logbook/blob/d195974a455cb7bd00d865f86f4741389693b2a8/docs/m4a/meshy/texture-poc/export/meshy-painted-selection.glb?raw=true) · [Binding](https://github.com/mkfreyer/logbook/blob/d195974a455cb7bd00d865f86f4741389693b2a8/docs/m4a/meshy/texture-poc/export/export-binding.json)
- [Contrôles complets](https://github.com/mkfreyer/logbook/blob/d195974a455cb7bd00d865f86f4741389693b2a8/docs/m4a/meshy/texture-poc/verification.json) · [Audit du masque](https://github.com/mkfreyer/logbook/blob/d195974a455cb7bd00d865f86f4741389693b2a8/docs/m4a/meshy/texture-poc/comparisons-and-mask-audit.json)

Validation : géométrie et UV relus, masque en une composante sans trou au seuil 0,5, couture UV hors peinture, vraie relecture des buffers GLB et PNG embarqués, sept raycasts source/export avec interpolation UV, import glTF dans Blender. Deux points dans le même triangle source donnent masque 0,003 et 0,994 : la sélection n’est plus limitée par les faces.

**Limites techniques :** UV local seulement, corps entier non déplié ; l’export GLB affiche un orange précalculé. Il fournit PBR/UV/PNG compatibles avec une voie glTF, et le masque séparé pour un futur lookup/shader. La sélection interactive, Three.js, WebView, Expo Go et les performances sur iPhone réel ne sont pas implémentés ni testés. Une texture de masque et un UV cohérent seront nécessaires avant toute extension.

Les **262 fichiers antérieurs sont inchangés**, avec 36 ajouts uniquement. [Audit par triangles conservé](https://github.com/mkfreyer/logbook/blob/d195974a455cb7bd00d865f86f4741389693b2a8/docs/M4A_MESHY_CORRECTION_MASQUES.md). PR #11 et branche M3.4C préservées. Model created with Meshy – CC BY 4.0 License ; [provenance conservée](https://github.com/mkfreyer/logbook/blob/d195974a455cb7bd00d865f86f4741389693b2a8/docs/m4a/meshy/LICENCE_ET_PROVENANCE.md). Budget additionnel **0 €**, aucun Astra ni service payant.

**PR #12 toujours en brouillon, sans fusion. Aucun changement applicatif, SQLite ou M4B. Arrêt après ce POC pour validation de l’utilisateur avant toute autre zone ou intégration.**


</details>


</details>


</details>


</details>


</details>


</details>


</details>


</details>


</details>


</details>


</details>


</details>


</details>


</details>


</details>


</details>


</details>


</details>

</details>

</details>

</details>
