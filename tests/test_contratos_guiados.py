"""Contratos do hospedeiro, sem socket ou Blender aberto."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.dont_write_bytecode=True
S=Path(os.environ.get('PACOTE_MODELAGEM_3D') or Path(__file__).resolve().parents[1]/'produto')/'scripts';sys.path.insert(0,str(S))
import sessao_blender as sessao
import executa_com_relatorio as runner


class Contratos(unittest.TestCase):
    def test_transporte_fixo_somente_consulta(self):
        def fake(tipo,params,**kw):
            self.assertEqual(tipo,'execute_code')
            self.assertIn('mod.diagnostica()',params['code'])
            self.assertNotIn('mode_set',params['code'])
            return {'estado':'OK','resposta':{'result':{'result':sessao.MARCA+json.dumps({'versao':'1.0.0','estado':'SELECAO_VAZIA'})}}}
        self.assertEqual(sessao.diagnosticar(fake)['diagnostico']['estado'],'SELECAO_VAZIA')

    def test_resposta_sem_diagnostico_nao_passa(self):
        self.assertEqual(sessao.diagnosticar(lambda *a,**k:{'estado':'OK','result':'feito'})['estado'],'DIAGNOSTICO_AUSENTE')

    def test_timeout_nao_reexecuta(self):
        calls=[]
        def fake(*a,**kw):calls.append(1);return {'estado':'TEMPO_ESGOTADO'}
        self.assertEqual(sessao.diagnosticar(fake)['estado'],'TEMPO_ESGOTADO')
        self.assertEqual(len(calls),1)

    def executar(self,texto,config=None):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'job.py').write_text(texto,encoding='utf-8')
            args=['--script',str(p/'job.py'),'--resultado-em',str(p/'out.json')]
            if config is not None:
                (p/'cfg.json').write_text(config,encoding='utf-8');args+=['--config',str(p/'cfg.json')]
            rc=runner.main(args)
            return rc,json.loads((p/'out.json').read_text(encoding='utf-8'))

    def test_execucao_nao_promove_reprovacao(self):
        rc,r=self.executar("def executar(cfg): return {'estado':'REPROVADA','falhas':['forma']}\n")
        self.assertEqual(rc,0);self.assertEqual(r['resultado']['estado'],'REPROVADA')
        self.assertNotIn('veredito_global',r)

    def test_excecao_tem_traceback(self):
        rc,r=self.executar("def executar(cfg): raise ValueError('controle_sintetico')\n")
        self.assertEqual(rc,1);self.assertIn('controle_sintetico',r['traceback'])

    def test_erro_de_sintaxe_capturado(self):
        rc,r=self.executar('def executar(:')
        self.assertEqual(rc,1);self.assertEqual(r['tipo'],'SyntaxError')

    def test_config_invalida_capturada(self):
        rc,r=self.executar('def executar(cfg): return {}','{')
        self.assertEqual(rc,1);self.assertEqual(r['tipo'],'JSONDecodeError')

    def test_none_nao_e_resultado(self):
        rc,r=self.executar('def executar(cfg): pass')
        self.assertEqual(rc,1)

    def test_colisao_preserva_script(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'job.py';p.write_text('original')
            with self.assertRaises(SystemExit):runner.main(['--script',str(p),'--resultado-em',str(p)])
            self.assertEqual(p.read_text(),'original')


if __name__=='__main__':unittest.main()
