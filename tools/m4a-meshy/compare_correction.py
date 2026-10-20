"""Place unretouched Blender renders side by side; resize only for layout/mobile width."""
import argparse,json,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mesh_io import sha
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prepared',type=Path,required=True)
a=p.parse_args();root=a.prepared.resolve();out=root/'correction/renders';records=[]
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
def pair(name,left,right,width,caption):
 images=[]
 for file in [left,right]:
  im=Image.open(file).convert('RGB');im=im.resize((width,round(im.height*width/im.width)),Image.Resampling.LANCZOS);images.append(im)
 result=Image.new('RGB',(2*width,max(i.height for i in images)+72),'#0a1722');draw=ImageDraw.Draw(result)
 for i,(image,label) in enumerate(zip(images,['AVANT · ff09299','APRES · passe locale'])):
  result.paste(image,(i*width,42));draw.text((i*width+12,12),label,font=font,fill='#ebf3ff')
 draw.text((12,result.height-26),caption,font=font,fill='#cbd8e7');file=out/name;result.save(file)
 records.append({'file':name,'sha256':sha(file.read_bytes()),'inputs':[{'file':str(f.relative_to(root)),'sha256':sha(f.read_bytes())} for f in [left,right]],'operation':'Side-by-side layout, text labels and proportional LANCZOS resize only; no muscle recoloring or contour edit.','panel_width':width,'size':list(result.size)})
pair('comparison-mobile-390.png',root/'renders/selection.png',out/'after-left-three-quarter.png',390,'Chaque panneau : 390 px de large, corps entier')
for stem in ['left-detail','deltoid-profile','deltoid-back']:
 pair('comparison-'+stem+'.png',out/('before-'+stem+'.png'),out/('after-'+stem+'.png'),700,'Meme camera, eclairage et 48 echantillons Cycles')
(out/'comparisons-metadata.json').write_text(json.dumps({'script_sha256':sha(Path(__file__).read_bytes()),'comparisons':records},ensure_ascii=False,indent=2)+'\n')
print('COMPARISONS_CREATED',len(records))
