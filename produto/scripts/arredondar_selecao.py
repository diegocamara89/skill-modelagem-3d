import argparse,json,sys,uuid,math,re
from pathlib import Path
sys.dont_write_bytecode=True
from mcp_blender import chama

def executar(objeto,porta,raio_mm,segmentos):
 request=uuid.uuid4().hex
 args=dict(objeto=objeto,raio_mm=raio_mm,segmentos=segmentos)
 root=str(Path(__file__).resolve().parent)
 code=f"import sys,json,importlib\nsys.dont_write_bytecode=True\nsys.path.insert(0,{root!r})\nimport arredondamento_regiao,operador_local\nimportlib.reload(arredondamento_regiao);importlib.reload(operador_local)\nr=operador_local.executar(arredondamento_regiao.executar,{args!r})\nr['request_id']={request!r}\nr['parametros']={args!r}\nprint('ARREDONDAMENTO_RESULTADO='+json.dumps(r))"
 response=chama('execute_code',{'code':code},porta=porta,permitir_escrita=True)
 if response.get('estado')!='OK':return response
 try:
  lines=[l.split('=',1)[1] for l in response['resultado']['result'].splitlines() if l.startswith('ARREDONDAMENTO_RESULTADO=')]
  if len(lines)!=1:raise ValueError()
  r=json.loads(lines[0])
  if not isinstance(r,dict) or r.get('request_id')!=request or r.get('parametros')!=args:raise ValueError()
  if r.get('estado')=='RECUSADO':return r
  if not (r.get('estado')=='PERFIL_MEDIDO' and r.get('objeto')==objeto):raise ValueError()
  if not (all(type(r.get(k)) in (int,float) and math.isfinite(r[k]) and 0<=r[k]<=1e-5 for k in ['erro_raio_mm'])):raise ValueError()
  if not (type(r.get('faces_criadas')) is int and r['faces_criadas']==segmentos and r.get('raio_mm')==raio_mm and r.get('segmentos')==segmentos):raise ValueError()
  if not (re.fullmatch('[0-9a-f]{64}',str(r.get('hash_geometria','')))):raise ValueError()
  if not (isinstance(r.get('nao_verificado'),list) and not r.get('falhas') and not r.get('motivos_de_reprovacao')):raise ValueError()
  return r
 except (KeyError,ValueError,TypeError,AssertionError):return dict(estado='INDETERMINADO',motivo='Resposta invalida; inspecione antes de repetir.')

if __name__=='__main__':
 p=argparse.ArgumentParser()
 p.add_argument('--objeto',required=True);p.add_argument('--porta',type=int,required=True)
 p.add_argument('--raio-mm',type=float,required=True);p.add_argument('--segmentos',type=int,required=True)
 r=executar(**vars(p.parse_args()));print(json.dumps(r));sys.exit(0 if r.get('estado')=='PERFIL_MEDIDO' else 1)
