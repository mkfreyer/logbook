"""Lay out unretouched Blender images and audit matched before/after cameras."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--asset', type=Path, required=True)
    a = p.parse_args()
    root = a.asset
    meta = json.loads((root/'finition.json').read_text())
    manifests = {mode: json.loads((root/'renders'/mode/'metadata.json').read_text())
                 for mode in ['before', 'after']}
    assert manifests['before']['master_sha256'] == meta['baseline_blend_sha256']
    assert manifests['after']['master_sha256'] == meta['master_sha256']
    frames = {mode: {r['file']: r for r in manifest['frames']}
              for mode, manifest in manifests.items()}
    assert set(frames['before']) == set(frames['after'])
    assert len(frames['before']) == 4
    for file, before in frames['before'].items():
        after = frames['after'][file]
        for key in ['camera_matrix', 'ortho_scale', 'resolution']:
            assert before[key] == after[key], (file, key)
        for mode in frames:
            path = root/'renders'/mode/file
            assert hashlib.sha256(path.read_bytes()).hexdigest() == frames[mode][file]['sha256']
    font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    title_font = ImageFont.truetype(font_path, 29)
    label_font = ImageFont.truetype(font_path, 22)
    small_font = ImageFont.truetype(font_path, 18)

    def board(name, title, entries, cols, width, crop=None):
        margin, header, caption, footer = 22, 86, 38, 52
        sample = Image.open(root/'renders'/entries[0][0]/(entries[0][1]+'.png'))
        if crop:
            sample = sample.crop(crop)
        height = round(sample.height*width/sample.width)
        rows = (len(entries)+cols-1)//cols
        image = Image.new('RGB', (cols*(width+margin)+margin,
                                  header+rows*(height+caption+margin)+footer), '#141b24')
        draw = ImageDraw.Draw(image)
        draw.text((margin, 18), title, font=title_font, fill='#f0f4fa')
        draw.text((margin, 54), 'Même matériau mat, mêmes caméras, mêmes lumières — Blender / Cycles',
                  font=small_font, fill='#bac7d6')
        for i, (mode, view, label) in enumerate(entries):
            x, y = margin+(i%cols)*(width+margin), header+(i//cols)*(height+caption+margin)
            draw.text((x, y), label, font=label_font, fill='#f0f4fa')
            src = Image.open(root/'renders'/mode/(view+'.png')).convert('RGB')
            if crop:
                src = src.crop(crop)
            image.paste(src.resize((width, height), Image.Resampling.LANCZOS), (x, y+caption))
        draw.text((margin, image.height-footer+8),
                  'Référence d79692f • Proposition locale pour validation • Aucune intégration',
                  font=small_font, fill='#bac7d6')
        image.save(root/'renders'/name)

    board('comparatif-aine.png', 'Aine / pubis — avant et après', [
        ('before', 'aine-face', 'Avant — face'), ('after', 'aine-face', 'Après — face'),
        ('before', 'aine-trois-quarts', 'Avant — trois quarts'),
        ('after', 'aine-trois-quarts', 'Après — trois quarts')], 2, 850)
    board('planche-neutre.png', 'Contrôle à l’échelle du mannequin', [
        ('before', 'face', 'Avant — face'), ('after', 'face', 'Après — face'),
        ('before', 'trois-quarts', 'Avant — 3/4'), ('after', 'trois-quarts', 'Après — 3/4')], 4, 360)
    board('comparatif-central-serre.png', 'Région centrale — détail avant / après', [
        ('before', 'aine-face', 'Avant — d79692f'),
        ('after', 'aine-face', 'Après — proposition')], 2, 640, crop=(280, 300, 720, 650))
    (root/'renders/verification.json').write_text(json.dumps({
        'matched_before_after_views': 4, 'camera_matrices_scale_and_resolution_equal': True,
        'render_file_hashes_verified': 8,
        'image_processing': 'Board labels, uniform resizing and identical detail crop only; individual renders untouched.',
        'detail_crop_box_px': [280, 300, 720, 650],
        'baseline_sha256': meta['baseline_blend_sha256'], 'master_sha256': meta['master_sha256'],
        'compositor_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }, indent=2)+'\n')


if __name__ == '__main__':
    main()
