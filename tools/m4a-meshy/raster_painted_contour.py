"""Rasterize the authored cubic selection stencil, with supersampled edge coverage."""
import argparse,re,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prepared',type=Path,required=True);a=p.parse_args()
root=a.prepared/'texture-poc';svg=ET.parse(root/'painted-contour.svg').getroot();path=svg.find('{http://www.w3.org/2000/svg}path').attrib['d']
parts=re.findall(r'[MCZ]|-?\d+(?:\.\d+)?',path);assert parts.pop(0)=='M';point=np.array([float(parts.pop(0)),float(parts.pop(0))]);points=[point]
while parts[0]!='Z':
 assert parts.pop(0)=='C';controls=np.array([point,*[np.array([float(parts.pop(0)),float(parts.pop(0))]) for _ in range(3)]])
 for t in np.linspace(0,1,65)[1:]:points.append((1-t)**3*controls[0]+3*(1-t)**2*t*controls[1]+3*(1-t)*t*t*controls[2]+t**3*controls[3])
 point=controls[3]
im=Image.new('L',(4000,3360),0);ImageDraw.Draw(im).polygon([tuple(4*q) for q in points],fill=255)
im.resize((1000,840),Image.Resampling.LANCZOS).save(root/'textures/projection-stencil.png')
print('AUTHORED_STENCIL_RASTERIZED')
