# Restauration personnelle — tâche obligatoire avant publication V1

## Décision M3.3

M3.3 livre l’export complet, **aucun import ni bouton de restauration**. Le fichier format 1 conserve les informations nécessaires à une reconstruction future, mais aucune restauration de ce fichier n’a encore été implémentée ou validée sur iPhone. Le changement d’appareil n’est donc pas encore un parcours couvert.

Le choix de reporter évite un remplacement de base insuffisamment testé au milieu des connexions du `SQLiteProvider`, des repositories, d’un repos actif et de l’observateur sonore. Une transaction d’insertion seule ne couvre pas le redémarrage de ces connexions ni une interruption du processus lors du changement de fichier. Cette tâche est un **prérequis de publication App Store V1**, distinct de M3.4 et du coaching V2.

## Politique proposée : remplacement explicite, pas fusion implicite

Importer dans une base de préparation indépendante. Présenter les nombres de programmes et d’entraînements du fichier, sa date, l’état d’une éventuelle séance active et le fait que le carnet local sera remplacé. Exiger une confirmation native explicite. Annuler ne doit modifier ni fichier local ni préférence.

Conserver une copie de récupération vérifiée du carnet actuel avant tout changement, et expliquer où elle se trouve. Un échec ne doit jamais supprimer le carnet courant. La copie précédente reste récupérable après redémarrage jusqu’à validation du nouveau carnet. Définir et tester sa durée de conservation et sa suppression explicite. Une fusion de deux carnets, avec collisions d’identifiants et plusieurs séances actives, est hors de cette première restauration : ne jamais la simuler en régénérant silencieusement des UUID.

Cette politique doit être annoncée dans l’interface avant confirmation. Pour un premier appareil vide, le parcours peut être simplifié, tout en gardant validation et confirmation. Un export préalable ne dispense pas d’une récupération automatique locale.

## Validation avant toute écriture dans le carnet actuel

1. Sélection native d’un fichier local choisi par l’utilisateur. Contrôler sa taille avant lecture et fixer une limite documentée ; lecture progressive si nécessaire pour plusieurs années de données. Pas de permission générale aux fichiers ni d’envoi réseau.
2. Vérifier `format`, `formatVersion`, `sqliteSchemaVersion`, champs obligatoires, types, colonnes autorisées, comptes, nombres finis, chaînes, plages numériques, modes et unités. Refuser une version inconnue ou future avec un message clair. Les anciens formats acceptés doivent avoir une conversion testée.
3. Vérifier unicité des identifiants et `__rowid` par table, limites sûres des entiers, toutes les relations et leur portée : une série/performance/repos ne doit jamais changer d’entraînement via une référence incohérente. Les références de provenance supprimées peuvent rester sans parent selon le schéma historique ; ne pas rejeter un cas historique valide.
4. Valider les JSON stockés comme TEXT, types de séries, cibles, pauses ouvertes/fermées, horodatages, ordre, journaux de remplacement/choix, immutabilité des performances et au plus un entraînement actif. Vérifier les valeurs de préférences connues ; préserver explicitement ou refuser celles inconnues selon la version.
5. Ne pas identifier les références de catalogue par leur nom : conserver les IDs exportés, y compris les exercices renommés. Ne pas réinjecter automatiquement un catalogue si cela double les références existantes. Conserver les `null`, zéros et modes de charge distincts.

## Préparation, transaction et récupération

- Construire le schéma attendu à partir du code de l’application, jamais à partir de SQL du fichier. Insérer par paramètres liés dans une **transaction** de la base de préparation. Prévoir un chemin spécifique pour importer l’historique tout en respectant les protections de performances immuables ; ne jamais désactiver ces protections dans la base active.
- Conserver les ordres et `__rowid` nécessaires au départage des journaux. Activer les contraintes et vérifier les index, déclencheurs et relations après insertion. Exécuter intégrité SQLite et validations métier, puis comparer comptes et données sources, bilan compris.
- Mettre en place une barrière globale d’écriture et une interface occupée non ambiguë. Suspendre observateurs, sauvegardes et son ; attendre les écritures en cours ; fermer **toutes** les connexions et requêtes actives, pas seulement le lecteur d’export. Gérer correctement WAL/SHM via SQLite avant de déplacer des fichiers, sans effacer un journal non consolidé.
- Concevoir une procédure de bascule atomique et un journal d’état de récupération indépendant, durable. À chaque démarrage, déterminer sans ambiguïté quel carnet est valide ; pouvoir revenir au précédent si la bascule est incomplète. Évaluer les garanties réelles de renommage/fermeture sur iOS avant de choisir cette procédure.
- Rouvrir les providers/repositories, vérifier la base finale puis seulement confirmer la réussite. Restaurer un repos actif à partir de ses dates et pauses sans le redémarrer ni jouer une alarme tardive. Les caches et préférences en mémoire doivent correspondre au nouveau carnet.
- Les temporaires invalides sont nettoyés après abandon ; la dernière copie valide ne l’est jamais automatiquement pendant une erreur. Ne pas afficher de contenu personnel dans les logs.

## Tests bloquants

- Aller-retour export → restauration → export : égalité des données, IDs, ordres, objectifs originaux, performances, temps, pauses et préférences ; dates égales dans les journaux incluses.
- Carnet vide, plusieurs années, programme supprimé, exercice renommé/remplacé, poids absent/zéro, RIR absent/zéro, entraînement actif et repos en pause.
- Format tronqué, JSON invalide, version future, table/colonne inconnue, doublons, liens cassés ou inter-séances, nombre non fini, objectifs invalides, plusieurs séances actives : refus sans modification du carnet existant.
- Annulation à chaque étape, double clic, stockage saturé, erreur de lecture/écriture/fermeture et panne pendant insertion ou bascule : récupération de l’ancien carnet, y compris après fermeture forcée du processus.
- Repositories reconstruits, statistiques recalculées, historique identique, poursuite d’un entraînement et nouvelles écritures sans doublon.
- Essais réels sur iPhone : sélectionner depuis Fichiers, restaurer dans une installation de test indépendante, fermer/réouvrir pendant les étapes sensibles et vérifier reprise/chronomètre. Ne pas utiliser le seul carnet du propriétaire pour les essais destructifs.

La restauration ne sera annoncée disponible qu’après ces garanties et la validation native. L’export M3.3 reste utile pour conserver une copie personnelle lisible et préparer cette tâche, sans promettre un import actuel.

## Extension M3.4A — schéma 6

La restauration devra également importer `set_load_rules`, vérifier même exercice, référence manuelle, type top set pour les back-offs, pourcentage > 0 et ≤ 100 et absence de chaîne/cycle. Une référence null après suppression est valide ; aucune charge ne doit être inventée. Préserver exactement `session_sets.load_rule_snapshot` et son mode de charge sans le recalculer depuis les préparations actuelles. Vérifier la préférence `series_display` (number/name/both). Tester des exports v5 et v6, anciens instantanés nulls, suppressions et entraînements actifs avec calculs capturés. L’import reste absent en M3.4A.

## Extension M3.4B à prendre en charge

Le futur restaurateur devra accepter explicitement le schéma 7 (19 tables), les liens source nullables/colonne de compatibilité, les ajouts et retraits logiques, les règles réelles et prévues distinctes, les ajustements append-only et les notes personnelles. Valider les références d’exécution, suspensions, modes de charge et jetons d’ajout, sans recalculer les captures ou performances. Les métadonnées initiales sont immuables. Aucun import n’est livré en M3.4B.
