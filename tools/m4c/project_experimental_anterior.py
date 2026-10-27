"""Read-only camera control or local surface projection, on exact restored base."""
import argparse,json,sys
from pathlib import Path
import bpy,numpy as np
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
from PIL import Image
from scipy.interpolate import CubicSpline
from scipy.ndimage import distance_transform_edt,binary_dilation
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/m4c'))
from experimental_anterior import BASE,OUT,maps,project,axes
from scene import bv,render
from glb_io import sha
p=argparse.ArgumentParser();p.add_argument('--preview',action='store_true');a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
g=json.loads((OUT/'guide-camera.json').read_text());params=g['cameraParameters']
angle,elevation,distance,scale,cx,cy=params;r,u,z=axes(angle,elevation)
anchor=np.array(g['cameraAnchorSourceM']);location=anchor+z*distance
bpy.ops.wm.open_mainfile(filepath=str(BASE/'meshy-posterieurs-harmonises.blend'),use_scripts=False)
s=bpy.context.scene;mesh=bpy.data.objects['MESHY_M4C'].data;mat=mesh.materials[0]
def fitted_camera(multiplier=3):
    s.camera.location=bv(location)
    s.camera.rotation_euler=Matrix([bv(r),bv(u),bv(z)]).transposed().to_euler()
    s.camera.data.type='PERSP';s.camera.data.sensor_fit='HORIZONTAL';s.camera.data.sensor_width=36
    s.camera.data.lens=scale*distance/305*36
    s.camera.data.shift_x=(305/2-cx)/305;s.camera.data.shift_y=(cy-221/2)/305
    s.render.resolution_x=305*multiplier;s.render.resolution_y=221*multiplier;s.render.resolution_percentage=100
    bpy.context.view_layer.update()
fitted_camera();s.cycles.samples=16;s.cycles.seed=0;s.cycles.use_denoising=False
for node in mat.node_tree.nodes:
    if node.name.startswith('SHOW::'):node.outputs[0].default_value=int(node.name=='SHOW::deltoid.right.anterior')
rgb=mat.node_tree.nodes['COLOR::deltoid.right.anterior'];hexcolor='#ff932b'
c=np.array([int(hexcolor[i:i+2],16)/255 for i in (1,3,5)]);c=np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4);rgb.outputs[0].default_value=(*c,1)
if a.preview:
    render(s,ROOT.parent/'m4c-anterieur-cache/camera-control.png')
    print('CAMERA_CONTROL_ONLY; no masks changed',flush=True);sys.exit(0)

tree=BVHTree.FromPolygons([v.co[:] for v in mesh.vertices],[f.vertices[:] for f in mesh.polygons],all_triangles=True)
uv=np.load(ROOT/'docs/m4c/meshy-huit-zones/source-uv-binding.npz')['uv_blender'].copy();uv[:,:,1]=1-uv[:,:,1]
vertices=np.array([[v.co.x,v.co.z,-v.co.y] for v in mesh.vertices]);faces=np.array([f.vertices[:] for f in mesh.polygons])
def capture(pixel):
    # The input view is mirrored to the physical right side, not the texture.
    px,py=305-pixel[0],pixel[1]
    direction=(r*((px-cx)/(scale*distance))+u*((cy-py)/(scale*distance))-z)
    hit=tree.ray_cast(bv(location),bv(direction).normalized())
    assert hit[0] is not None,('Guide leaves actual surface',pixel)
    pt=np.array([hit[0].x,hit[0].z,-hit[0].y]);tri=vertices[faces[hit[2]]]
    ab=np.linalg.lstsq(np.column_stack([tri[1]-tri[0],tri[2]-tri[0]]),pt-tri[0],rcond=None)[0]
    return {'inputPixel':list(pixel),'point':pt.tolist(),'sourceFace':hit[2],'uv':(np.r_[1-ab.sum(),ab]@uv[hit[2]]).tolist()}
curve=[capture(p) for p in g['curvePixels']]
(OUT/'projected-curve.json').write_text(json.dumps({'samples':curve,'sourceGeometryChanged':False,'cameraMatrix':[list(row) for row in s.camera.matrix_world]},indent=2)+'\n')
old=np.array(Image.open(BASE/'textures/muscle-ids.png'));alpha=np.array(Image.open(BASE/'textures/deltoid.right.anterior.png'))
m=maps();covered=m['face']>=0;world=m['world'];nearest=m['nearest'];ny,nx=nearest
# Source chart padding is copied along the source triangle's screen-space
# derivative, so crossing UV seams cannot leave a constant-value spur.
sourcepoints=world[ny,nx];screen=project(sourcepoints.reshape(-1,3),params).reshape(2048,2048,2);screen[:,:,0]=305-screen[:,:,0]
controls=np.array(g['guideControlsPixels']);boundary=CubicSpline(controls[:,1],controls[:,0],bc_type='natural')
old_front=np.array([[130,75],[123,90],[126,104],[132,116],[142,132],[160,148],[185,164],[209,177]],float)
old_boundary=CubicSpline(old_front[:,1],old_front[:,0],bc_type='natural')
distance_from_old=distance_transform_edt(alpha<128)
# A conservative texture neighborhood excludes unrelated torso/back surfaces.
eligible=(np.isin(old,[0,6])&(distance_from_old<34)&(sourcepoints[:,:,0]<-.14)&
          (screen[:,:,1]>=controls[0,1])&(screen[:,:,1]<=controls[-1,1])&
          (screen[:,:,0]<=old_boundary(screen[:,:,1])+2)&
          (screen[:,:,0]>=boundary(screen[:,:,1])-1))
# The anterior/lateral frontier and its filtering neighborhood are immutable.
protected=binary_dilation(old==7,iterations=4)
eligible&=~protected
y,x=np.where(eligible);points=sourcepoints[y,x];q=screen[y,x]
visible=np.zeros(len(y),bool)
for i,pt in enumerate(points):
    hit=tree.ray_cast(bv(location),bv(pt-location).normalized())
    visible[i]=hit[0] is not None and (hit[0]-bv(pt)).length<.0015
y,x,points,q=y[visible],x[visible],points[visible],q[visible]
signed=(q[:,0]-boundary(q[:,1]))/np.sqrt(1+boundary(q[:,1],1)**2)
# Approximate one UV texel footprint in image pixels, including local slope.
# Use extrapolation in empty gutters, never modify their nearest surface point.
_,_,_,f=__import__('glb_io').source(ROOT/'assets/models/meshy-e45e5d8.glb')
faceids=m['face'][ny[y,x],nx[y,x]];foot=np.zeros((len(y),2,2))
for face in np.unique(faceids):
    selected=faceids==face;t=uv[face].astype(float)*2048-.5
    tri=project(vertices[f[face]],params);tri[:,0]=305-tri[:,0]
    foot[selected]=np.column_stack([tri[1]-tri[0],tri[2]-tri[0]])@np.linalg.inv(np.column_stack([t[1]-t[0],t[2]-t[0]]))
delta=np.column_stack([x-nx[y,x],y-ny[y,x]])
q=q+np.einsum('nij,nj->ni',foot,delta)
gradient=np.column_stack([np.ones(len(y)),-boundary(q[:,1],1)]);gradient/=np.linalg.norm(gradient,axis=1)[:,None]
signed=(q[:,0]-boundary(q[:,1]))/np.sqrt(1+boundary(q[:,1],1)**2)
aa=np.maximum(.12,np.abs(np.einsum('ni,nij->nj',gradient,foot)).sum(1))
desired=np.maximum(alpha[y,x],np.rint(np.clip(signed/aa+.5,0,1)*255).astype(np.uint8))
# Keep the side of the existing mask away from the pectoral edge unchanged.
near=np.abs(signed)<16
change=near&(desired!=alpha[y,x]);y,x,points,desired=y[change],x[change],points[change],desired[change]
np.savez_compressed(OUT/'surface-edit.npz',y=y,x=x,point=points,alpha=desired)
print('PROJECTED',len(curve),'SAMPLES; LOCAL EDIT',len(y),'TEXELS',flush=True)
