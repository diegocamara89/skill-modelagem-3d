import argparse,json,sys,uuid,math,re
from pathlib import Path
sys.dont_write_bytecode=True
from mcp_blender import chama

def executar(objeto,porta,ponto_mm,normal,maximo_mm):
 request=uuid.uuid4().hex
 args=dict(objeto=objeto,ponto_mm=ponto_mm,normal=normal,maximo_mm=maximo_mm)
 root=str(Path(__file__).resolve().parent)
 code=f"import sys,json,importlib\nsys.dont_write_bytecode=True\nsys.path.insert(0,{root!r})\nimport alinhamento_regiao,operador_local\nimportlib.reload(alinhamento_regiao);importlib.reload(operador_local)\nr=operador_local.executar(alinhamento_regiao.executar,{args!r})\nr['request_id']={request!r}\nr['parametros']={args!r}\nprint('ALINHAMENTO_RESULTADO='+json.dumps(r))"
 response=chama('execute_code',{'code':code},porta=porta,permitir_escrita=True)
 if response.get('estado')!='OK':return response
 try:
  lines=[l.split('=',1)[1] for l in response['resultado']['result'].splitlines() if l.startswith('ALINHAMENTO_RESULTADO=')]
  if len(lines)!=1:raise ValueError()
  r=json.loads(lines[0])
  if not isinstance(r,dict) or r.get('request_id')!=request or r.get('parametros')!=args:raise ValueError()
  if r.get('estado')=='RECUSADO':return r
  if not (r.get('estado')=='ALINHAMENTO_MEDIDO' and r.get('objeto')==objeto):raise ValueError()
  if not (all(type(r.get(k)) in (int,float) and math.isfinite(r[k]) and 0<=r[k]<=1e-5 for k in ['residuo_mm','erro_protegidos_mm'])):raise ValueError()
  if not (type(r.get('vertices')) is int and r['vertices']>0):raise ValueError()
  if not (re.fullmatch('[0-9a-f]{64}',str(r.get('hash_geometria','')))):raise ValueError()
  if not (isinstance(r.get('nao_verificado'),list) and not r.get('falhas') and not r.get('motivos_de_reprovacao')):raise ValueError()
  return r
 except (KeyError,ValueError,TypeError,AssertionError):return dict(estado='INDETERMINADO',motivo='Resposta invalida; inspecione antes de repetir.')

if __name__=='__main__':
 p=argparse.ArgumentParser()
 p.add_argument('--objeto',required=True);p.add_argument('--porta',type=int,required=True)
 p.add_argument('--ponto-mm',type=float,nargs=3,required=True);p.add_argument('--normal',type=float,nargs=3,required=True);p.add_argument('--maximo-mm',type=float,required=True)
 r=executar(**vars(p.parse_args()));print(json.dumps(r));sys.exit(0 if r.get('estado')=='ALINHAMENTO_MEDIDO' else 1)
