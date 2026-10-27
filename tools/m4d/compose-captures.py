"""Compose/crop actual WebGL screenshots; never repaint mannequin pixels."""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont
root = Path('docs/m4d/selection-interactive')
audit = json.loads((root / 'browser-verification.json').read_text())
assert audit['status'] == 'passed'
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 17)
small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 13)
board = Image.new('RGB', (1248, 604), '#101c29')
d = ImageDraw.Draw(board)
d.text((16, 10), 'M4D-A • 8 sélections indépendantes • captures WebGL recadrées', font=font, fill='white')
d.text((16, 36), 'Chromium / SwiftShader • pas de capture iPhone • aucun pixel du modèle repeint', font=small, fill='#b8cadb')
for k, item in enumerate(audit['eightMuscles']):
    picture = Image.open(root / f"selection-{item['id']}.png").convert('RGB')
    x = max(0, min(picture.width-300, round(item['touch']['x'])-150))
    y = max(0, min(picture.height-215, round(item['touch']['y'])-100))
    crop = picture.crop((x, y, x+300, y+215))
    px, py = 12+(k%4)*312, 70+(k//4)*266
    board.paste(crop, (px, py))
    d.text((px+4, py+221), item['label'], font=small, fill='white')
board.save(root / 'planche-huit-selections.png')
