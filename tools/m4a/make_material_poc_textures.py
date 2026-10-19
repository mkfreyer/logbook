#!/usr/bin/env python3
"""Author original anatomical-flow normal/surface maps, using only NumPy/Pillow."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--size',type=int,default=1024);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
N=a.size;u,v=np.meshgrid((np.arange(N)+.5)/N,(np.arange(N)+.5)/N)
def sig(x):
 x=np.clip(x,0,1);return x*x*(3-2*x)
def normal(height,width,length):
 dv,du=np.gradient(height,length/N,width/N)
 n=np.stack([-du,-dv,np.ones_like(du)],-1);n/=np.linalg.norm(n,axis=-1,keepdims=True)
 return np.round(np.clip(n*.5+.5,0,1)*255).astype(np.uint8)
files=[]
for zone in ['pectoral','deltoid']:
 mask=sig((u-.015)/.065)*sig((.985-u)/.065)*sig((v-.012)/.060)*sig((.988-v)/.060)
 if zone=='pectoral':
  phase=v+.027*np.sin(np.pi*u)*(v-.45)+.010*np.sin(2*np.pi*u)*(1-v)
  belly=.0060*np.sin(np.pi*u)**.8*np.sin(np.pi*v)**.7
  boundaries=np.array([.055,.155,.280,.420,.570,.710,.835,.935]);bundles=np.zeros_like(u)
  for j,center in enumerate(boundaries):
   width=[.045,.050,.052,.058,.056,.052,.043,.031][j]
   d=(phase-center)/width;bundles+=(.0011+.00075*np.sin(j*1.7)**2)*np.exp(-d*d*1.6)
  taper=sig((u-.025)/.15)*sig((.985-u)/.17)
  fibrils=np.sin((phase*39+.10*np.sin(2*np.pi*u*1.3+v*3))*2*np.pi)
  fibrils+=.35*np.sin((phase*73+.19*np.sin(2*np.pi*u*.9))*2*np.pi)
  fibre=.00027*fibrils*taper
  height=(belly+bundles*taper+fibre)*mask
  rough=.365-.048*fibrils*taper+.045*(1-np.sin(np.pi*v))
  tone=.965+.035*np.tanh((bundles-.0008)*900)+.014*fibrils*taper
  width_m,length_m=.224,.145
 else:
  phi=(u-.5)*4.6;t=np.clip((v*1.2-.15),0,1)
  flow=phi/(1-.53*t);heads=np.zeros_like(u)
  for center,width,amp in [(-.95,.48,.0048),(0,.44,.0055),(.90,.50,.0046)]:
   heads+=amp*np.exp(-((phi-center*(1-.43*t))/width)**2)
  taper=sig((v-.015)/.15)*sig((.99-v)/.25)
  fascicles=.00065*np.exp(-((np.sin(flow*9+.12*np.sin(v*5)))/.42)**2)
  fibrils=np.sin(flow*39+.35*np.sin(v*5+flow))+.35*np.sin(flow*71+.20*np.sin(v*8))
  height=(heads+fascicles+.00024*fibrils)*taper*mask
  rough=.375-.043*fibrils*taper+.035*(1-np.clip(heads/.006,0,1))
  tone=.97+.030*np.clip(heads/.006,0,1)+.012*fibrils*taper
  width_m,length_m=.235,.225
 # RGBA surface atlas: region coverage, linear roughness, encoded tone, fibre detail.
 surface=np.stack([mask,np.clip(rough,.27,.49),np.clip((tone-.80)/.40,0,1),np.clip(.5+.24*fibrils,0,1)],-1)
 for suffix,array in [('normal',normal(height,width_m,length_m)),('surface',np.round(surface*255).astype(np.uint8))]:
  # Blender UV v=0 addresses the bottom image row.
  file=a.output/(zone+'-'+suffix+'.png');Image.fromarray(np.flipud(array)).save(file)
  files.append({'path':file.name,'bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'channels':array.shape[-1]})
report={'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'resolution':[N,N],'source':'Original procedural anatomy-flow artwork; no downloaded image, paid tool, AI image or third-party anatomy.',
 'files':files,'normal_convention':'Tangent-space OpenGL +Y, RGB8, non-color; generated from virtual height, no mesh displacement.',
 'surface_channels':{'R':'region coverage','G':'linear roughness','B':'tone encoded (0.80 + 0.40*B)','A':'fibre modulation diagnostic'},
 'gpu_estimate':'Four RGBA8 textures: 16 MiB at 1024x1024 without mipmaps, about 21.33 MiB with full mip chains; engine-dependent, not measured.'}
(a.output/'textures.json').write_text(json.dumps(report,indent=2)+'\n');print('Four original 1024 textures authored.')
