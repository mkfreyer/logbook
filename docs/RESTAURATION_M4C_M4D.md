# Restauration des masques validés — M4C et M4D-A

Les essais rejetés `6817b08` et `265d058` sont annulés par de nouveaux commits. Aucune réinterprétation anatomique, aucun lissage ni nouveau contour.

## Références retrouvées exactement

- **M4C : `06fa665`.** Les 47 fichiers du dossier `docs/m4c/meshy-posterieurs-harmonises/` sont identiques octet pour octet à cette référence, dont les huit masques, l’atlas d’IDs, les deux atlas RGBA, le Blender et le GLB de contrôle. Ils n’avaient pas été écrasés ; la proposition ajoutée pour les annotations jaunes est retirée de la branche courante.
- **M4D-A : `268ea3e`.** Les frontières chargées dans le visualiseur retrouvent leur version originale. Les trois fichiers runtime sont restaurés octet pour octet, ainsi que le générateur et la liaison utilisée par les tests.
- **Géométrie : Meshy `e45e5d8` inchangé.** Aucun déplacement de sommet, modification de normale, d’UV ou de silhouette. Toujours 110 588 triangles.

### Fichiers M4D remis à l’identique de 268ea3e

| Fichier | Restauration |
| --- | --- |
| `assets/models/meshy-m4d-uv.glb` | Binaire runtime exact, 2 606 152 octets |
| `src/features/model3d/generated/selectionData.ts` | Métadonnées et PNG de l’ancien atlas exacts |
| `src/features/model3d/generated/viewerBundle.ts` | Bundle du visualiseur exact |
| `tools/m4d/build-selection.mjs` | Source M4C rétablie sur `meshy-posterieurs-harmonises` |
| `tests/muscle-selection.test.ts` | Liaison restaurée vers les sources validées |

Les **132 fichiers applicatifs** contrôlés (`src`, `app`, `assets`, identité, dépendances et configuration TypeScript) sont tous identiques à `268ea3e`. La sélection des huit zones, les noms français, l’orange, la réinitialisation et les gestes de caméra sont donc conservés, avec leurs contrôles automatisés. SQLite v8 et les fonctions existantes restent inchangés.

Deux améliorations indépendantes des outils de test sont préservées : l’attente de stabilisation de l’inertie avant la projection d’un toucher et le choix du dossier de sortie des planches. Le test utilise une vue de profil pour les portions latérales afin de viser une surface visible. Ces réglages ne modifient ni les masques, ni le code applicatif, ni les gestes du visualiseur.

Les dossiers et scripts ajoutés pour les annotations jaunes sont retirés des branches courantes. Ils restent accessibles dans l’historique Git. Aucun reset destructeur, force-push, suppression de branche ou fusion de Pull Request. La PR #18 reprend le nouveau commit de restauration de la PR #17 par une synchronisation Git conservant les parents existants.

## Rendus de confirmation

Vrais rendus Blender effectués depuis le fichier original de `06fa665`, sans réexporter ou modifier les ressources :

- [Face](m4c/restauration-06fa665/renders/face.png)
- [Dos](m4c/restauration-06fa665/renders/dos.png)
- [Trois quarts arrière gauche](m4c/restauration-06fa665/renders/trois-quarts-gauche.png)
- [Trois quarts arrière droit](m4c/restauration-06fa665/renders/trois-quarts-droit.png)

[Huit sélections orange restaurées](m4d/selection-restauree/planche-huit-selections.png) — captures réelles du visualiseur WebGL dans Chromium/SwiftShader, pas d’un nouvel essai iPhone. Les captures individuelles sont dans le même dossier. La planche ne modifie pas les pixels du mannequin.

## Vérifications

- [Comparaison binaire M4C](m4c/restauration-06fa665/verification.json).
- [Comparaison runtime et fichiers applicatifs avec 268ea3e](m4d/selection-restauree/verification.json).
- [Huit touchers dans le visualiseur](m4d/selection-restauree/browser-verification.json).
- [Régression des gestes et libération du moteur](m4d/selection-restauree/viewer-regression.json).

La comparaison binaire vérifie tous les huit masques, les huit identifiants et l’atlas utilisé par le runtime. Les ressources interactives ne sont pas régénérées à partir des essais rejetés : ce sont exactement les fichiers du commit demandé. Le contrôle de génération confirme qu’ils correspondent à leurs sources restaurées.

## Pour vérifier sur iPhone

Dans PowerShell, depuis le dépôt Logbook, conserver d’éventuels fichiers locaux modifiés avant de changer de branche :

```powershell
git status --short
git fetch origin
git switch feat/m4d-a-selection-muscles
git pull --ff-only
npm.cmd ci
npx.cmd expo start --go --lan
```

Si Metro affiche encore l’ancien cache : `npx.cmd expo start --go --lan --clear`. Aucune réinstallation ou suppression des données Expo Go n’est demandée. Expo SDK 58 reste inchangé.

Les deux PR restent en brouillon. Arrêt après restauration pour vérification utilisateur ; aucune autre fonctionnalité commencée.

### Résultats de contrôle

**551 tests réussis**, cohérence Expo SDK 58, TypeScript, contrôle du bundle et export JavaScript iOS réussis. Huit sélections avec les anciens contours vérifiées par de vrais événements tactiles WebGL, avec noms français, changement de muscle et réinitialisation. Rotation >360°, zoom/dézoom, déplacement vertical, Face et Vue générale contrôlés ; cinq cycles de fermeture/réouverture libèrent le moteur. Ces tests navigateur ne constituent pas un nouvel essai physique sur iPhone.

La restauration source est publiée dans la PR #17 au commit `168ac61`. Sa synchronisation dans la branche M4D est le merge Git `4c2bc53`. Les fichiers runtime restaurés et le présent rapport sont livrés par le nouveau commit de correction de la PR #18.
