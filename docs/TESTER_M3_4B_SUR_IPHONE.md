# Tester M3.4B sur iPhone avec Expo Go

M0 à M3.4A ont été validés sur appareil. **M3.4B attend votre validation.** Aucun programme ni résultat d’exemple n’est installé. Pour ces essais, utiliser un programme identifiable ; toute série que vous validez rejoint réellement votre carnet et ses statistiques.

## Récupérer la branche sous Windows

Arrêter Metro avec **Ctrl+C**. Ouvrir PowerShell dans le dossier `logbook` :

```powershell
git fetch origin
git switch feat/m34b-liberte-entrainement
git pull --ff-only origin feat/m34b-liberte-entrainement
npm.cmd ci
npm.cmd start -- --clear
```

Si la branche n’existe pas localement, remplacer la commande `git switch` par :

```powershell
git switch --track origin/feat/m34b-liberte-entrainement
```

Conserver le même projet Expo Go, le même iPhone et le même réseau Wi-Fi. Scanner le QR code. Faire un **Reload complet du projet** dans Expo Go, ou fermer puis rouvrir ce projet ; un simple Fast Refresh peut conserver l’ancienne initialisation SQLite. `--clear` nettoie le cache Metro, pas les données SQLite.

**Ne pas désinstaller Expo Go ni effacer son stockage.** La migration v6 → v7 conserve le carnet mais les anciennes branches M3.4A et antérieures refusent ensuite cette base. Rester sur M3.4B ou une version ultérieure. Un export personnel peut être conservé séparément avant mise à jour ; il n’est toujours pas réimportable par Logbook.

## 1. Préparation et calcul réel

1. Vérifier les programmes, exercices, séries et historiques déjà présents, ainsi que les préférences de nom/numéro et de son.
2. Dans la préparation, configurer un top set manuel à 100 kg et un back-off. Ouvrir Charge calculée, choisir **Pourcentage de la charge réellement effectuée**, sélectionner explicitement ce top set et saisir 90 %.
3. La préparation ne doit pas afficher 90 kg comme une cible déjà résolue : la charge réelle est encore inconnue. Enregistrer, sortir avec Terminer / Terminer la configuration puis rouvrir pour vérifier la règle.
4. Démarrer la séance. L’écran garde une seule série et les champs Charge réelle, Répétitions réelles, RIR réel sont vides.
5. Valider le top set avec 95 kg. Terminer son repos manuellement. Le back-off doit proposer **85,5 kg**, sans remplir vos résultats réels. Choisir vos propres valeurs puis valider.
6. Refaire avec une charge réelle vide, puis avec zéro explicitement saisi : la proposition reste absente dans le premier cas et vaut zéro dans le second. Le RIR vide doit rester facultatif.
7. Vérifier qu’une règle **Pourcentage d’une série prévue** conserve son comportement M3.4A : 90 % de 100 kg prévus reste 90 kg, même si le résultat réel de la référence est 95 kg.

## 2. Ajouts, portées et retraits

1. Pendant une série active, menu « … » → Ajouter une série. Choisir l’exercice courant puis un autre exercice ; vérifier le nom/mode affiché et la remise à vide de la charge lors du changement.
2. Tester les cinq types, un nom, une plage de répétitions, les champs facultatifs, un repos propre et une note. Garder **Cette séance**, enregistrer avec plusieurs appuis rapides : un seul ajout et compteur augmenté d’une série.
3. Ouvrir le programme : aucun ajout pour Cette séance. Faire ensuite un ajout explicite **Programme** et vérifier qu’il existe aussi dans la préparation future.
4. Quitter puis rouvrir le projet. Reprendre : série ajoutée, type, cibles, règle et notes doivent être conservés. Elle reste non réalisée jusqu’à validation manuelle.
5. Menu → Modifier une série restante. Déplier Choisir une autre série restante, choisir une série non active et modifier nom/type/notes/objectifs. Vérifier la portée choisie et l’absence de changement des résultats précédents.
6. Retirer une série ajoutée non réalisée : Annuler ne change rien ; confirmer retire seulement cette série de l’entraînement. Si elle avait été ajoutée au Programme, la préparation reste conservée, comme le précise la confirmation.
7. Une série validée ne doit jamais proposer de modification/suppression. Une série prévue d’origine n’a pas d’action de retrait dans cet éditeur.
8. Après toutes les validations, **avant Terminer la séance**, utiliser le menu pour ajouter une série supplémentaire. Elle doit être proposée sans nouveau repos rétroactif ; réaliser ou retirer cet ajout, puis terminer normalement.

## 3. Repos et situations particulières

1. Pendant un repos, le mettre en pause puis ouvrir Ajouter une série. Revenir : même repos, même durée prévue, mêmes horodatages, pause conservée. Reprendre le minuteur puis terminer manuellement. Vérifier aussi le dépassement et le bouton Repos terminé.
2. Ajouter une série avec un autre repos prévu : cela ne doit pas prolonger le repos ouvert. Son propre repos sera utilisé uniquement si un intervalle est applicable après sa validation.
3. Modifier une série calculée en **charge manuelle** avant d’exécuter sa référence. Valider ensuite la référence : la cible manuelle doit rester intacte.
4. Choisir librement un autre exercice, puis revenir à la référence : le calcul doit suivre son identité stable, pas sa position à l’écran.
5. Remplacer temporairement l’exercice : les performances déjà validées gardent leur vrai exercice ; les calculs touchés sont suspendus, charges restantes libres. Choisir une référence compatible ou une cible manuelle. L’option Programme doit être indisponible pour l’occurrence remplacée.
6. Fermer complètement Expo Go pendant un repos puis revenir : reprendre le même entraînement, sans doublon, avec calcul du temps depuis les horaires persistés.
7. Dans un programme d’essai supprimable, démarrer puis quitter temporairement. Supprimer le programme et reprendre : l’entraînement et ses données doivent rester accessibles, les ajouts locaux possibles, Programme indisponible.

## 4. Notes, bilan et export

1. Menu → Notes personnelles : écrire une note pour l’entraînement, puis une pour un exercice. Fermer/réouvrir et vérifier leur conservation. Les notes de série et les consignes du programme restent distinctes.
2. Terminer la séance, ouvrir son bilan puis son historique. Vérifier les vrais résultats, l’ordre réel, le tonnage et les notes. Modifier une note depuis le bilan : aucun résultat ni repos ne doit changer.
3. Paramètres → Exporter mes données → enregistrer dans Fichiers. Le JSON doit annoncer `formatVersion: 1`, `sqliteSchemaVersion: 7`, **19 tables** ; inclure `set_actual_load_rules`, `session_set_load_rules`, `session_set_adjustments`, `session_personal_notes` et les colonnes d’ajout/retrait/provenance dans `session_sets`.
4. Ne pas partager ce fichier publiquement : il contient vos données personnelles en clair. Aucun import n’existe encore ; conserver le carnet sur l’iPhone.

## 5. Régressions et limites

Vérifier le swipe vertical Accueil ↔ Musculation dans les deux sens, les boutons accessibles, le défilement des programmes, les chargements silencieux, les créations/modifications/suppressions, les historiques/graphes et les performances précédentes. Tester le Switch sonore et sa persistance après relance.

Le son de repos reste une alerte locale au premier plan, soumise au volume et au mode silencieux iOS. Aucun son/notification en arrière-plan ou écran verrouillé n’est garanti dans Expo Go. Les calculs d’horaires et le passage manuel ne changent pas.

Vérifications facultatives sur ordinateur :

```powershell
npm.cmd run typecheck
npm.cmd test
npm.cmd run export:ios
```

L’export iOS vérifie le JavaScript et les ressources ; il ne compile pas un binaire App Store sur Windows/Linux. Signaler l’action exacte, les valeurs attendues/obtenues et la version iOS/Expo Go si un problème apparaît. **M3.4C attend votre retour sur M3.4B.**
