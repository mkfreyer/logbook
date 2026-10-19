# Groupes retenus pour l’exploration BodyParts3D fitness

**15 familles / 30 zones latéralisées / 74 OBJ musculaires identifiés.**
La peau de soutien `FJ2810` est une 75e source OBJ, non comptée comme muscle.
Les IDs 1–30 sont des régions artistiques provisoires, pas des identifiants FMA.
L’ID 0 désigne le soutien non assigné, notamment tête, mains et pieds.

| Famille | ID gauche / droit | OBJ retenus, deux côtés | Origine |
| --- | --- | ---: | --- |
| Pectoraux | 1 / 2 | 6 | BodyParts3D, identité vérifiée dans l’audit |
| Deltoïdes | 3 / 4 | 6 | BodyParts3D, identité vérifiée dans l’audit |
| Biceps | 5 / 6 | 4 | BodyParts3D, identité vérifiée dans l’audit |
| Triceps | 7 / 8 | 6 | BodyParts3D, identité vérifiée dans l’audit |
| Avant-bras | 9 / 10 | 14 | BodyParts3D, identité vérifiée dans l’audit |
| Trapèzes | 11 / 12 | 6 | BodyParts3D, identité vérifiée dans l’audit |
| Grands dorsaux | 13 / 14 | 0 | **Complément artistique original, identité source non vérifiée** |
| Grands droits abdominaux | 15 / 16 | 0 | **Complément artistique original, identité source non vérifiée** |
| Obliques externes | 17 / 18 | 2 | BodyParts3D, identité vérifiée dans l’audit |
| Fessiers | 19 / 20 | 4 | BodyParts3D, identité vérifiée dans l’audit |
| Quadriceps | 21 / 22 | 6 | BodyParts3D, identité vérifiée dans l’audit |
| Ischio-jambiers | 23 / 24 | 8 | BodyParts3D, identité vérifiée dans l’audit |
| Mollets | 25 / 26 | 6 | BodyParts3D, identité vérifiée dans l’audit |
| Adducteurs | 27 / 28 | 4 | BodyParts3D, identité vérifiée dans l’audit |
| Tibial antérieur | 29 / 30 | 2 | BodyParts3D, identité vérifiée dans l’audit |

Les correspondances FMA/BP/FJ et lignes des tables sont conservées intégralement
dans [groups.json](groups.json). Aucune identité de grand dorsal ou de grand droit
absent du manifeste audité n’a été inventée. Ces quatre volumes complémentaires
servent uniquement à essayer une silhouette ; ils ne démontrent pas une anatomie
médicale correcte.

Regroupements volontaires : plusieurs fléchisseurs/extenseurs sont réunis en une
zone avant-bras par côté ; les portions des pectoraux/deltoïdes/trapèzes sont
regroupées ; le quadriceps retient droit fémoral, vaste latéral et vaste médial, sans
conserver le vaste intermédiaire profond ; grand et moyen fessier partagent une zone. Les adducteurs et le
tibial antérieur complètent les 13 familles demandées pour couvrir la lecture
médiale de cuisse et antérieure de jambe. Les détails profonds, os, nerfs, organes
et tendons isolés ne sont pas conservés comme objets sélectionnables.

Le transfert d’ID repose sur la proximité des surfaces sources après reconstruction.
Les limites sont irrégulières et doivent être redessinées avant toute sélection de
production. Une face a un seul ID ; cela ne garantit pas une frontière pertinente.
La présence des 30 IDs ne signifie pas que les 30 régions soient toutes lisibles
ou correctement délimitées. Aucun tonnage ni calcul de volume d’entraînement
n’est branché.
