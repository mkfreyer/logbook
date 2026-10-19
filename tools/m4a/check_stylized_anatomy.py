"""Inspect prototype geometry and the S1 union partition, without app integration."""
import argparse, hashlib, json, sys
from collections import Counter
from pathlib import Path
import bpy,bmesh,numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prepared',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.prepared=a.prepared.resolve()
bpy.ops.wm.open_mainfile(filepath=str(a.prepared/'model.blend'),use_scripts=False)
c=json.loads((a.prepared/'construction.json').read_text())
visible=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.get('render')]
assert len(visible)==c['counts']['visible_objects']
rows=[];all_points=[]

def inspect(ob):
    me=ob.data;me.calc_loop_triangles()
    xyz=np.empty(len(me.vertices)*3,dtype=np.float64);me.vertices.foreach_get('co',xyz);xyz=xyz.reshape(-1,3)
    assert np.isfinite(xyz).all()
    ix=np.empty(len(me.loop_triangles)*3,dtype=np.int32);me.loop_triangles.foreach_get('vertices',ix);ix=ix.reshape(-1,3)
    t=xyz[ix];area=np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1)
    assert np.all(area>1e-12),(ob.name,'degenerate triangles',int(sum(area<=1e-12)))
    bm=bmesh.new();bm.from_mesh(me)
    nonmanifold=sum(not e.is_manifold for e in bm.edges);boundary=sum(e.is_boundary for e in bm.edges)
    loose=sum(not v.link_faces for v in bm.verts);todo=set(bm.verts);components=[]
    while todo:
        stack=[todo.pop()];n=0
        while stack:
            v=stack.pop();n+=1
            for edge in v.link_edges:
                other=edge.other_vert(v)
                if other in todo:todo.remove(other);stack.append(other)
        components.append(n)
    euler=len(bm.verts)-len(bm.edges)+len(bm.faces);volume=bm.calc_volume(signed=True);bm.free()
    assert loose==0
    return {'object':ob.name,'zone':ob.get('zone'),'role':ob.get('role'),'selectable':bool(ob.get('selectable')),
            'vertices':len(xyz),'triangles':len(ix),'boundary_edges':boundary,'nonmanifold_edges':nonmanifold,
            'near_degenerate_triangles':0,'nonfinite_coordinates':0,'loose_vertices':loose,
            'connected_components':len(components),'component_vertex_counts':sorted(components,reverse=True),
            'minimum_double_area_m2':float(area.min()),'signed_volume_m3':volume,'euler_characteristic':euler,
            'bounds_min':xyz.min(0).tolist(),'bounds_max':xyz.max(0).tolist()},xyz


def face_keys(ob):
    me=ob.data;me.calc_loop_triangles()
    return Counter(tuple(sorted(tuple(me.vertices[i].co) for i in tri.vertices)) for tri in me.loop_triangles)

for ob in visible:
    r,xyz=inspect(ob);rows.append(r);all_points.extend(xyz.tolist())
    zone=ob['zone'];center=xyz.mean(0)
    if zone.endswith('.left'):assert center[0]>0
    if zone.endswith('.right'):assert center[0]<0
assert sum(r['triangles'] for r in rows)==c['counts']['triangles']
assert sum(r['selectable'] for r in rows)==c['counts']['selectable_objects']
assert any(o['zone']=='pectoralis.left' for o in visible) and any(o['zone']=='pectoralis.right' for o in visible)
report={'variant':c['variant'],'source_blend_sha256':hashlib.sha256((a.prepared/'model.blend').read_bytes()).hexdigest(),
 'visible_triangles':sum(r['triangles'] for r in rows),'visible_objects':len(rows),
 'bounds_min':np.min(all_points,axis=0).tolist(),'bounds_max':np.max(all_points,axis=0).tolist(),
 'surface_zone_ids':sorted({r['zone'] for r in rows if r['selectable']}),'objects':rows,
 'limitations':['Surface labels are provisional, not full medical or final product segmentation.',
 'No exhaustive self-intersection, occlusion, rig, raycast or iPhone benchmark.',
 'S2/S3 retain overlapping closed anatomical masses; no final nonoverlapping skin partition.']}
if c['variant']=='s1':
    base=bpy.data.objects['S1.hidden-continuous-source'];r,_=inspect(base)
    combined=Counter()
    for ob in visible:combined.update(face_keys(ob))
    assert combined==face_keys(base),'Visible patches must partition the exact union triangles'
    report['continuous_source']=r
    report['all_union_faces_used_exactly_once']=True
    assert r['boundary_edges']==r['nonmanifold_edges']==0
else:
    report['nonmanifold_visible_edges']=sum(r['nonmanifold_edges'] for r in rows)
(a.prepared/'geometry-check.json').write_text(json.dumps(report,indent=2)+'\n')
print('STYLIZED_CHECK',json.dumps({k:v for k,v in report.items() if k not in {'objects','surface_zone_ids','limitations'}}),flush=True)
