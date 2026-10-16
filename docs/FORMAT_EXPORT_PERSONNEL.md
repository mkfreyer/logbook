# Export personnel Logbook — format 1

Format de conservation des données locales ; **pas encore importable par Logbook M3.4A**. La restauration V1 reste une tâche distincte, avec validation sur appareil. Le fichier n’est ni chiffré ni anonymisé. L’utilisateur est responsable de la destination qu’il choisit dans la feuille native.

## Enveloppe JSON

| Champ | Valeur / sens |
| --- | --- |
| `format` | `logbook.personal-data` |
| `formatVersion` | `1`, version du contrat de fichier |
| `sqliteSchemaVersion` | `6`, schéma de la base exportée (M3.4A ; anciens fichiers M3.3 : 5) |
| `createdAt` | Date ISO UTC de préparation, après fixation de l’instantané |
| `application` | `{ "name": "Logbook", "version": "0.1.0" }` pour cette livraison |
| `units` | `{ "weight": "kg" }` ; les modes de charge restent dans les lignes d’exercices |
| `preferenceDefaults` | `{ "restSoundEnabled": true, "seriesDisplay": "name" }` si aucune préférence explicite n’existe |
| `rowidField` | `__rowid`, identifiant technique de ligne SQLite préservé |
| `conventions` | Identifiants des règles de tonnage, durée et repos ci-dessous |
| `restorationAvailableInExporter` | `false` ; ce logiciel exportateur n’offre pas d’import |
| `tables` | Objet contenant les 15 tables ci-dessous |

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
| `workout_sessions` | `id`, entraînements actifs/terminés, provenance, instantanés, dates, choix courant |
| `session_exercises` | `id`, identité réellement utilisée, provenance et ordre programmé capturés |
| `session_sets` | `id`, séries capturées, objectifs actuels et originaux, ordre et rattachement |
| `performed_sets` | `id`, résultats réels, ordre de validation, dates et passage manuel |
| `rest_intervals` | `id`, repos prévu, début/fin, durées chronologique et active |
| `rest_pauses` | `id`, périodes de pause, y compris une pause non terminée |
| `session_exercise_replacements` | `id`, provenance et transition des substitutions temporaires |
| `session_exercise_choices` | `id`, journal des choix d’ordre effectués |
| `app_preferences` | `key`, valeur JSON et date de modification |

Les colonnes exactes sont celles du schéma v5 dans `src/db/migrations.ts`, exportées sans sélection partielle. Tous les identifiants et références sont inclus, même lorsqu’une provenance ne pointe plus vers un programme supprimé. Les historiques, courbes et statistiques d’accueil sont **dérivés** de ces réalisations et n’ont pas besoin de tables de chiffres dupliqués.

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
