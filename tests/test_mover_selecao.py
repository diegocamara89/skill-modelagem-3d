import sys,unittest
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'produto/scripts'))
import mover_selecao as m
class Contract(unittest.TestCase):
 def test_invalid_without_transport(self):
  def no(*a,**k):raise AssertionError('transport called')
  for d in (None,0,float('nan'),float('inf')):
   self.assertEqual(m.executar('A','mover',19877,d,transporte=no)['estado'],'RECUSADO')
 def test_timeout_not_retried(self):
  calls=[]
  def transport(*a,**k):calls.append(a);return {'estado':'TEMPO_ESGOTADO'}
  self.assertEqual(m.executar('A','mover',19877,1,transporte=transport)['estado'],'TEMPO_ESGOTADO');self.assertEqual(len(calls),1)
 def test_missing_evidence(self):
  self.assertEqual(m.executar('A','mover',19877,1,transporte=lambda *a,**k:{'estado':'OK','resultado':{}})['estado'],'RESULTADO_INDETERMINADO')
 def test_incomplete_result_and_code(self):
  def transport(kind,params,**kw):
   self.assertEqual(kw['porta'],19877);compile(params['code'],'generated','exec')
   return {'estado':'OK','resultado':{'result':'MODELAGEM_MOVIMENTO={"versao":"1.0.0","estado":"DESLOCAMENTO_VERIFICADO"}'}}
  self.assertEqual(m.executar('A','mover',19877,1,transporte=transport)['estado'],'RESULTADO_INDETERMINADO')
 def test_complete_result(self):
  import json
  payload=dict(versao='1.0.0',estado='DESLOCAMENTO_VERIFICADO',acao='mover',objeto='A',distancia_mm=1,eixo_global='Z',hash_geometria='a'*64,erro_alvo_mm=0,erro_vertices_protegidos_mm=0,tolerancia_mm=1e-5,vertices_movidos=4,faces_selecionadas=1,nao_verificado=['colisao'])
  def transport(*a,**k):return {'estado':'OK','resultado':{'result':'MODELAGEM_MOVIMENTO='+json.dumps(payload)}}
  self.assertEqual(m.executar('A','mover',19877,1,transporte=transport)['estado'],'DESLOCAMENTO_VERIFICADO')
if __name__=='__main__':unittest.main()
