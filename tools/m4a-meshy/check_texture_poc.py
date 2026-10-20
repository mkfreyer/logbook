"""Check geometry, UV export, mask sampling and actual imported GLB materials."""
import argparse,json,struct,sys
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mesh_io import load_glb,sha,EXPECTED_SHA
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prepared',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.prepared.resolve();out=root/'texture-poc'
raw,source,v,ix=load_glb(root/'source.glb');assert sha(raw)==EXPECTED_SHA
build=json.loads((out/'build.json').read_text());assert sha((out/'meshy-painted-mask.blend').read_bytes())==build['blend_sha256']
assert sha(Path(__file__).with_name('build_texture_poc.py').read_bytes())==build['builder_sha256']
assert sha((out/'painted-contour.svg').read_bytes())==build['stencil_sha256']
assert sha((out/'textures/pectoralis-left-mask.png').read_bytes())==build['mask_sha256']
uv=np.frombuffer((out/'uv-loops.f32').read_bytes(),dtype='<f4').reshape(len(ix),3,2);assert sha(uv.tobytes())==build['uv_loops_sha256']
bpy.ops.wm.open_mainfile(filepath=str(out/'meshy-painted-mask.blend'),use_scripts=False)
meshes={o.data for o in bpy.data.objects if o.type=='MESH'};assert len(meshes)==1;mesh=meshes.pop()
assert np.array([p.co[:] for p in mesh.vertices],dtype='<f4').tobytes()==v.tobytes()
assert np.array([f.vertices[:] for f in mesh.polygons],dtype='<u4').tobytes()==ix.tobytes()
assert np.array([p.uv[:] for p in mesh.uv_layers['UV_LOCAL_PECTORAL'].data],dtype='<f4').tobytes()==uv.tobytes()
assert not mesh.shape_keys and all(not o.modifiers for o in bpy.data.objects if o.type=='MESH')
assert all(f.material_index==0 for f in mesh.polygons),'The selection must not use region face slots'
mat=bpy.data.materials['PECTORAL_GAUCHE__MASQUE_PEINT'];node=next(n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE')
assert node.image.packed_file and node.image.colorspace_settings.name=='Non-Color' and node.interpolation=='Linear' and node.extension=='EXTEND'
assert mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].is_linked
assert mat.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value==0
assert bpy.data.texts['LIRE_MASQUE_PEINT.md'].as_string()==(out/'README.md').read_text()
assert bpy.data.texts['LICENCE_ET_PROVENANCE.md'].as_string()==(root/'LICENCE_ET_PROVENANCE.md').read_text()
assert not bpy.data.texts.get('RAYCAST_ET_EXPORT.md')
post=build['documentation_postprocess']
assert sha(Path(__file__).with_name('finish_texture_poc.py').read_bytes())==post['script_sha256']
assert post['final_blend_sha256']==build['blend_sha256']
def png(path):
 image=bpy.data.images.load(str(path),check_existing=False);image.colorspace_settings.name='Non-Color'
 return np.array(image.pixels[:],dtype=float).reshape(image.size[1],image.size[0],4)[::-1]
mask=png(out/'textures/pectoralis-left-mask.png')[:,:,0];base=png(out/'textures/selected-basecolor-srgb.png')[:,:,:3];orm=png(out/'textures/selected-coat-roughness-metallic-linear.png')[:,:,:3]
def sample(array,points):
 q=np.asarray(points);x=np.clip(q[...,0]*array.shape[1]-.5,0,array.shape[1]-1);y=np.clip(q[...,1]*array.shape[0]-.5,0,array.shape[0]-1)
 i=np.floor(x).astype(int);j=np.floor(y).astype(int);ii=np.minimum(i+1,array.shape[1]-1);jj=np.minimum(j+1,array.shape[0]-1);u=x-i;w=y-j
 return (1-u)*(1-w)*array[j,i]+u*(1-w)*array[j,ii]+(1-u)*w*array[jj,i]+u*w*array[jj,ii]
decoded=np.where(base<=.04045,base/12.92,((base+.055)/1.055)**2.4);target=np.array([.19,.28,.42])+(np.array([1,.085,.006])-np.array([.19,.28,.42]))*mask[:,:,None]
assert np.max(abs(decoded-target))<.006
assert np.max(abs(orm-np.stack([.08+.04*mask,.37-.05*mask,.12-.04*mask],axis=2)))<.004
binding=json.loads((out/'export/export-binding.json').read_text());data=(out/'export'/binding['file']).read_bytes();assert sha(data)==binding['export_sha256']
assert struct.unpack_from('<I',data,8)[0]==len(data)
n=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+n]);binary=data[28+n:]
assert doc['asset']['generator']==source['asset']['generator'] and 'Meshy' in doc['asset']['copyright']
def accessor(i,dtype,width):
 ac=doc['accessors'][i];view=doc['bufferViews'][ac['bufferView']]
 return np.frombuffer(binary,dtype=dtype,count=ac['count']*width,offset=view.get('byteOffset',0)+ac.get('byteOffset',0)).reshape(-1,width)
prims=doc['meshes'][0]['primitives'];assert len(prims)==1;p=prims[0]
pos=accessor(p['attributes']['POSITION'],'<f4',3);norm=accessor(p['attributes']['NORMAL'],'<f4',3);tex=accessor(p['attributes']['TEXCOORD_0'],'<f4',2);tri=accessor(p['indices'],'<u4',1).reshape(-1,3)
mapping=np.frombuffer((out/'export'/binding['vertex_map_file']).read_bytes(),dtype='<u4');assert sha(mapping.tobytes())==binding['vertex_map_sha256']
assert pos.tobytes()==v[mapping].tobytes() and np.array_equal(mapping[tri],ix)
assert np.allclose(tex[tri][:,:,0],uv[:,:,0],atol=1e-7) and np.allclose(tex[tri][:,:,1],1-uv[:,:,1],atol=1e-7)
assert np.allclose(np.linalg.norm(norm,axis=1),1,atol=1e-6)
for i,row in enumerate(doc['images']):
 view=doc['bufferViews'][row['bufferView']];start=view.get('byteOffset',0);raw_png=binary[start:start+view['byteLength']]
 assert sha(raw_png)==binding['material_textures'][row['name']]
source_tree=BVHTree.FromPolygons(v.tolist(),ix.tolist(),all_triangles=True);export_tree=BVHTree.FromPolygons(pos.tolist(),tri.tolist(),all_triangles=True);rays=[]
def barycentric(point,pts):
 ab=pts[1]-pts[0];ac=pts[2]-pts[0];ap=np.array(point)-pts[0]
 aa=np.dot(ab,ab);bb=np.dot(ac,ac);cc=np.dot(ab,ac);d=np.dot(ap,ab);e=np.dot(ap,ac);den=aa*bb-cc*cc
 u=(bb*d-cc*e)/den;w=(aa*e-cc*d)/den;return np.array([1-u-w,u,w])
def ray(origin,direction,label,expected=None):
 h=source_tree.ray_cast(Vector(origin),Vector(direction));g=export_tree.ray_cast(Vector(origin),Vector(direction))
 assert h[2] is not None and h[2]==g[2];f=h[2]
 w=barycentric(h[0],v[ix[f]].astype(float));q=w@uv[f];q[1]=1-q[1];r=w@tex[tri[f]]
 value=float(sample(mask,q));value_export=float(sample(mask,r));assert abs(value-value_export)<.001
 selected=value>=.5
 if expected is not None:assert selected==expected,(label,value)
 rays.append({'case':label,'source_triangle':int(f),'export_triangle':int(g[2]),'uv_gltf':r.tolist(),'mask_value':value_export,'selected':selected})
for label,origin,expected in [('left_pectoral',(.09,.52,1),True),('right_pectoral',(-.09,.52,1),False),('deltoid',(.22,.56,1),False),('abdomen',(0,.10,1),False)]:ray(origin,(0,0,-1),label,expected)
def face_ray(i,weights,label,expected):
 pts=v[ix[i]].astype(float);point=np.asarray(weights)@pts;normal=np.cross(pts[1]-pts[0],pts[2]-pts[0]);normal/=np.linalg.norm(normal)
 ray(point+normal*.00002,-normal,label,expected)
corners=uv.copy();corners[:,:,1]=1-corners[:,:,1];corner_values=sample(mask,corners)
old=np.frombuffer((root/'correction/regions/triangle-regions.u8').read_bytes(),dtype=np.uint8);centers=v[ix].mean(1)
average=corners.mean(1);center_values=sample(mask,average)
fold=np.flatnonzero((old==1)&(centers[:,0]>.12)&(centers[:,1]<.49)&(center_values<.01));assert len(fold)
i=int(fold[np.argmin(centers[fold,2])]);face_ray(i,(1/3,1/3,1/3),'formerly_orange_axillary_fold_now_blue',False)
crossing=np.flatnonzero((corner_values.min(1)<.05)&(corner_values.max(1)>.95));assert len(crossing)
for i in crossing:
 weights=np.eye(3)*.925+.025;values=sample(mask,weights@corners[i])
 if values.min()<.1 and values.max()>.9:
  face_ray(int(i),weights[values.argmin()],'same_triangle_unpainted_point',False)
  face_ray(int(i),weights[values.argmax()],'same_triangle_painted_point',True)
  break
else:raise AssertionError('No test points prove within-face texture selection')
render=json.loads((out/'renders/render-metadata.json').read_text());assert len(render['frames'])==7
assert render['blend_sha256']==post['input_blend_sha256'] and sha(Path(__file__).with_name('render_texture_poc.py').read_bytes())==render['renderer_sha256']
for frame in render['frames']:assert sha((out/'renders'/frame['file']).read_bytes())==frame['sha256']
neutral=png(out/'renders/neutral-front.png');previous=png(root/'correction/renders/after-neutral-front.png');assert np.array_equal(neutral,previous)
# Exercise Blender's independent glTF importer; this is not a WebView/iPhone test.
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(out/'export'/binding['file']),merge_vertices=False)
imported=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(imported)==1
im=imported[0];assert len(im.data.polygons)==len(ix) and len(im.data.vertices)==len(pos)
assert len(im.data.uv_layers)==1 and im.data.materials[0].use_nodes
ibsdf=im.data.materials[0].node_tree.nodes.get('Principled BSDF');assert ibsdf.inputs['Base Color'].is_linked and ibsdf.inputs['Roughness'].is_linked and ibsdf.inputs['Coat Weight'].is_linked
report={'source_file_intact':True,'source_sha256':EXPECTED_SHA,'source_vertices':len(v),'source_triangles':len(ix),'blender_positions_and_indices_bit_equal_source':True,'source_geometry_changes':0,
 'blender_mask_image_packed_linear':True,'selection_is_not_face_material_labels':True,'uv_chart_triangles':build['uv_chart_triangles'],'painted_uv_overlap_texels':build['painted_uv_overlap_texels'],'mask_at_chart_seam':build['uv_seam_mask_max'],
 'export_vertices':len(pos),'uv_seam_duplicate_vertices':len(pos)-len(v),'export_triangles':len(tri),'export_source_face_order_verified':True,'export_vertex_to_source_verified':True,'export_normals_unit_length':True,
 'png_bytes_embedded_verified':True,'baked_PBR_matches_mask_within_8bit_tolerance':True,'source_export_raycast_uv_checks':rays,'boundary_triangles_with_black_and_white_corners':len(crossing),'glb_independent_blender_import_ok':True,
 'neutral_render_pixel_identical_to_898aac6':True,'render_hashes_verified':True,'blender_frames':7,'mobile_runtime_tested':False,'application_integration':False,
 'limitations':['Only one pectoral; local UV working chart, not full-body atlas.','Blender importer and offline UV raycasts are not Three.js/WebView/iPhone validation.','Authored surface contour is an artistic approximation, not a medical boundary.']}
(out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('TEXTURE_POC_VERIFIED',json.dumps({'rays':len(rays),'boundary_triangles':len(crossing),'export_vertices':len(pos),'geometry_changes':0,'neutral_pixels_identical':True}),flush=True)
