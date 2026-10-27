# Retester les deltoïdes corrigés sur iPhone

La branche reste **`feat/m4d-a-selection-muscles`**, PR #18 en brouillon. Elle reprend la correction M4C `6817b08` de la PR #17. La sélection tactile et les gestes n’ont pas été modifiés.

Dans PowerShell, depuis ton dossier Logbook :

```powershell
git status --short
git fetch origin
git switch feat/m4d-a-selection-muscles
git pull --ff-only
npm.cmd ci
npx.cmd expo install --check
npx.cmd expo start --go --lan
```

Conserver d’éventuels fichiers locaux modifiés avant le changement de branche. Ne pas utiliser de remise à zéro du dépôt. Si cette branche n’existe pas encore sur le PC, remplacer `git switch ...` par :

```powershell
git switch --track -c feat/m4d-a-selection-muscles origin/feat/m4d-a-selection-muscles
```

PC et iPhone sur le même Wi-Fi, Expo Go SDK 58. Ouvrir le QR code puis **Musculation → Mannequin 3D · Aperçu**. Si Metro était déjà ouvert, l’arrêter avec Ctrl+C avant de relancer. Si les anciens contours restent visibles malgré la mise à jour :

```powershell
npx.cmd expo start --go --lan --clear
```

Cette commande ne demande aucune réinstallation ni suppression de données Expo Go ou SQLite.

Contrôler les six faisceaux, un à un, en faisant tourner le mannequin :

1. Antérieurs : le contour se rapproche de l’avant de l’épaule et du pectoral.
2. Moyens : le dôme latéral est davantage occupé, avec des limites partagées continues.
3. Postérieurs : l’arrondi supérieur et le bord commun avec le moyen sont régularisés.
4. Comparer les deux épaules en face, de profil et de dos. Vérifier surtout les pointes : les extrémités des trois annotations ont été raccordées vers une insertion commune, comme expliqué dans le rapport.
5. Confirmer qu’un seul muscle devient orange et que le nom français correspond au côté anatomique. Les deux pectoraux doivent garder leurs contours précédents.
6. Tester le changement de muscle, une surface grise, le fond et **Réinitialiser la sélection**.
7. Tester rotation, pincement, déplacement à deux doigts, **Face**, **Vue générale**, puis fermeture/réouverture du visualiseur.

Les captures livrées proviennent de Blender et d’un navigateur WebGL. **La nouvelle répartition des masques reste à valider sur ton véritable iPhone.** Aucun nouveau zoom automatique, orientation automatique, exercice lié ou carte thermique.
