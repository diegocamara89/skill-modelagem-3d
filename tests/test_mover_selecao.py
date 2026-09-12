import sys,unittest
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'produto/scripts'))
import mover_selecao as M
class Movimento(unittest.TestCase):
 def test_captura_obrigatoria(self):
  self.assertEqual(M.executar('Cubo','mover',12345,1,transporte=lambda *a,**k:self.fail())['estado'],'RECUSADO')
 def test_timeout_nao_repete(self):
  calls=[]
  def transport(*a,**k):calls.append(a);return dict(estado='TEMPO_ESGOTADO')
  self.assertEqual(M.executar('Cubo','mover',12345,1,captura='a'*64,transporte=transport)['estado'],'TEMPO_ESGOTADO');self.assertEqual(len(calls),1)
 def test_sem_numero_finito(self):
  self.assertEqual(M.executar('Cubo','mover',12345,float('nan'),captura='a'*64,transporte=lambda *a,**k:self.fail())['estado'],'RECUSADO')
if __name__=='__main__':unittest.main()
