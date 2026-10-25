"""Layout Blender renders; reuse unchanged approved neutral views transparently."""
import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def font(size):
    return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', size)


def plate(root, name, title, items, columns, size, color_legend=True):
    width, height = size
    header, label, footer = 96, 44, 66
    rows = (len(items) + columns - 1) // columns
    canvas = Image.new('RGB', (columns * width, header + rows * (height + label) + footer), '#181818')
    draw = ImageDraw.Draw(canvas)
    draw.text((24, 12), title, font=font(28), fill='white')
    subtitle = ('Antérieur : rouge  |  Latéral : bleu  |  Postérieur : vert  —  côtés anatomiques du modèle'
                if color_legend else 'Matériau mat neutre P4 — mêmes caméras et éclairage, surface conservée')
    draw.text((24, 52), subtitle,
              font=font(19), fill='#dddddd')
    for i, (path, text) in enumerate(items):
        im = Image.open(path).convert('RGB')
        im.thumbnail((width, height), Image.Resampling.LANCZOS)
        x = (i % columns) * width
        y = header + (i // columns) * (height + label)
        draw.text((x + 15, y + 8), text, font=font(22), fill='white')
        canvas.paste(im, (x + (width - im.width) // 2, y + label + (height - im.height) // 2))
    draw.text((24, canvas.height - 44), 'Référence 0ab3d83 — aucune sculpture, aucun sommet déplacé. Limites fonctionnelles à valider.',
              font=font(19), fill='#dddddd')
    path = root / name
    canvas.save(path)
    return {'file': name, 'sha256': sha(path), 'sources': [os.path.relpath(p, root) for p, _ in items]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--asset', type=Path, required=True)
    parser.add_argument('--baseline-asset', type=Path, required=True)
    args = parser.parse_args()
    root = args.asset.resolve() / 'renders'
    reference = args.baseline_asset.resolve() / 'renders'
    baseline_metadata = json.loads((reference / 'metadata.json').read_text())
    verify = json.loads((args.asset / 'verification.json').read_text())
    assert verify['all_300_evaluated_surfaces_topology_normals_identical']
    assert verify['cameras_lights_world_identical']
    neutral = root / 'neutral'
    neutral.mkdir(exist_ok=True)
    new_frames = {f['file'] for f in json.loads((neutral / 'metadata.json').read_text())['frames']}
    checks, reuse = [], []
    for frame in baseline_metadata['frames']:
        path = neutral / frame['file']
        approved = reference / frame['file']
        assert sha(approved) == frame['sha256']
        if frame['file'] in new_frames:
            before = np.array(Image.open(approved).convert('RGB')).astype(np.int16)
            after = np.array(Image.open(path).convert('RGB')).astype(np.int16)
            assert before.shape == after.shape
            difference = np.abs(before - after)
            # Geometry and all normals already checked independently. Record any
            # stochastic sampling/serialization differences honestly, without edits.
            checks.append({'file': frame['file'], 'new_render': True,
                           'pixels_exactly_equal': bool(not difference.any()),
                           'max_channel_difference_8bit': int(difference.max()),
                           'mean_absolute_channel_difference_8bit': float(difference.mean()),
                           'new_sha256': sha(path), 'baseline_sha256': sha(approved)})
        else:
            shutil.copyfile(approved, path)
            reuse.append({'file': frame['file'], 'sha256': sha(path),
                          'source': '../../ecorche-beatriz-combinaison-p4-p5/renders/' + frame['file']})
    (root / 'neutral-provenance.json').write_text(json.dumps({
        'new_neutral_render_checks': checks,
        'approved_neutral_views_reused_after_geometry_and_setup_verification': reuse,
        'reason': 'Unchanged geometry/material/lighting/cameras; avoid redundant CPU rendering.',
        'pixels_repainted': False,
    }, indent=2) + '\n')
    views = [('face', 'Face'), ('profil', 'Profil droit'), ('dos', 'Dos'), ('trois-quarts', 'Trois quarts')]
    records = []
    records.append(plate(root, 'planche-neutre.png', 'P4 + tête P5 — version neutre',
                         [(neutral / (v + '.png'), t) for v, t in views], 4, (540, 864), False))
    records.append(plate(root, 'planche-zones.png', 'Six zones indépendantes — contrôle des couleurs',
                         [(root / 'zones' / (v + '.png'), t) for v, t in views], 4, (540, 864)))
    shoulders = [('epaule-droite', 'Épaule droite — avant oblique'),
                 ('epaule-gauche', 'Épaule gauche — avant oblique'),
                 ('epaule-profil', 'Épaule droite — profil'),
                 ('epaule-arriere', 'Épaule droite — arrière oblique'),
                 ('epaules-face', 'Les deux épaules — face'),
                 ('epaules-dos', 'Les deux épaules — dos')]
    records.append(plate(root, 'planche-epaules-zones.png', 'Délimitations antérieure / latérale / postérieure',
                         [(root / 'zones' / (v + '.png'), t) for v, t in shoulders], 2, (720, 648)))
    records.append(plate(root, 'planche-epaules-neutres.png', 'Épaules P4 — matériau mat neutre commun',
                         [(neutral / (v + '.png'), t) for v, t in shoulders[:4]], 2, (720, 648), False))
    records.append(plate(root, 'comparatif-reference-neutre-zones.png',
                         'Même caméra — référence / neutre segmenté / contrôle',
                         [(reference / 'epaule-profil.png', '0ab3d83 — P4 original'),
                          (neutral / 'epaule-profil.png', 'Nouveau fichier — neutre'),
                          (root / 'zones/epaule-profil.png', 'Même surface — zones colorées')],
                         3, (720, 648)))
    (root / 'planches.json').write_text(json.dumps({
        'composition_only_no_geometry_or_image_retouching': True, 'plates': records,
        'compositor_sha256': sha(Path(__file__)),
    }, indent=2) + '\n')
    preview = root / 'preview'
    if preview.exists():
        shutil.rmtree(preview)  # Only this task's disposable low-sample previews.
    print('COMPOSED', json.dumps({'neutral_checks': checks, 'reused_views': len(reuse), 'plates': len(records)}))


if __name__ == '__main__':
    main()
