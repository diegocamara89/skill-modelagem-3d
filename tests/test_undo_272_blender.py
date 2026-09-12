"""Executar apenas pelo launcher isolado roda_regressao_272.py --gui."""
import bpy,sys,json,os,traceback
from pathlib import Path
assert os.environ.get('MODELAGEM_TESTE_ISOLADO')=='1'
assert not bpy.app.background and not bpy.data.filepath
OUT=Path(sys.argv[sys.argv.index('--')+1]);ROOT=Path(__file__).resolve().parents[1]
# Reuse fixture and independent geometry assertions, not a copy of product logic.
source=(ROOT/'tests/test_operacoes_272_blender.py').read_text(encoding='utf-8')
source=source[:source.index("run('captura_desatualizada'")]
source=source.replace("assert bpy.app.background,'Somente headless; nao executar na cena do usuario'",'')
exec(compile(source,str(ROOT/'tests/test_operacoes_272_blender.py'),'exec'),globals())
from mover_regiao import _contexto
ops=iter(['extrusao','alinhamento','preenchimento','arredondamento']);state={'phase':'start'}

def tick():
 try:
  phase=state['phase']
  if phase=='start':
   try:state['op']=next(ops)
   except StopIteration:
    OUT.write_text(json.dumps(rows,indent=2));bpy.ops.wm.quit_blender();return None
   # positive() constructs fixture and executes one operation; to capture its before
   # without duplicating setup, wrap transport and push baseline immediately before mutation.
   original=globals()['call']
   def tracked(op,params,token=None):
    if op!='capturar':
     state['before']=geometry()
     with bpy.context.temp_override(**_contexto()):bpy.ops.ed.undo_push(message='Baseline sintetica')
    return original(op,params,token)
   globals()['call']=tracked
   try:positive(state['op'])
   finally:globals()['call']=original
   state['after']=geometry();state['phase']='undo'
  elif phase=='undo':
   with bpy.context.temp_override(**_contexto()):bpy.ops.ed.undo()
   assert geometry()==state['before'],'Undo nao restaurou geometria'
   state['phase']='redo'
  else:
   with bpy.context.temp_override(**_contexto()):bpy.ops.ed.redo()
   assert geometry()==state['after'],'Redo nao restaurou geometria'
   rows.append(dict(caso=state['op'],undo_exato=True,redo_exato=True,passou=True));OUT.write_text(json.dumps(rows,indent=2));state['phase']='start'
 except Exception:
  rows.append(dict(caso=state.get('op'),passou=False,erro=traceback.format_exc()));OUT.write_text(json.dumps(rows,indent=2));bpy.ops.wm.quit_blender();return None
 return .3
bpy.app.timers.register(tick,first_interval=2)
