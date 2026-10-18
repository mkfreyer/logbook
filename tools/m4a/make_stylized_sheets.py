#!/usr/bin/env python3
"""Assemble actual Blender PNGs, preserving anatomy and CC BY-SA attribution."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,PngImagePlugin
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);a=p.parse_args()
f='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';font=ImageFont.truetype(f,27);small=ImageFont.truetype(f,21)
bg='#0a1621';fg='#e6edf7';muted='#aebfd2'
variants=[('s1','S1 · Anatomique doux'),('s2','S2 · Anatomique premium'),('s3','S3 · Écorché fitness simplifié')]
views=[('front','Face'),('three-quarter','Trois quarts'),('back','Dos'),('side','Profil'),('selection','Pectoraux sélectionnés')]
sources=[];credit='Écorché / BodyParts3D / Z-Anatomy · Adaptations Logbook · CC BY-SA 4.0 · Voir ATTRIBUTION.md'
meta=PngImagePlugin.PngInfo();meta.add_text('License','CC BY-SA 4.0');meta.add_text('Attribution',credit)
for view,title in views:
    sheet=Image.new('RGB',(2160,1340),bg);d=ImageDraw.Draw(sheet)
    d.text((24,15),'LOGBOOK · Trois nouvelles bases anatomiques · '+title,font=font,fill=fg)
    for col,(variant,label) in enumerate(variants):
        x=col*720;c=json.loads((a.root/variant/'construction.json').read_text())
        d.text((x+24,60),label,font=font,fill=fg)
        d.text((x+24,103),f"{c['counts']['triangles']:,} triangles · {c['counts']['visible_objects']} objets".replace(',',' '),font=small,fill=muted)
        file=a.root/variant/(view+'.png')
        with Image.open(file) as im:
            assert im.size==(720,1152);sheet.paste(im.convert('RGB'),(x,145))
        sources.append({'file':str(file.relative_to(a.root)),'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
    d.text((24,1307),credit,font=small,fill=muted);sheet.save(a.root/('comparaison-'+view+'.png'),pnginfo=meta)
overview=Image.new('RGB',(1296,2210),bg);d=ImageDraw.Draw(overview)
d.text((20,14),'LOGBOOK · S1 / S2 / S3 · Même studio Blender',font=font,fill=fg)
for col,(variant,label) in enumerate(variants):
    x=col*432;d.text((x+12,62),variant.upper(),font=font,fill=fg)
    for row,(view,title) in enumerate(views[:3]):
        y=110+row*694
        with Image.open(a.root/variant/(view+'.png')) as im:overview.paste(im.convert('RGB').resize((432,691),Image.Resampling.LANCZOS),(x,y))
        d.text((x+12,y+5),title,font=small,fill=muted)
d.text((20,2180),'Écorché / BodyParts3D / Z-Anatomy · CC BY-SA 4.0 · ATTRIBUTION.md',font=small,fill=muted)
overview.save(a.root/'comparaison.png',pnginfo=meta)
detail=Image.new('RGB',(2160,870),bg);d=ImageDraw.Draw(detail)
d.text((24,15),'LOGBOOK · Détail torse / abdomen · Recadrages identiques',font=font,fill=fg)
for col,(variant,label) in enumerate(variants):
    x=col*720;d.text((x+24,63),label,font=font,fill=fg)
    with Image.open(a.root/variant/'front.png') as im:
        crop=im.convert('RGB').crop((150,210,570,620)).resize((720,703),Image.Resampling.LANCZOS);detail.paste(crop,(x,110))
d.text((24,838),credit,font=small,fill=muted);detail.save(a.root/'detail-torse.png',pnginfo=meta)
(a.root/'sheets-metadata.json').write_text(json.dumps({'sources':sources,'full_comparison_size':[2160,1340],'detail_crop':[150,210,570,620],'anatomy_repainted':False,'license':'CC-BY-SA-4.0'},indent=2)+'\n')
print('Seven sheets from fifteen genuine Blender renders.')
