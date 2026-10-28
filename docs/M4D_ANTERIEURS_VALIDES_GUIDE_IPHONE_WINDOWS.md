# Windows → iPhone : tester les deux antérieurs validés

Version : branche `feat/m4d-a-selection-muscles`, PR #18. Les deux masques
antérieurs sont ceux de `09c61ab` ; les six autres muscles sont conservés.
Le projet garde Expo SDK 58, son identité et SQLite v8. Aucune réinstallation
d'Expo Go, compilation native, Mac ou offre payante nécessaire pour ce test.

## 1. Vérifier ton dossier actuel sans le modifier

Arrête l'ancien serveur Expo avec **Ctrl+C**. Ouvre PowerShell dans ton dossier
Logbook habituel et exécute :

```powershell
git rev-parse --show-toplevel
git status --short --branch
```

Les lignes de `git status` permettent de voir tes modifications locales.
**Qu'il soit propre ou modifié, le dossier actuel sera conservé tel quel.**
La méthode ci-dessous crée un second dossier de test : aucun changement de
branche, remise à zéro, suppression ou rangement automatique de tes fichiers.

## 2. Créer une copie de travail séparée

Toujours depuis ton dossier Logbook actuel, copier ce bloc :

```powershell
$logbookRacine = git rev-parse --show-toplevel
if ($LASTEXITCODE -ne 0) { throw "Ouvre PowerShell dans ton depot Logbook." }
$logbookRacine = $logbookRacine.Trim()
$logbookDossierTest = Join-Path (Split-Path $logbookRacine -Parent) "logbook-test-anterieurs-valides"

if (Test-Path $logbookDossierTest) {
    throw "Le dossier de test existe deja. Choisis un autre nom ; rien n'a ete efface."
}

git fetch origin feat/m4d-a-selection-muscles
if ($LASTEXITCODE -ne 0) { throw "La recuperation Git a echoue. Arrete-toi ici." }

$logbookCommitTest = (git rev-parse FETCH_HEAD).Trim()
git worktree add --detach "$logbookDossierTest" "$logbookCommitTest"
if ($LASTEXITCODE -ne 0) { throw "La creation du dossier de test a echoue." }

Set-Location "$logbookDossierTest"
git status --short --branch
git log -1 --oneline
```

Le dernier commit affiché doit correspondre à la livraison de la PR #18 indiquée
dans le message accompagnant ce guide. `HEAD` détachée est normale : ce dossier
sert uniquement à tester une version précise, sans déplacer ta branche actuelle.
La commande `fetch` met à jour les références Git, sans écraser tes fichiers.

Si le dossier de test existe déjà, garder son contenu et remplacer uniquement
le nom `logbook-test-anterieurs-valides` dans le bloc par un nom libre, par exemple
`logbook-test-anterieurs-valides-2`.

## 3. Installer et démarrer Expo

Dans ce **nouveau dossier de test** :

```powershell
npm.cmd ci
if ($LASTEXITCODE -ne 0) { throw "L'installation a echoue. Arrete-toi ici." }
npx.cmd expo start --go --lan
```

`npm.cmd` et `npx.cmd` évitent les scripts PowerShell `npm.ps1` bloqués sur ton PC.
`npm.cmd ci` utilise les dépendances verrouillées de la version testée.

Garde le PC et l'iPhone sur le même Wi-Fi. Le serveur doit reprendre le port
habituel **8081** ; s'il est occupé, arrêter l'ancien serveur plutôt que lancer
une seconde instance sur un autre port. Ouvrir le QR code avec l'appareil photo
de l'iPhone puis **Expo Go SDK 58**. Accepter l'accès réseau local si demandé.
Conserver l'installation et les données existantes d'Expo Go.

## 4. Contrôles sur l'iPhone

Ouvrir **Musculation → Mannequin 3D · Aperçu**.

1. Vérifier le mannequin neutre au départ, puis le nouveau deltoïde antérieur
   droit et le nouveau gauche. En vue de face, le côté gauche anatomique apparaît
   à droite de l'écran. Une seule zone est orange à la fois.
2. Vérifier les huit sélections et leurs noms français : deux pectoraux et les
   six faisceaux des épaules. Les moyens, postérieurs et pectoraux doivent garder
   leurs limites précédentes.
3. Tester **Réinitialiser la sélection** : retour au gris sans déplacement de
   caméra. Changer directement de muscle doit déplacer la surbrillance orange.
4. Tester rotation complète, zoom/dézoom à deux doigts et déplacement vertical.
   Les gestes doivent conserver le muscle actif.
5. Tester **Face** et **Vue générale**, puis quitter et rouvrir le visualiseur.
6. Vérifier que tes programmes, séances, repos, historique, exercices et paramètres
   habituels sont toujours présents. Le schéma SQLite et les chemins de stockage
   n'ont pas été modifiés.

Les captures du rapport sont de vrais rendus WebGL de test, pas des captures
de ton iPhone. **La validation sur ton téléphone reste à faire par toi.**
Après le test, arrêter Expo avec Ctrl+C ; ton ancien dossier et tes modifications
locales sont toujours disponibles. Aucune suppression du dossier de test n'est
nécessaire pour reprendre ton travail habituel.
