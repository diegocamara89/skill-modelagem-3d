"""Abre o FreeCAD com a bancada de marcas (letras A, B, C… + notas) num projeto.

  python abrir_bancada_freecad.py <projeto> [--documento Peca.FCStd] [--importar a.stl b.step ...]
  python abrir_bancada_freecad.py <pasta vazia> --testar      # ensaio automático; fecha sozinho

- <projeto>: pasta do projeto. Ali ficam marcas.json (o que o agente lê), a macro e config/ isolada.
- --documento: .FCStd a abrir (padrão: <nome da pasta, espaços viram _>.FCStd dentro do projeto). Se não existir,
  é criado a partir de --importar (STL/3MF/OBJ entram como malha; STEP/IGES/BREP como sólido).
- Reaproveita o FreeCAD já aberto (--single-instance): uma janela só. O ensaio abre outra, à parte.
Não usa mouse/teclado do sistema. Caminho do FreeCAD: variável FREECAD_EXE ou a instalação portátil.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

FREECAD = Path(os.environ.get('FREECAD_EXE', 'D:/Diego/Pessoal/3D/Ferramentas/FreeCAD/FreeCAD_1.1.4-Windows-x86_64-py311/bin/freecad.exe'))
PACOTE = Path(__file__).resolve().parent.parent / 'freecad'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('projeto', type=Path)
    ap.add_argument('--documento', type=Path)
    ap.add_argument('--importar', nargs='*', type=Path, default=[])
    ap.add_argument('--testar', action='store_true')
    ap.add_argument('--verificar-marcacao', action='store_true', help='testa clique e desenho nos grupos Montado e Desmontado')
    ap.add_argument('--nova-janela', action='store_true', help='não reaproveita o FreeCAD já aberto')
    a = ap.parse_args()
    if not FREECAD.exists():
        sys.exit(f'FreeCAD não encontrado em {FREECAD}. Defina FREECAD_EXE.')
    projeto = a.projeto.resolve()
    projeto.mkdir(parents=True, exist_ok=True)
    doc = a.documento or Path(projeto.name.replace(' ', '_') + '.FCStd')
    doc = doc if doc.is_absolute() else projeto / doc
    importar = [str(p.resolve()) for p in a.importar]
    faltam = [p for p in importar if not Path(p).exists()]
    if faltam:
        sys.exit(f'Arquivo para importar não existe: {faltam}')
    if not doc.exists() and not importar and not a.testar:
        sys.exit(f'{doc} não existe. Informe --documento ou --importar.')
    if a.testar and doc.exists():
        sys.exit(f'--testar recusado: {doc} já existe e seria sobrescrito. Use uma pasta vazia.')
    if doc.exists() and importar:
        print(f'AVISO: {doc.name} já existe; --importar foi ignorado e o documento existente será aberto.')

    linhas = ['import sys', f'sys.path.insert(0, {str(PACOTE)!r})', 'import bancada_freecad']
    if a.testar:
        resultado = projeto / 'bancada_teste.json'
        resultado.unlink(missing_ok=True)
        linhas += ['import testar_bancada, FreeCAD, FreeCADGui', 'from PySide import QtCore',
                   f'testar_bancada.criar_documento({str(doc)!r})',
                   f'r = bancada_freecad.iniciar({str(projeto)!r}, {str(doc)!r})',
                   'def _ensaio():',
                   '    testar_bancada.executar(r)',
                   '    QtCore.QTimer.singleShot(500, lambda: (r.fechar(), FreeCAD.closeDocument(r.doc_name), FreeCADGui.getMainWindow().close()))',  # fecha o doc antes: sem pergunta de salvar
                   'QtCore.QTimer.singleShot(3000, _ensaio)']
    else:
        if a.verificar_marcacao:
            linhas += ['import importlib', 'importlib.reload(bancada_freecad)']
        linhas.append(f'bancada_freecad.iniciar({str(projeto)!r}, {str(doc)!r}, {importar!r})')
        if a.verificar_marcacao:
            resultado = projeto / 'bancada_projecao.json'
            resultado.unlink(missing_ok=True)
            linhas += ['from PySide import QtCore', 'import testar_bancada, FreeCAD, traceback, importlib',
                       'importlib.reload(testar_bancada)',
                       'def _projecao():',
                       '    r = FreeCAD.BancadaMarcas',
                       '    try:',
                       "        casos = testar_bancada.verificar_projecao(r)",
                       "        r.gravar('bancada_projecao.json', {'resultado':'PASSOU','casos':casos})",
                       '    except Exception:',
                       "        r.gravar('bancada_projecao.json', {'resultado':'FALHOU','erro':traceback.format_exc()})",
                       'QtCore.QTimer.singleShot(1800, _projecao)']
    macro = projeto / 'Abrir_bancada.FCMacro'
    macro.write_text('\n'.join(linhas) + '\n', encoding='utf-8')
    (projeto / 'config').mkdir(exist_ok=True)
    cmd = [str(FREECAD), '--user-cfg', str(projeto / 'config' / 'user.cfg'), '--system-cfg', str(projeto / 'config' / 'system.cfg'), str(macro)]
    if not a.testar and not a.nova_janela:
        cmd.insert(1, '--single-instance')
    pronto = projeto / 'bancada_pronto.json'
    pronto.unlink(missing_ok=True)
    subprocess.Popen(cmd, creationflags=getattr(subprocess, 'DETACHED_PROCESS', 0))

    alvo = resultado if a.testar or a.verificar_marcacao else pronto
    erro = projeto / 'bancada_erro.log'
    inicio = time.time()
    while time.time() - inicio < 120:
        if alvo.exists():
            try:
                dados = json.loads(alvo.read_text(encoding='utf-8'))
            except json.JSONDecodeError:  # ainda sendo gravado
                time.sleep(0.3)
                continue
            print(json.dumps(dados, ensure_ascii=False, indent=2))
            sys.exit(0 if alvo == pronto or dados.get('resultado') == 'PASSOU' else 1)
        if erro.exists() and erro.stat().st_mtime > inicio:
            sys.exit('Falha na bancada:\n' + erro.read_text(encoding='utf-8'))
        time.sleep(1)
    sys.exit(f'Sem resposta em 120 s: {alvo.name} não apareceu.')


if __name__ == '__main__':
    main()
