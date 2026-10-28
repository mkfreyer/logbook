"""Validate matched Blender frames; add layout and captions, never repaint pixels."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from glb_io import sha

root = Path(__file__).resolve().parents[2]
base = root / 'docs/m4c/meshy-deltoides-limite-inferieure'
out = root / 'docs/m4c/meshy-deltoides-residu-local'
dest = out / 'renders'
meta = json.loads((dest / 'render-metadata.json').read_text())
assert sha((out / 'meshy-residu-corrige.blend').read_bytes()) == meta['correctedBlendSha256']
frames = {item['file']: item for item in meta['frames']}
for item in frames.values():
    assert sha((dest / item['file']).read_bytes()) == item['sha256']
for before, after in [('avant-gros-plan.png', 'apres-gros-plan.png'),
                      ('avant-angle-35.png', 'apres-angle-35.png'),
                      ('avant-angle-55.png', 'apres-angle-55.png')]:
    for key in ['camera_matrix', 'ortho_scale', 'full_resolution', 'normalized_border']:
        assert frames[before][key] == frames[after][key], (before, key)
neutral_before = np.array(Image.open(base / 'renders/neutre-face.png'))
neutral_after = np.array(Image.open(dest / 'neutre-face.png'))
assert np.array_equal(neutral_before, neutral_after)
font = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
title = ImageFont.truetype(font, 25)
label = ImageFont.truetype(font, 22)
small = ImageFont.truetype(font, 18)

def board(name, heading, pairs, width, height):
    gap, top, caption, footer = 20, 96, 34, 64
    image = Image.new('RGB', (2 * width + 3 * gap,
                            top + len(pairs) * (height + caption + gap) + footer), '#18202a')
    d = ImageDraw.Draw(image)
    d.text((gap, 14), heading, font=title, fill='#f1f5fb')
    d.text((gap, 49), 'Avant : 71f70dc     /     Après : retrait local du résidu vert', font=small, fill='#cad4e1')
    d.text((gap, 74), 'Même caméra et lumière ; géométrie et sept autres masques inchangés.', font=small, fill='#cad4e1')
    for row, (text, before, after) in enumerate(pairs):
        y = top + row * (height + caption + gap)
        for col, path in enumerate([before, after]):
            x = gap + col * (width + gap)
            d.text((x, y), ('Avant — ' if col == 0 else 'Après — ') + text,
                   font=label, fill='#f1f5fb')
            source = Image.open(path).convert('RGB')
            source.thumbnail((width, height), Image.Resampling.LANCZOS)
            image.paste(source, (x + (width - source.width) // 2,
                                 y + caption + (height - source.height) // 2))
    d.text((gap, image.height - 54), 'Vert retiré → neutre. Images Blender sans retouche de la surface.', font=small, fill='#cad4e1')
    d.text((gap, image.height - 29), 'Model created with Meshy — CC BY 4.0 — à valider visuellement', font=small, fill='#cad4e1')
    image.save(dest / name)

board('comparatif-residu-serre.png', 'Petit débordement vert — gros plan de référence',
      [('raccord inférieur', dest / 'avant-gros-plan.png', dest / 'apres-gros-plan.png')], 500, 650)
board('comparatif-contexte.png', 'Contexte — portion postérieure conservée',
      [('épaule droite', base / 'renders/deltoide-droit-avant.png', dest / 'apres-vue-large.png')], 640, 640)
board('comparatif-angles-voisins.png', 'Contrôle sous deux angles voisins',
      [(f'caméra −{angle}°', dest / f'avant-angle-{angle}.png', dest / f'apres-angle-{angle}.png')
       for angle in [35, 55]], 640, 640)
report = {
    'matchedBlenderFrameCount': len(frames),
    'closeupPixelSize': list(Image.open(dest / 'apres-gros-plan.png').size),
    'closeupRenderedAtSourceResolution': [6400, 6400],
    'commonCropIn640ReferencePixels': [196, 432, 246, 497],
    'closeAndNeighborCameraMatricesEqual': True,
    'neutralFacePixelIdenticalTo71f70dc': True,
    'maxNeutralChannelDifference8bit': int(np.abs(neutral_before.astype(int) - neutral_after.astype(int)).max()),
    'imageProcessing': 'Layout, captions and proportional reduction only. No model pixels painted or modified.',
}
(out / 'render-verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report), flush=True)
