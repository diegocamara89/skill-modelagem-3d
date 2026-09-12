"""Transporte e envelope comuns das operacoes prontas; nunca repete uma chamada."""
import hashlib,json,math,re,uuid
from pathlib import Path
from mcp_blender import chama

MARCA='MODELAGEM_RESULTADO='
FALHAS={'RECUSADO','FALHA_SEM_ALTERACAO_LIQUIDA','FALHA_RESTAURADA','FALHA_COM_ALTERACAO','INDETERMINADO','ERRO_VERIFICACAO'}
ESTADOS={'capturar':'CAPTURA_DISPONIVEL','extrusao':'EXTRUSAO_MEDIDA','alinhamento':'ALINHAMENTO_MEDIDO','preenchimento':'SUPERFICIE_CRIADA','arredondamento':'PERFIL_MEDIDO'}
MODULOS={'extrusao':'extrusao_regiao','alinhamento':'alinhamento_regiao','preenchimento':'preenchimento_regiao','arredondamento':'arredondamento_regiao','selecao':'selecao_regiao','movimento':'mover_regiao'}

def hash_valido(value):return isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value) is not None

def numero(x):return type(x) in (int,float) and math.isfinite(x)

def natural(x,minimo=0):return type(x) is int and x>=minimo

def valida_resultado(r,op,p):
    if not isinstance(r,dict) or r.get('objeto')!=p['objeto']:return False
    state=r.get('estado')
    if state in FALHAS:
        if state in ('FALHA_RESTAURADA','FALHA_SEM_ALTERACAO_LIQUIDA'):return r.get('restauracao_exata') is True
        return isinstance(r.get('motivo'),str) or state=='ERRO_VERIFICACAO'
    if r.get('falhas') or r.get('motivos_de_reprovacao'):return False
    if op=='capturar':
        return state==ESTADOS[op] and hash_valido(r.get('captura')) and natural(r.get('pid'),1) and natural(r.get('faces_selecionadas')) and natural(r.get('arestas_selecionadas'))
    if op=='selecao':
        faces=r.get('faces');seed=r.get('semente')
        return (state==('SELECAO_APLICADA' if p.get('aplicar') else 'SELECAO_PLANEJADA') and r.get('modo')==p['modo'] and isinstance(faces,list) and bool(faces) and all(natural(i) for i in faces) and len(set(faces))==len(faces) and natural(seed) and seed in faces and hash_valido(r.get('captura')) and (not p.get('aplicar') or hash_valido(r.get('captura_depois'))) and isinstance(r.get('nao_verificado'),list))
    if op=='movimento':
        expected={'mover':'DESLOCAMENTO_VERIFICADO','inspecionar':'INSPECIONADO','desfazer':'HISTORICO_EXECUTADO','refazer':'HISTORICO_EXECUTADO'}[p['acao']]
        if state!=expected or r.get('acao')!=p['acao'] or not hash_valido(r.get('hash_geometria')):return False
        if p['acao']=='inspecionar':return natural(r.get('faces_selecionadas')) and natural(r.get('historico_posicao')) and natural(r.get('historico_total')) and r['historico_posicao']<=r['historico_total'] and hash_valido(r.get('captura'))
        if not hash_valido(r.get('captura_depois')):return False
        if p['acao'] in ('desfazer','refazer'):return r.get('restauracao_exata') is True
        tol=r.get('tolerancia_mm')
        return (numero(tol) and 0<tol<=max(1e-5,abs(p['distancia_mm'])*1e-5) and r.get('distancia_mm')==p['distancia_mm'] and r.get('eixo_global')==p['eixo'] and all(numero(r.get(k)) and 0<=r[k]<=tol for k in ['erro_alvo_mm','erro_vertices_protegidos_mm']) and natural(r.get('vertices_movidos'),1) and natural(r.get('faces_selecionadas'),1) and isinstance(r.get('nao_verificado'),list))
    if state!=ESTADOS.get(op) or not hash_valido(r.get('hash_geometria')) or not hash_valido(r.get('captura_depois')) or not isinstance(r.get('nao_verificado'),list):return False
    if op=='extrusao':
        n=r.get('normal_global');e=r.get('erro_altura_mm')
        return (r.get('distancia_mm')==p['distancia_mm'] and numero(e) and 0<=e<=max(p['tolerancia_plano_mm'],1e-5) and natural(r.get('novos_vertices'),1) and isinstance(n,list) and len(n)==3 and all(numero(x) for x in n) and abs(sum(x*x for x in n)-1)<1e-5)
    if op=='alinhamento':return natural(r.get('vertices'),1) and all(numero(r.get(k)) and 0<=r[k]<=1e-5 for k in ['residuo_mm','erro_protegidos_mm'])
    if op=='preenchimento':return r.get('modo')==p['modo'] and type(r.get('faces_criadas')) is int and r['faces_criadas']==1 and natural(r.get('vertices_preservados'),3)
    if op=='arredondamento':return r.get('raio_mm')==p['raio_mm'] and type(r.get('faces_criadas')) is int and r['faces_criadas']==p['segmentos'] and r.get('segmentos')==p['segmentos'] and numero(r.get('erro_raio_mm')) and 0<=r['erro_raio_mm']<=1e-5
    return False

def interpretar(response,request,op,params):
    bad=dict(estado='INDETERMINADO',motivo='Resposta invalida ou contraditoria; inspecione antes de repetir.')
    if not isinstance(response,dict):return bad
    if response.get('estado')!='OK':return response if response.get('estado') in ('ESCRITA_BARRADA','SEM_SERVIDOR','TEMPO_ESGOTADO','RESPOSTA_ILEGIVEL','ERRO_DO_ADDON') else bad
    data=response.get('resultado')
    if not isinstance(data,dict) or not isinstance(data.get('result'),str):return bad
    lines=[l[len(MARCA):] for l in data['result'].splitlines() if l.startswith(MARCA)]
    if len(lines)!=1:return bad
    try:
        envelope=json.loads(lines[0])
        if not isinstance(envelope,dict) or envelope.get('request_id')!=request or envelope.get('operacao')!=op or envelope.get('parametros')!=params:return bad
        result=envelope.get('resultado')
        if not valida_resultado(result,op,params):return bad
        return result
    except (ValueError,TypeError,KeyError,OverflowError):return bad

def executar(op,params,porta,captura=None,transporte=None):
    if type(porta) is not int or not 1<=porta<=65535:return dict(estado='RECUSADO',motivo='Porta explicita invalida.')
    if not isinstance(params,dict) or not isinstance(params.get('objeto'),str) or not params['objeto']:return dict(estado='RECUSADO',motivo='Nome do objeto obrigatorio.')
    if op not in set(MODULOS)|{'capturar'}:return dict(estado='RECUSADO',motivo='Operacao desconhecida.')
    if op=='movimento' and params.get('acao') not in ('mover','desfazer','refazer','inspecionar'):return dict(estado='RECUSADO',motivo='Acao desconhecida.')
    read=op=='capturar' or (op=='selecao' and not params.get('aplicar')) or (op=='movimento' and params['acao']=='inspecionar')
    if not read and not hash_valido(captura):return dict(estado='RECUSADO',motivo='Capture a selecao e forneca --captura antes da escrita.')
    try:serialized=json.dumps(params,allow_nan=False)
    except (ValueError,TypeError):return dict(estado='RECUSADO',motivo='Parametros devem ser JSON finito.')
    root=Path(__file__).resolve().parent;request=uuid.uuid4().hex
    # Fixed module allowlist, exact package paths. Helpers have no persistent history.
    code="import importlib.util,sys,json\nsys.dont_write_bytecode=True\n"
    code+=f"root={str(root)!r}\n"
    code+="def load(name):\n spec=importlib.util.spec_from_file_location(name,root+'/'+name+'.py')\n mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod\n"
    code+="load('mover_regiao');capture=load('captura_estado')\n"
    code+=f"p=json.loads({serialized!r})\n"
    code+="try:\n"
    if op=='capturar':code+=" r=capture.capturar(p['objeto'])\n"
    elif op=='selecao':
        code+=f" m=load('selecao_regiao');r=m.executar(**p,captura={captura!r})\n"
    elif op=='movimento':
        digest=hashlib.sha256((root/'mover_regiao.py').read_bytes()).hexdigest()
        code+=f" m=sys.modules.get('_modelagem_mover_pronto')\n if m is not None and getattr(m,'_source_hash',None)!={digest!r}:raise ValueError('Runtime mudou; conclua historico antigo antes de recarregar.')\n if m is None:\n  m=load('mover_regiao');m._source_hash={digest!r};sys.modules['_modelagem_mover_pronto']=m\n"
        if not read:code+=f" capture.conferir(p['objeto'],{captura!r})\n"
        code+=" r=m.executar(**p)\n if r.get('estado') in ('DESLOCAMENTO_VERIFICADO','HISTORICO_EXECUTADO','INSPECIONADO'):\n  r['captura' if p['acao']=='inspecionar' else 'captura_depois']=capture.capturar(p['objeto'])['captura']\n"
    else:code+=f" load('mcp_blender');load('cliente_operacao');m=load({MODULOS[op]!r});wrapper=load('operador_local');r=wrapper.executar(m.executar,p,{captura!r},{op!r})\n"
    code+="except Exception as exc:\n r=dict(estado='INDETERMINADO',objeto=p['objeto'],motivo=str(exc))\n"
    code+=f"print({MARCA!r}+json.dumps(dict(request_id={request!r},operacao={op!r},parametros=p,resultado=r)))\n"
    response=(transporte or chama)('execute_code',{'code':code},porta=porta,permitir_escrita=True)
    return interpretar(response,request,op,params)
