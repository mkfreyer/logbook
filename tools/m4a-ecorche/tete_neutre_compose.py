"""Caption matched Blender frames; no image retouching."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

p = argparse.ArgumentParser()
p.add_argument('--asset', type=Path, required=True)
a = p.parse_args()
root = a.asset.resolve()
meta = json.loads((root/'tete.json').read_text())
data = {mode: json.loads((root/'renders'/mode/'metadata.json').read_text())
        for mode in ['before', 'after']}
assert data['before']['master_sha256'] == meta['baseline_blend_sha256']
assert data['after']['master_sha256'] == meta['master_sha256']
assert data['before']['lights'] == data['after']['lights']
frames = {mode: {f['file']: f for f in record['frames']} for mode, record in data.items()}
assert frames['before'].keys() == frames['after'].keys() and len(frames['before']) == 5
for file, old in frames['before'].items():
    for field in ['camera_matrix', 'ortho_scale', 'resolution', 'samples']:
        assert old[field] == frames['after'][file][field], (file, field)
    for mode in frames:
        assert hashlib.sha256((root/'renders'/mode/file).read_bytes()).hexdigest() == frames[mode][file]['sha256']
font_file = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
title_font = ImageFont.truetype(font_file, 27)
label_font = ImageFont.truetype(font_file, 21)
small_font = ImageFont.truetype(font_file, 17)


def board(file, title, views, width):
    margin, header, label, footer = 20, 86, 38, 67
    first = Image.open(root/'renders/before'/(views[0][0]+'.png'))
    height = round(first.height*width/first.width)
    canvas = Image.new('RGB', (2*width+3*margin, header+len(views)*(height+label+margin)+footer), '#141b24')
    draw = ImageDraw.Draw(canvas)
    draw.text((margin, 14), title, font=title_font, fill='#f0f4fa')
    draw.text((margin, 51), 'Même matériau mat, mêmes caméras et lumières — Blender / Cycles', font=small_font, fill='#bac7d6')
    for row, (view, caption) in enumerate(views):
        for col, mode in enumerate(['before', 'after']):
            x, y = margin+col*(width+margin), header+row*(height+label+margin)
            text = ('Tête P5' if mode == 'before' else 'Tête sans visage')+' — '+caption
            draw.text((x, y), text, font=label_font, fill='#f0f4fa')
            im = Image.open(root/'renders'/mode/(view+'.png')).convert('RGB')
            canvas.paste(im.resize((width, height), Image.Resampling.LANCZOS), (x, y+label))
    draw.text((margin, canvas.height-footer+7), 'Base d83fc44 • Tête et raccord supérieur uniquement • Proposition pour validation', font=small_font, fill='#bac7d6')
    draw.text((margin, canvas.height-footer+32), 'Corps, gorge P4, six zones des deltoïdes, aine et pieds conservés', font=small_font, fill='#bac7d6')
    canvas.save(root/'renders'/file)


board('comparatif-tete-face-trois-quarts.png', 'Tête neutre — face et trois quarts',
      [('face', 'face'), ('trois-quarts', 'trois quarts')], 660)
board('comparatif-tete-profil-arriere.png', 'Tête neutre — profil et arrière',
      [('profil', 'profil'), ('arriere', 'arrière')], 660)
board('planche-generale.png', 'Mannequin — comparaison générale', [('ensemble', 'vue générale')], 470)
(root/'renders/verification.json').write_text(json.dumps({
    'matched_before_after_views': 5, 'raw_render_hashes_verified': 10,
    'camera_matrices_resolution_scale_samples_lighting_equal': True,
    'baseline_sha256': meta['baseline_blend_sha256'], 'master_sha256': meta['master_sha256'],
    'processing': 'Captions and uniform resizing only; individual Blender frames untouched.',
    'compositor_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
}, indent=2)+'\n')
