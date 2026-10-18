#!/usr/bin/env python3
"""Create a stable, path-independent summary from source inventory diagnostics."""
import argparse
import json
from pathlib import Path

COUNT_KEYS=('vertices','faces','valid_faces','triangles_if_fan_triangulated','degenerate_triangles','boundary_edges','nonmanifold_edges','inconsistent_winding_edges')
TOPOLOGY_KEYS=('boundary_edges','nonmanifold_edges','inconsistent_winding_edges','collapsed_edges')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--audit-dir',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args(); b=args.audit_dir
    full=json.loads((b/'geometry/full-inventory.json').read_text())
    topology=json.loads((b/'geometry/selected-topology.json').read_text())
    selection=json.loads((b/'anatomy/selection-candidate.json').read_text())
    records={r['element_id']:r for r in full['elements']}
    welded={r['element_id']:r for r in topology['elements']}
    def summarize(ids):
        ids=sorted(set(ids)); rr=[records[e] for e in ids]
        result={
            'element_count':len(rr),
            'all_element_ids_present_in_archive':True,
            **{k:sum(r[k] for r in rr) for k in COUNT_KEYS},
            'elements_with_structural_issues':[r['element_id'] for r in rr if any(r['structural_issues'].values())],
            'elements_with_degenerate_triangles':[{'element_id':r['element_id'],'triangles':r['degenerate_triangles']} for r in rr if r['degenerate_triangles']],
            'bounds':{
                'min':[min(r['bounds']['min'][i] for r in rr) for i in range(3)],
                'max':[max(r['bounds']['max'][i] for r in rr) for i in range(3)],
            },
        }
        if all(e in welded for e in ids):
            result['exact_position_weld_diagnostic']={
                **{k:sum(welded[e]['after_exact_position_weld_diagnostic'][k] for e in ids) for k in TOPOLOGY_KEYS},
                'elements_with_multiple_components':sum(welded[e]['after_exact_position_weld_diagnostic']['connected_components']>1 for e in ids),
                'elements_with_nonmanifold_edges':[
                    {'element_id':e,'edges':welded[e]['after_exact_position_weld_diagnostic']['nonmanifold_edges']}
                    for e in ids if welded[e]['after_exact_position_weld_diagnostic']['nonmanifold_edges']
                ],
            }
        return result
    groups={}
    for label,file in [('all_muscles','all-muscle-audit-obj-ids.txt'),('candidate_surface','candidate-surface-obj-ids.txt'),('skin','skin-obj-ids.txt')]:
        groups[label]=summarize((b/'anatomy'/file).read_text().splitlines())
    pec_ids=['FJ1446','FJ1447','FJ1464','FJ1446M','FJ1447M','FJ1464M']
    groups['pectoralis_major_bilateral']=summarize(pec_ids)
    detail=[]
    for e in pec_ids+['FJ2810']:
        r=records[e]
        detail.append({k:r[k] for k in ('element_id','sha256','bytes','vertices','normals','texture_coordinates','faces','polygon_sizes','bounds','structural_issues','degenerate_triangles','boundary_edges','nonmanifold_edges','inconsistent_winding_edges')})
        detail[-1]['exact_position_weld_diagnostic']=welded[e]['after_exact_position_weld_diagnostic']
    official_tables=[]
    for table in full['tables']:
        name=Path(table['path']).name
        if name.startswith(('isa_','partof_')):
            official_tables.append({'file':name,'sha256':table['sha256'],'rows':table['rows']})
    report={
        'schema_version':1,
        'source_version':selection['source_version'],
        'source':{k:v for k,v in full['source'].items() if k!='archive'},
        'official_tables':sorted(official_tables,key=lambda x:x['file']),
        'methods':{
            **full['method'],
            'exact_position_weld':topology['method'],
            'degeneracy_threshold_cross_product_squared':1e-24,
            'geometry_modified':False,
            'interpretation':'Finite coordinates, valid indices, watertight edges, or component counts do not establish anatomical accuracy or the requested aesthetic. Visual and domain review remain separate gates.',
        },
        'source_coordinate_axes':{
            'x_positive':'anatomical left, verified by official lateralized pectoralis element labels and their coordinate bounds',
            'y_negative':'anterior, supported by pectoralis vs trapezius coordinate locations and initial render-agent inspection',
            'z_positive':'superior, supported by whole-body vertical range and initial render-agent inspection',
            'units':'source coordinate units; physical units not established by the archived README/download pages',
        },
        'full_archive':summarize(records),
        'groups':groups,
        'pectoral_and_skin_elements':detail,
        'selection_candidates':[
            {'id':entry['id'],'group_id':entry['group_id'],'side':entry['side'],'element_ids':entry['element_ids'],
             'component_identities':[{'concept_id':c['concept_id'],'name_en':c['name_en'],'element_ids':[e['element_id'] for e in c['elements']]} for c in entry['components']],
             'geometry':summarize(entry['element_ids']),
             'anatomical_and_visual_approval':False}
            for entry in selection['selection_candidates']
        ],
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(f'Wrote {args.output}: {len(report["selection_candidates"])} selection candidates')
    print(json.dumps(report['groups'],indent=2))
if __name__=='__main__':main()
