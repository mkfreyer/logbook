"""Independent buffer/UV/mask integrity checks; never writes the source asset."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from glb_io import source,read_glb,accessor,sha,SOURCE_SHA
root=Path(__file__).resolve().parents[2];out=root/'docs/m4c/meshy-huit-zones'
_,v,n,f=source(root/'assets/models/meshy-e45e5d8.glb');raw,doc,binary=read_glb(out/'exports/meshy-eight-zones-control.glb')
p=doc['meshes'][0]['primitives'][0];ev=accessor(doc,binary,p['attributes']['POSITION']);en=accessor(doc,binary,p['attributes']['NORMAL']);ef=accessor(doc,binary,p['indices']).reshape(-1,3);eu=accessor(doc,binary,p['attributes']['TEXCOORD_0'])
bind=np.load(out/'exports/export-source-binding.npz');mapping=bind['source_vertex'];uv=bind['uv_gltf'];spec=json.loads((out/'regions.json').read_text())
assert np.array_equal(v[mapping],ev) and np.array_equal(n[mapping],en)
assert np.array_equal(mapping[ef],f) and np.array_equal(eu[ef],uv)
assert np.array_equal(ev[:len(v)],v) and np.array_equal(en[:len(n)],n)
assert np.array_equal(v[f],ev[ef]) and np.array_equal(n[f],en[ef])
labels=np.array(Image.open(out/'textures/muscle-ids.png'));assert labels.shape==(2048,2048) and np.array_equal(np.unique(labels),np.arange(9))
masks=np.array([np.array(Image.open(out/'textures'/(z['id']+'.png')))//255 for z in spec['zones']])
assert np.all(masks.sum(0)<=1)
for i,z in enumerate(spec['zones']):assert np.array_equal(masks[i],labels==z['code'])
for group in range(2):
    rgba=np.array(Image.open(out/'textures'/f'masks-rgba-{group}.png'))
    assert np.array_equal(rgba,np.moveaxis(masks[group*4:group*4+4]*255,0,-1))
# Source geometric connectivity: report every component instead of guessing a clean contour.
ids=np.load(out/'face-samples.npy');edges=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1);owners=np.tile(np.arange(len(f)),3);order=np.lexsort((edges[:,1],edges[:,0]));edges=edges[order];owners=owners[order]
starts=np.r_[0,1+np.flatnonzero(np.any(edges[1:]!=edges[:-1],axis=1))];counts=np.diff(np.r_[starts,len(edges)]);pairs=np.column_stack([owners[starts[counts==2]],owners[starts[counts==2]+1]])
adj=[[] for _ in f]
for a,b in pairs:adj[a].append(int(b));adj[b].append(int(a))
regions=[];witnesses=[]
for zone in spec['zones']:
    code=zone['code'];faces=np.flatnonzero(ids==code);todo=set(faces.tolist());components=[]
    while todo:
        stack=[todo.pop()];comp=[]
        while stack:
            current=stack.pop();comp.append(current)
            for other in adj[current]:
                if other in todo:todo.remove(other);stack.append(other)
        components.append(comp)
    components.sort(key=len,reverse=True)
    points=v[f[faces]].reshape(-1,3);center=points.mean(0);low=points.min(0);high=points.max(0)
    regions.append({**zone,'sourceFaceCenterSamples':len(faces),'faceCenterDiagnosticComponentCounts':[len(c) for c in components], 'boundsSourceM':{'min':low.tolist(),'max':high.tolist()},'centerSourceM':center.tolist(),'boundsAreConservativeFaceExtent':True})
    # A safe, non-boundary witness with all three UV corners and center in one ID.
    q=uv[faces];xy=np.minimum((q*2048).astype(int),2047);cornercodes=labels[xy[:,:,1],xy[:,:,0]]
    mean=q.mean(1);ij=np.minimum((mean*2048).astype(int),2047);centerCodes=labels[ij[:,1],ij[:,0]]
    good=faces[(cornercodes==code).all(1)&(centerCodes==code)]
    assert len(good)>0,'No interior sample for '+zone['id']
    nearest=good[np.argmin(np.linalg.norm(v[f[good]].mean(1)-center,axis=1))]
    point=v[f[nearest]].mean(0)
    witnesses.append({'expectedId':zone['id'],'faceIndex':int(nearest),'point':{'x':float(point[0]),'y':float(point[1]),'z':float(point[2])},'normal':n[f[nearest]].mean(0).tolist(),'uvGltf':uv[nearest].mean(0).tolist()})
(out/'region-binding.json').write_text(json.dumps({'schemaVersion':1,'assetId':'meshy-e45e5d8','sourceSha256':SOURCE_SHA,'referenceHasUV':False,'lookup':'SurfaceHit on original: SHA-bound sparse face corner UV, barycentric interpolation, discrete atlas ID. New GLB: use hit.uv directly.','boundFaces':'exports/source-face-indices.u32','cornerUV':'exports/source-corner-uv.f32','faceCount':(out/'exports/source-face-indices.u32').stat().st_size//4,'byteOrder':'little-endian','neutralCode':0,'regionCodesStableAcrossTriangleOrder':True,'zones':regions},indent=2)+'\n')
(out/'picking-witnesses.json').write_text(json.dumps(witnesses,indent=2)+'\n')
report={'source_sha256':SOURCE_SHA,'source_sha_verified':True,'export_vertices':len(ev),'source_vertices':len(v),'triangles_source':len(f),'triangles_export':len(ef),'all_original_vertices_bit_identical':True,'all_export_corners_positions_bit_identical':True,'all_export_corners_normals_bit_identical':True,'max_position_displacement_m':0,'new_surface_triangles':0,'new_geometric_holes_or_intersections':False,'eight_ids_present':True,'overlapping_mask_pixels':int((masks.sum(0)>1).sum()),'rgba_masks_match_ids':True,'source_face_order_preserved':True,'glb_export_sha256':sha(raw),'source_face_center_components_diagnostic_only':{r['id']:r['faceCenterDiagnosticComponentCounts'] for r in regions}}
(out/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
