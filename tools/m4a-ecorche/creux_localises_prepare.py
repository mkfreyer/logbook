"""Extract only the validated 0ab3d83 geometry and calibrate the reference crop."""
import argparse,hashlib,json,math,sys
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--preview',action='store_true')
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.output.resolve();root.mkdir(parents=True,exist_ok=True)
assert hashlib.sha256(a.baseline.read_bytes()).hexdigest()=='f8b6a232a18335221af3cafc62b37837fedc1caaf9bc6cb48e1cb583f222d9ab'
bpy.ops.wm.open_mainfile(filepath=str(a.baseline.resolve()),use_scripts=False)
scene=bpy.data.scenes['16_COMBINAISON_P4_P5'];bpy.context.window.scene=scene;scene.view_layers[0].update();g=bpy.context.evaluated_depsgraph_get();ob=scene.objects['P4P5__deltoid.right'];ev=ob.evaluated_get(g);mesh=ev.to_mesh()
v=np.array([ob.matrix_world@p.co for p in mesh.vertices]);f=np.array([p.vertices[:]for p in mesh.polygons],np.int32);ev.to_mesh_clear()
# Keep the original -55 degree orientation. Match the supplied crop using its
# visible upper and lateral landmarks; aspect is calibrated, not shape geometry.
yaw=-55.;theta=math.radians(yaw);right=np.array([math.cos(theta),math.sin(theta),0.]);direction=np.array([math.sin(theta),-math.cos(theta),0.])
proj=v@right;outer_idx=proj.argmin();top_idx=v[:,2].argmax()
sy=(270-54)/(v[top_idx,2]-v[outer_idx,2]);sx=233/(proj[top_idx]-proj[outer_idx]);aspect=sy/sx
target=np.array([-.19,.06,v[top_idx,2]-(192-54)/sy]);target+=right*(proj.min()+160/sx-target@right)
camera=bpy.data.cameras.new('CREUX_REFERENCE');camera.type='ORTHO';camera.ortho_scale=384/sy
cam=bpy.data.objects.new(camera.name,camera);scene.collection.objects.link(cam);cam.location=target+4*direction;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
scene.camera=cam;scene.render.resolution_x=320;scene.render.resolution_y=384;scene.render.resolution_percentage=100;scene.render.pixel_aspect_x=aspect;scene.render.pixel_aspect_y=1;scene.view_layers[0].update()
uv=np.array([world_to_camera_view(scene,cam,Vector(p))[:]for p in v]);uv=uv[:,:2]*[320,-384]+[0,384]
meta={'yaw_degrees':yaw,'target_m':target.tolist(),'location_m':list(cam.location),'ortho_scale':camera.ortho_scale,'pixel_aspect_x':aspect,'pixel_aspect_y':1.,'pixels_per_meter_x':sx,'pixels_per_meter_y':sy,'reference_size_px':[320,384],'registration':'Original orientation with manually identified crop landmarks; calibrated framing/aspect. Not an automatic image registration.','top_landmark_px':uv[top_idx].tolist(),'lateral_landmark_px':uv[outer_idx].tolist()}
visible=[]
for point in v:
 hit=scene.ray_cast(g,Vector(point+4*direction),Vector(-direction),distance=8)
 visible.append(bool(hit[0]and hit[4].get('asset_id')=='deltoid.right'and np.linalg.norm(np.array(hit[1])-point)<.00003))
last_visible=None
for y in np.linspace(352,379,109):
 x=149+(y-352)*(132-149)/(379-352)
 ray=target+right*(x-160)/sx+[0,0,(192-y)/sy]+4*direction
 hit=scene.ray_cast(g,Vector(ray),Vector(-direction),distance=8)
 if not hit[0]or hit[4].get('asset_id')!='deltoid.right':break
 last_visible=[float(x),float(y)]
meta['blue2_last_visible_reference_px']=last_visible
meta['blue2_requested_endpoint_px']=[132,379]
np.savez_compressed(root/'source.npz',v=v,f=f,uv=uv,direction=direction,right=right,visible=np.array(visible,bool))
(root/'camera.json').write_text(json.dumps(meta,indent=2)+'\n');print('CAMERA',json.dumps(meta),flush=True)
if a.preview:
 scene.cycles.samples=8;scene.cycles.seed=0;scene.cycles.use_denoising=False;scene.render.image_settings.file_format='PNG';scene.render.filepath=str(root/'reference-p4.png');bpy.ops.render.render(write_still=True,scene=scene.name)
