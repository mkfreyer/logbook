# Reprise de la comparaison M4A — sauvegarde du 18 octobre 2026

## Objectif et limites

L’utilisateur a validé la recherche d’une nouvelle base 3D, pas la reconstruction
de BodyParts3D. Comparer 2 ou 3 bases réelles sous licence compatible avec une
application commerciale propriétaire. Étudier MakeHuman/MPFB et des modèles
athlétiques existants. Corps masculin entier, anatomie crédible, muscles définis,
surfaces relativement lisses, satin gris bleuté sur fond bleu nuit ; segmentation
précise possible, géométrie optimisable pour iPhone.

Les rendus finaux doivent montrer chaque candidat entier, face (0°), trois quarts
(−35°), dos (180°), avec matériau et éclairage identiques. S’arrêter ensuite pour
le choix du modèle. Aucun moteur interactif, M4B, changement SQLite, modification
des fonctions existantes ou fusion. La référence visuelle reste l’image jointe
dans la conversation ; la demander à nouveau si elle n’est plus accessible avant
toute validation visuelle.

L’utilisateur demande Sol 6.1 / raisonnement Élevé pour les tâches courantes.
Ne pas changer de modèle de sa propre initiative. Si Astra Ultra présente un
avantage technique significatif, arrêter avant ce travail coûteux et présenter
le problème, l’apport attendu et la tâche précise, puis attendre la décision.

## État publié et fichiers à conserver

- Dépôt : https://github.com/mkfreyer/logbook
- Branche : feat/m4a-prototype-carte-musculaire-3d
- PR #11 : ouverte en brouillon, base feat/m34c-fiches-exercices ; aucune fusion.
- Dernier commit avant cette sauvegarde : 7fb0962bfead3d37363d1a20d8af81caa5a8de89.
  La CI y a réussi. L’audit BodyParts3D antérieur est conservé dans les docs.
- Rapport courant : docs/M4A_CHOIX_MODELE.md. La comparaison est INCOMPLÈTE,
  ne pas demander de choix final sur un seul candidat.
- Trois rendus MPFB et provenance : docs/m4a/alternatives/mpfb-athletic/.
- Outils portables : tools/m4a/alternatives/.

Cette archive conserve le dossier de travail et ses sources, hors historiques Git,
caches et bytecode Python régénérables. Les fichiers Blender courants, leur version
précédente et la reproduction indépendante sont conservés. Aucun original local
n’a été supprimé pour réaliser la sauvegarde.

## Travail déjà terminé

MPFB officiel acquis au commit 3af0cd5a2ffba072e93a34e5f6f494fdc4813ddf,
version source 2.0.18, dans sources/mpfb2/. Code GPL et assets CC0 : conserver
les licences incluses. Yeux MakeHuman CC0 du commit
a8bc2d54ff0ac92e78ff71431b1023eda42bf482 dans sources/makehuman-eyes/.

mpfb-athletic-probe.blend contient MPFB_Athletic_Body et MPFB_Core_Eyes.
Paramètres dans mpfb-settings.json : homme 1, adulte 0,5, muscle 1, poids 0,35,
proportions 0,55 ; tonus abdominal 0,6, volumes pectoral et dorsal 0,25.
Ce sont des paramètres de génération, aucune statistique corporelle ou Logbook.
Helpers retirés par l’API officielle ; yeux chargés par le chargeur officiel.

renders/mpfb-athletic/ contient les trois PNG finaux 900 × 1400, Cycles CPU,
128 échantillons, et leurs métadonnées. Génération reproduite dans reproduction/ :
les deux exécutions donnent exactement la même géométrie évaluée, vérifiée dans
generation-reproduction-check.json. Corps : 13 380 sommets, 13 378 quads,
26 756 triangles ; SHA géométrie
1710848caec30b917beb3d539c150291d24434fd483e92d058265f1a0b96a7d0.
Yeux évalués : 96 sommets, 86 faces ; SHA géométrie
18029462efd56ecf32712e0e2c5ef7e0a7aad7b268df783548b387033ec3c957.

Constat : surface continue et corps cohérent, mais relief musculaire insuffisant
par rapport à la référence. MPFB n’est pas validé visuellement. Il manque la
segmentation anatomique ; les groupes de rig/helpers ne sont pas des muscles.
Le nombre de triangles ne prouve aucun FPS ou résultat GPU iPhone.

## Prochaine source à acquérir

L’utilisateur a ajouté download.blender.org et publié la configuration réseau.
Au dernier contrôle de la machine précédente, le runtime restait lié à l’ancienne
version, sans ce domaine, et renvoyait CONNECT 403. Cette note est historique :
après redémarrage, relire le statut et la politique effectivement appliqués puis
tester la requête réelle. Ne pas supposer un refus ou un succès à partir de ce texte.

Source officielle Blender Studio Human Base Meshes v1.4.1 :
https://download.blender.org/demo/asset-bundles/human-base-meshes/human-base-meshes-bundle-v1.4.1.zip

L’index officiel annonçait 50 643 039 octets. L’archive n’a pas encore été obtenue ;
aucun SHA de son contenu ni licence interne ne sont déjà vérifiés. La page de
téléchargement annonce CC0. Vérifier taille, SHA et CRC, lire les licences internes,
puis inventorier les vrais objets/collections masculins, auteurs et modificateurs.
Les corps réaliste de Dan Ulrich et stylisé de Julien Kaspar sont des pistes à
inspecter ; ne pas les déclarer retenus avant examen des vrais fichiers.

Attention au rendu : render_comparison.py évalue actuellement les modificateurs
viewport de la source, puis ajoute un niveau de subdivision de comparaison.
Pour une source sculptée en Multires, vérifier les niveaux afin de ne pas perdre
les détails sculptés, ni de multiplier inutilement une géométrie déjà dense.
Enregistrer les réglages retenus. Conserver matériau, lumière et échelle relative
identiques ; signaler les poses natives. Si une pose plus large exige un autre
cadrage, recalculer aussi les trois vues MPFB avec ce cadrage commun.

Le candidat MPFB en A-pose mesure 1,18145 unité de large pour une hauteur
normalisée de 1,8 ; caméra orthographique 2,30, ratio 900/1400. Il est cadré entier.

## Autres pistes déjà étudiées

- Alexlashko, Muscular Male Basemesh, CGTrader : 49 USD affichés, niveau bas
  annoncé 18 002 polygones, OBJ/ZTL, Royalty Free (no AI) et restrictions
  d’incorporation/récupération. Ni acheté ni rendu.
- -Sako-, Stylized Muscular Male Anatomy Basemeshes, CGTrader : 15 USD affichés,
  niveau bas annoncé 34 000 polygones, BLEND/FBX/OBJ et rig, Royalty Free.
  Ni acheté ni rendu. Les chiffres restent ceux du vendeur.
- 3D Scan Store écarté : ses conditions interdisent un visualiseur anatomique
  en ligne ou hors ligne, même avec la licence commerciale standard.
- Fab/PolyOne, base gratuite 8,7k triangles : trop peu définie, licence choisie
  non exposée sur la page consultée, fichier non acquis.

Lire le rapport publié et ses sources avant toute nouvelle recherche. Aucun achat,
contact de vendeur ou source de remplacement approximative n’a été autorisé.
La prochaine action est l’acquisition officielle Blender Studio après vérification
du réseau, pas une nouvelle génération MPFB ou un nouvel audit BodyParts3D.
