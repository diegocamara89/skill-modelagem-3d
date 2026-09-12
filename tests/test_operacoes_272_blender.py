"""Somente Blender headless com factory startup; nenhum socket e usado."""
import sys,json,traceback,tempfile,struct,math
from pathlib import Path
import bpy,bmesh
ROOT=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT/'produto/scripts'))
from captura_estado import capturar
import operador_local as O
import cliente_operacao as C
OUT=Path(sys.argv[sys.argv.index('--')+1]);rows=[]
assert bpy.app.background,'Somente headless; nao executar na cena do usuario'
bpy.context.preferences.edit.use_global_undo=True

def fixture():
 if bpy.context.object and bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 bpy.ops.mesh.primitive_cube_add(size=10);ob=bpy.context.object;ob.name='Cubo'
 bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=.001
 bpy.context.tool_settings.mesh_select_mode=(False,False,True);bpy.ops.object.mode_set(mode='EDIT')
 bm=bmesh.from_edit_mesh(ob.data)
 for v in bm.verts:v.select_set(False)
 for e in bm.edges:e.select_set(False)
 for f in bm.faces:f.select_set(f.normal.z>.9)
 bm.select_flush_mode();bmesh.update_edit_mesh(ob.data)
 return ob

def geometry():
 bm=bmesh.from_edit_mesh(bpy.context.object.data);bm.verts.index_update()
 return dict(coords=[list(v.co) for v in bm.verts],faces=[[v.index for v in f.verts] for f in bm.faces])

def local_transport(kind,params,**kw):
 import contextlib,io
 out=io.StringIO()
 with contextlib.redirect_stdout(out):exec(compile(params['code'],'remote_same_process','exec'),{})
 return dict(estado='OK',resultado=dict(result=out.getvalue()))

def call(op,params,token=None):return C.executar(op,params,12345,token,local_transport)

def run(name,fn):
 try:detail=fn();rows.append(dict(caso=name,passou=True,detalhe=detail))
 except Exception:rows.append(dict(caso=name,passou=False,erro=traceback.format_exc()))
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(rows,indent=2))

def stale():
 ob=fixture();cap=capturar('Cubo')['captura'];bm=bmesh.from_edit_mesh(ob.data)
 next(iter(bm.verts)).co.x+=.2
 before=geometry()
 r=call('extrusao',dict(objeto='Cubo',distancia_mm=1,tolerancia_plano_mm=.001),cap)
 assert r['estado']=='RECUSADO' and geometry()==before,r
 # Same vertex/face count, different selection.
 cap=capturar('Cubo')['captura']
 for f in bm.faces:f.select_set(f.normal.z<-.9)
 before=geometry();r=call('extrusao',dict(objeto='Cubo',distancia_mm=1,tolerancia_plano_mm=.001),cap)
 assert r['estado']=='RECUSADO' and geometry()==before,r
 return r

def stale_edges():
 ob=fixture();bm=bmesh.from_edit_mesh(ob.data)
 bm.clear()
 vs=[bm.verts.new(co) for co in [(0,0,0),(1,0,0),(0,1,0),(1,1,0)]]
 bm.edges.new((vs[0],vs[1]));bm.edges.new((vs[2],vs[3]));bmesh.update_edit_mesh(ob.data,destructive=True)
 cap=capturar('Cubo')['captura'];counts=(len(bm.verts),len(bm.edges),len(bm.faces))
 for e in list(bm.edges):bm.edges.remove(e)
 bm.edges.new((vs[0],vs[2]));bm.edges.new((vs[1],vs[3]));bmesh.update_edit_mesh(ob.data,destructive=True)
 assert counts==(len(bm.verts),len(bm.edges),len(bm.faces))
 assert cap!=capturar('Cubo')['captura'],'Conectividade de arestas soltas ignorada'
 return dict(mesmas_contagens=True,token_mudou=True)

def failure(kind):
 ob=fixture();cap=capturar('Cubo')['captura'];before=geometry()
 def fn(**kw):
  bm=bmesh.from_edit_mesh(ob.data)
  if kind=='after':next(iter(bm.verts)).co.x+=2
  raise RuntimeError('Falha plantada '+kind)
 r=O.executar(fn,dict(objeto='Cubo'),cap,'extrusao')
 assert r['estado']==('FALHA_RESTAURADA' if kind=='after' else 'FALHA_SEM_ALTERACAO_LIQUIDA'),r
 assert geometry()==before and capturar('Cubo')['captura']==cap
 return r

def positive(op):
 ob=fixture();params=dict(objeto='Cubo')
 if op=='extrusao':params.update(distancia_mm=1,tolerancia_plano_mm=.001)
 if op=='alinhamento':params.update(ponto_mm=[0,0,6],normal=[0,0,1],maximo_mm=2)
 if op=='arredondamento':
  bpy.context.tool_settings.mesh_select_mode=(False,True,False);bm=bmesh.from_edit_mesh(ob.data)
  for f in bm.faces:f.select_set(False)
  for e in bm.edges:e.select_set(all(v.co.x>4.99 and v.co.y>4.99 for v in e.verts))
  params.update(raio_mm=1,segmentos=8)
 if op=='preenchimento':
  bm=bmesh.from_edit_mesh(ob.data);top=next(f for f in bm.faces if f.normal.z>.9);edges=list(top.edges)
  bmesh.ops.delete(bm,geom=[top],context='FACES_ONLY');bpy.context.tool_settings.mesh_select_mode=(False,True,False)
  for e in bm.edges:e.select_set(e in edges)
  params.update(modo='contorno',tolerancia_mm=.001)
 cap=call('capturar',dict(objeto='Cubo'));assert cap['estado']=='CAPTURA_DISPONIVEL',cap
 r=call(op,params,cap['captura']);assert r['estado']==C.ESTADOS[op],r
 bm=bmesh.from_edit_mesh(ob.data)
 if op in ('extrusao','alinhamento'):assert abs(max(v.co.z for v in bm.verts)-6)<1e-5 and abs(bm.calc_volume()-1100)<.001
 if op=='preenchimento':assert len(bm.faces)==6 and all(e.is_manifold for e in bm.edges)
 if op=='arredondamento':
  profile=[v for v in bm.verts if v.co.x>=3.9999 and v.co.y>=3.9999]
  assert len(profile)==18 and max(abs(math.hypot(v.co.x-4,v.co.y-4)-1) for v in profile)<1e-5
 return r

def movement():
 fixture();before=geometry()
 p=dict(objeto='Cubo',acao='inspecionar',distancia_mm=None,eixo='Z');cap=call('movimento',p)
 p.update(acao='mover',distancia_mm=1);r=call('movimento',p,cap['captura']);assert r['estado']=='DESLOCAMENTO_VERIFICADO',r
 after=geometry();assert max(v[2] for v in after['coords'])==6
 p.update(acao='desfazer',distancia_mm=None);undo=call('movimento',p,r['captura_depois']);assert undo['estado']=='HISTORICO_EXECUTADO' and geometry()==before,undo
 p.update(acao='refazer');redo=call('movimento',p,undo['captura_depois']);assert redo['estado']=='HISTORICO_EXECUTADO' and geometry()==after,redo
 return redo

def selection():
 fixture();p=dict(objeto='Cubo',modo='conectada',angulo_graus=None,distancia_mm=None,aplicar=False)
 before=geometry();r=call('selecao',p);assert r['estado']=='SELECAO_PLANEJADA' and len(r['faces'])==6,r
 p['aplicar']=True;result=call('selecao',p,r['captura']);assert result['estado']=='SELECAO_APLICADA' and geometry()==before,result
 assert all(f.select for f in bmesh.from_edit_mesh(bpy.context.object.data).faces)
 return result

def export():
 from bl_ferramentas import exporta_malha
 fixture();before=geometry();token=capturar('Cubo')['captura']
 with tempfile.TemporaryDirectory() as d:
  path=Path(d)/'cube.stl';r=exporta_malha('Cubo',str(path))
  data=path.read_bytes();count=struct.unpack('<I',data[80:84])[0]
  points=[struct.unpack('<12fH',data[84+50*i:134+50*i])[3:12] for i in range(count)]
  xyz=[[c[j] for c in points for j in range(axis,9,3)] for axis in range(3)]
  assert all(abs(max(a)-min(a)-10)<1e-5 for a in xyz)
  assert geometry()==before and capturar('Cubo')['captura']==token
  saved=path.read_bytes()
  try:exporta_malha('Cubo',str(path))
  except Exception:pass
  else:raise AssertionError('Sobrescreveu sem autorizacao')
  assert path.read_bytes()==saved
  return dict(triangulos=count,dimensoes=[max(a)-min(a) for a in xyz],modo_preservado=True)

def failure_unrecoverable():
 ob=fixture();cap=capturar('Cubo')['captura']
 def fn(**kw):
  bm=bmesh.from_edit_mesh(ob.data);next(iter(bm.verts)).co.x+=2
  bpy.ops.object.mode_set(mode='OBJECT')
  raise RuntimeError('Falha com contexto alterado')
 r=O.executar(fn,dict(objeto='Cubo'),cap,'extrusao')
 assert r['estado']=='INDETERMINADO' and r.get('restauracao_exata') is False,r
 assert ob.mode=='OBJECT'
 return r

def invalid_measurement():
 ob=fixture();cap=capturar('Cubo')['captura'];before=geometry()
 def fn(**kw):
  bm=bmesh.from_edit_mesh(ob.data);next(iter(bm.verts)).co.x+=2
  return dict(estado='EXTRUSAO_MEDIDA',objeto='Cubo',distancia_mm=1,erro_altura_mm=99,novos_vertices=4,normal_global=[0,0,1],nao_verificado=[])
 r=O.executar(fn,dict(objeto='Cubo',distancia_mm=1,tolerancia_plano_mm=.001),cap,'extrusao')
 assert r['estado']=='FALHA_RESTAURADA' and geometry()==before,r
 return r

run('captura_desatualizada',stale)
run('captura_arestas_reconectadas',stale_edges)
run('recuperacao_impossivel',failure_unrecoverable)
run('medida_invalida_recuperada',invalid_measurement)
run('falha_antes',lambda:failure('before'))
run('falha_depois_recuperada',lambda:failure('after'))
for op in ['extrusao','alinhamento','preenchimento','arredondamento']:run(op,lambda op=op:positive(op))
run('movimento_historico',movement);run('selecao',selection);run('exportacao',export)
if not all(r['passou'] for r in rows):raise RuntimeError('Casos falharam; veja JSON')
