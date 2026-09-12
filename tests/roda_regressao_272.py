"""Regressoes sinteticas. --blender aponta executavel; --gui testa Undo em GUI isolada."""
import argparse,os,json,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--blender',required=True);p.add_argument('--saida',required=True);p.add_argument('--gui',action='store_true');a=p.parse_args()
out=Path(a.saida).resolve();out.mkdir(parents=True,exist_ok=True);rows=[]
with tempfile.TemporaryDirectory(prefix='modelagem-regressao-') as d:
 env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['MODELAGEM_TESTE_ISOLADO']='1'
 for key,name in [('BLENDER_USER_CONFIG','config'),('BLENDER_USER_SCRIPTS','scripts'),('BLENDER_USER_DATAFILES','datafiles')]:
  folder=Path(d)/name;folder.mkdir();env[key]=str(folder)
 tests=['test_exportacao_segura.py','test_cliente_operacao.py','test_mover_selecao.py','test_contratos_guiados.py']
 for name in tests:
  argv=[sys.executable,'-B',str(ROOT/'tests'/name)];r=subprocess.run(argv,cwd=ROOT,env=env,capture_output=True,text=True,timeout=90)
  rows.append(dict(argv=argv,cwd=str(ROOT),exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr))
  if r.returncode:break
 if all(row['exit_code']==0 for row in rows):
  kinds=['headless']+(['gui'] if a.gui else [])
  for kind in kinds:
   evidence=out/(kind+'.json');start=time.time()
   script='test_operacoes_272_blender.py' if kind=='headless' else 'test_undo_272_blender.py'
   argv=[a.blender]+(['--background'] if kind=='headless' else [])+['--factory-startup','--python-exit-code','1','--python',str(ROOT/'tests'/script),'--',str(evidence)]
   kw={}
   if os.name=='nt':
    si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0;kw['startupinfo']=si
   r=subprocess.run(argv,cwd=ROOT,env=env,capture_output=True,text=True,timeout=120,**kw)
   fresh=evidence.exists() and evidence.stat().st_mtime>=start-1
   data=json.loads(evidence.read_text()) if fresh else []
   passed=r.returncode==0 and len(data)==(13 if kind=='headless' else 4) and all(x['passou'] for x in data)
   rows.append(dict(argv=argv,cwd=str(ROOT),exit_code=r.returncode,passou=passed,stdout=r.stdout,stderr=r.stderr))
   if not passed:break
(out/'comandos.json').write_text(json.dumps(rows,indent=2))
print(json.dumps([{'exit_code':x['exit_code'],'passou':x.get('passou',x['exit_code']==0)} for x in rows]))
sys.exit(0 if all(x['exit_code']==0 and x.get('passou',True) for x in rows) else 1)
