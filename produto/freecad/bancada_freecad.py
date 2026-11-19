"""Bancada de marcas no FreeCAD: o operador clica na peça e vê A, B, C…; o agente lê marcas.json.

Roda somente dentro do FreeCAD (janela aberta). Abra por `scripts/abrir_bancada_freecad.py`.
Nasceu no projeto Túneis V3 (07/11/2026) e foi generalizada em 10/11/2026.
Nada aqui usa mouse/teclado do sistema, rede ou execução de código vindo de arquivo.
"""
import copy
import importlib
import json
import os
import re
import subprocess
import textwrap
import traceback
import uuid
import zipfile
from pathlib import Path

import FreeCAD as App
import FreeCADGui as Gui
from pivy import coin
from PySide import QtCore, QtGui
try:
    from PySide import QtWidgets
except ImportError:
    QtWidgets = QtGui

import ambiente
import marcas
importlib.reload(marcas)
Marcas = marcas.Marcas

MALHAS = {'.stl', '.obj', '.ply', '.3mf', '.off', '.amf'}
FATIADOR = ambiente.caminho('bambu_studio_exe', 'BAMBU_STUDIO_EXE', '%ProgramFiles%/Bambu Studio/bambu-studio.exe')
# 3MF salvo pelo Bambu Studio de onde sai o perfil (máquina, filamento, processo). Padrão: A1, PETG genérico, 0,20 mm,
# que vem no pacote. Trocar: variável MODELO_3MF ou chave "modelo_3mf" no ambiente.json.
MODELO_3MF = ambiente.caminho('modelo_3mf', 'MODELO_3MF', Path(__file__).resolve().parent.parent / 'assets' / 'perfil_A1_PETG.3mf')
NS_3MF = ('xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
          'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p"')
SUPORTE = {'enable_support': '1', 'support_type': 'tree(auto)', 'support_threshold_angle': '30'}
LITERAL = re.compile(r'^=?\s*(-?\d+(?:\.\d+)?)\s*([A-Za-zµ°]*)$')  # célula "=60 mm" ou "3"; fórmula não é editável aqui


def paredes_finas(tri, n, centro, ok, minimo, bloco=300):
    """Máscara das faces cuja parede (distância até a face oposta, na normal) é menor que `minimo`.

    O raio do kernel de malha custa proporcional ao número de faces (medido: 3,9 ms com 50 mil), então a
    peça é cortada em blocos de ~`bloco` faces e cada raio só enxerga o bloco e a vizinhança dele.
    Medido em casca esférica de 0,8 mm e esfera maciça: 100 % e 0 % de faces finas.
    """
    import numpy as np
    import Mesh
    fina = np.zeros(len(tri), bool)
    idx = np.nonzero(ok)[0]
    if not len(idx):
        return fina
    lo, hi = tri[idx].min(axis=1), tri[idx].max(axis=1)
    area = np.linalg.norm(np.cross(tri[idx, 1] - tri[idx, 0], tri[idx, 2] - tri[idx, 0]), axis=1).sum() / 2
    lado = max(4 * minimo, float(area * bloco / len(idx)) ** 0.5)  # peça é casca: o bloco se dimensiona pela área, não pelo volume
    celula = np.floor((centro[idx] - lo.min(axis=0)) / lado).astype(int)
    origem = centro - n * minimo  # a reta parte de `minimo` para dentro: parede mais fina aparece antes da própria face
    for c in np.unique(celula, axis=0):
        meus = np.all(celula == c, axis=1)
        blo, bhi = lo[meus].min(axis=0) - minimo, hi[meus].max(axis=0) + minimo
        perto = ~meus & np.all(hi >= blo, axis=1) & np.all(lo <= bhi, axis=1)
        ordem = np.concatenate([idx[meus], idx[perto]])
        sub = Mesh.Mesh(tri[ordem].tolist())
        if sub.CountFacets != len(ordem):  # o kernel descartou alguma face: índices não batem, não arrisca
            continue
        for local, i in enumerate(idx[meus]):
            for j, ponto in sub.nearestFacetOnRay(tuple(origem[i]), tuple(-n[i])).items():
                if j != local and 0.05 < np.linalg.norm(np.array(ponto) - centro[i]) < minimo:
                    fina[i] = True
    return fina


def hms(segundos):
    return f'{int(segundos // 3600)}h{int(segundos % 3600 // 60):02d}'
MODOS = ['Navegar', 'Ponto — clique', 'Traço — arraste', 'Mover ponto selecionado — clique']
AJUDA = ['Navegação livre. Selecione Ponto ou Traço para marcar.', 'Clique na superfície para criar A, B, C…',
         'Arraste com o botão esquerdo sobre a superfície.', 'Selecione uma marca de ponto na lista e clique na nova posição.']


class ListaMarcas(QtWidgets.QListWidget):
    apagarSolicitado = QtCore.Signal()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Delete:
            self.apagarSolicitado.emit()
            event.accept()
            return
        super().keyPressEvent(event)


class CapturaViewport(QtCore.QObject):
    """Captura o clique no Qt ANTES da seleção do FreeCAD (senão a peça inteira acende)."""

    def __init__(self, bancada, viewer):
        super().__init__(bancada.dock)
        self.r = bancada
        self.viewer = viewer
        self.contagem = {'pressionar': 0, 'soltar': 0, 'ultimo': None}

    def coordenada(self, widget, pos):
        p = widget.mapTo(self.viewer, pos)
        width, height = self.r.view.getSize()
        return (round(p.x() * width / self.viewer.width()), height - 1 - round(p.y() * height / self.viewer.height()))

    def eventFilter(self, widget, event):
        r = self.r
        typ = event.type()
        if typ not in (QtCore.QEvent.MouseButtonPress, QtCore.QEvent.MouseButtonRelease, QtCore.QEvent.MouseButtonDblClick, QtCore.QEvent.MouseMove):
            return False
        if r.closed or r.modo.currentIndex() == 0 or App.ActiveDocument != r.doc:
            return False
        if not isinstance(widget, QtWidgets.QWidget) or not (widget == self.viewer or self.viewer.isAncestorOf(widget)):
            return False
        if event.modifiers() & (QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier):
            return False
        pos = self.coordenada(widget, event.pos())
        if typ == QtCore.QEvent.MouseMove:
            if event.buttons() & (QtCore.Qt.MiddleButton | QtCore.Qt.RightButton):
                return False
            if r.drag is not None:
                r.seguro(lambda: r.arrastar(pos))
            return True  # impede a pré-seleção da peça inteira no modo de marcação
        if event.button() != QtCore.Qt.LeftButton:
            return False
        press = typ in (QtCore.QEvent.MouseButtonPress, QtCore.QEvent.MouseButtonDblClick)
        name = 'pressionar' if press else 'soltar'
        self.contagem[name] += 1
        self.contagem['ultimo'] = {'evento': name, 'posicao': pos, 'origem_fisica': event.spontaneous()}
        r.seguro(lambda: r.pressionar(pos) if press else r.soltar(pos))
        event.accept()
        return True


class Bancada:
    def __init__(self, projeto, documento, importar=()):
        self.root = Path(projeto)
        target = Path(documento)
        self.doc = next((d for d in App.listDocuments().values() if d.FileName and Path(d.FileName) == target), None)
        if self.doc is None:
            self.doc = App.openDocument(str(target)) if target.exists() else self.importar(target, importar)
        App.setActiveDocument(self.doc.Name)
        self.doc_name = self.doc.Name
        self.view = Gui.activeDocument().activeView()
        self.view.setAnimationEnabled(False)
        # Peças = objetos de topo visíveis agora. Corpo do PartDesign conta como uma peça.
        self.objetos = [o for o in self.doc.RootObjects if getattr(o, 'ViewObject', None) and o.ViewObject.Visibility
                        and (hasattr(o, 'Placement') or hasattr(o, 'Group'))]  # planilha e afins não são peça
        self.marcas = Marcas(self.root / 'marcas.json', target.name)
        viewers = [w for w in Gui.getMainWindow().findChildren(QtWidgets.QWidget)
                   if w.metaObject().className() == 'Gui::View3DInventorViewer' and w.isVisible()]
        if len(viewers) > 1:
            abas = [a.activeSubWindow() for a in Gui.getMainWindow().findChildren(QtWidgets.QMdiArea)]
            viewers = [w for w in viewers if any(aba and aba.isAncestorOf(w) for aba in abas)]
        if len(viewers) != 1:  # antes de criar painel/camada: falha aqui não deixa resto na tela
            raise RuntimeError(f'A bancada precisa de uma única vista 3D visível; achei {len(viewers)}. Feche as outras abas 3D.')
        self.layer = coin.SoAnnotation()
        self.layer.ref()
        self.view.getSceneGraph().addChild(self.layer)
        self.mapa_no = coin.SoSeparator()  # mapa de suporte/parede: na cena normal, some atrás da peça
        self.mapa_no.ref()
        self.view.getSceneGraph().addChild(self.mapa_no)
        self.drag = None
        self.closed = False
        self.proc = None
        self.atual_idx = self.antes_idx = 0
        self.alternando = False
        self.painel()
        self.viewer = viewers[0]
        self.captura = CapturaViewport(self, self.viewer)
        QtWidgets.QApplication.instance().installEventFilter(self.captura)
        # Canal do agente: arquivo comando.json com ação de lista fechada. Sem porta, sem código arbitrário.
        self.timer = QtCore.QTimer(self.dock)
        self.timer.timeout.connect(self.comando)
        self.timer.start(500)
        self.timer_docs = QtCore.QTimer(self.dock)
        self.timer_docs.timeout.connect(self.conferir_documento)
        self.timer_docs.start(1000)
        self.atualizar()
        self.modo.setCurrentIndex(1)
        QtCore.QTimer.singleShot(1200, self.pronto)

    def gravar(self, nome, dados):
        (self.root / nome).write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding='utf-8')

    def importar(self, target, arquivos):
        if not arquivos:
            raise FileNotFoundError(f'{target} não existe e nenhum arquivo foi dado para importar.')
        doc = App.newDocument(target.stem)
        for arq in map(Path, arquivos):
            if arq.suffix.lower() in MALHAS:
                import Mesh
                Mesh.insert(str(arq), doc.Name)
            else:  # STEP, IGES, BREP…
                import Import
                Import.insert(str(arq), doc.Name)
        doc.recompute()
        doc.saveAs(str(target))  # só o documento novo é gravado; documento do dono nunca é regravado aqui
        Gui.activeDocument().activeView().viewAxonometric()
        Gui.SendMsgToActiveView('ViewFit')
        return doc

    def painel(self):
        self.dock = QtWidgets.QDockWidget(f'Marcar e revisar — {self.doc.Label}', Gui.getMainWindow())
        self.dock.setObjectName('BancadaMarcas')
        self.dock.setMinimumWidth(320)
        body = QtWidgets.QWidget()
        fora = QtWidgets.QVBoxLayout(body)
        fora.addWidget(QtWidgets.QLabel('Peça visível'))
        self.pecas = QtWidgets.QComboBox()
        self.pecas.addItem('Todas as peças', None)
        groups = {}
        for o in self.objetos:
            groups.setdefault(o.Label.split(' / ')[0], []).append(o.Name)
        for label, names in groups.items():
            self.pecas.addItem(label, names)
        self.pecas.currentIndexChanged.connect(self.trocou_peca)
        fora.addWidget(self.pecas)
        abas = QtWidgets.QTabWidget()
        fora.addWidget(abas)
        aba = QtWidgets.QWidget()
        box = QtWidgets.QVBoxLayout(aba)
        abas.addTab(aba, 'Marcas')
        abas.addTab(self.aba_revisar(), 'Revisar')
        self.celulas = {}
        medidas = self.aba_medidas()
        if medidas is not None:
            abas.addTab(medidas, 'Medidas')
        intro = QtWidgets.QLabel('Pontos: clique na superfície. Traço: arraste.\nPara girar livremente, escolha Navegar.\nAs marcas são salvas automaticamente.')
        intro.setWordWrap(True)
        box.addWidget(intro)
        self.modo = QtWidgets.QComboBox()
        self.modo.addItems(MODOS)
        self.modo.currentIndexChanged.connect(self.mudar_modo)
        box.addWidget(self.modo)
        self.pedir_anotacao = QtWidgets.QCheckBox('Abrir anotação ao criar uma marca')
        self.pedir_anotacao.setToolTip('Abre uma caixa de texto após marcar. Duplo clique na lista edita a anotação depois.')
        box.addWidget(self.pedir_anotacao)
        self.notas_na_peca = QtWidgets.QCheckBox('Mostrar as notas na peça (post-it)')
        self.notas_na_peca.setChecked(True)
        self.notas_na_peca.toggled.connect(lambda *_: self.desenhar())
        box.addWidget(self.notas_na_peca)
        self.lista = ListaMarcas()
        self.lista.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.lista.itemSelectionChanged.connect(self.escolher)
        self.lista.itemDoubleClicked.connect(lambda item: self.seguro(lambda: self.anotar(item.data(QtCore.Qt.UserRole))))
        self.lista.apagarSolicitado.connect(lambda: self.seguro(self.apagar))
        box.addWidget(self.lista)
        ajuda = QtWidgets.QLabel('Ctrl/Shift selecionam várias marcas. Delete apaga as selecionadas.\nDuplo clique abre a anotação.')
        ajuda.setWordWrap(True)
        box.addWidget(ajuda)
        box.addWidget(QtWidgets.QLabel('Anotação da marca selecionada'))
        self.editando = None
        self.texto = QtWidgets.QPlainTextEdit()
        self.texto.setMaximumHeight(100)
        self.texto.setPlaceholderText('Ex.: parede fina neste canto. Texto salvo automaticamente.')
        self.texto.textChanged.connect(self.descrever)
        box.addWidget(self.texto)
        row = QtWidgets.QHBoxLayout()
        for label, func in [('Apagar selecionadas', self.apagar), ('Desfazer', self.desfazer), ('Enquadrar', self.view.fitAll)]:
            b = QtWidgets.QPushButton(label)
            b.clicked.connect(lambda checked=False, f=func: self.seguro(f))
            row.addWidget(b)
        box.addLayout(row)
        self.status = QtWidgets.QLabel('Preparando…')
        self.status.setWordWrap(True)
        fora.addWidget(self.status)
        self.dock.setWidget(body)
        Gui.getMainWindow().addDockWidget(QtCore.Qt.RightDockWidgetArea, self.dock)
        self.dock.visibilityChanged.connect(lambda visible: self.modo.setCurrentIndex(0) if not visible and not self.closed else None)

    def seguro(self, func):
        try:
            return func()
        except Exception as e:
            self.status.setText('Falha: ' + str(e))
            App.Console.PrintError(traceback.format_exc() + '\n')
            (self.root / 'bancada_erro.log').write_text(traceback.format_exc(), encoding='utf-8')

    def selecionadas(self):
        return [item.data(QtCore.Qt.UserRole) for item in self.lista.selectedItems()]

    def selecionada(self):
        ids = self.selecionadas()
        return ids[0] if len(ids) == 1 else None

    def escolher(self, *args):
        self.editando = self.selecionada()
        self.texto.blockSignals(True)
        self.texto.setPlainText(self.marcas.obter(self.editando)['descricao'] if self.editando else '')
        self.texto.setEnabled(self.editando is not None)
        self.texto.blockSignals(False)
        self.desenhar()

    def atualizar(self, selecionar=None):
        ids = {selecionar} if selecionar else set(self.selecionadas())
        self.lista.blockSignals(True)
        self.lista.clear()
        current = None
        for m in self.marcas.itens:
            o = self.doc.getObject(m['objeto'])
            item = QtWidgets.QListWidgetItem(f"{m['id']} · {m['tipo']} · {o.Label if o else m['objeto']}")
            item.setData(QtCore.Qt.UserRole, m['id'])
            item.setToolTip(m['descricao'])
            self.lista.addItem(item)
            if m['id'] in ids:
                item.setSelected(True)
                current = item
        if current:
            self.lista.setCurrentItem(current, QtCore.QItemSelectionModel.NoUpdate)
        self.lista.blockSignals(False)
        self.escolher()

    def descrever(self):
        ident = self.editando
        if ident:
            self.seguro(lambda: self.marcas.descrever(ident, self.texto.toPlainText()))
            for i in range(self.lista.count()):
                item = self.lista.item(i)
                if item.data(QtCore.Qt.UserRole) == ident:
                    item.setToolTip(self.texto.toPlainText())
            self.desenhar()  # o post-it acompanha a digitação

    def anotar(self, ident=None):
        ident = ident or self.selecionada()
        if not ident:
            return
        texto, ok = QtWidgets.QInputDialog.getMultiLineText(self.dock, f'Anotação {ident}', 'O que você quer registrar neste ponto?', self.marcas.obter(ident)['descricao'])
        if ok:
            self.marcas.descrever(ident, texto)
            self.atualizar(ident)

    def apagar(self):
        ids = self.selecionadas()
        if ids:
            self.marcas.apagar_lote(ids)
            self.atualizar()
            self.status.setText('Marcas ' + ', '.join(ids) + ' apagadas. Desfazer restaura o lote.')

    def desfazer(self):
        self.marcas.desfazer()
        self.atualizar()
        self.status.setText('Última alteração desfeita.')

    def mudar_modo(self, *args):
        self.drag = None
        if hasattr(self, 'viewer'):
            if self.modo.currentIndex() == 0:
                self.viewer.unsetCursor()
            else:
                self.viewer.setCursor(QtCore.Qt.CrossCursor)
                Gui.Selection.clearSelection()
                if hasattr(Gui.Selection, 'removePreselection'):
                    Gui.Selection.removePreselection()
        self.status.setText(AJUDA[self.modo.currentIndex()])
        self.desenhar()

    def isolar(self, *args, enquadrar=True):
        names = self.pecas.currentData()
        for o in self.objetos:
            o.ViewObject.Visibility = (names is None or o.Name in names)
        self.limpar_mapa()
        self.desenhar()
        if enquadrar:
            self.view.fitAll()

    # ---- antes/depois -------------------------------------------------------------------------
    def trocou_peca(self, idx):
        if idx != self.atual_idx:
            self.antes_idx, self.atual_idx = self.atual_idx, idx
        self.isolar(enquadrar=not self.alternando)  # ao alternar, a câmera fica parada para comparar
        self.status.setText(f'Mostrando: {self.pecas.currentText()}. Antes/Depois volta para: {self.pecas.itemText(self.antes_idx)}.')

    def alternar(self):
        self.alternando = True
        try:
            self.pecas.setCurrentIndex(self.antes_idx)
        finally:
            self.alternando = False

    def comparar(self, antes, depois):
        a, d = self.pecas.findText(antes), self.pecas.findText(depois)
        if a < 0 or d < 0 or a == d:
            raise ValueError(f'Para comparar preciso de duas peças da lista; recebi {antes!r} e {depois!r}.')
        self.pecas.setCurrentIndex(a)
        self.pecas.setCurrentIndex(d)

    def aba_revisar(self):
        aba = QtWidgets.QWidget()
        box = QtWidgets.QVBoxLayout(aba)
        b = QtWidgets.QPushButton('Antes / Depois')
        b.setToolTip('Alterna entre a peça visível agora e a anterior, sem mexer na câmera.\nEscolha uma versão em "Peça visível", depois a outra, e clique aqui.')
        b.clicked.connect(lambda *_: self.seguro(self.alternar))
        box.addWidget(b)
        box.addWidget(QtWidgets.QLabel('Mapa na peça: vermelho = pede suporte; amarelo = parede fina'))
        linha = QtWidgets.QHBoxLayout()
        self.limiar = QtWidgets.QDoubleSpinBox()
        self.limiar.setRange(5, 80)
        self.limiar.setValue(30)
        self.limiar.setSuffix(' ° (suporte abaixo de)')
        self.parede = QtWidgets.QDoubleSpinBox()
        self.parede.setRange(0.2, 10)
        self.parede.setSingleStep(0.2)
        self.parede.setValue(1.2)
        self.parede.setSuffix(' mm (parede mín.)')
        linha.addWidget(self.limiar)
        linha.addWidget(self.parede)
        box.addLayout(linha)
        linha = QtWidgets.QHBoxLayout()
        for label, func in [('Mostrar mapa', self.mapa), ('Limpar mapa', self.limpar_mapa)]:
            b = QtWidgets.QPushButton(label)
            b.clicked.connect(lambda checked=False, f=func: self.seguro(f))
            linha.addWidget(b)
        box.addLayout(linha)
        self.mapa_txt = QtWidgets.QLabel('A mesa é o Z mais baixo do que está visível.')
        self.mapa_txt.setWordWrap(True)
        box.addWidget(self.mapa_txt)
        self.botao_fatiar = QtWidgets.QPushButton('Fatiar o que está visível')
        self.botao_fatiar.setToolTip('Fatia no Bambu Studio sem abrir a janela dele. Não envia nada à impressora.')
        self.botao_fatiar.clicked.connect(lambda *_: self.seguro(self.fatiar))
        box.addWidget(self.botao_fatiar)
        self.fatiar_txt = QtWidgets.QLabel('Gramas e tempo aparecem aqui.')
        self.fatiar_txt.setWordWrap(True)
        box.addWidget(self.fatiar_txt)
        box.addStretch()
        return aba

    # ---- geometria do que está visível ----------------------------------------------------------
    def corpos(self):
        """(objeto, malha em coordenadas globais) de cada peça visível. Sólido é triangulado só para medir."""
        vistos, saida = set(), []
        for raiz in self.objetos:
            if not raiz.ViewObject.Visibility:
                continue
            filhos = [x for x in raiz.OutListRecursive if getattr(x, 'ViewObject', None) and x.ViewObject.Visibility and x not in self.objetos]
            for o in [raiz] + sorted(filhos, key=lambda x: len(x.InListRecursive)):  # o corpo vem antes das etapas dele
                if o.Name in vistos:
                    continue
                if o.isDerivedFrom('Mesh::Feature'):
                    m = o.Mesh.copy()
                elif o.isDerivedFrom('Part::Feature') and not o.Shape.isNull() and o.Shape.Faces:
                    import MeshPart
                    m = MeshPart.meshFromShape(Shape=o.Shape, LinearDeflection=0.05, AngularDeflection=0.3)
                else:
                    continue
                pai = o.getGlobalPlacement().multiply(o.Placement.inverse())  # a malha já traz o Placement do próprio objeto
                if not pai.isIdentity():
                    m.transform(pai.toMatrix())
                saida.append((o, m))
                vistos.update(x.Name for x in [o] + o.OutListRecursive if x is o or x not in self.objetos)  # corpo já contém as etapas; outra peça de topo não
        return saida

    # ---- mapa de suporte e parede fina ---------------------------------------------------------------
    def limpar_mapa(self):
        self.mapa_no.removeAllChildren()
        if hasattr(self, 'mapa_txt'):
            self.mapa_txt.setText('A mesa é o Z mais baixo do que está visível.')
        self.view.redraw()

    def mapa(self):
        import numpy as np
        corpos = self.corpos()
        if not corpos:
            raise ValueError('Nenhuma peça visível com geometria.')
        self.limpar_mapa()
        self.mapa_txt.setText('Calculando o mapa… (alguns segundos em peça grande)')
        QtWidgets.QApplication.processEvents()
        L, minimo = self.limiar.value(), self.parede.value()
        dados = [(o, m, np.array([tuple(p) for p in m.Topology[0]], float), np.array(m.Topology[1], int)) for o, m in corpos]
        mesa = min(p[:, 2].min() for _, _, p, _ in dados)
        vermelho, amarelo, relatorio = [], [], []
        for o, m, p, f in dados:
            tri = p[f]
            n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
            dobro = np.linalg.norm(n, axis=1)
            ok = dobro > 1e-12
            n[ok] /= dobro[ok][:, None]
            area, centro = dobro / 2, tri.mean(axis=1)
            cosd = -n[:, 2]
            ang = np.degrees(np.arccos(np.clip(cosd, -1, 1)))  # 0 = teto, 90 = parede (igual a mapa_balanco.py)
            no_ar = ok & (cosd > 1e-6) & (centro[:, 2] - mesa > 0.5)
            pede = no_ar & (ang < L)
            contato = area[ok & (cosd > 0.99) & (centro[:, 2] - mesa < 0.3)].sum()
            fina = paredes_finas(tri, n, centro, ok, minimo)
            vermelho.append(tri[pede])
            amarelo.append(tri[fina & ~pede])
            relatorio.append({'peca': o.Label, 'faces': int(len(f)), 'suporte_mm2': round(float(area[pede].sum()), 1),
                              'pior_inclinacao_graus': round(float(ang[no_ar].min()), 1) if no_ar.any() else 90.0,
                              'parede_fina_mm2': round(float(area[fina].sum()), 1), 'contato_mesa_mm2': round(float(contato), 1)})
        for tris, cor in [(np.concatenate(vermelho), (1., 0.1, 0.1)), (np.concatenate(amarelo), (1., 0.85, 0.))]:
            if len(tris):
                self.mapa_no.addChild(self.no_faces(tris, cor))
        self.view.redraw()
        total = lambda k: sum(r[k] for r in relatorio)
        resumo = {'limiar_graus': L, 'parede_minima_mm': minimo, 'mesa_z': round(float(mesa), 3), 'pecas': relatorio,
                  'alcance': 'Indicador por face (ângulo e espessura na normal de cada triângulo). Face apoiada em OUTRA peça visível também '
                             'aparece como suporte e sem contato: só a mesa conta. Não prova suporte zero nem resistência: confirme fatiando.'}
        self.gravar('bancada_mapa.json', resumo)
        sem = [r['peca'] for r in relatorio if r['contato_mesa_mm2'] < 1]
        self.mapa_txt.setText(f"Pede suporte: {total('suporte_mm2'):.0f} mm². Parede abaixo de {minimo:g} mm: {total('parede_fina_mm2'):.0f} mm². "
                              f"Contato com a mesa: {total('contato_mesa_mm2'):.0f} mm²." + (f" SEM CONTATO: {', '.join(sem)}." if sem else '') + ' É indicador; fatie para confirmar.')
        return resumo

    def no_faces(self, tris, cor):
        node = coin.SoSeparator()
        pick = coin.SoPickStyle()
        pick.style = coin.SoPickStyle.UNPICKABLE
        node.addChild(pick)
        offset = coin.SoPolygonOffset()  # puxa a pintura para a frente da superfície da peça
        offset.factor = -2
        offset.units = -2
        node.addChild(offset)
        luz = coin.SoLightModel()
        luz.model = coin.SoLightModel.BASE_COLOR
        node.addChild(luz)
        hints = coin.SoShapeHints()
        hints.vertexOrdering = coin.SoShapeHints.UNKNOWN_ORDERING  # visível dos dois lados
        node.addChild(hints)
        color = coin.SoBaseColor()
        color.rgb = cor
        node.addChild(color)
        pts = tris.reshape(-1, 3).tolist()
        coords = coin.SoCoordinate3()
        coords.point.setValues(0, len(pts), pts)
        node.addChild(coords)
        faces = coin.SoFaceSet()
        faces.numVertices.setValues(0, len(tris), [3] * len(tris))
        node.addChild(faces)
        return node

    # ---- medidas (planilha com alias) ----------------------------------------------------------------
    def aba_medidas(self):
        for sh in self.doc.Objects:
            if sh.isDerivedFrom('Spreadsheet::Sheet'):
                for cel in sh.getUsedCells():
                    nome, lit = sh.getAlias(cel), LITERAL.match(str(sh.getContents(cel)))
                    if nome and lit:
                        self.celulas[nome] = {'planilha': sh.Name, 'celula': cel, 'unidade': lit.group(2), 'inteiro': '.' not in lit.group(1) and not lit.group(2)}
        if not self.celulas:
            return None
        aba = QtWidgets.QWidget()
        box = QtWidgets.QVBoxLayout(aba)
        box.addWidget(QtWidgets.QLabel('Arraste ou digite. A peça se refaz ao soltar.'))
        for nome, c in self.celulas.items():
            v = self.valor(nome)
            box.addWidget(QtWidgets.QLabel(nome))
            linha = QtWidgets.QHBoxLayout()
            spin = QtWidgets.QDoubleSpinBox()
            spin.setKeyboardTracking(False)
            spin.setDecimals(0 if c['inteiro'] else 4)
            spin.setRange(-1e6, 1e6)
            spin.setValue(v)
            spin.setSuffix(' ' + c['unidade'] if c['unidade'] else '')
            lo, hi = sorted((v * 0.5, v * 1.5)) if v else (0.0, 10.0)
            barra = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            barra.setRange(0, 1000)
            barra.setValue(500 if v else 0)
            barra.sliderMoved.connect(lambda pos, s=spin, lo=lo, hi=hi, c=c: (c.update(moveu=True), s.blockSignals(True), s.setValue(lo + (hi - lo) * pos / 1000), s.blockSignals(False)))
            # só aplica se arrastou: clique parado na barra não reescreve a célula com o valor arredondado
            barra.sliderReleased.connect(lambda n=nome, s=spin, c=c: c.pop('moveu', False) and self.seguro(lambda: self.medida(n, s.value())))
            spin.valueChanged.connect(lambda valor, n=nome: self.seguro(lambda: self.medida(n, valor)))
            c['spin'] = spin
            linha.addWidget(barra, 2)
            linha.addWidget(spin, 1)
            box.addLayout(linha)
        box.addStretch()
        return aba

    def valor(self, nome):
        c = self.celulas[nome]
        return float(LITERAL.match(str(self.doc.getObject(c['planilha']).getContents(c['celula']))).group(1))

    def invalidos(self):
        return [o.Label for o in self.doc.Objects if 'Invalid' in o.State or 'Error' in o.State
                or (o.isDerivedFrom('Part::Feature') and not o.Shape.isNull() and not o.Shape.isValid())]

    def medida(self, nome, valor):
        """Muda uma medida e refaz a peça. Se alguma etapa ficar inválida, volta ao valor anterior."""
        if nome not in self.celulas:
            raise ValueError(f'Medida {nome!r} não existe. Disponíveis: {sorted(self.celulas)}')
        c = self.celulas[nome]
        sh = self.doc.getObject(c['planilha'])
        valor = round(float(valor)) if c['inteiro'] else round(float(valor), 4)
        antes = sh.getContents(c['celula'])
        num = lambda v: f'{v:.4f}'.rstrip('0').rstrip('.')  # sem notação exponencial, que a leitura não aceita
        escrever = lambda v: num(v) if not c['unidade'] else f'={num(v)} {c["unidade"]}'
        if valor == self.valor(nome):
            return
        ja_ruins = set(self.invalidos())  # defeito que já existia não é culpa desta medida
        sh.set(c['celula'], escrever(valor))
        self.doc.recompute()
        ruins = [x for x in self.invalidos() if x not in ja_ruins]  # recompute não acusa etapa inválida sozinho (freecad.md, seção 3)
        if ruins:
            sh.set(c['celula'], antes)
            self.doc.recompute()
        final = self.valor(nome)
        c['spin'].blockSignals(True)
        c['spin'].setValue(final)
        c['spin'].blockSignals(False)
        self.limpar_mapa()
        self.gravar('bancada_medidas.json', {'medidas': {n: self.valor(n) for n in self.celulas}, 'recusada': {'nome': nome, 'valor': valor, 'invalidos': ruins} if ruins else None})
        self.status.setText(f'{nome} = {valor:g} deixou inválido: {", ".join(ruins)}. Voltei para {final:g}.' if ruins else f'{nome} = {final:g} {c["unidade"]}. Peça refeita (não salva).')
        self.view.redraw()

    # ---- fatiar ----------------------------------------------------------------------------------------
    def fatiar(self):
        if self.proc is not None:
            raise RuntimeError('Já há um fatiamento em andamento.')
        (self.root / 'bancada_fatiado.json').unlink(missing_ok=True)  # resultado velho não pode passar por novo
        if not FATIADOR.exists() or not MODELO_3MF.exists():
            raise FileNotFoundError(f'Preciso do Bambu Studio ({FATIADOR}) e de um 3MF de perfil ({MODELO_3MF}; variável MODELO_3MF).')
        lista = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq bambu-studio.exe', '/NH'], capture_output=True, text=True, creationflags=0x08000000).stdout
        if 'bambu-studio.exe' in lista.lower():
            raise RuntimeError('Há um Bambu Studio aberto ou fatiando. Um por vez: feche-o ou espere terminar.')
        corpos = self.corpos()
        if not corpos:
            raise ValueError('Nenhuma peça visível com geometria.')
        pontos = [m.Topology[0] for _, m in corpos]
        lo = [min(getattr(p, e) for ps in pontos for p in ps) for e in 'xyz']
        hi = [max(getattr(p, e) for ps in pontos for p in ps) for e in 'xyz']
        with zipfile.ZipFile(MODELO_3MF) as z:
            cfg = json.loads(z.read('Metadata/project_settings.config'))
            tipos = z.read('[Content_Types].xml')
        area = [tuple(map(float, c.split('x'))) for c in cfg['printable_area']]
        mesa = (max(a[0] for a in area), max(a[1] for a in area), float(cfg.get('printable_height', 256)))
        tam = [h - l for l, h in zip(lo, hi)]
        if any(t > m for t, m in zip(tam, mesa)):
            raise ValueError(f'O que está visível mede {tam[0]:.0f}×{tam[1]:.0f}×{tam[2]:.0f} mm e não cabe na mesa {mesa[0]:.0f}×{mesa[1]:.0f}×{mesa[2]:.0f}. Isole uma peça em "Peça visível".')
        for k, v in SUPORTE.items():
            cfg[k] = [v] if isinstance(cfg.get(k), list) else v
        dif = list(cfg.get('different_settings_to_system', ['', '', ''])) + ['', '', '']
        dif[0] = ';'.join(sorted(set(filter(None, dif[0].split(';'))) | set(SUPORTE)))  # senão a interface do Studio ignora o ajuste
        cfg['different_settings_to_system'] = dif[:max(3, len(cfg.get('different_settings_to_system', [])))]
        pasta = self.root / 'fatiar'
        pasta.mkdir(exist_ok=True)
        for velho in list(pasta.glob('plate_*.gcode')) + [pasta / 'result.json']:
            velho.unlink(missing_ok=True)  # saída da rodada anterior desta mesma função
        projeto = pasta / 'visivel.3mf'
        rel = 'http://schemas.openxmlformats.org/package/2006/relationships'
        tipo = 'http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel'
        comps, partes, arquivos = [], [], {}
        for i, (o, m) in enumerate(corpos, 1):
            pts, fcs = m.Topology
            malha = ''.join(f'<vertex x="{p.x:.6f}" y="{p.y:.6f}" z="{p.z:.6f}"/>' for p in pts)
            tri = ''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in fcs)
            caminho = f'3D/Objects/object_{i}.model'
            arquivos[caminho] = (f'<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" {NS_3MF}><metadata name="BambuStudio:3mfVersion">1</metadata>'
                                 f'<resources><object id="{i}" type="model"><mesh><vertices>{malha}</vertices><triangles>{tri}</triangles></mesh></object></resources><build/></model>')
            comps.append(f'<component p:path="/{caminho}" objectid="{i}" p:UUID="{uuid.uuid4()}" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>')
            nome = o.Label.replace('&', 'e').replace('"', "'").replace('<', '(').replace('>', ')')
            partes.append(f'<part id="{i}" subtype="normal_part"><metadata key="name" value="{nome}"/></part>')
        tx, ty, tz = mesa[0] / 2 - (lo[0] + hi[0]) / 2, mesa[1] / 2 - (lo[1] + hi[1]) / 2, -lo[2]
        modelo = (f'<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" {NS_3MF}><metadata name="Application">BambuStudio-02.08.02.61</metadata>'
                  f'<metadata name="BambuStudio:3mfVersion">1</metadata><resources><object id="100" p:UUID="{uuid.uuid4()}" type="model"><components>{"".join(comps)}</components></object></resources>'
                  f'<build><item objectid="100" p:UUID="{uuid.uuid4()}" transform="1 0 0 0 1 0 0 0 1 {tx} {ty} {tz}" printable="1"/></build></model>')
        ajustes = ('<config><object id="100"><metadata key="name" value="Bancada"/><metadata key="extruder" value="1"/>' + ''.join(partes) + '</object><plate><metadata key="plater_id" value="1"/>'
                   '<metadata key="plater_name" value="Bancada"/><metadata key="locked" value="false"/><model_instance><metadata key="object_id" value="100"/>'
                   '<metadata key="instance_id" value="0"/><metadata key="identify_id" value="100"/></model_instance></plate></config>')
        with zipfile.ZipFile(projeto, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('[Content_Types].xml', tipos)
            z.writestr('_rels/.rels', f'<Relationships xmlns="{rel}"><Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="{tipo}"/></Relationships>')
            z.writestr('3D/3dmodel.model', modelo)
            z.writestr('3D/_rels/3dmodel.model.rels', f'<Relationships xmlns="{rel}">' + ''.join(f'<Relationship Target="/{c}" Id="rel-{i}" Type="{tipo}"/>' for i, c in enumerate(arquivos, 1)) + '</Relationships>')
            z.writestr('Metadata/model_settings.config', ajustes)
            z.writestr('Metadata/project_settings.config', json.dumps(cfg, ensure_ascii=False, indent=2))
            for caminho, texto in arquivos.items():
                z.writestr(caminho, texto)
        self.fatiando = {'pecas': [o.Label for o, _ in corpos], 'pasta': pasta, 'projeto': projeto,
                         'perfil': f"{cfg.get('printer_model')} · {cfg.get('filament_settings_id', ['?'])[0]} · {cfg.get('print_settings_id')} · suporte automático em árvore"}
        self.proc = QtCore.QProcess(self.dock)
        self.proc.finished.connect(lambda *_: self.seguro(self.fatiado))
        self.proc.errorOccurred.connect(lambda *_: self.seguro(self.fatiado))
        self.proc.start(str(FATIADOR), ['--slice', '0', '--outputdir', str(pasta), str(projeto)])
        QtCore.QTimer.singleShot(20 * 60 * 1000, lambda p=self.proc: p is self.proc and p.kill())  # teto de 20 min
        self.botao_fatiar.setEnabled(False)
        self.fatiar_txt.setText('Fatiando… pode levar alguns minutos. Dá para continuar marcando.')

    def fatiado(self):
        if self.proc is None:
            return
        codigo, self.proc = self.proc.exitCode(), None
        self.botao_fatiar.setEnabled(True)
        info, resultado = self.fatiando, self.fatiando['pasta'] / 'result.json'
        saida = {'resultado': 'FALHOU', 'pecas': info['pecas'], 'perfil': info['perfil'], 'projeto': str(info['projeto'])}
        try:
            if not resultado.exists():
                raise RuntimeError('o Bambu Studio não iniciou, foi interrompido ou passou do teto de 20 min (não gravou result.json)')
            r = json.loads(resultado.read_text(encoding='utf-8'))
            if codigo != 0 or r.get('return_code', 0) != 0 or not r.get('sliced_plates'):
                raise RuntimeError(r.get('error_string') or f'código {codigo}')
            placa = r['sliced_plates'][0]
            tempos = placa.get('feature_type_times', {})
            suporte = tempos.get('Support', 0) + tempos.get('Support interface', 0)
            saida.update(resultado='FATIADO', gramas=round(sum(f['total_used_g'] for f in placa['filaments']), 2), tempo_s=round(placa['main_predication']),
                         tempo=hms(placa['main_predication']), suporte_s=round(suporte), gcode=str(next(info['pasta'].glob('plate_*.gcode'))))
            self.fatiar_txt.setText(f"{saida['gramas']:.1f} g · {saida['tempo']} · " + (f'suporte: {hms(suporte)} do tempo' if suporte else 'sem suporte gerado') + f"\n{info['perfil']}")
        except Exception as e:
            saida['erro'] = str(e)
            self.fatiar_txt.setText(f'Fatiamento falhou: {e}')
        self.gravar('bancada_fatiado.json', saida)

    def visivel(self, obj):
        """Objeto e todos os seus pais estão visíveis (marca some junto com a peça isolada)."""
        return obj.ViewObject.Visibility and all(p.ViewObject.Visibility for p in obj.InListRecursive if p in self.objetos)

    def hit(self, pos):
        info = self.view.getObjectInfo(tuple(map(int, pos)), 0.0)
        if not info:
            return None
        obj = self.doc.getObject(info.get('Object') or '')
        if obj is None or not hasattr(obj, 'getGlobalPlacement'):
            return None
        ponto = [float(info[k]) for k in ('x', 'y', 'z')]
        local = obj.getGlobalPlacement().inverse().multVec(App.Vector(*ponto))
        return {'objeto': obj.Name, 'ponto': ponto, 'local': [local.x, local.y, local.z]}

    def pressionar(self, pos):
        Gui.Selection.clearSelection()
        hit = self.hit(pos)
        if not hit:
            self.status.setText('Clique sobre a superfície de uma peça.')
            return
        self.drag = {'inicio': tuple(pos), 'ultimo': tuple(pos), 'hit': hit, 'pontos': [hit['ponto']], 'locais': [hit['local']]}

    def arrastar(self, pos):
        if self.drag is None or self.modo.currentIndex() != 2:
            return
        last = self.drag['ultimo']
        if (pos[0] - last[0]) ** 2 + (pos[1] - last[1]) ** 2 < 9:
            return
        hit = self.hit(pos)
        if not hit or hit['objeto'] != self.drag['hit']['objeto']:
            self.soltar(last)  # não une segmentos através de um vão ou de outra peça
            return
        self.drag['pontos'].append(hit['ponto'])
        self.drag['locais'].append(hit['local'])
        self.drag['ultimo'] = tuple(pos)
        self.desenhar()

    def soltar(self, pos):
        if self.drag is None:
            return
        drag = self.drag
        self.drag = None
        mode = self.modo.currentIndex()
        if mode == 2:
            if len(drag['pontos']) < 2:
                self.status.setText('Arraste sobre a peça para criar um traço.')
                return
            ident = self.marcas.adicionar('traco', drag['hit']['objeto'], drag['pontos'], drag['locais'])
        else:
            if sum((a - b) ** 2 for a, b in zip(pos, drag['inicio'])) > 25:
                return
            hit = self.hit(pos)
            if not hit:
                return
            if mode == 3:
                ident = self.selecionada()
                if not ident:
                    self.status.setText('Selecione somente um ponto na lista para mover.')
                    return
                self.marcas.mover(ident, hit['objeto'], hit['ponto'], hit['local'])
            elif mode == 1:
                ident = self.marcas.adicionar('ponto', hit['objeto'], [hit['ponto']], [hit['local']])
            else:
                return
        self.atualizar(ident)
        self.status.setText(f'Marca {ident} salva. Você pode continuar marcando ou escolher Navegar.')
        if mode in (1, 2) and self.pedir_anotacao.isChecked():
            self.anotar(ident)

    def no_marca(self, ident, pts, selected=False, nota=''):
        node = coin.SoSeparator()
        # Os pontos já estão em coordenadas globais. A cena pode deixar uma
        # transformação de peça ativa antes da camada de anotações.
        reset = coin.SoResetTransform()
        reset.whatToReset = coin.SoResetTransform.TRANSFORM
        node.addChild(reset)
        pick = coin.SoPickStyle()
        pick.style = coin.SoPickStyle.UNPICKABLE
        node.addChild(pick)
        color = coin.SoBaseColor()
        color.rgb = (1., 0.20, 0.75) if selected else (1., 0.82, 0.05)
        node.addChild(color)
        style = coin.SoDrawStyle()
        style.pointSize = 11
        style.lineWidth = 4
        node.addChild(style)
        coords = coin.SoCoordinate3()
        coords.point.setValues(0, len(pts), pts)
        node.addChild(coords)
        if len(pts) > 1:
            shape = coin.SoLineSet()
            shape.numVertices.setValue(len(pts))
        else:
            shape = coin.SoPointSet()
            shape.numPoints = 1
        node.addChild(shape)
        shift = coin.SoTranslation()
        shift.translation = pts[0]
        node.addChild(shift)
        font = coin.SoFont()
        font.name = 'Arial'
        font.size = 22
        node.addChild(font)
        text = coin.SoText2()
        linhas = ['  ' + ident]
        if nota:  # post-it: até 3 linhas da nota ao lado da letra
            dobra = textwrap.wrap(' '.join(nota.split()), 44)
            linhas += ['  ' + l for l in dobra[:3]]
            if len(dobra) > 3:
                linhas[-1] += ' …'
        text.string.setValues(0, len(linhas), linhas)
        node.addChild(text)
        return node

    def desenhar(self):
        self.layer.removeAllChildren()
        sel = set(self.selecionadas())
        for m in self.marcas.itens:
            obj = self.doc.getObject(m['objeto'])
            if obj and self.visivel(obj):
                self.layer.addChild(self.no_marca(m['id'], m['pontos'], m['id'] in sel, m['descricao'] if self.notas_na_peca.isChecked() else ''))
        if self.drag and self.modo.currentIndex() == 2:
            self.layer.addChild(self.no_marca('…', self.drag['pontos'], True))
        self.view.redraw()

    def diagnostico(self):
        return {'versao_freecad': App.Version()[:3], 'documento': self.doc.FileName, 'pecas': [o.Name for o in self.objetos],
                'painel_visivel': self.dock.isVisible(), 'modo': self.modo.currentText(), 'vista': list(self.view.getSize()),
                'marcas': [m['id'] for m in self.marcas.itens], 'cliques': self.captura.contagem,
                'marcas_desenhadas': self.layer.getNumChildren(), 'peca_isolada': self.pecas.currentText(),
                'lista_de_pecas': [self.pecas.itemText(i) for i in range(self.pecas.count())],
                'medidas': {n: self.valor(n) for n in self.celulas}, 'fatiando': self.proc is not None}

    def vistas(self):
        """Quatro vistas de conferência (render_de_conferencia.md) em PNG, sem mexer na câmera do operador."""
        camera = self.view.getCameraOrientation()
        oposta = lambda: self.view.setCameraOrientation(App.Rotation(App.Vector(0, 0, 1), 180) * self.view.getCameraOrientation())
        for nome, apontar in [('iso', self.view.viewIsometric), ('iso_oposto', lambda: (self.view.viewIsometric(), oposta())),
                              ('topo', self.view.viewTop), ('frente', self.view.viewFront)]:
            apontar()
            self.view.fitAll()
            self.view.saveImage(str(self.root / f'bancada_{nome}.png'), 1280, 900, 'Current')
        self.view.setCameraOrientation(camera)
        self.view.fitAll()

    def pronto(self):
        self.view.fitAll()
        self.gravar('bancada_pronto.json', self.diagnostico())
        self.status.setText('Pronto: clique na peça para criar A, B, C…')

    def comando(self):
        path = self.root / 'comando.json'
        if not path.exists():
            return
        try:
            texto = path.read_text(encoding='utf-8')
            path.unlink()  # antes de interpretar: comando inválido não fica repetindo erro
            cmd = json.loads(texto)
            action = cmd['acao']
            if action == 'mapa':  # opcionais: limiar (graus), parede (mm)
                self.limiar.setValue(cmd.get('limiar', self.limiar.value()))
                self.parede.setValue(cmd.get('parede', self.parede.value()))
                self.mapa()
            elif action == 'limpar_mapa':
                self.limpar_mapa()
            elif action == 'fatiar':
                self.fatiar()
            elif action == 'medida':
                self.medida(cmd['nome'], cmd['valor'])
            elif action == 'comparar':
                self.comparar(cmd['antes'], cmd['depois'])
            elif action == 'isolar':
                idx = self.pecas.findText(cmd['peca'])
                if idx < 0:
                    raise ValueError(f"Peça {cmd['peca']!r} não está na lista.")
                self.pecas.setCurrentIndex(idx)
            elif action == 'diagnostico':
                self.gravar('bancada_diagnostico.json', self.diagnostico())
            elif action == 'capturar':  # imagem da própria vista 3D, não do desktop
                self.view.saveImage(str(self.root / 'bancada.png'), 1280, 900, 'Current')
            elif action == 'vistas':
                self.vistas()
            elif action == 'recarregar':  # código do painel mudou
                import sys
                self.fechar()
                importlib.reload(sys.modules[__name__]).iniciar(self.root, self.doc.FileName)
            elif action == 'reabrir':  # o .FCStd mudou no disco (ex.: editado por FreeCADCmd)
                if Gui.getDocument(self.doc_name).Modified:
                    raise RuntimeError('Documento com alterações não salvas na janela; não reabri.')
                arquivo = self.doc.FileName
                self.fechar()
                App.closeDocument(self.doc_name)
                iniciar(self.root, arquivo)
            else:
                raise ValueError(f'Ação desconhecida: {action}')
        except Exception:
            (self.root / 'bancada_erro.log').write_text(traceback.format_exc(), encoding='utf-8')

    def conferir_documento(self):
        if self.doc_name not in App.listDocuments():
            self.fechar()

    def fechar(self):
        if self.closed:
            return
        self.closed = True
        self.timer.stop()
        self.timer_docs.stop()
        if hasattr(self, 'captura'):
            QtWidgets.QApplication.instance().removeEventFilter(self.captura)
        if self.proc is not None:
            proc, self.proc = self.proc, None
            proc.kill()
            self.gravar('bancada_fatiado.json', {'resultado': 'FALHOU', 'erro': 'fatiamento interrompido: o painel foi fechado ou recarregado'})
        try:  # com o documento já fechado, vista e viewer não existem mais
            self.viewer.unsetCursor()
            self.view.getSceneGraph().removeChild(self.mapa_no)
            self.view.getSceneGraph().removeChild(self.layer)
        except (AttributeError, RuntimeError, ReferenceError):
            pass
        self.layer.unref()
        self.mapa_no.unref()
        self.dock.hide()
        self.dock.deleteLater()


def iniciar(projeto, documento, importar=()):
    """projeto: pasta onde ficam marcas.json e os arquivos da bancada. documento: caminho do .FCStd."""
    projeto = Path(projeto)
    try:
        anterior = getattr(App, 'BancadaMarcas', None)
        mesmo = anterior is not None and anterior.root == projeto
        historico = copy.deepcopy(anterior.marcas.historico) if mesmo else []
        dados = copy.deepcopy(anterior.marcas.dados) if mesmo else None
        pedir = False
        if anterior is not None:
            try:
                pedir = anterior.pedir_anotacao.isChecked()
            except RuntimeError:
                pass
            if not anterior.closed:
                anterior.fechar()
        r = Bancada(projeto, documento, importar)
        if r.marcas.dados == dados:
            r.marcas.historico = historico
        r.pedir_anotacao.setChecked(pedir)
        App.BancadaMarcas = r
        return r
    except Exception:
        projeto.mkdir(parents=True, exist_ok=True)
        (projeto / 'bancada_erro.log').write_text(traceback.format_exc(), encoding='utf-8')
        App.Console.PrintError(traceback.format_exc() + '\n')
