"""Arrange native Blender pixels into validation sheets; no retouching/resizing."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

p = argparse.ArgumentParser()
p.add_argument('--asset', type=Path, required=True)
a = p.parse_args()
root = a.asset.resolve()
out = root / 'renders'
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 23)
small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
records = []


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sheet(name, title, items):
    images = [Image.open(out / file).convert('RGB') for file, label in items]
    canvas = Image.new('RGB', (sum(i.width for i in images) + 24 * (len(images) + 1),
                              max(i.height for i in images) + 132), (25, 27, 30))
    d = ImageDraw.Draw(canvas)
    d.text((24, 16), title, font=font, fill='white')
    x = 24
    for image, (file, label) in zip(images, items):
        d.text((x, 61), label, font=small, fill=(220, 220, 220))
        canvas.paste(image, (x, 108))
        x += image.width + 24
    dest = out / (name + '.png')
    canvas.save(dest)
    records.append({'file': dest.name, 'sha256': sha(dest),
                    'sources': [{'file': f, 'sha256': sha(out / f)} for f, label in items],
                    'raw_pixels_resized': False, 'raw_pixels_retouched': False})


sheet('planche-finale', 'Combinaison : deltoïdes P4 exacts — tête P5 et corps conservés',
      [('face.png', 'Face'), ('profil.png', 'Profil'), ('dos.png', 'Dos'), ('trois-quarts.png', 'Trois quarts')])
sheet('epaules-face-dos', 'Deltoïdes P4 restaurés — aucun changement de forme',
      [('epaules-face.png', 'Face'), ('epaules-dos.png', 'Dos')])
sheet('deux-deltoides', 'Les deux épaules — matériau mat neutre identique',
      [('epaule-droite.png', 'Deltoïde droit'), ('epaule-gauche.png', 'Deltoïde gauche')])
sheet('epaule-profil-arriere', 'Deltoïde P4 restauré — profil et trois quarts arrière',
      [('epaule-profil.png', 'Profil'), ('epaule-arriere.png', 'Trois quarts arrière')])
(out / 'planches.json').write_text(json.dumps({'composer_sha256': sha(Path(__file__)),
    'sheets': records}, ensure_ascii=False, indent=2) + '\n')
print('COMBINAISON_SHEETS', len(records))
