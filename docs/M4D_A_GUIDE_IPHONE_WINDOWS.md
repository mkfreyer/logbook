# M4D-A — Tester la sélection sur iPhone depuis Windows

Branche : `feat/m4d-a-selection-muscles`. Base : M4C `06fa665`, Expo SDK 58. Aucun changement de données ni réinstallation d’Expo Go demandés.

Dans PowerShell, dans **ton dossier Logbook existant** :

```powershell
git status --short
```

Si cette commande affiche des fichiers modifiés, les conserver avant de changer de branche. Ne pas utiliser de commande de remise à zéro.

Pour récupérer la branche la première fois :

```powershell
git fetch origin
git switch --track -c feat/m4d-a-selection-muscles origin/feat/m4d-a-selection-muscles
npm.cmd ci
npx.cmd expo install --check
npx.cmd expo start --go --lan
```

Si cette branche existe déjà sur ton PC, remplacer la commande `git switch --track ...` par :

```powershell
git switch feat/m4d-a-selection-muscles
git pull --ff-only
```

Garder le PC et l’iPhone sur le même Wi-Fi, accepter l’accès réseau local si Windows ou iOS le demande. Ouvrir le QR code avec l’appareil photo de l’iPhone puis Expo Go SDK 58. Conserver les données de l’application et d’Expo Go. Si un autre serveur Metro tourne, l’arrêter avec Ctrl+C avant le lancement. En cas de cache JavaScript ancien :

```powershell
npx.cmd expo start --go --lan --clear
```

Dans Logbook, ouvrir **Musculation → Mannequin 3D · Aperçu** (accès existant). Tester :

1. Le mannequin est gris au départ, sans couleurs de contrôle rouge/bleu/vert.
2. Un toucher bref sur un pectoral affiche son nom français et colore **uniquement ce pectoral en orange**. La gauche est celle du mannequin : elle apparaît à droite de l’écran quand il est de face.
3. Toucher l’autre pectoral change la sélection. Tourner le mannequin et tester les portions antérieure, moyenne et postérieure de chaque épaule : huit noms distincts au total.
4. Toucher une surface grise (par exemple la tête ou une cuisse) retire la sélection. Un toucher sur le fond fait de même.
5. **Réinitialiser la sélection** revient au gris sans changer le cadrage.
6. Un glissement à un doigt tourne le modèle sans sélectionner un autre muscle. Un pincement zoome/dézoome et un glissement à deux doigts déplace le cadrage verticalement, sans changer le muscle actif.
7. **Face** conserve le zoom ; **Vue générale** retrouve le corps entier. Ces boutons conservent la sélection.
8. Quitter le visualiseur puis le rouvrir : le mannequin revient neutre. Vérifier également le retour après passage en arrière-plan.
9. Vérifier que les programmes, la séance en cours, le chronomètre, l’historique et les paramètres habituels restent disponibles.

Faire remonter les éventuels touchers difficiles à viser, faux positifs pendant les gestes, ralentissements ou erreurs au retour dans le visualiseur, avec le côté anatomique concerné et l’angle. Les captures du rapport proviennent d’un navigateur de test, **pas d’un véritable iPhone**. La validation M4D-A sur iPhone reste à faire par l’utilisateur.

Aucun Mac, compilation native ou abonnement nécessaire pour ce test Expo Go.
