"""CLI pronta; captura obrigatoria para escrita. Nao repete chamadas."""
import argparse,json,sys
sys.dont_write_bytecode=True
from cliente_operacao import executar as chamar

def executar(objeto,porta,modo='conectada',angulo_graus=None,distancia_mm=None,aplicar=False,captura=None,transporte=None):
    return chamar('selecao',dict(objeto=objeto,modo=modo,angulo_graus=angulo_graus,distancia_mm=distancia_mm,aplicar=aplicar),porta,captura,transporte)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--objeto',required=True);p.add_argument('--porta',type=int,required=True)
    p.add_argument('--captura',help='Token da captura inspecionada, obrigatorio para escrita')
    p.add_argument('--modo',choices=['conectada','plano'],default='conectada');p.add_argument('--angulo-graus',type=float);p.add_argument('--distancia-mm',type=float);p.add_argument('--aplicar',action='store_true')
    r=executar(**vars(p.parse_args()));print(json.dumps(r,ensure_ascii=False))
    sys.exit(0 if r.get('estado') in ('SELECAO_APLICADA','SELECAO_PLANEJADA',) else 1)
