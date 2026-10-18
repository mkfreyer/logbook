"""Presentation layout only: source PNGs are resized uniformly, without retouching."""
from pathlib import Path
import argparse
from PIL import Image,ImageDraw,ImageFont
parser=argparse.ArgumentParser(description='Assemble the nine unretouched M4A renders into a labelled contact sheet.')
parser.add_argument('--renders-root',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--font',default='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
a=parser.parse_args()
base=a.renders_root
items=[('A','mpfb-athletic','MakeHuman / MPFB'),('B','studio-realistic','Blender Studio · Réaliste'),('C','studio-stylized','Blender Studio · Stylisé')]
views=[('front','Face · 0°'),('three-quarter','Trois quarts · −35°'),('back','Dos · 180°')]
fontpath=a.font
font=lambda n:ImageFont.truetype(fontpath,n)
w=1848;cellw=600;cellh=933;gap=12;top=164;rowtitle=48
board=Image.new('RGB',(w,top+3*(cellh+rowtitle+gap)+64),(12,20,34));d=ImageDraw.Draw(board)
d.text((24,20),'M4A — Choix du mannequin',font=font(38),fill='#edf3ff')
d.text((24,74),'Géométries réelles · Même caméra, matériau et éclairage · Aucun modèle intégré',font=font(21),fill='#b8c6dc')
for col,(letter,key,title) in enumerate(items):
 d.text((gap+col*(cellw+gap)+12,122),f'{letter} · {title}',font=font(22),fill='#edf3ff')
for row,(view,label) in enumerate(views):
 y=top+row*(cellh+rowtitle+gap)
 d.text((24,y+5),label,font=font(24),fill='#b8c6dc')
 for col,(_,key,_) in enumerate(items):
  p=base/key/(view+'.png')
  im=Image.open(p).convert('RGB').resize((cellw,cellh),Image.Resampling.LANCZOS)
  board.paste(im,(gap+col*(cellw+gap),y+rowtitle))
d.text((24,board.height-45),'Sources CC0 · Poses natives conservées · Référence d’origine à joindre pour validation finale',font=font(21),fill='#b8c6dc')
a.output.parent.mkdir(parents=True,exist_ok=True)
board.save(a.output)
print(a.output)
