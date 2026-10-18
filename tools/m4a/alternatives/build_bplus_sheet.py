"""Lay out real B/B+ renders; use equal resizing and equal crops, without retouching."""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--original-root', type=Path, required=True)
parser.add_argument('--original-side-root', type=Path, required=True)
parser.add_argument('--variant-root', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--detail-output', type=Path)
parser.add_argument('--font', default='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
args = parser.parse_args()
font = lambda size: ImageFont.truetype(args.font, size)
background, foreground, muted = '#0c1422', '#edf3ff', '#b8c6dc'
views = [('front', 'Face · 0°'), ('three-quarter', 'Trois quarts · −35°'),
         ('back', 'Dos · 180°'), ('side', 'Profil · 90°')]
canvas = Image.new('RGB', (1236, 4156), background)
draw = ImageDraw.Draw(canvas)
draw.text((20, 16), 'M4A — B original / B+ modérément athlétique', font=font(29), fill=foreground)
draw.text((20, 62), 'Même pose, cadrage, matière et lumière · Rendus de vraies géométries', font=font(21), fill=muted)
draw.text((20, 102), 'B original', font=font(24), fill=foreground)
draw.text((632, 102), 'B+ proposé', font=font(24), fill=foreground)
for row, (view, label) in enumerate(views):
    y = 146 + row * 989
    draw.text((20, y), label, font=font(24), fill=muted)
    original = args.original_side_root if view == 'side' else args.original_root
    for col, root in enumerate([original, args.variant_root]):
        image = Image.open(root / (view + '.png')).convert('RGB')
        if image.size != (900, 1400):
            raise ValueError('Expected final 900 × 1400 render')
        canvas.paste(image.resize((600, 933), Image.Resampling.LANCZOS), (12 + col * 612, y + 44))
draw.text((20, 4120), 'CC0 · Variante réversible · Aucune intégration · Choix utilisateur attendu', font=font(21), fill=muted)
args.output.parent.mkdir(parents=True, exist_ok=True)
canvas.save(args.output)
if args.detail_output:
    detail = Image.new('RGB', (1236, 740), background)
    d = ImageDraw.Draw(detail)
    d.text((20, 14), 'Détail du torse — même découpe des rendus de face', font=font(28), fill=foreground)
    for col, (title, root) in enumerate([('B original', args.original_root), ('B+ proposé', args.variant_root)]):
        d.text((20 + col * 612, 62), title, font=font(24), fill=foreground)
        image = Image.open(root / 'front.png').convert('RGB')
        detail.paste(image.crop((225, 300, 675, 775)).resize((600, 633), Image.Resampling.LANCZOS), (12 + col * 612, 102))
    detail.save(args.detail_output)
print(args.output)
