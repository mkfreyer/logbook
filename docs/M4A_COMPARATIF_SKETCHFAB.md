# M4A — Étude comparative des deux pistes Sketchfab

**Recommandation : « Aucun des deux » comme base validée pour Logbook à cette étape.**

B ne fournit pas la séparation musculaire recherchée selon la description de son
auteur. A est la piste à contrôler en priorité pour son orientation de basemesh
stylisé et ses variantes de résolution, mais son téléchargement Sketchfab, sa
licence exacte et la structure du mannequin du milieu restent non vérifiés.
Aucun achat n'est effectué avec le budget de **0 €**. L'utilisateur a confirmé ne disposer **d'aucune licence ni copie existante**
pour ces deux modèles.

**Limite majeure : cette livraison est une étude documentaire technique, avec
références visuelles, et non une inspection de fichiers ou un audit visuel complet
des deux modèles.** Les fiches directes, API et viewers Sketchfab n'ont pas pu être
ouverts depuis cet environnement. Aucun GLB/FBX/OBJ n'a été acquis, aucun modèle
n'a été rendu localement et aucune sélection musculaire n'a été testée. Les
inconnues sont conservées comme telles dans le tableau ci-dessous.

## Modèles et sources

- **A — mannequin du milieu uniquement :** [3 male Power Body Types Highpoly Lowpoly](https://sketchfab.com/3d-models/3-male-power-body-types-highpoly-lowpoly-31f1e665ed684f4eabc125788d616cf3),
  UID `31f1e665ed684f4eabc125788d616cf3`.
- **B :** [Écorché Male Musclenames Anatomy, Chris Fischer](https://sketchfab.com/3d-models/ecorche-male-musclenames-anatomy-33162ec759e04d2985dbbdf4ec908d66),
  UID `33162ec759e04d2985dbbdf4ec908d66`.

Les [sources et leur mode d'accès](m4a/sketchfab-study/sources.json), les
[extraits courts déterminants](m4a/sketchfab-study/EXTRAITS.md), les
[métadonnées retenues](m4a/sketchfab-study/metadata.json), le
[journal des accès](m4a/sketchfab-study/access-log.json) et les
[liens des aperçus officiels](m4a/sketchfab-study/VISUELS.md) sont conservés.
Consultation : **20 octobre 2026**, contexte Europe/Paris. Certains extraits
proviennent d'index de recherche plus anciens : ils ne certifient pas l'état
instantané d'une offre ou d'un fichier téléchargeable.

Dans le rapport, « annoncé » désigne une information du vendeur ; « non vérifié »
signifie qu'aucune observation de fichier ne permet de conclure. Une appréciation
du potentiel futur n'est pas une validation du modèle.

## Comparaison technique

| Point à vérifier | A — mannequin du milieu | B — écorché nommé |
| --- | --- | --- |
| Téléchargement réel pendant l'étude | **Non réalisé.** Statut du téléchargement officiel Sketchfab inconnu. Une offre commerciale de même intitulé est trouvée chez Vincent Freelancer [S1]. | **Non réalisé.** L'auteur renvoie vers une acquisition commerciale [S2, S3]. Aucune acquisition à budget nul démontrée. |
| Licence du fichier précis | Licence Sketchfab **non vérifiée**. Ne pas lui attribuer une licence CC par analogie avec une autre publication. | Fiche indexée historiquement commerciale ; conditions actuelles à choisir dans la boutique officielle. Aucun droit acquis ici. |
| Offre commerciale consultée | Standard **19,99 USD**, Extended **199 USD** [S1]. Correspondance du contenu binaire avec l'UID non contrôlée. | Standard **15 USD**, Extended **150 USD** pour l'offre mâle [S3]. |
| Formats annoncés par l'auteur | **FBX** lowpoly, highpoly et décimé ; **ZPR/ZTL** [S1]. Aucun GLB/OBJ/BLEND confirmé pour ce téléchargement. | **OBJ**, avec variante non triangulée [S3] ; la description du bundle ajoute highpoly en quads, version décimée et UV [S4]. Aucun GLB/FBX/BLEND confirmé par ces sources officielles. |
| Triangles / sommets | **Inconnus**, pour le pack comme pour le mannequin du milieu. Ne pas diviser un éventuel total de scène par trois. | Fiche Sketchfab indexée : **environ 664,3 k triangles / 332,3 k sommets** [S2]. Compteurs affichés arrondis, non recomptés. |
| Poids | Archives annoncées : **330 + 140 + 330 + 1,1 Mo** [S1]. Aucune attribution fiable du fichier `m2` au mannequin du milieu. Taille du GLB futur inconnue. | Archive mâle annoncée : **190 Mo** [S3]. Poids du modèle runtime et des textures inconnu ; cette archive ne constitue pas un budget mobile. |
| Topologie / mesh | UV et topologie propre revendiqués par le vendeur [S1] ; aucun contrôle de quads, normales, îlots ou intersections. | Apparence anatomique documentée et plusieurs résolutions annoncées ; aucune vérification de manifold, d'îlots, de normales ou d'intersections. |
| Muscles séparés | **Non démontré.** Ni la notion de basemesh ni la présence de trois corps n'impliquent des muscles indépendants. | **Non selon l'auteur du bundle** : un objet OBJ et une texture de couleurs par corps, sans division en muscles [S4]. Nombre réel d'îlots non mesuré. |
| Noms exploitables | Aucun inventaire de noms de muscles, objets, matériaux ou groupes vérifié. | Abréviations documentées par une légende [S5]. Pas d'identifiants de muscles indépendants démontrés dans un fichier. |
| Sélection propre d'un groupe | À démontrer ; segmentation artistique probablement nécessaire si le corps est une enveloppe continue. | Le nom peint et la couleur ne suffisent pas à une sélection par objet. Il reste à construire une correspondance de régions ou une segmentation. |
| Surbrillance orange | Colorer le modèle entier est conceptuellement simple ; surligner seulement un muscle exige des régions ou pièces fiables, absentes de l'audit. | Même limite. Remplacer la texture par un matériau bleu/orange ne crée pas de limites musculaires sélectionnables. |
| iPhone / WebView futur | Variante lowpoly intéressante **si** sa densité, ses matériaux et son export sont confirmés. Aucune fluidité mesurée. | Charge géométrique notable dans la vue indexée ; adaptation/LOD et contrôle des textures à prévoir. Aucune fluidité mesurée. |
| Premium / fitness | Piste de basemesh stylisé à évaluer, sans validation visuelle du mannequin central. | Orientation pédagogique anatomique explicite ; intérêt de référence, mais mise en scène et annotations à adapter au langage fitness. |

## Ce que les noms de B prouvent réellement

La page du bundle publiée par Chris Fischer contient cette précision :
**“they are not split into different muscles”** [S4]. Elle décrit le produit
mâle/femelle de la même collection, pas une analyse de l'OBJ que nous aurions
ouvert. C'est une preuve documentaire forte contre l'hypothèse « achat = muscles
déjà séparés », tout en laissant la version exacte du fichier à contrôler.

La [légende de l'auteur][S5] associe notamment PM au grand pectoral, BB au biceps,
D aux deltoïdes et T aux triceps. Cette nomenclature aide un humain à lire la
surface. Elle ne donne pas une liste de nœuds glTF, des groupes OBJ, des sous-meshes
ou un mapping de triangles utilisable dans une application.

Inversement, un seul objet 3D peut contenir plusieurs îlots. Le nombre d'objets,
pris isolément, ne prouverait donc pas l'absence de parties séparables. Ici,
l'information déterminante est la déclaration de l'auteur ; la structure réelle
et les éventuels groupes internes restent non inspectés.

## Licences et possibilité d'usage dans Logbook

Les deux boutiques proposent des licences commerciales Standard et Extended.
Les encarts affichent un plafond de 2 000 ventes / 20 000 vues pour la Standard,
et une étendue sans ces plafonds pour l'Extended. Les conditions liées précisent
le périmètre commercial et les limites de partage [S6]. L'application exacte des
seuils à une app gratuite, à abonnement ou très distribuée reste à établir pour
le contrat retenu. Une licence « royalty free » n'est pas synonyme de gratuité
ou de libre redistribution du modèle source.

Il faut distinguer deux questions pour A : les conditions de son **pack vendu**
sont consultables ; celles du **téléchargement Sketchfab exact** ne l'ont pas été.
Une liste de tags indexée fait apparaître le titre près de boutons de téléchargement,
mais son extraction linéaire mélange des cartes : elle ne prouve ni qu'un bouton
vise A, ni qu'il est gratuit, ni quelle licence l'accompagne.

Pour B, l'extrait Sketchfab affiche aussi un tag **NoAI** [S2]. Ce tag ne remplace
pas la licence commerciale. L'étude n'a acquis ni traité son fichier géométrique
comme entrée de génération ; elle consulte des descriptions publiques.

Les fichiers d'un produit commercial ne seraient pas automatiquement publiables
comme assets autonomes dans un dépôt ouvert. Les permissions de distribution
avec l'app et de partage entre collaborateurs doivent venir du contrat acquis
[S6]. Aucun fichier propriétaire n'est ajouté à cette PR. Aucun achat, compte
créé, message envoyé à un vendeur ou service payant n'a été utilisé.

Le lien « nouveaux termes 2025 » de la page EULA mène à des conditions générales
du site [S7] : il n'identifie pas, à lui seul, la licence effectivement accordée
lors d'un achat. L'étude documente les offres observées, sans prétendre avoir
vérifié un contrat d'acquisition qui n'existe pas dans ce travail.

## Comparaison visuelle : potentiel et limites de l'observation

**Aucun score visuel définitif n'est attribué.** Les URL des galeries officielles
sont fournies dans [VISUELS.md](m4a/sketchfab-study/VISUELS.md), mais aucun viewer
360°, wireframe, gros plan ni test local à 390 px n'a pu être inspecté. Il n'y a
pas de captures fabriquées, de rendu simulant les modèles ni de comparaison
présentée comme ayant un matériau et un éclairage communs.

**Pour A**, la description commerciale situe le pack dans le stylisé/fantasy.
Ce positionnement peut convenir à une identité fitness, mais il ne permet pas de
juger la silhouette centrale demandée : degré de musculature, lisibilité du dos,
attaches sous les épaules, mains et visage restent à examiner. Les noms de variantes
ne prouvent pas leur ordre dans le viewer ; le mannequin du milieu n'est pas
identifié d'office comme un fichier ou une variante précise. Les incohérences du
catalogue — annonce de quatre types alors que trois sont listés, et note générique
sur des vêtements — rendent particulièrement nécessaire une vérification des
fichiers avant de promettre une topologie ou un contenu [S1].

**Pour B**, les abréviations anatomiques et la légende détaillée privilégient la
lecture pédagogique. C'est utile pour identifier des structures, mais la lecture
de texte sur un corps réduit à la taille d'un écran mobile risque de charger
l'image. Une palette unifiée pourrait changer l'impression sans corriger la
segmentation. Un écorché détaillé peut rester trop médical pour l'expérience
premium fitness recherchée ; cette appréciation doit être confirmée sur les
vues réelles. Aucune exactitude médicale n'est certifiée par cette étude.

| Risque fort | A | B |
| --- | --- | --- |
| Trop bodybuildé / trop peu musclé | Indéterminé pour le mannequin central ; ne pas extrapoler aux trois corps. | Une musculature documentée ne valide pas à elle seule les proportions fitness. |
| Trop médical | Positionnement stylisé annoncé, donc risque a priori moindre ; à confirmer visuellement. | Risque plus fort lié à la nomenclature et à la vocation d'étude anatomique. |
| Trop lourd | Impossible à conclure sans le lowpoly précis et ses textures. | Densité affichée importante ; coût runtime réel inconnu. |
| Découpe / nettoyage complexes | Séparation non prouvée ; risque de revenir à une découpe manuelle d'enveloppe. | L'absence de séparation annoncée maintient ce travail ; le nom peint ne l'évite pas. |
| Licence bloquante | Téléchargement exact non vérifié ; pack payant identifié. | Offre payante identifiée ; aucune acquisition couverte par le budget actuel démontrée. |

## Faisabilité mobile et sélection future

Un FBX ou OBJ peut être converti en glTF avec un outil gratuit tel que Blender.
Cela rend une voie technique plausible, mais n'optimise pas automatiquement le
maillage et ne transforme pas des couleurs en muscles indépendants. Aucun export
ou développement de cette nature n'est réalisé dans l'étude.

À titre de **calcul hypothétique**, les compteurs arrondis de B donneraient
environ **17,7 Mio** pour positions, normales et UV en float32 plus indices en
uint32, avant textures, doublons de coutures, allocations moteur et buffers CPU/GPU.
Ce n'est ni la taille de son OBJ/GLB, ni une mesure de mémoire réelle. Une archive
de 190 Mo et un compteur de triangles ne suffisent pas à conclure à l'impossibilité
sur iPhone ; inversement, la présence d'un viewer web ne prouve pas une expérience
mobile satisfaisante.

L'obstacle fonctionnel prioritaire est la correspondance entre le point touché
et le groupe musculaire. B n'apporte pas les objets musculaires recherchés ; A ne
les démontre pas. Réduire des polygones ou recolorer en orange ne résout pas ce
problème. Le futur travail de segmentation reste donc substantiel ou incertain
sur les deux pistes.

## Décision et suite limitée

**Choix explicite : « Aucun des deux », en l'état des preuves et du budget.**

- **B n'est pas recommandé comme raccourci vers la carte interactive.** Son intérêt
  anatomique de référence ne compense pas l'absence annoncée de pièces séparées,
  la densité affichée et l'acquisition commerciale nécessaire à la voie identifiée.
- **A est la première piste à réexaminer si un fichier officiel et une licence
  exploitable sont disponibles.** Son offre de résolutions est un avantage potentiel,
  mais le mannequin central n'a pas été audité. Ce n'est pas un choix d'achat ni une
  validation d'intégration.

Le verdict pourrait évoluer après confirmation d'un accès légal déjà détenu et
contrôle de la structure réelle. La [liste précise des vérifications restantes](m4a/sketchfab-study/A_VERIFIER.md)
est préparée pour cette éventualité. Rien n'est lancé automatiquement après la PR.

Cette branche contient uniquement l'analyse et ses métadonnées. **Aucune fusion,
modification d'une PR existante, intégration, SQLite, M3.x, M4B ou reconstruction
expérimentale. Aucun Astra Ultra. Arrêt après publication pour validation.**

[S1]: https://vincentpage.artstation.com/store/lrMM8/3-male-power-body-types-highpoly-lowpoly-included-man-base-anatomy-young-girl-zbursh-doll-highpoly-anatomy-human-cartoon-male-female-torso-head-body-foot-hand-highpoly-basemesh-young-anatomy-semi-realistic-character
[S2]: https://sketchfab.com/3d-models/ecorche-male-musclenames-anatomy-33162ec759e04d2985dbbdf4ec908d66
[S3]: https://chrisfischer.artstation.com/store/XKBG1/ecorche-musclenames-male-anatomy
[S4]: https://chrisfischer.gumroad.com/l/fgxyho
[S5]: https://chrisfischer.artstation.com/pages/musclechart
[S6]: https://www.artstation.com/marketplace-product-eula
[S7]: https://cdn2.unrealengine.com/artstation-terms-of-service-eu-65335878bd2c.pdf
