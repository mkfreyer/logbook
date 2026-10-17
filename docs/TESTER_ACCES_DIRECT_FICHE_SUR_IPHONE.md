# Vérifier l’accès direct à la fiche — M3.4C

M3.4C `c85a2a9` est validée sur iPhone. Ce petit correctif reste à vérifier : **toucher l’encadré bleu ouvre la fiche immédiatement**. Aucun changement de schéma : SQLite reste v8.

Dans PowerShell, après Ctrl+C, depuis `logbook` :

```powershell
git switch feat/m34c-fiches-exercices
git pull --ff-only origin feat/m34c-fiches-exercices
npm.cmd ci
npm.cmd start -- --clear
```

Scannez le nouveau QR code sur le même Wi-Fi. Ne désinstallez pas Expo Go ; `--clear` ne supprime pas vos données SQLite.

1. Reprenez une séance et saisissez charge, répétitions et RIR réels **sans valider**.
2. Touchez le nom de l’exercice dans l’encadré bleu : la bonne fiche doit s’ouvrir directement, sans menu. Vérifiez Description, Conseils et Alternatives.
3. Revenez avec la flèche de retour ou **Revenir à la séance** : même série, mêmes trois valeurs non validées et mêmes objectifs. Aucun résultat n’a été enregistré.
4. Recommencez en touchant le groupe musculaire, l’icône ou le bas de l’encadré. Essayez des doubles appuis rapides : une seule fiche doit s’ouvrir, sans empilement de doublons.
5. Depuis Alternatives, consultez une autre fiche puis revenez sans remplacer. La saisie de l’exercice initial doit rester intacte.
6. Si vous souhaitez réellement remplacer, confirmez **Remplacer pour cette séance**. Le remplaçant utilise sa vraie identité et son mode de charge. Comme avant, ses champs réels sont vides pour éviter de lui attribuer la saisie précédente. Annuler ne doit rien modifier.
7. Vérifiez le défilement vertical en commençant un mouvement sur l’encadré, le clavier numérique ouvert, et si possible VoiceOver (« Voir la fiche de … »). Le menu « … » conserve ses autres actions, sans l’entrée redondante de fiche.
8. Validez seulement une vraie série si souhaité : repos, pause/reprise, dépassement et passage manuel doivent fonctionner comme avant. Vérifiez aussi les swipes Accueil ↔ Musculation.

La conservation des champs concerne la consultation et son retour pendant l’utilisation de l’app. Une fermeture complète peut perdre une saisie non validée, comme avant ; les performances validées restent enregistrées. Les tests Linux ne prouvent pas le comportement tactile natif : ce correctif attend votre retour iPhone.
