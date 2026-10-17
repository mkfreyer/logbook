# Tester les séries passées et réintégrées sur iPhone

M3.4B initiale est validée sur appareil. Ce complément reste à tester dans Expo Go avant M3.4C. Aucun jeu de données n’est installé. Utiliser une séance d’essai identifiable : seules les performances que vous validez rejoignent réellement votre carnet.

## Installation Windows PowerShell

Arrêter Metro avec **Ctrl+C**, puis dans le dossier `logbook` :

```powershell
git switch feat/m34b-liberte-entrainement
git pull --ff-only origin feat/m34b-liberte-entrainement
npm.cmd ci
npm.cmd start -- --clear
```

Scanner le QR code dans le même projet Expo Go. Faire un **Reload complet du projet**, ou fermer puis rouvrir ce projet : un simple Fast Refresh peut conserver l’ancienne initialisation SQLite. `--clear` nettoie le cache Metro, pas le carnet.

La migration **v7 → v8** conserve les données. Les versions précédentes ne pourront ensuite plus ouvrir cette base : rester sur le correctif ou une version ultérieure. **Ne pas désinstaller Expo Go ni effacer son stockage.** L’export reste conservable dans Fichiers mais aucune restauration n’existe encore.

## Passer et réintégrer

1. Démarrer une séance comportant plusieurs séries. Vérifier que Valider la série reste l’action principale et que **Passer cette série** est visible comme action secondaire.
2. Toucher Passer cette série, puis **Annuler** : même série active, mêmes objectifs, aucune performance ni repos créé.
3. Confirmer le passage : la série suivante disponible apparaît. La série précédente figure dans **Séries passées**, avec le statut **Passée**, ses cibles et notes. Le compteur distingue réalisées / passées / restantes.
4. Utiliser **Réintégrer la série**. Vérifier les mêmes nom, type, charge cible, répétitions, RIR, repos et notes. Elle revient dans l’ordre normal ; les champs de résultats restent libres, jamais remplis automatiquement. La réaliser pour vérifier la validation normale.
5. Passer plusieurs séries successivement. Tester des doubles appuis rapides sur les deux actions : chaque action doit concerner une seule série, sans doublon ni passage de la suivante.
6. Depuis le menu « … » → Modifier une série restante, choisir une autre série non réalisée puis Passer cette série. Aucun changement du programme. Les champs non enregistrés de cet éditeur ne sont pas appliqués par le passage.
7. Ajouter une série, puis la passer et la réintégrer. Pour tester le retrait distinct, utiliser ensuite Retirer la série ajoutée : elle ne doit plus être comptée comme passée. Vérifier séparément que les séries prévues dans le programme existent toujours pour le prochain entraînement.

## Reprise et fin

1. Avec des séries passées, Quitter et reprendre plus tard ; fermer complètement Expo Go puis rouvrir le projet. Vérifier le statut, les compteurs, les objectifs et l’accès à Réintégrer la série.
2. Choisir librement un autre exercice puis réintégrer une série d’un exercice précédent : le choix d’exercice en cours doit être respecté et l’autre série rester accessible.
3. Terminer une séance avec de vraies séries réalisées et d’autres passées. Le bilan et le détail historique montrent les passages séparément. Tonnage, RIR et nombre réalisé ne doivent compter que les validations réelles.
4. Après clôture, aucune action Réintégrer la série ni Passer cette série ne doit permettre de changer les statuts.
5. Dans une séance d’essai, passer toutes les séries sans en réaliser aucune : Terminer la séance doit rester indisponible. Réintégrer une série puis enregistrer une vraie performance pour pouvoir finir.

## Repos et références

1. Valider une série pour ouvrir son repos et mettre le minuteur en pause. Depuis les actions, passer toutes les séries encore restantes.
2. Revenir au repos : même intervalle, même durée prévue et pause conservée. Le repos ne se ferme pas automatiquement, même sans série restante. Utiliser **Terminer le repos** pour le fermer manuellement.
3. Refaire en réintégrant une série pendant ce repos : le minuteur et ses pauses ne doivent pas repartir de zéro ; le passage à la suite reste manuel.
4. Préparer un top set à 100 kg et un back-off à 90 % de sa **charge réelle**. Passer le top set : la cible du back-off reste non résolue, avec une explication. Aucun 90 kg prévu ni 0 kg fictif ne remplace la charge réelle absente.
5. Réintégrer le top set, le valider à 95 kg : la cible doit devenir **85,5 kg**, sauf si vous aviez explicitement choisi une cible manuelle. Aucun résultat réel du back-off n’est prérempli.
6. Vérifier séparément un pourcentage de **charge prévue** : il reste calculable même si sa référence est passée.
7. Si un exercice est remplacé alors que certaines séries sont passées, ces séries conservent leur exercice initial et leurs cibles. Leur réintégration doit permettre de les retrouver et de les réaliser sur cet exercice.

## Export et régressions

Exporter depuis Paramètres vers Fichiers : vérifier `formatVersion: 1`, `sqliteSchemaVersion: 8`, **20 tables**, dont `session_set_passages`. Chaque passage/réintégration conserve la série, l’action, la révision et la date. Le carnet doit rester inchangé après export ; le fichier n’est pas encore réimportable.

Refaire les swipes Accueil ↔ Musculation, les chargements silencieux, le Switch sonore, un repos normal/dépassé, les notes, ajouts/modifications, bilans et graphiques. Le son reste soumis au mode silencieux et au premier plan ; aucune notification en arrière-plan n’est promise.

Vérifications facultatives sur ordinateur :

```powershell
npm.cmd run typecheck
npm.cmd test
npm.cmd run export:ios
```

Pour un problème, noter l’écran, la série concernée, l’action et le résultat attendu/obtenu. **Votre validation sur iPhone reste nécessaire avant la suite.**
