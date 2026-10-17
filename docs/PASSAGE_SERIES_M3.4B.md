# M3.4B — Passer cette série / Réintégrer la série

Complément de M3.4B validée sur iPhone au commit `1da942a`. Même branche `feat/m34b-liberte-entrainement`, même PR #9 en brouillon, basée sur M3.4A. Les nouvelles actions attendent leur validation iPhone ; aucune fusion ni travail M3.4C.

## Utilisation

**Passer cette série** est une action secondaire sur l’écran actif, sous Valider la série. Elle est aussi disponible dans Modifier une série restante après choix explicite de la série. La confirmation native affiche : « Passer cette série pour aujourd'hui ? Elle restera dans votre programme. » Annuler ne modifie rien. Le passage ne sauvegarde pas les champs de formulaire non enregistrés : il conserve les objectifs déjà persistés.

Une série prévue ou ajoutée peut être passée, tant qu’elle n’est pas réalisée. L’action concerne exclusivement cet entraînement : elle n’a aucune option Programme et n’appelle aucune écriture de préparation. Aucun résultat, charge nulle, RIR ou repos ne sont créés. Une ancienne validation en attente ne peut pas s’appliquer après un cycle passage/réintégration : elle doit porter la version courante du statut.

La section Séries passées présente le vrai exercice, le nom/numéro, le statut **Passée**, les objectifs conservés et les notes de série. **Réintégrer la série** y reste disponible pendant l’entraînement. L’action conserve objectifs, règles, ajustements et identifiants ; aucun résultat n’est créé. Elle remet la série dans l’ordre normal parmi les restantes et conserve le choix libre d’exercice en cours. Elle peut ainsi redevenir active si elle est la prochaine dans cet ordre.

Les compteurs distinguent réalisées, passées et restantes. La barre de progression rapporte les performances aux séries à réaliser, sans transformer les passages en performances. La carte de reprise reprend ces compteurs. La fin exige toutes les séries réalisées ou passées **et au moins une performance véritable**. Après clôture, les statuts restent consultables mais les deux actions sont refusées.

Le bilan et le détail historique partagent une section séparée pour les séries passées, y compris un exercice sans aucune performance. Les lignes réellement validées restent dans leur ordre réel ; une série passée n’a pas de ligne de performance fictive. Tonnage, RIR, graphiques, historique d’exercice et statistiques d’accueil continuent de lire uniquement les performances réelles. Les conventions de calcul M2/M3 ne changent pas.

## Opérations distinctes

- Passer cette série : conserver pour aujourd’hui avec le statut Passée, sans changer le programme ; retour possible par Réintégrer la série.
- Retirer la série ajoutée : retrait logique M3.4B, non compté comme passage. Si l’ajout est passé, utiliser d’abord Réintégrer la série, puis Retirer la série ajoutée. Le journal antérieur reste exportable ; la dernière action est alors une réintégration et la ligne retirée n’est pas comptée dans le parcours.
- Supprimer une série du programme : action de préparation existante, distincte et confirmée. Elle n’efface ni les performances ni les statuts d’un entraînement.

Un remplacement temporaire concerne les **séries restantes**, pas les séries passées. Réintégrer ensuite une série passée conserve donc son exercice initial et ses objectifs, même si les autres séries avaient changé d’exercice. Cette occurrence initiale redevient réalisable dans la grille des exercices restants. Une occurrence déjà remplacée ne peut pas être remplacée une seconde fois depuis cette ancienne identité : un message explicite évite tout rattachement ambigu ; les remplacements successifs sur la nouvelle occurrence restent disponibles.

## Repos et charges calculées

Passage et réintégration ne modifient aucune ligne de performance, d’intervalle ou de pause. Ils n’arrêtent pas le repos, ne changent pas sa durée prévue et ne créent pas d’intervalle artificiel. Si toutes les séries suivantes sont passées pendant un repos, celui-ci reste visible, actif ou en pause ; **Terminer le repos** permet de le fermer explicitement avant la fin de séance. Le composant et les calculs du chronomètre restent inchangés. Sans repos, un passage manuel Continuer conserve la transition de la performance précédente.

Une référence réelle passée reste sans résultat. Le dépendant reste non résolu et affiche une explication avec le libellé Réintégrer la série ; aucun remplacement par la cible prévue ou par zéro. Une fois réintégrée et réellement validée, sa charge résout normalement les dépendants applicables non réalisés. Une cible passée en manuel n’est pas écrasée. Si le dépendant est lui-même passé, il peut recevoir cette proposition légitime et la conserver à sa réintégration. Une série déjà réalisée ne change jamais. Les règles fondées sur une charge **prévue** restent utilisables même si la référence est passée.

## SQLite v7 → v8

Migration additive transactionnelle : **une seule table ajoutée**, `session_set_passages`, avec index et protections. Aucune ligne v7, aucun objectif initial, ajustement, repos, note ou préférence n’est mis à jour par la migration.

Chaque ligne conserve `id`, `session_id`, `session_set_id`, `action` (`skip` ou `reintegrate`), `revision` et `changed_at` (ISO UTC). La révision est propre à l’identifiant stable de série, commence à 1 et augmente d’une unité. Les actions alternent, en commençant par skip. Le journal est append-only. Le dernier événement décide du statut ; les anciens entraînements sans événements restent inchangés.

Le repository expose les statuts dérivés `skippedAt` et `passageRevision` et conserve le journal. Les décisions capturent l’ID exact et la révision affichée. Les doublons de la même intention sont sans effet ; les actions d’un ancien cycle sont refusées. La validation réelle transmet également la révision pour rejeter une ancienne saisie après réintégration.

Les transactions exclusives sérialisent lectures/écritures et vérifient appartenance, état actif, absence de performance et de retrait. Les triggers SQLite protègent aussi le journal, l’ordre des révisions et l’interdiction d’insérer une performance pour une série encore passée. Aucune suppression physique de série passée ni modification de programme. Les erreurs laissent l’écran et les dernières valeurs disponibles pour réessayer.

Même fichier `logbook.db`, même identité Expo et dépendances. Les anciennes branches au schéma v7 ou inférieur refusent ensuite une base v8, sans l’effacer : rester sur ce correctif ou une version ultérieure. Un rechargement complet du projet est nécessaire pour initialiser la migration.

## Export et vérification

L’export personnel garde son enveloppe format 1 et annonce `sqliteSchemaVersion: 8`, avec **20 tables**. Le journal complet conserve les passages, réintégrations, identifiants, révisions et dates. L’export vérifie les relations, la succession des états et l’absence de performance/retrait incompatible avec un dernier passage. Une lecture WAL cohérente conserve le même instantané sous écritures concurrentes. La restauration JSON reste indisponible.

La fixture v7 a été produite avec les repositories publiés de `1da942a` : performances terminées, règles prévues/réelles, ajustements, ajouts locaux/Programme, retrait logique, notes, préférences et repos actif en pause. Les tests comparent toutes les lignes et anciens instantanés après migration, simulent un échec et vérifient la reprise. Les nouveaux tests couvrent aussi concurrence, actions retardées, annulation, erreurs, bilans, calculs et export.

Les vérifications Linux et CI ne constituent pas une validation tactile iPhone. Voir le [guide de test](TESTER_PASSAGE_SERIES_SUR_IPHONE.md).

Vérification du complément : **475 tests réussis** (196 SQLite/domaine, 13 navigation, 266 composants), TypeScript et export JavaScript iOS. Les 17 tests du pager ont aussi été exécutés avec diagnostic activé. Metro sert un manifeste et un bundle iOS avec l’identité Logbook conservée. Le swipe, le composant/les calculs du chronomètre et le provider du Switch sonore ne sont pas modifiés.
