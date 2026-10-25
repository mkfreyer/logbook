"""Captions/uniform layout only. All model pixels come from raw Blender renders."""
import json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
root=Path(__file__).resolve().parents[2];out=root/'docs/m4c/meshy-huit-zones';dest=out/'renders'
meta=json.loads((dest/'render-metadata.json').read_text())
for frame in meta['frames']:assert hashlib.sha256((dest/frame['file']).read_bytes()).hexdigest()==frame['sha256']
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';title=ImageFont.truetype(font,28);label=ImageFont.truetype(font,22);small=ImageFont.truetype(font,18)
legend=[('Pectoral G','#FF932B'),('Pectoral D','#F2D347'),('Antérieur','#E55B5B'),('Moyen','#447EEB'),('Postérieur','#46C47B')]
def board(name,heading,frames,columns=2,width=640):
    rows=(len(frames)+columns-1)//columns;gap=20;caption=38;header=112;foot=86;height=width
    im=Image.new('RGB',(columns*width+(columns+1)*gap,header+rows*(height+caption+gap)+foot),'#18202a');d=ImageDraw.Draw(im)
    d.text((gap,15),heading,font=title,fill='#f0f4fa');d.text((gap,55),'M4C — Meshy e45e5d8 — proposition anatomique à valider',font=small,fill='#c5cfdc')
    d.text((gap,82),'Gauche/droite anatomiques : de face, la gauche est à droite de l’image.',font=small,fill='#c5cfdc')
    for i,(file,text) in enumerate(frames):
        x=gap+(i%columns)*(width+gap);y=header+(i//columns)*(height+caption+gap)
        d.text((x,y),text,font=label,fill='#f0f4fa');source=Image.open(dest/(file+'.png')).convert('RGB');source.thumbnail((width,height),Image.Resampling.LANCZOS)
        im.paste(source,(x+(width-source.width)//2,y+caption+(height-source.height)//2))
    x=gap;y=im.height-foot+8
    for text,color in legend:
        d.rectangle((x,y+3,x+19,y+22),fill=color);d.text((x+27,y),text,font=small,fill='#e5edf8');x+=220
    d.text((gap,im.height-32),'Vrais rendus Blender — aucune sculpture — Model created with Meshy / CC BY 4.0',font=small,fill='#c5cfdc');im.save(dest/name)
board('planche-huit-zones.png','Huit zones — contrôle sous six angles',[(f'zones-{file}',text) for file,text in [('face','Face'),('trois-quarts-avant','Trois quarts avant'),('profil-gauche','Profil gauche'),('profil-droit','Profil droit'),('trois-quarts-arriere','Trois quarts arrière'),('dos','Dos')]],3,640)
board('planche-pectoraux.png','Pectoraux — contours et plis axillaires',[('pectoral-gauche','Grand pectoral gauche'),('pectoral-droit','Grand pectoral droit')],2,640)
board('planche-deltoides.png','Deltoïdes — dôme latéral et convergence des faisceaux',[('deltoide-gauche-avant','Gauche — avant'),('deltoide-droit-avant','Droit — avant'),('deltoide-gauche-arriere','Gauche — arrière'),('deltoide-droit-arriere','Droit — arrière')],2,640)
board('controle-neutre.png','Préservation — référence et masques désactivés',[(file,text) for view,name in [('face','face'),('profil','profil'),('dos','dos')] for file,text in [(f'reference-{view}','Référence — '+name),(f'neutre-{view}','Zones désactivées — '+name)]],2,640)
neutral=[]
for view in ['face','profil','dos']:
    a=np.array(Image.open(dest/f'reference-{view}.png'));b=np.array(Image.open(dest/f'neutre-{view}.png'));assert a.shape==b.shape
    delta=np.abs(a.astype(int)-b.astype(int));neutral.append({'view':view,'pixel_identical':bool(np.array_equal(a,b)),'max_channel_difference_8bit':int(delta.max()),'changed_pixels':int(np.any(delta!=0,axis=2).sum())})
report={'raw_render_hashes_verified':len(meta['frames']),'neutral_comparisons':neutral,'processing':'Captions, solid external legend, proportional resize and layout only. No model pixels painted or retouched.','raw_frames':meta['frames']}
(out/'render-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(neutral),flush=True)
assert all(v['pixel_identical'] for v in neutral),'Neutral shading changed; inspect before claiming preservation'
