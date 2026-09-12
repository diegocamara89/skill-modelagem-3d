"""Captura identidade sem modificar geometria, selecao ou modo."""
import argparse,json,sys
sys.dont_write_bytecode=True
from cliente_operacao import executar
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--objeto',required=True);p.add_argument('--porta',type=int,required=True)
 a=p.parse_args();r=executar('capturar',dict(objeto=a.objeto),a.porta);print(json.dumps(r))
 sys.exit(0 if r.get('estado')=='CAPTURA_DISPONIVEL' else 1)
