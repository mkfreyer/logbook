"""Assemble Blender controls without recoloring or retouching captures; audit PNG mask."""
import argparse,json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy import ndimage
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mesh_io import sha
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prepared',type=Path,required=True);a=p.parse_args();root=a.prepared.resolve();out=root/'texture-poc'
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18);records=[]
def pair(name,first,second,width):
 inputs=[first,second];images=[]
 for file in inputs:
  image=Image.open(file).convert('RGB');images.append(image.resize((width,round(image.height*width/image.width)),Image.Resampling.LANCZOS))
 result=Image.new('RGB',(width*2,images[0].height+42),'#0a1722');draw=ImageDraw.Draw(result)
 for i,label in enumerate(['AVANT · triangles 898aac6','POC UNIQUE · masque peint']):
  result.paste(images[i],(i*width,42));draw.text((i*width+10,12),label,font=font,fill='#eaf2ff')
 file=out/'renders'/name;result.save(file)
 records.append({'file':name,'sha256':sha(file.read_bytes()),'panel_width':width,'inputs':[{'file':str(f.relative_to(root)),'sha256':sha(f.read_bytes())} for f in inputs],'operations':'Proportional resize, text labels and side-by-side composition only. No muscle recoloring, lighting, sharpening or contour retouch.'})
pair('comparison-detail.png',root/'correction/renders/after-left-detail.png',out/'renders/painted-detail.png',700)
pair('comparison-profile.png',out/'renders/triangles-profile.png',out/'renders/painted-profile.png',700)
pair('comparison-mobile-390.png',root/'correction/renders/after-left-three-quarter.png',out/'renders/painted-three-quarter.png',390)
image=Image.open(out/'textures/pectoralis-left-mask.png').convert('L');mask=np.array(image);binary=mask>=128
labels,n=ndimage.label(binary);holes=ndimage.binary_fill_holes(binary)&~binary
assert n==1 and not holes.any()
original=np.array(Image.open(root/'correction/renders/after-neutral-front.png'));neutral=np.array(Image.open(out/'renders/neutral-front.png'));assert np.array_equal(original,neutral)
report={'script_sha256':sha(Path(__file__).read_bytes()),'mask_sha256':sha((out/'textures/pectoralis-left-mask.png').read_bytes()),'mask_components_at_half_threshold':n,'mask_hole_texels_at_half_threshold':int(holes.sum()),'selected_mask_texels':int(binary.sum()),'neutral_render_pixel_identical_to_898aac6':True,'comparisons':records}
(out/'comparisons-and-mask-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('TEXTURE_COMPARISONS',len(records),'mask_components',n)
