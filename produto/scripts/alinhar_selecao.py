"""CLI pronta; captura obrigatoria para escrita. Nao repete chamadas."""
import argparse,json,sys
sys.dont_write_bytecode=True
from cliente_operacao import executar as chamar

def executar(objeto,porta,ponto_mm,normal,maximo_mm,captura=None,transporte=None):
    return chamar('alinhamento',dict(objeto=objeto,ponto_mm=ponto_mm,normal=normal,maximo_mm=maximo_mm),porta,captura,transporte)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--objeto',required=True);p.add_argument('--porta',type=int,required=True)
    p.add_argument('--captura',help='Token da captura inspecionada, obrigatorio para escrita')
    p.add_argument('--ponto-mm',type=float,nargs=3,required=True);p.add_argument('--normal',type=float,nargs=3,required=True);p.add_argument('--maximo-mm',type=float,required=True)
    r=executar(**vars(p.parse_args()));print(json.dumps(r,ensure_ascii=False))
    sys.exit(0 if r.get('estado') in ('ALINHAMENTO_MEDIDO',) else 1)
