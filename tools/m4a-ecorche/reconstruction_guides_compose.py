"""Compose only real Blender pixels; draw a separate measured topology diagram."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont

p=argparse.ArgumentParser();p.add_argument('--asset',type=Path,required=True);a=p.parse_args()
root=a.asset/'renders';fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
font=lambda n:ImageFont.truetype(fontpath,n);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rows=[]
def pair(name,title,files,crop=None,size=(600,720)):
    canvas=Image.new('RGB',(size[0]*2+60,size[1]+180),'#171a1e');d=ImageDraw.Draw(canvas)
    d.text((20,16),title,font=font(26),fill='white')
    d.text((20,54),'ESSAI NON VALIDÉ — 7 intersections par épaule ; aucun changement applicatif',font=font(18),fill='#e2b47b')
    for i,(filename,label) in enumerate(files):
        image=Image.open(root/filename).convert('RGB')
        if crop:image=image.crop(tuple(int(c*3)for c in crop))
        scale=min(size[0]/image.width,size[1]/image.height)
        image=image.resize((round(image.width*scale),round(image.height*scale)),Image.Resampling.LANCZOS)
        x=20+i*(size[0]+20);d.text((x,86),label,font=font(21),fill='white')
        canvas.paste(image,(x+(size[0]-image.width)//2,120))
    d.text((20,canvas.height-35),'Même caméra, mat neutre et lumières • pixels Blender sans retouche',font=font(17),fill='#bfc3c9')
    path=root/(name+'.png');canvas.save(path)
    rows.append({'file':path.name,'sha256':sha(path),'sources':[{'file':f,'sha256':sha(root/f)}for f,l in files],'crop_reference_px':crop})

for label,title in [('reference','Vue de référence — avant / après serré'),('epaule-gauche','Épaule gauche — avant / après'),
                    ('face','Face — avant / après'),('profil','Profil — avant / après'),
                    ('trois-quarts','Trois quarts — avant / après'),('arriere-oblique','Arrière oblique — avant / après')]:
    pair('comparatif-'+label,title,[('avant-'+label+'.png','Référence P4 + tête P5'),('apres-'+label+'.png','Reconstruction locale — non validée')])
pair('bombe-preserve','Bombé central — surface géométrique conservée',[
    ('avant-reference.png','P4 — référence'),('apres-reference.png','Après — mêmes points protégés')],(90,135,170,260),size=(500,650))
pair('creux-1-detail','Premier creux — terminaison et raccord à examiner',[
    ('avant-reference.png','Avant'),('apres-reference.png','Après — marques résiduelles')],(30,270,115,384),size=(500,650))
pair('creux-2-detail','Second creux — reconstruction et raccord à examiner',[
    ('avant-reference.png','Avant'),('apres-reference.png','Après — raccord non conforme')],(130,120,250,380),size=(500,650))
(root/'planches.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')

# Measured mesh projection, kept separate from the photographic render sheets.
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
s=np.load(a.asset/'surface.npz');source=np.load(a.asset.parent/'ecorche-beatriz-creux-localises/source.npz')
fig,axes=plt.subplots(1,2,figsize=(11,8),facecolor='#f5f5f3')
for ax,uv,f,title in [(axes[0],source['uv'],s['original_f'],'P4 — 11 938 triangles / deltoïde'),
                       (axes[1],s['uv'],s['f'],'Après — 53 984 triangles / deltoïde')]:
    ax.set_facecolor('#f5f5f3')
    # Only front-facing triangles in this camera chart are shown.
    t=uv[f];area=(t[:,1,0]-t[:,0,0])*(t[:,2,1]-t[:,0,1])-(t[:,1,1]-t[:,0,1])*(t[:,2,0]-t[:,0,0])
    show=f[area<0];edges=np.sort(np.concatenate([show[:,[0,1]],show[:,[1,2]],show[:,[2,0]]]),axis=1);edges=np.unique(edges,axis=0)
    ax.add_collection(LineCollection(uv[edges],colors='#53687c',linewidths=.18))
    ax.set(xlim=(20,265),ylim=(384,60),aspect='equal',title=title)
    ax.set_xlabel('Pixels de la caméra de référence');ax.set_ylabel('Pixels')
fig.suptitle('Topologie locale — projection des véritables triangles, pas un rendu retouché')
fig.tight_layout();fig.savefig(root/'topologie-locale.png',dpi=160);plt.close(fig)
print('COMPOSED',len(rows),'sheets and one topology figure')
