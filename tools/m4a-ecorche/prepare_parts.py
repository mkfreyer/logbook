"""Prepare component arrays for Blender, with no geometry retouch at this stage."""
import argparse,json
from pathlib import Path
import numpy as np
from source_parts import source_parts
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
doc,parts,meta=source_parts(a.source);records=[];data={}
for i,part in enumerate(parts):
 for k in ['v','n','c','f']:data[f'{i}_{k}']=part[k]
 records.append({k:part[k]for k in ['id','component','material']})
np.savez_compressed(a.output/'parts.npz',**data)
(a.output/'parts.json').write_text(json.dumps({'source_asset':doc['asset'],'normalization':meta,'parts':records},indent=2)+'\n');print('SOURCE_COMPONENTS_PREPARED',meta)
