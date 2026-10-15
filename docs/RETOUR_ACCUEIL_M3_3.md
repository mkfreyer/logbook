# M3.3 — Présentation du retour Musculation → Accueil

Le propriétaire a confirmé sur iPhone que le correctif `262a844` résout l’animation du Switch sonore. Le retour vers l’accueil présente encore une composition visuelle gênante. Cette livraison reste sur `feat/m3-parametres-stabilisation`, dans la PR #7 en brouillon, sans fusion ni début de M3.4.

## Cause reproduite : la disposition de deux pages entières

Les six fichiers demandés ont été examinés : `UniversePager.tsx`, `UniverseScreen.tsx`, `physics.ts`, `HomeScreen.tsx`, `ProgramsScreen.tsx` et `app/index.tsx`. Aucun élément ne justifie de rétablir ou modifier les seuils des gestes.

Le pager déplaçait un ruban de pages de hauteur H. Au retour descendant de déplacement d :

- haut de l’accueil = **−H + d** ;
- haut de Musculation = **d**.

Le bas de l’accueil apparaissait donc avant son en-tête. À mi-course, l’en-tête restait au-dessus du viewport, tandis que les boutons du bas étaient déjà visibles. `marginTop: 'auto'` poussait ces boutons loin de la carte du programme. L’espace libre entre les deux traversait le viewport avec tout le reste de la page, ce qui pouvait donner une impression de défilement par morceaux **même avec une translation continue**.

Une reproduction React Native Web avec hauteurs de page fixes, conteneurs flex, marges de sécurité simulées et composants réels montre cet effet. Avec les données de démonstration uniquement utilisées dans cet outil de contrôle, l’espace carte → boutons était de 22 px à 375 × 667, 138 px à 390 × 844 et 234 px à 430 × 932. Le titre de l’accueil était hors écran à mi-retour. Les valeurs exactes dépendent de la police, de la taille de texte, des données et d’iOS ; elles ne prétendent pas mesurer la vidéo.

**La vidéo n’était pas jointe à la demande.** Les instants 1 s et 4,2–4,5 s ne peuvent donc pas être analysés image par image. Cette reproduction confirme le défaut de composition décrit ; elle ne prouve pas l’absence de toute autre saccade native. L’ancien problème de retour Expo Router n’est pas supposé revenu et son correctif est conservé.

## Correction limitée à la présentation

L’accueil sert maintenant d’arrière-plan stable. Musculation monte depuis le bas pour le couvrir et descend au rythme du doigt pour le découvrir par son en-tête. Le contenu de chaque page reste un bloc unique ; il n’existe pas d’animation indépendante des cartes ou boutons.

Le track conserve **exactement** son offset interactif, ses bornes et sa fin d’animation. Une compensation calculée sur le thread UI empêche uniquement les pages déjà couvertes de partir au-dessus du viewport :

```text
compensation = max(0, −offsetDuTrack − index × hauteur)
hautVisibleDeLaPage = max(0, index × hauteur + offsetDuTrack)
```

Pour nos deux univers, l’accueil reste à y = 0 et Musculation reste à y = H + offsetDuTrack. Cette page suit donc le même déplacement absolu du doigt qu’avant. Les couches ont un ordre explicite, un fond opaque et une découpe à leur hauteur ; elles ne laissent pas d’interstice entre deux écrans. Une annulation inverse naturellement le même mouvement. Le calcul permet aussi une troisième page ultérieure, testée avec une fixture, sans ajouter de Cardio dans l’application.

La marge automatique du bloc inférieur de l’accueil est retirée. Les boutons suivent les cartes avec l’espacement normal de **18 px**, au lieu d’être isolés par un intervalle extensible. Une place libre peut rester en bas d’un grand écran, ainsi que les marges de sécurité iOS ; elle reste fixe et ne traverse plus l’écran entre l’en-tête et les boutons.

## Fichiers modifiés et garanties

| Fichier | Modification |
| --- | --- |
| `src/navigation/presentation.ts` | Compensation de présentation pure et utilisable sur le thread UI |
| `src/navigation/UniversePager.tsx` | Application de cette compensation aux pages, ordre des couches et découpe |
| `src/features/home/HomeScreen.tsx` | Retrait de `marginTop: 'auto'` du bloc inférieur |
| `tests/pager.test.tsx` | Géométrie effective des pages pendant les deux gestes, annulations, couche opaque et troisième page de test |
| Documentation M3.3 | Explication, résultats et protocole iPhone actualisés |

`UniverseScreen.tsx`, `physics.ts`, `ProgramsScreen.tsx` et `app/index.tsx` ont été inspectés puis conservés. Pas de changement de `Gesture.Native`, de reconnaissance Pan, de coordonnées du doigt, de seuils, de règles de bord de liste, de reçus Expo Router, de verrou ni des 260 ms de fin d’animation. Les pages restent montées ; les positions des ScrollView ne sont pas réinitialisées. L’interaction et l’accessibilité des pages inactives restent désactivées jusqu’à l’arrivée.

**SQLite reste v5, sans migration. Aucun programme, historique, chronomètre, réglage sonore, dépendance ou identité Expo modifié.** Le précédent correctif du Switch reste intact.

## Vérifications

Un nouveau test échouait avant correction : après un retour de 20 px sur une page de 800 px, le haut de l’accueil restait à −780 px. Il doit maintenant rester à 0 tandis que Musculation est à 20 px.

Les tests vérifient les positions effectives, donc la translation du track **et** celle des pages : plusieurs déplacements dans chaque sens, geste court, annulation native, superposition opaque, navigation accessible, accusés de route retardés et état au milieu d’une animation. Les règles qui laissent défiler les programmes à mi-liste restent couvertes par les tests existants.

Le contrôle visuel compare 15 positions sur les trois dimensions ci-dessus, avant/après, avec le même calcul de présentation que l’application. Après correction : haut de l’accueil fixe, haut de Musculation correspondant au déplacement, espace carte/boutons de 18 px et aucun débordement horizontal. Les composants utilisent des données simulées dans cet outil hors application ; aucune donnée n’est insérée dans SQLite.

Résultats locaux : **331 tests** (124 SQLite/domaines, 13 navigation, 194 composants), TypeScript et export JavaScript iOS réussis. Les **24 tests du pager** passent également avec le diagnostic activé. Les cinq nouveaux scénarios couvrent le retour, l’aller, deux formes d’annulation et l’extension de la présentation à une troisième page de test.

Ces vérifications ne font tourner ni UIKit ni la reconnaissance native du geste. **La fluidité réelle et la correspondance exacte avec les vidéos restent à confirmer sur iPhone.**

## Installer sur Windows

Après **Ctrl+C** pour arrêter Metro, dans PowerShell ouvert dans `logbook` :

```powershell
git fetch origin
git switch feat/m3-parametres-stabilisation
git pull --ff-only origin feat/m3-parametres-stabilisation
npm.cmd ci
Remove-Item Env:EXPO_PUBLIC_GESTURE_DEBUG -ErrorAction SilentlyContinue
npm.cmd start -- --clear
```

Scanner le nouveau QR code sur le même Wi-Fi, dans le même projet Expo Go. **Ne pas désinstaller Expo Go ni effacer son stockage.** Aucune migration supplémentaire. Si la branche n’existe pas localement, utiliser `git switch --track origin/feat/m3-parametres-stabilisation` à la place du premier `git switch`.

## Gestes à refaire sur iPhone

1. Depuis le haut de Programmes, descendre lentement en gardant le doigt posé à un quart, à la moitié et aux trois quarts du trajet. L’en-tête de l’accueil doit se découvrir en premier et rester stable ; les boutons du bas ne doivent plus être transportés seuls dans le haut de l’écran.
2. Remonter depuis l’accueil : Musculation doit monter comme une page entière, continuellement attachée au déplacement du doigt. L’accueil reste en arrière-plan pendant cette présentation.
3. Faire de petits gestes puis relâcher, revenir en arrière sans lever le doigt, puis interrompre un geste. Vérifier que la page revient naturellement sans changement d’univers accidentel.
4. Faire dix allers-retours, puis des gestes plus rapides. Distinguer un saut de position d’un nouveau toucher refusé pendant les 260 ms de fin d’animation : ce verrou n’a pas changé.
5. Dérouler une longue liste de programmes. À mi-liste, un geste descendant doit défiler la liste. Revenir en haut puis faire un nouveau geste pour l’accueil. Vérifier que les positions ne se réinitialisent pas après l’aller-retour.
6. Vérifier les boutons **Accueil**, **Musculation**, l’ouverture/retour d’un programme et des paramètres. Si l’accueil avait lui-même été défilé sur un petit écran ou avec du grand texte, sa position antérieure est conservée ; le retour ne force pas son ScrollView en haut.
7. Refaire quelques bascules rapides du son, quitter/revenir, puis vérifier un repos court et une reprise d’entraînement. Le correctif sonore et le minuteur doivent rester identiques.

Tester d’abord sans diagnostic, puis enregistrer une vidéo si nécessaire. Si un vrai saut persiste, conserver les logs autour de l’événement avec le sens du geste, le modèle d’iPhone, iOS, Expo Go et la taille de texte. Le [diagnostic facultatif existant](CORRECTIFS_ANIMATION_M3_3.md#diagnostic-ciblé-si-le-défaut-persiste) permet de repérer un recalage de route ou de hauteur ; son panneau ajoute du travail JS et ne doit pas servir seul à juger la fluidité.

**M3.4 reste en attente de votre validation.**
