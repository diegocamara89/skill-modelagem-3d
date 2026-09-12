import sys,struct,tempfile,unittest
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'produto/scripts'))
from exportacao_segura import publicar_stl
DATA=b' '*80+struct.pack('<I',1)+struct.pack('<12fH',0,0,1,0,0,0,1,0,0,0,1,0,0)
class Exportacao(unittest.TestCase):
 def test_publica_e_substitui_quando_autorizado(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'a.stl';r=publicar_stl(p,lambda t:Path(t).write_bytes(DATA))
   self.assertEqual(p.read_bytes(),DATA);self.assertEqual(r['triangulos'],1)
   p.write_bytes(b'anterior');publicar_stl(p,lambda t:Path(t).write_bytes(DATA),True)
   self.assertEqual(p.read_bytes(),DATA);self.assertEqual(list(Path(d).iterdir()),[p])
 def test_recusa_sem_chamar_exportador(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'a.stl';p.write_bytes(b'anterior')
   with self.assertRaises(FileExistsError):publicar_stl(p,lambda t:self.fail('Chamou exportador'))
   self.assertEqual(p.read_bytes(),b'anterior')
 def test_falha_e_saida_invalida_preservam_anterior(self):
  for kind in ['erro','vazio','truncado','nan']:
   with self.subTest(kind=kind),tempfile.TemporaryDirectory() as d:
    p=Path(d)/'a.stl';p.write_bytes(b'anterior')
    def writer(t):
     if kind=='erro':Path(t).write_bytes(DATA);raise RuntimeError('falha apos escrever')
     out=b'' if kind=='vazio' else DATA[:-1] if kind=='truncado' else DATA[:84]+struct.pack('<f',float('nan'))+DATA[88:]
     Path(t).write_bytes(out)
    with self.assertRaises((ValueError,RuntimeError)):publicar_stl(p,writer,True)
    self.assertEqual(p.read_bytes(),b'anterior');self.assertEqual(list(Path(d).iterdir()),[p])
 def test_destino_criado_durante_exportacao_nao_e_substituido(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'a.stl'
   def writer(t):Path(t).write_bytes(DATA);p.write_bytes(b'concorrente')
   with self.assertRaises(FileExistsError):publicar_stl(p,writer)
   self.assertEqual(p.read_bytes(),b'concorrente')
if __name__=='__main__':unittest.main()
