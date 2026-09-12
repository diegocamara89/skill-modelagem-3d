"""CLI pronta de expansao de selecao. Transporte existente; sem retry."""
import argparse,json,sys,uuid
from pathlib import Path
sys.dont_write_bytecode=True
from mcp_blender import chama

def executar(objeto,porta,modo='conectada',angulo_graus=None,distancia_mm=None,aplicar=False):
    request=uuid.uuid4().hex
    path=str(Path(__file__).with_name('selecao_regiao.py').resolve())
    args=dict(objeto=objeto,modo=modo,angulo_graus=angulo_graus,distancia_mm=distancia_mm,aplicar=aplicar)
    code=("import importlib.util,json,sys\nsys.dont_write_bytecode=True\n"
          f"spec=importlib.util.spec_from_file_location('selecao_regiao',{path!r})\n"
          "m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)\n"
          f"r=m.executar(**{args!r})\nr['request_id']={request!r}\n"
          "print('REGIAO_RESULTADO='+json.dumps(r))")
    response=chama('execute_code',{'code':code},porta=porta,permitir_escrita=True)
    if response.get('estado')!='OK':return response
    raw=(response.get('resultado') or {}).get('result','')
    lines=[l[len('REGIAO_RESULTADO='):] for l in raw.splitlines() if l.startswith('REGIAO_RESULTADO=')]
    if len(lines)!=1:return {'estado':'INDETERMINADO','motivo':'Resposta ausente ou ambigua; inspecione antes de repetir.'}
    try:r=json.loads(lines[0])
    except ValueError:return {'estado':'INDETERMINADO','motivo':'Resposta ilegivel.'}
    state='SELECAO_APLICADA' if aplicar else 'SELECAO_PLANEJADA'
    faces=r.get('faces')
    if not (r.get('estado')==state and r.get('objeto')==objeto and r.get('modo')==modo and r.get('request_id')==request and isinstance(faces,list) and faces and all(type(f) is int and f>=0 for f in faces) and len(set(faces))==len(faces)):
        return {'estado':'INDETERMINADO','motivo':'Contrato de resposta invalido.'}
    return r

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--objeto',required=True);p.add_argument('--porta',required=True,type=int)
    p.add_argument('--modo',choices=['conectada','plano'],default='conectada')
    p.add_argument('--angulo-graus',type=float);p.add_argument('--distancia-mm',type=float)
    p.add_argument('--aplicar',action='store_true')
    r=executar(**vars(p.parse_args()));print(json.dumps(r,ensure_ascii=False))
    sys.exit(0 if r.get('estado') in ('SELECAO_APLICADA','SELECAO_PLANEJADA') else 1)
