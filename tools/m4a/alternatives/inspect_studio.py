"""Inventory official body meshes, embedded licence statements and sculpt face sets."""
import bpy,json,hashlib,argparse,sys
from pathlib import Path
from collections import Counter
parser=argparse.ArgumentParser(description='Inspect the two complete male Blender Studio assets without executing embedded scripts.')
parser.add_argument('--blend',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
p=args.blend
collections=['Body Male - Realistic','Body Male - Stylized']
with bpy.data.libraries.load(str(p),link=False) as (src,dst):
 dst.collections=collections
 dst.texts=list(src.texts)
r={'source_blend_sha256':hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),'texts':{t.name:t.as_string() for t in dst.texts},'collections':[]}
for c in dst.collections:
 a=c.asset_data
 d={'name':c.name,'asset':{k:getattr(a,k) for k in ['author','description','license','copyright']},'objects':[]}
 for o in c.objects:
  m=o.data;m.calc_loop_triangles();parents=list(range(len(m.vertices)))
  def find(x):
   while parents[x]!=x:parents[x]=parents[parents[x]];x=parents[x]
   return x
  for e in m.edges:
   i,j=map(find,e.vertices);parents[i]=j
  fs=m.attributes.get('.sculpt_face_set')
  d['objects'].append({'name':o.name,'vertices':len(m.vertices),'faces':len(m.polygons),'triangles':len(m.loop_triangles),'vertex_groups':[g.name for g in o.vertex_groups],'connected_components':len({find(i) for i in range(len(parents))}),'face_sets':dict(Counter(v.value for v in fs.data)) if fs else None,'modifiers':[{'name':mod.name,'type':mod.type,**{k:getattr(mod,k) for k in ['levels','render_levels','sculpt_levels','total_levels'] if hasattr(mod,k)}} for mod in o.modifiers]})
 r['collections'].append(d)
args.output.write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({'output':str(args.output),'collections':len(r['collections'])}))
