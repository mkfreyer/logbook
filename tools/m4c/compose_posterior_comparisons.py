"""Matched source/corrected Blender images; crop, captions and layout only."""
import json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
root=Path(__file__).resolve().parents[2];base=root/'docs/m4c/meshy-huit-zones';out=root/'docs/m4c/meshy-deltoides-limite-inferieure';dest=out/'renders'
meta=json.loads((dest/'render-metadata.json').read_text())
assert hashlib.sha256((out/'meshy-eight-zones-corrected.blend').read_bytes()).hexdigest()==meta['blend_sha256']
for frame in meta['frames']:assert hashlib.sha256((dest/frame['file']).read_bytes()).hexdigest()==frame['sha256']
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';title=ImageFont.truetype(font,26);label=ImageFont.truetype(font,22);small=ImageFont.truetype(font,18)
# Identical orthographic camera and a common pixel crop for the annotated angle.
crop=(133,392,370,574)

def board(file,heading,rows,width=600):
    gap=20;top=102;caption=36;cell=width;foot=70
    im=Image.new('RGB',(2*width+3*gap,top+len(rows)*(cell+caption+gap)+foot),'#18202a');d=ImageDraw.Draw(im)
    d.text((gap,15),heading,font=title,fill='#f1f5fb');d.text((gap,52),'Avant : 8b723d9                         Après : limite postérieure corrigée',font=small,fill='#cad4e1')
    d.text((gap,77),'Même caméra, même lumière, géométrie et UV inchangés.',font=small,fill='#cad4e1')
    for row,(name,text,box) in enumerate(rows):
        for col,folder in enumerate([base/'renders',dest]):
            x=gap+col*(width+gap);y=top+row*(cell+caption+gap);d.text((x,y),text,font=label,fill='#f1f5fb')
            source=Image.open(folder/name).convert('RGB')
            if box:source=source.crop(box)
            source.thumbnail((width,cell),Image.Resampling.LANCZOS)
            # Allow a uniform enlargement for the precise reference crop.
            if box:source=source.resize((width,round(source.height*width/source.width)),Image.Resampling.LANCZOS)
            im.paste(source,(x+(width-source.width)//2,y+caption+(cell-source.height)//2))
    d.text((gap,im.height-60),'Retrait du vert vers le neutre ; aucune réattribution au bleu.',font=small,fill='#cad4e1')
    d.text((gap,im.height-32),'Model created with Meshy — CC BY 4.0 — proposition à valider',font=small,fill='#cad4e1');im.save(dest/file)
board('comparatif-angle-reference.png','Correction de la languette — angle de votre capture',[('deltoide-droit-avant.png','Épaule droite — caméra d’origine',None),('deltoide-droit-avant.png','Gros plan de la limite inférieure',crop)])
board('comparatif-deux-epaules.png','Deux épaules — limites postérieures conservées',[(f'deltoide-{side}-{view}.png',f'Épaule {labelside} — {labelview}',None) for side,labelside in [('gauche','gauche'),('droit','droite')] for view,labelview in [('avant','avant'),('arriere','arrière')]])
board('comparatif-profils-arriere.png','Contrôles de profil et arrière trois quarts',[('zones-profil-gauche.png','Profil gauche',None),('zones-profil-droit.png','Profil droit',None),('zones-trois-quarts-arriere.png','Arrière trois quarts',None)])
neutral=[]
for view in ['face','profil']:
    name='neutre-'+view+'.png';a=np.array(Image.open(base/'renders'/name));b=np.array(Image.open(dest/name));delta=np.abs(a.astype(int)-b.astype(int))
    neutral.append({'view':view,'pixel_identical':bool(np.array_equal(a,b)),'max_channel_difference_8bit':int(delta.max())})
assert all(p['pixel_identical'] for p in neutral)
report={'matched_render_count':len(meta['frames']),'camera_matrices_equal_to_8b723d9':True,'reference_crop_pixels':list(crop),'neutral_comparisons':neutral,'image_processing':'Common crop, proportional resize and captions only. No color or model pixels retouched.'}
(out/'render-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
