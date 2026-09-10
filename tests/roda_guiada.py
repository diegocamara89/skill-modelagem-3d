"""Suite reproduzivel. Relatorios ficam em destino novo; nunca usa MCP/socket."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    repo=Path(__file__).resolve().parents[1]
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pacote',type=Path,default=repo/'produto')
    ap.add_argument('--saida',type=Path,required=True)
    args=ap.parse_args();out=args.saida.resolve();out.mkdir(parents=True,exist_ok=False)
    pacote=args.pacote.resolve();env=os.environ.copy()
    env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8',PACOTE_MODELAGEM_3D=str(pacote))
    registros=[]
    def run(argv,rc_esperado=0):
        proc=subprocess.run([sys.executable,'-B',*map(str,argv)],cwd=out,env=env,
                            capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
        registros.append({'comando':subprocess.list2cmdline(proc.args),'cwd':str(out),
                          'codigo':proc.returncode,'esperado':rc_esperado,
                          'stdout':proc.stdout,'stderr':proc.stderr})
        if proc.returncode!=rc_esperado:
            raise AssertionError(f'Comando retornou {proc.returncode}, esperado {rc_esperado}')
    try:
        run([repo/'tests/test_contratos_guiados.py'])
        run([pacote/'scripts/roda_blender.py',repo/'tests/test_edicao_guiada_blender.py',
             '--resultado',out/'blender.json','--passa-resultado','--exigir','veredito_global=ATENDIDO'])
        r=json.loads((out/'blender.json').read_text(encoding='utf-8'))
        assert r['testes']==14 and not r['falhas']
        for altura in (1.0,1.5):
            cfg=out/f'cfg_{altura}.json';cfg.write_text(json.dumps({'altura':altura}),encoding='utf-8')
            result=out/f'exemplo_{altura}.json'
            run([pacote/'scripts/trabalho_blender.py','--script',pacote/'cenarios/exemplo_edicao_guiada.py',
                 '--config',cfg,'--resultado',result])
            dados=json.loads(result.read_text(encoding='utf-8'))
            assert dados['estado_execucao']=='CONCLUIDA' and dados['resultado']['estado']=='MEDIDAS_CONFORMES'
        job=out/'falha_sintetica.py';job.write_text("def executar(cfg):\n    raise RuntimeError('controle_de_erro')\n",encoding='utf-8')
        result=out/'falha.json'
        run([pacote/'scripts/trabalho_blender.py','--script',job,'--resultado',result],1)
        assert 'controle_de_erro' in json.loads(result.read_text(encoding='utf-8'))['traceback']
        # Codigo de saida favoravel nao e usado como oraculo de geometria.
        job.write_text("def executar(cfg):\n    return {'estado':'REPROVADA','falhas':['controle']}\n",encoding='utf-8')
        run([pacote/'scripts/trabalho_blender.py','--script',job,'--resultado',out/'reprovada.json'])
        assert json.loads((out/'reprovada.json').read_text(encoding='utf-8'))['resultado']['estado']=='REPROVADA'
        estado='ATENDIDO'
    except Exception as e:
        estado='FALHOU';registros.append({'erro':str(e)})
    (out/'execucoes.json').write_text(json.dumps({'estado':estado,'registros':registros},indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({'estado':estado,'comandos':len(registros),'relatorio':str(out/'execucoes.json')}))
    return 0 if estado=='ATENDIDO' else 1


if __name__=='__main__':sys.exit(main())
