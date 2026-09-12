"""CLI pronta; captura obrigatoria para escrita. Nao repete chamadas."""
import argparse,json,sys
sys.dont_write_bytecode=True
from cliente_operacao import executar as chamar

def executar(objeto,acao,porta,distancia_mm=None,eixo='Z',captura=None,transporte=None):
    return chamar('movimento',dict(objeto=objeto,acao=acao,distancia_mm=distancia_mm,eixo=eixo),porta,captura,transporte)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--objeto',required=True);p.add_argument('--porta',type=int,required=True)
    p.add_argument('--captura',help='Token da captura inspecionada, obrigatorio para escrita')
    p.add_argument('--acao',choices=['mover','desfazer','refazer','inspecionar'],required=True);p.add_argument('--distancia-mm',type=float);p.add_argument('--eixo',choices=['X','Y','Z'],default='Z')
    r=executar(**vars(p.parse_args()));print(json.dumps(r,ensure_ascii=False))
    sys.exit(0 if r.get('estado') in ('DESLOCAMENTO_VERIFICADO','HISTORICO_EXECUTADO','INSPECIONADO',) else 1)
