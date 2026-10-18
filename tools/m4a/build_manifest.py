"""Read only official BodyParts3D 4.0 metadata; never infer an OBJ's anatomy."""
from pathlib import Path
from collections import defaultdict
import argparse,csv,json,hashlib
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--isa-dir',required=True,type=Path)
parser.add_argument('--partof-dir',required=True,type=Path)
parser.add_argument('--output-dir',required=True,type=Path)
args=parser.parse_args()
SOURCE=args.isa_dir;PARTOF=args.partof_dir;OUT=args.output_dir
OUT.mkdir(parents=True,exist_ok=True)
def read(path):
    with path.open() as f:
        return [(i,r) for i,r in enumerate(csv.DictReader(f,delimiter='\t'),2)]
p={r['concept id']:{'representation_id':r['representation id'],'name_en':r['en'],'parts_list_line':i} for i,r in read(SOURCE/'isa_parts_list_e.txt')}
e=defaultdict(list)
for i,r in read(SOURCE/'isa_element_parts.txt'):
    e[r['concept id']].append({'element_id':r['element file id'],'obj_filename':r['element file id']+'.obj','element_parts_line':i})
def concept(c):return {'concept_id':c,**p[c],'elements':e[c]}
# Every entry explicitly names the desired muscle and side in the official file.
# Components are unions of actual named parts, never bounding-box assignments.
groups=[
 ('pectoralis-major','Grand pectoral', ['FMA34690','FMA79979','FMA45874'],['FMA34691','FMA79980','FMA45875']),
 ('deltoid','Deltoïde',['FMA34680','FMA34682','FMA34684'],['FMA34681','FMA34683','FMA34685']),
 ('trapezius','Trapèze',['FMA33581','FMA33584','FMA33586'],['FMA33583','FMA33585','FMA33587']),
 ('biceps-brachii','Biceps brachial',['FMA37684','FMA37686'],['FMA37685','FMA37687']),
 ('triceps-brachii','Triceps brachial',['FMA37695','FMA37697','FMA37699'],['FMA37696','FMA37698','FMA37700']),
 ('external-oblique','Oblique externe',['FMA13336'],['FMA13337']),
 ('serratus-anterior','Dentelé antérieur',['FMA13398'],['FMA13399']),
 ('gluteus-maximus','Grand fessier',['FMA22328'],['FMA22329']),
 ('gluteus-medius','Moyen fessier',['FMA22330'],['FMA22331']),
 ('rectus-femoris','Droit fémoral',['FMA38928'],['FMA38929']),
 ('vastus-lateralis','Vaste latéral',['FMA38930'],['FMA38931']),
 ('vastus-medialis','Vaste médial',['FMA38932'],['FMA38933']),
 ('biceps-femoris','Biceps fémoral',['FMA45888','FMA45891'],['FMA45889','FMA45892']),
 ('semitendinosus','Semi-tendineux',['FMA22358'],['FMA22359']),
 ('semimembranosus','Semi-membraneux',['FMA22448'],['FMA22449']),
 ('gastrocnemius','Gastrocnémien',['FMA45957','FMA45960'],['FMA45958','FMA45961']),
 ('soleus','Soléaire',['FMA22558'],['FMA22559']),
 ('tibialis-anterior','Tibial antérieur',['FMA22544'],['FMA22545']),
 ('sartorius','Sartorius',['FMA22354'],['FMA22355']),
 ('tensor-fasciae-latae','Tenseur du fascia lata',['FMA22425'],['FMA22426']),
 ('adductor-longus','Long adducteur',['FMA22456'],['FMA22457']),
 ('gracilis','Gracile',['FMA43883'],['FMA43884']),
 ('brachioradialis','Brachio-radial',['FMA38486'],['FMA38487']),
 ('sternocleidomastoid','Sterno-cléido-mastoïdien',['FMA13408'],['FMA13409']),
 ('flexor-carpi-radialis','Fléchisseur radial du carpe',['FMA38460'],['FMA38461']),
 ('extensor-carpi-radialis-longus','Long extenseur radial du carpe',['FMA38495'],['FMA38496']),
 ('extensor-carpi-radialis-brevis','Court extenseur radial du carpe',['FMA38498'],['FMA38499']),
 ('extensor-carpi-ulnaris','Extenseur ulnaire du carpe',['FMA38507'],['FMA38508']),
 ('extensor-digitorum','Extenseur des doigts',['FMA38501'],['FMA38502']),
 ('fibularis-longus','Long fibulaire',['FMA22552'],['FMA22553']),
 ('extensor-digitorum-longus','Long extenseur des orteils',['FMA22548'],['FMA22549']),
]
selections=[];owner={}
for slug,fr,right,left in groups:
    for side,ids in [('right',right),('left',left)]:
        items=[concept(c) for c in ids]
        for item in items:
            assert side in item['name_en'],item
        elements=sorted({x['element_id'] for item in items for x in item['elements']})
        for item in elements:
            assert item not in owner,(item,owner.get(item),slug,side)
            owner[item]=slug+'-'+side
        selections.append({'id':slug+'-'+side,'group_id':slug,'side':side,'name_fr':fr+(' droit' if side=='right' else ' gauche'),'components':items,'element_ids':elements,'status':'metadata_identity_verified_not_approved_for_product'})
source_files={}
for prefix,folder in [('isa',SOURCE),('partof',PARTOF)]:
    for suffix in ['parts_list_e.txt','element_parts.txt','inclusion_relation_list.txt']:
        name=prefix+'_'+suffix;f=folder/name
        source_files[name]={'url':'https://dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/'+name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size}
broad_ids=['FMA5022','FMA10474','FMA32558','FMA85453']
broad=sorted({x['element_id'] for c in broad_ids for x in e[c]}|set(owner))
pe={r['element file id'] for _,r in read(PARTOF/'partof_element_parts.txt')};ie={x['element_id'] for a in e.values() for x in a}
manifest={'schema_version':1,'purpose':'Audit candidate only; no final geometric or visual approval','source_version':'BodyParts3D 4.0 / official LATEST download, 2026-10-17','source_files':source_files,'selection_candidates':selections,'skin':concept('FMA7163'),'audit_all_muscle_sources':[concept(c) for c in broad_ids],'audit_all_muscle_element_ids':broad,'missing_requested_identities':['latissimus dorsi','rectus abdominis'],'missing_identity_scope':'No occurrence in the six official IS-A/PART-OF names and inclusion tables; not yet proof of geometric absence. Never infer IDs from position or filename.','partof_elements_not_in_isa':sorted(pe-ie)}
(OUT/'selection-candidate.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(OUT/'candidate-surface-obj-ids.txt').write_text('\n'.join(sorted(owner))+'\n')
(OUT/'all-muscle-audit-obj-ids.txt').write_text('\n'.join(broad)+'\n')
(OUT/'skin-obj-ids.txt').write_text('FJ2810\n')
# Audit render support, derived from official identities rather than filenames.
# Keep this separate from the surface-candidate manifest: bones are not muscles.
bone_concepts=['FMA5018','FMA10483']
assert p['FMA5018']['name_en']=='bone organ',p['FMA5018']
assert p['FMA10483']['name_en']=='zone of bone organ',p['FMA10483']
bones=sorted({x['element_id'] for c in bone_concepts for x in e[c]})
skin={x['element_id'] for x in e['FMA7163']}
assert skin=={'FJ2810'},skin
(OUT/'bone-obj-ids.txt').write_text('\n'.join(bones)+'\n')
for filename,ids in [
    ('extraction-elements.json',sorted(set(broad)|skin)),
    ('bone-elements.json',bones),
    ('render-elements.json',sorted(set(broad)|skin|set(bones))),
]:
    payload={'element_ids':ids}
    if filename=='bone-elements.json':
        payload['source_concepts']=[concept(c) for c in bone_concepts]
    (OUT/filename).write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
with (OUT/'selection-components.tsv').open('w',newline='',encoding='utf-8') as f:
    w=csv.writer(f,delimiter='\t',lineterminator='\n');w.writerow(['selection_id','side','concept_id','representation_id','official_name','element_id','isa_element_parts_line'])
    for g in selections:
        for c in g['components']:
            for a in c['elements']:w.writerow([g['id'],g['side'],c['concept_id'],c['representation_id'],c['name_en'],a['element_id'],a['element_parts_line']])
print(json.dumps({'candidates':len(selections),'candidate_elements':len(owner),'all_muscle_audit_elements':len(broad),'isa_elements':len(ie),'partof_elements':len(pe),'partof_extra':len(pe-ie)}))
