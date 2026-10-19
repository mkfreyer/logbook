#!/usr/bin/env python3
"""Diagnose exact-position seams without modifying the official source geometry."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def diagnose(path):
    vertices, faces = [], []
    for raw in path.read_text(encoding='utf-8-sig').splitlines():
        parts=raw.split()
        if not parts:
            continue
        if parts[0] == 'v':
            vertices.append(tuple(float(v) for v in parts[1:4]))
        elif parts[0] == 'f':
            face=[]
            for corner in parts[1:]:
                index=int(corner.split('/')[0])
                if index == 0:
                    raise ValueError('Zero OBJ index')
                face.append(index-1 if index>0 else len(vertices)+index)
            faces.append(face)
    unique={}
    position_ids=[]
    for vertex in vertices:
        position_ids.append(unique.setdefault(vertex,len(unique)))
    parents=list(range(len(unique)))
    def root(a):
        while parents[a] != a:
            parents[a]=parents[parents[a]]
            a=parents[a]
        return a
    edges=Counter()
    winding=Counter()
    used=set()
    for face in faces:
        welded=[position_ids[i] for i in face]
        used.update(welded)
        for a,b in zip(welded,welded[1:]+welded[:1]):
            edge=tuple(sorted((a,b)))
            edges[edge]+=1
            winding[edge]+=1 if a<b else -1
            a,b=root(a),root(b)
            if a!=b:
                parents[b]=a
    components=Counter(root(i) for i in used)
    return {
        'element_id':path.stem,
        'obj_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'source_vertices':len(vertices),
        'unique_exact_positions':len(unique),
        'duplicate_position_vertices':len(vertices)-len(unique),
        'faces':len(faces),
        'after_exact_position_weld_diagnostic':{
            'boundary_edges':sum(count==1 for count in edges.values()),
            'nonmanifold_edges':sum(count>2 for count in edges.values()),
            'inconsistent_winding_edges':sum(edges[e]==2 and abs(w)==2 for e,w in winding.items()),
            'collapsed_edges':sum(a==b for a,b in edges),
            'connected_components':len(components),
            'component_used_vertex_counts':sorted(components.values(),reverse=True),
            'euler_characteristic':len(used)-len(edges)+len(faces),
        },
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--obj-dir',type=Path,required=True)
    p.add_argument('--elements-file',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    selection=json.loads(args.elements_file.read_text())
    elements=selection if isinstance(selection,list) else selection['element_ids']
    results=[diagnose(args.obj_dir/f'{element}.obj') for element in sorted(set(elements))]
    out={
        'schema_version':1,
        'method':{
            'geometry_mutation':False,
            'precision':'exact parsed floating-point coordinate equality; no rounding, tolerance, repair, or decimation',
            'scope':'Topological diagnostics only. Neither manifold topology nor connectedness establishes anatomical accuracy.',
            'rationale':'OBJ source can repeat positions at normal seams; raw vertex-index boundary counts alone do not establish holes.',
        },
        'elements':results,
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(f'Wrote {args.output}: {len(results)} elements')
if __name__=='__main__':
    main()
