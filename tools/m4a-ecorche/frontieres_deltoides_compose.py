"""Compare native Blender renders without repainting any model pixels."""
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


def plate(root, name, title, entries, columns=2, color_legend=True):
    cell_w, cell_h, label_h = 720, 648, 44
    rows = (len(entries) + columns - 1) // columns
    image = Image.new('RGB', (cell_w * columns, 108 + rows * (cell_h + label_h) + 62), '#181818')
    draw = ImageDraw.Draw(image)
    font = lambda n: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', n)
    draw.text((20, 12), title, font=font(27), fill='white')
    subtitle = ('Antérieur rouge • Moyen bleu • Postérieur vert — aucune sculpture'
                if color_legend else 'Matériau mat neutre — aucune sculpture, mêmes formes P4')
    draw.text((20, 54), subtitle, font=font(20), fill='#dddddd')
    for i, (source, label) in enumerate(entries):
        im = Image.open(source).convert('RGB')
        im.thumbnail((cell_w, cell_h), Image.Resampling.LANCZOS)
        x, y = (i % columns) * cell_w, 108 + (i // columns) * (cell_h + label_h)
        draw.text((x + 12, y + 8), label, font=font(21), fill='white')
        image.paste(im, (x + (cell_w - im.width) // 2, y + label_h + (cell_h - im.height) // 2))
    draw.text((20, image.height - 42), 'P4 + tête P5 — sommets d’origine conservés ; découpage local des frontières uniquement.',
              font=font(18), fill='#dddddd')
    path = root / name
    image.save(path)
    return {'file': name, 'sha256': sha(path),
            'sources': [os.path.relpath(p, root) for p, _ in entries]}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--asset', type=Path, required=True)
    p.add_argument('--baseline-asset', type=Path, required=True)
    args = p.parse_args()
    asset, baseline = args.asset.resolve(), args.baseline_asset.resolve()
    root = asset / 'renders'
    verification = json.loads((asset / 'verification.json').read_text())
    assert verification['all_original_surface_vertices_unchanged']
    original_frames = {r['file']: r for r in json.loads((baseline / 'renders/zones/metadata.json').read_text())['frames']}
    new_before = {r['file']: r for r in json.loads((root / 'before/metadata.json').read_text())['frames']}
    after = {r['file']: r for r in json.loads((root / 'after/metadata.json').read_text())['frames']}
    provenance = []
    for name, frame in after.items():
        before_frame = new_before.get(name, original_frames.get(name))
        assert before_frame is not None
        for key in ['camera_matrix', 'ortho_scale', 'resolution']:
            assert frame[key] == before_frame[key], (name, key)
        source = root / 'before' / name if name in new_before else baseline / 'renders/zones' / name
        assert sha(source) == before_frame['sha256']
        assert sha(root / 'after' / name) == frame['sha256']
        provenance.append({'file': name, 'before_source': os.path.relpath(source, root),
                           'before_sha256': sha(source), 'after_sha256': frame['sha256'],
                           'camera_and_resolution_identical': True})
    neutral_checks = []
    for name in ['epaule-profil.png', 'epaule-droite.png']:
        before_path = baseline / 'renders/neutral' / name
        new_path = root / 'neutral' / name
        before = np.array(Image.open(before_path).convert('RGB')).astype(np.int16)
        new = np.array(Image.open(new_path).convert('RGB')).astype(np.int16)
        d = np.abs(before - new)
        neutral_checks.append({'file': name, 'pixels_identical': bool(not d.any()),
                               'changed_pixels_percent': float(np.any(d, axis=2).mean() * 100),
                               'max_channel_difference_8bit': int(d.max()),
                               'mean_channel_difference_8bit': float(d.mean()),
                               'before_sha256': sha(before_path), 'after_sha256': sha(new_path)})
    def before_path(view):
        return (root / 'before' if view + '.png' in new_before else baseline / 'renders/zones') / (view + '.png')
    entries = []
    for view, label in [('epaule-profil', 'Profil droit'), ('epaule-droite', 'Trois quarts droit'),
                        ('epaules-face', 'Face — deux épaules'), ('epaules-dos', 'Dos — deux épaules')]:
        entries += [(before_path(view), label + ' — fb68f5e'),
                    (root / 'after' / (view + '.png'), label + ' — frontières découpées')]
    plates = [plate(root, 'comparatif-frontieres.png', 'Avant / après — mêmes caméras et éclairage', entries)]
    close = [('epaule-face-droite', 'Épaule droite — face'), ('epaule-face-gauche', 'Épaule gauche — face'),
             ('epaule-droite', 'Épaule droite — trois quarts'), ('epaule-gauche', 'Épaule gauche — trois quarts'),
             ('epaule-profil', 'Profil droit'), ('epaules-dos', 'Dos — six zones indépendantes')]
    plates.append(plate(root, 'controle-six-zones.png', 'Frontières continues — contrôle des six zones',
                        [(root / 'after' / (view + '.png'), label) for view, label in close]))
    plates.append(plate(root, 'comparatif-neutre.png', 'Neutre avant / après — conservation visuelle de P4', [
        (baseline / 'renders/neutral/epaule-profil.png', 'Profil — P4 dans fb68f5e'),
        (root / 'neutral/epaule-profil.png', 'Profil — découpage local, neutre'),
        (baseline / 'renders/neutral/epaule-droite.png', 'Trois quarts — P4 dans fb68f5e'),
        (root / 'neutral/epaule-droite.png', 'Trois quarts — découpage local, neutre')], color_legend=False))
    plates.append(plate(root, 'epaules-face-neutres.png', 'Deux épaules — matériau mat neutre', [
        (root / 'neutral/epaule-face-droite.png', 'Épaule droite — neutre'),
        (root / 'neutral/epaule-face-gauche.png', 'Épaule gauche — neutre')], color_legend=False))
    (root / 'comparisons.json').write_text(json.dumps({
        'before_after_views': provenance, 'neutral_checks': neutral_checks,
        'plates': plates, 'pixels_repainted': False,
        'compositor_sha256': sha(Path(__file__)),
    }, indent=2) + '\n')
    preview = root / 'preview'
    if preview.exists():
        shutil.rmtree(preview)
    print('COMPOSED', json.dumps({'neutral_checks': neutral_checks, 'plates': len(plates)}))


if __name__ == '__main__':
    main()
