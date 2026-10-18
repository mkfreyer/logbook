# Attribution des rendus et scènes M4A écorché

Les PNG, planches et scènes sélectionnées de cette étude sont publiés sous
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
Le [texte intégral](licenses/CC-BY-SA-4.0.txt) est conservé.
Cette licence concerne ces assets dérivés ; elle ne remplace pas celle du code Logbook.

- **BodyParts3D**, © The Database Center for Life Science, licensed under CC Attribution 4.0 International.
  [Licence officielle actuelle](https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html),
  mise à jour le 27 février 2025. Les anciens en-têtes OBJ mentionnent encore
  **CC BY-SA 2.1 Japan** ; cette provenance historique est conservée dans
  [l’audit initial](../../AUDIT_M4A_ANATOMIE.md). Les présentes sorties sont
  diffusées sous CC BY-SA 4.0, sans effacer cette ancienne mention.
- **Z-Anatomy — The libre 3D atlas of anatomy**, par **Gauthier Kervyn** ;
  modèle original BodyParts3D par **Kousaku Okubo** ;
  [notice source complète](licenses/Z-Anatomy-License.txt), CC BY-SA 4.0.
  Le modèle est chargé comme bibliothèque, sans exécuter ses scripts/add-ons.
  Les crédits des autres contributeurs restent dans cette notice.
- **Écorché**, [Charleeh/ecorche](https://github.com/Charleeh/ecorche), CC BY-SA 4.0,
  d’après BodyParts3D et Z-Anatomy par Gauthier Kervyn.
  Les géométries Z de ce dérivé proviennent de l’export **BodyExplorer** par
  **Johan Bellander**. [Attributions et modifications de l’auteur](licenses/Ecorche-ATTRIBUTION.md),
  [licence du dépôt source](licenses/Ecorche-LICENSE.md).

Modifications M4A : sélection des maillages musculaires ; douze tendons/aponévroses
authentiques conservés pour Z-Anatomy ; os, yeux, cartilages et organes exclus ;
application des transformations du fichier, translation et échelle uniforme ;
soudure des positions strictement identiques **à l’intérieur de chaque OBJ BP3D** ;
ombrage lisse, remplacement des matières et éclairage commun. Uniquement dans les
vues `selection.png`, les trois composants réels du **grand pectoral gauche**
reçoivent la matière orange. Les planches assemblent et redimensionnent les PNG.
Aucune sculpture, fermeture artificielle des trous, subdivision ou décimation M4A.

**Attention au périmètre Z-Anatomy :** son atlas complet contient des notices tierces
CC BY-NC / CC BY-NC-SA pour le rein et l’oreille interne, ainsi que d’autres crédits.
Ces organes et les collections nerveuses ne sont pas importés dans cette étude.
Les muscles stapédien et tenseur du tympan sont également exclus de la sélection Z.
La sélection n’est pas une autorisation commerciale globale de l’atlas.
Avant une distribution commerciale, conserver la provenance du sous-ensemble retenu
et lever les éventuelles ambiguïtés de droits. Ne pas embarquer l’atlas entier.

Les scènes de sauvegarde ne contiennent que les maillages sélectionnés ; les
datablocks inutilisés du chargement initial sont purgés. Leurs positions et leur
topologie sont vérifiées identiques avant/après sauvegarde et rechargement.

Les licences commerciales des candidats payants ne sont **pas** acquises.
Leurs fichiers et images promotionnelles ne sont pas redistribués dans ce dossier.
