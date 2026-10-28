"""Source-only fitness inventory. No exercise linking, database read or writes."""
import json,re,collections
from pathlib import Path
from glb_io import sha
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/m4c/meshy-bras-prototype'
catalog=ROOT/'src/db/exerciseCatalog.ts';text=catalog.read_text();counts=collections.Counter(re.findall(r"muscleGroup: '([^']+)'",text))
rows=[
('Bras','biceps.{side}','Biceps brachial','Face antérieure du bras, sous le deltoïde, avant le coude.','Bonne pour le ventre global ; chefs long/court non séparables de façon fiable.','POC'),
('Bras','triceps.{side}','Triceps brachial','Face postérieure et externe du bras, vers le tendon du coude.','Bonne pour le groupe ; portion médiale profonde et trois chefs non isolés.','POC'),
('Bras','brachialis.{side}','Brachial','Bandes latérales/distales entre biceps et triceps, au-dessus du coude.','Moyenne : bande visible, limite exacte avec le biceps peu marquée.','Ultérieur'),
('Avant-bras','brachioradialis.{side}','Brachio-radial','Relief externe proximal de l’avant-bras, côté pouce.','Bonne pour le relief global ; raccord au coude à vérifier en rotation.','Ultérieur'),
('Avant-bras','forearm.{side}.flexors','Fléchisseurs superficiels de l’avant-bras','Face palmaire/antérieure, du coude au poignet.','Groupe fonctionnel : les muscles individuels et tendons ne sont pas tous distincts.','Ultérieur'),
('Avant-bras','forearm.{side}.extensors','Extenseurs superficiels de l’avant-bras','Face dorsale/postérieure, du coude au poignet.','Groupe fonctionnel : ne pas inventer une séparation de chaque tendon.','Ultérieur'),
('Dos','trapezius.{side}.upper','Trapèze supérieur','Du cou vers le sommet des épaules.','Volume lisible, origine cervicale simplifiée ; ne pas altérer le cou validé.','Priorité suivante possible'),
('Dos','trapezius.{side}.middle','Trapèze moyen','Haut du dos, entre rachis et omoplate.','Moyenne : subdivisions du trapèze peu matérialisées, frontière fonctionnelle à valider.','Ultérieur'),
('Dos','trapezius.{side}.lower','Trapèze inférieur','Triangle inférieur du haut du dos vers le rachis thoracique.','Moyenne : transition vers les dorsaux graduelle.','Ultérieur'),
('Dos','latissimus.{side}','Grand dorsal','Large aile latérale et inférieure du dos, jusqu’au pli axillaire postérieur.','Bonne pour l’aile ; raccord grand rond/triceps plus ambigu.','Priorité suivante possible'),
('Dos','teres_major.{side}','Grand rond','Sous le deltoïde postérieur, bord externe de l’omoplate.','Partiel : très proche des dorsaux et du triceps ; bornes à contrôler.','Ultérieur'),
('Dos','infraspinatus.{side}','Infra-épineux','Partie postérieure de l’omoplate, sous son épine.','Moyenne/faible : relief scapulaire stylisé, zone partiellement masquée par le deltoïde.','Optionnel'),
('Dos','erector_spinae.{side}','Érecteurs du rachis','Colonnes lombaires de part et d’autre de la colonne.','Moyenne : groupe superficiel, pas de subdivision multifides/longissimus.','Ultérieur'),
('Abdomen','rectus_abdominis.{side}','Grand droit de l’abdomen','De part et d’autre de la ligne médiane abdominale.','Bonne : tablettes lisibles ; une région par côté, pas un muscle par tablette.','Priorité suivante possible'),
('Abdomen','obliques.{side}.external','Oblique externe','Flancs, sous les côtes et vers le bassin.','Bonne globalement ; limites basses simplifiées par la finition du bassin.','Ultérieur'),
('Abdomen','serratus_anterior.{side}','Dentelé antérieur','Digitations latérales du thorax, sous les pectoraux.','Reliefs visibles, plusieurs digitations regroupées ; respecter les pectoraux validés.','Ultérieur'),
('Bassin et fessiers','gluteus_maximus.{side}','Grand fessier','Masse postérieure principale de la fesse.','Bonne globalement ; jonction ischio-jambiers progressive.','Priorité suivante possible'),
('Bassin et fessiers','gluteus_medius.{side}','Moyen fessier superficiel','Partie supérieure/externe de la hanche.','Partiellement visible ; ne représenter que la surface exposée.','Ultérieur'),
('Bassin et fessiers','tensor_fasciae_latae.{side}','Tenseur du fascia lata','Petite région antéro-externe de la hanche.','Faible/moyenne : relief proche du quadriceps et du fessier, à confirmer.','Optionnel'),
('Cuisses','quadriceps.{side}.rectus_femoris','Droit fémoral','Ventre central de la face antérieure de cuisse.','Bonne : volume principal lisible.','Priorité suivante possible'),
('Cuisses','quadriceps.{side}.vastus_lateralis','Vaste latéral','Face antéro-externe de la cuisse.','Bonne : galbe latéral net, origine haute moins délimitée.','Ultérieur'),
('Cuisses','quadriceps.{side}.vastus_medialis','Vaste médial','Goutte au-dessus du bord interne du genou.','Bonne distalement ; raccord proximal plus progressif.','Ultérieur'),
('Cuisses','hamstrings.{side}.biceps_femoris','Biceps fémoral superficiel','Partie postéro-externe de la cuisse.','Bonne pour le territoire externe ; tendon bas à préserver neutre.','Priorité suivante possible'),
('Cuisses','hamstrings.{side}.semitendinosus','Semi-tendineux superficiel','Partie postéro-interne de la cuisse.','Moyenne : ne pas attribuer arbitrairement le semi-membraneux profond.','Ultérieur'),
('Cuisses','adductors.{side}','Adducteurs superficiels','Face interne de cuisse, sous le pli de l’aine.','Groupe : origine proximale volontairement simplifiée ; préserver l’aine validée.','Ultérieur'),
('Cuisses','gracilis.{side}','Gracile','Bande fine médiale de cuisse.','Faible : voisin des adducteurs, séparation non fiable partout.','Optionnel'),
('Cuisses','sartorius.{side}','Sartorius','Trajet diagonal de la hanche externe vers le genou interne.','Faible/moyenne : ne pas inventer un ruban là où le relief est absent.','Optionnel'),
('Jambes','gastrocnemius.{side}.medial','Gastrocnémien médial','Chef interne du mollet postérieur.','Bonne pour les grands galbes, raccord au tendon d’Achille simplifié.','Priorité suivante possible'),
('Jambes','gastrocnemius.{side}.lateral','Gastrocnémien latéral','Chef externe du mollet postérieur.','Bonne globalement ; séparation centrale à confirmer sous plusieurs angles.','Ultérieur'),
('Jambes','soleus.{side}','Soléaire superficiel exposé','Bords inférieurs/latéraux du mollet, sous les gastrocnémiens.','Partiel : seule la portion réellement exposée est sélectionnable.','Ultérieur'),
('Jambes','tibialis_anterior.{side}','Tibial antérieur','Face antéro-externe de la jambe, à côté du tibia.','Moyenne : territoire long lisible mais cheville/pied volontairement lissés.','Ultérieur'),
('Jambes','fibularis.{side}','Fibulaires superficiels','Bord externe de la jambe.','Faible/moyenne : groupe fonctionnel, long/court fibulaire non distingués.','Optionnel'),
('Cou — facultatif','neck.{side}.sternocleidomastoid','Sterno-cléido-mastoïdien','Bande oblique superficielle latérale du cou.','Zone simplifiée et validée esthétiquement ; intérêt fitness secondaire, pas de retouche prévue.','Optionnel')]
proposals=[]
for index,(group,pattern,name,location,limit,stage) in enumerate(rows):
    for j,side in enumerate(['left','right']):proposals.append({'codeProposed':9+index*2+j,'idProposed':pattern.format(side=side),'nameFrench':name+(' gauche' if side=='left' else ' droit'),'group':group,'location':location,'visibleLimits':limit,'stage':stage,'maskCreated':index<2})
assert len(proposals)==66 and len({p['idProposed'] for p in proposals})==len({p['codeProposed'] for p in proposals})==66
data={'baseCommit':'d552e23','catalogSource':'src/db/exerciseCatalog.ts','catalogSourceSha256':sha(catalog.read_bytes()),'initialExerciseCount':sum(counts.values()),'initialGroupCounts':dict(counts),
    'personalDatabaseRead':False,'exerciseToMuscleLinksCreated':False,'existingValidatedCodes':list(range(1,9)),
    'proposedRemainingZones':proposals,'onlyMasksCreatedInThisDelivery':[p['idProposed'] for p in proposals if p['maskCreated']],
    'excludedAsDeepOrNotRepresentable':['Petit pectoral','Transverse abdominal','Vaste intermédiaire','Rhomboïdes sous les trapèzes','Sous-scapulaire','Muscles faciaux','Muscles intrinsèques des mains/pieds'],
    'scope':'Main superficial fitness groups, not all anatomical muscles. Future IDs are proposals; no future masks or app mappings implemented.'}
(OUT/'inventory.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
lines=['# M4C — inventaire des principaux territoires superficiels restants','',
 'Base : `d552e23`, huit zones validées conservées. Cet inventaire propose **33 paires / 66 territoires** encore absents à cette base. Seuls les quatre biceps/triceps sont créés ici ; les 62 autres restent des propositions à examiner dans les lots suivants.','',
 'Le catalogue initial contient **15 exercices, huit familles** : '+', '.join(f'{k} ({v})' for k,v in counts.items())+'. Les catégories sont des textes libres, pas une nomenclature anatomique. Les exercices personnalisés de la base utilisateur ne sont ni lus ni modifiés. Aucun lien exercice→zone, coefficient de volume ou statistique n’est développé.','',
 'Les IDs 1–8 et leurs noms existants restent réservés. Les nouveaux IDs proposés ci-dessous sont distincts et tiennent dans un atlas L8 (maximum proposé : 74). Les codes futurs ne sont pas ajoutés au visualiseur.','']
last=None
for i,(group,pattern,name,location,limit,stage) in enumerate(rows):
    if group!=last:
        lines+=['## '+group,'','| Groupe / emplacement | IDs proposés gauche et droit | Lisibilité et limites |','| --- | --- | --- |'];last=group
    ids='`'+pattern.format(side='left')+'` / `'+pattern.format(side='right')+'`'
    lines.append(f'| **{name}** — {location} | {ids}<br>Codes {9+2*i} / {10+2*i} | {limit} **{stage}.** |')
    if i+1==len(rows) or rows[i+1][0]!=group:lines.append('')
lines+=['## Limites générales de la sculpture','',
 '- Les gros volumes sont exploitables pour une carte fitness. La sculpture Meshy reste stylisée : une frontière propre n’équivaut pas à une insertion anatomique chirurgicale. Les petites portions profondes ne doivent pas devenir des plaques superposées.','- Biceps et triceps sont proposés par groupe entier, sans inventer leurs deux/trois chefs. Les bandes du brachial et les avant-bras restent neutres dans ce POC.','- Les limites de certains muscles du dos, de la hanche et des avant-bras seront des approximations fonctionnelles. Les rhomboïdes, petit pectoral, transverse et vaste intermédiaire ne sont pas des régions superficielles indépendantes sur ce mannequin.','- La finition de l’aine, du cou et des pieds a volontairement simplifié des détails. Elle doit rester intacte ; les futurs masques devront s’arrêter sur les surfaces encore identifiables.','- Les tableaux décrivent des candidats et leurs difficultés, pas des masques déjà validés ni un engagement de découper chaque ligne séparément.','',
 'Données exploitables : [`inventory.json`](m4c/meshy-bras-prototype/inventory.json). **Arrêt après le prototype des quatre bras ; aucun autre groupe n’est segmenté dans cette livraison.**','']
(ROOT/'docs/M4C_INVENTAIRE_MUSCLES_SUPERFICIELS.md').write_text('\n'.join(lines))
print('INVENTORY_READY',sum(counts.values()),'EXERCISES;',len(proposals),'PROPOSED ZONES;',4,'MASKS ONLY',flush=True)
