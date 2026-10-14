# Spécification technique fonctionnelle — Application Musculation & Cardio

**Version :** 0.1 — 14 octobre 2026  
**Statut :** document de passage vers le développement ; propositions techniques à confirmer avant implémentation.  
**Périmètre de démarrage :** iPhone, musculation, sans compte et sans serveur, données locales.  
**Sources :** `cahier_des_charges_musculation.xlsx` (66 décisions F-001 à F-066), `cahier_des_charges_fonctionnel_musculation.docx`, maquette V2 validée des 21 écrans, puis dernières décisions orales.

> **Consigne fondamentale pour Codex :** ne jamais interpréter une maquette comme une spécification de contenu préinstallé ni implémenter les 21 écrans d'un seul coup. Respecter les règles ci-dessous, signaler les ambiguïtés et avancer par petites tâches testables.

## 1. Objectif du produit

Créer un **logbook de musculation moderne**, pensé d'abord pour les débutants mais sans brider les pratiquants avancés. Pendant l'effort, l'utilisateur voit **une seule série à la fois**. Il peut enregistrer charge, répétitions et RIR puis piloter son repos. Hors séance, il organise ses programmes, consulte ses historiques et ses graphiques. L'application n'impose pas de progression automatique dans son mode principal.

Principes non négociables :
- **Simplicité pendant l'effort** : une seule série active, une seule action principale, commandes secondaires discrètes.
- **Contrôle utilisateur** : aucune transition automatique à l'expiration du repos ; choix manuel de modifier, remplacer ou sauter à un exercice restant.
- **Prévu ≠ réalisé** : ne jamais écraser une donnée effectivement réalisée par une prévision modifiée ultérieurement.
- **Hors ligne d'abord** : la séance doit être utilisable sans réseau et sauvegardée progressivement.
- **Débutants d'abord** : configuration avancée facultative ; termes comme RIR et double progression expliqués simplement.
- **Aucun programme préinstallé au lancement initial** : « Prise de muscle », « Force » et « Push » sont des exemples de maquettes, pas du contenu à livrer automatiquement.

## 2. Statuts, priorités et décisions

- **VALIDÉ — Produit** : règle issue des échanges utilisateur et du cahier des charges.
- **PROPOSÉ — Technique** : choix pragmatique pour Codex, modifiable si un meilleur choix est justifié.
- **À CONFIRMER** : décision manquante ; ne pas la supposer validée.

**M0 — Socle exécutable.** Projet iOS Expo/TypeScript, navigation, thème, création locale d'un programme et d'une séance, base de données, application vide au premier démarrage.

**M1 — Séance utile en salle.** Exercices, séries configurables, saisie une série à la fois, repos prévu/réel et dépassement, pause et bouton dynamique, modification de série, sauvegarde/récupération après fermeture.

**M2 — Liberté en séance.** Remplacer un exercice temporairement, sélectionner dans une grille un autre exercice restant, conserver l'ordre normal sinon, finir et consulter le bilan (durée réelle, séries, tonnage).

**M3 — Historique et confort.** Historique général → programme → séance → exercice, graphiques, dernière performance, fiches/bibliothèque, personnalisation et export de sauvegarde.

**M4 — Fonctions différables sans refonte.** Carte musculaire réellement 3D avec rotation et zoom, calculs de volume musculaire par groupe, suggestions de progression, cardio spécialisé, partage coach via fichier/lien, synchronisation ou espace coach.

Les fonctionnalités déjà approuvées de M4 ne sont **pas abandonnées** : elles doivent être anticipées dans le modèle de données lorsque c'est raisonnable, sans construire une fausse fonctionnalité.

## 3. Choix techniques proposés

| Sujet | Proposition | Raison / précaution |
|---|---|---|
| Plateforme | React Native + Expo + TypeScript, iOS d'abord | Application mobile native distribuable sur iPhone ; évolution Android envisageable |
| Navigation | Expo Router | Parcours explicites et séparés de la logique métier |
| Stockage | SQLite local via `expo-sqlite` | Fiabilité hors ligne, requêtes historiques et migrations |
| État d'interface | React state / éventuellement Zustand | Garder la logique de séance indépendante des composants |
| Validation des entrées | Schémas TypeScript et contrôles à la saisie ; Zod facultatif | Empêcher les séries impossibles ou données incohérentes |
| Chronomètre | Horodatages persistés et recalcul sur reprise | Évite de dépendre d'un `setInterval` qui s'interrompt en arrière-plan |
| Alertes repos | Son / vibration locaux, suivant permissions iOS | Notification et comportement en arrière-plan à tester sur appareil |
| Tests | Unitaires pour calculs + tests de flux de séance | Empêcher les régressions de temps, tonnage et historique |
| Hébergement | Aucun en M0–M3 | Les coachs et la synchronisation en ligne viendront plus tard |

**Ne pas confondre** « connexion avec Apple », sauvegarde iCloud, compte application et stockage local : ce sont quatre mécanismes différents. Aucun n'est indispensable au premier prototype. Une suppression de l'app peut effacer les données locales ; prévoir ensuite une véritable stratégie d'export/sauvegarde avant une sortie publique.

Structure logique suggérée : `app/` routes, `src/features/programs/`, `workouts/`, `sessions/`, `history/`, `exercise-library/`, `settings/`, `src/db/` schémas et migrations, `src/domain/` calculs purs, `src/ui/` composants réutilisables, `tests/`.

## 4. Carte des 21 écrans validés

Les numéros identifient la **maquette**, pas nécessairement un itinéraire strict : plusieurs écrans sont des modales, variantes d'état ou vues ouvertes depuis un autre écran.

| N° | Écran | Fonction indispensable / état | Lot |
|---|---|---|---|
| 01 | Accueil | Résumé de progression, séance du moment, indicateur discret de navigation verticale ; état vide adapté | M0/M3 |
| 02 | Programmes Musculation | Liste locale de programmes créés, bouton « Créer un programme » ; pas d'onglet « Séances » redondant | M0 |
| 03 | Détail programme | Résumé et accès **explicite « Voir les séances »** ; visuel musculaire si disponible | M0 ; visuel M4 |
| 04 | Sélection de séance | Séances du programme choisi | M0 |
| 05 | Vue d'ensemble séance | Exercices prévus, bouton « Démarrer la séance » ; **pas de volume estimé** en en-tête | M1 |
| 06 | Une série active | Une série seulement, charge, répétitions, RIR, « Valider la série » | M1 |
| 07 | Repos normal | Cercle + pause au centre, deux blocs prévu/réel, CTA « Passer à la série suivante » | M1 |
| 08 | Repos dépassé | Cercle rouge/orange, temps réel continue, CTA « Repos terminé », animation discrète possible | M1 |
| 09 | Modifier une série | Champs **2 × 2** : charge, répétitions, RIR, repos ; choix « Cette séance » / « Programme » | M1 |
| 10 | Remplacer un exercice | Alternatives ; changement temporaire sans fusion d'historiques | M2 |
| 11 | Choisir un autre exercice | Grille illustrée des exercices **restants**, pour l'exécuter maintenant | M2 |
| 12 | Fin de séance | Durée totale, tonnage, séries réalisées, RIR moyen, accès détails | M2 |
| 13 | Historique général | Tonnage global, graphiques, filtres, entrées par programme | M3 |
| 14 | Historique programme | Performances et séances du programme sélectionné | M3 |
| 15 | Historique séance | Résumé aéré puis liste des exercices réellement faits | M3 |
| 16 | Historique exercice | Séries, graphiques, comparaison, **pas de colonne date dans le tableau compact** | M3 |
| 17 | Carte musculaire 3D | Mannequin réellement orientable, heatmap de volume, aide gestuelle affichée **une seule fois** | M4 |
| 18 | Zoom sur un muscle | Zoom animé depuis l'angle actuel ; **3 indicateurs sobres** : tonnage, séries, part du volume | M4 |
| 19 | Bibliothèque d'exercices | Recherche/filtres ; exercice référencé de façon stable | M1/M3 |
| 20 | Fiche exercice | Description, Conseils, Alternatives ; action de substitution en séance | M2/M3 |
| 21 | Paramètres / profil | Unités, affichage, sons, préférences ; pas de compte obligatoire | M0/M3 |

**Navigation verticale validée** : accueil → univers Musculation → univers Cardio via geste vertical, sans page de choix « Musculation ou Cardio ». Le libellé d'aide sur l'accueil reste à affiner ; prévoir aussi une alternative accessible au geste. Le cardio dédié peut afficher un état « à venir » tant qu'il n'est pas développé, sans simuler des données.

## 5. Premier lancement et création de programme

**VALIDÉ :** le premier lancement ne contient aucun programme utilisateur, aucune séance d'historique et aucune statistique inventée. Afficher une invitation claire à créer son programme (et plus tard à l'importer). La bibliothèque d'exercices peut comporter un catalogue initial ; elle est distincte des **programmes prêts à l'emploi**, exclus du lancement.

Parcours initial : `Accueil vide → Programmes → Créer programme → Ajouter séance → Ajouter exercice → Configurer les séries → Enregistrer → Vue d'ensemble → Démarrer`.

Champs du programme : identifiant stable, nom libre, discipline (`musculation` initialement), statut archivé/actif si nécessaire, date de création. Les séances peuvent porter un nom libre (« Push A », « Full body »). Les exercices sont ordonnés dans chaque séance.

Chaque **série prévue** peut définir indépendamment : ordre, étiquette libre et/ou numéro, type (échauffement, travail, top set, back-off ou personnalisé), répétitions min/max, RIR cible facultatif, charge cible facultative, repos **après cette série** en secondes (si intervalle applicable), notes ou consignes. Un nom n'implique pas automatiquement une logique de progression.

Le réglage par défaut est **manuel** : l'application aide à retrouver sa performance précédente, mais n'augmente pas la charge à la place de l'utilisateur. Si un utilisateur configure trois séries indépendantes, on suit trois séries indépendantes. Si un groupe back-off lié est programmé plus tard, la règle du groupe est distincte de celle du top set.

**Options conservées dans le modèle** : montée en gamme manuelle ou calculée en pourcentage, back-off à un pourcentage du top set, charge de référence planifiée ou constatée, possibilité de modifier la valeur calculée. Ne pas rendre le calcul automatique obligatoire. Arrondi aux incréments de disques et répartition des charges par haltère sont **à confirmer**.

## 6. Séance active : parcours d'exécution

1. L'utilisateur consulte la séance prévue (écran 05), puis démarre explicitement. Enregistrer `startedAt`.
2. Ouvrir l'écran 06 sur **la série suivante à effectuer**, une seule à l'écran. Montrer si possible la dernière performance comparable, sans envahir l'interface.
3. L'utilisateur saisit **charge réelle**, **répétitions réelles** et **RIR réel**, puis valide. Sauvegarder immédiatement le résultat ; conserver les valeurs prévues dans le template d'origine.
4. S'il existe un repos après cette série, ouvrir l'écran 07. Le repos programmé est propre à cet intervalle, pas un champ global imposé à l'exercice.
5. L'utilisateur contrôle le passage : avant expiration du repos, un bouton « Passer à la série suivante » ; après expiration, il se transforme en « Repos terminé ». Dans les deux cas, enregistrer le repos réel et passer à l'étape choisie.
6. Si l'exercice est terminé et qu'il reste d'autres exercices, poursuivre normalement vers le prochain ; l'utilisateur peut ouvrir la **grille des exercices restants** (écran 11) pour faire un autre exercice maintenant. L'exercice en attente n'est pas supprimé.
7. L'utilisateur peut aussi remplacer ponctuellement l'exercice (écran 10), ou éditer une série via une commande secondaire (écran 09). Toute substitution garde son propre identifiant d'exercice dans l'historique.
8. À la fin réelle de la séance, enregistrer `finishedAt`, afficher écran 12 et archiver la séance effectuée sans effacer ni réécrire les anciennes performances.

**Distinction essentielle :** le chemin par défaut garde l'ordre programmé ; la grille et le remplacement sont des **exceptions choisies** par l'utilisateur, jamais une étape imposée après chaque série.

**Édition en cours de séance** : choisir explicitement « Cette séance » (modifier seulement le déroulé courant) ou « Programme » (mettre à jour les prochaines séances). Une modification de programme ne doit jamais réécrire les événements historiques déjà enregistrés.

## 7. Chronomètre de repos : machine à états

Un repos est lié à une **transition entre séries** ; pour N séries successives d'un exercice, il y a normalement N−1 intervalles internes. Le repos entre deux exercices reste un choix produit **à confirmer**. La durée prévue est celle définie sur la série/transition concernée.

| État | Visuel | Temps affiché | Action principale |
|---|---|---|---|
| `RUNNING_BEFORE_TARGET` | Cercle vert/bleu | Temps restant avant l'objectif ; bloc « Repos réel » croissant | **Passer à la série suivante** |
| `RUNNING_OVERTIME` | Cercle rouge/orange, éventuelles étincelles | Dépassement +00:01, +00:02... ; repos réel continue | **Repos terminé** |
| `PAUSED` | Icône lecture au centre | Valeur figée selon sémantique de pause à confirmer | Reprendre puis terminer |
| `COMPLETED_EARLY` | Historique uniquement | Durée réelle strictement inférieure à durée prévue | Passage demandé avant cible |
| `COMPLETED` | Historique uniquement | Durée réelle et écart enregistrés | Passage demandé à/après cible |

**Invariant :** quand le compte à rebours atteint 0, l'app signale l'échéance (son/vibration selon préférences) mais **ne change pas d'écran**. Il n'existe pas de bouton « +15 s / +30 s ». Le **pause/play reste au centre du cercle**. Sous celui-ci, deux blocs bien visibles indiquent **repos prévu** et **repos réel**.

**Implémentation recommandée :** stocker l'heure de début, la cible, les intervalles de pause éventuels et l'heure de validation. Recalculer avec l'horloge réelle à chaque reprise d'app ; ne pas utiliser uniquement un décompte en mémoire. Attention : le moment précis qui marque la fin du repos est le clic utilisateur sur le bouton, non la sonnerie. Le bouton « Passer à la série suivante » ne signifie pas effacer le repos mesuré.

**À CONFIRMER** : quand l'utilisateur met manuellement en pause le minuteur, le « repos réel » doit-il continuer à mesurer le temps chronologique ou exclure les pauses ? Les deux notions peuvent être stockées séparément pour préserver l'information.

## 8. Modèle de données minimal recommandé

Clés UUID locales ; dates ISO horodatées ; migrations versionnées. Les modèles ci-dessous sont des **propositions de structure**, pas un schéma figé validé.

| Entité | Champs principaux | Rôle |
|---|---|---|
| `Program` | `id`, `name`, `sportType`, `createdAt`, `archivedAt?` | Organisation générale, propriété locale au début |
| `WorkoutTemplate` | `id`, `programId`, `name`, `sortOrder` | Une séance prévue dans un programme |
| `ExerciseCatalogItem` | `id`, `name`, `muscleTags`, `equipment`, `instructions?` | Catalogue distinct des programmes utilisateur |
| `WorkoutExercise` | `id`, `workoutTemplateId`, `exerciseId`, `sortOrder`, `notes?` | Exercice prévu et sa position |
| `SetTemplate` | `id`, `workoutExerciseId`, `sortOrder`, `label?`, `kind?`, `repsMin?`, `repsMax?`, `targetRir?`, `targetWeightKg?`, `restAfterSec?`, `progressionGroupId?`, `percentRule?` | Paramètres par série, charge et RIR facultatifs |
| `WorkoutSession` | `id`, `workoutTemplateId`, `startedAt`, `finishedAt?`, `status`, `durationSec?` | Séance réellement commencée, terminée ou interrompue |
| `SessionExercise` | `id`, `workoutSessionId`, `sourceWorkoutExerciseId?`, `performedExerciseId`, `performedOrder`, `replacedFromExerciseId?` | Exercice réellement fait, y compris substitution |
| `PerformedSet` | `id`, `sessionExerciseId`, `sourceSetTemplateId?`, `performedOrder`, `weightKg?`, `reps`, `rir?`, `completedAt`, `notes?` | Performance constatée, jamais écrasée par le programme |
| `RestInterval` | `id`, `workoutSessionId`, `afterPerformedSetId`, `beforePerformedSetId?`, `plannedSec`, `startedAt`, `endedAt?`, `pausedSec?`, `outcome` | Repos prévu/réel et qualification de l'écart |
| `AppPreference` | `key`, `value` | Unités, son, aide 3D vue une fois, labels des séries |

**Principes d'intégrité :** conserver les identifiants des exercices, même en cas de renommage ; ne pas confondre ordre prévu et ordre réellement exécuté ; ne pas supprimer d'historique lorsqu'un coach modifiera un programme ; stockage des durées en **secondes** et des charges dans une unité canonique interne avant affichage. Conserver la notion de provenance du programme pour un futur coach (sans compte coach à ce stade).

**Persistances indispensables :** création/édition de programmes, toutes les validations de séries, état du minuteur, ordre et exercices effectivement réalisés, séance en cours et reprise après fermeture. Faire des migrations non destructrices dès le départ.

## 9. Calculs, historique et pédagogie

**Tonnage d'une série chargée (règle simple initiale) :** `charge enregistrée × répétitions réalisées`. Tonnage d'exercice/séance : somme des séries pertinentes. Le choix d'inclure échauffements, poids de corps, charges par haltère ou machines sera explicité avant statistiques avancées ; ne pas afficher une précision trompeuse. Le **volume musculaire attribué par muscle** est une estimation distincte du tonnage brut d'un exercice.

**Durée totale d'une séance :** différence entre horodatage de démarrage et horodatage de fin, avec une politique d'interruption à définir. Afficher à la fin et dans l'historique/graphiques. Ne pas inventer des durées estimées comme si elles étaient réalisées.

**RIR :** une cible programmée est différente du RIR réellement saisi. Afficher ces informations séparément lorsque pertinent. « RIR 0 » ne déclenche aucune recommandation obligatoire.

**Progression en mode manuel :** expliquer la double progression (exemple pédagogique 8–12 reps : conserver la charge pendant la progression en répétitions et envisager une hausse après avoir atteint le haut de plage selon la règle choisie). Les séries peuvent être indépendantes ou liées en groupe ; le top set peut progresser séparément des back-offs. L'aide à augmenter les charges demeure **optionnelle**, différée à M4.

**Historique à niveaux :** écran 13 = tonnage global, un à trois graphiques et entrées par programmes ; écran 14 = historique du programme ; écran 15 = séance ; écran 16 = exercice. Dans le tableau compact de l'écran 16, ne pas afficher de colonne date ; conserver les horodatages en base pour un éventuel calendrier accessible ailleurs.

**Carte musculaire M4 :** volume planifié et volume réellement exécuté sont distincts. Colorer les régions d'une **vraie géométrie 3D orientable**. Afficher l'indication « Faire glisser pour pivoter » uniquement lors de la première visite (préférence persistée). Au tap sur un muscle : animation de caméra qui zoome depuis **l'angle actuellement affiché**, puis 3 petites cartes « Tonnage », « Nombre de séries », « Part du volume ». Aucun tableau d'exercices envahissant dans cette vue zoomée. Définir auparavant la répartition polyarticulaire / muscles secondaires ; ce n'est pas une mesure directe de « fibres activées ».

## 10. États vides, erreurs et protection des données

- **Premier lancement :** pas de programme précréé, pas de données fictives, une action « Créer mon premier programme » ; accès à la bibliothèque pour choisir les exercices.
- **Pas d'historique :** cartes sobres expliquant que les graphiques apparaîtront après les premières séances ; aucune fausse statistique « +12 % ».
- **Saisie invalide :** contrôler les champs numériques (répétitions entières ≥ 0, charge non négative et unités définies, RIR cohérent). Demander confirmation avant suppression de données importantes.
- **App fermée / appel entrant :** reprendre la séance en cours sans perte ; recalculer les temps sur reprise.
- **Modifications de programme :** ne pas modifier rétroactivement les séances enregistrées.
- **Suppression/export :** sauvegardes exportables à prévoir avant lancement public ; spécifier la restauration et les migrations.
- **Vie privée :** éviter l'envoi de données de santé/entraînement à des services tiers par défaut ; documenter les permissions si des notifications sont ajoutées.

## 11. Critères d'acceptation prioritaires pour Codex

**AC-01 — Installation et première ouverture.** Étant donné une installation neuve, quand j'ouvre l'application, alors je ne vois **aucun programme fictif**, je peux créer un programme, et l'app fonctionne hors ligne.

**AC-02 — Configuration fine.** Étant donné une séance, quand j'ajoute trois séries, alors chacune possède ses propres répétitions cibles, RIR facultatif et repos éventuel ; les noms des séries peuvent être libres.

**AC-03 — Charge facultative.** Étant donné un exercice non planifié en charge, quand je commence, alors aucune charge cible n'est imposée, mais je peux saisir ma charge réelle.

**AC-04 — Série unique.** Étant donné une séance active, quand j'arrive à l'exercice, alors **une seule série** est affichée et le bouton principal permet de la valider.

**AC-05 — Repos normal.** Quand je valide une série assortie d'un repos de 120 s, alors le minuteur démarre, le bloc repos réel croît, le bloc prévu reste 2:00 et le bouton « Passer à la série suivante » est disponible.

**AC-06 — Repos dépassé.** Si 120 s s'écoulent sans validation, alors j'entends/ressens l'alerte selon réglages, le chrono passe en dépassement rouge et l'écran **reste ouvert** ; le bouton affiche « Repos terminé ».

**AC-07 — Validation du repos.** Quand je termine tôt à 70 s ou tard à 155 s, alors la durée réellement écoulée est enregistrée ; il n'y a **pas de +15 s** ni de passage automatique.

**AC-08 — Continuité.** Si l'app est fermée pendant une séance, à la réouverture j'ai les résultats déjà saisis et l'état de la séance ; le minuteur est recalculé correctement.

**AC-09 — Substitution.** Si je remplace le développé couché barre par haltères pour cette séance, l'historique distingue bien les deux exercices, et le modèle original reste disponible au prochain entraînement.

**AC-10 — Ordre exceptionnel.** Si je sélectionne un exercice plus loin via une grille, les autres exercices non réalisés restent accessibles ; le programme ne change pas par défaut.

**AC-11 — Modifications.** Si je modifie la séance en cours, cela ne réécrit pas l'historique. Si je choisis « Programme », seules les séances futures héritent de la modification.

**AC-12 — Bilan et historique.** À la fin, la durée totale est conservée ; les graphiques ne se basent que sur les performances réellement enregistrées, et l'accès hiérarchique général → programme → séance → exercice est respecté.

**AC-13 — Carte 3D, lot ultérieur.** Le mannequin tourne réellement en réponse au geste et zoome sur le muscle touché depuis l'angle actuel ; l'aide gestuelle disparaît définitivement après le premier affichage ; seules trois statistiques compactes figurent au bas de l'écran zoomé.

## 12. Points à trancher avant certains développements

| ID | Question | Décision momentanée pour ne pas bloquer |
|---|---|---|
| Q-01 | Repos entre **deux exercices distincts** : transition automatique, réglage explicite, ou aucune ? | Repos seulement lorsqu'un `restAfterSec` est défini |
| Q-02 | Pause du timer : mesure du repos réel inclut-elle le temps « en pause » ? | Conserver temps écoulé brut + temps mis en pause séparément |
| Q-03 | Poids des haltères : par main ou charge totale ? Et poids de corps / machines ? | Documenter l'unité au niveau de l'exercice ; ne pas supposer |
| Q-04 | Tonnage : échauffements inclus ou exclus par défaut ? | Stocker le type de série ; calcul paramétrable ultérieurement |
| Q-05 | Valeur de RIR non renseignée : obligatoire à la validation ? | Champ facultatif dans le schéma, comportement UI à confirmer |
| Q-06 | Raccourci de navigation vers Cardio depuis l'accueil, accessible sans swipe ? | Prévoir un indicateur discret ; design non figé |
| Q-07 | Alertes lorsque l'app est en arrière-plan et le téléphone verrouillé ? | Tester la solution iOS avant promesse d'alerte exacte |
| Q-08 | Séance mise en pause / interrompue : durée inclut-elle toutes les interruptions ? | Stocker des horodatages bruts ; règle à définir avant publication |
| Q-09 | Attribution du volume par muscle : coefficients primaires/secondaires ? | Ne pas calculer de carte 3D « précise » avant validation du modèle |
| Q-10 | Sauvegarde et changement d'iPhone, export/restauration ? | Architecture locale ; définir une solution avant App Store |

## 13. Consignes d'exécution pour Codex

1. **Commencer par lire ce document**, les 21 maquettes et le cahier des charges fonctionnel ; ne pas inférer des données fictives depuis les captures.
2. **Proposer un plan de fichiers et de tests** avant d'ajouter des dépendances. Pas de code volumineux sans validation.
3. **Livrer un seul jalon à la fois** : d'abord M0, puis un petit parcours bout en bout de M1.
4. **En cas d'ambiguïté**, noter la question dans une liste plutôt que d'inventer une règle produit.
5. **Conserver les décisions de l'utilisateur** : première ouverture vide, pas de compte, progressions manuelles, une série active, repos manuel.
6. **Tester avant de déclarer terminé** : exécuter les tests, vérifier la compilation TypeScript et détailler ce qui a été essayé sur simulateur/appareil.
7. **Expliquer en langage non technique** les prochaines actions du créateur de l'application (commandes à copier, boutons à cliquer, erreurs et solutions possibles).

### Première livraison demandée

**Construire seulement M0** : squelette de l'application, thème sombre et navigation, persistance SQLite et migrations, écran de liste de programmes réellement vide avec action de création, création d'un programme et d'une séance, tests élémentaires. Ne pas créer de compte, programme prédéfini, graphique fictif, faux mannequin 3D ou synchronisation. À la fin, expliquer comment démarrer l'application dans Expo Go ou un simulateur iOS, et quelles limites impliquent un iPhone/compte développeur Apple.

---

**Traçabilité.** Les décisions fonctionnelles proviennent des documents de référence F-001–F-066 et des corrections ultérieures validées pendant la revue des maquettes. Les choix d'outils, les noms de tables et les lots sont des **propositions d'implémentation** à confirmer, pas des décisions produit déjà approuvées.
