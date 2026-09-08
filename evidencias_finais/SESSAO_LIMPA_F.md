<!-- Relatorio de sessao limpa F, preservado no repositorio. Operador: subagente
sem historico deste projeto, modelo claude-opus-5. Pacote sob ensaio: 2.0.0,
montado e nunca executado, hash 1c988264. Tarefa: ESCREVER o proprio script que
roda dentro do Blender, e nao apenas executar os exemplos. Nada aqui foi editado
por mim: os sete achados estao como ele escreveu, inclusive o que contesta uma
afirmacao fundadora do produto e que eu remedi do zero. -->

# Relatório — escrever o meu próprio script de dentro do Blender

**Pasta da habilidade (só leitura):** `C:\Users\marce\AppData\Local\Temp\pacote_intocado_20`
(pacote 2.0.0, `bl_ferramentas` 1.5.0, conforme `INVENTARIO.json`)
**Pasta de trabalho:** `C:\Users\marce\AppData\Local\Temp\sessao_limpa_F`
**Interpretador do hospedeiro:** `C:\Users\marce\AppData\Local\Temp\ensaio_isolado_20\venv\Scripts\python.exe`
**Blender:** 5.2.1 LTS, sempre headless, via `blender-launcher.exe` achado pelo alias de
execução do Windows. **Nada foi enviado ao socket 127.0.0.1:9876; `scripts/mcp_blender.py`
não foi executado nem importado.** A sessão aberta do usuário não foi tocada.

Todas as execuções usaram `--factory-startup` (padrão de `roda_blender.py`, linha 98),
`PYTHONDONTWRITEBYTECODE=1` e `PACOTE_MODELAGEM_3D` apontando para a pasta da habilidade.

---

## 1. Comandos, na íntegra, com diretório e código de saída

Abreviações usadas só nesta seção, para as linhas caberem:
`PY = C:\Users\marce\AppData\Local\Temp\ensaio_isolado_20\venv\Scripts\python.exe`
`PKG = C:\Users\marce\AppData\Local\Temp\pacote_intocado_20`
`W = C:\Users\marce\AppData\Local\Temp\sessao_limpa_F`
Nenhum caminho relativo foi usado como argumento; os `cd` abaixo são reais.

### C1 — localizar o Blender
```
diretório: PKG
PYTHONDONTWRITEBYTECODE=1 "PY" scripts/roda_blender.py --achar
```
**Código de saída: 0.** Devolveu
`C:\Users\marce\AppData\Local\Microsoft\WindowsApps\blender-launcher.exe`,
`"como": "alias de execucao do Windows"`.

### C2 — hash dos meus dois argumentos, ANTES de rodar
```
diretório: W
sha256sum params_geometria.json params_criterios.json | tee hashes_antes.txt
```
**Código de saída: 0.**

### C3 — caminho de SUCESSO (a execução principal)
```
diretório: W
PYTHONDONTWRITEBYTECODE=1 PACOTE_MODELAGEM_3D="PKG" "PY" "PKG\scripts\roda_blender.py" \
  "W\meu_ensaio_flange.py" \
  --resultado "W\resultado_ok.json" \
  --passa-resultado \
  --exigir veredito_global=ATENDIDO \
  --args "W\params_geometria.json" "W\params_criterios.json" \
  > "W\chamada_ok.json" 2>&1
```
**Código de saída: 0.** `estado: "OK"`, `exigencia: {campo: veredito_global,
esperado: ATENDIDO, obtido: ATENDIDO}`, 2,05 s,
`codigo_de_saida_do_lancador: 0`, `saida_do_processo: ""` (vazio).

### C4 — os dois argumentos, DEPOIS de rodar
```
diretório: W
sha256sum params_geometria.json params_criterios.json | tee hashes_depois.txt
diff hashes_antes.txt hashes_depois.txt
```
**Código de saída: 0** (diff vazio → nenhum dos dois foi tocado).

### C5 — caminho de FALHA acidental (registrada por honestidade)
Ao criar o arquivo de parâmetros de falha por heredoc, o `\\` do JSON foi colapsado
para `\` e o arquivo saiu inválido. O comando foi o mesmo padrão de C6, com
`params_geometria_falha_json_invalido.json` no lugar do primeiro argumento.
**Código de saída: 1.** `estado: "VEREDITO_NEGATIVO"`; o meu script gravou
`veredito_global: "ERRO"`, `erro.tipo: "RuntimeError"`, mensagem
`parametros ilegiveis: JSONDecodeError: Invalid \escape: line 9 column 12 (char 128)`.
Isto não estava planejado, e é evidência a favor do contrato: **erro que eu não previ
também chegou ao chamador com código != 0.** Artefatos preservados em
`chamada_falha_acidental_json_invalido.json` e
`resultado_falha_acidental_json_invalido.json`.

### C6 — caminho de FALHA DELIBERADA (exceção dentro do meu script)
```
diretório: W
PYTHONDONTWRITEBYTECODE=1 PACOTE_MODELAGEM_3D="PKG" "PY" "PKG\scripts\roda_blender.py" \
  "W\meu_ensaio_flange.py" \
  --resultado "W\resultado_falha.json" \
  --passa-resultado \
  --exigir veredito_global=ATENDIDO \
  --args "W\params_geometria_falha.json" "W\params_criterios.json" \
  > "W\chamada_falha.json" 2>&1
```
**Código de saída: 1.** Detalhe na seção 3.

### C7 — caminho de REPROVAÇÃO POR CRITÉRIO, com `--exigir`
```
diretório: W
... roda_blender.py "W\meu_ensaio_flange.py" \
  --resultado "W\resultado_criterio_reprovado.json" --passa-resultado \
  --exigir veredito_global=ATENDIDO \
  --args "W\params_geometria.json" "W\params_criterios_impossivel.json" \
  > "W\chamada_criterio_com_exigir.json" 2>&1
```
**Código de saída: 1.** `estado: VEREDITO_NEGATIVO`, `veredito_global: NAO_ATENDIDO`.

### C8 — o MESMO relatório reprovado, SEM `--exigir`
```
diretório: W
... roda_blender.py "W\meu_ensaio_flange.py" \
  --resultado "W\resultado_criterio_reprovado2.json" --passa-resultado \
  --args "W\params_geometria.json" "W\params_criterios_impossivel.json" \
  > "W\chamada_criterio_sem_exigir.json" 2>&1
```
**Código de saída: 0**, com `veredito_global: NAO_ATENDIDO` dentro. Confirma na medida
o aviso de `referencias/verificar.md`, linhas 154-156, e de
`referencias/mapa_de_ferramentas.md`, linha 43.

### C9 — controle: sem `--passa-resultado` e sem campo `saida`
```
diretório: W
... roda_blender.py "W\meu_ensaio_flange.py" \
  --resultado "W\resultado_sem_destino.json" --exigir veredito_global=ATENDIDO \
  --args "W\params_geometria.json" "W\params_criterios.json" \
  > "W\chamada_sem_passa_resultado.json" 2>&1
```
**Código de saída: 1.** `estado: "SEM_RESULTADO"`, `codigo_de_saida_do_lancador: 2`
(o `SystemExit(2)` do meu script), `saida_do_processo: ""`, **`segundos: 300.29`**.

### C10 — validar a FORMA do arquivo de requisitos
```
diretório: PKG
PYTHONDONTWRITEBYTECODE=1 "PY" scripts/valida_requisitos.py "W\req.json"
```
**Código de saída: 0.** `estado: "OK"`, 4 requisitos, 0 problemas,
`tipos_que_exigem_referencia: []`.

### C11 — verificador topológico sobre o artefato entregue
```
diretório: PKG
PYTHONDONTWRITEBYTECODE=1 "PY" verificadores/check_mesh.py \
  --malha "W\flange.stl" --json "W\check_mesh.json"
```
**Código de saída: 0.**

### C12 — verificador de intenção sobre o artefato entregue
```
diretório: PKG
PYTHONDONTWRITEBYTECODE=1 "PY" verificadores/check_intent.py \
  --malha "W\flange.stl" --requisitos "W\req.json" --json "W\check_intent.json"
```
**Código de saída: 0.**

### C13 — integridade da pasta da habilidade (proteção, não medida da peça)
Script de uma linha rodado pelo `PY` (saída em `integridade_do_pacote.txt`), conferindo
o sha256 de cada uma das 23 entradas de `INVENTARIO.json` e contando os arquivos no disco.
**Código de saída: 0.** `divergencias = []`, `arquivos_no_disco = 24`
(23 do manifesto + `INVENTARIO.json`), `extras_fora_do_manifesto = []`,
nenhum `__pycache__` e nenhum `.pyc`.

---

## 2. Arquivos criados

Todos em `C:\Users\marce\AppData\Local\Temp\sessao_limpa_F\`, todos com caminho absoluto.

| Arquivo | O que é |
|---|---|
| `meu_ensaio_flange.py` | **o meu script**, que roda dentro do Blender (conteúdo abaixo) |
| `params_geometria.json` | 1º argumento meu — parâmetros da peça |
| `params_criterios.json` | 2º argumento meu — critérios de julgamento |
| `params_geometria_falha.json` | 1º argumento da execução de falha deliberada |
| `params_criterios_impossivel.json` | 2º argumento da execução de reprovação por critério |
| `params_geometria_falha_json_invalido.json` | o arquivo malformado de C5, preservado |
| `resultado_ok.json` | relatório gravado pelo meu script no caminho de sucesso |
| `resultado_falha.json` | relatório gravado pelo meu script no caminho de falha deliberada |
| `resultado_criterio_reprovado.json`, `resultado_criterio_reprovado2.json` | relatórios `NAO_ATENDIDO` |
| `resultado_falha_acidental_json_invalido.json` | relatório da falha não planejada de C5 |
| `chamada_ok.json`, `chamada_falha.json`, `chamada_falha_acidental_json_invalido.json`, `chamada_criterio_com_exigir.json`, `chamada_criterio_sem_exigir.json`, `chamada_sem_passa_resultado.json` | o que o **chamador** (`roda_blender.py`) devolveu em cada execução |
| `flange.stl` | o artefato, 14.084 bytes, sha256 `746dc7c471ae6672378c01038fbe6dc0e45dcbda12fefdb330a004b8475ab650` |
| `req.json` | requisitos declarados para o `check_intent.py` |
| `check_mesh.json`, `check_intent.json` | saídas dos verificadores |
| `hashes_antes.txt`, `hashes_depois.txt`, `hashes_falha_antes.txt`, `hashes_falha_depois.txt` | prova de que os argumentos não foram sobrescritos |
| `integridade_do_pacote.txt` | conferência do `INVENTARIO.json` |
| `RELATORIO.md` | este arquivo |

`flange_falha.stl` **não existe**, e isso é correto: a falha deliberada acontece antes
da exportação, então nenhum artefato ficou amarrado a uma execução que falhou.

### Conteúdo de `meu_ensaio_flange.py`

```python
# -*- coding: utf-8 -*-
"""meu_ensaio_flange.py - script PROPRIO, escrito nesta sessao, que roda DENTRO do
Blender headless, constroi uma peca simples e MEDE a malha dela.

RODA DENTRO DO BLENDER:
  blender --background --factory-startup --python meu_ensaio_flange.py -- \
      <params_geometria.json> <params_criterios.json> [--resultado-em <rel.json>]

Chamado, na pratica, por `scripts/roda_blender.py --passa-resultado`.

CONTRATO QUE ESTE ARQUIVO CUMPRE, e de onde cada obrigacao saiu:

1. Grava o relatorio SEMPRE, inclusive no caminho de erro, e sai com codigo != 0
   quando o veredito nao e ATENDIDO. Fonte: `cenarios/gera_cenario.py`, linhas
   200-216 ("grava SEMPRE, inclusive no caminho de erro"). Motivo medido em
   `scripts/roda_blender.py`, linhas 12-19: o `blender-launcher.exe` DESANEXA o
   processo, devolve 0 e stdout vazio; sem arquivo nao houve resultado.
2. Le o destino do relatorio pela bandeira NOMEADA `--resultado-em`, que manda sobre
   o campo do arquivo de configuracao. Fonte: `cenarios/gera_cenario.py`, linhas
   155-168 e `scripts/roda_blender.py`, linha 47 (ROTULO_DO_RESULTADO).
   Ela e nomeada, e nao posicional, exatamente para nao sobrescrever o SEGUNDO
   argumento do chamador (roda_blender.py, linhas 109-113).
3. Confere a versao da biblioteca com `F.confere_versao`, que so roda dentro do
   Blender. Fonte: SKILL.md, tabela "Onde conferir a versao, e onde nao da".
4. MEDE em vez de presumir: exige FINISHED dos operadores, separa medida topologica
   (mede_malha) de medida de forma (caixa envolvente medida contra a acordada), e
   repassa o campo `limite` de cada medida. Fonte: SKILL.md, "Tres regras que valem
   em todas as rotas", e `referencias/verificar.md`, "As tres familias".
5. Atravessa o furo com FOLGA (altura = T * folga_de_corte), nunca com altura igual a
   parede. Fonte: `referencias/criar_e_parametrizar.md`, Passo 1, regra 1.

O que este script NAO prova: nada sobre passagem do furo, imprimibilidade, parede
minima ou encaixe. Ver SKILL.md, "O que este pacote nao faz".
"""
import json
import os
import sys
import traceback

# Nao poluir a pasta da habilidade com __pycache__: o import de bl_ferramentas sai de
# lá e a pasta e de leitura apenas nesta sessao.
sys.dont_write_bytecode = True

import bpy                                                        # noqa: E402
from mathutils import Vector                                      # noqa: E402

ROTULO_DO_RESULTADO = "--resultado-em"

# Caminho da pasta da habilidade. Fica em variavel de ambiente para o script nao
# carregar caminho absoluto de outra maquina cravado no codigo.
PACOTE = os.environ.get(
    "PACOTE_MODELAGEM_3D",
    r"C:\Users\marce\AppData\Local\Temp\pacote_intocado_20")
sys.path.insert(0, os.path.join(PACOTE, "scripts"))

import bl_ferramentas as F                                        # noqa: E402

VERSAO_ESPERADA = "1.5.0"      # de INVENTARIO.json: versao_de_bl_ferramentas


def destino_do_resultado(argv, do_arquivo=None):
    """Bandeira NOMEADA manda; campo do arquivo de configuracao e o reserva."""
    if ROTULO_DO_RESULTADO in argv:
        i = argv.index(ROTULO_DO_RESULTADO)
        if i + 1 < len(argv) and argv[i + 1]:
            return argv[i + 1]
    return do_arquivo


def arquivos_posicionais(argv):
    """Os argumentos do CHAMADOR: tudo antes da primeira bandeira."""
    fora = []
    for a in argv:
        if a.startswith("--"):
            break
        fora.append(a)
    return fora


def _estados(retorno):
    return sorted(retorno) if hasattr(retorno, "__iter__") else [str(retorno)]


def _exige_finished(nome, retorno):
    """Operador que devolve CANCELLED nao levanta excecao e nao faz nada.

    Medido no proprio pacote: bl_ferramentas.py, linhas 13-16."""
    est = _estados(retorno)
    if "FINISHED" not in est:
        raise RuntimeError("o operador %s nao devolveu FINISHED: %s" % (nome, est))
    return est


def caixa_de_mundo(nome_do_objeto):
    """Caixa envolvente em coordenada de MUNDO, com as dimensoes medidas.

    Em MUNDO de proposito: bl_ferramentas.py, linhas 11-14, mede que criterio
    aplicado em coordenada LOCAL seleciona zero faces onde o de mundo seleciona uma.
    """
    obj = bpy.data.objects.get(nome_do_objeto)
    if obj is None:
        raise F.ErroDePrecondicao("nao existe objeto chamado %r" % nome_do_objeto)
    cantos = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    mn = [min(c[i] for c in cantos) for i in range(3)]
    mx = [max(c[i] for c in cantos) for i in range(3)]
    return {"minimo": [round(v, 6) for v in mn],
            "maximo": [round(v, 6) for v in mx],
            "dimensoes": [round(mx[i] - mn[i], 6) for i in range(3)],
            "limite": ("a caixa envolvente prova SO o envelope externo. Ela nao diz "
                       "nada sobre furo, ranhura ou forma interna.")}


def constroi_flange(p):
    """Placa retangular com UM furo central passante, por diferenca booleana.

    Todo valor vem de parametro: nenhuma constante magica.
    Fonte da regra: referencias/criar_e_parametrizar.md, Passo 1, regra 2.
    """
    nome = p["nome"]
    L, P, T, d = float(p["L"]), float(p["P"]), float(p["T"]), float(p["d"])
    folga = float(p["folga_de_corte"])
    if folga <= 1.0:
        raise F.ErroDePrecondicao(
            "folga_de_corte = %r: corte com altura IGUAL ou menor que a parede produz "
            "faces coincidentes e degenera. A referencia usa T * 3 "
            "(criar_e_parametrizar.md, Passo 1, regra 1)." % folga)

    # cena de fabrica vem com objetos; limpa para medir so a peca
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    _exige_finished("mesh.primitive_cube_add",
                    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, T / 2)))
    corpo = bpy.context.active_object
    corpo.name = nome
    corpo.scale = (L, P, T)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    _exige_finished(
        "mesh.primitive_cylinder_add",
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=int(p["lados_do_cilindro"]), radius=d / 2.0,
            depth=T * folga, location=(0, 0, T / 2)))
    furo = bpy.context.active_object
    furo.name = nome + "_furo"

    bpy.context.view_layer.objects.active = corpo
    mod = corpo.modifiers.new(name="furo", type="BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.object = furo
    mod.solver = "EXACT"
    _exige_finished("object.modifier_apply",
                    bpy.ops.object.modifier_apply(modifier=mod.name))

    # o cortador tem que sair da cena: senao ele entra na contagem de corpos e no STL
    bpy.ops.object.select_all(action="DESELECT")
    furo.select_set(True)
    bpy.context.view_layer.objects.active = furo
    bpy.ops.object.delete(use_global=False)
    bpy.context.view_layer.objects.active = corpo

    if corpo.modifiers:
        raise RuntimeError("sobrou modificador ativo em %r: a assinatura nao cobriria "
                           "o resultado dele (bl_ferramentas.exporta_malha, "
                           "aviso_de_modificador)" % nome)
    return corpo


def julga(rel, criterio, predicado, descricao):
    """Um criterio, um predicado EXECUTAVEL, um veredito.

    Fonte da forma: cenarios/ensaio_preenchimento.py, funcao `julga` e o comentario
    de `passo` (linhas 51-60): `estado: OK` diz so que nao houve excecao, e nao que a
    medida passou."""
    try:
        ok = bool(predicado())
        erro = None
    except Exception as e:                                        # noqa: BLE001
        ok, erro = False, "%s: %s" % (type(e).__name__, e)
    rel["vereditos"].append({"criterio": criterio, "descricao": descricao,
                             "passou": ok, "erro_no_predicado": erro})
    return ok


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    posicionais = arquivos_posicionais(argv)

    rel = {"script": os.path.abspath(__file__),
           "argumentos_recebidos": argv,
           "argumentos_posicionais": posicionais,
           "passos": [], "vereditos": [],
           "aviso": ("dimensoes deste ensaio escolhidas para o exercicio; nenhuma "
                     "provem de projeto real")}

    # o destino do relatorio e resolvido ANTES de qualquer coisa que possa falhar:
    # sem destino nao ha como o chamador saber que falhou
    cfg_geo, cfg_crit = {}, {}
    try:
        if len(posicionais) >= 1:
            cfg_geo = json.load(open(posicionais[0], encoding="utf-8"))
        if len(posicionais) >= 2:
            cfg_crit = json.load(open(posicionais[1], encoding="utf-8"))
    except Exception as e:                                        # noqa: BLE001
        cfg_geo = cfg_geo if isinstance(cfg_geo, dict) else {}
        rel["erro_ao_ler_parametros"] = "%s: %s" % (type(e).__name__, e)

    saida = destino_do_resultado(argv, cfg_geo.get("saida"))
    if not saida:
        # sem destino, o unico canal que resta e stdout, e ele nao chega ao chamador
        print(json.dumps({"veredito_global": "ESPEC_INVALIDA",
                          "motivo": "informe --resultado-em ou 'saida' no arquivo de "
                                    "parametros de geometria"}, ensure_ascii=False))
        raise SystemExit(2)
    saida = os.path.abspath(saida)
    rel["arquivo_de_resultado"] = saida

    try:
        if rel.get("erro_ao_ler_parametros"):
            raise RuntimeError("parametros ilegiveis: " + rel["erro_ao_ler_parametros"])
        if len(posicionais) != 2:
            raise F.ErroDePrecondicao(
                "este script exige DOIS argumentos posicionais: "
                "<params_geometria.json> <params_criterios.json>. Recebidos: %r"
                % posicionais)

        rel["parametros_geometria"] = cfg_geo
        rel["parametros_criterios"] = cfg_crit
        rel["versao_blender"] = bpy.app.version_string
        rel["versao_ferramentas"] = F.VERSAO
        rel["conferencia_de_versao"] = F.confere_versao(VERSAO_ESPERADA)

        nome = cfg_geo["nome"]
        obj = constroi_flange(cfg_geo)
        rel["objetos_na_cena"] = [o.name for o in bpy.data.objects]

        # --- falha deliberada, para provar o caminho de erro do contrato ----------
        falha = cfg_geo.get("modo_de_falha")
        if falha == "excecao_deliberada":
            raise RuntimeError(
                "falha DELIBERADA pedida por modo_de_falha=%r no arquivo de "
                "parametros de geometria. Existe para provar que o caminho de erro "
                "chega ao chamador com codigo de saida != 0." % falha)
        if falha not in (None, "", "excecao_deliberada"):
            raise F.ErroDePrecondicao(
                "modo_de_falha %r nao existe. Vocabulario fechado: None ou "
                "'excecao_deliberada'." % falha)

        # --- medida topologica ---------------------------------------------------
        malha = F.mede_malha(nome)
        rel["passos"].append({"passo": "mede_malha", "estado": "OK", "resultado": malha})

        # --- medida de forma (separada da topologica) ----------------------------
        caixa = caixa_de_mundo(nome)
        rel["passos"].append({"passo": "caixa_de_mundo", "estado": "OK",
                              "resultado": caixa})

        assin = F.assinatura(nome)
        rel["passos"].append({"passo": "assinatura", "estado": "OK", "resultado": assin})

        # --- artefato ------------------------------------------------------------
        stl = os.path.abspath(cfg_geo["stl"])
        exp = F.exporta_malha(nome, stl)
        rel["passos"].append({"passo": "exporta_malha", "estado": "OK", "resultado": exp})

        # --- vereditos, com predicado executavel ---------------------------------
        c = cfg_crit.get("criterios") or {}
        if not c:
            raise F.ErroDePrecondicao(
                "o segundo arquivo tem que trazer a chave 'criterios' com os limites "
                "a julgar. Sem criterio declarado nao ha veredito: so medida.")
        tol = float(c["tol_caixa_mm"])
        esperada = [float(v) for v in c["caixa_esperada_mm"]]
        rel["tolerancia_da_caixa_mm"] = tol
        rel["fonte_da_tolerancia"] = c.get("fonte_da_tolerancia")

        julga(rel, "sem_aresta_aberta",
              lambda: malha["arestas_abertas"] <= int(c["arestas_abertas_max"]),
              "arestas_abertas <= %s" % c["arestas_abertas_max"])
        julga(rel, "sem_nao_manifold",
              lambda: malha["arestas_nao_manifold"] <= int(c["arestas_nao_manifold_max"]),
              "arestas_nao_manifold <= %s" % c["arestas_nao_manifold_max"])
        julga(rel, "sem_degeneracao",
              lambda: malha["faces_degeneradas"] <= int(c["faces_degeneradas_max"]),
              "faces_degeneradas <= %s" % c["faces_degeneradas_max"])
        julga(rel, "um_corpo",
              lambda: malha["n_componentes_conexos"] == int(c["n_componentes_esperado"]),
              "n_componentes_conexos == %s (contagem inteira, sem tolerancia)"
              % c["n_componentes_esperado"])
        desvios = [round(abs(caixa["dimensoes"][i] - esperada[i]), 6) for i in range(3)]
        rel["desvios_da_caixa_mm"] = desvios
        rel["desvio_maximo_da_caixa_mm"] = max(desvios)
        julga(rel, "envelope",
              lambda: max(desvios) <= tol,
              "desvio maximo da caixa <= %s mm (medido contra %s)" % (tol, esperada))
        julga(rel, "artefato_no_disco",
              lambda: exp["existe"] and exp["bytes"] > 0,
              "o STL existe no disco e nao esta vazio")

        rel["n_criterios"] = len(rel["vereditos"])
        rel["n_falhos"] = sum(1 for v in rel["vereditos"] if not v["passou"])
        rel["veredito_global"] = "ATENDIDO" if rel["n_falhos"] == 0 else "NAO_ATENDIDO"
        rel["alcance"] = (
            "medido: topologia da malha na cena, envelope externo em coordenada de "
            "mundo, e existencia do STL entregue. NAO medido: passagem do furo, "
            "parede minima, silhueta, imprimibilidade, folga de encaixe. O artefato "
            "no disco tem que ser conferido por check_mesh.py / check_intent.py, "
            "fora do Blender.")
    except Exception as e:                                        # noqa: BLE001
        rel["veredito_global"] = "ERRO"
        rel["erro"] = {"tipo": type(e).__name__, "mensagem": str(e)}
        rel["traceback"] = traceback.format_exc()[-2000:]
        rel.setdefault("n_criterios", len(rel["vereditos"]))
        rel.setdefault("n_falhos", sum(1 for v in rel["vereditos"] if not v["passou"]))

    os.makedirs(os.path.dirname(saida) or ".", exist_ok=True)
    open(saida, "w", encoding="utf-8").write(
        json.dumps(rel, ensure_ascii=False, indent=1))
    if rel["veredito_global"] != "ATENDIDO":
        raise SystemExit(1)
    return 0


if __name__ == "__main__":
    main()
```

### Conteúdo dos meus dois argumentos

`params_geometria.json` (1º argumento):
```json
{
 "nome": "Flange", "L": 40.0, "P": 24.0, "T": 6.0, "d": 8.0,
 "folga_de_corte": 3.0, "lados_do_cilindro": 64,
 "stl": "C:\\Users\\marce\\AppData\\Local\\Temp\\sessao_limpa_F\\flange.stl",
 "modo_de_falha": null,
 "nota": "folga_de_corte = 3 reproduz o T * 3 de referencias/criar_e_parametrizar.md, Passo 1, regra 1"
}
```

`params_criterios.json` (2º argumento):
```json
{
 "criterios": {
  "arestas_abertas_max": 0, "arestas_nao_manifold_max": 0,
  "faces_degeneradas_max": 0, "n_componentes_esperado": 1,
  "caixa_esperada_mm": [40.0, 24.0, 6.0], "tol_caixa_mm": 0.05,
  "fonte_da_tolerancia": "referencias/verificar.md, tabela 'Tolerancia que o verificador le' ..."
 },
 "nota": "contagens sao criterios INTEIROS e nao levam tolerancia"
}
```

---

## 3. Prova de que o mecanismo de retorno funciona nos DOIS sentidos

O mecanismo é o de `scripts/roda_blender.py`: **o script de dentro escreve um arquivo
de resultado, e o chamador espera esse arquivo**; `--exigir CAMPO=VALOR` transforma o
veredito gravado em código de saída.

### Sentido de sucesso (C3)

| Onde | O que veio |
|---|---|
| chamador | código de saída **0**, `estado: "OK"`, `exigencia.obtido = "ATENDIDO"` |
| relatório do meu script | `veredito_global: "ATENDIDO"`, `n_criterios: 6`, `n_falhos: 0` |
| disco | `flange.stl`, 14.084 bytes, sha256 `746dc7c4…5ab650` |
| `saida_do_processo` | **vazio** — confirma que stdout não serve de canal |

### Sentido de falha, com a falha PROVOCADA por mim (C6)

Fiz o meu script falhar de propósito pelo campo `modo_de_falha: "excecao_deliberada"`
do meu 1º arquivo de parâmetros, que levanta `RuntimeError` **depois** de a peça já
estar construída. O que o chamador recebeu, na íntegra dos campos relevantes:

```
código de saída do processo chamador (roda_blender.py): 1
estado = "VEREDITO_NEGATIVO"
motivo = "o script rodou e o relatorio traz veredito_global = 'ERRO', e a exigencia
          era 'ATENDIDO'. Resultado legivel nao e resultado aprovado."
codigo_de_saida_do_lancador = 1
exigencia = {"campo": "veredito_global", "esperado": "ATENDIDO", "obtido": "ERRO"}
segundos = 1.96
saida_do_processo = ""            <- vazio: sem o arquivo, nada teria chegado
```
e, dentro do relatório que o **meu** script gravou em `resultado_falha.json`:
```
veredito_global = "ERRO"
erro = {"tipo": "RuntimeError",
        "mensagem": "falha DELIBERADA pedida por modo_de_falha='excecao_deliberada' ..."}
objetos_na_cena = ["Flange"]      <- a peça existia; a falha é posterior
passos = []                       <- nenhuma medida foi creditada
n_criterios = 0, n_falhos = 0
traceback = "... meu_ensaio_flange.py, line 240, in main / RuntimeError: falha DELIBERADA ..."
```
`flange_falha.stl` **não foi criado**: a falha impediu a exportação, então não há
artefato órfão amarrado a uma execução que falhou.

### Terceiro sentido, de bônus: reprovação de critério sem exceção nenhuma (C7/C8)

| Execução | `--exigir`? | `veredito_global` gravado | código de saída |
|---|---|---|---|
| C7 | sim | `NAO_ATENDIDO` (`envelope` reprovado, desvio 10,0 mm) | **1** |
| C8 | **não** | `NAO_ATENDIDO` (o mesmo) | **0** |

Isto separa três coisas que o pacote insiste em não confundir: erro operacional
(`ERRO`), reprovação de medida (`NAO_ATENDIDO`) e aprovação (`ATENDIDO`) — e mede o
aviso de `verificar.md` linhas 154-156: **sem `--exigir`, relatório reprovado sai com
código 0.**

### Quarto sentido: o script nem chegar a gravar (C9)

Sem `--passa-resultado` e sem campo `saida`, o meu script imprime `ESPEC_INVALIDA` em
stdout e sai com 2. O chamador devolveu `estado: "SEM_RESULTADO"`, código de saída 1,
e `saida_do_processo` **vazio** — a mensagem que eu imprimi foi perdida, exatamente
como o pacote prevê. Sem arquivo, não houve resultado.

---

## 4. Os meus dois argumentos, e a prova de que nenhum foi sobrescrito

Passei **dois** arquivos meus, como argumentos posicionais, via
`--args <geometria.json> <criterios.json>`.

Que o script recebeu os dois, na ordem, e que a bandeira do resultado veio **depois**
e **nomeada** (de `resultado_ok.json`):
```
argumentos_recebidos    = [".../params_geometria.json", ".../params_criterios.json",
                           "--resultado-em", ".../resultado_ok.json"]
argumentos_posicionais  = [".../params_geometria.json", ".../params_criterios.json"]
arquivo_de_resultado    = ".../resultado_ok.json"     <- terceiro caminho, distinto dos dois
```

Hashes, antes e depois da execução de sucesso (`hashes_antes.txt` vs `hashes_depois.txt`,
`diff` vazio, C4):

| Arquivo | sha256 antes | sha256 depois |
|---|---|---|
| `params_geometria.json` | `f3b5c8835d7f6c5731098cd733a4375c973ce84edda021db399566972c9a29c0` | idêntico |
| `params_criterios.json` | `5e8e4a894b18e93f054de47040ed5af0e64fa1c19f75bcb20cabec8d2f693b9e` | idêntico |

E na execução de falha (`hashes_falha_antes.txt` vs `hashes_falha_depois.txt`, `diff` vazio):

| Arquivo | sha256 |
|---|---|
| `params_geometria_falha.json` | `1a87cdb1799aeab994b16dab75157cf04f67e6840fd09760712f722f9ead6115` (inalterado) |
| `params_criterios.json` | `5e8e4a894b18e93f054de47040ed5af0e64fa1c19f75bcb20cabec8d2f693b9e` (inalterado) |

Nenhum dos dois foi tocado, nem no caminho de sucesso nem no de falha. É o defeito que
`roda_blender.py`, linhas 109-113, diz ter corrigido ao trocar o caminho do resultado
de posicional para nomeado — e aqui ele está medido com **dois** argumentos, que é a
configuração que discrimina o erro (com um só argumento, o defeito antigo não aparecia).

---

## 5. Todo número medido, com a tolerância usada e de onde ela saiu

### Peça construída
Placa 40 × 24 × 6 mm, com um furo central de Ø8 mm, feito por diferença booleana
(`solver = "EXACT"`) com cilindro de 64 lados e altura `T × 3 = 18 mm`.
A folga de corte `T × 3` sai de `referencias/criar_e_parametrizar.md`, Passo 1, regra 1
(«O cilindro do furo tem altura `T * 3`, não `T`»). Dimensões escolhidas para o
exercício; nenhuma provém de projeto real.

### Medido DENTRO do Blender (`F.mede_malha`, `caixa_de_mundo`, `F.assinatura`)

| Medida | Valor | Critério | Tolerância e procedência |
|---|---|---|---|
| `arestas_abertas` | **0** | ≤ 0 | contagem inteira — **sem tolerância**, por `verificar.md`: «Tipo de contagem não precisa de tolerância» |
| `arestas_nao_manifold` | **0** | ≤ 0 | idem |
| `arestas_soltas` | **0** | (informativo) | idem |
| `faces_degeneradas` | **0** | ≤ 0 | limiar de área `1e-9` — **padrão de `bl_ferramentas.mede_malha`**, parâmetro `area_minima`, não declarado por mim; o próprio retorno traz `limite_de_area_usado: 1e-09` |
| `n_componentes_conexos` | **1** | == 1 | contagem inteira, sem tolerância |
| `faces` / `vertices` | **72** / **140** | (informativo) | — |
| caixa envolvente (mundo) | **[40,0; 24,0; 6,0] mm** | desvio máx. ≤ **0,05 mm** | **0,05 mm**, de `referencias/verificar.md`, tabela «Tolerância que o verificador lê»: para o tipo `caixa` a tolerância é `tol_mm` e o valor que decide quando nada é declarado é 0,05. Declarei-a explicitamente em `params_criterios.json` em vez de herdá-la, porque `verificar.md` avisa: «Não declarar não é "sem margem": é aceitar a da terceira coluna» |
| desvio máximo da caixa | **0,0 mm** | ≤ 0,05 | — |
| assinatura da geometria | `c2c1cd824624b0b754cf82a0ce7bc0f999c4446615cb33674ff4da4b19504952` | — | arredondamento de **6 casas**, `CASAS` padrão de `bl_ferramentas` |
| sha256 do STL | `746dc7c471ae6672378c01038fbe6dc0e45dcbda12fefdb330a004b8475ab650` | — | — |
| bytes do STL | **14.084** | > 0 | — |
| operador de exportação | `wm.stl_export` → `["FINISHED"]` | FINISHED exigido | exigência do próprio `bl_ferramentas.exporta_malha` |
| `modificadores_ativos` | **[]** | vazio | condição que eu impus, porque `exporta_malha` avisa que a assinatura não cobre resultado de modificador |

Veredito do meu script: **6 critérios, 0 falhos, `ATENDIDO`.**

### Medido FORA do Blender, sobre o artefato no disco — `check_mesh.py` (C11)

| Medida | Valor |
|---|---|
| triângulos | 280 |
| vértices antes / depois de soldar | 840 / **140** (bate com os 140 vértices medidos na cena) |
| `fechada_watertight` | **true** |
| `euler` | **0** |
| `arestas_abertas` / `> 2 faces` / degeneradas / duplicadas | 0 / 0 / 0 / 0 |
| `orientacao_consistente` | true |
| `n_componentes_conexos` | 1 |
| `volume_mm3` | **5458,891** |
| `caixa_mm` | [40,0; 24,0; 6,0] |
| `apto_para_booleana` / `volume_confiavel` | true / true |
| `precisao_no_kernel_de_malha` | `float64 via Mesh64` |
| `status_kernel_malha` | `Error.NoError` — e o próprio verificador avisa que **isso não é oráculo de validade** |

Tolerâncias em `check_mesh.py`: as contagens são exatas; o limiar de faceta
degenerada é `1e-12` **cravado no fonte** (`check_mesh.py`, linha **46**:
`degeneradas = int((areas <= 1e-12).sum())`), não configurável e não declarado na
documentação — note que é **diferente** do `1e-9` usado dentro do Blender por
`mede_malha`. Duas ferramentas do mesmo pacote medem "degenerada" com limiares
mil vezes distintos, e nenhuma referência aponta isso.

### Medido FORA do Blender — `check_intent.py` (C12), 4 requisitos declarados em `req.json`

| `id` | `tipo` | Medido | Esperado | Tolerância usada | Procedência da tolerância | Estado |
|---|---|---|---|---|---|---|
| `envelope` | `caixa` | [40,0; 24,0; 6,0] | [40,0; 24,0; 6,0] | `tol_mm = 0,05`, maior desvio 0,0 | **declarada por mim**, igual ao padrão da tabela de `verificar.md` | APROVADA |
| `um_corpo` | `n_solidos` | 1 | 1 | **nenhuma** (contagem exata) | `verificar.md`: contagem não leva tolerância | APROVADA |
| `um_furo_no_meio_da_espessura` | `n_furos_no_plano` (eixo z, plano 3,0) | 1 furo, centro (−0,0; 0,0), área 50,1848 mm², Ø equivalente **7,9936 mm**, circularidade **0,9992** | 1 | **nenhuma** para a contagem | idem | APROVADA |
| `volume_com_o_furo` | `volume` | 5458,891 mm³ | 5458,891345 mm³ | `tol_mm3 = 1,0`, desvio **0,0 mm³** | **declarada por mim**. O padrão do verificador é `max(1,0; 1% do esperado)` = 54,6 mm³, que seria 50× mais frouxo; usei o piso 1,0 do próprio padrão | APROVADA |

Como cheguei ao volume esperado, **antes** de medir (para não calibrar a tolerância no
resultado): o cortador é um prisma de 64 lados, não um cilindro ideal, logo a área do
polígono inscrito é `½·n·r²·sen(2π/n) = ½·64·4²·sen(5,625°) = 50,18477584 mm²`;
volume `= 40·24·6 − 50,18477584·6 = 5760 − 301,1086550 = 5458,891345 mm³`.
O verificador mediu 50,1848 mm² para a mesma área — coincide. O Ø equivalente de
7,9936 mm (e não 8,0000) é consequência esperada do polígono inscrito, não desvio de
processo.

**check_intent: 4 requisitos, 4 aprovados, 0 reprovados, 0 não verificados,
`atende_ao_pedido: true`, código de saída 0.**

### Alcance declarado, que é obrigação do pacote

- Foram medidas: topologia da malha (na cena e no artefato), envelope externo,
  volume, contagem de corpos, contagem de furos no plano z = 3,0 e circularidade
  naquele plano.
- **Uma seção prova aquele plano.** O requisito `n_furos_no_plano` mediu **z = 3,0** e
  nada além dele.
- **Não foi verificado que o furo é passante.** É exatamente a linha que `SKILL.md`
  reserva para isto. O que dá para deduzir a partir de medida, e apresentado como
  dedução e não como veredito de verificador: a malha é fechada, com orientação
  consistente, **1** componente conexo e `euler = 0`. Como `euler = 2 − 2·gênero` para
  superfície fechada e conexa, isso implica **gênero 1**, isto é **um túnel**
  atravessando o sólido — coerente com um furo passante (o `SKILL.md` cita o caso
  análogo de `euler = −2` para dois túneis). Reforça, mas não prova, que o volume
  medido bate com o calculado assumindo passagem, com desvio de 0,0 mm³ contra uma
  tolerância declarada de 1,0 mm³ — o que limita material residual dentro do furo a
  menos de 1 mm³.
- **Não foram medidos:** parede mínima, silhueta, folga de encaixe (`A_CALIBRAR`,
  sem valor calibrado no pacote), imprimibilidade. Nada aqui aprova a peça para
  fabricação.

---

## 6. Onde a pasta me deixou na mão

A pasta **não** está vazia neste quesito. Sete pontos, com arquivo e linha. Dois deles
são afirmações medidas do pacote que **não reproduziram** nesta máquina.

### 6.1 O `--help` de `roda_blender.py` descreve o contrato ERRADO — e é o contrato antigo, defeituoso

`scripts/roda_blender.py`, linhas **193-197**, texto de ajuda de `--passa-resultado`:

> «acrescenta o caminho de `--resultado` como **ultimo argumento** do script, para nao
> ter que repeti-lo dentro do arquivo de parametros»

O código faz outra coisa: linhas **45-47** definem
`ROTULO_DO_RESULTADO = "--resultado-em"` e as linhas **114-119** acrescentam o caminho
**nomeado**. As próprias linhas **109-113** explicam que a versão posicional foi
removida porque, «com dois argumentos do chamador, o script gravava sobre o SEGUNDO
argumento dele». Ou seja: **o texto de ajuda ainda ensina o contrato que o comentário
logo acima declara corrigido**, e é justamente o contrato que quebra no cenário desta
tarefa (dois argumentos). Quem faz o movimento mais natural — rodar `--help` primeiro —
recebe a instrução de ler `argv[-1]`, e escreve um script que sobrescreve o próprio
segundo argumento. Correção: um argumento a menos de trabalho, trocar o texto de ajuda
pelo nome real da bandeira.

### 6.2 Duas afirmações medidas sobre o código de saída do lançador NÃO reproduziram

`scripts/roda_blender.py`, linhas **12-14**: «`blender-launcher.exe` DESANEXA o
processo e devolve imediatamente, com codigo de saida 0 e stdout VAZIO»; e a mensagem
de `SEM_RESULTADO`, linhas **152-154**: «O codigo de saida do lancador e 0 mesmo
quando o Blender falha, entao ele nao serve de prova». O mesmo em
`referencias/mapa_de_ferramentas.md`, linhas **25-27**.

**Medido nesta máquina, três pontos, Blender 5.2.1 LTS, o mesmo
`blender-launcher.exe` que o `--achar` devolve:**

| Execução | `SystemExit` do meu script | `codigo_de_saida_do_lancador` |
|---|---|---|
| C3, sucesso | 0 | **0** |
| C6, falha deliberada | 1 | **1** |
| C9, sem destino de resultado | 2 | **2** |

O código de saída **foi propagado fielmente nas três**. A afirmação de que ele «é 0
mesmo quando o Blender falha» está impressa dentro do próprio JSON que trazia
`codigo_de_saida_do_lancador: 2` — uma mensagem se contradizendo com o dado ao lado.
A outra metade da afirmação (stdout vazio) **reproduziu**: `saida_do_processo` veio
vazio em todas as execuções, e isso é o que sustenta o contrato de arquivo. Não estou
dizendo que o contrato de arquivo é dispensável — é mais robusto de qualquer forma —
estou dizendo que a evidência declarada para ele não se reproduz aqui, e um agente
que a leia como universal vai descrever mal o próprio ambiente. Alcance da minha
medida: três execuções, uma máquina, um lançador.

### 6.3 `SEM_RESULTADO` custa o tempo-limite inteiro, calado

Em C9 o processo do Blender já havia terminado (`proc.communicate()` retornou e o
código de saída chegou), e ainda assim `roda` ficou **300,29 s** no laço de espera das
linhas **141-143** de `roda_blender.py`, que só olha se o arquivo apareceu e o relógio.
Nada na documentação avisa que o caminho de falha mais comum — script que não gravou —
é o mais lento, nem que se deve baixar `--tempo-limite` para diagnosticar. O laço
poderia parar assim que o processo morresse. Cinco minutos por tentativa, em silêncio.

### 6.4 A tabela de rotas do `SKILL.md` não aponta para o contrato do script de dentro

O contrato **está** documentado, e bem: `referencias/mapa_de_ferramentas.md`, linha
**68** em diante, seção «O contrato do script que roda DENTRO do Blender», com molde de
código, o nome real de `--resultado-em` e até o aviso do `__pycache__`. O problema é de
localização: a tabela «Rotas e onde está cada receita» do `SKILL.md` descreve essa
referência como «que ferramenta existe, o que ela exige, o que **não** existe», e o
`SKILL.md` manda «Carregue **uma** referência por vez, a da rota em uso». Não há linha
para «escrever o meu próprio script que roda dentro do Blender», que era literalmente a
minha tarefa. Resultado prático: eu reconstruí o contrato lendo o fonte de
`cenarios/gera_cenario.py` (linhas 172-216) e `cenarios/ensaio_preenchimento.py`
(linhas 139-202) **antes** de descobrir que a página já o explicava. A própria seção
admite a origem do problema («Esta parte não estava escrita em nenhuma referência, e
uma sessão limpa precisou extraí-la lendo o código dos cenários») — a lacuna foi
fechada no lugar certo e o índice não foi atualizado. Uma linha nova na tabela do
`SKILL.md` resolve.

### 6.5 Como importar `bl_ferramentas` de um script que vive FORA do pacote

Nenhum exemplo cobre esse caso, que é o único caso possível quando a pasta é somente
leitura. Os dois cenários resolvem com
`AQUI = os.path.dirname(os.path.abspath(__file__))` e
`sys.path.insert(0, os.path.dirname(AQUI) + "/scripts")`
(`ensaio_preenchimento.py`, linhas **41-43**), que só funciona porque eles moram dentro
de `cenarios/`. Para o meu script tive que inventar o mecanismo (variável de ambiente
`PACOTE_MODELAGEM_3D` com reserva embutida). Adivinhação, funcionou, mas é minha e não
da pasta. O aviso do `__pycache__` de `mapa_de_ferramentas.md` (linhas 122-126) é
excelente e eu o apliquei — só não está no lugar onde o import é ensinado.

### 6.6 O pacote não tem medidor de caixa envolvente DENTRO do Blender

`bl_ferramentas.FUNCOES` (linhas **1410-1427**) não expõe nenhuma função de caixa
envolvente, e nenhuma referência menciona uma. `check_mesh.py` e `check_intent.py`,
fora do Blender, medem `caixa_mm` sem problema. Como o envelope externo é o requisito
mais elementar da rota de criar, tive que escrever `caixa_de_mundo` eu mesmo — o que me
obrigou também a escolher, sozinho, medir em coordenada de **mundo** e não local. A
escolha é claramente a certa (é o defeito nº 1 medido em `bl_ferramentas.py`, linhas
**11-14**), mas foi minha, não da receita.

### 6.7 Dois limiares diferentes de "face degenerada", sem ninguém avisar

`bl_ferramentas.mede_malha` usa `area_minima = 1e-9` (linha **1052**) e o devolve como
`limite_de_area_usado` — comportamento exemplar. `check_mesh.py` usa `1e-12`, cravado
no fonte, não parametrizável e não reportado. `referencias/verificar.md` lista
`faces_degeneradas` como a mesma medida nas duas ferramentas («área nula»), sem dizer
que os limiares diferem por três ordens de magnitude. No meu caso as duas mediram 0 e
a divergência não decidiu nada, mas uma peça com faces muito pequenas seria classificada
diferente pelas duas — e a referência levaria a crer que uma confirma a outra.

### Coisas que funcionaram exatamente como escritas, e merecem ser ditas

`roda_blender.py --achar`; `--passa-resultado` e `--exigir` combinados;
`F.confere_versao("1.5.0")` (e o `SKILL.md` acertou ao avisar que ela não roda no
Python do hospedeiro); `F.exporta_malha`, que exigiu `FINISHED`, removeu destino
anterior e devolveu hash do arquivo junto da assinatura da geometria;
`valida_requisitos.py` antes do `check_intent.py`, na ordem que `verificar.md` manda;
a tabela de tolerâncias de `verificar.md`, que bateu com o que `check_intent.py`
realmente usou; e o aviso de que `--saida`/`--json` relativos gravam dentro do pacote
(`criar_e_parametrizar.md`), que me fez usar caminho absoluto em tudo desde o primeiro
comando. Nenhum exemplo que eu executei deixou de rodar como estava escrito.

---

## 7. Quanto tempo, em passos, até a primeira execução bem-sucedida

**14 passos, e a primeira execução do meu script passou na primeira tentativa** — zero
execuções falhas não intencionais do script em si.

| # | Passo |
|---|---|
| 1 | listar os arquivos da pasta da habilidade |
| 2 | ler `SKILL.md` |
| 3 | ler `referencias/criar_e_parametrizar.md` e `scripts/roda_blender.py` inteiro |
| 4 | contar linhas e indexar a API de `bl_ferramentas.py` |
| 5 | ler o cabeçalho de `bl_ferramentas.py` |
| 6 | ler `mede_malha`, `exporta_malha`, `executa_tarefa`, `FUNCOES` |
| 7 | ler o cabeçalho dos dois cenários e procurar o tratamento de `argv` |
| 8 | ler o `main()` dos dois cenários — foi aqui que o contrato ficou claro |
| 9 | ler `extrai_tolerancias.py`, `INVENTARIO.json` e o cabeçalho de `check_mesh.py` |
| 10 | ler `referencias/verificar.md` inteiro; rodar `roda_blender.py --achar` (**C1**) |
| 11 | ler `assinatura`; conferir que não havia `__pycache__` na pasta |
| 12 | escrever `meu_ensaio_flange.py` |
| 13 | escrever os dois arquivos de parâmetros e hashear (**C2**) |
| 14 | **executar (C3) → `ATENDIDO`, código de saída 0** |

Onze dos treze passos preparatórios foram leitura, e nove desses onze foram leitura de
**código-fonte**, não de documentação. Foi o passo 8 (o `main()` dos cenários) que
tornou possível escrever o script — e ele não era o passo que a tabela de rotas do
`SKILL.md` me mandaria dar (ver 6.4). Só descobri a seção «O contrato do script que
roda DENTRO do Blender» de `mapa_de_ferramentas.md` **depois** da primeira execução
bem-sucedida, ao verificar se as minhas queixas eram justas — e metade delas não era.

---

## 8. Declaração sobre escrita dentro da pasta da habilidade

**Não escrevi nada dentro de `C:\Users\marce\AppData\Local\Temp\pacote_intocado_20`,
nem por acidente.** Provado, não afirmado (C13, saída em `integridade_do_pacote.txt`):

- os **23** arquivos do `INVENTARIO.json` conferem no sha256, **zero divergências**;
- há **24** arquivos no disco — os 23 do manifesto mais o próprio `INVENTARIO.json` —
  e **nenhum extra fora do manifesto**;
- **nenhum `__pycache__` e nenhum `.pyc`**, apesar de o meu script importar
  `bl_ferramentas` de dentro do pacote: prevenido com `sys.dont_write_bytecode = True`
  antes do import e com `PYTHONDONTWRITEBYTECODE=1` em todos os processos.

Os comandos dos verificadores foram executados **com o diretório corrente na pasta do
pacote** (é como as receitas estão escritas), mas **todos** os `--malha`, `--json`,
`--requisitos`, `--resultado` e `--args` usaram caminho **absoluto** para a pasta de
trabalho, que é a precaução que `criar_e_parametrizar.md` pede depois de uma sessão
anterior ter criado `<pacote>/varredura/` seguindo os exemplos ao pé da letra.

E, quanto à regra que não podia ser quebrada: `scripts/mcp_blender.py` não foi
executado nem importado, nenhuma conexão foi aberta com `127.0.0.1:9876`, e todas as
sete execuções de Blender foram `--background --factory-startup`, em processo próprio,
sem abrir nem salvar nenhum `.blend`. A sessão do Blender do usuário permaneceu intacta.
