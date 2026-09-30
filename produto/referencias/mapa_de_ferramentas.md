# Mapa de ferramentas: o que existe, o que exige, o que não existe

Medidas feitas nesta máquina em 07/09/2026, salvo data indicada. Ausência de auxiliar
não é impossibilidade geométrica. As versões do pacote e de `bl_ferramentas` ficam só
em `INVENTARIO.json`. O que o pacote não faz: ver `SKILL.md`, "O que este pacote não faz".

**Ambiente e dependências**

- **Blender** 5.2.1 LTS, Python 3.13.13. Confirmar: `python scripts/roda_blender.py
  --achar`, depois um script que imprima `bpy.app.version_string`.
- **Python do hospedeiro** (fora do Blender), todos importáveis nesta máquina e
  confirmados por `python -c "import <módulo>"`: `build123d` (com OCP; varredura de
  família), `trimesh` e `numpy` (verificadores, `check_mesh.py`), `manifold3d` e
  `shapely` (verificadores e `secoes.py`), `lib3mf` (escritor de 3MF), `scipy`
  (`piso_espessura.py`). `verificadores/matriz.py` roda só com a biblioteca padrão.
- **Não pressupostos:** `rtree`, `matplotlib`, `fast_simplification`. Se uma receita
  parecer precisar deles, a receita está errada.

## Rodar o Blender em processo separado

Entrada preferida: `scripts/trabalho_blender.py --script ... --resultado ...`, com
`executar(config)` no script. Ele chama `scripts/roda_blender.py` e usa
`scripts/executa_com_relatorio.py`, invólucro que captura traceback inclusive em erro de
sintaxe ou de configuração (não reescreva o invólucro a cada tarefa). Roda sempre em
processo headless separado e nunca se conecta a sessão aberta. Execução não é aprovação
geométrica. Ver a seção 5 de `sessao_e_edicao_guiada.md` e o exemplo executável.

### Três armadilhas do lançador

Instalação pela Microsoft Store:

1. `C:\Program Files\WindowsApps\...\blender.exe` **não é executável direto**: dá
   "Acesso negado", tanto pelo shell quanto pelo Python. O caminho que funciona é o
   alias de execução `%LOCALAPPDATA%\Microsoft\WindowsApps\blender-launcher.exe`.
2. O launcher devolve **stdout vazio, sempre**: medido em 8 modos de execução
   diferentes, 0 bytes em stdout e 0 em stderr nos oito. Ler stdout não funciona.
3. O código de saída é prova **negativa**, não positiva. Medido em oito modos:

| O que o script de dentro faz | Código devolvido |
|---|---|
| termina normalmente, ou `sys.exit(0)` | 0 |
| `sys.exit(1)` / `sys.exit(2)` | **1** / **2**, propagados fielmente |
| levanta exceção não tratada | **0** |
| erro de sintaxe no script | **0** |
| importa módulo que não existe | **0** |
| chama operador do Blender que não existe | **0** |

O código propaga a saída **deliberada** do script e engole toda falha **imprevista**.
**Código não zero é sinal confiável de falha; código zero não é sinal de nada.**

### O contrato: o script grava um arquivo de resultado

Por isso o **script de dentro escreve um arquivo de resultado**, e quem chama espera esse
arquivo. Sem arquivo, não houve resultado. O lançador desanexa, devolve código 0 e stdout
vazio: quem levanta uma exceção e não a grava não deixa vestígio nenhum no chamador.
`scripts/roda_blender.py` implementa isso:

```bash
python scripts/roda_blender.py meu_script.py --resultado saida.json
python scripts/roda_blender.py --achar          # só localiza o executável
```

Duas bandeiras existem por causa de defeito medido, não por conveniência:

| Bandeira | Sem ela | Com ela |
|---|---|---|
| `--passa-resultado` | o caminho do resultado tem que ser escrito **duas vezes** — aqui e dentro do arquivo de parâmetros — e nada confere se as duas grafias coincidem; divergindo, sai `SEM_RESULTADO` com o arquivo existindo em outra pasta | o caminho vai numa bandeira **nomeada**, `--resultado-em <path>`, acrescentada ao fim dos seus argumentos, e é escrito num lugar só. `gera_cenario.py` e `ensaio_preenchimento.py` leem essa bandeira. É nomeada, não posicional: com dois argumentos seus, ler `argv[1]` faria o script gravar sobre o **segundo argumento seu**, e o chamador esperaria outro arquivo |
| `--exigir CAMPO=VALOR` | **qualquer** JSON legível sai como `OK`, com código de saída **zero** — inclusive um relatório que diz `"veredito_global": "FALHOU"` | o estado só é `OK` se o relatório trouxer aquele campo com aquele valor; senão, `VEREDITO_NEGATIVO` e saída não zero |

O caminho de `--resultado` é resolvido para **absoluto** antes de tudo: o script roda
com outro diretório corrente dentro do Blender, e caminho relativo faz os dois lados
apontarem para arquivos diferentes.

Como módulo:

```python
from roda_blender import roda
r = roda("meu_script.py", "saida.json", args=["param.json"], tempo_limite_s=300,
         passa_resultado=True, exigir=("veredito_global", "ATENDIDO"))
# r["estado"] ∈ OK | SEM_BLENDER | SEM_CENA | SEM_RESULTADO | TEMPO_ESGOTADO
#              | RESULTADO_ILEGIVEL | FALHA_AO_INICIAR | VEREDITO_NEGATIVO
```

`roda_blender.py` sai **1** em qualquer estado diferente de `OK`.
`TEMPO_ESGOTADO` **não prova** que o script parou dentro do Blender. Inspecione antes
de repetir. E `OK` **sem** `--exigir` prova só que o arquivo é legível: legível não é
aprovado.

`SEM_RESULTADO` é o caminho de falha mais comum (script que não gravou). Depois de o
processo sair, a espera pelo arquivo dura uma carência de 5 s e desiste; medido: **7 s**
no total, em vez dos 300 s do tempo-limite. O retorno traz
`segundos_de_espera_pelo_arquivo`, para o custo ser visível.

`--cena <arquivo.blend>` abre um `.blend` existente em vez da cena inicial, e é assim
que se retoma a peça salva numa execução anterior para rodar a próxima variante sobre
ela. `--sem-fabrica` desliga o `--factory-startup`; deixe ligado nos ensaios, porque é
o que impede herdar preferências e complementos do usuário.

### Script de dentro que não usa `trabalho_blender.py`

Os cenários do pacote seguem este protocolo. O script de dentro precisa fazer quatro
coisas:

```python
import json, os, sys

# 1. ler os argumentos DEPOIS de `--`
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
cfg = json.load(open(argv[0], encoding="utf-8")) if argv else {}

# 2. a bandeira NOMEADA `--resultado-em` traz o caminho do resultado, quando se
#    usa --passa-resultado. Nomeada, e nao posicional: com dois argumentos seus,
#    ler `argv[1]` faria o script gravar sobre o seu segundo argumento.
saida = None
if "--resultado-em" in argv:
    i = argv.index("--resultado-em")
    saida = argv[i + 1] if i + 1 < len(argv) else None
saida = saida or cfg.get("saida")
if not saida:
    raise SystemExit("informe o destino do relatorio")

rel = {"passos": []}
try:
    ...                                   # o trabalho
    rel["veredito_global"] = "ATENDIDO"
except Exception as e:                    # 3. capturar E GRAVAR: nao so levantar
    rel["veredito_global"] = "ERRO"
    rel["motivo"] = "%s: %s" % (type(e).__name__, e)

# 4. ESCREVER o arquivo, sempre — inclusive no caminho de erro
os.makedirs(os.path.dirname(saida) or ".", exist_ok=True)
open(saida, "w", encoding="utf-8").write(json.dumps(rel, ensure_ascii=False, indent=1))
```

O `cfg` sai de `argv[0]` **só** quando ele não começa com `--`: senão a própria bandeira
seria lida como arquivo de parâmetros.

Combine com `--exigir veredito_global=ATENDIDO` do lado de fora: aí o erro que você
gravou vira código de saída não zero, em vez de um `OK` sobre um relatório que diz
`ERRO`. `cenarios/gera_cenario.py` e `cenarios/ensaio_preenchimento.py` são os dois
exemplos completos deste contrato. Medido: com `saida_blend` apontando para um caminho
ocupado por diretório, `gera_cenario.py` grava `veredito_global: "ERRO"` com tipo e
mensagem, e o invocador devolve `VEREDITO_NEGATIVO`.

**Como importar quando o seu script vive FORA do pacote** (o único caso possível se a
pasta é somente leitura). Os dois cenários do pacote resolvem com
`os.path.dirname(os.path.abspath(__file__))`, e isso **só funciona porque eles moram
dentro de `cenarios/`**. Para um script seu, em outra pasta, o caminho tem que vir de
fora — a forma mais simples é uma variável de ambiente com reserva explícita:

```python
import os, sys
sys.dont_write_bytecode = True
pacote = os.environ.get("PACOTE_MODELAGEM_3D") or r"<raiz do pacote>"
sys.path.insert(0, os.path.join(pacote, "scripts"))
import bl_ferramentas as F
```

O caminho é relativo à **raiz do pacote**, sem prefixo `produto/` (esse prefixo existe
só na árvore de desenvolvimento e não resolve no pacote extraído).

**Antes de importar, desligue o bytecode.** `sys.path.insert(...)` seguido de
`import bl_ferramentas` faz o Python criar `<pacote>/scripts/__pycache__`, dentro da
pasta que o pacote declara somente-leitura. Ponha `sys.dont_write_bytecode = True`
**antes** do import, ou exporte `PYTHONDONTWRITEBYTECODE=1` no processo que lança o
Blender.

## Sessão aberta (socket 9876, mcp_blender.py)

| Via | Quando usar | Limite |
|---|---|---|
| **headless** (`--background --factory-startup`) | todo teste, toda receita reproduzível | sem interface: sobreposições e viewport **não existem**, e o histórico se comporta diferente (ver `recuperar_salvar_exportar.md`) |
| **sessão aberta** | quando o usuário está trabalhando e quer orientação sobre a própria cena | a cena é do usuário: não carregue outro arquivo, não encerre, cuidado com alterações não salvas |

O transporte da sessão aberta é um socket em `127.0.0.1:9876` mantido pelo complemento
dentro do Blender. Protocolo: `{"type": "<comando>", "params": {...}}` →
`{"status": "success", "result": {...}}`. O comando `get_scene_info` é leitura e serve de
teste de conexão. **Não crie outro transporte.** Como o agente descobre e usa as
ferramentas do Blender: ver `SKILL.md`, "Conectar ao Blender, por agente".

MCP sem resposta: confira handshake, se a aplicação está aberta e a versão. No
experimento, abrir a aplicação restabeleceu a conexão: falha de conexão **não** prova
complemento antigo, e reinstalar por inferência é errado.

`scripts/mcp_blender.py` roda **fora** do Blender e é o cliente do socket do complemento
(leitura incremental de JSON em socket é trecho mecânico frágil que não se improvisa).
**Somente leitura por padrão**: comando que altera a cena exige `permitir_escrita`
explícito, porque a cena é do usuário e pode ter alteração não salva.

Estados, todos medidos com controle: `OK`, `SEM_SERVIDOR`, `TEMPO_ESGOTADO`,
`RESPOSTA_ILEGIVEL`, `ERRO_DO_ADDON`, `ESCRITA_BARRADA`, `PARAMS_ILEGIVEIS`.
`TEMPO_ESGOTADO` **não prova** que o código parou dentro do Blender.

```bash
python scripts/mcp_blender.py --testa-conexao
python scripts/mcp_blender.py get_object_info --params '{"name": "Cubo"}'
```

`scripts/sessao_blender.py --diagnosticar` (hospedeiro, consulta pelo socket) é a
entrada da sessão: não altera seleção nem geometria.

## Funções de bl_ferramentas

`scripts/bl_ferramentas.py` roda **dentro** do Blender (importação: ver a seção
"Rodar o Blender em processo separado"). Cada função cobre uma etapa que erra em
silêncio. Toda função devolve fato medido e levanta `ErroDePrecondicao` em vez de operar
sobre pré-condição falsa.

| Função | Para que serve | Lacuna que ela fecha |
|---|---|---|
| `diagnostico` | modo, objeto, unidades, transformação, seleção viva, sobreposições | seleção lida de `obj.data` está desatualizada em Edit Mode |
| `assinatura` | identidade de coordenadas **e** conectividade, com cobertura declarada | hash de `.blend` não separa geometria de câmera |
| `entra_em_edicao` / `sai_de_edicao` / `limpa_selecao` | pré-condição de modo | operações de malha exigem Edit Mode |
| `seleciona_faces_por_caixa_de_mundo` | seleção por critério em coordenada de **mundo** | `calc_center_median()` é LOCAL; MEDIDO: 1 face em mundo, 0 em local |
| `le_selecao` / `confere_selecao_capturada` | seleção viva com índices e centros; confere que os índices ainda valem | índice só vale para a geometria capturada |
| `desloca_selecao` | deslocar e **medir** o efeito | MEDIDO: seleção vazia devolve `CANCELLED` e nada muda |
| `preenche_entre_limites` | volume fechado ligando dois limites, com sobreposição no material | volume que só encosta deixa ranhura, e estanqueidade não pega |
| `volume_de_material_na_caixa` | volume **exato** de material dentro de uma caixa, medido em cópia por booleana. **Devolve um `float` nu**, não dicionário — é a única função do pacote assim; tratá-la como dicionário dá `TypeError: 'float' object is not subscriptable` | é com ela que o preenchimento prova as **três** interseções antes de alterar a peça |
| `limpa_degeneracoes_na_regiao` | remover face de área nula **só** na região, com tolerância justificada | MEDIDO: a união deixa 4 faces degeneradas sem abrir borda |
| `mede_malha` | bordas, não-manifold, soltas, degeneradas **e componentes conexos** — cada um separado | "sem borda aberta" não é "sem degeneração" |
| `mede_topo_em_pontos` | altura do material contra o valor **esperado** | é a única medida aqui que pega ranhura e desnível |
| `secao_por_plano` | interseção das arestas com um plano, tratando coplanar e duplicado | inspeção independente da junção |
| `captura_regiao_protegida` / `compara_regiao_protegida` | conjunto de posições **e área** das faces inteiras dentro de uma caixa | contar faces cujos vértices caem na caixa não prova preservação; e conjunto de posições **sozinho** também não: apagando uma face de um tetraedro, os quatro vértices continuam nas faces vizinhas e 3,4641 mm² desaparecem sem o conjunto mudar (medido em 08/09/2026) |
| `marca_recuperacao` / `contexto_de_historico` / `desfaz_e_confere` / `refaz_e_confere` | histórico conferido pelo conteúdo | `ed.undo` falha de dois modos diferentes; ver `recuperar_salvar_exportar.md` |
| `salva_cena` / `exporta_malha` | entrega com hash e assinatura | recusa sobrescrever a origem por padrão |

**A caixa envolvente em coordenada de MUNDO já existe:** `diagnostico(nome)` devolve
`objeto.caixa_mundo_min` e `objeto.caixa_mundo_max`, com a matriz de mundo já aplicada,
o que evita medir em coordenada local. Não há função separada de caixa envolvente.

Booleana, STL e round-trip de malha: ver `criar_e_parametrizar.md`, booleana.

### Edição guiada (`scripts/edicao_guiada.py` e `scripts/mover_selecao.py`)

| Ferramenta | Onde roda | Para que usar / limite |
|---|---|---|
| `scripts/mover_selecao.py` | hospedeiro, MCP | translação em mm no eixo global, seleção existente; não reconstrói junções. Ver `chamadas_prontas.md` |
| `edicao_guiada.diagnostica()` | Blender | seleção viva, objeto ativo, unidades e flags persistidas |
| `edicao_guiada.entra_em_edicao(nome)` | Blender | contexto explícito; recusa trocar o modo de outro objeto |
| `edicao_guiada.captura(nome)` | Blender | coordenadas, conectividade e unidade; não avalia modificadores |
| `edicao_guiada.copia_para_previa(nome, novo_nome)` | Blender | objeto e malha independentes, materiais compartilhados preservados |
| `edicao_guiada.desloca_com_pesos(nome, plano)` | Blender | executa pesos explícitos; não escolhe a feição nem reconstrói topologia |
| `edicao_guiada.mede_regiao(snapshot, indices_faces)` | Blender | área, qualidade e ângulos; não emite aprovação estética |
| `edicao_guiada.verifica_deslocamento(...)` | Blender | alvo, transição e protegido com correspondência por índice; não serve após retriangulação |

Assinaturas, parâmetros, exemplo completo e escolha de verificação estão em
`sessao_e_edicao_guiada.md`. Reconstrução com topologia nova exige referências de
superfície/seção: não a force para dentro de `verifica_deslocamento`.

## Verificadores e validador

Verificadores estabilizados em M0 que **acompanham o pacote**, em `verificadores/`,
como derivados da base estabilizada (`PROVENIENCIA.json` traz os hashes). **Não reescreva
os resultados nem a agregação deles**, e não os edite ali: o comportamento foi
estabilizado com teste, e mudar aqui alteraria resultado sem prova. Dependências:
ver "Ambiente e dependências" acima. Eles preservam a distinção entre falha
operacional, requisito reprovado, não implementado, não aplicável e indeterminado, e os
papéis decisivo e informativo.

| Ferramenta | O que responde | Chamada |
|---|---|---|
| `check_mesh.py` | malha apta a booleana e a export fechado; contagens topológicas e componentes | `python verificadores/check_mesh.py --malha peca.stl` |
| `check_intent.py` | a geometria atende aos **requisitos declarados** | `python verificadores/check_intent.py --malha peca.stl --requisitos req.json` — `--malha` é **obrigatório**; formato do arquivo em `verificar.md` |
| `secoes.py` | seção de malha em polígonos 2D | importado por `check_intent.py` |
| `sweep_params.py` | varredura de família paramétrica por três portões | precisa do diretório do módulo no caminho de importação. PowerShell: `$env:PYTHONPATH = "cenarios"` e depois `python verificadores/sweep_params.py --modulo familia_exemplo --funcao familia_placa --grade "L=70,80;d=4,5" --json r.json`. Em bash, o prefixo `PYTHONPATH=cenarios` na mesma linha |
| `matriz.py` | **o que** verificar, a partir da classificação | `python verificadores/matriz.py criar superficie visualizacao '{"borda":"proibida"}'` — vocabulário fechado; a finalidade de impressão é `impressao_fdm`, não `impressao` |

`scripts/valida_requisitos.py` (fora do Blender) confere a **forma** do arquivo de
requisitos antes de `check_intent.py`; `--tipos` lista tipos, campos obrigatórios e
tolerâncias aceitas. `scripts/testa_paridade_validador.py` compara as respostas do
validador e do verificador na mesma entrada (339 casos: oito requisitos bem formados,
bateria cega de 14 valores ruins em cada campo de cada tipo, 23 casos especiais) e
separa `FALHA_PERMISSIVO` (o verificador recusa e o validador diz OK — o lado que
engana pior) de `FALHA_ESTRITO`. Detalhes, tabela de tolerâncias e códigos de saída:
ver `verificar.md`.

O verificador `check_intent.py` cita `tolerance_lookup.py` numa mensagem; esse arquivo
**não existe** no pacote. Folga calibrada: `projetar_para_imprimir.md`, seção 1 (tabela
de folgas calibradas); fora dela, **A_CALIBRAR**.

### Sem medidor: não substitua por improviso

| Capacidade | Estado |
|---|---|
| folga de encaixe calibrada | só as condições da tabela em `projetar_para_imprimir.md`, seção 1; fora delas, **A_CALIBRAR** |
| parede mínima | em malha, `scripts/piso_espessura.py` mede por raio; não há requisito de parede no `check_intent.py` |
| folga entre peças | sem medidor |
| silhueta contra imagem | sem medidor |
| reconstrução de CAD a partir de malha | fora do escopo |
| seleção por imagem | fora do escopo |
| geometria de junta para peça dividida | sem medidor |
| detectar declaração inconsistente com a geometria | sem medidor |
| preenchimento em superfície curva ou com mais de dois limites | fora do domínio da receita; ela **recusa** e diz isso |
| preenchimento em objeto girado | fora do domínio; MEDIDO: a receita recusa com as alternativas |

Requisito declarado sem medidor sai como `NAO_IMPLEMENTADA`, que **barra** quando o
papel é decisivo e **não barra** quando é informativo. Em nenhum dos dois casos se
preenche com valor favorável, zero ou estimativa.

## Scripts de medição

Fora do Blender (hospedeiro, trimesh/numpy):

| Ferramenta | Para que usar / limite |
|---|---|
| `scripts/transplante_deslocamento.py` | combinar regiões de versões da **mesma** malha e levar para uma derivada, sem booleana. Ver `transplante_de_deslocamento.md` |
| `scripts/origem_do_recorte.py` | de qual malha inteira um cupom saiu, por coincidência exata de vértices (~1 s) |
| `scripts/recorta_cupom.py` | recorta cupom por caixa (coordenadas da malha ou da mesa), mantém orientação, rótulo em baixo-relevo no topo; STL na entrada pode fundir vértices — prefira PLY |
| `scripts/componentes.py` | lista corpos de 3MF/STL com assinatura (faces, dimensões, centro) e nomes do Studio. Aponta; o render confirma |
| `scripts/mapa_balanco.py` | área que pedirá suporte e área de contato com a mesa, por corpo, antes de fatiar |
| `scripts/piso_espessura.py` | mede espessura por raio e engrossa feição fina; minutos em 200 mil vértices |

Booleana com malha (auto-interseção, round-trip de STL, ordem de recorte e
engrossamento): ver `criar_e_parametrizar.md`, booleana. Se a peça final precisa de uma
booleana já feita numa versão antiga, prefira `transplante_de_deslocamento.md` a
refazê-la na versão engrossada.
