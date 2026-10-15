# Tester M3.3 sur iPhone avec Expo Go

M0 à M3.2 sont validés. **M3.3 ne sera validé qu’après votre retour sur iPhone.** Les tests Linux vérifient les données et les composants ; ils ne prouvent pas le son, Fichiers ni les gestes natifs.

## Récupérer la version sur Windows

Conserver le même dossier `logbook` et le même projet Expo Go. Dans PowerShell, arrêter Metro avec **Ctrl+C**, puis :

```powershell
git fetch origin
git switch feat/m3-parametres-stabilisation
git pull --ff-only origin feat/m3-parametres-stabilisation
npm.cmd ci
npm.cmd start -- --clear
```

Si la branche n’existe pas encore sur l’ordinateur, remplacer la commande `git switch` par :

```powershell
git switch --track origin/feat/m3-parametres-stabilisation
```

Utiliser Node.js 24 et la version d’Expo Go déjà compatible avec notre SDK 57. Scanner le nouveau QR code avec l’appareil photo, iPhone et PC sur le même Wi-Fi. `--clear` efface le cache Metro, **pas SQLite**. Si le réseau local bloque la connexion, arrêter le serveur puis essayer :

```powershell
npx.cmd expo start --tunnel --clear
```

Un tunnel peut demander l’installation de son utilitaire et une connexion Internet. Ce transport de développement ne synchronise pas les données SQLite de l’application.

**Ne pas désinstaller Expo Go, supprimer son stockage, changer l’identité Expo ou effacer les programmes pour tester.** M3.3 ajoute la table de préférences et passe SQLite de v4 à **v5**. Les données M0–M3.2 restent présentes. Une ancienne branche M2/M3.1/M3.2 ne peut plus ouvrir cette base v5 ; elle la refuse sans l’effacer. Conserver cette version ou une version plus récente.

## Paramètres

1. Sur l’accueil, toucher l’engrenage. Dans Musculation, vérifier aussi le bouton **Paramètres**. Les deux ouvrent le même écran.
2. Vérifier les sections son, kilogrammes, données personnelles et À propos. Le seul réglage interactif est celui du son ; aucun changement kg/lb ni bouton Restaurer n’est proposé.
3. Revenir en arrière. Tester les swipes Accueil → Musculation et retour. Ils doivent rester identiques à la version validée.

## Son et minuteur

Utiliser un vrai entraînement de test configuré par vos soins avec au moins deux séries du même exercice et un repos court, par exemple 5 secondes. Ne pas confondre objectifs avec résultats : saisir vous-même les répétitions réelles.

1. Son activé, volume audible, mode silencieux **désactivé** : valider une série et laisser expirer le repos au premier plan. Une alerte doit être audible une seule fois. Le compteur passe en dépassement sans changer d’écran.
2. Pendant le repos, ouvrir Paramètres, couper **Son de fin de repos**, puis revenir. Le repos continue et ne sonne pas. Son temps et le passage manuel sont inchangés.
3. Fermer puis rouvrir le projet Expo Go : le réglage reste désactivé et l’entraînement est reprenable. Le repos ne repart pas de zéro.
4. Réactiver le son sur un repos déjà dépassé : aucune alarme tardive attendue. Le repos suivant peut sonner normalement.
5. Activer le mode silencieux iOS puis laisser un nouveau repos expirer : le son doit respecter ce mode. Vérifier aussi avec volume faible/coupé. En cas d’écart, indiquer modèle d’iPhone, version iOS, Expo Go et état du mode silencieux.
6. Vérifier pause/reprise, repos différents par série, fin anticipée et dépassement. **Repos réel** inclut les pauses ; le décompte actif les exclut. Le passage reste toujours manuel.

Le son utilise l’API Expo avec respect du mode silencieux. Il reste à confirmer sur votre matériel. **Aucune notification ou son écran verrouillé, Expo Go fermé ou en arrière-plan n’est garanti.** Le chronomètre est reconstruit au retour grâce aux dates sauvegardées ; une expiration manquée ne déclenche pas d’alarme tardive.

## Export personnel dans Fichiers

Le fichier contient vos données non chiffrées. Choisir un emplacement de confiance, par exemple un dossier dans Fichiers. Aucun envoi automatique n’est effectué. Une destination iCloud ou autre service n’est utilisée que si vous la choisissez dans la feuille iOS.

1. Garder si possible un entraînement terminé et un entraînement en cours, avec un repos en pause. Noter le nombre de programmes et quelques résultats existants.
2. Ouvrir Paramètres → **Exporter mes données**. Un seul export doit démarrer même en touchant rapidement deux fois. Pendant la préparation, **Annuler l’export** doit revenir à l’état normal sans partager de fichier ; sur une petite base, cette phase peut être trop brève pour la toucher.
3. Quand la feuille native apparaît, choisir **Enregistrer dans Fichiers** puis un dossier. Vérifier que le fichier `logbook-personnel-….json` y existe et n’est pas vide.
4. Recommencer puis **annuler la feuille iOS**. Logbook doit redevenir utilisable et ne pas annoncer « Sauvegarde enregistrée ». L’API ne dit pas si vous avez sauvegardé ou annulé : le message demande volontairement de vérifier Fichiers.
5. Ouvrir le JSON avec un visualiseur de texte de confiance ou le copier sur votre PC. Ne pas le publier dans un dépôt ou une capture publique. Vérifier `formatVersion: 1`, `sqliteSchemaVersion: 5`, `restorationAvailableInExporter: false` et la présence de `tables` avec 14 entrées.
6. Vérifier vos noms/identifiants et quelques lignes : `programs`, `workout_templates`, `set_templates`, `workout_sessions`, `performed_sets`, `rest_intervals`, `rest_pauses`, journaux de remplacement/choix et `app_preferences`. `__rowid` est normal, comme les textes JSON stockés dans certaines colonnes. Une charge ou un RIR absent reste `null`, un zéro explicitement saisi reste `0`.
7. Vérifier ensuite que tous les programmes et résultats sont encore visibles dans l’application. Reprendre le repos en pause : rien ne doit avoir changé à cause de l’export.
8. Fermer puis rouvrir le projet ; vérifier les préférences, l’entraînement actif et les historiques. Un export suivant doit fonctionner. Le nettoyage des temporaires ne doit jamais effacer le fichier que vous avez enregistré dans Fichiers.

Sur une installation de test vide, l’export contient les 15 références initiales du catalogue, mais aucun programme ni entraînement. **Ne pas effacer votre installation personnelle pour vérifier ce cas**, déjà couvert par les tests SQLite.

L’export correspond à un instantané : une modification validée après son début ne doit pas y apparaître partiellement. Sur Linux, un test enregistre réellement programme, préférence et série depuis une autre connexion pendant l’export ; toutes les tables exportées restent cohérentes.

## Limite essentielle : pas encore de restauration

Il n’y a **pas de bouton Restaurer** et le JSON ne peut pas encore être réimporté par l’application. Garder des copies personnelles est utile, mais **ne pas supprimer le carnet actuel ou l’ancien iPhone en pensant pouvoir déjà le restaurer**. La restauration sécurisée constitue une tâche dédiée obligatoire avant la publication V1, décrite dans [RESTAURATION_V1.md](RESTAURATION_V1.md).

## Régression rapide

- Créer/modifier un programme et une séance, ajouter/réordonner des exercices/séries, utiliser **Terminer** et **Terminer la configuration**.
- Démarrer ou reprendre un entraînement, saisir une seule série à la fois, valider une fois, quitter et reprendre plus tard.
- Remplacer temporairement un exercice puis choisir un autre exercice restant, y compris pendant le repos : pas de clôture automatique du repos ni de changement du programme.
- Finir l’entraînement puis consulter bilan, historique, courbes, fiche d’exercice et carte **Dernière fois** au prochain entraînement. L’accueil doit actualiser les séances de la semaine locale.
- Vérifier que supprimer un programme ne supprime pas ses performances historiques. Utiliser un programme de test dont vous acceptez la suppression, pas vos seules configurations.

## Vérifications facultatives sur le PC

```powershell
npm.cmd run typecheck
npm.cmd test
npm.cmd run export:ios
```

L’export iOS produit le JavaScript et les ressources, pas une application App Store. En cas de problème iPhone, noter l’action exacte, le message affiché et la version Expo Go/iOS ; ne pas effacer les données pour contourner l’erreur.
