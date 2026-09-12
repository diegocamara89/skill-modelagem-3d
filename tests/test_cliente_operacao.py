import sys,json,unittest,copy,ast
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'produto/scripts'))
import cliente_operacao as C
TOKEN='a'*64
P=dict(objeto='Cubo',modo='conectada',angulo_graus=None,distancia_mm=None,aplicar=True)
GOOD=dict(estado='SELECAO_APLICADA',objeto='Cubo',modo='conectada',semente=0,faces=[0,1],captura=TOKEN,captura_depois=TOKEN,nao_verificado=[])
def envelope(result,request='request',op='selecao',params=P):return dict(estado='OK',resultado=dict(result=C.MARCA+json.dumps(dict(request_id=request,operacao=op,parametros=params,resultado=result))))
class Contrato(unittest.TestCase):
 def test_validos(self):
  self.assertEqual(C.interpretar(envelope(GOOD),'request','selecao',P)['estado'],'SELECAO_APLICADA')
  for state in ['FALHA_RESTAURADA','FALHA_SEM_ALTERACAO_LIQUIDA']:
   r=dict(estado=state,objeto='Cubo',restauracao_exata=True)
   self.assertEqual(C.interpretar(envelope(r),'request','selecao',P)['estado'],state)
 def test_contradicoes(self):
  for key,value in [('falhas',['erro']),('motivos_de_reprovacao',['erro']),('faces',[]),('faces',[0,0]),('faces',[True]),('semente',5),('captura',None),('captura_depois',None),('nao_verificado',None),('objeto','Outro')]:
   with self.subTest(key=key,value=value):
    r=copy.deepcopy(GOOD);r[key]=value
    self.assertEqual(C.interpretar(envelope(r),'request','selecao',P)['estado'],'INDETERMINADO')
 def test_formatos_malformados(self):
  bad=[dict(estado='SELECAO_APLICADA'),dict(estado='FALHA_RESTAURADA'),dict(estado='DESCONHECIDO'),None,[],{},dict(estado='OK',resultado=None),dict(estado='OK',resultado=[]),dict(estado='OK',resultado=dict(result=[]))]
  for raw in ['[]','null','1','{','{}',json.dumps(GOOD)]:bad.append(dict(estado='OK',resultado=dict(result=C.MARCA+raw)))
  for value in bad:
   with self.subTest(value=value):self.assertEqual(C.interpretar(value,'request','selecao',P)['estado'],'INDETERMINADO')
 def test_identidade_envelope(self):
  for r in [envelope(GOOD,request='velha'),envelope(GOOD,op='extrusao'),envelope(GOOD,params={}),envelope(dict(estado='FALHA_RESTAURADA',objeto='Cubo',restauracao_exata=False))]:
   self.assertEqual(C.interpretar(r,'request','selecao',P)['estado'],'INDETERMINADO')
 def test_sem_token_nao_transporta(self):
  self.assertEqual(C.executar('selecao',P,12345,transporte=lambda *a,**k:self.fail())['estado'],'RECUSADO')
 def test_timeout_uma_chamada_e_codigo_compila(self):
  calls=[]
  def transport(*a,**k):compile(a[1]['code'],'remote','exec');calls.append(a);return dict(estado='TEMPO_ESGOTADO')
  self.assertEqual(C.executar('selecao',P,12345,TOKEN,transport)['estado'],'TEMPO_ESGOTADO');self.assertEqual(len(calls),1)
 def test_todos_codigos_compilam(self):
  cases=[('capturar',dict(objeto='Cubo')),('extrusao',dict(objeto='Cubo',distancia_mm=1,tolerancia_plano_mm=.001)),('alinhamento',dict(objeto='Cubo',ponto_mm=[0,0,1],normal=[0,0,1],maximo_mm=2)),('preenchimento',dict(objeto='Cubo',modo='ponte',tolerancia_mm=.001)),('arredondamento',dict(objeto='Cubo',raio_mm=1,segmentos=8))]+[('movimento',dict(objeto='Cubo',acao=a,distancia_mm=1,eixo='Z')) for a in ['mover','inspecionar','desfazer','refazer']]
  for op,p in cases:
   def transport(*a,**k):compile(a[1]['code'],'remote','exec');return dict(estado='TEMPO_ESGOTADO')
   self.assertEqual(C.executar(op,p,12345,TOKEN,transport)['estado'],'TEMPO_ESGOTADO')
if __name__=='__main__':unittest.main()
