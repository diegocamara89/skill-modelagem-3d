"""Ensaio da bancada dentro do FreeCAD, por eventos Qt internos (sem mouse/teclado do sistema).

Rodar: python scripts/abrir_bancada_freecad.py <pasta vazia> --testar
Grava <pasta>/bancada_teste.json. As marcas do operador não são tocadas (usa arquivo temporário).
Limite: evento Qt interno prova o filtro de clique e o desenho; não prova o olho do operador.
"""
import json
import math
import tempfile
import traceback
from pathlib import Path

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui
from pivy import coin

from bancada_freecad import Marcas, QtWidgets

DOWN = QtCore.QEvent.MouseButtonPress
UP = QtCore.QEvent.MouseButtonRelease


def criar_documento(caminho):
    """Caixa na origem + cilindro deslocado por Placement (prova de coordenada local)."""
    doc = App.newDocument('EnsaioBancada')
    sh = doc.addObject('Spreadsheet::Sheet', 'Medidas')
    sh.set('A1', 'comprimento')
    sh.set('B1', '=60 mm')
    sh.setAlias('B1', 'comprimento')
    box = doc.addObject('Part::Box', 'Caixa')
    box.Width, box.Height = 40, 20
    box.setExpression('Length', 'Medidas.comprimento')
    cil = doc.addObject('Part::Cylinder', 'Cilindro')
    cil.Radius, cil.Height = 12, 30
    cil.Placement.Base = App.Vector(100, 0, 0)
    ponte = doc.addObject('Part::Box', 'Ponte')  # flutua a 30 mm: a face de baixo pede suporte
    ponte.Length, ponte.Width, ponte.Height = 30, 30, 2
    ponte.Placement.Base = App.Vector(0, 60, 30)
    lamina = doc.addObject('Part::Box', 'Lamina')  # 0,8 mm: parede fina
    lamina.Length, lamina.Width, lamina.Height = 20, 20, 0.8
    lamina.Placement.Base = App.Vector(60, 60, 0)
    doc.recompute()
    doc.saveAs(str(caminho))
    Gui.activeDocument().activeView().viewAxonometric()
    Gui.SendMsgToActiveView('ViewFit')


def receptor(r):
    widgets = [w for w in r.viewer.findChildren(QtWidgets.QWidget) if w.metaObject().className() == 'QOpenGLWidget']
    return max(widgets, key=lambda w: w.width() * w.height()) if widgets else r.viewer


def evento(r, pos, typ):
    widget = receptor(r)
    width, height = r.view.getSize()
    logical = QtCore.QPoint(round(pos[0] * r.viewer.width() / width), round((height - 1 - pos[1]) * r.viewer.height() / height))
    local = widget.mapFrom(r.viewer, logical)
    button = QtCore.Qt.NoButton if typ == QtCore.QEvent.MouseMove else QtCore.Qt.LeftButton
    buttons = QtCore.Qt.NoButton if typ == UP else QtCore.Qt.LeftButton
    return widget, QtGui.QMouseEvent(typ, QtCore.QPointF(local), button, buttons, QtCore.Qt.NoModifier)


def enviar(r, pos, typ):
    widget, event = evento(r, pos, typ)
    antes = r.captura.contagem['pressionar'] + r.captura.contagem['soltar']
    QtCore.QCoreApplication.sendEvent(widget, event)  # despacho interno do Qt
    return r.captura.contagem['pressionar'] + r.captura.contagem['soltar'] > antes


def clique(r, pos):
    assert enviar(r, pos, DOWN), 'o filtro não capturou o clique'
    enviar(r, pos, UP)


def hit_logico(r, pos):
    widget, event = evento(r, pos, DOWN)
    return r.hit(r.captura.coordenada(widget, event.pos()))


def verificar_projecao(r):
    """Compara clique, marca persistida e pixels renderizados nas vistas da revisão."""
    original = r.marcas
    nota = r.pedir_anotacao.isChecked()
    modo = r.modo.currentIndex()
    camera = r.view.getCameraNode()
    altura = camera.height.getValue()
    provas = []
    try:
        r.pedir_anotacao.setChecked(False)
        r.modo.setCurrentIndex(1)
        w, h = r.view.getSize()
        alvos = {"Montado": set(), "Desmontado": set()}
        for grupo in alvos:
            obj = r.doc.getObject(grupo)
            assert obj, f"Falta o grupo {grupo}."
            alvos[grupo] = {o.Name for o in obj.Group if o.Name[1:3].isdigit()}
        with tempfile.TemporaryDirectory(prefix="prova_bancada_") as tmp:
            pasta = Path(tmp)
            for zoom in (1, .75):
                camera.height.setValue(altura * zoom)
                r.view.redraw()
                volume = camera.getViewVolume(w / h)
                for grupo, nomes in alvos.items():
                    pos = next(((x, y) for y in range(h//5, 4*h//5, 14)
                                for x in range(w//8, 7*w//8, 12)
                                if (alvo := hit_logico(r, (x,y))) and alvo['objeto'] in nomes), None)
                    assert pos, f"Nenhuma peça do grupo {grupo} encontrada na vista."
                    alvo = hit_logico(r, pos)
                    r.marcas = Marcas(pasta / f"{grupo}-{zoom}.json", original.dados['origem'])
                    r.atualizar()
                    clique(r, pos)
                    [marca] = Marcas(r.marcas.path, original.dados['origem']).itens
                    assert marca['objeto'] == alvo['objeto']
                    assert math.dist(marca['pontos'][0], alvo['ponto']) < .001
                    proj = volume.projectToScreen(coin.SbVec3f(*marca['pontos'][0])).getValue()
                    assert math.dist(pos, (proj[0]*w, proj[1]*h)) < 1.5
                    if zoom != 1:
                        # Reproduz o deslocamento herdado da cena que fez as
                        # primeiras marcas do bebedouro saírem da peça.
                        deslocamento = coin.SoTranslation()
                        deslocamento.translation = (40, 0, 0)
                        r.layer.insertChild(deslocamento, 0)
                        r.view.redraw()
                    imagem = pasta / "vista.png"
                    r.view.saveImage(str(imagem), w, h, "Current")
                    img = QtGui.QImage(str(imagem))
                    assert not img.isNull()
                    x,y = round(proj[0]*w), round((1-proj[1])*h)
                    cores = (img.pixelColor(i,j) for i in range(x-5,x+6) for j in range(y-5,y+6))
                    pixels = sum(c.red()>225 and c.green()<95 and c.blue()>135 for c in cores)
                    assert pixels > 35, (grupo, zoom, pos, pixels)
                    provas.append(dict(grupo=grupo, zoom=zoom, objeto=marca['objeto'], pixels=pixels))
    finally:
        camera.height.setValue(altura)
        r.marcas = original
        r.pedir_anotacao.setChecked(nota)
        r.modo.setCurrentIndex(modo)
        r.atualizar()
        r.desenhar()
    return provas


def executar(r):
    checks = []
    original = r.marcas
    pedir = r.pedir_anotacao.isChecked()
    r.pedir_anotacao.setChecked(False)
    report = {'resultado': 'FALHOU', 'checks': checks}
    try:
        r.pecas.setCurrentIndex(0)
        r.isolar()
        width, height = r.view.getSize()
        por_objeto = {}
        for y in range(height // 4, 3 * height // 4, 24):
            for x in range(40, width - 40, 24):
                h = r.hit((x, y))
                if h:
                    por_objeto.setdefault((h['objeto'], y), []).append((x, y))
        linha = max(por_objeto.values(), key=len) if por_objeto else []
        assert len(linha) >= 3, 'Nenhuma superfície suficiente no enquadramento'
        p, p2, p3 = linha[0], linha[len(linha) // 2], linha[-1]
        h, h2 = hit_logico(r, p), hit_logico(r, p2)
        checks.append('Picking nativo encontra ponto da peça na projeção')
        with tempfile.TemporaryDirectory(dir=r.root, prefix='ensaio_') as td:
            r.marcas = Marcas(Path(td) / 'marcas.json', original.dados['origem'])
            r.atualizar()
            r.modo.setCurrentIndex(0)
            widget, event = evento(r, p, DOWN)
            assert not r.captura.eventFilter(widget, event) and not r.marcas.itens
            checks.append('Navegar não captura clique nem cria marca')
            r.modo.setCurrentIndex(1)
            clique(r, p)
            clique(r, p3)
            assert [m['id'] for m in r.marcas.itens] == ['A', 'B']
            assert math.dist(r.marcas.itens[0]['pontos'][0], h['ponto']) < 0.001
            assert r.layer.getNumChildren() == 2 and not Gui.Selection.getSelection()
            checks.append('Clique pelo widget 3D cria A e B, desenha as letras e não seleciona a peça inteira')
            r.lista.setCurrentRow(0)
            r.modo.setCurrentIndex(3)
            clique(r, p2)
            assert math.dist(r.marcas.obter('A')['pontos'][0], h2['ponto']) < 0.001
            r.texto.setPlainText('Ensaio\nSegunda linha')
            r.descrever()
            assert r.marcas.obter('A')['descricao'] == 'Ensaio\nSegunda linha'
            checks.append('Mover e anotar atualizam a marca selecionada sem criar outra')
            r.modo.setCurrentIndex(2)
            enviar(r, p, DOWN)
            enviar(r, p2, QtCore.QEvent.MouseMove)
            enviar(r, p3, QtCore.QEvent.MouseMove)
            enviar(r, p3, UP)
            assert r.marcas.obter('C')['tipo'] == 'traco' and len(r.marcas.obter('C')['pontos']) == 3
            assert Marcas(r.marcas.path, original.dados['origem']).itens == r.marcas.itens
            checks.append('Traço C coleta três pontos; reabrir o JSON preserva tudo')
            r.lista.clearSelection()
            r.lista.item(0).setSelected(True)
            r.lista.item(2).setSelected(True)
            QtCore.QCoreApplication.sendEvent(r.lista, QtGui.QKeyEvent(QtCore.QEvent.KeyPress, QtCore.Qt.Key_Delete, QtCore.Qt.NoModifier))
            assert [m['id'] for m in r.marcas.itens] == ['B']
            r.desfazer()
            assert [m['id'] for m in r.marcas.itens] == ['A', 'B', 'C']
            checks.append('Delete apaga o lote selecionado; um Desfazer restaura')
            r.lista.clearSelection()
            r.lista.setCurrentRow(1)
            r.apagar()
            r.modo.setCurrentIndex(1)
            clique(r, p3)
            assert r.selecionada() == 'B'
            checks.append('Letra apagada é reutilizada (apagou B, a próxima é B)')
            # Coordenada local: marca em objeto com Placement desconta o deslocamento.
            desloc = next((o for o in r.objetos if o.Placement.Base.Length > 1), None)
            if desloc is not None:
                r.pecas.setCurrentIndex(r.pecas.findText(desloc.Label))
                r.isolar()
                alvo = next(((x, y) for y in range(height // 4, 3 * height // 4, 24) for x in range(40, width - 40, 24) if r.hit((x, y))), None)
                assert alvo, 'peça deslocada não apareceu isolada'
                clique(r, alvo)
                m = r.marcas.obter(r.selecionada())
                esperado = App.Vector(*m['pontos'][0]) - desloc.Placement.Base
                assert math.dist(m['locais'][0], list(esperado)) < 0.001 and m['locais'] != m['pontos']
                assert r.layer.getNumChildren() == 1, 'marcas de peça escondida deveriam sumir'
                checks.append('Peça isolada esconde as marcas das outras; ponto local desconta o Placement')
            # Post-it: a nota aparece ao lado da letra e some ao desligar a opção.
            r.pecas.setCurrentIndex(0)
            ident = r.marcas.itens[0]['id']
            r.marcas.descrever(ident, 'parede fina neste canto, engrossar para 2 mm sem mexer no furo')
            r.desenhar()
            texto = lambda: r.layer.getChild(0).getChild(r.layer.getChild(0).getNumChildren() - 1).string
            assert texto().getNum() == 3 and 'parede fina' in str(texto().getValues()[1]), 'post-it ausente'
            r.notas_na_peca.setChecked(False)
            assert texto().getNum() == 1
            r.notas_na_peca.setChecked(True)
            checks.append('Post-it: a nota aparece na peça ao lado da letra e some ao desligar')
            # Antes/Depois: alterna duas peças sem mexer na câmera.
            ia, ib = r.pecas.findText('Caixa'), r.pecas.findText('Cilindro')
            r.pecas.setCurrentIndex(ia)
            r.pecas.setCurrentIndex(ib)
            pos = r.view.getCameraNode().position.getValue().getValue()
            r.alternar()
            assert r.pecas.currentIndex() == ia and r.antes_idx == ib
            assert r.doc.Caixa.ViewObject.Visibility and not r.doc.Cilindro.ViewObject.Visibility
            assert math.dist(pos, r.view.getCameraNode().position.getValue().getValue()) < 1e-6, 'a câmera mexeu'
            r.alternar()
            assert r.pecas.currentIndex() == ib
            r.comparar('Ponte', 'Lamina')
            assert r.pecas.currentText() == 'Lamina' and r.pecas.itemText(r.antes_idx) == 'Ponte'
            checks.append('Antes/Depois alterna as duas peças com a câmera parada')
            # Mapa: ponte flutuante pede suporte; lâmina de 0,8 mm é parede fina; caixa não tem nada.
            r.pecas.setCurrentIndex(0)
            mapa = {p['peca']: p for p in r.mapa()['pecas']}
            assert abs(mapa['Ponte']['suporte_mm2'] - 900) < 1 and mapa['Ponte']['contato_mesa_mm2'] == 0, mapa['Ponte']
            assert mapa['Caixa']['suporte_mm2'] == 0 and abs(mapa['Caixa']['contato_mesa_mm2'] - 2400) < 1, mapa['Caixa']
            assert mapa['Caixa']['parede_fina_mm2'] == 0 and abs(mapa['Lamina']['parede_fina_mm2'] - 800) < 1, (mapa['Caixa'], mapa['Lamina'])
            assert mapa['Cilindro']['suporte_mm2'] == 0 and mapa['Cilindro']['contato_mesa_mm2'] > 400, mapa['Cilindro']
            assert r.mapa_no.getNumChildren() == 2 and (r.root / 'bancada_mapa.json').exists()
            r.limpar_mapa()
            assert r.mapa_no.getNumChildren() == 0
            checks.append('Mapa: ponte flutuante = 900 mm² de suporte; lâmina 0,8 mm = parede fina; caixa limpa')
            # Medidas: muda, refaz, e recusa valor que quebra a peça.
            r.medida('comprimento', 80)
            assert abs(r.doc.Caixa.Length.Value - 80) < 1e-6 and r.celulas['comprimento']['spin'].value() == 80
            r.medida('comprimento', 0)
            assert abs(r.doc.Caixa.Length.Value - 80) < 1e-6 and not r.invalidos(), 'valor inválido deveria ter sido desfeito'
            assert json.loads((r.root / 'bancada_medidas.json').read_text(encoding='utf-8'))['recusada']['valor'] == 0
            r.medida('comprimento', 60)
            checks.append('Medidas: 60 → 80 refaz a caixa; valor 0 é recusado e a peça volta ao que era')
            camera = r.view.getCameraOrientation().Q
            r.vistas()
            nomes = [f'bancada_{n}.png' for n in ('iso', 'iso_oposto', 'topo', 'frente')]
            assert all((r.root / n).stat().st_size > 2000 for n in nomes)
            assert len({(r.root / n).read_bytes() for n in nomes}) == 4, 'vistas repetidas'
            assert max(abs(a - b) for a, b in zip(camera, r.view.getCameraOrientation().Q)) < 1e-6
            checks.append('Quatro vistas de conferência distintas; câmera do operador restaurada')
            r.dock.hide()
            assert r.modo.currentIndex() == 0
            r.dock.show()
            checks.append('Fechar o painel devolve a navegação')
        report['resultado'] = 'PASSOU'
    except Exception:
        report['erro'] = traceback.format_exc()
    finally:
        r.drag = None
        r.marcas = original
        r.pedir_anotacao.setChecked(pedir)
        r.pecas.setCurrentIndex(0)
        r.isolar()
        r.atualizar()
        r.modo.setCurrentIndex(1)
        report['marcas_do_operador_ao_final'] = len(original.itens)
        r.gravar('bancada_teste.json', report)
    return report
