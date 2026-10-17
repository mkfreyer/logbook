# Tester M3.4C sur iPhone avec Expo Go

M0 à M3.4B (dont Passer/Réintégrer) sont validés par le propriétaire. **M3.4C doit encore être vérifié sur votre iPhone.** La base reste SQLite **v8**, sans nouvelle migration ; données, identité Expo et fichier `logbook.db` sont conservés.

## Récupérer le code sur Windows

Arrêtez Expo avec **Ctrl+C**, puis ouvrez PowerShell dans votre dossier `logbook` :

```powershell
git fetch origin
git switch feat/m34c-fiches-exercices
git pull --ff-only origin feat/m34c-fiches-exercices
npm.cmd ci
npm.cmd start -- --clear
```

Si la branche n’existe pas encore localement, remplacez la ligne `git switch` par :

```powershell
git switch --track origin/feat/m34c-fiches-exercices
```

Scannez le nouveau QR code avec l’iPhone sur le même Wi-Fi. Ne désinstallez pas Expo Go et n’effacez pas son stockage. `--clear` nettoie le cache JavaScript du serveur, pas votre base personnelle. Si Git signale des modifications locales, conservez-les avant de changer de branche ; ne forcez pas l’opération.

## 1. Fiches et bibliothèque

1. Musculation → Bibliothèque d’exercices. Recherchez `developpe incline` sans accent, puis ouvrez sa fiche.
2. Touchez **Description**, **Conseils**, **Alternatives**. Vérifiez la lisibilité, la sélection de l’onglet, les consignes, les étapes et l’explication « par haltère ».
3. Sur le couché barre, ouvrez l’alternative incliné haltères. La différence est annoncée ; aucun remplacement n’a lieu dans la bibliothèque générale.
4. Revenez en arrière : la fiche précédente et son onglet doivent être retrouvés. Essayez un texte agrandi dans iOS et vérifiez les retours sur un petit écran.
5. Consultez Tractions → Tirage vertical, Squat → Presse et une fiche sans alternative connue (par exemple Curl haltères). Aucune fausse proposition n’est attendue.
6. Ouvrez votre exercice personnalisé : aucune explication spécifique inventée. Modifiez ses consignes, enregistrez, revenez et vérifiez leur présence. Son historique et son identifiant restent les mêmes.
7. Depuis la préparation d’un programme, ouvrez la fiche avec l’icône d’information ou **Fiche de l’exercice**. Aucun remplacement d’entraînement ne doit être proposé et aucun exercice ne doit être ajouté par cette consultation.

Après ouverture de Logbook, coupez le Wi-Fi et les données mobiles temporairement : les fiches, consignes, alternatives et recherches restent utilisables. Rétablissez le réseau pour recharger le projet depuis le serveur Expo si nécessaire.

## 2. Aide et entraînement simple

1. Dans une configuration de série, dépliez **Comprendre les termes d’entraînement** puis refermez. Vérifiez cible/réel, RIR, types, unités, passage/suppression.
2. Démarrez une séance avec plusieurs séries. Pendant l’effort, une seule série reste active et ses trois champs réels restent vides avant votre saisie.
3. Ouvrez l’aide sous les champs, puis le menu « … » → **Fiche et conseils de l’exercice**. Consultez les onglets et revenez. La consultation ne valide aucune série et ne change aucun objectif.
4. Vérifiez que **Terminer**, **Terminer la configuration**, **Quitter et reprendre plus tard**, Passer et Réintégrer restent opérationnels.

## 3. Remplacement temporaire depuis une alternative

Utilisez une séance de votre choix avec au moins quatre séries sur le couché barre et un repos positif entre séries, sans créer de performances dans vos véritables historiques si vous ne souhaitez pas y garder cet essai.

1. Passez la première série. Réalisez et validez la suivante avec vos vraies valeurs. Testez pause/reprise et fin manuelle du repos.
2. Sur la prochaine série active, menu « … » → **Fiche et conseils de l’exercice** → Alternatives → incliné haltères.
3. Touchez **Remplacer pour cette séance**. Vérifiez que la confirmation nomme les deux exercices, annonce les charges cibles effacées et le programme inchangé. **Annuler** ne doit rien changer.
4. Recommencez et confirmez. Vous revenez à l’entraînement : les séries restantes admissibles utilisent le vrai nom et le mode par haltère, avec une charge cible à adapter. Les règles de pourcentage liées sont suspendues, jamais transposées entre deux modes.
5. La série validée reste sur le couché barre avec ses résultats. La série passée reste passée sur l’exercice initial. Réintégrez-la si vous souhaitez la réaliser : elle doit garder son identité d’origine.
6. Vérifiez le même accès depuis **Remplacer cet exercice**, avec l’icône d’information d’une ligne. La recherche inclut toujours vos exercices personnalisés ; toucher cette icône consulte seulement la fiche.
7. Quittez temporairement et fermez Expo Go, puis rouvrez le même projet. Reprenez : identités, résultats, séries restantes et passées doivent être conservés.
8. Terminez réellement la séance si souhaité. Le bilan et l’historique doivent séparer les vrais noms et modes utilisés. Revenez à la préparation : l’exercice d’origine n’a pas changé.

## 4. Protections et erreurs

- Ouvrir une fiche pendant un contexte ancien/terminé ou un repos ne doit pas permettre de remplacer la série ; l’explication propose **Revenir à la séance**. Un repos n’est jamais terminé par une simple consultation.
- Répétez rapidement les appuis sur le remplacement et la confirmation : une seule substitution doit être enregistrée.
- Après annulation ou retour arrière, aucune substitution ne doit apparaître.
- Vérifiez les retours dans les fiches : un rafraîchissement ordinaire conserve les données déjà lues et l’onglet, sans roue qui remplace tout le contenu.

## 5. Non-régression

- Swipes Accueil ↔ Musculation, boutons de navigation, chargements silencieux.
- Son de fin de repos et Switch dans Paramètres ; pause, dépassement et passage manuel.
- Ajout de série, cibles calculées prévues/réelles, notes et choix du prochain exercice.
- Historiques, graphiques, bilans et statistiques de l’accueil.
- Exporter mes données → Fichiers : JSON format 1 / SQLite 8, avec les consignes personnalisées, références et remplacements. Les textes éditoriaux sont embarqués avec l’app. **La restauration JSON n’existe toujours pas.**

Les tests Linux et l’export iOS ne démontrent pas la fluidité native. Envoyez les étapes et l’écran concernés si un comportement diffère. Aucun jalon suivant ne sera entamé avant votre validation.
