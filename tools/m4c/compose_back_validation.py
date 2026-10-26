"""Matched rear comparison boards and file preservation checks; no repainting."""
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from glb_io import sha

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs/m4c/meshy-validation-arriere'
DEST = OUT / 'renders'
metadata = json.loads((DEST / 'render-metadata.json').read_text())
assert len(metadata['frames']) == 7
frames = {item['file']: item for item in metadata['frames']}
for item in frames.values():
    assert sha((DEST / item['file']).read_bytes()) == item['sha256']
    assert sha((ROOT / item['sourceBlend']).read_bytes()) == item['sourceBlendSha256']
for name, expected in metadata['preservation']['protectedSourcesByteIdentical'].items():
    assert sha((ROOT / name).read_bytes()) == expected, name
scenes = metadata['sceneAudits']
assert scenes[0]['geometry'] == scenes[1]['geometry']
assert scenes[0]['lights'] == scenes[1]['lights']

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
title = ImageFont.truetype(FONT, 25)
label = ImageFont.truetype(FONT, 21)
small = ImageFont.truetype(FONT, 18)
checks = []

def compare(view, filename, heading, width, height):
    before = frames[f'avant-{view}.png']
    after = frames[f'apres-{view}.png']
    for key in ['cameraMatrix', 'targetSourceM', 'resolution', 'orthoScale']:
        assert before[key] == after[key], (view, key)
    a = np.array(Image.open(DEST / before['file']).convert('RGB'))
    b = np.array(Image.open(DEST / after['file']).convert('RGB'))
    delta = np.abs(a.astype(int) - b.astype(int))
    checks.append({'view': view, 'cameraAndFramingIdentical': True,
                   'pixelIdentical': bool(np.array_equal(a, b)),
                   'changedRGBPixels': int(np.any(delta != 0, axis=2).sum()),
                   'pixelsWithChannelDifferenceAbove2': int(np.any(delta > 2, axis=2).sum()),
                   'maxChannelDifference8bit': int(delta.max())})
    gap, top, caption, foot = 20, 92, 34, 65
    board = Image.new('RGB', (2 * width + 3 * gap, top + caption + height + foot), '#18202a')
    draw = ImageDraw.Draw(board)
    draw.text((gap, 14), heading, font=title, fill='#f1f5fb')
    draw.text((gap, 49), 'Comparaison de la correction locale : 71f70dc → daf5878', font=small, fill='#cad4e1')
    draw.text((gap, 73), 'Caméra, cadrage, lumière et géométrie identiques.', font=small, fill='#cad4e1')
    for col, frame in enumerate([before, after]):
        x = gap + col * (width + gap)
        draw.text((x, top), 'Avant — 71f70dc' if col == 0 else 'Après — daf5878', font=label, fill='#f1f5fb')
        image = Image.open(DEST / frame['file']).convert('RGB')
        image.thumbnail((width, height), Image.Resampling.LANCZOS)
        board.paste(image, (x + (width - image.width) // 2,
                            top + caption + (height - image.height) // 2))
    draw.text((gap, board.height - 54), 'Rendus de contrôle uniquement ; aucun masque ni maillage modifié.', font=small, fill='#cad4e1')
    draw.text((gap, board.height - 29), 'Model created with Meshy — CC BY 4.0 — validation visuelle attendue', font=small, fill='#cad4e1')
    board.save(DEST / filename)

compare('dos-complet', 'comparatif-dos-complet.png', 'Vue complète de dos — avant / après', 600, 900)
compare('epaules-dos', 'comparatif-epaules-dos.png', 'Deux épaules de dos — avant / après', 700, 450)
compare('trois-quarts-arriere-droit', 'comparatif-arriere-droit.png',
        'Épaule droite — trois quarts arrière avant / après', 700, 700)
report = {
    'referenceCommit': metadata['referenceCommit'],
    'beforeCommit': metadata['comparisonBeforeCommit'],
    'rawBlenderFrames': len(frames), 'comparisons': checks,
    'protectedSourceFileCount': len(metadata['preservation']['protectedSourcesByteIdentical']),
    'sourcesByteIdentical': True, 'lightsIdenticalBetweenScenes': True,
    'geometryPositionsNormalsUVIndicesIdentical': True,
    'applicationFilesUnchanged': metadata['preservation']['applicationFilesUnchanged'],
    'eightIdentifiersUnchanged': metadata['preservation']['eightIdentifiersUnchanged'],
    'imageProcessing': 'Captions, layout and proportional reduction only; no model pixel repainting.',
}
(OUT / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report), flush=True)
