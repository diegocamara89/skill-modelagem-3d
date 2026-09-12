"""CLI pronta; captura obrigatoria para escrita. Nao repete chamadas."""
import argparse,json,sys
sys.dont_write_bytecode=True
from cliente_operacao import executar as chamar

def executar(objeto,porta,distancia_mm,tolerancia_plano_mm,captura=None,transporte=None):
    return chamar('extrusao',dict(objeto=objeto,distancia_mm=distancia_mm,tolerancia_plano_mm=tolerancia_plano_mm),porta,captura,transporte)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--objeto',required=True);p.add_argument('--porta',type=int,required=True)
    p.add_argument('--captura',help='Token da captura inspecionada, obrigatorio para escrita')
    p.add_argument('--distancia-mm',type=float,required=True);p.add_argument('--tolerancia-plano-mm',type=float,required=True)
    r=executar(**vars(p.parse_args()));print(json.dumps(r,ensure_ascii=False))
    sys.exit(0 if r.get('estado') in ('EXTRUSAO_MEDIDA',) else 1)
