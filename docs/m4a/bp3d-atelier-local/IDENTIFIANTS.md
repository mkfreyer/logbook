# Identifiants anatomiques — atelier local

Trois identités sélectionnables, neuf portions anatomiques indépendantes.
Le suffixe `M` est conservé tel quel ; la latéralité vient des tables officielles,
pas d’une supposition sur le nom. +X = gauche anatomique, −Y = avant, +Z = haut.

| Muscle logique (`muscle_id`) | Portion | OBJ | FMA | Représentation BP | Triangles | Îlots après soudure exacte |
| --- | --- | --- | --- | --- | ---: | ---: |
| `pectoralis-major-left` | clavicular part of left pectoralis major | `FJ1447M` | `FMA34691` | `BP9095` | 1 846 | 13 |
| `pectoralis-major-left` | sternocostal part of left pectoralis major | `FJ1464M` | `FMA79980` | `BP8323` | 7 114 | 7 |
| `pectoralis-major-left` | abdominal part of left pectoralis major | `FJ1446M` | `FMA45875` | `BP7862` | 1 536 | 3 |
| `pectoralis-major-right` | clavicular part of right pectoralis major | `FJ1447` | `FMA34690` | `BP5582` | 1 846 | 13 |
| `pectoralis-major-right` | sternocostal part of right pectoralis major | `FJ1464` | `FMA79979` | `BP5613` | 7 114 | 7 |
| `pectoralis-major-right` | abdominal part of right pectoralis major | `FJ1446` | `FMA45874` | `BP5615` | 1 536 | 3 |
| `deltoid-left` | clavicular part of left deltoid | `FJ1468M` | `FMA34681` | `BP8259` | 2 206 | 1 |
| `deltoid-left` | acromial part of left deltoid | `FJ1467M` | `FMA34683` | `BP9075` | 1 300 | 4 |
| `deltoid-left` | spinal part of left deltoid | `FJ1513M` | `FMA34685` | `BP8151` | 1 900 | 20 |

Total local : **26 398 triangles musculaires**. Les neuf objets sont conservés,
y compris les îlots sources minimes. Les groupes `DIAG_ILOT_…` permettent de les
inspecter sans suppression. Un objet et un muscle logique ne sont pas synonymes.

## Repères osseux en fil de fer

| Nom source | OBJ | FMA | Représentation BP |
| --- | --- | --- | --- |
| manubrium | `FJ3290` | `FMA7486` | `BP8562` |
| body of sternum | `FJ3178` | `FMA7487` | `BP8989` |
| right clavicle | `FJ3362` | `FMA13322` | `BP9271` |
| left clavicle | `FJ3237` | `FMA13323` | `BP8841` |
| left scapula | `FJ3279` | `FMA13396` | `BP9121` |
| left humerus | `FJ3262` | `FMA23131` | `BP9191` |

La scène conserve les positions anatomiques sources, après transformation de
cadrage uniforme commune. Les os sont exclus du rendu par défaut. Les lignes
exactes des deux tables officielles et SHA-256 de chaque OBJ sont consignés dans
[identites.json](identites.json), également embarqué dans le `.blend` et le ZIP.

Les noms de portions renseignent leurs origines générales, pas les coordonnées
exactes d’insertion ou la direction des fibres. Ces dernières restent à vérifier
manuellement. Les six Empty de [raccords-a-reprendre.json](raccords-a-reprendre.json)
sont des repères géométriques approximatifs ; aucun n’est une attache validée.

Les scènes orange utilisent le `muscle_id` sur les objets entiers. Les trois
portions du muscle choisi sont activées ensemble. La géométrie disjointe d’origine
n’est pas corrigée par cette coloration ; aucune sélection tactile n’est développée.
