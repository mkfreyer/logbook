#!/usr/bin/env python3
"""Lay out real render PNGs; only resize and add labels, no geometry/image synthesis."""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2] / 'docs/m4a/ecorche')
a = p.parse_args()
font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
font = ImageFont.truetype(font_path, 29)
small = ImageFont.truetype(font_path, 19)
bg, fg, muted = '#0a1621', '#e6edf7', '#aebfd2'
candidates = [('bodyparts3d', 'BodyParts3D brut', '425 objets / 2 404 604 triangles'),
              ('z-anatomy', 'Z-Anatomy', '457 objets / 1 948 068 triangles'),
              ('ecorche', 'Écorché — dérivé BP3D / Z', '362 objets / 726 468 triangles')]
views = [('front', 'Face'), ('three-quarter', 'Trois quarts'), ('back', 'Dos'),
         ('selection', 'Grand pectoral gauche : trois vrais composants')]
for view, label in views:
    sheet = Image.new('RGB', (1800, 1190), bg)
    draw = ImageDraw.Draw(sheet)
    draw.text((28, 15), 'M4A · Bases réelles · ' + label, font=font, fill=fg)
    for col, (candidate, title, counts) in enumerate(candidates):
        x = 600 * col
        draw.text((x + 20, 65), title, font=font, fill=fg)
        draw.text((x + 20, 104), counts, font=small, fill=muted)
        with Image.open(a.root / candidate / (view + '.png')) as im:
            assert im.size == (600, 1000)
            sheet.paste(im.convert('RGB'), (x, 145))
    draw.text((24, 1154), 'Muscles sans os ni organes · Lacunes conservées · Aucun candidat fini · CC BY-SA 4.0 / crédits : ATTRIBUTION.md', font=small, fill=muted)
    sheet.save(a.root / ('comparaison-' + view + '.png'))

overview = Image.new('RGB', (1200, 2240), bg)
draw = ImageDraw.Draw(overview)
draw.text((22, 12), 'M4A · Comparaison des géométries sources', font=font, fill=fg)
for col, (candidate, title, counts) in enumerate(candidates):
    draw.text((col * 400 + 12, 64), title, font=small, fill=fg)
    for row, (view, label) in enumerate(views[:3]):
        with Image.open(a.root / candidate / (view + '.png')) as im:
            im = im.convert('RGB').resize((400, 667), Image.Resampling.LANCZOS)
            overview.paste(im, (col * 400, 110 + row * 690))
        draw.text((col * 400 + 12, 110 + row * 690), label, font=small, fill=muted)
draw.text((20, 2198), 'Même protocole · Pas de comblement inventé · Attribution et licences dans le dossier', font=small, fill=muted)
overview.save(a.root / 'comparaison.png')
print('Saved five comparison sheets; geometry and source render pixels otherwise unchanged.')
