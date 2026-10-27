# M4C / M4D-A — Six deltoïdes corrigés et ressources interactives synchronisées

Les nouvelles limites des six deltoïdes sont disponibles dans le visualiseur de la PR #18. La fonction de sélection validée sur iPhone au commit `268ea3e` est conservée ; seuls ses fichiers de données sont régénérés.

## Historique et commits

- Base anatomique et esthétique : Meshy `e45e5d8`, inchangée.
- Ancienne segmentation : `06fa665`, conservée avec tous ses fichiers.
- Correction M4C : **`6817b08caf12dbcde4d275befcbe8191bfc5642e`**, PR #17.
- Base interactive : `268ea3e`, PR #18.
- Synchronisation de la base M4C dans M4D : merge Git `149abcc`, sans fusion d’aucune Pull Request et sans réécriture de l’historique.
- Les ressources interactives et captures de cette livraison figurent dans le commit courant de la PR #18.

## Lecture des annotations

Les surfaces orange indiquaient les anciens masques et les traits jaunes les nouvelles limites. Les six régions sont recalculées ensemble avec des frontières communes. Les pectoraux restent identiques, y compris leurs franges de masque.

Les angles iPhone ont été reconstitués à partir des contours existants ; leurs paramètres exacts n’étaient pas disponibles. Les comparatifs avant/après utilisent strictement les mêmes caméras et éclairages.

**Limite importante à examiner : les trois pointes jaunes ne correspondent pas à la même insertion en 3D.** Elles sont raccordées vers une insertion commune sur la surface d’origine. Le compromis conserve une jonction unique ; il ne reproduit pas simultanément les trois pointes au pixel près (environ 63 px d’écart résiduel en antérieur/postérieur et 5 px en moyen). Le [rapport anatomique](M4C_DELTOIDES_REPERES_IPHONE.md) détaille cette interprétation et les guides projetés.

## Fichiers et intégration des données

- Sources : `docs/m4c/meshy-deltoides-reperes-iphone/` — six masques PNG corrigés, deux pectoraux préservés, atlas d’IDs, deux atlas RGBA, guides 3D, Blender éditable, GLB de contrôle et 20 rendus Blender.
- Générateur : `tools/m4d/build-selection.mjs` pointe sur ce nouveau dossier. Il reprend exactement l’atlas corrigé ; les anciens atlas historiques ne sont pas chargés par le visualiseur.
- Dérivé local : `assets/models/meshy-m4d-uv.glb`, **2 606 304 octets**, avec les positions, normales, UV et triangles validés, et le même matériau neutre.
- Atlas embarqué : `src/features/model3d/generated/selectionData.ts`, PNG L8 de **31 238 octets**, toujours 2048 × 2048.
- Bundle local régénéré : `src/features/model3d/generated/viewerBundle.ts`.
- Tests : témoins géométriques mis à jour ; le banc navigateur attend maintenant la fin de l’inertie avant de projeter les points de toucher. Cela empêche de calculer un pixel sous une caméra puis de le toucher après qu’elle a tourné. Ce changement concerne uniquement le test, pas le visualiseur.

Le code de sélection, les noms français, l’orange, la réinitialisation, les gestes et les boutons n’ont pas changé. Aucun nouveau triangle, aucune nouvelle dépendance. Coût de texture toujours voisin de **4 Mio CPU + 4 Mio GPU**, avec les mêmes allocations temporaires au décodage. Pas de mesure de performances du nouvel atlas sur un véritable iPhone à ce stade.

## Visuels et contrôles

- [Postérieur droit avant/après](m4c/meshy-deltoides-reperes-iphone/renders/comparatif-posterior.png)
- [Moyen droit avant/après](m4c/meshy-deltoides-reperes-iphone/renders/comparatif-lateral.png)
- [Antérieur droit avant/après](m4c/meshy-deltoides-reperes-iphone/renders/comparatif-anterior.png)
- [Deux épaules : face, dos, quatre vues trois quarts](m4c/meshy-deltoides-reperes-iphone/renders/planche-vues-anatomiques.png)
- [Six faisceaux séparés en Blender](m4c/meshy-deltoides-reperes-iphone/renders/planche-six-faisceaux.png)
- [Nouvelles sélections orange dans le visualiseur](m4d/selection-deltoides-corriges/planche-huit-selections.png)
- [Résultats du test tactile WebGL](m4d/selection-deltoides-corriges/browser-verification.json)
- [Régression des gestes et libération du moteur](m4d/selection-deltoides-corriges/viewer-regression.json)
- [Vérifications et journaux](m4d/selection-deltoides-corriges/verification.json)

Les captures WebGL sont de vrais touchers CDP dans Chromium/SwiftShader, viewport mobile 430 × 760. Elles ne sont pas des captures d’un nouvel essai iPhone ni de l’interface native complète. Les planches assemblent des captures et recadrages, sans repeindre les frontières.

Les contrôles M4C confirment huit IDs sans chevauchement, un composant par zone, aucun trou interne y compris dans l’union des deltoïdes, deux pectoraux identiques octet pour octet, géométrie et normales par triangle identiques au master, UV et indices inchangés. Le mannequin neutre Blender avant/après est identique pixel pour pixel.

Les programmes, séances, séries, chronomètre, historique, statistiques, paramètres et schéma SQLite v8 restent inchangés. Aucun développement de nouvelle fonctionnalité, orientation automatique, zoom automatique, carte thermique ou lien aux exercices.

## Test utilisateur

[Commandes PowerShell et points à vérifier sur iPhone](M4D_A_DELTOIDES_CORRIGES_IPHONE.md).

Les deux PR restent en brouillon. Aucune Pull Request fusionnée. Arrêt pour validation visuelle et nouveau test iPhone.

### Résultats de cette livraison

Cohérence Expo SDK 58, TypeScript, bundle et export JavaScript iOS : réussis. Suite complète : **551 tests réussis**. Les huit vrais touchers WebGL identifient les nouveaux masques ; changement direct, réinitialisation, surface neutre/fond, appui long et coexistence des gestes sont vérifiés. Le contrôle du visualiseur confirme rotation supérieure à 360°, pincement dans les deux sens, limites de zoom, déplacement vertical, Face, Vue générale, arrêt du rendu au repos et cinq cycles de fermeture/réouverture sans géométrie résiduelle. Aucune requête externe du visualiseur. Les journaux et empreintes sont fournis avec les captures.
