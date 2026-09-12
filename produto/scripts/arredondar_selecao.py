"""CLI pronta; captura obrigatoria para escrita. Nao repete chamadas."""
import argparse,json,sys
sys.dont_write_bytecode=True
from cliente_operacao import executar as chamar

def executar(objeto,porta,raio_mm,segmentos,captura=None,transporte=None):
    return chamar('arredondamento',dict(objeto=objeto,raio_mm=raio_mm,segmentos=segmentos),porta,captura,transporte)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--objeto',required=True);p.add_argument('--porta',type=int,required=True)
    p.add_argument('--captura',help='Token da captura inspecionada, obrigatorio para escrita')
    p.add_argument('--raio-mm',type=float,required=True);p.add_argument('--segmentos',type=int,required=True)
    r=executar(**vars(p.parse_args()));print(json.dumps(r,ensure_ascii=False))
    sys.exit(0 if r.get('estado') in ('PERFIL_MEDIDO',) else 1)
