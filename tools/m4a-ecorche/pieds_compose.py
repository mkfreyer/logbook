"""Captioned boards from untouched, matched Blender renders."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

p = argparse.ArgumentParser()
p.add_argument('--asset', type=Path, required=True)
a = p.parse_args()
root = a.asset.resolve()
meta = json.loads((root/'finition.json').read_text())
manifests = {mode: json.loads((root/'renders'/mode/'metadata.json').read_text())
             for mode in ['before', 'after']}
assert manifests['before']['master_sha256'] == meta['baseline_blend_sha256']
assert manifests['after']['master_sha256'] == meta['master_sha256']
frames = {mode: {f['file']: f for f in data['frames']} for mode, data in manifests.items()}
assert frames['before'].keys() == frames['after'].keys() and len(frames['before']) == 6
for file, before in frames['before'].items():
    for field in ['camera_matrix', 'ortho_scale', 'resolution', 'samples']:
        assert before[field] == frames['after'][file][field], (file, field)
    for mode in frames:
        assert hashlib.sha256((root/'renders'/mode/file).read_bytes()).hexdigest() == frames[mode][file]['sha256']
font = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
title_font = ImageFont.truetype(font, 28)
label_font = ImageFont.truetype(font, 21)
small = ImageFont.truetype(font, 17)


def board(file, title, views, width):
    margin, header, label, footer = 20, 88, 38, 65
    first = Image.open(root/'renders/before'/(views[0][0]+'.png'))
    height = round(first.height*width/first.width)
    canvas = Image.new('RGB', (2*width+3*margin, header+len(views)*(height+label+margin)+footer), '#141b24')
    d = ImageDraw.Draw(canvas)
    d.text((margin, 15), title, font=title_font, fill='#f0f4fa')
    d.text((margin, 54), 'Même matériau mat, mêmes caméras et lumières — Blender / Cycles', font=small, fill='#bac7d6')
    for row, (view, caption) in enumerate(views):
        for col, mode in enumerate(['before', 'after']):
            x, y = margin+col*(width+margin), header+row*(height+label+margin)
            d.text((x, y), ('Avant' if mode == 'before' else 'Après')+' — '+caption, font=label_font, fill='#f0f4fa')
            im = Image.open(root/'renders'/mode/(view+'.png')).convert('RGB')
            im = im.resize((width, height), Image.Resampling.LANCZOS)
            canvas.paste(im, (x, y+label))
    d.text((margin, canvas.height-footer+7), 'Base '+meta['baseline_commit'][:7]+' • Pieds et chevilles uniquement • Proposition pour validation', font=small, fill='#bac7d6')
    d.text((margin, canvas.height-footer+31), 'Aine, deltoïdes, tête, gorge et muscles des jambes conservés', font=small, fill='#bac7d6')
    canvas.save(root/'renders'/file)


board('comparatif-pieds.png', 'Pieds — finition avant / après',
      [('face-pieds', 'face'), ('trois-quarts-pieds', 'trois quarts')], 740)
board('comparatif-profils.png', 'Pieds — contrôle des deux profils',
      [('profil-droit', 'profil droit'), ('profil-gauche', 'profil gauche')], 740)
board('raccords-chevilles.png', 'Raccords cheville / pied', [('chevilles', 'raccords rapprochés')], 780)
board('planche-generale.png', 'Contrôle de l’harmonie du mannequin', [('ensemble', 'vue générale')], 470)
(root/'renders/verification.json').write_text(json.dumps({
    'matched_before_after_views': 6, 'raw_render_hashes_verified': 12,
    'camera_matrices_scale_resolution_samples_equal': True,
    'baseline_sha256': meta['baseline_blend_sha256'], 'master_sha256': meta['master_sha256'],
    'processing': 'Labels and uniform resizing only. Individual Blender images unmodified.',
    'compositor_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
}, indent=2)+'\n')
