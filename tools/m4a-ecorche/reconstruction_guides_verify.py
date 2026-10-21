"""Verify serialized geometry, protected pieces/belly, supports, topology and GLB."""
import argparse,ast,hashlib,json,struct,sys
from pathlib import Path
import bpy,numpy as np
from mathutils.bvhtree import BVHTree

p=argparse.ArgumentParser();p.add_argument('--asset',type=Path,required=True);p.add_argument('--geometry-only',action='store_true')
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.asset.resolve()
meta=json.loads((root/'reconstruction.json').read_text());s=np.load(root/'surface.npz')
baseline=root.parent/'ecorche-beatriz-combinaison-p4-p5/ecorche-p4-p5.blend'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(baseline)==meta['baseline_blend_sha256']
# Reuse the independent raw data/material snapshot checker published in step 1.
helper=Path(__file__).with_name('guides_deltoides_verify.py')
tree=ast.parse(helper.read_text());defs=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.Import,ast.ImportFrom))]
namespace={};exec(compile(ast.Module(body=defs,type_ignores=[]),str(helper),'exec'),namespace)
before,lights0=namespace['snapshot'](baseline,meta['before_scene'])
archived,_=namespace['snapshot'](root/meta['master'],meta['before_scene'])
assert before.keys()==archived.keys()
for key in before:
    for field in ['v','f']:assert np.array_equal(before[key][field],archived[key][field]),('archived reference',key,field)
    for field in ['fingerprint','normals','modifiers','materials']:assert before[key][field]==archived[key][field],('archived reference',key,field)
after,lights1=namespace['snapshot'](root/meta['master'],meta['scene'])
assert len(before)==len(after)==300 and before.keys()==after.keys()
assert lights0==lights1 and len(lights1)==5
for key in set(after)-{'deltoid.right','deltoid.left'}:
    for field in ['v','f']:assert np.array_equal(before[key][field],after[key][field]),(key,field)
    for field in ['fingerprint','normals','modifiers','materials']:
        assert before[key][field]==after[key][field],(key,field)

def hull2d(points):
    points=sorted(set(map(tuple,points.tolist())))
    cross=lambda o,a,b:(a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lower=[]
    for q in points:
        while len(lower)>1 and cross(lower[-2],lower[-1],q)<=0:lower.pop()
        lower.append(q)
    upper=[]
    for q in reversed(points):
        while len(upper)>1 and cross(upper[-2],upper[-1],q)<=0:upper.pop()
        upper.append(q)
    return np.array(lower[:-1]+upper[:-1])

checks={};N=len(s['original_v'])
retained=s['retained_original_ids'] if 'retained_original_ids' in s else np.arange(N)
unmodified_original=np.linalg.norm(s['v'][:len(retained)]-s['original_v'][retained],axis=1)<1e-10
for key in ['deltoid.right','deltoid.left']:
    v,f=after[key]['v'],after[key]['f'];b=before[key]['v'];data=np.load(root/('serialized-'+key+'.npz'))
    assert np.array_equal(v,data['v']) and np.array_equal(f,data['f'])
    belly_ids=np.flatnonzero(s['original_belly']);belly_indices=np.searchsorted(retained,belly_ids)
    assert np.array_equal(v[belly_indices],b[belly_ids])
    assert np.array_equal(v[:len(retained)][unmodified_original],b[retained[unmodified_original]])
    assert np.array_equal(np.ptp(v,axis=0),np.ptp(b,axis=0))
    edge=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1)
    unique,count=np.unique(edge,axis=0,return_counts=True)
    assert (count==2).all() and len(v)-len(unique)+len(f)==2
    cross=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]])
    assert np.linalg.norm(cross,axis=1).min()>1e-11
    bv=BVHTree.FromPolygons(v.tolist(),f.tolist(),all_triangles=True)
    contacts=[(i,j)for i,j in bv.overlap(bv)if i<j and not np.isin(f[i],f[j]).any()]
    supports={}
    for yaw in [0,90,-55,-135]:
        t=np.radians(yaw);axis=np.array([np.cos(t),np.sin(t),0])
        p0=np.c_[b@axis,b[:,2]];p1=np.c_[v@axis,v[:,2]];h=hull2d(p0)
        edges=np.roll(h,-1,axis=0)-h;norm=np.c_[edges[:,1],-edges[:,0]];norm/=np.linalg.norm(norm,axis=1)[:,None]
        err=float((p1@norm.T-np.einsum('ij,ij->i',norm,h)).max())
        supports[str(yaw)]=err
    vol=lambda v,f:float(np.einsum('ij,ij->i',v[f[:,0]],np.cross(v[f[:,1]],v[f[:,2]])).sum()/6)
    volume0,volume1=vol(b,before[key]['f']),vol(v,f)
    checks[key]={'vertices':len(v),'triangles':len(f),'original_belly_vertices_exact':int(s['original_belly'].sum()),
        'belly_max_displacement_m':0,'unchanged_original_vertices':int(unmodified_original.sum()),
        'bbox_identical':True,'convex_support_outward_error_m':supports,
        'closed_two_manifold':True,'self_intersections':len(contacts),'self_intersection_triangle_pairs':contacts,'euler_characteristic':2,
        'volume_before_m3':volume0,'volume_after_m3':volume1,'relative_volume_change':volume1/volume0-1}
plane=.002114987923242599;mirrored=after['deltoid.right']['v'].copy();mirrored[:,0]=2*plane-mirrored[:,0]
symmetry=float(np.linalg.norm(mirrored-after['deltoid.left']['v'],axis=1).max());assert symmetry<2e-7
report={'validation_status':'INSUFFISANT_NON_VALIDE','baseline_sha256':sha(baseline),'master_sha256':sha(root/meta['master']),
        'baseline_commit':meta['reference_commit'],'validated_guides_commit':meta['guides_commit'],
        'protected_other_objects_exact':298,'head_throat_pectorals_body_raw_and_evaluated_exact':True,
        'source_scene_unchanged':True,'master_mesh_objects':300,'new_segmentation':False,
        'master_triangles':sum(len(r['f'])for r in after.values()),'surface_checks':checks,
        'mirror_max_distance_m':symmetry,'original_lights_identical':True,
        'scope':'Preservation applies to the protected belly and 298 other objects. Deltoid topology changed. This proposal fails the clean-intersection/raccord criteria and is not validated.'}
report['no_self_intersections']=all(r['self_intersections']==0 for r in checks.values())
if not a.geometry_only:
    raw=(root/'reconstruction-guides.glb').read_bytes();length=struct.unpack_from('<I',raw,12)[0]
    doc=json.loads(raw[20:20+length]);binary=raw[28+length:]
    def accessor(i):
        ac=doc['accessors'][i];view=doc['bufferViews'][ac['bufferView']]
        width={'SCALAR':1,'VEC3':3,'VEC4':4}[ac['type']];dtype=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2'}[ac['componentType']])
        return np.ndarray((ac['count'],width),dtype=dtype,buffer=binary,
            offset=view.get('byteOffset',0)+ac.get('byteOffset',0),
            strides=(view.get('byteStride',width*dtype.itemsize),dtype.itemsize)).copy()
    def signature(v,f):
        q=np.rint(v[f]*1e6).astype('<i4');order=np.lexsort((q[:,:,2],q[:,:,1],q[:,:,0]),axis=1)
        q=np.ascontiguousarray(np.take_along_axis(q,order[:,:,None],axis=1).reshape(-1,9))
        return np.sort(q.view(np.dtype([(f'c{i}','<i4')for i in range(9)])).ravel())
    assert len(doc['nodes'])==300 and len(doc['materials'])==1
    total=0;omissions=[]
    for node in doc['nodes']:
        key=node['name'];primitive=doc['meshes'][node['mesh']]['primitives'][0]
        v=accessor(primitive['attributes']['POSITION']).astype(float)[:,[0,2,1]];v[:,1]*=-1
        f=accessor(primitive['indices']).reshape(-1,3);expected=signature(after[key]['v'],after[key]['f']);actual=signature(v,f)
        assert not len(np.setdiff1d(actual,expected)),key
        if not np.array_equal(actual,expected):
            s0,c0=np.unique(expected,return_counts=True);s1,c1=np.unique(actual,return_counts=True)
            remaining=np.zeros(len(s0),int);remaining[np.searchsorted(s0,s1)]=c1;diff=c0-remaining
            assert (diff>=0).all()
            for i in np.flatnonzero(diff):
                assert remaining[i]>0
                omissions.append({'object':key,'duplicate_copies_removed':int(diff[i])})
        total+=len(f)
    assert 'CC BY 4.0' in doc['asset']['copyright'] and 'CC0' in doc['asset']['copyright']
    frames=json.loads((root/'renders/metadata.json').read_text())['frames'];assert len(frames)==12
    for row in frames:assert sha(root/'renders'/row['file'])==row['sha256']
    for label in ['reference','epaule-gauche','face','profil','trois-quarts','arriere-oblique']:
        pair=[r for r in frames if r['file'] in ['avant-'+label+'.png','apres-'+label+'.png']]
        for field in ['camera_matrix','ortho_scale','resolution','resolution_percentage','pixel_aspect_x']:
            assert pair[0][field]==pair[1][field],(label,field)
    report.update(glb_triangles=total,glb_sha256=sha(root/'reconstruction-guides.glb'),
        glb_surface_match_at_micron_precision=True,glb_duplicate_faces_removed=omissions,
        render_hashes_verified=len(frames),paired_cameras_identical=True)
    (root/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
else:
    (root/'verification-geometrie.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('VERIFIED',json.dumps(report),flush=True)
