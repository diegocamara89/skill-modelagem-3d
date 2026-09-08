# Mapa de ferramentas: o que existe, o que exige, o que não existe

Tudo aqui foi verificado em 07/09/2026 na instalação de ensaio. Onde diz MEDIDO, há
número atrás. Onde diz NÃO EXISTE, não invente substituto.

## Ambiente medido

| Componente | Versão medida | Como confirmar |
|---|---|---|
| Blender | 5.2.1 LTS, Python 3.13.13 | `python scripts/roda_blender.py --achar`, depois um script que imprima `bpy.app.version_string` |
| build123d + OCP | usado pelos verificadores de M0 | `python -c "import build123d"` |
| trimesh | usado por `check_mesh.py` | `python -c "import trimesh"` |
| lib3mf | escritor de 3MF | `python -c "import lib3mf"` |

**Não disponíveis e nunca exigidos:** `rtree`, `matplotlib`, `fast_simplification`.
Se uma receita parecer precisar deles, a receita está errada.

## Como chamar o Blender — duas lacunas medidas

Instalação pela Microsoft Store. **Duas coisas quebram quem tenta o caminho óbvio:**

1. `C:\Program Files\WindowsApps\...\blender.exe` **não é executável direto**: dá
   "Acesso negado", tanto pelo shell quanto pelo Python. O caminho que funciona é o
   alias de execução `%LOCALAPPDATA%\Microsoft\WindowsApps\blender-launcher.exe`.
2. O launcher devolve **stdout vazio, sempre**: medido em 8 modos de execução
   diferentes, 0 bytes em stdout e 0 em stderr nos oito. Ler stdout não funciona.
3. O código de saída é prova **negativa**, não positiva. Uma sessão limpa contestou
   a afirmação anterior desta página — que ele «é 0 mesmo quando o Blender falhou» —
   e ela estava **errada como escrita**. Remedido, oito modos:

| O que o script de dentro faz | Código devolvido |
|---|---|
| termina normalmente, ou `sys.exit(0)` | 0 |
| `sys.exit(1)` / `sys.exit(2)` | **1** / **2**, propagados fielmente |
| levanta exceção não tratada | **0** |
| erro de sintaxe no script | **0** |
| importa módulo que não existe | **0** |
| chama operador do Blender que não existe | **0** |

   Ou seja: o código propaga a saída **deliberada** do script e engole toda falha
   **imprevista** — que são exatamente as que ninguém planeja. **Código não zero é
   sinal confiável de falha; código zero não é sinal de nada.** A medição está em
   `evidencias_finais/CODIGO_DE_SAIDA_DO_LANCADOR.json`, fora do pacote.

Por isso o contrato é: **o script de dentro escreve um arquivo de resultado**, e quem
chama espera esse arquivo. Sem arquivo, não houve resultado — e note que a correção
acima **não** dispensa o contrato: ela apenas troca o motivo, de «o código não diz
nada» para «o código não diz nada quando é zero, que é o caso das falhas que
importam». Use
`scripts/roda_blender.py`, que implementa exatamente isso:

```bash
python scripts/roda_blender.py meu_script.py --resultado saida.json
python scripts/roda_blender.py --achar          # só localiza o executável
```

Duas bandeiras que existem por causa de defeito medido, não por conveniência:

| Bandeira | Sem ela | Com ela |
|---|---|---|
| `--passa-resultado` | o caminho do resultado tem que ser escrito **duas vezes** — aqui e dentro do arquivo de parâmetros — e nada confere se as duas grafias coincidem; divergindo, sai `SEM_RESULTADO` com o arquivo existindo em outra pasta | o caminho vai numa bandeira **nomeada**, `--resultado-em <path>`, acrescentada ao fim dos seus argumentos, e é escrito num lugar só. `gera_cenario.py` e `ensaio_preenchimento.py` leem essa bandeira. Ela é nomeada porque a primeira versão a passava por **posição** e os cenários liam `argv[1]` — com dois argumentos seus, o script gravava sobre o **segundo argumento seu** e o chamador esperava outro arquivo |
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

`TEMPO_ESGOTADO` **não prova** que o script parou dentro do Blender. Inspecione antes
de repetir. E `OK` **sem** `--exigir` prova só que o arquivo é legível: legível não é
aprovado.

`SEM_RESULTADO` é o caminho de falha mais comum — script que não gravou — e era o mais
**lento**: a espera pelo arquivo ia até o tempo-limite inteiro mesmo com o processo já
morto, e uma sessão limpa gastou **300 s** num erro decidido no primeiro segundo.
Corrigido: depois de o processo sair, a espera dura uma carência de 5 s e desiste.
Medido depois da correção: **7 s** em vez de 300. O retorno traz
`segundos_de_espera_pelo_arquivo`, para o custo ser visível.

`--cena <arquivo.blend>` abre um `.blend` existente em vez da cena inicial, e é assim
que se retoma a peça salva numa execução anterior para rodar a próxima variante sobre
ela. `--sem-fabrica` desliga o `--factory-startup`; deixe ligado nos ensaios, porque é
o que impede herdar preferências e complementos do usuário.

### O contrato do script que roda DENTRO do Blender

Esta parte não estava escrita em nenhuma referência, e uma sessão limpa precisou
extraí-la lendo o código dos cenários. É o contrato central da rota headless, e o
motivo dele está no começo desta página: **o lançador desanexa, devolve código 0 e
stdout vazio**. Quem levanta uma exceção e não a grava não deixa vestígio nenhum no
chamador.

O script de dentro precisa fazer quatro coisas:

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

Note que o `cfg` sai de `argv[0]` **só** quando ele não começa com `--`: senão a
própria bandeira seria lida como arquivo de parâmetros.

Combine com `--exigir veredito_global=ATENDIDO` do lado de fora: aí o erro que você
gravou vira código de saída não zero, em vez de um `OK` sobre um relatório que diz
`ERRO`. `cenarios/gera_cenario.py` e `cenarios/ensaio_preenchimento.py` são os dois
exemplos completos deste contrato — e o gerador **passou a ser**: até a quinta revisão
ele era apresentado como exemplo completo e não capturava exceção nem emitia veredito,
de modo que um erro nele não deixava vestígio nenhum. Medido depois da correção: com
`saida_blend` apontando para um caminho ocupado por diretório, ele grava
`veredito_global: "ERRO"` com tipo e mensagem, e o invocador devolve
`VEREDITO_NEGATIVO` (`evidencias_finais/CONTRATO_DO_RESULTADO.json`).

**Como importar quando o seu script vive FORA do pacote**, que é o único caso
possível se a pasta é somente leitura. Os dois cenários deste pacote resolvem com
`os.path.dirname(os.path.abspath(__file__))`, e isso **só funciona porque eles moram
dentro de `cenarios/`**. Para um script seu, em outra pasta, o caminho tem que vir de
fora — e a forma mais simples é uma variável de ambiente com reserva explícita:

```python
import os, sys
sys.dont_write_bytecode = True
pacote = os.environ.get("PACOTE_MODELAGEM_3D") or r"<raiz do pacote>"
sys.path.insert(0, os.path.join(pacote, "scripts"))
import bl_ferramentas as F
```

Uma sessão limpa teve que inventar exatamente este mecanismo, e registrou que
funcionou mas era invenção dela e não da pasta. Agora é da pasta.

**A caixa envolvente em coordenada de MUNDO já existe, e é fácil não achar.**
`diagnostico(nome)` devolve `objeto.caixa_mundo_min` e `objeto.caixa_mundo_max`, com a
matriz de mundo já aplicada — que é justamente o que evita o defeito nº 1 desta rota,
o de medir em coordenada local. Não há função separada de caixa envolvente, e não
precisa haver: a mesma sessão limpa escreveu a sua própria por não encontrar esta, e
teve que decidir sozinha medir em mundo. **Use o `diagnostico`.**

**Antes de importar, desligue o bytecode.** `sys.path.insert(...)` seguido de
`import bl_ferramentas` faz o Python criar `<pacote>/scripts/__pycache__` — ou seja, a
receita manda escrever dentro da pasta que o pacote declara somente-leitura. Ponha
`sys.dont_write_bytecode = True` **antes** do import, ou exporte
`PYTHONDONTWRITEBYTECODE=1` no processo que lança o Blender.

## Duas vias de acesso ao Blender, para usos diferentes

| Via | Quando usar | Limite |
|---|---|---|
| **headless** (`--background --factory-startup`) | todo teste, toda receita reproduzível | sem interface: sobreposições e viewport **não existem**, e o histórico se comporta diferente (ver abaixo) |
| **sessão viva pelo MCP** | quando o usuário está trabalhando e quer orientação sobre a própria cena | a cena é do usuário: não carregue outro arquivo, não encerre, cuidado com alterações não salvas |

Na sessão viva, o transporte do MCP comunitário é um socket em `127.0.0.1:9876`
mantido pelo complemento dentro do Blender. Protocolo:
`{"type": "<comando>", "params": {...}}` → `{"status": "success", "result": {...}}`.
`get_scene_info` é leitura e serve de teste de conexão. **Não crie outro transporte.**

MCP sem resposta: confira handshake, se a aplicação está aberta e a versão. No
experimento, abrir a aplicação restabeleceu a conexão — falha de conexão **não**
provava complemento antigo, e reinstalar por inferência era errado.

## Auxiliares deste pacote

`scripts/bl_ferramentas.py` roda **dentro** do Blender. Existe porque cada função
abaixo cobre uma etapa que erra em silêncio. Toda função devolve fato medido e
levanta `ErroDePrecondicao` em vez de operar sobre pré-condição falsa.

| Função | Para que serve | Lacuna que ela fecha |
|---|---|---|
| `diagnostico` | modo, objeto, unidades, transformação, seleção viva, sobreposições | seleção lida de `obj.data` está desatualizada em Edit Mode |
| `assinatura` | identidade de coordenadas **e** conectividade, com cobertura declarada | hash de `.blend` não separa geometria de câmera |
| `entra_em_edicao` / `sai_de_edicao` / `limpa_selecao` | pré-condição de modo | operações de malha exigem Edit Mode |
| `seleciona_faces_por_caixa_de_mundo` | seleção por critério em coordenada de **mundo** | `calc_center_median()` é LOCAL; MEDIDO: 1 face em mundo, 0 em local |
| `le_selecao` | seleção viva com índices e centros | índice só vale para a geometria capturada |
| `desloca_selecao` | deslocar e **medir** o efeito | MEDIDO: seleção vazia devolve `CANCELLED` e nada muda |
| `preenche_entre_limites` | volume fechado ligando dois limites, com sobreposição no material | volume que só encosta deixa ranhura, e estanqueidade não pega |
| `volume_de_material_na_caixa` | volume **exato** de material dentro de uma caixa, medido em cópia por booleana. **Devolve um `float` nu**, não dicionário — é a única função do pacote que faz isso, e uma sessão limpa perdeu um comando com `TypeError: 'float' object is not subscriptable` por analogia com as outras | é com ela que o preenchimento prova as **três** interseções antes de alterar a peça |
| `limpa_degeneracoes_na_regiao` | remover face de área nula **só** na região, com tolerância justificada | MEDIDO: a união deixa 4 faces degeneradas sem abrir borda |
| `mede_malha` | bordas, não-manifold, soltas, degeneradas **e componentes conexos** — cada um separado | "sem borda aberta" não é "sem degeneração". A contagem de componentes foi acrescentada depois de uma revisão notar que o docstring a prometia e o retorno não a trazia |
| `mede_topo_em_pontos` | altura do material contra o valor **esperado** | é a única medida aqui que pega ranhura e desnível |
| `secao_por_plano` | interseção das arestas com um plano, tratando coplanar e duplicado | inspeção independente da junção |
| `captura_regiao_protegida` / `compara_regiao_protegida` | conjunto de posições **e área** das faces inteiras dentro de uma caixa | contar faces cujos vértices caem na caixa não prova preservação; e conjunto de posições **sozinho** também não: apagando uma face de um tetraedro, os quatro vértices continuam nas faces vizinhas e 3,4641 mm² desaparecem sem o conjunto mudar. Medido por validação adversarial em 08/09/2026 |
| `marca_recuperacao` / `contexto_de_historico` / `desfaz_e_confere` / `refaz_e_confere` | histórico conferido pelo conteúdo | `ed.undo` falha de dois modos diferentes; ver `recuperar_salvar_exportar.md` |
| `salva_cena` / `exporta_malha` | entrega com hash e assinatura | recusa sobrescrever a origem por padrão |

`scripts/roda_blender.py` roda **fora** do Blender e resolve as duas lacunas de
invocação descritas acima.

`scripts/mcp_blender.py` roda **fora** do Blender e é o cliente do socket do
complemento MCP. Existe porque a referência descrevia o protocolo e o pacote não
trazia cliente, obrigando o agente a escrever leitura incremental de JSON em socket —
o tipo de trecho mecânico frágil que a receita não deve deixar para ele improvisar.
**Somente leitura por padrão**: comando que altera a cena exige `permitir_escrita`
explícito, porque a cena é do usuário e pode ter alteração não salva.

Estados, todos medidos com controle: `OK`, `SEM_SERVIDOR`, `TEMPO_ESGOTADO`,
`RESPOSTA_ILEGIVEL`, `ERRO_DO_ADDON`, `ESCRITA_BARRADA`, `PARAMS_ILEGIVEIS`.
`TEMPO_ESGOTADO` **não prova** que o código parou dentro do Blender.

```bash
python scripts/mcp_blender.py --testa-conexao
python scripts/mcp_blender.py get_object_info --params '{"name": "Cubo"}'
```

`scripts/valida_requisitos.py` roda **fora** do Blender e confere a **forma** do
arquivo de requisitos antes de chamar `check_intent.py`. Existe porque a forma natural
do JSON — uma lista nua — produz traceback não tratado dentro do verificador, que é
cópia congelada e não pode ser editado. `--tipos` lista os tipos, campos obrigatórios
e tolerâncias aceitas.

Ele **espelha** o esquema do verificador: eixo restrito a X/Y/Z, número finito,
tolerância finita não negativa, `caixa_min < caixa_max` em todos os eixos, `entre` com
**dois** caminhos. E aceita o que o verificador aceita, inclusive número escrito como
texto (`"30"`) — recusar aqui o que ele aceita é a mesma divergência, com o sinal
trocado; esses casos saem em `avisos`, não em `problemas`.

Além do espelho, ele confere o que o verificador **não** confere: tolerância cujo nome
não é lido para aquele tipo, contagem fracionária ou negativa, identificador repetido e
tipo fora do vocabulário. Esses extras estão declarados um por um em
`EXTRAS_ALEM_DO_ESPELHO`, no próprio arquivo.

```bash
python scripts/testa_paridade_validador.py            # 339 casos, ATENDIDO
```

`scripts/testa_paridade_validador.py` importa o verificador congelado e compara as
**duas** respostas na mesma entrada, caso por caso: oito requisitos bem formados, uma
bateria cega de 14 valores ruins em cada campo de cada tipo, e 23 casos especiais
vindos de achados concretos. Ele separa `FALHA_PERMISSIVO` (o verificador recusa e o
validador diz OK — o lado que engana pior) de `FALHA_ESTRITO`. Existe porque a versão
anterior do validador **anunciava** espelhar o esquema e não espelhava, e "eu conferi o
fonte tipo por tipo" não é prova de paridade.

## Verificadores reaproveitados, fora do Blender

Estes são os verificadores estabilizados em M0 e **acompanham o pacote**, em
`verificadores/`, como cópias **byte a byte** da base congelada — `PROVENIENCIA.json`
traz os hashes. **Não reescreva os resultados nem a agregação deles**, e não os edite
ali: o comportamento foi estabilizado com teste, e mudar aqui alteraria resultado sem
prova.

Eles precisam, no Python do hospedeiro: `trimesh`, `numpy`, `manifold3d`, `shapely` e,
para a varredura, `build123d`. `matriz.py` roda só com a biblioteca padrão.

Eles preservam a distinção entre falha operacional, requisito reprovado, não
implementado, não aplicável e indeterminado, e os papéis decisivo e informativo.

### Incluídos no pacote, em `verificadores/`

| Ferramenta | O que responde | Chamada |
|---|---|---|
| `check_mesh.py` | malha apta a booleana e a export fechado; contagens topológicas e componentes | `python verificadores/check_mesh.py --malha peca.stl` |
| `check_intent.py` | a geometria atende aos **requisitos declarados** | `python verificadores/check_intent.py --malha peca.stl --requisitos req.json` — `--malha` é **obrigatório**; formato do arquivo em `verificar.md` |
| `secoes.py` | seção de malha em polígonos 2D | importado por `check_intent.py` |
| `sweep_params.py` | varredura de família paramétrica por três portões | precisa do diretório do módulo no caminho de importação. PowerShell: `$env:PYTHONPATH = "cenarios"` e depois `python verificadores/sweep_params.py --modulo familia_exemplo --funcao familia_placa --grade "L=70,80;d=4,5" --json r.json`. Em bash, o prefixo `PYTHONPATH=cenarios` na mesma linha |
| `matriz.py` | **o que** verificar, a partir da classificação | `python verificadores/matriz.py criar superficie visualizacao '{"borda":"proibida"}'` — vocabulário fechado; a finalidade de impressão é `impressao_fdm`, não `impressao` |

### NÃO incluídos neste pacote

Existem no acervo do projeto e **não acompanham esta entrega**, porque nenhuma rota
daqui os chama. Se um pedido precisar deles, diga que estão fora do pacote em vez de
improvisar substituto.

| Ferramenta | O que faria | Por que ficou fora |
|---|---|---|
| `find_datums.py` | regiões planas coplanares conexas | nenhuma rota atual usa |
| `align_rigid.py` | transformação rígida entre referências | rota de reconstrução, fora do escopo |
| `split_for_volume.py` | orientação e planos de corte contra envelope | rota de impressão, fora do escopo |
| `slice_check.py` | portão de fatiador, envelope e área de mesa | exige fatiador instalado, que este pacote não pressupõe |
| `tolerance_lookup.py` | consulta de folga, que **recusa inventar** | a folga é `A_CALIBRAR`; sem dado medido não há o que consultar |

## O que NÃO existe — não substitua por improviso

| Capacidade | Estado |
|---|---|
| folga de encaixe calibrada | **A_CALIBRAR**: não há valor medido. `tolerance_lookup.py` devolve pendência de propósito |
| parede mínima | sem medidor |
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
