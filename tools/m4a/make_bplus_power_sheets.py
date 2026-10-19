#!/usr/bin/env python3
"""Assemble old/new B+ Premium Blender comparisons, with no anatomy repainted."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,PngImagePlugin
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);a=p.parse_args()
f='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';font=ImageFont.truetype(f,27);small=ImageFont.truetype(f,21)
bg='#0a1621';fg='#e6edf7';muted='#aebfd2'
variants=[('../bplus-fitness/premium','Premium actuel'),('power','Premium Puissance')]
views=[('front','Face'),('three-quarter','Trois quarts'),('back','Dos'),('side','Profil'),('selection','Pectoraux sélectionnés')]
sources=[];credit='Base B+ · Dan Ulrich / Blender Studio · CC0 · Rendus Blender · Relief continu'
meta=PngImagePlugin.PngInfo();meta.add_text('Source geometry license','CC0');meta.add_text('Attribution',credit)
for view,title in views:
    sheet=Image.new('RGB',(1440,1340),bg);d=ImageDraw.Draw(sheet)
    d.text((24,15),'LOGBOOK · B+ Écorché Premium · Comparaison · '+title,font=font,fill=fg)
    for col,(variant,label) in enumerate(variants):
        x=col*720;c=json.loads((a.root/variant/'construction.json').read_text())
        d.text((x+24,60),label,font=font,fill=fg)
        d.text((x+24,103),f"{c['counts']['visible_triangles']:,} triangles · {c['counts']['objects']} objets".replace(',',' '),font=small,fill=muted)
        file=a.root/variant/(view+'.png')
        with Image.open(file) as im:
            assert im.size==(720,1152);sheet.paste(im.convert('RGB'),(x,145))
        sources.append({'file':str(file.relative_to(a.root)),'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
    d.text((24,1307),credit,font=small,fill=muted);sheet.save(a.root/('comparaison-'+view+'.png'),pnginfo=meta)
overview=Image.new('RGB',(864,2210),bg);d=ImageDraw.Draw(overview)
d.text((20,14),'LOGBOOK · Premium actuel / Puissance',font=font,fill=fg)
for col,(variant,label) in enumerate(variants):
    x=col*432;d.text((x+12,62),{'../bplus-fitness/premium':'Actuel','power':'Puissance'}[variant],font=font,fill=fg)
    for row,(view,title) in enumerate(views[:3]):
        y=110+row*694
        with Image.open(a.root/variant/(view+'.png')) as im:overview.paste(im.convert('RGB').resize((432,691),Image.Resampling.LANCZOS),(x,y))
        d.text((x+12,y+5),title,font=small,fill=muted)
d.text((20,2180),'B+ · Dan Ulrich / Blender Studio · CC0',font=small,fill=muted)
overview.save(a.root/'comparaison.png',pnginfo=meta)
detail=Image.new('RGB',(1440,870),bg);d=ImageDraw.Draw(detail)
d.text((24,15),'LOGBOOK · Détail torse / abdomen · Recadrages identiques',font=font,fill=fg)
for col,(variant,label) in enumerate(variants):
    x=col*720;d.text((x+24,63),label,font=font,fill=fg)
    with Image.open(a.root/variant/'front.png') as im:
        crop=im.convert('RGB').crop((150,210,570,620)).resize((720,703),Image.Resampling.LANCZOS);detail.paste(crop,(x,110))
d.text((24,838),credit,font=small,fill=muted);detail.save(a.root/'detail-torse.png',pnginfo=meta)
(a.root/'sheets-metadata.json').write_text(json.dumps({'sources':sources,'full_comparison_size':[1440,1340],'detail_crop':[150,210,570,620],'anatomy_repainted':False,'source_geometry_license':'CC0'},indent=2)+'\n')
print('Seven sheets from ten genuine Blender renders (five preserved, five new).')
