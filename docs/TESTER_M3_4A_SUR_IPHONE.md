# Tester M3.4A sur iPhone — Expo Go

M0 à M3.3 sont validés. **M3.4A attend votre validation sur iPhone.** Garder le même projet Expo Go pour retrouver le carnet.

## Mise à jour PowerShell

Arrêter Metro avec **Ctrl+C**, ouvrir PowerShell dans le dossier `logbook` :

```powershell
git fetch origin
git switch feat/m34a-series-avancees
git pull --ff-only origin feat/m34a-series-avancees
npm.cmd ci
npm.cmd start -- --clear
```

Si Git ne trouve pas la branche localement, utiliser `git switch --track origin/feat/m34a-series-avancees`. Node.js 24 et Expo Go compatible SDK 57, comme auparavant. Scanner le QR code avec l’iPhone, sur le même Wi-Fi. En cas de blocage réseau local : arrêter Metro puis `npx.cmd expo start --tunnel --clear` (peut demander l’utilitaire tunnel).

Après ce changement de version, fermer puis rouvrir le projet Expo Go, ou utiliser **Reload** dans son menu de développement. Un rechargement complet permet d’exécuter la migration au démarrage ; ne pas se contenter d’un rafraîchissement partiel des composants.

**Ne pas désinstaller Expo Go ni effacer ses données.** La migration v5 → v6 conserve programmes, historiques, préférences et entraînement en cours. M3.3 ne pourra plus ouvrir cette base v6 : rester sur cette branche ou une version ultérieure. `--clear` vide seulement le cache Metro.

## Séries ordinaires et noms

1. Avant l’essai, retrouver les programmes et bilans déjà enregistrés. Vérifier le réglage du son et, si présent, le repos en pause de la séance en cours.
2. Dans une séance de votre choix, créer une série de travail normale. Laisser les options avancées fermées. Tester nom facultatif, répétitions exactes puis plage, charge/RIR laissés vides, repos et notes. Enregistrer puis rouvrir : mêmes valeurs.
3. Tester **Suggestions de noms**. Choisir un nom ne doit pas changer le type de série. Tester ensuite les cinq types : travail, échauffement, top set, back-off, personnalisée. Échauffements et calculs restent facultatifs.

## Échauffements et back-off calculés

Les nombres suivants sont des **objectifs de configuration**, pas des performances à enregistrer artificiellement.

1. Créer un **Top set** avec cible 100 kg, puis un échauffement du même exercice. Ouvrir **Charge calculée (facultatif)** → **Pourcentage d’une série prévue**. Choisir explicitement le top set comme référence, saisir 50 : proposition **50 kg**. Répétitions et repos restent ceux que vous choisissez, par exemple 5 répétitions et 30 s.
2. Créer un deuxième échauffement à 75 % de cette référence : **75 kg**, avec un repos différent. Créer un back-off à 90 % : **90 kg**. Déplacer les échauffements avant le top set avec les flèches ; leurs références et charges doivent rester correctes.
3. Modifier le top set à 80 kg : les objectifs calculés deviennent 40, 60 et 72 kg. Modifier un pourcentage avec virgule, rouvrir les écrans et vérifier la persistance. Aucun arrondi au matériel : 83,25 kg à 12,5 % donne **10,40625 kg**.
4. Sur le back-off, toucher **Remplacer par une charge manuelle**, saisir votre autre cible et sauvegarder. Changer encore le top set : ce back-off manuel ne doit plus suivre sa charge.
5. Vider la charge de référence : les cibles liées indiquent une charge à définir, jamais 0 inventé. Un zéro explicitement saisi reste zéro.
6. La référence doit toujours appartenir au même exercice ; un back-off ne propose que les top sets manuels. Aucun échauffement calculé ne doit pouvoir être choisi comme référence. Pour changer le type d’une référence utilisée vers un type incompatible, un message doit demander de retirer ses liens d’abord.
7. Sur des séries de test dont vous acceptez la suppression, supprimer la référence. La confirmation doit avertir des séries dépendantes ; elles restent présentes avec une charge à redéfinir. Choisir une autre référence ou le mode manuel pour continuer leur édition.
8. Répéter sur un exercice en charge totale, un en charge par haltère et un en charge ajoutée. Le calcul ne doit ni doubler les haltères ni ajouter un poids corporel.

## Affichage et historique

1. Paramètres → **Affichage des séries** : choisir Numéro uniquement, Nom uniquement, puis Numéro et nom. Revenir à la préparation : les titres doivent suivre ce choix. Les numéros correspondent à l’ordre actuel.
2. Fermer et rouvrir le projet : préférence conservée. Sans nom, le type ou « Série N » fournit un repli lisible.
3. Consulter un bilan et un historique existants. L’affichage change, mais les noms capturés, performances, modes et statistiques restent les mêmes. Le Switch sonore doit conserver son réglage et sa fluidité, même après plusieurs choix rapides d’affichage.

## Entraînement réel et régressions

1. S’il existe déjà un entraînement en cours, vérifier d’abord sa reprise : progression et repos inchangés. Le bouton Démarrer ne doit pas créer de doublon ; terminer votre vraie séance selon votre usage avant d’en commencer une autre.
2. Au démarrage d’une nouvelle séance comportant une charge calculée, vérifier l’objectif affiché. **Charge réelle, répétitions réelles et RIR réel restent vides** ; une seule série est active.
3. Quitter temporairement, changer la programmation puis reprendre : l’entraînement déjà commencé garde les cibles capturées, sans recalcul sur les nouveaux objectifs. Ne saisir que vos résultats réellement effectués.
4. Vérifier validation unique, repos individuel, pause/reprise, dépassement et passage toujours manuel. Une règle de pourcentage ne doit jamais modifier une série réalisée ni déclencher automatiquement une nouvelle performance.
5. L’éditeur manuel déjà présent pendant une séance reste disponible. Pour une série calculée, son texte précise que **Programme** remplace la règle future par la cible manuelle saisie ; **Cette séance** garde le programme. Aucun calcul sur les résultats réels n’est livré avant M3.4B.
6. Vérifier les swipes, les actualisations silencieuses de l’accueil et des programmes, les boutons Terminer et Terminer la configuration, les suppressions et les historiques.

## Export personnel

Dans Paramètres, exporter vers Fichiers puis ouvrir le JSON dans un lecteur de confiance : `formatVersion: 1`, `sqliteSchemaVersion: 6`, **15 tables**, dont `set_load_rules`. Vérifier références/pourcentages, `session_sets.load_rule_snapshot` pour un nouvel entraînement calculé et `app_preferences` avec `series_display` si vous avez choisi un affichage. Une ancienne séance ne reçoit pas de règle rétroactive. Reprendre ensuite votre carnet : l’export ne doit avoir rien modifié.

Ce fichier personnel n’est pas chiffré et n’est **pas encore réimportable** par Logbook. Ne pas effacer le carnet actuel en pensant pouvoir le restaurer. Les alertes sonores restent soumises au mode silencieux/volume ; aucune alerte écran verrouillé ou en arrière-plan n’est garantie dans Expo Go.

Pour un problème, noter l’écran, l’action, le résultat attendu/obtenu et la version Expo Go/iOS. La validation tactile reste la vôtre ; M3.4B attend votre retour.
