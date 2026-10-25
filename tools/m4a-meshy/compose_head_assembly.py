"""Caption untouched, matched Blender renders for visual validation."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

p = argparse.ArgumentParser()
p.add_argument('--asset', type=Path, required=True)
a = p.parse_args()
root = a.asset.resolve()
meta = json.loads((root/'assemblage.json').read_text())
records = {mode: json.loads((root/'renders'/mode/'metadata.json').read_text())
           for mode in ['before', 'after']}
assert all(r['master_sha256'] == meta['master_sha256'] for r in records.values())
assert records['before']['lights'] == records['after']['lights']
frames = {mode: {f['file']: f for f in record['frames']} for mode, record in records.items()}
assert frames['before'].keys() == frames['after'].keys() and len(frames['before']) == 6
for file, before in frames['before'].items():
    for field in ['camera_matrix', 'ortho_scale', 'resolution', 'samples']:
        assert before[field] == frames['after'][file][field], (file, field)
    for mode in frames:
        path = root/'renders'/mode/file
        assert hashlib.sha256(path.read_bytes()).hexdigest() == frames[mode][file]['sha256']
font = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
title = ImageFont.truetype(font, 27)
label = ImageFont.truetype(font, 21)
small = ImageFont.truetype(font, 17)
head_label = meta.get('head_label', 'Rib Reach Exercise')
before_label = 'Tête précédente' if 'comparison_glb' in meta else 'Origine'


def comparison(file, heading, views, width):
    margin, header, caption, footer = 20, 86, 38, 68
    first = Image.open(root/'renders/before'/(views[0][0]+'.png'))
    height = round(first.height*width/first.width)
    canvas = Image.new('RGB', (2*width+3*margin, header+len(views)*(height+caption+margin)+footer), '#141b24')
    draw = ImageDraw.Draw(canvas)
    draw.text((margin, 14), heading, font=title, fill='#f0f4fa')
    draw.text((margin, 50), 'Même matériau mat, mêmes caméras et lumières — Blender / Cycles', font=small, fill='#bac7d6')
    for row, (view, text) in enumerate(views):
        for col, mode in enumerate(['before', 'after']):
            x, y = margin+col*(width+margin), header+row*(height+caption+margin)
            draw.text((x, y), (before_label if mode == 'before' else head_label)+' — '+text, font=label, fill='#f0f4fa')
            im = Image.open(root/'renders'/mode/(view+'.png')).convert('RGB')
            canvas.paste(im.resize((width, height), Image.Resampling.LANCZOS), (x, y+caption))
    draw.text((margin, canvas.height-footer+7), 'Corps : Anatomical Form • Tête : '+head_label+' • Sources utilisateur', font=small, fill='#bac7d6')
    draw.text((margin, canvas.height-footer+32), 'Corps conservé sous le raccord • Model created with Meshy — CC BY 4.0', font=small, fill='#bac7d6')
    canvas.save(root/'renders'/file)


comparison('comparatif-tetes.png', 'Assemblage Meshy — tête et raccord',
    [('tete-face', 'face'), ('tete-profil', 'profil'), ('tete-trois-quarts', 'trois quarts')], 620)
comparison('comparatif-ensemble.png', 'Corps conservé — comparaison générale', [('face', 'vue générale')], 490)
width, margin, header, caption, footer = 470, 20, 86, 38, 68
height = round(1152*width/720)
canvas = Image.new('RGB', (3*width+4*margin, header+caption+height+footer), '#141b24')
draw = ImageDraw.Draw(canvas)
draw.text((margin, 14), 'Mannequin assemblé — trois vues de validation', font=title, fill='#f0f4fa')
draw.text((margin, 50), 'Corps Anatomical Form + tête '+head_label+' — Blender / Cycles', font=small, fill='#bac7d6')
for i, (view, text) in enumerate([('face', 'Face'), ('profil', 'Profil'), ('trois-quarts', 'Trois quarts')]):
    x = margin+i*(width+margin)
    draw.text((x, header), text, font=label, fill='#f0f4fa')
    im = Image.open(root/'renders/after'/(view+'.png')).convert('RGB')
    canvas.paste(im.resize((width, height), Image.Resampling.LANCZOS), (x, header+caption))
draw.text((margin, canvas.height-footer+8), 'Proposition pour validation • Aucune intégration applicative', font=small, fill='#bac7d6')
draw.text((margin, canvas.height-footer+32), 'Model created with Meshy — CC BY 4.0 License', font=small, fill='#bac7d6')
canvas.save(root/'renders/mannequin-assemble.png')
(root/'renders/verification.json').write_text(json.dumps({
    'matched_before_after_views': 6, 'raw_render_hashes_verified': 12,
    'camera_scale_resolution_samples_lighting_equal': True,
    'master_sha256': meta['master_sha256'],
    'image_processing': 'Captions and uniform resizing only. Raw Blender frames untouched.',
    'compositor_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
}, indent=2)+'\n')
