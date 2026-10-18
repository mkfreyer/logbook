#!/usr/bin/env python3
"""Comparison layout from actual Blender PNGs; no generated or repainted anatomy."""
import argparse, hashlib, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2] / 'docs/m4a/l3')
a = p.parse_args()
font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
font = ImageFont.truetype(font_path, 28)
small = ImageFont.truetype(font_path, 20)
bg, fg, muted = '#0a1621', '#e6edf7', '#aebfd2'
variants = [('l2', 'L2 · Base précédente'), ('l3', 'L3 · Exploration anatomique')]
views = [('front', 'Face'), ('three-quarter', 'Trois quarts'), ('back', 'Dos'),
         ('side', 'Profil'), ('selection', 'Pectoraux orange')]
sources = []
for view, title in views:
    sheet = Image.new('RGB', (1600, 1470), bg)
    draw = ImageDraw.Draw(sheet)
    draw.text((25, 14), 'LOGBOOK · Nouvelle direction L3 · ' + title, font=font, fill=fg)
    for column, (variant, label) in enumerate(variants):
        x = 800 * column
        construction = json.loads((a.root / variant / 'construction.json').read_text())
        triangles = construction['counts']['visible_triangles']
        draw.text((x + 24, 61), label, font=font, fill=fg)
        draw.text((x + 24, 102), f'{triangles:,} triangles · 22 zones de surface'.replace(',', ' '), font=small, fill=muted)
        file = a.root / variant / (view + '.png')
        with Image.open(file) as image:
            assert image.size == (800, 1280)
            sheet.paste(image.convert('RGB'), (x, 145))
        sources.append({'file': str(file.relative_to(a.root)), 'sha256': hashlib.sha256(file.read_bytes()).hexdigest()})
    draw.text((24, 1438), 'Vrais rendus Blender · Mêmes matière et studio · Zones de surface stylisées · Choix visuel avant intégration', font=small, fill=muted)
    sheet.save(a.root / ('comparaison-' + view + '.png'))

overview = Image.new('RGB', (1200, 3150), bg)
draw = ImageDraw.Draw(overview)
draw.text((22, 15), 'LOGBOOK · L2 / L3 · Comparaison de géométrie', font=font, fill=fg)
for column, (variant, label) in enumerate(variants):
    x = column * 600
    draw.text((x + 20, 65), label, font=font, fill=fg)
    for row, (view, title) in enumerate(views[:3]):
        y = 120 + row * 990
        with Image.open(a.root / variant / (view + '.png')) as image:
            overview.paste(image.convert('RGB').resize((600, 960), Image.Resampling.LANCZOS), (x, y))
        draw.text((x + 20, y + 8), title, font=small, fill=muted)
draw.text((22, 3100), 'Géométrie originale · Images calculées en 3D · Aucune intégration dans l’app', font=small, fill=muted)
overview.save(a.root / 'comparaison.png')

detail = Image.new('RGB', (1600, 955), bg)
draw = ImageDraw.Draw(detail)
draw.text((25, 14), 'LOGBOOK · Détail du torse — même recadrage, agrandi', font=font, fill=fg)
for column, (variant, label) in enumerate(variants):
    draw.text((column * 800 + 24, 62), label, font=font, fill=fg)
    with Image.open(a.root / variant / 'front.png') as image:
        crop = image.convert('RGB').crop((190, 260, 610, 680))
        detail.paste(crop.resize((800, 800), Image.Resampling.LANCZOS), (column * 800, 110))
draw.text((24, 925), 'Recadrages des PNG de face ; aucune anatomie ajoutée ou retouchée.', font=small, fill=muted)
detail.save(a.root / 'detail-torse.png')
(a.root / 'sheets-metadata.json').write_text(json.dumps({'sources': sources, 'full_comparison_size': [1600, 1470],
    'detail_crop': [190, 260, 610, 680], 'geometry_or_anatomy_repainted': False}, indent=2) + '\n')
print('Saved seven sheets from ten real PNGs.')
