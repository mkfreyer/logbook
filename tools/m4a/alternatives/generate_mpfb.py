"""Generate the audited MPFB candidate from official core assets, outside Logbook runtime."""
import argparse,importlib,importlib.util,json,sys,types
from pathlib import Path
import bpy

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--mpfb-dir',required=True,type=Path)
parser.add_argument('--eyes-dir',required=True,type=Path)
parser.add_argument('--work-dir',required=True,type=Path)
parser.add_argument('--output',required=True,type=Path)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
args.work_dir.mkdir(parents=True,exist_ok=True)
args.output.parent.mkdir(parents=True,exist_ok=True)
bpy.context.preferences.system.use_online_access=False
package='bl_ext.logbook_audit.mpfb'
for name in ['bl_ext','bl_ext.logbook_audit']:
    if name not in sys.modules:
        module=types.ModuleType(name);module.__path__=[];sys.modules[name]=module
module_path=args.mpfb_dir/'src/mpfb'
spec=importlib.util.spec_from_file_location(package,module_path/'__init__.py',submodule_search_locations=[str(module_path)])
module=importlib.util.module_from_spec(spec);sys.modules[package]=module;spec.loader.exec_module(module)
preferences=importlib.import_module(package+'._preferences').MpfbPreferences
bpy.utils.register_class(preferences)
entry=bpy.context.preferences.addons.new();entry.module=package
entry.preferences.mpfb_user_data=str(args.work_dir.resolve())
module.register()
HumanService=importlib.import_module(package+'.services.humanservice').HumanService
TargetService=importlib.import_module(package+'.services.targetservice').TargetService
ExportService=importlib.import_module(package+'.services.exportservice').ExportService
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
macros=TargetService.get_default_macro_info_dict()
macros.update(gender=1.0,age=0.5,muscle=1.0,weight=0.35,proportions=0.55)
body=HumanService.create_human(macro_detail_dict=macros)
body.name='MPFB_Athletic_Body'
details={'stomach/stomach-tone-incr':0.6,'torso/torso-muscle-pectoral-incr':0.25,'torso/torso-muscle-dorsi-incr':0.25}
for fragment,weight in details.items():
    TargetService.load_target(body,str(module_path/'data/targets'/(fragment+'.target.gz')),weight=weight)
eyes=HumanService.add_mhclo_asset(str(args.eyes_dir/'low-poly.mhclo'),body,asset_type='Eyes',subdiv_levels=1,material_type='NONE',set_up_rigging=False,import_weights=False)
eyes.name='MPFB_Core_Eyes'
ExportService.bake_modifiers_remove_helpers(body,bake_masks=True,bake_subdiv=False,remove_helpers=True,also_proxy=False)
bpy.ops.wm.save_as_mainfile(filepath=str(args.output.resolve()))
settings={'macros':macros,'detail_targets':details,'objects':[body.name,eyes.name]}
args.output.with_suffix('.settings.json').write_text(json.dumps(settings,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'body_vertices':len(body.data.vertices),'body_polygons':len(body.data.polygons),'output':str(args.output)}))
