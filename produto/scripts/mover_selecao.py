"""Chamada parametrizada da operacao pronta. Requer porta explicita; sem tentativas automaticas."""
import argparse
import json
import math
import hashlib
from pathlib import Path
import sys

sys.dont_write_bytecode = True
from mcp_blender import chama

MARCA = 'MODELAGEM_MOVIMENTO='


def executar(objeto, acao, porta, distancia_mm=None, eixo='Z', transporte=chama):
    if not isinstance(porta, int) or not 1 <= porta <= 65535:
        return dict(estado='RECUSADO', motivo='Porta explicita valida obrigatoria.')
    if not objeto or acao not in ('mover', 'desfazer', 'refazer', 'inspecionar'):
        return dict(estado='RECUSADO', motivo='Objeto e acao validos sao obrigatorios.')
    if acao == 'mover' and (distancia_mm is None or not math.isfinite(distancia_mm) or distancia_mm == 0 or eixo not in 'XYZ' or len(eixo) != 1):
        return dict(estado='RECUSADO', motivo='Informe distancia finita nao zero e eixo X/Y/Z.')
    runtime = str(Path(__file__).resolve().with_name('mover_regiao.py'))
    digest = hashlib.sha256(Path(runtime).read_bytes()).hexdigest()
    params = dict(acao=acao, objeto=objeto, distancia_mm=distancia_mm, eixo=eixo)
    codigo = ("import importlib.util, json, sys\n"
              "sys.dont_write_bytecode = True\n"
              "mod = sys.modules.get('_modelagem_mover_pronto')\n"
              f"if mod is not None and getattr(mod, '_source_hash', None) != {digest!r}:\n"
              "    raise RuntimeError('Ferramenta atualizada no disco. Reinicie a sessao de teste ou conclua o historico antigo antes de recarregar. Nenhuma edicao executada.')\n"
              "if mod is None:\n"
              f"    spec = importlib.util.spec_from_file_location('_modelagem_mover_pronto', {runtime!r})\n"
              "    mod = importlib.util.module_from_spec(spec)\n    spec.loader.exec_module(mod)\n"
              f"    mod._source_hash = {digest!r}\n"
              "    sys.modules['_modelagem_mover_pronto'] = mod\n"
              f"print({MARCA!r} + json.dumps(mod.executar(**{params!r})))\n")
    response = transporte('execute_code', {'code': codigo}, porta=porta, permitir_escrita=True)
    if response.get('estado') != 'OK':
        return response
    def strings(value):
        if isinstance(value, str):
            yield value
        elif isinstance(value, dict):
            for child in value.values(): yield from strings(child)
        elif isinstance(value, list):
            for child in value: yield from strings(child)
    results = []
    for value in strings(response.get('resultado')):
        for line in value.splitlines():
            if line.startswith(MARCA):
                try: results.append(json.loads(line[len(MARCA):]))
                except ValueError: pass
    if len(results) != 1 or not isinstance(results[0], dict) or results[0].get('versao') != '1.0.0':
        return dict(estado='RESULTADO_INDETERMINADO', motivo='Resposta sem relatorio unico compativel. Inspecione antes de repetir.')
    report = results[0]
    state = report.get('estado')
    successes = {'mover': 'DESLOCAMENTO_VERIFICADO', 'inspecionar': 'INSPECIONADO',
                 'desfazer': 'HISTORICO_EXECUTADO', 'refazer': 'HISTORICO_EXECUTADO'}
    if state not in set(successes.values()) | {'RECUSADO', 'ERRO_VERIFICACAO'}:
        return dict(estado='RESULTADO_INDETERMINADO', motivo='Estado ausente ou desconhecido; inspecione antes de repetir.')
    if state in successes.values():
        valid = state == successes[acao] and report.get('acao') == acao and report.get('objeto') == objeto
        digest = report.get('hash_geometria', '')
        valid = valid and isinstance(digest, str) and len(digest) == 64 and all(c in '0123456789abcdef' for c in digest)
        valid = valid and not report.get('falhas') and not report.get('motivos_de_reprovacao')
        def finite(value):
            return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
        if acao == 'mover':
            tol = report.get('tolerancia_mm')
            valid = valid and finite(tol) and tol > 0 and tol <= max(1e-5, abs(distancia_mm)*1e-5)
            valid = valid and report.get('distancia_mm') == distancia_mm and report.get('eixo_global') == eixo
            for key in ('erro_alvo_mm', 'erro_vertices_protegidos_mm'):
                value = report.get(key)
                valid = valid and finite(value) and value >= 0 and value <= tol
            for key in ('vertices_movidos', 'faces_selecionadas'):
                value = report.get(key)
                valid = valid and type(value) is int and value > 0
            valid = valid and isinstance(report.get('nao_verificado'), list)
        elif acao in ('desfazer', 'refazer'):
            valid = valid and report.get('restauracao_exata') is True
        else:
            for key in ('faces_selecionadas','historico_posicao','historico_total'):
                value = report.get(key)
                valid = valid and type(value) is int and value >= 0
            valid = valid and report.get('historico_posicao', 0) <= report.get('historico_total', -1)
        if not valid:
            return dict(estado='RESULTADO_INDETERMINADO', motivo='Relatorio incompleto, contraditorio ou de outra operacao. Inspecione antes de repetir.', relatorio_recebido=report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--objeto', required=True)
    parser.add_argument('--acao', choices=['mover', 'desfazer', 'refazer', 'inspecionar'], required=True)
    parser.add_argument('--porta', type=int, required=True)
    parser.add_argument('--distancia-mm', type=float)
    parser.add_argument('--eixo', choices=['X', 'Y', 'Z'], default='Z', help='Eixo GLOBAL')
    args = parser.parse_args()
    result = executar(**vars(args))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get('estado') in ('DESLOCAMENTO_VERIFICADO', 'HISTORICO_EXECUTADO', 'INSPECIONADO') else 1


if __name__ == '__main__':
    sys.exit(main())
