"""Real Blender renders, matched cameras/lights. Never recolors screenshots."""
import argparse,json,sys
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from scene import camera,render
from glb_io import sha
p=argparse.ArgumentParser();p.add_argument('--inspection',action='store_true');args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
root=Path(__file__).resolve().parents[2];out=root/'docs/m4c/meshy-huit-zones';dest=out/'renders'
bpy.ops.wm.open_mainfile(filepath=str(out/'meshy-eight-zones.blend'),use_scripts=False)
s=bpy.context.scene;s.cycles.samples=24;s.cycles.use_denoising=False
ob=bpy.data.objects['MESHY_M4C'];mat=ob.data.materials[0];spec=json.loads((out/'regions.json').read_text())
record={'engine':'Blender 4.3.2 / Cycles CPU','samples':24,'seed':0,'denoising':False,'blend_sha256':sha((out/'meshy-eight-zones.blend').read_bytes()),'frames':[]}

def state(active):
    for zone in spec['zones']:mat.node_tree.nodes['SHOW::'+zone['id']].outputs[0].default_value=1 if active is True or zone['id'] in active else 0

def shot(name,angle,target,scale,res=(800,800)):
    camera(s,angle,target,scale,res);file=dest/(name+'.png');render(s,file)
    record['frames'].append({'file':file.name,'angle':angle,'target':target,'ortho_scale':scale,'resolution':list(res),'camera_matrix':[list(r) for r in s.camera.matrix_world],'sha256':sha(file.read_bytes())})
    (dest/('inspection-metadata.json' if args.inspection else 'render-metadata.json')).write_text(json.dumps(record,indent=2)+'\n')
state(True)
if args.inspection:
    for name,angle in [('front',0),('left',90),('back',150)]:shot('inspection-'+name,angle,(.13,.515,-.025),.44,(640,640))
else:
    for name,angle in [('face',0),('profil-gauche',90),('profil-droit',-90),('trois-quarts-avant',45),('trois-quarts-arriere',135),('dos',180)]:
        shot('zones-'+name,angle,(0,.505,-.02),.7,(900,780))
    for side,x,sign in [('gauche',.10,1),('droit',-.10,-1)]:shot('pectoral-'+side,sign*15,(x,.52,.075),.30,(640,640))
    for side,x,sign in [('gauche',.225,1),('droit',-.225,-1)]:
        for view,angle in [('avant',45),('arriere',135)]:shot('deltoide-'+side+'-'+view,sign*angle,(x,.555,-.055),.29,(640,640))
    state({'pectoralis.left'});shot('independance-pectoral-gauche',0,(0,.52,0),.69,(900,780))
    state(set());shot('neutre-complet',0,(0,0,0),2.05,(700,1100))
    for name,angle in [('face',0),('profil',90),('dos',180)]:shot('neutre-'+name,angle,(0,.505,-.02),.7,(900,780))
    ref=bpy.data.materials.new('REFERENCE_NEUTRE_INTACTE');ref.use_nodes=True
    bs=ref.node_tree.nodes['Principled BSDF'];bs.inputs['Base Color'].default_value=(.5,.52,.55,1);bs.inputs['Metallic'].default_value=0;bs.inputs['Roughness'].default_value=.86
    ob.data.materials[0]=ref
    for name,angle in [('face',0),('profil',90),('dos',180)]:shot('reference-'+name,angle,(0,.505,-.02),.7,(900,780))
print('RENDERED',len(record['frames']),flush=True)
