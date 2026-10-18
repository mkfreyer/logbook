"""Texture-only regional material experiment on the exact B+ Puissance mesh."""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy,numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.output=a.output.resolve();a.output.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(a.source.resolve()),use_scripts=False)
body=bpy.data.objects['BPF.body'];mesh=body.data;xyz=np.array([v.co[:] for v in mesh.vertices]);x=np.abs(xyz[:,0]);y=xyz[:,1];z=xyz[:,2]
def sig(t):
 t=np.clip(t,0,1);return t*t*(3-2*t)
u=(x-.010)/.224;uc=np.clip(u,0,1)
zlo=(1-uc)*1.306+uc*1.366-.030*np.sin(np.pi*uc);zhi=(1-uc)*1.458+uc*1.391+.010*np.sin(np.pi*uc)
v=(z-zlo)/(zhi-zlo)
pec=sig((u+.02)/.06)*sig((1.02-u)/.06)*sig((v+.02)/.06)*sig((1.02-v)/.06)*sig((.015-y)/.065)
origin=np.array([.218,.027,1.480]);axis=np.array([.345,0,-.939]);axis/=np.linalg.norm(axis);lateral=np.array([-axis[2],0,axis[0]])
local=np.column_stack([x,y,z])-origin;t=local@axis/.205;angle=np.arctan2(-local[:,1],local@lateral)
du=.5+angle/4.6;dv=(t+.15)/1.2
shoulder=sig((x-.165)/.035)*sig((.330-x)/.030)*sig((du-.012)/.055)*sig((.988-du)/.055)*sig((dv-.012)/.060)*sig((.988-dv)/.060)
loop_index=np.array([l.vertex_index for l in mesh.loops]);active=mesh.uv_layers.active_index
for name,coords in [('M4A_visual_pectoral',np.column_stack([u,v])),('M4A_visual_deltoid',np.column_stack([du,dv]))]:
 uv=mesh.uv_layers.new(name=name);uv.data.foreach_set('uv',coords[loop_index].astype(np.float32).ravel())
mesh.uv_layers.active_index=active
attrs={}
for prefix,values in [('pec',pec),('delt',shoulder)]:
 for side,test in [('L',xyz[:,0]>0),('R',xyz[:,0]<0)]:
  name='m4a_mat_'+prefix+'_'+side;values_side=(values*test).astype(np.float32);attrs[name]=values_side
  attr=mesh.attributes.new(name,'FLOAT','POINT');attr.data.foreach_set('value',values_side)
m=bpy.data.materials.new('M4A visual ecorche / original texture maps');m.use_nodes=True;nodes=m.node_tree.nodes;links=m.node_tree.links;n=nodes.get('Principled BSDF')
n.inputs['Metallic'].default_value=.12;n.inputs['Roughness'].default_value=.37;n.inputs['Coat Weight'].default_value=.08;n.inputs['Coat Roughness'].default_value=.32
base=nodes.new('ShaderNodeRGB');base.outputs[0].default_value=(.23,.30,.41,1)
color=base.outputs[0];rough=nodes.new('ShaderNodeValue');rough.outputs[0].default_value=.37;rough_socket=rough.outputs[0]
geometry=nodes.new('ShaderNodeNewGeometry');normal=geometry.outputs['Normal'];selected=nodes.new('ShaderNodeValue');selected.name='M4A selected region';selected.outputs[0].default_value=0
orange_factor=None
for zone,uv_name,attr_prefix,ids in [('pectoral','M4A_visual_pectoral','pec',(1,2)),('deltoid','M4A_visual_deltoid','delt',(3,4))]:
 uvnode=nodes.new('ShaderNodeUVMap');uvnode.uv_map=uv_name
 textures={}
 for kind in ['normal','surface']:
  file=a.output/'textures'/(zone+'-'+kind+'.png');im=bpy.data.images.load(str(file),check_existing=False);im.colorspace_settings.name='Non-Color';im.pack();im.filepath='//textures/'+file.name
  tex=nodes.new('ShaderNodeTexImage');tex.image=im;tex.interpolation='Linear';tex.extension='CLIP';links.new(uvnode.outputs['UV'],tex.inputs['Vector']);textures[kind]=tex
 split=nodes.new('ShaderNodeSeparateColor');links.new(textures['surface'].outputs['Color'],split.inputs['Color'])
 mask_sum=None
 for side,region_id in zip(['L','R'],ids):
  attr=nodes.new('ShaderNodeAttribute');attr.attribute_name='m4a_mat_'+attr_prefix+'_'+side
  mask=nodes.new('ShaderNodeMath');mask.operation='MULTIPLY';links.new(attr.outputs['Fac'],mask.inputs[0]);links.new(split.outputs['Red'],mask.inputs[1])
  if mask_sum is None:mask_sum=mask.outputs[0]
  else:
   add=nodes.new('ShaderNodeMath');add.operation='ADD';links.new(mask_sum,add.inputs[0]);links.new(mask.outputs[0],add.inputs[1]);mask_sum=add.outputs[0]
  compare=nodes.new('ShaderNodeMath');compare.operation='COMPARE';compare.inputs[1].default_value=region_id;compare.inputs[2].default_value=.1;links.new(selected.outputs[0],compare.inputs[0])
  mult=nodes.new('ShaderNodeMath');mult.operation='MULTIPLY';links.new(mask.outputs[0],mult.inputs[0]);links.new(compare.outputs[0],mult.inputs[1])
  if orange_factor is None:orange_factor=mult.outputs[0]
  else:
   mx=nodes.new('ShaderNodeMath');mx.operation='MAXIMUM';links.new(orange_factor,mx.inputs[0]);links.new(mult.outputs[0],mx.inputs[1]);orange_factor=mx.outputs[0]
 nm=nodes.new('ShaderNodeNormalMap');nm.uv_map=uv_name;nm.inputs['Strength'].default_value=.85;links.new(textures['normal'].outputs['Color'],nm.inputs['Color'])
 mix=nodes.new('ShaderNodeMixRGB');links.new(mask_sum,mix.inputs[0]);links.new(normal,mix.inputs[1]);links.new(nm.outputs['Normal'],mix.inputs[2])
 normalize=nodes.new('ShaderNodeVectorMath');normalize.operation='NORMALIZE';links.new(mix.outputs[0],normalize.inputs[0]);normal=normalize.outputs[0]
 tone=nodes.new('ShaderNodeMath');tone.operation='MULTIPLY_ADD';tone.inputs[1].default_value=.4;tone.inputs[2].default_value=.8;links.new(split.outputs['Blue'],tone.inputs[0])
 tinted=nodes.new('ShaderNodeMixRGB');tinted.blend_type='MULTIPLY';tinted.inputs[0].default_value=1;links.new(base.outputs[0],tinted.inputs[1]);links.new(tone.outputs[0],tinted.inputs[2])
 mix=nodes.new('ShaderNodeMixRGB');links.new(mask_sum,mix.inputs[0]);links.new(color,mix.inputs[1]);links.new(tinted.outputs[0],mix.inputs[2]);color=mix.outputs[0]
 r_mix=nodes.new('ShaderNodeMixRGB');links.new(mask_sum,r_mix.inputs[0]);links.new(rough_socket,r_mix.inputs[1]);links.new(split.outputs['Green'],r_mix.inputs[2]);rough_socket=r_mix.outputs[0]
sel=nodes.new('ShaderNodeMixRGB');links.new(orange_factor,sel.inputs[0]);links.new(color,sel.inputs[1]);sel.inputs[2].default_value=(1,.18,.025,1)
links.new(sel.outputs[0],n.inputs['Base Color']);links.new(rough_socket,n.inputs['Roughness']);links.new(normal,n.inputs['Normal'])
for o in bpy.context.scene.objects:
 if o.type=='MESH' and o.get('m4a_render'):o.data.materials.clear();o.data.materials.append(m)
body['m4a_material_poc']='One material-only experiment; no displaced vertices or changed normals in the mesh'
report={'variant':'material-poc','source_path':'docs/m4a/bplus-power/power/model.blend','source_sha256':hashlib.sha256(a.source.read_bytes()).hexdigest(),
 'preparer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'geometry_changes':False,'added_triangles':0,'visible_triangles':112176,'objects':3,
 'new_uv_sets':['M4A_visual_pectoral','M4A_visual_deltoid'],'preserved_original_uv':'UVMap',
 'material':'Blue silver base, two regional tangent-space normal maps, two packed surface maps, scalar regional coverage and independent selection ID',
 'selection_ids':{'0':'none','1':'pectoralis.left','2':'pectoralis.right','3':'deltoid.left','4':'deltoid.right'},
 'selection_masks':{k:int((v>.5).sum()) for k,v in attrs.items()},'commercial_cost_eur':0,'third_party_anatomy':False,
 'limitations':['Layered Blender shader is not a mobile material export; atlas consolidation or shader port remains future work.',
 'Normal maps affect shading, not silhouette, cast shadows or actual muscle geometry.','No mobile FPS benchmark or final anatomical segmentation.']}
(a.output/'construction.json').write_text(json.dumps(report,indent=2)+'\n');bpy.ops.wm.save_as_mainfile(filepath=str(a.output/'model.blend'),compress=True)
print('MATERIAL_POC',json.dumps(report),flush=True)
