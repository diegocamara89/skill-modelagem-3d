import argparse,json,sys,uuid,math,re
from pathlib import Path
sys.dont_write_bytecode=True
from mcp_blender import chama

def executar(objeto,porta,distancia_mm,tolerancia_plano_mm):
    request=uuid.uuid4().hex
    root=str(Path(__file__).resolve().parent)
    args=dict(objeto=objeto,distancia_mm=distancia_mm,tolerancia_plano_mm=tolerancia_plano_mm)
    code=(f"import sys,json\nsys.dont_write_bytecode=True\nsys.path.insert(0,{root!r})\n"
          "import importlib,extrusao_regiao,operador_local\nimportlib.reload(extrusao_regiao);importlib.reload(operador_local)\n"
          f"r=operador_local.executar(extrusao_regiao.executar,{args!r})\nr['request_id']={request!r}\n"
          "print('EXTRUSAO_RESULTADO='+json.dumps(r))")
    response=chama('execute_code',{'code':code},porta=porta,permitir_escrita=True)
    if response.get('estado')!='OK':return response
    lines=[l[len('EXTRUSAO_RESULTADO='):] for l in response.get('resultado',{}).get('result','').splitlines() if l.startswith('EXTRUSAO_RESULTADO=')]
    if len(lines)!=1:return {'estado':'INDETERMINADO','motivo':'Resposta ausente/ambigua; inspecione antes de repetir.'}
    try:r=json.loads(lines[0])
    except ValueError:return {'estado':'INDETERMINADO','motivo':'JSON invalido.'}
    if not isinstance(r,dict) or r.get('request_id')!=request:return {'estado':'INDETERMINADO','motivo':'Resposta de outra chamada.'}
    if r.get('estado')=='RECUSADO':return r
    normal=r.get('normal_global');error=r.get('erro_altura_mm');count=r.get('novos_vertices')
    valid=(r.get('estado')=='EXTRUSAO_MEDIDA' and r.get('objeto')==objeto
           and r.get('distancia_mm')==distancia_mm and type(error) in (int,float)
           and math.isfinite(error) and 0<=error<=max(tolerancia_plano_mm,1e-5)
           and type(count) is int and count>0 and isinstance(normal,list) and len(normal)==3
           and all(type(x) in (int,float) and math.isfinite(x) for x in normal)
           and abs(sum(x*x for x in normal)-1)<1e-5
           and re.fullmatch('[0-9a-f]{64}',str(r.get('hash_geometria','')))
           and isinstance(r.get('nao_verificado'),list) and not r.get('falhas')
           and not r.get('motivos_de_reprovacao'))
    if not valid:return {'estado':'INDETERMINADO','motivo':'Evidencia incompleta ou invalida; inspecione antes de repetir.'}
    return r

if __name__=='__main__':
    p=argparse.ArgumentParser(description='Extrudar patch planar selecionado na normal global por mm.')
    p.add_argument('--objeto',required=True);p.add_argument('--porta',type=int,required=True)
    p.add_argument('--distancia-mm',type=float,required=True);p.add_argument('--tolerancia-plano-mm',type=float,required=True)
    r=executar(**vars(p.parse_args()));print(json.dumps(r,ensure_ascii=False));sys.exit(0 if r.get('estado')=='EXTRUSAO_MEDIDA' else 1)
