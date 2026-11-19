"""Marcas (pontos e traços com letra e nota), em mm; sem dependência do FreeCAD.

Arquivo `marcas.json` do projeto. O agente lê este JSON; não precisa de print.
`pontos` = coordenadas globais do documento; `locais` = no referencial do objeto
(já descontado o Placement), que é o que vale para analisar a malha/sólido.
"""
import copy
import json
import math
from pathlib import Path


def letra(numero):
    text = ''
    while numero:
        numero, resto = divmod(numero - 1, 26)
        text = chr(65 + resto) + text
    return text


class Marcas:
    def __init__(self, path, origem):
        self.path = Path(path)
        self.historico = []
        self.dados = {'versao': 2, 'origem': origem, 'unidade': 'mm', 'marcas': []}
        if self.path.exists():
            self.dados = json.loads(self.path.read_text(encoding='utf-8'))
            if self.dados.get('origem') != origem:
                raise ValueError(f"As marcas de {self.path.name} pertencem a outro documento ({self.dados.get('origem')}).")

    @property
    def itens(self):
        return self.dados['marcas']

    def salvar(self):
        tmp = self.path.with_suffix('.tmp')
        tmp.write_text(json.dumps(self.dados, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
        tmp.replace(self.path)

    def alterar(self, func):
        antes = copy.deepcopy(self.dados)
        try:
            result = func()
            self.salvar()
        except Exception:
            self.dados = antes
            raise
        self._nota = None  # qualquer outra alteração encerra a digitação em curso
        self.historico.append(antes)
        self.historico = self.historico[-50:]
        return result

    def obter(self, ident):
        return next(x for x in self.itens if x['id'] == ident)

    def validar(self, tipo, obj, pontos):
        if tipo not in ('ponto', 'traco') or not obj:
            raise ValueError('Tipo ou objeto inválido.')
        if len(pontos) < (1 if tipo == 'ponto' else 2) or (tipo == 'ponto' and len(pontos) != 1):
            raise ValueError('Quantidade de pontos inválida.')
        pts = [[float(v) for v in p] for p in pontos]
        if any(len(p) != 3 or not all(math.isfinite(v) for v in p) for p in pts):
            raise ValueError('Coordenadas inválidas.')
        return pts

    def adicionar(self, tipo, obj, pontos, locais=None):
        pts = self.validar(tipo, obj, pontos)
        loc = self.validar(tipo, obj, locais) if locais else pts

        def change():
            numero = 1
            ocupadas = {item['id'] for item in self.itens}
            while letra(numero) in ocupadas:  # menor letra livre: apagou B, a próxima é B
                numero += 1
            ident = letra(numero)
            self.itens.append({'id': ident, 'tipo': tipo, 'objeto': obj, 'pontos': pts, 'locais': loc, 'descricao': ''})
            return ident
        return self.alterar(change)

    def mover(self, ident, obj, ponto, local=None):
        item = self.obter(ident)
        if item['tipo'] != 'ponto':
            raise ValueError('Mover aplica-se a pontos. Para traço, apague e redesenhe.')
        pts = self.validar('ponto', obj, [ponto])
        loc = self.validar('ponto', obj, [local]) if local else pts
        self.alterar(lambda: item.update(objeto=obj, pontos=pts, locais=loc))

    def descrever(self, ident, texto):
        item = self.obter(ident)
        if item['descricao'] == texto:
            return
        if getattr(self, '_nota', None) == ident:  # digitação contínua = um só passo de Desfazer
            item['descricao'] = texto
            self.salvar()
            return
        self.alterar(lambda: item.update(descricao=texto))
        self._nota = ident

    def apagar_lote(self, identificadores):
        ids = set(identificadores)
        if not ids:
            return
        for ident in ids:
            self.obter(ident)
        self.alterar(lambda: self.dados.update(marcas=[item for item in self.itens if item['id'] not in ids]))

    def desfazer(self):
        if not self.historico:
            return
        atual = self.dados
        self.dados = self.historico[-1]
        try:
            self.salvar()
        except Exception:
            self.dados = atual
            raise
        self.historico.pop()


if __name__ == '__main__':  # python marcas.py  -> autoteste sem FreeCAD
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        m = Marcas(Path(td) / 'marcas.json', 'Doc.FCStd')
        assert [m.adicionar('ponto', 'Box', [[0, 0, 0]]) for _ in range(3)] == ['A', 'B', 'C']
        m.apagar_lote(['B'])
        assert m.adicionar('ponto', 'Box', [[1, 2, 3]], [[0, 0, 3]]) == 'B'
        assert m.obter('B')['locais'] == [[0.0, 0.0, 3.0]]
        n = len(m.historico)
        for texto in ('n', 'no', 'nota'):
            m.descrever('B', texto)
        assert len(m.historico) == n + 1 and Marcas(m.path, 'Doc.FCStd').obter('B')['descricao'] == 'nota'
        m.apagar_lote(['A', 'C'])
        m.desfazer()
        assert [x['id'] for x in m.itens] == ['A', 'C', 'B']
        assert Marcas(m.path, 'Doc.FCStd').itens == m.itens
        try:
            Marcas(m.path, 'Outro.FCStd')
            raise SystemExit('deveria recusar outro documento')
        except ValueError:
            pass
    print('marcas: PASSOU')
