# M4A — Audit réel de la carte musculaire 3D

## État de la livraison du 18 octobre 2026

**L’accès officiel BodyParts3D est débloqué et l’archive a été intégralement inspectée. L’intégration du prototype reste suspendue au contrôle qualité du modèle.** Les vrais rendus ne correspondent pas au mannequin athlétique de référence. Aucun écran 3D n’est présenté comme prêt à tester dans Logbook.

Reprise depuis `96fa0e9` sur `feat/m4a-prototype-carte-musculaire-3d`, [PR #11](https://github.com/mkfreyer/logbook/pull/11) en brouillon, base M3.4C `feat/m34c-fiches-exercices` / `7c2aa5c`. Aucune fusion. SQLite reste v8 ; aucune donnée, migration, dépendance ou fonction de l’application n’est modifiée. M4B n’est pas commencé.

**Orientation validée le 18 octobre : recherche d’une nouvelle base, sans reconstruction de BodyParts3D.** La [comparaison des alternatives](M4A_CHOIX_MODELE.md) étudie MakeHuman/MPFB et des modèles existants sous licence compatible. Les 2–3 meilleurs candidats doivent être rendus en entier, face/trois quarts/dos avec les mêmes réglages, puis soumis au choix utilisateur avant toute intégration. La reprise depuis `1da5ba6` a restauré et vérifié la sauvegarde ; l’accès Blender Studio fonctionne désormais (HTTP 200 et archive officielle complète). Les trois candidats MPFB / Blender réaliste / Blender stylisé sont comparés sous neuf vues. Le choix utilisateur reste attendu avant intégration. Le moteur interactif n’est pas commencé.

Lors de l’étude précédente, l’image jointe avait bien été consultée : corps masculin entier athlétique, muscles définis, surface satinée relativement lisse, gris bleuté sur bleu nuit. Elle sert de référence ; elle n’a pas été remplacée par une image générée. Elle n’est pas accessible dans la nouvelle reprise et doit être jointe à nouveau avant validation de la fidélité visuelle.

Le [guide de sauvegarde et reprise réseau](M4A_REPRISE_ENVIRONNEMENT.md) conserve
les sources, fichiers Blender et rendus de la comparaison avant redémarrage,
avec une archive autonome vérifiée et la prochaine tâche exacte.

## Résultat de l’audit

- Pages officielles de téléchargement et licence : **HTTP 200**. La politique active autorise désormais `dbarchive.biosciencedbc.jp`.
- Archive officielle `isa_BP3D_4.0_obj_99.zip` : **142 903 898 octets**, **2 234 OBJ**, tous les CRC vérifiés. Le transfert interrompu a été repris par HTTP 206 ; le fichier final est complet.
- Six tables IS-A/PART-OF, README et licence récupérés le 17 octobre. **CC BY 4.0** confirmée par la page officielle de licence.
- Identités de **62 sélections latéralisées / 86 OBJ** établies depuis les tables IS-A. Pectoraux en trois portions par côté ; deltoïdes et trapèzes également identifiés. Un trapèze n’est pas un grand dorsal.
- Aucune identité officielle exploitable pour le **grand dorsal** ou le **grand droit abdominal** dans les tables et en-têtes inspectés. Cela ne prouve pas l’absence de tout volume correspondant dans une enveloppe agrégée ; cela interdit de lui attribuer arbitrairement un mesh.
- Deux séries de vrais rendus, face / trois quarts / profil / dos : **peau entière**, puis **structures musculaires et osseuses** avec pectoraux orange. La soudure des positions exactement identiques et les normales lissées ne suffisent pas à obtenir la référence.

Les [rendus, mesures, identités et limites de l’audit](AUDIT_M4A_ANATOMIE.md) détaillent les constats. Les [empreintes et URLs exactes](m4a/bodyparts3d/provenance.json), le [manifeste anatomique](m4a/bodyparts3d/selection-candidate.json), le [résumé structurel](m4a/bodyparts3d/audit-summary.json) et les [scripts reproductibles](../tools/m4a/README.md) sont conservés. Les archives et OBJ sources restent hors du dépôt.

## Décision qualité avant intégration

La peau source est une enveloppe unique, peu définie musculairement. L’assemblage des structures internes expose le crâne, les os/tendons des mains et pieds, des séparations entre les éléments et une paroi abdominale différente de la référence. Ajouter la peau entière masque les muscles. Les deux assemblages vérifiés ne constituent pas le mannequin demandé.

La règle de M4A reste celle du plan initial : **si le nettoyage et la simplification ne permettent pas le résultat demandé, arrêter l’intégration, montrer les défauts constatés et demander une décision avant une autre source.** Un changement de matériau, une décimation ou un lissage ne crée ni les identités absentes ni la définition anatomique manquante. Une reconstruction artistique ou un autre modèle doit faire l’objet d’un choix explicite ; aucune source de remplacement n’a été intégrée.

Cette suspension n’est plus un problème réseau. Aucun GLB de production, budget mobile atteint, draw call ou FPS iPhone n’est annoncé.

## Contrat conservé pour le futur prototype

1. Première ouverture : uniquement le corps entier, rotation horizontale tactile 360°, pas de boutons de vue, pas de zoom/pan manuel.
2. Tap distinct d’un glissement, raycasting sur les surfaces visibles et identités anatomiques vérifiées. Un drag revenu à son point de départ, une annulation ou un deuxième doigt ne sélectionnent pas.
3. Sélection orange limitée au muscle ; interpolation fluide depuis l’orientation et la pose courantes. Un tap depuis le dos ne réinitialise pas la vue de face.
4. Fiche compacte accessible : nom, **Tonnage / Nombre de séries / Part du volume**, valeurs **« — »** en M4A. Aucune lecture ou écriture SQLite pour fabriquer des statistiques.
5. Fermeture animée vers le corps entier en conservant l’orientation ; nouvelle sélection et interruption d’animation sans saut.
6. Route `/muscle-map` isolée, accès depuis Musculation, aucune modification du pager, de `app/index.tsx`, du chronomètre ou de l’observateur sonore. Utiliser un conteneur fixe, pas le composant `Screen` à ScrollView.
7. Géométrie, HTML et moteur embarqués, sans CDN. Attribution consultable depuis À propos une fois un asset effectivement intégré.
8. Focus + AppState, rendu à la demande, chargements tardifs invalidés, pertes de contexte/processus gérées et ressources GPU libérées.

[Three.js dans une WebView locale reste le candidat documenté](AUDIT_M4A_MOTEUR_3D.md), à éprouver avec un asset approuvé. Aucune compatibilité de rendu, mesure mémoire ou fluidité dans Expo Go sur iPhone n’est encore établie.

## Vérifications de cette reprise

- Taille, SHA-256 et CRC de toute l’archive ; analyse réelle des **2 234 OBJ** : indices, valeurs finies, triangles, dégénérescences, bornes et associations aux tables.
- Contrôle topologique distinct des coutures dues aux sommets dupliqués ; métriques précises et limites dans l’audit.
- Relecture indépendante des identités pectoraux/deltoïdes/trapèzes, des côtés et des différences entre IS-A et PART-OF.
- Rendus Blender 4.3.2 calculés à partir des vrais OBJ et inspectés visuellement ; ce sont des preuves d’audit, pas des captures d’un prototype intégré.
- Régénération du manifeste et du résumé structurel ; validation de la syntaxe des scripts et du diff documentaire. La CI de la PR vérifie la base applicative inchangée sur le commit publié.

Les **535 tests**, TypeScript, export iOS et contrôle Metro documentés dans `96fa0e9` concernaient la préparation précédente. Ils ne deviennent pas une validation 3D et ne sont pas présentés comme réexécutés localement lors de cette reprise.

Après choix du modèle : tests du vrai GLB, raycasting face/profil/dos, gestes, caméra, erreurs/réessai, cycle de vie et chargements tardifs ; suite applicative complète, TypeScript, export iOS et CI ; puis essais réels iPhone (visuel, tactile, mode avion après chargement, arrière-plan, réouvertures et repos pendant entraînement). Ces validations du prototype restent **à faire**.

## Consulter la branche

```powershell
git fetch origin
git switch feat/m4a-prototype-carte-musculaire-3d
git pull --ff-only origin feat/m4a-prototype-carte-musculaire-3d
```

Cette livraison ajoute le dossier d’audit, pas une carte à ouvrir sur l’iPhone. Aucun effacement de données ou réinstallation d’Expo Go n’est nécessaire. La PR reste en brouillon, empilée sur M3.4C ; ne fusionner aucun parent ni M4A sans autorisation.
