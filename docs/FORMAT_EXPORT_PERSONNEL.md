# Export personnel Logbook — format 1

Format de conservation des données locales ; **pas encore importable par Logbook M3.4B**. La restauration V1 reste une tâche distincte, avec validation sur appareil. Le fichier n’est ni chiffré ni anonymisé. L’utilisateur est responsable de la destination qu’il choisit dans la feuille native.

## Enveloppe JSON

| Champ | Valeur / sens |
| --- | --- |
| `format` | `logbook.personal-data` |
| `formatVersion` | `1`, version du contrat de fichier |
| `sqliteSchemaVersion` | `8`, schéma courant M3.4B avec passages (M3.4B initial : 7 ; M3.4A : 6 ; M3.3 : 5) |
| `createdAt` | Date ISO UTC de préparation, après fixation de l’instantané |
| `application` | `{ "name": "Logbook", "version": "0.1.0" }` pour cette livraison |
| `units` | `{ "weight": "kg" }` ; les modes de charge restent dans les lignes d’exercices |
| `preferenceDefaults` | `{ "restSoundEnabled": true, "seriesDisplay": "name" }` si aucune préférence explicite n’existe |
| `rowidField` | `__rowid`, identifiant technique de ligne SQLite préservé |
| `conventions` | Identifiants des règles de tonnage, durée et repos ci-dessous |
| `restorationAvailableInExporter` | `false` ; ce logiciel exportateur n’offre pas d’import |
| `tables` | Objet contenant les 20 tables ci-dessous |

Chaque entrée de `tables` contient `columns` (noms SQL des colonnes physiques), `rows` (objets avec toutes ces colonnes, plus `__rowid`) et `rowCount` (nombre exact). `__rowid` n’est pas une colonne physique et ne figure donc pas dans `columns`. Les tables vides ont `rows: []` et `rowCount: 0`.

La sérialisation conserve les valeurs SQL : chaînes, nombres finis, `null`. Les zéros explicites restent zéro. Les booléens SQL restent leurs entiers ; les documents stockés comme TEXT (`original_targets`, `value_json`, etc.) restent des **chaînes JSON**, sans transformation des données originales. Le restaurateur devra valider puis reconstituer ces types, jamais exécuter du SQL fourni par le fichier.

Les lignes sont ordonnées par `__rowid` croissant. Les ordres métier restent dans leurs colonnes : `sort_order`, `planned_order`, `series_index`, horodatages et journaux. `__rowid` est aussi nécessaire pour conserver l’ordre de départage de choix/remplacements ayant exactement la même date. Il est local à sa table ; il ne remplace pas les identifiants stables.

## Données incluses

| Table | Identité et contenu |
| --- | --- |
| `programs` | `id`, programmes utilisateur |
| `workout_templates` | `id`, séances programmées et programme parent |
| `exercise_catalog` | `id`, références initiales et personnalisées, noms, instructions, matériel, modes |
| `workout_exercises` | `id`, exercice dans la configuration d’une séance et ordre |
| `set_templates` | `id`, étiquettes, type, objectifs et repos propres à chaque série |
| `set_load_rules` | Clé `set_template_id`, référence prévue `reference_set_id` nullable après suppression, `percent`, `basis = planned_target`. Liens seulement entre séries du même exercice ; aucune chaîne de calcul. |
| `set_actual_load_rules` | Clé `set_template_id`, référence prévue manuelle `reference_set_id`, `percent`, base `performed_weight` ; calcul différé au résultat validé de la séance. |
| `session_set_load_rules` | Clé `session_set_id`, référence de série d’exécution, base prévue/réelle, pourcentage, mode et suspension. |
| `session_set_adjustments` | `id`, portée, action, JSON des objectifs/règle/base/résultat appliqué, référence de performance et horodatage ; journal immuable. |
| `session_set_passages` | `id`, série d’exécution, séance, action `skip`/`reintegrate`, révision croissante par série et date ISO ; journal immuable des passages et réintégrations. |
| `session_personal_notes` | `id`, séance, exercice réel facultatif, texte personnel et date ; distinct des consignes prévues. |
| `workout_sessions` | `id`, entraînements actifs/terminés, provenance, instantanés, dates, choix courant |
| `session_exercises` | `id`, identité réellement utilisée, provenance et ordre programmé capturés |
| `session_sets` | `id`, séries capturées, objectifs actuels et originaux, ordre et rattachement |
| `performed_sets` | `id`, résultats réels, ordre de validation, dates et passage manuel |
| `rest_intervals` | `id`, repos prévu, début/fin, durées chronologique et active |
| `rest_pauses` | `id`, périodes de pause, y compris une pause non terminée |
| `session_exercise_replacements` | `id`, provenance et transition des substitutions temporaires |
| `session_exercise_choices` | `id`, journal des choix d’ordre effectués |
| `app_preferences` | `key`, valeur JSON et date de modification |

Les colonnes exactes sont celles du schéma v8 dans `src/db/migrations.ts`, exportées sans sélection partielle. Tous les identifiants et références sont inclus, même lorsqu’une provenance ne pointe plus vers un programme supprimé. Les historiques, courbes et statistiques d’accueil sont **dérivés** de ces réalisations et n’ont pas besoin de tables de chiffres dupliqués.

Un premier lancement possède 15 références réelles de catalogue, mais aucun programme ni entraînement. Ce catalogue n’est pas une performance ni un programme préinstallé.

## Conventions conservées

- `tonnage: recorded_kg_x_reps_including_warmups_no_doubling_no_bodyweight` : charge réellement saisie × répétitions, échauffements compris ; charge absente exclue, pas de poids corporel inventé ni de doublement automatique des haltères. Les modes de charge restent distincts.
- `duration: finished_at_minus_started_at_including_absences` : durée chronologique entre démarrage et fin, absences comprises ; pas une mesure d’effort pur.
- `restChronological: includes_pauses` : repos réel chronologique incluant les pauses manuelles.
- `restActive: excludes_pauses` : décompte actif excluant les pauses manuelles. Une pause ouverte et les horodatages permettent la reconstruction ultérieure ; aucune nouvelle durée n’est écrite dans la base pendant l’export.

## Cohérence et ressources

Une connexion indépendante en lecture seule fixe un instantané SQLite/WAL pour toutes les lectures. Une modification validée ensuite dans l’application n’apparaît pas partiellement dans le fichier. Une modification déjà validée au début y figure. Les préférences suivent ce même instantané.

L’export utilise des lots de 256 lignes et des écritures successives dans le fichier, sans construire en mémoire un objet contenant toute la base. `quick_check`, `foreign_key_check`, version de schéma, liste des tables et comptes de lignes sont contrôlés. Le fichier n’est proposé qu’après clôture réussie ; l’export ne modifie aucune ligne applicative.

Le temporaire vit dans le cache privé `logbook-personal-exports`, puis est nettoyé à la fermeture de la feuille native. Une annulation de préparation produit aucun fichier partagé. La feuille ne rapporte pas de façon fiable sauvegarde/annulation : vérifier la présence du fichier dans Fichiers. Après un arrêt brutal, ouvrir les paramètres nettoie les éventuels restes temporaires, jamais les copies enregistrées par l’utilisateur.

## Limites et évolution

Le fichier ne contient pas le code de l’application, les caches de graphiques, ressources Expo ou secrets de compte (aucun compte n’existe). Il ne comprend pas les modifications postérieures à son instantané. Aucun checksum n’est une preuve d’authenticité ; le futur import traitera le fichier comme une entrée non fiable. Le partage choisi par l’utilisateur peut copier le fichier vers un autre service ; aucun transfert n’est déclenché sans son action.

**Ne pas annoncer une sauvegarde déjà restaurable ou effacer l’ancien iPhone sur cette seule base.** La tâche [RESTAURATION_V1.md](RESTAURATION_V1.md) doit être livrée et validée avant publication. Toute nouvelle table, sémantique ou version de schéma impose d’actualiser explicitement l’export et ses tests ; un schéma inconnu est refusé plutôt que tronqué.

## Données avancées M3.4A

Le format d’enveloppe reste **1** ; `sqliteSchemaVersion: 6` identifie la nouvelle structure. `set_templates.target_weight_kg` reste null pour une série calculée : sa règle et sa référence permettent de reconstruire l’objectif. `session_sets.load_rule_snapshot` est une chaîne JSON nullable : base `planned_target`, ID de référence source, pourcentage, charge de référence, résultat capturé et mode. Cette provenance est indépendante du programme courant et n’est pas une performance réalisée. Les anciennes séances restent null. `series_display` dans `app_preferences` contient une chaîne JSON `number`, `name` ou `both` ; défaut `name`, distinct du réglage sonore. La convention `plannedLoad` précise le produit décimal sans arrondi au matériel et sa capture au démarrage.

L’export conserve les valeurs brutes et les relations de ces nouvelles données, y compris une référence devenue null après suppression. Le futur restaurateur devra valider portée, types, absence de cycles/chaînes et cohérence des instantanés, sans recalculer les résultats historiques avec le programme courant.

## Données M3.4B — schéma 7

L’enveloppe reste au format 1 : le contrat brut `tables/columns/rows` est identique, et **la version de schéma distingue obligatoirement chaque structure**. La vue interne `all_load_rules` n’est pas une table exportée : ses deux tables sources sont incluses. Les 19 tables couvrent toutes les données, même retirées logiquement, pendant un repos actif ou après clôture.

`session_sets.source_set_template_id` devient nullable pour les séries exclusivement locales. L’ancien champ obligatoire est conservé sous `legacy_source_set_template_id` avec ses valeurs ; il contient une chaîne vide pour un ajout sans modèle et ne sert jamais de lien. Les anciens IDs sont copiés sans modification dans le nouveau champ. Les nouveaux champs sont `added_at`, `addition_scope`, `addition_key` (jeton d’idempotence), `edit_scope`, `removed_at` et `initial_metadata` (nom/type/notes initiaux, JSON protégé). Un retrait ne supprime aucune performance. Le futur import devra conserver ces colonnes et distinguer les séries restantes des lignes retirées.

`load_rule_snapshot` et `original_targets` restent immuables ; une base de règle peut désormais être `performed_weight` avec résolution initiale null. Les règles courantes et le journal d’ajustements expliquent les résolutions ultérieures. Une performance validée peut produire un objectif, jamais une autre performance. `performedLoad` documente `validated_reference_weight_x_percent_div_100_proposed_target_only`, `sessionAdjustments` la conservation append-only et `removedSeries` les seuls ajouts non réalisés retirés logiquement.

Les notes personnelles restent indépendantes et peuvent être modifiées après clôture. Les nouvelles relations sont contrôlées en plus des vérifications SQLite : pas de double règle prévue/réelle, règles actives compatibles avec leurs références et modes, provenance complète des ajouts. Les IDs de modèles supprimés restent de simples provenances historiques valides ; ils ne sont pas traités comme des relations manquantes à reconstruire artificiellement.

La restauration reste une tâche V1 distincte. Elle devra vérifier les versions, ces liens et les valeurs gelées, et ne jamais réexécuter les calculs pour réécrire un résultat historique.

## Séries passées — schéma 8

Le schéma 8 contient **20 tables**. `session_set_passages` conserve tous les événements, sans mise à jour des objectifs initiaux ni insertion de performance. La dernière révision pour chaque `session_set_id` détermine le statut : `skip` = Passée, `reintegrate` = à nouveau disponible si elle n’est pas réalisée/retirée. Une série sans événement conserve son comportement antérieur. Les statuts `skippedAt`/`passageRevision` des objets TypeScript sont dérivés de ce journal ; ils ne sont pas des colonnes supplémentaires de l’export.

Les révisions commencent à 1 et sont consécutives ; les actions alternent en commençant par `skip`. Les horodatages, IDs et révisions sont conservés, même si une série ajoutée a été réintégrée puis retirée logiquement. Un dernier passage ne peut pas coexister avec une performance réelle ou un retrait. Ces invariants sont vérifiés avant partage, en plus de SQLite et des autres contrôles. La convention `skippedSeries: latest_passage_revision_is_not_a_performance` interdit de traiter un passage comme une réalisation ou un poids nul.

L’enveloppe reste format 1 et doit être interprétée avec `sqliteSchemaVersion: 8`. Une restauration future devra conserver le journal et reconstruire le dernier statut, sans compter les passages dans les performances ni rejouer les calculs historiques. **Aucune restauration n’est livrée.**


## M3.4C — Contenu des fiches sans migration

SQLite reste **v8**, l’enveloppe **format 1**, avec les mêmes **20 tables**. Présentations, étapes, conseils et liens d’alternatives du catalogue initial sont des contenus éditoriaux embarqués dans `src/data/exerciseGuides.ts`, liés aux identifiants stables existants. Ils ne sont pas des données personnelles SQLite et ne sont pas dupliqués dans le JSON. Aucun entraînement ni programme n’est créé pour les fournir.

Les consignes personnelles restent dans `exercise_catalog.instructions`, donc sont déjà exportées intégralement. Les identités du catalogue, instantanés, remplacements, règles, résultats, repos et passages restent exportés comme auparavant. Aucun nouveau champ utilisateur ou table ne nécessite de changement de format. **L’import/restauration reste indisponible.**
