# M4A — Audit préalable de la carte musculaire 3D

## État de cette livraison

**Audit préparatoire seulement : aucun prototype 3D n’est intégré ni annoncé validable.** L’inspection réelle de BodyParts3D est bloquée par l’accès réseau de l’environnement cloud. Il n’y a donc ni mannequin de remplacement, ni nouvel écran ou bouton factice, ni métrique de modèle inventée.

Base vérifiée le 17 octobre 2026 : `feat/m34c-fiches-exercices`, commit `7c2aa5c47994f1bc58758302274a8c5b9693200b`. La PR #10 est ouverte, en brouillon et non fusionnée, basée sur M3.4B. La branche `feat/m4a-prototype-carte-musculaire-3d` est créée depuis ce commit ; sa PR doit cibler M3.4C. Aucune fusion autorisée.

La demande M4A et son image jointe prévalent sur les anciennes propositions : corps masculin entier, silhouette athlétique, relief anatomique lisible, matière satinée gris bleuté, fond bleu nuit, sélection orange, rotation horizontale et zoom automatique depuis l’angle courant. Pas de zoom manuel, de boutons de vues ou de statistiques inventées.

## Ce qui a réellement été vérifié

| Vérification | Résultat |
| --- | --- |
| Références Logbook | Spécification, maquette des 21 écrans et documentation M3.4C consultées |
| Base Git et PR #10 | Commit et base conformes à la demande |
| Page officielle de téléchargement | Requête HTTPS refusée avec HTTP 403 ; domaine absent de la politique réseau active |
| Page officielle de licence | Connexion HTTPS refusée par le proxy : `CONNECT tunnel failed, response 403` |
| Archives OBJ officielles | Non récupérées ; aucun fichier OBJ inspecté |
| Métadonnées anatomiques officielles | Non récupérées ; aucune correspondance mesh/muscle établie |
| Anatomie, corps complet, intersections, trous, rendu | Non évalués faute de géométrie |
| GLB, triangles, meshes, matériaux, taille, FPS | Aucun fichier produit ; aucune mesure disponible |
| Moteurs de rendu | Sources officielles npm/Expo/GitHub examinées ; [comparaison détaillée](AUDIT_M4A_MOTEUR_3D.md) |

Ce refus réseau ne prouve pas que le site ou les archives sont indisponibles ailleurs. Il ne permet pas non plus de conclure que BodyParts3D convient ou ne convient pas à la référence.

### Accès nécessaire

- [Téléchargement officiel](https://dbarchive.biosciencedbc.jp/en/bodyparts3d/download.html).
- [Licence officielle](https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html).
- Le domaine `dbarchive.biosciencedbc.jp` a été ajouté au **brouillon** de configuration réseau, ainsi que `docs.expo.dev`, en préservant `api.expo.dev` et `api.github.com` et le préréglage des gestionnaires de paquets. Les instructions de démarrage de l’environnement ont été actualisées et vérifiées.
- Le brouillon nécessite une application/publication via les paramètres de l’environnement. À la dernière vérification, la politique de la machine active n’autorisait toujours pas BodyParts3D. Enregistrer un brouillon ne débloque pas rétroactivement la connexion.
- Après application, relire les deux pages, puis suivre **leurs liens réels**. Si une archive utilise un autre domaine, demander cet accès précis par le même mécanisme ; ne pas contourner le proxy.

### Fichiers à fournir si le téléchargement cloud reste impossible

Une [documentation publique de lecteur BodyParts3D](https://github.com/wspr/BodyParts3D-Matlab/blob/master/README.md) cite exactement **`isa_BP3D_4.0_obj_99.zip`** (Polygon Mesh Data, IS-A Tree, version 4.0) et **`isa_element_parts.txt`**. Il s’agit d’une référence secondaire à la distribution officielle, pas d’une vérification actuelle de la page de téléchargement, de la taille, de l’intégrité ou de la licence de l’archive.

Depuis la page officielle, choisir cette archive 4.0 et sa table d’identification, joindre aussi les autres métadonnées associées et une copie de la page de licence. Si le nom présenté aujourd’hui diffère, fournir la page ou son lien exact avant de choisir une autre version. Aucune géométrie issue d’un miroir tiers n’a été téléchargée ou intégrée.

L’outil de lecture des pièces jointes cloud accepte au maximum 32 Mio par fichier. Pour transmettre une archive plus grande, ce script PowerShell crée des parties binaires de 30 Mio à joindre **toutes**, sans modifier l’archive originale :

```powershell
$archive = (Resolve-Path '.\isa_BP3D_4.0_obj_99.zip').Path
$folder = Join-Path (Split-Path $archive) ('bodyparts-upload-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force $folder | Out-Null
$buffer = New-Object byte[] (30 * 1024 * 1024)
$inputStream = [System.IO.File]::OpenRead($archive)
try {
    $part = 1
    while (($count = $inputStream.Read($buffer, 0, $buffer.Length)) -gt 0) {
        $path = Join-Path $folder ('isa_BP3D_4.0_obj_99.zip.part{0:D3}' -f $part)
        $outputStream = [System.IO.File]::Create($path)
        try { $outputStream.Write($buffer, 0, $count) }
        finally { $outputStream.Dispose() }
        $part++
    }
} finally { $inputStream.Dispose() }
Get-FileHash $archive -Algorithm SHA256
```

Transmettre les parties, la somme SHA-256 affichée et les métadonnées. La reconstruction sera contrôlée avant extraction. Ne pas mettre les archives sources dans Git. Le script est fourni pour PowerShell ; il n’a pas été exécuté sur un ordinateur Windows dans cet environnement Linux.

## Licence et provenance

La demande cite CC BY 4.0 et l’attribution :

> BodyParts3D, © The Database Center for Life Science licensed under CC Attribution 4.0 International

Cette mention est préparée pour les crédits mais **la page officielle n’a pas encore pu être lue**. La licence applicable à la distribution exacte devra être conservée avec sa provenance avant intégration commerciale.

Les références secondaires anciennes mentionnent CC BY-SA 2.1 Japan. Le [miroir de Kevin Moerman](https://github.com/Kevin-Mattheus-Moerman/BodyParts3D) annonce notamment une version **3.0**, convertie en STL, et signale des intersections pour la 4.0. Ce sont des avertissements documentaires d’un tiers, pas nos observations de la version 4.0. Ils ne justifient ni un changement de source silencieux ni une conclusion sur la qualité. La licence d’un ancien miroir ne remplace pas celle de l’archive officielle à vérifier.

Pour chaque fichier finalement utilisé : URL exacte, version, date, SHA-256, licence, IDs anatomiques, modifications et outil/version. Les crédits devront accompagner l’asset distribué et être consultables depuis À propos.

## Plan après déblocage de l’asset

1. **Inventaire réel** : vérifier l’archive, lire OBJ et tables, identifier unités/axes, structures et côtés gauche/droit. Sélectionner les pectoraux, puis deltoïdes et grands dorsaux seulement si leurs identités sont établies. Inventorier également les autres groupes demandés, sans association approximative.
2. **Évaluation visuelle avant intégration** : produire des rendus face, trois quarts, profil et dos à partir des vrais fichiers, avec matière acier satinée et éclairage doux. Examiner silhouette, tête, mains, pieds, surfaces superposées, trous, parties flottantes, normales et muscles visibles. Les rendus servent à l’audit ; ils ne remplacent pas la scène 3D de l’application.
3. **Décision qualité** : si le nettoyage et la simplification ne permettent pas le résultat demandé, arrêter l’intégration, montrer les défauts constatés et demander une décision avant une autre source. Une silhouette faite de primitives n’est pas une solution de remplacement autorisée.
4. **Préparation reproductible** : nettoyer sans changer les identités anatomiques, simplifier avec comparaison visuelle, préserver les côtés, limiter matériaux/textures, exporter GLB. Mesurer triangles, meshes, matériaux, taille et draw calls. Conserver scripts/manifestes/attribution ; aucune archive volumineuse dans le dépôt. Aucun budget atteint n’est annoncé avant mesure.
5. **Intégration isolée** : éprouver le candidat Three.js dans une WebView locale, puis confirmer le choix selon rendu, chargement local, mémoire et compatibilité Expo Go. Aucun development build imposé. Une route `/muscle-map` depuis Musculation évite toute modification du pager existant.
6. **Interactions** : vraie rotation 360°, tap distinct d’un glissement, raycasting des surfaces visibles, surbrillance orange limitée au mesh sélectionné, interpolation caméra depuis sa pose actuelle, cadrage de retour conservant l’orientation. Aucun zoom/pan manuel. Panneau accessible : nom et exactement Tonnage / Nombre de séries / Part du volume, toutes valeurs neutres « — ».
7. **Cycle de vie et validation** : rendu seulement nécessaire, arrêt au flou et en arrière-plan, nettoyage GPU, gestion des chargements tardifs et pertes de contexte. Tests ciblés, contrôles complets puis essai iPhone ; aucune annonce de 60 FPS sans mesure.

### Frontières de code prévues, non créées

- `app/muscle-map.tsx` et `src/features/muscle-map/*` : écran, adaptateur moteur, caméra, gestes, panneau. Conteneur fixe propre : le composant `Screen` actuel contient un ScrollView inadapté à une scène plein écran.
- Manifeste local de géométrie : IDs source et côtés, groupes Logbook séparés de la sélection et d’un futur contrat de volume. Aucun coefficient de répartition ni requête d’historique en M4A.
- Asset GLB et pipeline sous contrôle de version après audit, avec extension Metro ajoutée seulement si le chargement l’exige.
- `ProgramsScreen.tsx` : accès à ajouter uniquement lorsque la vraie carte existe ; crédits À propos une fois l’asset intégré.
- `src/navigation/*`, `app/index.tsx`, `src/db/*`, chronomètre, observateur sonore, exports, formulaires et identité Expo restent hors de cette intégration.

Le Stack peut garder une route montée sans focus : un nettoyage au seul démontage ne suffit pas. Le futur écran doit combiner focus et AppState, invalider les réponses de chargement anciennes et libérer les ressources au démontage. Le `SessionProvider` et son observateur de repos doivent continuer à fonctionner indépendamment de la carte.

## Stratégie de tests M4A

- Parser le **vrai GLB livré** : IDs uniques, côtés et groupes justifiés, références sans orphelin, indices valides, valeurs finies, aucune dépendance réseau externe, métriques calculées depuis le fichier.
- Raycasting réel face/profil/dos : surface visible touchée et identité exacte ; ne pas prendre un mock de renderer pour preuve de sélection anatomique.
- Tap, drag, drag revenu à son origine, annulation et deuxième doigt : la rotation ne sélectionne jamais au relâchement.
- Caméra : cadrage tête/pieds selon ratio iPhone, zoom depuis le dos sans retour de face, interruption/reprise sans saut, distance de sécurité, fermeture rapide et nouvelle sélection.
- Composants : première ouverture minimale, trois indicateurs neutres, fermeture, erreurs et réessai, appuis rapides sur l’accès, messages de scène validés.
- Cycle de vie : arrêt des frames au flou/arrière-plan, ressources libérées, chargement tardif ignoré, reprise après perte du contexte/processus ; aucun appel d’écriture SQLite.
- Régressions M0–M3.4C : suite existante, TypeScript, export iOS, CI sur le commit final ; conserver les tests du pager, du repos, des champs non validés et des alternatives.

**Ces tests 3D ne sont pas encore implémentés**, puisqu’aucun asset ou nouveau comportement n’a été intégré. Les contrôles de cette livraison portent sur la base existante et le dossier documentaire.

## Vérifications réellement exécutées

- **535 tests** : 219 SQLite/domaine, 13 navigation, 303 composants (19 suites UI), tous réussis, aucun ignoré.
- **17 tests du pager** répétés avec `EXPO_PUBLIC_GESTURE_DEBUG=1` : réussis.
- `npm run typecheck` : réussi.
- `CI=1 EXPO_OFFLINE=1 EXPO_NO_TELEMETRY=1 npm run export:ios` : réussi.
- Metro : manifeste iOS et bundle demandés réellement, HTTP 200 ; identité `Logbook` / `logbook` / `0.1.0`. Serveur démarré pour le contrôle puis arrêté.
- CI GitHub : consulter les checks de la PR sur son commit publié ; les contrôles existants ne testent pas de 3D.

**SQLite reste v8.** Aucun fichier de production, dépendance, migration ou donnée personnelle n’est modifié par cette préparation.

## Récupération Windows et future vérification iPhone

Pour consulter la branche d’audit, depuis le dossier Logbook dans PowerShell :

```powershell
git fetch origin
git switch feat/m4a-prototype-carte-musculaire-3d
git pull --ff-only origin feat/m4a-prototype-carte-musculaire-3d
```

Si nécessaire lors de la première récupération : `git switch --track origin/feat/m4a-prototype-carte-musculaire-3d`.

**Cette branche ne contient pas encore la carte et ne nécessite pas une mise à jour iPhone.** L’application y a exactement le comportement du commit M3.4C de référence. Pour relancer cette version existante uniquement :

```powershell
npm.cmd ci
npm.cmd start -- --clear
```

Ne pas effacer les données d’Expo Go ni réinstaller l’application.

Lorsque le prototype sera intégré, le guide iPhone devra faire vérifier : beauté face/profil/dos et fidélité à la référence ; corps entier au départ ; absence de boutons de vues/zoom ; rotation 360° sans sélection accidentelle ; pectoral orange ; zoom depuis l’angle courant, notamment dos ; fiche et ses trois indicateurs neutres ; fermeture animée et nouvelle sélection ; hors ligne après chargement Expo Go ; arrière-plan/reprise ; ouvertures/fermetures répétées ; entraînement et repos toujours intacts. Tous ces essais restent **à faire**, pas validés par les tests Linux.

La fusion suivra les parents M3.4B → M3.4C → M4A, uniquement après autorisation ; adapter la base et vérifier le diff si un parent est fusionné. M4B reste hors périmètre.
