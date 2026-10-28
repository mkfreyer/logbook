"""Four independently fitted anatomical guides on the real unchanged surface."""
import json,sys
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from scipy.interpolate import CubicSpline
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/m4c'))
from scene import camera
from glb_io import sha
BASE=ROOT/'docs/m4c/meshy-anterieurs-valides';OUT=ROOT/'docs/m4c/meshy-bras-prototype'
bpy.ops.wm.open_mainfile(filepath=str(BASE/'meshy-anterieurs-valides.blend'),use_scripts=False)
s=bpy.context.scene;s.camera.data.sensor_fit='HORIZONTAL';mesh=bpy.data.objects['MESHY_M4C'].data
tree=BVHTree.FromPolygons([v.co[:] for v in mesh.vertices],[p.vertices[:] for p in mesh.polygons],all_triangles=True)
v=np.array([[p.co.x,p.co.z,-p.co.y] for p in mesh.vertices]);f=np.array([p.vertices[:] for p in mesh.polygons])
uv0=np.load(ROOT/'docs/m4c/meshy-huit-zones/source-uv-binding.npz')['uv_blender'].copy();uv0[:,:,1]=1-uv0[:,:,1]
controls={
 'biceps.right':[[315,302],[335,329],[336,377],[322,437],[301,491],[278,531],[263,546],[248,526],[240,493],[242,435],[251,388],[264,351],[285,324]],
 'biceps.left':[[880,307],[861,338],[866,385],[881,439],[901,491],[925,539],[939,551],[952,533],[956,495],[953,437],[946,385],[934,350],[910,325]],
 'triceps.right':[[902,296],[878,301],[866,320],[867,365],[878,419],[894,467],[913,514],[935,546],[951,531],[962,493],[966,442],[965,386],[953,341],[929,311]],
 'triceps.left':[[304,299],[330,306],[340,324],[337,367],[327,420],[311,472],[288,519],[264,552],[248,537],[237,500],[233,446],[235,390],[247,344],[273,314]]}
codes={'biceps.left':9,'biceps.right':10,'triceps.left':11,'triceps.right':12}
zones=[]
for key,raw in controls.items():
    kind,side=key.split('.');sign=1 if side=='left' else -1
    # Centers follow measured upper-arm cross-sections. The Meshy arms sit
    # behind the torso; a torso-centered Z axis would misclassify their sides.
    root=np.array([sign*(.233 if side=='left' else .237),.465,-.065])
    elbow=np.array([sign*(.269 if side=='left' else .273),.275,-.075])
    axis=elbow-root;axis/=np.linalg.norm(axis)
    front=np.array([0.,0.,1.]);lateral=np.cross(front,axis);lateral*=sign;lateral/=np.linalg.norm(lateral)
    front=np.cross(axis,lateral)*sign;front/=np.linalg.norm(front)
    # Each side has its own closed pixel guide; no UV or pixel mirroring.
    p=np.array(raw,float);p=np.vstack([p,p[0]]);t=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))];t/=t[-1]
    pixels=CubicSpline(t,p,bc_type='periodic')(np.linspace(0,1,1000,endpoint=False))
    angle=0 if kind=='biceps' else 180;camera(s,angle,(0,.33,0),.9,(1200,1000));bpy.context.view_layer.update()
    rot=s.camera.rotation_euler.to_matrix();direction=rot@Vector((0,0,-1));samples=[]
    for pixel in pixels:
        origin=s.camera.location+rot@Vector(((pixel[0]/1200-.5)*.9,(.5-pixel[1]/1000)*.75,0))
        hit=tree.ray_cast(origin,direction);assert hit[0] is not None,(key,pixel)
        point=np.array([hit[0].x,hit[0].z,-hit[0].y]);tri=v[f[hit[2]]]
        ab=np.linalg.lstsq(np.column_stack([tri[1]-tri[0],tri[2]-tri[0]]),point-tri[0],rcond=None)[0]
        delta=point-root;axial=float(delta@axis);radial=delta-axis*axial
        theta=float(np.arctan2(radial@lateral,radial@front*(1 if kind=='biceps' else -1)))
        assert point[0]*sign>.17,(key,'Guide touches torso',point)
        samples.append({'pixel':pixel.tolist(),'point':point.tolist(),'sourceFace':int(hit[2]),'uv0':(np.r_[1-ab.sum(),ab]@uv0[hit[2]]).tolist(),'parameter':[theta*.06,axial]})
    profile_records=[]
    if kind=='triceps':
        # The lateral triceps head wraps around the arm. Fit that edge from
        # the real profile groove as well, rather than leaving a posterior cap.
        medial=[samples[int(np.argmin(np.linalg.norm(pixels-np.array(control),axis=1)))]['parameter'] for control in raw[:8]]
        profile_pixels=np.array([[530,330],[526,390],[526,450],[535,510],[560,560]] if side=='left' else [[371,332],[375,392],[375,451],[366,512],[340,561]],float)
        camera(s,90*sign,(sign*.28,.33,-.015),.52,(900,1100));bpy.context.view_layer.update()
        rr=s.camera.rotation_euler.to_matrix();dd=rr@Vector((0,0,-1))
        for pixel in profile_pixels:
            origin=s.camera.location+rr@Vector(((pixel[0]/900-.5)*.52,(.5-pixel[1]/1100)*(.52*1100/900),0))
            hit=tree.ray_cast(origin,dd);assert hit[0] is not None
            point=np.array([hit[0].x,hit[0].z,-hit[0].y]);delta=point-root;axial=float(delta@axis);radial=delta-axis*axial
            phi=float(np.arctan2(radial@lateral,-radial@front))
            profile_records.append({'pixel':pixel.tolist(),'point':point.tolist(),'sourceFace':int(hit[2]),'parameter':[phi*.06,axial]})
        # One closed periodic curve through posterior-medial and lateral
        # landmarks; no piecewise envelope or straight axial cutoff.
        controls_q=np.array(medial+[p['parameter'] for p in profile_records[::-1]])
        controls_q=np.vstack([controls_q,controls_q[0]])
        tt=np.r_[0,np.cumsum(np.linalg.norm(np.diff(controls_q,axis=0),axis=1))];tt/=tt[-1]
        curve_q=CubicSpline(tt,controls_q,bc_type='periodic')(np.linspace(0,1,1000,endpoint=False))
        samples=[]
        for q in curve_q:
            phi=q[0]/.06
            center=root+axis*q[1];direction3=-front*np.cos(phi)+lateral*np.sin(phi)
            hit=tree.ray_cast(Vector((center[0],-center[2],center[1])),Vector((direction3[0],-direction3[2],direction3[1])))
            assert hit[0] is not None and hit[3]<.13
            point=np.array([hit[0].x,hit[0].z,-hit[0].y]);tri=v[f[hit[2]]]
            ab=np.linalg.lstsq(np.column_stack([tri[1]-tri[0],tri[2]-tri[0]]),point-tri[0],rcond=None)[0]
            samples.append({'point':point.tolist(),'sourceFace':int(hit[2]),'uv0':(np.r_[1-ab.sum(),ab]@uv0[hit[2]]).tolist(),'parameter':q.tolist()})
        camera(s,angle,(0,.33,0),.9,(1200,1000));bpy.context.view_layer.update()
    poly=np.array([p['parameter'] for p in samples]);assert np.ptp(poly[:,0])<.23,(key,'Angular discontinuity',poly.min(0),poly.max(0))
    zones.append({'id':key,'code':codes[key],'name':('Biceps brachial ' if kind=='biceps' else 'Triceps brachial ')+('gauche' if side=='left' else 'droit'),
        'uvSet':1,'atlas':'textures/muscle-ids-arms.png','channel':codes[key]-9,'root':root.tolist(),'axis':axis.tolist(),'front':front.tolist(),'lateral':lateral.tolist(),
        'posterior':kind=='triceps','angularScaleM':.06,'manualGuidePixels':raw,'surfaceCurve':samples,
        'cameraMatrix':[list(row) for row in s.camera.matrix_world],'guideView':'front' if angle==0 else 'back-and-real-outer-profile','outerProfileSamples':profile_records,
        'posteriorMedialControlCount':8 if kind=='triceps' else None,
        'scope':'Visible superficial biceps/triceps group on currently neutral surface, not individual heads; existing eight zones protected; awaiting user validation.'})
zones.sort(key=lambda z:z['code'])
(OUT/'surface-guides.json').write_text(json.dumps({'baseCommit':'d552e23','geometryChanged':False,'method':'Independent smooth closed camera guides ray-projected on real source triangles, then intrinsic axial/angular surface coordinates. No UV reflection.','zones':zones},ensure_ascii=False,indent=2)+'\n')
print('FOUR_SURFACE_GUIDES',[(z['id'],len(z['surfaceCurve'])) for z in zones],flush=True)
