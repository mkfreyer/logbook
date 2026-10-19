"""Assemble paired BP3D Blender renders and honest 390px full-body previews."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path('docs/m4a/bp3d-fitness'));a=p.parse_args()
out=a.root/'comparisons';out.mkdir(exist_ok=True)
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def f(size):return ImageFont.truetype(font,size)
names={'soft':'D1 — Anatomique adouci','defined':'D2 — Anatomique accentué'}
views={'front':'Face','three-quarter':'Trois quarts','back':'Dos','selection':'Pectoral gauche sélectionné'}
manifest={'method':'Original Blender PNGs, Lanczos resize only; fixed full-body framing. No image synthesis or local retouch.','column_width':390,'mobile_preview_width':390,'images':[]}
for view,title in views.items():
 canvas=Image.new('RGB',(820,750),'#0b1724');draw=ImageDraw.Draw(canvas)
 draw.text((20,14),title,font=f(22),fill='#e3ebf5')
 for col,(key,name) in enumerate(names.items()):
  file=a.root/key/'renders'/(view+'.png');im=Image.open(file).convert('RGB');assert im.size==(720,1152)
  im=im.resize((390,624),Image.Resampling.LANCZOS);x=10+410*col
  canvas.paste(im,(x,80));draw.text((x+6,50),name,font=f(17),fill='#cbdaf0')
  if view=='three-quarter':
   mobile=out/(key+'-mobile-390.png');im.save(mobile)
   manifest['images'].append({'path':mobile.name,'sha256':hashlib.sha256(mobile.read_bytes()).hexdigest(),'source':str(file.relative_to(a.root)),'width':390,'height':624})
 draw.text((20,719),'Exploration non retenue comme base finale — mêmes caméra et matériau',font=f(16),fill='#b8c7da')
 file=out/(view+'.png');canvas.save(file)
 manifest['images'].append({'path':file.name,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'source_view':view,'width':820,'height':750})
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
