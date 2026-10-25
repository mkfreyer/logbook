"""Restore the native donor jaw/neck; join below it without resculpting the head."""
import argparse,json,os,sys
from pathlib import Path
import bpy
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from assemble_head import sha,clip,compact,boundary,cyclic,smooth_normals,Sampler,smooth,source as read_source


def zipper(faces,lower,upper,angle0,angle1):
 i=j=0
 while i<len(lower) or j<len(upper):
  a=angle0[(i+1)%len(lower)]+(2*np.pi if i+1>=len(lower) else 0) if i<len(lower) else float('inf')
  b=angle1[(j+1)%len(upper)]+(2*np.pi if j+1>=len(upper) else 0) if j<len(upper) else float('inf')
  x,y=int(lower[i%len(lower)]),int(upper[j%len(upper)])
  if a<b:faces.append([x,int(lower[(i+1)%len(lower)]),y]);i+=1
  else:faces.append([x,int(upper[(j+1)%len(upper)]),y]);j+=1


def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);source=a.source.resolve();root=a.output.resolve();root.mkdir(parents=True,exist_ok=True)
 prior=json.loads((source/'assemblage.json').read_text())
 assert prior['master_sha256']=='0ac1c4dc0529b1dc07bf13d1795fe283ed3d342f743e44ca058da68d6b9e9bd9'
 assert sha(source/prior['master'])==prior['master_sha256']
 bpy.ops.wm.open_mainfile(filepath=str(source/prior['master']),use_scripts=False)
 before=bpy.data.scenes[prior['scene_after']];before.name='03_ASSEMBLAGE_DBBA75E'
 old=next(o for o in before.objects if o.type=='MESH')
 oldv=np.array([x.co[:] for x in old.data.vertices]);oldf=np.array([x.vertices[:] for x in old.data.polygons],np.int32)
 oldn=np.array([x.vector[:] for x in old.data.corner_normals]).reshape(-1,3,3)
 oldids=np.array([x.value for x in old.data.attributes['source_triangle'].data])
 nbv=prior['body_vertex_count_after_cut'];nbf=prior['retained_body_triangles_after_cut'];nh=nbf+prior['bridge_triangles']
 # Keep the complete native chin/under-jaw; trim only the donor neck base.
 dv,df,_=read_source(source/'source-tete.glb')
 dv=dv*prior['head_scale_uniform']+np.array(prior['head_translation_m'])
 head_normals=smooth_normals(dv,df)
 head_sampler=Sampler(dv,df,head_normals)
 normal=(-.2,-.16,1);normal2=(.2,-.16,1);offset=.698;cut=.683
 hv,hf,hids=clip(dv,df,offset,True,plane_normal=normal)
 hv,hf,hids=clip(hv,hf,offset,True,hids,normal2);hv,hf=compact(hv,hf)
 full_body_v,full_body_f,_=read_source(source/prior['body_source'])
 bv,bf,body_ids=clip(full_body_v,full_body_f,cut,False);bv,bf=compact(bv,bf)
 nbv,nbf=len(bv),len(bf)
 center=np.array([-.0016,.015])
 br,ba=boundary(bv,bf,center);hr,ha=boundary(hv,hf,center)
 sampler=Sampler(oldv,oldf,oldn)
 hn=np.array([head_sampler.normal(q) for q in hv[hr]])
 ga=np.arange(192)*2*np.pi/192
 bottom=cyclic(ga,ba,bv[br]);bn=np.array([sampler.normal(q) for q in bottom])
 top=cyclic(ga,ha,hv[hr]);span=top[:,2]-cut
 radial_unit=np.column_stack([np.sin(ga),-np.cos(ga)])
 bottom_radius=np.linalg.norm(bottom[:,:2]-center,axis=1)
 top_radius=np.linalg.norm(top[:,:2]-center,axis=1)
 top_normal=cyclic(ga,ha,hn)
 ds0=np.clip(-bn[:,2]/np.maximum(np.sum(bn[:,:2]*radial_unit,axis=1),.1),-1.5,1.5)
 ds1=np.clip(-top_normal[:,2]/np.maximum(np.sum(top_normal[:,:2]*radial_unit,axis=1),.1),-1.5,1.5)
 for _ in range(8):
  ds0=.5*ds0+.25*(np.roll(ds0,1)+np.roll(ds0,-1));ds1=.5*ds1+.25*(np.roll(ds1,1)+np.roll(ds1,-1))
 assert span.min()>.004 and span.max()<.045
 vertices=bv.tolist();faces=bf.tolist();lower=br;rings=15
 for step in range(1,rings+1):
  t=step/(rings+1)
  radius=((2*t**3-3*t*t+1)*bottom_radius+(t**3-2*t*t+t)*span*ds0+(-2*t**3+3*t*t)*top_radius+(t**3-t*t)*span*ds1)
  # Fair small angular irregularities inside the new collar, fading to zero
  # at both fixed source rims. Work in angular distance, not vertex index.
  dense_angle=np.arange(720)*2*np.pi/720
  dense=cyclic(dense_angle,ga,radius[:,None])[:,0]
  kernel=np.exp(-np.arange(-24,25,dtype=float)**2/(2*8**2));kernel/=kernel.sum()
  filtered=sum(weight*np.roll(dense,k) for k,weight in zip(range(-24,25),kernel))
  fair=cyclic(ga,dense_angle,filtered[:,None])[:,0]
  radius+=.9*np.sin(np.pi*t)**2*(fair-radius)
  xy=center+radius[:,None]*radial_unit
  points=np.column_stack([xy,cut+t*span]);upper=np.arange(len(vertices),len(vertices)+len(points));vertices.extend(points.tolist())
  if step==1:zipper(faces,lower,upper,ba,ga)
  else:
   for k in range(len(lower)):
    j=(k+1)%len(lower);faces.extend([[int(lower[k]),int(lower[j]),int(upper[k])],[int(lower[j]),int(upper[j]),int(upper[k])]])
  lower=upper
 head_offset=len(vertices);vertices.extend(hv.tolist());upper=hr+head_offset
 zipper(faces,lower,upper,ga,ha)
 bridge=len(faces)-nbf;faces.extend((hf+head_offset).tolist())
 v=np.asarray(vertices,dtype=np.float32).astype(float);f=np.array(faces,np.int32)
 assert (v[:nbv,2]<=cut+1e-7).all()
 normals=smooth_normals(v,f);normals[:nbf]=np.array([[sampler.normal(q) for q in v[face]] for face in f[:nbf]])
 # Transfer original upper-head shading; blend the new collar to both fixed rims.
 headnorm=np.array([head_sampler.normal(q) for q in hv]);normals[nbf+bridge:]=headnorm[hf]
 for fi in range(nbf,nbf+bridge):
  for k,vi in enumerate(f[fi]):
   if vi<nbv:normals[fi,k]=sampler.normal(v[vi])
   elif vi>=head_offset:normals[fi,k]=headnorm[vi-head_offset]
   else:
    index=(vi-nbv)%len(ga);z=v[vi,2];tz=top[index,2];fade=min(.008,(tz-cut)/3)
    wb=1-float(smooth((z-cut)/fade));wh=1-float(smooth((tz-z)/fade))
    hn0=cyclic(np.array([ga[index]]),ha,hn)[0]
    normals[fi,k]=(1-wb-wh)*normals[fi,k]+wb*bn[index]+wh*hn0
 mesh=bpy.data.meshes.new('MARBLE_TITAN_RACCORD_LOCAL');mesh.from_pydata(v.tolist(),[],f.tolist())
 mesh.materials.append(old.data.materials[0])
 for polygon in mesh.polygons:polygon.use_smooth=True
 mesh.update();mesh.normals_split_custom_set(normals.reshape(-1,3).tolist())
 for name,values in [('surface_source',np.r_[np.zeros(nbf,np.int32),np.full(bridge,2,np.int32),np.ones(len(hf),np.int32)]),('source_triangle',np.r_[body_ids,np.full(bridge,-1,np.int32),hids])]:
  attr=mesh.attributes.new(name,'INT','FACE');attr.data.foreach_set('value',values)
 after=bpy.data.scenes.new('01_ASSEMBLAGE_CORPS_TETE');after.use_fake_user=True;after.world=before.world
 after.collection.children.link(bpy.data.collections['CAMERAS_LUMIERES_COMMUNES'])
 ob=bpy.data.objects.new('ASSEMBLAGE__Marble_Titan_Tete_Source',mesh);after.collection.objects.link(ob)
 for key in old.keys():ob[key]=old[key]
 ob['asset_id']='meshy.anatomical_form.marble_titan.native_head'
 ob['role']='Native donor head, chin and underside retained; only lower neck joined to preserved body.'
 for scene in list(bpy.data.scenes):
  if scene not in [before,after,bpy.data.scenes[prior['source_body_scene']]]:bpy.data.scenes.remove(scene)
 reference=bpy.data.scenes.new('02_TETE_DONNEUSE_SOURCE');reference.use_fake_user=True;reference.world=before.world
 reference.collection.children.link(bpy.data.collections['CAMERAS_LUMIERES_COMMUNES'])
 reference_mesh=bpy.data.meshes.new('MARBLE_TITAN_SOURCE_INTACT');reference_mesh.from_pydata(dv.tolist(),[],df.tolist())
 reference_mesh.materials.append(old.data.materials[0])
 for face in reference_mesh.polygons:face.use_smooth=True
 ref_ob=bpy.data.objects.new('REFERENCE__Marble_Titan_Original',reference_mesh);reference.collection.objects.link(ref_ob)
 meta=dict(prior)
 meta.update({'body_source':os.path.relpath(source/prior['body_source'],root),'head_source':os.path.relpath(source/prior['head_source'],root),
 'scene_before':reference.name,'scene_after':after.name,'comparison_master':os.path.relpath(source/prior['master'],root),
 'comparison_master_sha256':prior['master_sha256'],'comparison_glb':os.path.relpath(source/prior['export'],root),
 'comparison_glb_sha256':sha(source/prior['export']),'comparison_head_label':'Marble Titan source intacte',
 'head_label':'Marble Titan — tête source conservée','native_head_restoration':True,
 'head_cut_plane_normal':list(normal),'head_cut_plane_offset_m':offset,'head_cut_planes':[{'normal':list(normal),'offset':offset},{'normal':list(normal2),'offset':offset}],'head_offset':head_offset,
 'body_cut_z_m':cut,'body_vertex_count_after_cut':nbv,'retained_body_triangles_after_cut':nbf,
 'body_boundary_vertices':len(br),'body_reference_scene':before.name,'restored_body_neck_strip_m':[cut,prior['body_cut_z_m']],
 'donor_extracted_head_triangles':len(hf),'bridge_triangles':bridge,'assembled_triangles':len(f),
 'head_boundary_vertices':len(hr),'head_original_surface_retained_above_z_m':float(hv[hr,2].max()),
 'collar_regular_samples':len(ga),
 'head_core_unchanged_above_z_m':float(hv[hr,2].max()),'head_local_attachment_height_m':float(hv[hr,2].max()-cut),
 'local_z_range_m':[cut,float(hv[hr,2].max())], 'protected_body_vertices':nbv,
 'topology_changed':True,'topology_change_scope':'Donor neck clipped below the native chin with two oblique planes; receiving neck lowered 12 mm; local bridge only.',
 'modifications':'Native donor head, chin and under-jaw retained without sculpting; source body retained below z=0.683; only the immediate neck connection rebuilt. No muscle segmentation or app integration.',
 'refiner_sha256':sha(Path(__file__))})
 meta.pop('builder_sha256',None);meta.pop('master_sha256',None)
 bpy.data.texts['ASSEMBLAGE.json'].clear();bpy.data.texts['ASSEMBLAGE.json'].write(json.dumps(meta,indent=2))
 bpy.data.texts['ATTRIBUTION.txt'].clear();bpy.data.texts['ATTRIBUTION.txt'].write('Model created with Meshy — CC BY 4.0 License. '+meta['modifications'])
 bpy.context.window.scene=after;bpy.context.preferences.filepaths.save_version=0
 bpy.ops.wm.save_as_mainfile(filepath=str(root/meta['master']),compress=True);meta['master_sha256']=sha(root/meta['master'])
 (root/'assemblage.json').write_text(json.dumps(meta,indent=2)+'\n')
 translation=np.array(meta['head_translation_m']);scale=meta['head_scale_uniform']
 np.savez_compressed(root/'assembly-provenance.npz',head_original=(hv-translation)/scale,head_rigid=hv,head_fitted=hv,head_faces=hf,
 body_clipped=bv,body_faces=bf,body_source_faces=body_ids,head_source_faces=hids)
 print('REFINED',json.dumps({k:meta[k] for k in ['assembled_triangles','local_z_range_m','master_sha256']}),flush=True)

if __name__=='__main__':main()
