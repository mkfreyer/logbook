# Restauration exacte M4C — référence 06fa665

Les modifications anatomiques de `6817b08` sont annulées par un nouveau commit, sans réécriture d’historique. Les 64 fichiers ajoutés pour cette proposition rejetée sont retirés de la branche courante ; ils restent consultables dans l’ancien commit.

Les sources validées `docs/m4c/meshy-posterieurs-harmonises/` n’avaient pas été écrasées. Elles sont rétablies comme référence active et vérifiées **octet pour octet** contre `06fa665`, y compris :

- Les huit masques PNG (deux pectoraux et six deltoïdes).
- L’atlas `muscle-ids.png` et les deux atlas RGBA.
- Le Blender original, le GLB de contrôle, les correspondances de zones et les témoins de sélection.
- Tous les autres fichiers du dossier de référence.

Aucun nouveau dessin, lissage, guide, changement d’insertion ou traitement anatomique. Le master Meshy `e45e5d8` est inchangé, SHA-256 `421e593cad17f60d1c0c5e67707729fb88bbf69026795e22011ecc7d90b38959`. Les huit identifiants sont conservés.

## Confirmation visuelle

Quatre nouveaux rendus du **Blender original de 06fa665**, sans modification des textures ni de la géométrie, matériau et palette de contrôle enregistrés dans ce fichier :

- [Face](m4c/restauration-06fa665/renders/face.png)
- [Dos](m4c/restauration-06fa665/renders/dos.png)
- [Trois quarts arrière gauche](m4c/restauration-06fa665/renders/trois-quarts-gauche.png)
- [Trois quarts arrière droit](m4c/restauration-06fa665/renders/trois-quarts-droit.png)

Les couleurs servent uniquement au contrôle des zones. Les ressources sources ne sont pas réexportées ou réinterprétées : leur identité avec le commit demandé est vérifiée directement par comparaison binaire.

[Empreintes et comparaison de tous les fichiers](m4c/restauration-06fa665/verification.json) · [Caméras et empreintes des quatre rendus](m4c/restauration-06fa665/renders/render-metadata.json).

La restauration interactive de la PR #18 remet séparément les fichiers runtime et leurs liaisons à l’identique de `268ea3e`. La sélection tactile n’est pas supprimée. Les deux branches restent empilées et les deux PR restent en brouillon, sans fusion. Arrêt pour vérification utilisateur.
