"""Local neck finish on 62000ae; face, chin, hair and distant body are fixed."""
import argparse,json,os,sys
from pathlib import Path
import bpy,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from assemble_head import sha,smooth,smooth_normals


def finish_weight(v):
 z,x,y=v[:,2],np.abs(v[:,0]),v[:,1]
 upper=.735+.04*smooth((y+.005)/.04)
 w=smooth((z-.645)/.022)*smooth((upper-z)/.018)
 w*=smooth((.135-x)/.035)
 w*=smooth((y+.065)/.018)
 return w


def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);source=a.source.resolve();root=a.output.resolve();root.mkdir(parents=True,exist_ok=True)
 prior=json.loads((source/'assemblage.json').read_text());master=source/prior['master']
 assert sha(master)==prior['master_sha256']=='9754fd908e11671d53b016a7a791870d23a6931af2ea265d158f04590e345b18'
 bpy.ops.wm.open_mainfile(filepath=str(master),use_scripts=False)
 before=bpy.data.scenes[prior['scene_after']];before.name='00_AVANT_FINITION_62000AE'
 old=next(o for o in before.objects if o.type=='MESH')
 v=np.array([p.co[:] for p in old.data.vertices]);f=np.array([p.vertices[:] for p in old.data.polygons],np.int32)
 oldn=np.array([n.vector[:] for n in old.data.corner_normals]).reshape(-1,3,3)
 weight=finish_weight(v);allowed=weight>0
 edges=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1);edges=np.unique(edges,axis=0)
 adjacency=[[] for _ in v]
 for x,y in edges:adjacency[x].append(y);adjacency[y].append(x)
 active=np.flatnonzero(allowed);from_index=np.repeat(np.arange(len(active)),[len(adjacency[i]) for i in active]);neighbors=np.concatenate([adjacency[i] for i in active]);degree=np.bincount(from_index)
 # Tangential relaxation is limited as well as normal fairing. Alternating
 # steps retain the broad neck shape while removing small high-frequency kinks.
 result=v.copy()
 for iteration in range(50):
  for strength in ([.35] if iteration<30 else [.45,-.47]):
   average=np.column_stack([np.bincount(from_index,weights=result[neighbors,k],minlength=len(active))/degree for k in range(3)])
   step=(average-result[active])*weight[active,None]*strength
   result[active]+=step
   delta=result[active]-v[active];length=np.linalg.norm(delta,axis=1)
   limit=.003*weight[active]
   result[active]=v[active]+delta*np.minimum(1,limit/np.maximum(length,1e-12))[:,None]
 result=result.astype(np.float32).astype(float)
 assert np.array_equal(result[~allowed],v[~allowed])
 displacement=np.linalg.norm(result-v,axis=1);moved=displacement>0
 after=bpy.data.scenes.new('01_ASSEMBLAGE_CORPS_TETE');after.use_fake_user=True;after.world=before.world
 after.collection.children.link(bpy.data.collections['CAMERAS_LUMIERES_COMMUNES'])
 ob=old.copy();ob.data=old.data.copy();ob.name='ASSEMBLAGE__Marble_Titan_Finition_Locale_Cou';after.collection.objects.link(ob)
 ob.data.vertices.foreach_set('co',result.astype(np.float32).ravel());ob.data.update()
 normals=smooth_normals(result,f)
 # No shading change on protected corners. Geometry-derived smooth normals are
 # used only in the allowed neck domain, fading progressively at its boundary.
 blend=weight[f,None]
 normals=oldn*(1-blend)+normals*blend
 ob.data.normals_split_custom_set(normals.reshape(-1,3).tolist())
 ob['asset_id']='meshy.anatomical_form.marble_titan.local_neck_finish'
 ob['role']='Local neck/upper-trapezius surface finish only; head, chin and hair protected.'
 for scene in list(bpy.data.scenes):
  if scene not in [before,after]:bpy.data.scenes.remove(scene)
 meta=dict(prior)
 meta.update({'body_source':os.path.relpath(source/prior['body_source'],root),'head_source':os.path.relpath(source/prior['head_source'],root),
 'comparison_master':os.path.relpath(master,root),'comparison_master_sha256':prior['master_sha256'],
 'comparison_glb':os.path.relpath(source/prior['export'],root),'comparison_glb_sha256':sha(source/prior['export']),
 'scene_before':before.name,'scene_after':after.name,'head_label':'Marble Titan — finition locale du cou',
 'local_finish':True,'reference_commit':'62000ae','topology_changed':False,
 'topology_change_scope':'No vertices or triangles added, removed or reconnected.',
 'finish_weight_parameters':{'z_domain_m':[.645,.775],'upper_limit_front_m':.735,'upper_limit_back_m':.775,'x_absolute_max_m':.135,'front_protection_y_m':-.065,'displacement_cap_m':.003,'diffusion_steps':30,'taubin_pairs':20},
 'modified_vertices':int(moved.sum()),'displacement_max_m':float(displacement.max()),
 'displacement_mean_m':float(displacement[moved].mean()),
 'local_z_range_m':[float(v[moved,2].min()),float(v[moved,2].max())],
 'retained_body_vertices_moved':int(moved[:prior['body_vertex_count_after_cut']].sum()),
 'modifications':'Only local neck sides, head base and immediate upper-trapezius junction faired with a 3 mm displacement cap. Face, chin, hair and distant body fixed. Topology unchanged. No app or muscle segmentation work.',
 'finisher_sha256':sha(Path(__file__))})
 meta.pop('master_sha256',None);meta.pop('source_body_scene',None);meta.pop('body_reference_scene',None)
 bpy.data.texts['ASSEMBLAGE.json'].clear();bpy.data.texts['ASSEMBLAGE.json'].write(json.dumps(meta,indent=2))
 bpy.data.texts['ATTRIBUTION.txt'].clear();bpy.data.texts['ATTRIBUTION.txt'].write('Model created with Meshy — CC BY 4.0 License. '+meta['modifications'])
 bpy.context.window.scene=after;bpy.context.preferences.filepaths.save_version=0
 bpy.ops.wm.save_as_mainfile(filepath=str(root/meta['master']),compress=True)
 meta['master_sha256']=sha(root/meta['master']);(root/'assemblage.json').write_text(json.dumps(meta,indent=2)+'\n')
 np.savez_compressed(root/'finish-provenance.npz',original=v,finished=result,faces=f,allowed=allowed,weight=weight)
 print('FINISHED',json.dumps({k:meta[k] for k in ['modified_vertices','displacement_max_m','displacement_mean_m','local_z_range_m','master_sha256']}),flush=True)

if __name__=='__main__':main()
