# M3.3 — Correctifs d’animation après test iPhone

Les fonctionnalités testées de M3.3, y compris Paramètres et l’export personnel, fonctionnent sur l’iPhone du propriétaire. Cette correction reste sur `feat/m3-parametres-stabilisation`, dans la **PR #7 en brouillon**, sans fusion ni début de M3.4. Les deux animations doivent être réessayées sur l’appareil.

Retour suivant : le Switch est confirmé corrigé sur iPhone ; le retour Musculation → Accueil nécessite encore un ajustement de **composition**. La correction ultérieure et ses essais sont décrits dans [RETOUR_ACCUEIL_M3_3.md](RETOUR_ACCUEIL_M3_3.md). Le scénario de route ci-dessous n’est pas supposé expliquer ce nouvel effet de disposition.

## Switch : causes établies dans le code

Le Switch devenait `disabled` pendant chaque écriture SQLite. Sur iOS, React Native transmet ce changement à `UISwitch.enabled` ; sa documentation précise que le contrôle désactivé est translucide. En parallèle, sa valeur contrôlée React restait ancienne jusqu’au retour de SQLite. `Switch.js` compare cette valeur au nouvel état natif et peut rappeler `setValue` pour annuler l’état natif non acquitté. Cela oppose une remise à l’ancienne valeur au mouvement déjà engagé par UIKit. Enfin, remplacer l’aide par « Enregistrement… » pouvait changer la hauteur du texte et déplacer le contrôle.

Ces mécanismes sont vérifiables dans les sources React Native **installées dans la version du projet**, notamment `Libraries/Components/Switch/Switch.js` et `React/Fabric/Mounting/ComponentViews/Switch/RCTSwitchComponentView.mm`. Un test avec une écriture volontairement retardée échouait avant la correction : le Switch affichait encore `true` juste après une demande `false`.

La teinte exacte du contour bleu et les images de superposition ne peuvent pas être attribuées à un rendu UIKit précis sans l’enregistrement : les vidéos ne sont pas jointes à cette demande. Le correctif retire les conflits établis, sans remplacer le Switch par une animation maison.

## Switch : correction et garanties

- Valeur visible acquittée immédiatement dans le même événement natif. Pas de désactivation pendant les écritures ordinaires, pas de texte temporaire « Enregistrement… ». Le fond iOS du contrôle est explicitement accordé à sa piste éteinte ; le pouce conserve son apparence native.
- Chaque nouvelle intention est envoyée à la file d’écritures existante du repository. Une seule écriture SQLite s’exécute à la fois ; les appuis alternés ne sont plus abandonnés par un verrou d’interface. Un doublon de la même intention n’ajoute pas d’écriture.
- Les réponses anciennes ne repeignent pas la valeur visible. La dernière réponse termine l’état interne d’enregistrement ; le son reste coupé tant qu’une intention n’est pas confirmée.
- Un échec ancien n’annule pas une intention plus récente en attente, qui doit encore être sauvegardée. Si la dernière demande échoue, retour à la **dernière valeur réellement confirmée**, erreur visible, son coupé et bouton de relecture. Il ne s’agit pas d’un succès simulé.
- Quitter Paramètres ne démonte pas le provider de l’application et n’annule pas ses écritures. Au redémarrage, SQLite fournit la dernière valeur commise. Comme toute E/S asynchrone, un arrêt du processus avant le commit ne garantit pas la conservation d’une intention encore en cours.

Le schéma v5 et `PreferencesRepository` ne changent pas. Le minuteur et le hook audio ne changent pas.

## Pager : défaut reproductible et limite du diagnostic

Le déplacement se calcule sur le thread UI. Après une arrivée, `runOnJS(commit)` met à jour React et les paramètres Expo Router. L’effet de synchronisation de `selectedId` traitait tout changement de paramètre comme une **nouvelle demande** et pouvait annuler l’animation puis assigner directement une position de page.

Scénario reproduit dans un test avant correction :

1. Le swipe Accueil → Musculation est terminé.
2. Le swipe Musculation → Accueil est également terminé sur le thread UI.
3. React reçoit seulement alors le paramètre Musculation issu du premier swipe.
4. L’ancien effet repositionne le track de `0` à `-800` pixels pour un viewport de 800 pixels, sans animation.

C’est un défaut de synchronisation démontré. **Ce test fournit un ordre d’événements retardés ; il ne démontre pas que tous les à-coups filmés sur l’iPhone ont cette cause.** Il ne mesure ni le frame pacing UIKit ni la fréquence réelle de ce retard sur l’appareil.

Chaque sélection interne possède maintenant un reçu temporaire, transmis avec `universe` dans le paramètre de route `universeReceipt`. Le pager reconnaît un accusé de sa propre sélection et ne modifie pas le track. Les reçus confirmés ou dépassés par un accusé groupé sont retirés. Les véritables demandes externes restent prises en charge, y compris après réutilisation d’anciens paramètres. Rien n’est écrit dans SQLite pour ce mécanisme.

La reconnaissance `Pan`, les seuils, les coordonnées absolues du doigt, l’arbitrage `Gesture.Native().requireExternalGestureToFail(pan)`, les mesures sur le thread UI, les règles de bord de liste, les deux univers et l’animation de 260 ms sont conservés. **Aucune réécriture de `UniverseScreen.tsx` ni de `physics.ts`.** Le court verrou pendant l’arrivée d’une page reste en place ; un nouveau toucher pendant cette arrivée est toujours refusé selon le comportement précédent.

Si les saccades persistent, les autres pistes doivent être mesurées : toucher pendant ce verrou, ScrollView prenant ensuite le geste, vrai changement de hauteur du viewport, ou charge de rendu au focus. Aucune de ces hypothèses n’a justifié une modification spéculative des recognizers ou du chronomètre.

## Fichiers

| Fichier | Changement |
| --- | --- |
| `src/features/settings/SettingsScreen.tsx` | Switch actif pendant les écritures, aide stable, fond iOS |
| `src/store/PreferencesProvider.tsx` | Valeur immédiate, suivi des intentions et dernière sauvegarde confirmée, erreurs |
| `app/index.tsx` | Transmission du reçu de sélection à Expo Router et retour au pager |
| `src/navigation/UniversePager.tsx` | Reconnaissance des accusés sans déplacement ; diagnostic facultatif enrichi |
| `tests/m33-ui.test.tsx` | Latence, appuis rapides, réponses anciennes, erreurs, sortie des paramètres |
| `tests/m33-data.test.ts` | Écritures SQLite simultanément demandées, persistance et récupération après erreur |
| `tests/pager.test.tsx` | Retours de route retardés, troisième geste en cours, accusés groupés, navigation externe |

La documentation M3.3 et ce guide sont actualisés. Aucune migration, dépendance, identité Expo, performance historique ou convention de repos modifiée. La préférence sonore demeure la seule écriture métier concernée.

Les vérifications locales réussissent : **326 tests** (124 SQLite/domaines, 13 navigation, 189 composants), TypeScript et export JavaScript iOS. Le pager est également testé séparément avec diagnostic activé. Les 11 nouveaux tests vérifient aussi une position intermédiaire de fin d’animation, pas seulement ses extrémités. Le thread UI et les événements natifs sont simulés dans Jest ; seule une nouvelle manipulation sur iPhone permettra d’évaluer la fluidité réelle.

## Récupérer le correctif sur Windows

Arrêter Metro avec **Ctrl+C**, ouvrir PowerShell dans `logbook`, puis :

```powershell
git fetch origin
git switch feat/m3-parametres-stabilisation
git pull --ff-only origin feat/m3-parametres-stabilisation
npm.cmd ci
Remove-Item Env:EXPO_PUBLIC_GESTURE_DEBUG -ErrorAction SilentlyContinue
npm.cmd start -- --clear
```

Scanner le nouveau QR code avec le même projet Expo Go et le même Wi-Fi. Ne pas désinstaller Expo Go ni effacer le stockage. SQLite reste v5, sans migration supplémentaire. Pour les vérifications PC : `npm.cmd run typecheck`, `npm.cmd test`, `npm.cmd run export:ios`.

## Essais iPhone, d’abord sans diagnostic

1. Ouvrir Paramètres. Basculer lentement le son, puis faire 10 bascules rapprochées. Vérifier l’absence de transparence temporaire, de retour imposé à l’état précédent, de contour inhabituel et de déplacement du texte. L’apparence finale doit correspondre au dernier appui.
2. Faire un nombre pair, puis impair de bascules, en notant le résultat final. Attendre une seconde après la dernière bascule, quitter Paramètres et revenir, puis fermer/réouvrir le projet. Vérifier le même résultat. Répéter en revenant à l’accueil immédiatement après la dernière bascule.
3. Avec un vrai repos court, vérifier son activé/coupé et mode silencieux, comme dans le guide M3.3. Le décompte, pause/reprise, dépassement et passage manuel restent identiques. Aucun test de son en arrière-plan n’est présenté comme validé.
4. Faire 10 allers-retours Accueil ↔ Musculation : d’abord normalement, puis en inversant le geste dès l’arrivée de la page. Garder parfois le doigt posé à mi-course ; tester aussi un petit geste annulé. Aucun retour spontané à une ancienne page attendu.
5. Tester un nouveau toucher pendant la fin d’animation. Il peut être refusé par le verrou existant ; noter séparément un simple geste refusé et un vrai saut de page/contenu. Ne pas conclure que le reçu de navigation corrige tous ces cas.
6. Faire défiler les programmes à mi-liste : un swipe descendant doit défiler la liste. Revenir en haut, puis glisser vers le bas pour l’accueil. Vérifier également boutons Musculation/Accueil, ouverture/retour de Paramètres et d’un programme, et conservation des positions de liste.
7. Contrôler rapidement reprise d’entraînement, export personnel et historique. Pas de suppression nécessaire pour ces essais.

## Diagnostic ciblé si le défaut persiste

Arrêter Metro, puis :

```powershell
$env:EXPO_PUBLIC_GESTURE_DEBUG='1'
npm.cmd start -- --clear
```

Le panneau ne capte pas les touchers. Il affiche seulement des événements de début/fin et de synchronisation ; pas de mesure par image. Les mêmes messages apparaissent dans le terminal avec le préfixe `[UniversePager]`.

- `sélection UI #N` puis `route: accusé #N … (sans déplacement)` : retour normal d’une sélection interne ; le reçu ne doit jamais déplacer la page.
- `route externe: … position=…` : recalage demandé par une autre navigation ; signaler ce message s’il apparaît au milieu de swipes seuls.
- `refus: animation / plusieurs doigts` : verrou de fin de transition ou plusieurs contacts. Si un déplacement de contenu suit, le distinguer du déplacement plein écran.
- `géométrie: hauteur=…` : hauteur du viewport appliquée. Un changement au moment du défaut est une piste de recalage.
- `pan: ACTIVE`, `déplacement reçu`, `terminé/annulé` : trajet tactile déjà diagnostiqué dans les versions précédentes.

En cas d’échec, conserver la vidéo et les lignes du terminal autour du défaut, avec iPhone/iOS/Expo Go et sens du geste. Les logs ne contiennent aucun programme, résultat ou export personnel. Le mode diagnostic ajoute du travail JS ; comparer la même manipulation **sans** ce mode avant de juger la fluidité.

Pour le désactiver, arrêter Metro puis :

```powershell
Remove-Item Env:EXPO_PUBLIC_GESTURE_DEBUG -ErrorAction SilentlyContinue
npm.cmd start -- --clear
```

**Les tests automatisés ne valident pas la fluidité native. M3.4 reste en attente de votre retour.**
