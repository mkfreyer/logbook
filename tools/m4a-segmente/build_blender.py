"""Build, export and render the upper-body pilot. Blender 4.3.2, no external assets.
Usage: blender -b -t 3 --python tools/m4a-segmente/build_blender.py -- patches.npz [--preview]
"""
import sys,json,math,hashlib
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/m4a/segmente'
args=sys.argv[sys.argv.index('--')+1:];data=np.load(args[0]);preview='--preview' in args;build_only='--build-only' in args
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.name='PILOTE_8_PIECES'
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24 if preview else 64;scene.cycles.use_denoising=False;scene.cycles.seed=0
scene.render.resolution_x=780;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG'
scene.world.use_nodes=True;bg=scene.world.node_tree.nodes['Background'];bg.inputs['Color'].default_value=(.009,.019,.036,1);bg.inputs['Strength'].default_value=.45

def mat(name,col):
    m=bpy.data.materials.new(name);m.diffuse_color=(*col,1);m.use_nodes=True
    n=m.node_tree.nodes.get('Principled BSDF');n.inputs['Base Color'].default_value=(*col,1);n.inputs['Roughness'].default_value=.39;n.inputs['Metallic'].default_value=.12;n.inputs['Coat Weight'].default_value=.08
    return m
blue=mat('SATIN_BLEU',(.19,.28,.42));orange=mat('SELECTION_ORANGE',(1,.18,.025));dark=mat('CONTEXTE_ATTENUE',(.045,.065,.095))
names=[k[:-2] for k in data.files if k.endswith('_v')];objects={};audit=[]

def topology(mesh):
    edges={};adj=[[] for _ in mesh.vertices];vol=0
    for f in mesh.polygons:
        t=list(f.vertices)
        for a,b in zip(t,t[1:]+t[:1]):
            e=tuple(sorted((a,b)));edges[e]=edges.get(e,0)+1;adj[a].append(b);adj[b].append(a)
        for k in range(1,len(t)-1):vol+=mesh.vertices[t[0]].co.dot(mesh.vertices[t[k]].co.cross(mesh.vertices[t[k+1]].co))/6
    todo=set(range(len(adj)));comps=0
    while todo:
        stack=[todo.pop()];comps+=1
        while stack:
            for j in adj[stack.pop()]:
                if j in todo:todo.remove(j);stack.append(j)
    return dict(vertices=len(mesh.vertices),triangles=sum(len(p.vertices)-2 for p in mesh.polygons),boundary_edges=sum(v==1 for v in edges.values()),nonmanifold_edges=sum(v!=2 for v in edges.values()),components=comps,signed_volume=vol)

for name in names:
    v=data[name+'_v'].copy();n=data[name+'_n'].copy();f=data[name+'_f'].copy()
    edges={}
    for tri in f:
        for a,b in zip(tri,np.roll(tri,-1)):
            key=tuple(sorted((int(a),int(b))))
            if key in edges:edges[key]=None
            else:edges[key]=(int(a),int(b))
    boundary=[e for e in edges.values() if e is not None];nv=len(v)
    # A recessed V joint; no raised overlay/second skin. Limit outer movement to 0.8 mm.
    if name!='baseline':
        ids=sorted({i for e in boundary for i in e});tree=KDTree(len(ids))
        # Only recess muscle/context seams, not the display crop at the waist/forearms.
        ids=[i for i in ids if v[i,1]>.121]
        tree=KDTree(len(ids))
        for j,i in enumerate(ids):tree.insert(Vector(v[i]),j)
        tree.balance()
        if ids:
            ds=np.array([tree.find(Vector(p))[2] for p in v]);w=np.clip(1-ds/.004,0,1);w=w*w*(3-2*w);v-=n*(.0008*w[:,None])
    thickness=.018 if name not in ['support','baseline'] else .006
    # Closed shell: outer source surface, offset inner surface, full boundary sidewalls.
    if name not in ['support','baseline']:
        # Smooth only the inward construction. Outer source vertices stay intact.
        ee=np.array(list(edges),dtype=int);aidx=np.r_[ee[:,0],ee[:,1]];bidx=np.r_[ee[:,1],ee[:,0]]
        degree=np.bincount(aidx,minlength=len(v))[:,None]
        def smooth(points,steps):
            points=points.copy()
            for _ in range(steps):
                total=np.zeros_like(points);np.add.at(total,aidx,points[bidx]);points=.5*points+.5*total/degree
            return points
        sn=smooth(n,10);sn/=np.linalg.norm(sn,axis=1)[:,None]
        inner=smooth(v-sn*thickness,8)
    else:inner=v-n*thickness
    vv=np.vstack([v,inner]);ff=f.tolist()+[(tri[::-1]+nv).tolist() for tri in f]
    for a,b in boundary:ff.extend([[b,a,a+nv],[b,a+nv,b+nv]])
    # Convert glTF Y-up to Blender Z-up without scaling.
    vv=vv[:,[0,2,1]];vv[:,1]*=-1
    mesh=bpy.data.meshes.new('GEO_'+name);mesh.from_pydata(vv.tolist(),[],ff);mesh.update()
    for p in mesh.polygons:p.use_smooth=p.index<2*len(f)
    # Preserve interpolated source normals on outer skin; shared seams have the same normals.
    nn=n[:,[0,2,1]].copy();nn[:,1]*=-1
    custom=[]
    for p in mesh.polygons:
        for vi in p.vertices:
            custom.append(tuple(nn[vi]) if p.index<len(f) else tuple(-nn[vi-nv]) if p.index<2*len(f) else tuple(p.normal))
    mesh.normals_split_custom_set(custom)
    ob=bpy.data.objects.new('M4A.'+name,mesh);scene.collection.objects.link(ob);individual=blue.copy();individual.name='MAT_'+name;mesh.materials.append(individual)
    ob['muscle_id']=name;ob['selectable']=name not in ['support','baseline'];ob['representation']='closed stylized surface-group shell, not medical internal muscle';ob['source']='Meshy CC BY 4.0; adapted upper body'
    objects[name]=ob
    record=dict(id=name,inner_method='smoothed inner offset .018m; 10 normal + 8 position smoothing steps' if name not in ['support','baseline'] else 'normal offset .006m',max_inner_distance_m=float(np.linalg.norm(v-inner,axis=1).max()),**topology(mesh));audit.append(record)
    if name not in ['support','baseline']:assert record['components']==1 and record['nonmanifold_edges']==0,record
objects['baseline'].hide_render=True;objects['baseline'].hide_set(True)

def aim(o,t):o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,size,col in [('Key',(-2,-3,3),320,3,(.81,.88,1)),('Fill',(2.5,-2,1.3),150,2.5,(.56,.69,1)),('Rim',(1.6,2.3,2.8),320,2,(.58,.72,1)),('Back',(-2,2,1.3),100,2.5,(.75,.82,1))]:
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=col;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc;aim(o,(0,0,.5))
cameras={}
for name,yaw in [('front',0),('three-quarter',35),('profile',90),('back',180),('rear-three-quarter',145),('three-quarter-right',-35),('rear-three-quarter-right',-145)]:
    d=bpy.data.cameras.new(name);d.type='ORTHO';d.ortho_scale=1.0;o=bpy.data.objects.new('CAM_'+name,d);scene.collection.objects.link(o);t=math.radians(yaw);o.location=(4*math.sin(t),-4*math.cos(t),.535);aim(o,(0,0,.535));cameras[name]=o
scene.camera=cameras['three-quarter']
# Selected-object export includes exactly 9 meshes, no cameras, lights, lower body or baseline.
bpy.ops.object.select_all(action='DESELECT')
for name,ob in objects.items():
    if name!='baseline':ob.select_set(True)
bpy.context.view_layer.objects.active=objects['pectoralis.left']
bpy.ops.export_scene.gltf(filepath=str(OUT/'pilote-haut-corps.glb'),export_format='GLB',use_selection=True,export_extras=True,export_normals=True,export_texcoords=False,export_yup=True,export_animations=False)
# Archive baseline in a non-rendering collection in the BLEND only.
for ob in objects.values():ob.select_set(False)
objects['pectoralis.left'].select_set(True);bpy.context.view_layer.objects.active=objects['pectoralis.left']
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            s=area.spaces.active;s.shading.type='MATERIAL';s.overlay.show_floor=False;s.region_3d.view_location=(0,0,.535);s.region_3d.view_rotation=cameras['three-quarter'].rotation_euler.to_quaternion();s.region_3d.view_distance=1.3;s.region_3d.view_perspective='ORTHO'
bpy.data.texts.new('LIRE_MOI').write('8 vrais objets fermes : pectoralis/deltoid/biceps/triceps.left/right.\nSupport = contexte non selectionnable ; baseline = temoin cache, exclu GLB.\nPas de masque ou texture. Les pieces sont des coques de groupes de surface, pas des muscles internes medicalement reconstruits.\nPour isoler: selectionner un objet et presser / dans Blender. Pour orange: assigner SELECTION_ORANGE au seul objet.\nModel created with Meshy – CC BY 4.0 License. Modifications: crop, geometric partition, recessed seams, inner thickness, PBR materials.\n')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'pilote-haut-corps.blend'),compress=True)
(OUT/'geometry-audit.json').write_text(json.dumps(dict(blender=bpy.app.version_string,outer_max_recess_m=.0008,parts=audit),indent=2)+'\n')
frames=[]
def render(file,cam,selected=None,baseline=False,isolate=False,explode=False):
    scene.camera=cameras[cam]
    for name,ob in objects.items():
        ob.hide_render=(name=='baseline') != baseline
        ob.data.materials[0]=orange if name==selected else blue
        if isolate and not baseline and name!=selected:ob.hide_render=True
        if explode and name not in ['support','baseline']:
            c=sum((v.co for v in ob.data.vertices),Vector())/len(ob.data.vertices);d=Vector((c.x,-.05,c.z-.45));ob.location=d.normalized()*.07
        else:ob.location=(0,0,0)
    scene.render.filepath=str(OUT/'renders'/f'{file}.png');bpy.ops.render.render(write_still=True)
    frames.append(dict(file=file+'.png',camera=cam,selected=selected,baseline=baseline,isolate=isolate,exploded=explode))
    (OUT/'render-metadata.json').write_text(json.dumps(dict(engine='Cycles CPU',samples=scene.cycles.samples,resolution=[780,1000],seed=0,denoising=False,frames=frames),indent=2)+'\n')
if build_only:sys.exit(0)
if preview:
    render('preview-front','front',selected='pectoralis.left');render('preview-back','rear-three-quarter',selected='triceps.left');render('preview-profile','profile',selected='deltoid.left')
else:
    for cam in ['front','three-quarter','profile','back']:render(cam,cam)
    for cam in ['front','three-quarter','profile','back']:render('baseline-'+cam,cam,baseline=True)
    for name in [n for n in names if n not in ['baseline','support']]:
        camera='rear-three-quarter' if name.startswith('triceps') else 'three-quarter'
        if name.endswith('right'):camera+='-right'
        render('select-'+name,camera,selected=name)
    render('isolate-pectoralis.left','three-quarter',selected='pectoralis.left',isolate=True)
    render('exploded','three-quarter',explode=True)
print('PILOT_DONE',len(frames),flush=True)
