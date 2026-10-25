# Logbook — prototype M4B sur Expo SDK 58

Application iPhone de musculation en React Native, Expo SDK 58, TypeScript, Expo Router et SQLite local. M0 à M3.4C, y compris Passer/Réintégrer, ont été validés sur un véritable iPhone avant cette migration. **La version SDK 58 attend un nouveau test sur appareil.** La branche **`feat/m34c-fiches-exercices`**, basée sur M3.4B `e701785`, ajoute les fiches **Description / Conseils / Alternatives**, des repères hors ligne pour les 15 exercices et une aide facultative. Le remplacement depuis une alternative utilise le parcours existant et sa confirmation, uniquement pour l’entraînement actif. La fiche s’ouvre désormais en touchant directement l’encadré bleu de l’exercice actif ; le menu garde les autres actions. **Cet ajustement d’accès direct attend la validation iPhone.** [Vérification rapide](docs/TESTER_ACCES_DIRECT_FICHE_SUR_IPHONE.md).

Aucune migration supplémentaire : SQLite reste **v8**, export personnel format 1 / 20 tables. Les consignes personnelles restent enregistrées ; les nouveaux textes éditoriaux sont inclus avec l’app. [Décisions M3.4C](docs/M3.4C.md) · [Guide de test iPhone](docs/TESTER_M3_4C_SUR_IPHONE.md).

Vous pouvez configurer vos programmes, exercices et séries, puis démarrer un entraînement. Une seule série est affichée pendant l’effort. Les résultats saisis sont sauvegardés à chaque validation, séparément des objectifs. Le repos circulaire utilise la durée propre à la série ; il peut être mis en pause ou terminé tôt, et continue en dépassement sans passer automatiquement à la suivante.

La séance et les horodatages du repos sont conservés après fermeture. Une carte sur l’accueil et dans Musculation permet de reprendre. **Terminer** et **Terminer la configuration** sortent de la préparation ; **Terminer la séance** clôt un entraînement réellement effectué.

Le menu « … » permet maintenant de remplacer temporairement l’exercice actif ou de choisir un exercice restant. Les programmes ne changent pas. Un remplacement partiel conserve les performances déjà validées sur leur exercice initial et efface les charges cibles des séries restantes, après confirmation. Un choix pendant le repos le conserve jusqu’à sa fin manuelle.

Après la fin, le bilan présente durée chronologique, séries réalisées, tonnage enregistré, RIR moyen et exercices réellement utilisés. **Historique des entraînements**, dans Musculation, permet de rouvrir ce même bilan sauvegardé, même après suppression de son programme.

M3.1 ajoute le parcours historique général → programme → séance réelle → exercice, les périodes locales et des graphiques tactiles sobres. Les performances restent en lecture seule, les modes de charge d’un exercice sont séparés, et les dates sont regroupées au-dessus des tableaux compacts de séries. Les listes sont paginées ; les graphiques affichent au plus les 120 dernières séances filtrées, sans limiter les totaux.

M3.2 ajoute une carte **Dernière fois** sous les champs de la série active : résultats antérieurs du même exercice et mode, type/position privilégiés, sans remplir les résultats actuels. L’accueil compte les séances terminées dans la semaine locale lundi–dimanche. **Vos courbes** ouvre les graphiques sans inventer de progrès. La bibliothèque générale donne accès aux fiches et aux modifications de vos exercices personnalisés, avec leurs identifiants conservés.

M3.3 ajoute **Paramètres**, accessible depuis l’engrenage de l’accueil et Musculation. Le son de fin de repos peut être coupé ou activé, avec préférence persistante et respect du mode silencieux iOS. Les charges restent en kilogrammes. **Exporter mes données** prépare un JSON personnel complet et cohérent, puis permet de l’enregistrer dans Fichiers par la feuille native. Aucun envoi automatique. **La restauration n’est pas encore disponible** : conserver les données actuelles, même après export. Un import sécurisé reste obligatoire avant publication V1.

M3.4A ajoute des suggestions de noms, une préférence numéro/nom et des charges facultatives en pourcentage pour échauffements et back-offs. La référence planifiée est choisie explicitement dans le même exercice ; les calculs sont capturés au démarrage, sans préremplir les résultats réels. Le mode manuel reste disponible. Voir [les règles, la migration v6 et les limites](docs/M3.4A.md).

M3.4B ajoute les séries imprévues, l’édition des séries restantes avec portée explicite, les pourcentages fondés sur une charge réellement validée et les notes personnelles. Les captures initiales et performances sont protégées ; les ajustements sont conservés à part. Le repos en cours ne change pas lorsqu’on ajoute une série. Voir [architecture et migration v7](docs/M3.4B.md).

Le complément M3.4B permet de **Passer cette série**, prévue ou ajoutée, puis **Réintégrer la série** avant clôture. Le programme reste inchangé ; les statuts persistent, les repos restent manuels et les statistiques comptent seulement les performances réelles. Le bilan distingue les séries passées. Voir [fonctionnement, protections et schéma v8](docs/PASSAGE_SERIES_M3.4B.md).

Le premier lancement ne contient aucun programme ni performance fictive. La bibliothèque d’exercices est distincte des programmes utilisateur. Aucun compte ni serveur n’est nécessaire.

## Tester sur iPhone depuis Windows

Suivre le [guide M4B SDK 58](docs/M4B_SDK58_IPHONE_WINDOWS.md), avec Node.js 24,
Git et Expo Go SDK 58. Arrêter l’ancien Metro avec **Ctrl+C**, ouvrir PowerShell
dans `logbook`, puis :

```powershell
git fetch origin
git switch feat/m4b-migration-expo-sdk58
git pull --ff-only origin feat/m4b-migration-expo-sdk58
npm.cmd ci
npm.cmd run viewer:check
npx.cmd expo start --go --lan
```

Scanner le nouveau QR code avec l’iPhone, sur le même Wi-Fi. Dans Musculation,
ouvrir **Mannequin 3D · Aperçu**. Conserver les données du même projet Expo Go.
**Ne pas désinstaller Expo Go ni effacer son stockage.**
Voir [le rapport de migration et ses limites](docs/M4B_SDK58_MIGRATION.md).

## Vérifications

```powershell
npm.cmd run typecheck
npm.cmd test
npm.cmd run export:ios
```

Les tests couvrent les migrations M0 à M3.4B, la persistance SQLite, les configurations, entraînements, remplacements, choix d’ordre, calculs du bilan, historiques filtrés, identités, comparaisons de séries, semaines locales, graphiques, fiches, préférences et export personnel, erreurs et doubles validations. L’export de plusieurs années est testé par lots et sous écritures concurrentes. La CI vérifie aussi la navigation verticale. L’export iOS produit le JavaScript et les ressources, sans compiler une application native installable. Les sons, la feuille Fichiers, les interactions tactiles et la reprise doivent être testés sur iPhone.

## Données et limites

La livraison M3.4B initiale utilisait le schéma v7. Ce complément passe SQLite de **v7 à v8**, au même fichier `logbook.db`, en ajoutant uniquement un journal des passages/réintégrations et ses protections. Les anciennes lignes, objectifs initiaux, performances, repos, notes et préférences sont conservés. **Les anciennes branches au schéma v7 ou inférieur refusent une base v8** ; rester sur ce correctif ou une version ultérieure. Faire un Reload complet du projet après installation. Voir [la migration détaillée](docs/PASSAGE_SERIES_M3.4B.md).

Le décompte exclut les pauses manuelles ; **Repos réel** inclut tout le temps chronologique. L’arrière-plan ne met pas automatiquement en pause. Le son est une alerte locale au premier plan, soumise au volume et au mode silencieux ; aucune notification écran verrouillé n’est promise dans Expo Go.

Le tonnage est la somme **charge saisie × répétitions réalisées**, échauffements inclus. Une charge par haltère est comptée une fois, sans inventer le nombre de mains utilisées. Le poids corporel n’est pas estimé et les charges absentes sont exclues. Le RIR moyen exclut les valeurs absentes, tout en comptant un RIR explicitement saisi à zéro.

L’export JSON n’est pas chiffré et **n’est pas encore réimportable** par Logbook. Les données nécessaires à une restauration future sont incluses ; la restauration transactionnelle, validée sur appareil et avec récupération après échec, reste une [tâche V1 obligatoire](docs/RESTAURATION_V1.md). Les fiches pédagogiques M3.4C attendent la validation iPhone de ce lot. Cardio, mannequin 3D, synchronisation et refonte visuelle globale restent hors de M3.3 ; les fonctionnalités coach sont réservées à la V2.

Les PR #2 → #3 → #4 → #5 → #6 → #7 (M3.3) → #8 (M3.4A) → M3.4B restent empilées ; aucune fusion sans accord. La PR M3.4B cible `feat/m34a-series-avancees`. La PR M3.4A cible `feat/m3-parametres-stabilisation`. La PR M3.3 cible `feat/m3-performances-accueil` tant que ses parents ne sont pas fusionnés.

- [Passages et réintégrations M3.4B](docs/PASSAGE_SERIES_M3.4B.md)
- [Guide iPhone des séries passées](docs/TESTER_PASSAGE_SERIES_SUR_IPHONE.md)
- [Architecture et décisions M3.4B](docs/M3.4B.md)
- [Guide de test iPhone M3.4B](docs/TESTER_M3_4B_SUR_IPHONE.md)
- [Architecture et calculs M3.4A](docs/M3.4A.md)
- [Guide de test iPhone M3.4A](docs/TESTER_M3_4A_SUR_IPHONE.md)
- [Architecture, migration et stabilisation M3.3](docs/M3.3.md)
- [Guide de test M3.3](docs/TESTER_M3_3_SUR_IPHONE.md)
- [Format de l’export personnel](docs/FORMAT_EXPORT_PERSONNEL.md)
- [Restauration à livrer avant la publication V1](docs/RESTAURATION_V1.md)
- [Architecture et règles de comparaison M3.2](docs/M3.2.md)
- [Guide de test M3.2](docs/TESTER_M3_2_SUR_IPHONE.md)
- [Architecture, calculs et limites M3.1](docs/M3.1.md)
- [Guide de test M3.1](docs/TESTER_M3_1_SUR_IPHONE.md)
- [Finition visuelle future](docs/DESIGN_BACKLOG.md)
- [Architecture et conventions M2](docs/M2.md)
- [Guide de test M2](docs/TESTER_M2_SUR_IPHONE.md)
- [Référence M1.2](docs/M1.2.md)
- [Spécification](SPECIFICATION_CODEX%20.md)
- [Maquette](docs/design/Maquette%20d’application%20fitness%20complète%20en%2021%20écrans.png)
- [Référence M1.1](docs/M1.1.md)
- [Référence M0](docs/M0.md)
