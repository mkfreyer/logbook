# Navigation M3.2 rétablie dans M3.3

À la demande du propriétaire, les changements de swipe des commits `262a844` et `86c5119` sont retirés par un **nouveau commit ciblé sur `feat/m3-parametres-stabilisation`**. La PR #7 reste en brouillon, sans fusion. Aucune nouvelle animation proposée et aucun début de M3.4.

## État livré

- `src/navigation/UniversePager.tsx` et `app/index.tsx` sont **identiques au commit M3.2 `289cad0`**, octet pour octet. `UniverseScreen.tsx`, `UniverseContext.tsx` et `physics.ts` étaient déjà identiques et restent inchangés.
- Les reçus de sélection, les diagnostics ajoutés avec eux et la compensation de présentation sont retirés. `src/navigation/presentation.ts` est supprimé ; aucun code applicatif ne référence ce mécanisme.
- Le ruban de pages complètes, l’animation, les règles de bord de liste et les boutons retrouvent le fonctionnement M3.2. Le bloc inférieur de l’accueil retrouve `marginTop: 'auto'`.
- L’accueil correspond à celui de la première livraison M3.3 `3586bca` : organisation M3.2 et engrenage Paramètres conservé. Le bouton Paramètres de Musculation reste aussi présent.
- Le Switch sonore validé sur iPhone est conservé à l’identique : réponse visuelle immédiate, sauvegardes ordonnées, persistance et gestion des erreurs. L’écran Paramètres, le provider de préférences et l’export JSON ne sont pas modifiés.

Le dépôt reste sur la branche M3.3 actuelle. **Pas de retour de branche, pas de `git reset --hard`, pas de réécriture d’historique ni de push forcé.** Les anciens commits restent visibles dans l’historique Git.

## Données et fonctionnalités préservées

**SQLite reste v5, sans migration ni réinitialisation.** Même identité Expo et même `logbook.db`. Programmes, séances, performances, historiques, préférences, repos et pauses restent conservés. Aucun code du chronomètre ou de ses calculs n’est modifié. Aucune dépendance ajoutée ou retirée.

Le retour de code concerne uniquement la navigation et la présentation de l’accueil. **Ne pas ouvrir une ancienne branche M3.2 avec ce carnet v5** : elle ne connaît pas ce schéma et le refuserait. Pour tester cette restauration, conserver la branche M3.3 et l’installation Expo Go actuelle.

L’export personnel reste complet et fonctionnel ; la restauration des données JSON n’est toujours pas implémentée. Cette restauration de navigation ne constitue pas une restauration de base de données.

## Vérifications

La comparaison Git confirme l’identité des fichiers de navigation avec `289cad0` et celle de l’accueil avec `3586bca`. Elle confirme aussi l’absence de changement dans les fichiers SQLite, export, préférences, Paramètres, entraînement et chronomètre par rapport à la version précédente.

Les tests du pager M3.2 sont rétablis. Les tests des reçus/compensations retirés sont remplacés par des vérifications du comportement demandé : déplacement commun des deux pages, absence de transformation individuelle, retour de route d’origine et sélection avec un seul identifiant. Des tests vérifient la marge automatique de l’accueil et les deux accès Paramètres.

Toutes les vérifications du Switch corrigé, de la préférence persistante, des erreurs, de l’export et des parcours M0–M3.3 restent exécutées. Les tests, TypeScript, export JavaScript iOS et CI complètent ces comparaisons ; ils ne remplacent pas une nouvelle manipulation sur iPhone.

Résultats locaux : **326 tests réussis** (124 SQLite/domaines, 13 navigation, 189 composants), TypeScript et export JavaScript iOS. Les **17 tests du pager** passent également avec le diagnostic M3.2 activé. Les quatre nouveaux contrôles vérifient le déplacement commun des pages, le contrat de navigation d’origine, les accès Paramètres et la marge automatique de l’accueil. Les neuf tests propres aux mécanismes de swipe retirés ne sont plus applicables.

## Installation Windows PowerShell

Après **Ctrl+C** pour arrêter Metro, dans votre dossier `logbook` :

```powershell
git fetch origin
git switch feat/m3-parametres-stabilisation
git pull --ff-only origin feat/m3-parametres-stabilisation
npm.cmd ci
Remove-Item Env:EXPO_PUBLIC_GESTURE_DEBUG -ErrorAction SilentlyContinue
npm.cmd start -- --clear
```

Scanner le nouveau QR code avec l’iPhone sur le même Wi-Fi, dans le même projet Expo Go. `--clear` efface le cache Metro, pas vos données SQLite. **Ne pas désinstaller Expo Go ni effacer son stockage.**

## Essais iPhone

1. Retrouver l’organisation de l’accueil et le déplacement des deux pages que vous aviez validés en M3.2. Faire un aller-retour lent, un geste court annulé et quelques allers-retours rapides, puis essayer les boutons Musculation et Accueil.
2. Faire défiler la liste des programmes : depuis son milieu, le geste descendant doit défiler la liste ; depuis son haut, un nouveau geste doit permettre de revenir à l’accueil.
3. Ouvrir Paramètres depuis l’engrenage de l’accueil puis depuis Musculation. Basculer rapidement le son, conserver un dernier choix, quitter/revenir et fermer/réouvrir le projet pour vérifier sa persistance.
4. Exporter dans Fichiers, puis essayer l’annulation de la feuille native. Retrouver les programmes et historiques existants, puis reprendre un entraînement et vérifier le repos. Aucune suppression de données nécessaire pour ces contrôles.

Le [guide général M3.3](TESTER_M3_3_SUR_IPHONE.md) reste applicable aux paramètres et à l’export. Les anciennes présentations expérimentales de swipe sont abandonnées. **Attendre le retour du propriétaire avant M3.4.**
