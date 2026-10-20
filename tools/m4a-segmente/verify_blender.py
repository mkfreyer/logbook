"""Verify saved BLEND, GLB buffers, round-trip geometry and eight independent ray hits.
Run: blender -b -t 3 --python tools/m4a-segmente/verify_blender.py
"""
from pathlib import Path
import bpy,json,struct,hashlib,math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/m4a/segmente'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(ob):
    # Normal seams may duplicate GLB vertices; compare triangle coordinates instead.
    mesh=ob.data;mesh.calc_loop_triangles()
    rows=[]
    for tri in mesh.loop_triangles:
        pts=[tuple(round(float(x),6) for x in (ob.matrix_world@mesh.vertices[i].co)) for i in tri.vertices]
        # Cyclic rotation keeps winding, while allowing start-corner reindexing.
        start=min(range(3),key=lambda k:pts[k]);rows.append(tuple(pts[start:]+pts[:start]))
    return sorted(rows)
raw=(OUT/'pilote-haut-corps.glb').read_bytes();magic,version,total=struct.unpack_from('<4sII',raw);assert magic==b'glTF' and version==2 and total==len(raw)
n,kind=struct.unpack_from('<II',raw,12);doc=json.loads(raw[20:20+n]);assert not doc.get('images') and not doc.get('textures')
expected={a+'.'+s for a in ['pectoralis','deltoid','biceps','triceps'] for s in ['left','right']}
nodes={n['extras']['muscle_id']:n for n in doc['nodes']};assert set(nodes)==expected|{'support'}
assert len({n['mesh'] for n in nodes.values()})==9
mats=[]
for name,n in nodes.items():
    assert not any(k in n for k in ['translation','rotation','scale','matrix'])
    p=doc['meshes'][n['mesh']]['primitives'];assert len(p)==1
    assert p[0].get('mode',4)==4
    mats.append(p[0]['material'])
    assert n['extras']['selectable']==(name in expected)
assert len(set(mats))==9,'Each piece must have its own material to recolor independently'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'pilote-haut-corps.blend'),use_scripts=False)
source={ob['muscle_id']:ob for ob in bpy.context.scene.objects if ob.type=='MESH' and ob.get('muscle_id')!='baseline'}
assert len(source)==9 and len({ob.data.as_pointer() for ob in source.values()})==9
baseline=bpy.data.objects['M4A.baseline'];assert baseline.hide_render
source_triangles={name:canonical(ob) for name,ob in source.items()}
# Check self-intersection candidates on the source topology, ignoring adjacent triangles.
intersection={}
outer_counts={r['id']:r['triangles'] for r in json.loads((OUT/'partition-audit.json').read_text())['parts']}
for name,ob in source.items():
    mesh=ob.data;mesh.calc_loop_triangles();tris=[tuple(t.vertices) for t in mesh.loop_triangles];v=[tuple(p.co) for p in mesh.vertices]
    tree=BVHTree.FromPolygons(v,tris,all_triangles=True,epsilon=0)
    pairs={(min(a,b),max(a,b)) for a,b in tree.overlap(tree) if a!=b and not set(tris[a])&set(tris[b])}
    outer=outer_counts[name]
    def kind(i):return 'outer' if i<outer else 'inner' if i<2*outer else 'wall'
    categories={}
    for a,b in pairs:
        key='_'.join(sorted([kind(a),kind(b)]));categories[key]=categories.get(key,0)+1
    intersection[name]=dict(total=len(pairs),categories=categories)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(OUT/'pilote-haut-corps.glb'))
scene=bpy.context.scene;obs={ob['muscle_id']:ob for ob in scene.objects if ob.type=='MESH'}
assert set(obs)==set(source_triangles)
roundtrip=[]
for name,ob in obs.items():
    assert canonical(ob)==source_triangles[name],name
    roundtrip.append(dict(id=name,triangles=len(source_triangles[name]),geometry_equal_at_1_micrometre=True))
bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();proof=[]
for name in sorted(expected):
    ob=obs[name];mesh=ob.data;mesh.calc_loop_triangles();target=np.array([tuple(ob.matrix_world@v.co) for v in mesh.vertices]).mean(0);found=None
    # Cameras from both sides; a real first-hit scene ray, not an object-only query.
    yaw=145 if name.startswith('triceps') else 35
    if name.endswith('right'):yaw=-yaw
    camera=Vector((4*math.sin(math.radians(yaw)),-4*math.cos(math.radians(yaw)),.5))
    tris=sorted(mesh.loop_triangles,key=lambda t:-t.area)
    for tri in tris:
        center=ob.matrix_world@tri.center;direction=(center-camera).normalized()
        hit,point,normal,index,hitob,matrix=scene.ray_cast(deps,camera,direction,distance=8)
        if hit and hitob==ob and (point-center).length<.0001:
            found=dict(id=name,object=ob.name,origin=list(camera),direction=list(direction),hit=list(point),triangle=int(index));break
    assert found,'No externally visible ray hit: '+name
    # Changing one material cannot modify another object.
    material=ob.data.materials[0];assert all(other==ob or other.data.materials[0]!=material for other in obs.values())
    color=material.diffuse_color[:];material.diffuse_color=(1,.18,.025,1)
    assert all(other==ob or tuple(other.data.materials[0].diffuse_color)!=tuple(material.diffuse_color) for other in obs.values())
    material.diffuse_color=color
    proof.append(found)
report=dict(blend_sha256=digest(OUT/'pilote-haut-corps.blend'),glb_sha256=digest(OUT/'pilote-haut-corps.glb'),glb_bytes=len(raw),nodes=9,independent_materials=9,textures=0,roundtrip=roundtrip,first_hit_selection_probes=proof,nonadjacent_self_intersection_pairs=intersection,intersection_caveat='BVH triangle-overlap diagnostic, not a certification of printability or medical volumes.',mobile_runtime_tested=False)
(OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
print('VERIFIED',len(proof),'independent selections; source/export geometry identical at 1um',flush=True)
print('INTERSECTIONS',intersection,flush=True)
