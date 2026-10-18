# M4A — Sauvegarde et reprise après changement réseau

> **Reprise effectuée le 18 octobre 2026 depuis `1da5ba6` :** restauration des
> 3 606 fichiers vérifiée ; domaine Blender accessible (HTTP 200), bundle officiel
> récupéré et contrôlé. Les trois candidats et leurs neuf vues sont maintenant
> dans [M4A_CHOIX_MODELE.md](M4A_CHOIX_MODELE.md). **Étape courante : choix
> utilisateur, aucune intégration.** Depuis, B a été choisi provisoirement et
> une [variante B+ est proposée](M4A_B_PLUS.md), encore en attente de validation.
> La référence a été fournie à nouveau pour cette itération.
> Les instructions et constats ci-dessous
> décrivent la sauvegarde initiale et restent utiles à sa restauration.

Sauvegarde du **18 octobre 2026**, avant tout redémarrage, sur
`feat/m4a-prototype-carte-musculaire-3d`, dans la
[PR #11 en brouillon](https://github.com/mkfreyer/logbook/pull/11).
La comparaison reste incomplète : MPFB est rendu mais non approuvé, les vrais
fichiers Blender Studio restent à acquérir. Aucun moteur interactif ni M4B.

## Sauvegarde publiée

Le dossier `/workspace/work/m4a-alternatives/` est conservé dans une
[archive autonome](m4a/alternatives/checkpoint/m4a-alternatives-2026-10-18.tar.xz)
de **24 519 108 octets**. Elle contient **3 606 fichiers**, soit
**97 888 638 octets** avant compression :

- Sources MPFB et yeux MakeHuman aux commits épinglés, licences originales incluses.
- Fichier Blender courant, sauvegarde précédente `.blend1` et reproduction indépendante.
- Trois rendus MPFB finaux, réglages, métadonnées et contrôles géométriques.
- Scripts locaux, journaux utiles et notes détaillées de reprise.

SHA-256 de l’archive :

```text
d7d423d5f27781af5b5ea581de180e04b721cb92b6797eb658af0131fb9e6947
```

Le [manifeste](m4a/alternatives/checkpoint/manifest.json) donne taille et SHA-256
de chaque fichier. Le [point de reprise détaillé](m4a/alternatives/checkpoint/CHECKPOINT.md)
est consultable sans extraire l’archive. Les rendus restent également visibles
dans [l’étude comparative](M4A_CHOIX_MODELE.md).

Seuls les historiques/configurations `.git`, caches régénérables et bytecodes
Python sont exclus. Les sources MPFB n’avaient aucune modification locale ; leur
commit est consigné. Aucun original n’a été supprimé. Le code du générateur reste
sous GPL, ses assets officiels et sorties sous CC0 ; les licences de chaque source
sont conservées dans l’archive. Cette sauvegarde d’outils externes ne fait pas
partie du runtime Logbook et ne change pas la licence de l’application.

La restauration complète dans un dossier séparé et la vérification du dossier
original ont contrôlé les 3 606 tailles et empreintes. Aucun fichier applicatif,
SQLite, migration, dépendance ou fonction existante n’est modifié.

## Redémarrer avec la configuration publiée

1. Dans les paramètres de l’environnement cloud **Logbook**, conserver la
   configuration publiée autorisant `download.blender.org`, ainsi que les domaines
   déjà nécessaires. Il n’est pas utile de republier la même autorisation.
2. Après publication de cette sauvegarde dans la branche distante, arrêter puis
   redémarrer l’environnement depuis l’interface. Si l’interface propose une
   recréation pour utiliser la configuration publiée, sélectionner cette version.
   Le simple retour dans une conversation ne prouve pas que la machine a changé
   de configuration. Cette livraison n’a déclenché aucun redémarrage.
3. Reprendre cette conversation dans l’environnement démarré. L’assistant devra
   contrôler le statut réseau réellement appliqué puis effectuer le téléchargement
   officiel. L’ajout dans les paramètres, à lui seul, ne prouve pas l’accès HTTP.

Au contrôle avant sauvegarde, le runtime affichait les révisions observée/spécifiée
**24/24**, mais une ancienne version de configuration sans `download.blender.org`.
Ce constat est historique : le refaire après redémarrage, sans supposer un succès
ni un échec. Ne pas contourner le proxy ou désactiver les certificats.

## Retrouver le travail dans le nouvel environnement

Si le dépôt existe déjà, depuis sa racine :

```sh
git fetch origin
git switch feat/m4a-prototype-carte-musculaire-3d
git pull --ff-only origin feat/m4a-prototype-carte-musculaire-3d
```

S’il n’existe plus, le cloner dans un dossier libre avec l’authentification GitHub
habituelle, sans écraser un dépôt présent :

```sh
git clone --branch feat/m4a-prototype-carte-musculaire-3d \
  https://github.com/mkfreyer/logbook.git /workspace/logbook
cd /workspace/logbook
```

Si `/workspace/work/m4a-alternatives/` a persisté, vérifier la sauvegarde sans rien
écrire ni supprimer. Des fichiers supplémentaires sont autorisés ; une différence
sur un fichier sauvegardé est signalée et doit être examinée :

```sh
python3 tools/m4a/alternatives/restore_checkpoint.py \
  --destination /workspace/work --verify-only
```

Si le dossier a disparu, restaurer depuis le dépôt, sans accès réseau supplémentaire :

```sh
python3 tools/m4a/alternatives/restore_checkpoint.py \
  --destination /workspace/work
```

Python **3.11 ou plus récent** avec son module standard `lzma` suffit. Le script
contrôle d’abord l’archive, extrait uniquement les fichiers réguliers attendus
dans un dossier temporaire, vérifie toutes les empreintes puis publie le dossier.
Il refuse d’écraser un dossier existant. En cas de différences, utiliser une autre
destination pour comparer et conserver les deux versions. Ni Blender, ni
`npm install`, ni démarrage de Logbook, ni opération SQLite ne sont nécessaires
à cette restauration. Blender **4.3.2** était utilisé pour les rendus sauvegardés ;
vérifier sa disponibilité avant les prochains rendus.

## Prochaine tâche, sans refaire le travail terminé

1. Lire le point de reprise détaillé et `docs/M4A_CHOIX_MODELE.md`.
2. Contrôler la politique active puis télécharger réellement l’archive officielle :
   `https://download.blender.org/demo/asset-bundles/human-base-meshes/human-base-meshes-bundle-v1.4.1.zip`.
   Taille annoncée : 50 643 039 octets ; vérifier taille, SHA-256, CRC et licences
   internes. Si le transfert reste bloqué, arrêter et préciser l’erreur restante.
3. Inspecter les vrais corps masculins, leurs modificateurs et leur licence avant
   de les retenir. Attention aux niveaux Multires : conserver le détail sculpté
   sans multiplier aveuglément une géométrie déjà dense.
4. Comparer 2–3 meilleures bases réelles, corps entier face/trois quarts/dos,
   mêmes matériau satin gris bleuté, éclairage et fond bleu nuit. Garder le même
   cadrage pour tous ; si nécessaire, recalculer MPFB avec le cadrage commun.
   Documenter anatomie, segmentation des muscles et difficulté d’optimisation.
5. S’arrêter pour le choix utilisateur. Pas d’intégration, moteur interactif,
   M4B, fusion ou changement SQLite. Demander l’image de référence si elle
   n’est plus accessible avant de valider le rendu visuel.

Prompt de reprise à copier dans cette conversation :

> Reprends la comparaison M4A sur `feat/m4a-prototype-carte-musculaire-3d`,
> PR #11 en brouillon. Lis `docs/M4A_REPRISE_ENVIRONNEMENT.md` et le checkpoint
> détaillé, puis vérifie ou restaure `/workspace/work/m4a-alternatives/`.
> Vérifie le réseau réellement actif et télécharge le bundle officiel Blender
> Studio v1.4.1. Poursuis les vrais rendus comparatifs des 2–3 meilleures bases
> sous les mêmes angles et réglages, puis arrête-toi pour mon choix.
> Conserve la direction visuelle de ma référence ; demande-la si elle manque.
> Aucun moteur interactif, M4B, changement SQLite ou fusion. Travaille avec
> Sol 6.1 en raisonnement Élevé ; attends mon accord avant tout recours à Astra Ultra.
